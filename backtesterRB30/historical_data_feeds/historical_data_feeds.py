
import asyncio
from typing import List
from backtesterRB30.historical_data_feeds.historical_downloader import HistoricalDownloader
from backtesterRB30.libs.communication_broker.broker_base import BrokerBase
from backtesterRB30.libs.data_sources.data_sources_list import HISTORICAL_SOURCES
from backtesterRB30.libs.interfaces.python_backtester.data_start import DataStart
from backtesterRB30.libs.communication_broker.zmq_broker import ZMQ
from backtesterRB30.libs.communication_broker.asyncio_broker import AsyncioBroker
from backtesterRB30.libs.interfaces.utils.config import Config, BROKERS
from backtesterRB30.libs.utils.list_of_services import SERVICES, SERVICES_ARRAY
from backtesterRB30.libs.interfaces.utils.data_schema import DataSchema
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
from backtesterRB30.libs.data_sources.data_source_base import DataSource
from backtesterRB30.libs.interfaces.historical_data_feeds.instrument_file import InstrumentFile
from backtesterRB30.historical_data_feeds.functions import get_instrument_files, synchronize_dataframes, load_data_frame_ticks_2
from datetime import datetime
from os import path, makedirs
from os import listdir
from os.path import isfile, join
import pandas as pd
import time as tm
from backtesterRB30.libs.utils.service import Service
from appdirs import user_cache_dir
from json import dumps, loads

class HistoricalDataFeeds(Service):
    
    downloaded_data_path = user_cache_dir('rb30_cache')
    _broker: BrokerBase

    def __init__(self, config: Config, data_schema: DataSchema, loop = None, logger=print):
        super().__init__(config, logger)
        self.config: Config=config
        self.__loop =  loop
        self.__custom_event_loop = False
        if self.__loop == None: 
            self.__loop = asyncio.get_event_loop()
            self.__custom_event_loop= True
        self.__data_schema: DataSchema = data_schema
        self.__columns=['timestamp']+[c.symbol for c in self.__data_schema.data]
        self.__historical_sources_array = [i for i in dir(HISTORICAL_SOURCES) if not i.startswith('__')]
        self.__data_sources = {}
        self.__sending_locked = False
        self.__start_time = 0
        self.__data_to_download_2 = None
        self.__engine_ready = False
        self.__historical_downloader = HistoricalDownloader(self.__data_schema, 
                self.__historical_sources_array, self.downloaded_data_path, self._log)



    # # override
    # def _asyncio_loop(self, loop: asyncio.AbstractEventLoop):
    #     self._create_listeners(loop)
    #     self.__validate_downloaded_data_folder()
    #     if self.config.backtest:
    #         self.__data_to_download_2 = self.__historical_downloader.run(loop)
    #         data_parts = self.__prepare_loading_data_structure_2()
    #         loop.create_task(self.__historical_data_loop_ticks(data_parts))
    #     else:  
    #         self._log('backtest is off')

    def _loop(self):
        # self._broker.run()
        self._broker.create_listeners(self.__loop)
        self.__validate_downloaded_data_folder()
        if self.config.backtest:
            self.__data_to_download_2 = self.__historical_downloader.run(self.__loop)
            data_parts = self.__prepare_loading_data_structure_2()
            self.__loop.create_task(self.__historical_data_loop_ticks(data_parts))
        else:  
            self._log('backtest is off')
        if self.__custom_event_loop:
            self.__loop.run_forever()
            self.__loop.close()

    # def _send(self, service: SERVICES, msg: str, *args):
    #     self._broker.send(service, msg, *args)

    def _configure(self):
        super()._configure()
        # register commands
        self._broker.register("unlock_historical_sending", self.__unlock_historical_sending_event)
        self._broker.register("engine_ready_response", self.__engine_ready_response_event)

    # # override
    # def _handle_zmq_message(self, message):
    #     pass


    async def __send_start_params(self):
        self.__start_time = tm.time()
        file_names_grouped = []
        for symbol in self.__data_schema.data:
            file_names_grouped.append({
                "symbol": symbol.symbol,
                "source": symbol.historical_data_source,
                "files": get_instrument_files(symbol)
            })
        start_params = {
            'file_names': file_names_grouped,
            'start_time': self.__start_time
        }
        await self._broker.send(SERVICES.python_backtester, 'data_start', DataStart(**start_params))
        return


    async def __historical_data_loop_ticks(self, data_parts: dict):
        # waiting for zero mq ports starts up
        await asyncio.sleep(0.5)
        while True:
            # if self.__data_downloaded(self.__data_to_download):
            await self._broker.send(SERVICES.python_engine, 'engine_ready', SERVICES.historical_data_feeds.value)
            if self.__validate_data_downloaded(self.__data_to_download_2) and self.__engine_ready: 
                self._log('All data has been downloaded')
                
                sending_counter = 0
                self._log('Starting data loop')
                await self.__send_start_params()
                # return
                last_row = []
                for _, one_year_array in data_parts.items():
                    self._log('Synchronizing part of data')
                    data_part = load_data_frame_ticks_2(self.__data_schema, self.__columns, self.downloaded_data_path, last_row, one_year_array)
                    for row in data_part:
                        last_row = row
                        await self._broker.send(SERVICES.python_engine,'data_feed',list(last_row))
                        sending_counter += 1
                        if sending_counter % 1000 == 0:
                            self.__sending_locked = True
                            await self._broker.send(SERVICES.python_engine, 'historical_sending_locked')
                            while self.__sending_locked:
                                await asyncio.sleep(0.01)

                await self._broker.send(SERVICES.python_engine, 'data_finish')
                break
            await asyncio.sleep(1)


    def __validate_data_downloaded(self, files_to_download: List[InstrumentFile]):
        if files_to_download == None:
            return False
        files_in_directory = [f for f in listdir(self.downloaded_data_path) if isfile(join(self.downloaded_data_path, f))]
        data_to_download = list(set([f.to_filename() for f in files_to_download]) - set(files_in_directory))
        return data_to_download == []


    def __validate_downloaded_data_folder(self):
        if not path.exists(self.downloaded_data_path):
            makedirs(self.downloaded_data_path)


    def __prepare_loading_data_structure_2(self) -> dict:
        files_collection = {}
        for symbol in self.__data_schema.data:
            files: List[InstrumentFile] = get_instrument_files(symbol)
            for f in files:
                if not f.time_stop in files_collection:
                    files_collection[f.time_stop]: List[InstrumentFile] = []
                files_collection[f.time_stop].append(f)
        return dict(sorted(files_collection.items()))

    async def __stop_all_services(self):
        for service in SERVICES_ARRAY:
            if service != self.name:
                await self._broker.send(getattr(SERVICES, service), 'stop')
        self._broker.stop()

    # COMMANDS
    
    async def __unlock_historical_sending_event(self):
        self.__sending_locked = False

    async def __engine_ready_response_event(self):
        self.__engine_ready = True



    # def __map_raw_to_instruments(self, raw: list, instruments: list):
    #     last_raw_obj = {}
    #     if len(raw) != len(instruments):
    #         raise Exception('Error in map_raw_to_instruments. Lengths of raw and list of instruments are not equal')
    #     for value, instrument in zip(raw, instruments):
    #         last_raw_obj[instrument] = value
    #     return last_raw_obj


    # def __prepare_dataframes_to_synchronize_2(self, downloaded_data_path: str, 
    #                 last_row: list, files_array: List[InstrumentFile]) -> List[dict]:
    #     list_of_dfs = []
    #     for data_element in self.__data_schema.data:
    #         columns = ['timestamp', data_element.symbol]
    #         file_name = 'none'
    #         actual_raw = [0,0]
    #         prev_raw = [0,0]
    #         for element in files_array:
    #             if data_element.symbol == element.instrument:
    #                 file_name = element.to_filename()
    #         if file_name == 'none':
    #             # No file in this period for this instrument. Set empty dataframe.
    #             df = pd.DataFrame([], columns=columns)
    #         else:
    #             # File exists. Load dataframe.
    #             df = pd.read_csv(join(downloaded_data_path, file_name), index_col=None, header=None, names=columns)
    #             # append last raw it if exists
    #             if last_row != []:
    #                 # self._log('appending last row')
    #                 last_raw_mapped = self.__map_raw_to_instruments(last_row, self.__columns)
    #                 prev_raw[0] = last_raw_mapped["timestamp"]
    #                 prev_raw[1] = last_raw_mapped[data_element.symbol]
    #         obj = {
    #             "trigger_feed": data_element.trigger_feed,
    #             "rows_iterator": df.iterrows(),
    #             "actual_raw": actual_raw,
    #             "prev_raw": prev_raw,
    #             "consumed": False
    #         }            
    #         #prepare to load:
    #         if obj['actual_raw'][0] == 0:
    #             try:
    #                 i, v = next(obj['rows_iterator'])
    #                 obj['actual_raw'] = list(v)
    #             except StopIteration:
    #                 obj['consumed'] = True
    #         list_of_dfs.append(obj)
    #     return list_of_dfs
                

    # def __load_data_frame_ticks_2(self, downloaded_data_path: str, last_row: list, files_array: List[InstrumentFile]) -> List[list]:
    #     """
    #     Function is geting files array from one period that are going to be loaded. 
    #     Function returns synchronized data in list of lists which are ready to send to engine.
    #     """
    #     list_of_dfs = self.__prepare_dataframes_to_synchronize_2(downloaded_data_path, last_row, files_array)
    #     rows = synchronize_dataframes(list_of_dfs, last_row)
    #     return rows



    
    # def __get_data_to_download(self, data_schema: DataSchema):
    #     for data_symbol in data_schema.data:
    #         data_symbol.additional_properties['files_to_download']: List[InstrumentFile] = []
    #         data_symbol.additional_properties['files_to_download'] = self.__check_symbol_data_exists(data_symbol)
    #         if self.__data_to_download_2 == None:
    #             self.__data_to_download_2 = []
    #         self.__data_to_download_2 = self.__data_to_download_2 + data_symbol.additional_properties['files_to_download']


    # def __create_downloading_clients(self, historical_sources_array: list, data_schema: DataSchema, data_sources: dict):
    #     for source in historical_sources_array:
    #         if source in [data.historical_data_source for data in data_schema.data if \
    #                 data.additional_properties['files_to_download'] != []]:
    #             data_sources[source]: DataSource = getattr(HISTORICAL_SOURCES, source)(self._log)


    # def __validate_symbols_to_download(self,data_schema: DataSchema, loop: asyncio.AbstractEventLoop):
    #     self._log('validating symbols before download')
    #     for symbol in data_schema.data:
    #         if symbol.additional_properties['files_to_download'] != []:
    #             data_source_client: DataSource = self.__get_data_source_client(symbol.historical_data_source)
    #             res = loop.run_until_complete(data_source_client.validate_instrument(symbol))
    #             if not res:
    #                 raise Exception('Error while validation symbol.')

    # def __download_prepared_data(self, data_schema: DataSchema, loop: asyncio.AbstractEventLoop):
    #     for symbol in data_schema.data:
    #         if symbol.additional_properties['files_to_download'] != []:
    #             loop.create_task(self.__download_symbol_data(symbol))


    # def __get_data_source_client(self, historical_source: str) -> DataSource:
    #     client = self.__data_sources[historical_source]
    #     if not client:
    #             self._log('Error, no registered source client')
    #             self.__stop_all_services()
    #     return client


    # def __check_symbol_data_exists(self, data_symbol: DataSymbol) -> List[InstrumentFile]:
    #     """
    #     data scheme
    #     <symbol>__<source>__<interval>__<date-from>__<date-to>
    #     all instruments are downloaded in year files.
    #     """
    #     files: List[InstrumentFile] = get_instrument_files(data_symbol)
    #     # self._log('files to download "'+str(data_symbol.symbol)+'" :', files)
    #     files_in_directory = [f for f in listdir(self.downloaded_data_path) if isfile(join(self.downloaded_data_path, f))]
    #     files_to_download = list(set([f.to_filename() for f in files]) - set(files_in_directory))
    #     files_to_download = [InstrumentFile.from_filename(file) for file in files_to_download]
    #     return files_to_download
     

    # async def __download_symbol_data(self, symbol: DataSymbol):
    #     files_to_download: List[InstrumentFile] = symbol.additional_properties['files_to_download']
    #     await self.__download_symbol_files(files_to_download, symbol.historical_data_source)


    # async def __download_symbol_files(self, files: List[InstrumentFile], source: str):
    #     data_source_client: DataSource = self.__get_data_source_client(source)
    #     for file in files:
    #         await data_source_client.download_instrument(self.downloaded_data_path, file)


    # def __validate_data_schema_instruments(self, data_symbol_array: List[DataSymbol], loop: asyncio.AbstractEventLoop):
    #     self._log('Data_schema validation')
    #     #check for duplicates:
    #     seen = []
    #     for x in data_symbol_array:
    #         data = str(x.symbol)+str(x.historical_data_source)
    #         if data in seen:
    #             raise Exception('Duplicate data symbols')
    #         else:
    #             seen.append(data)
    #     #check other
    #     number_of_trigger_feeders = 0
    #     for data in data_symbol_array:
    #         if data.backtest_date_start == None:
    #             raise Exception('Error. You must provide "backtest_date_start" field in data_schema file while you are backtesting your strategy')
    #         if data.backtest_date_start >= data.backtest_date_stop: 
    #             raise Exception('Error. You have provided "backtest_date_start" is equal or bigger than "backtest_date_start" ')
    #         if [data.backtest_date_start.hour,
    #             data.backtest_date_start.minute,
    #             data.backtest_date_start.second,
    #             data.backtest_date_start.microsecond] != [0,0,0,0]:
    #             raise Exception('Error. Provide your "backtest_date_start" and "backtest_date_stop" in a day accuracy like: "backtest_date_start": datetime(2020,6,1)')
    #         if data.historical_data_source not in self.__historical_sources_array: 
    #             raise Exception('Error. This historical_data_source not implemented yet')
    #         if data.trigger_feed == True:
    #             number_of_trigger_feeders += 1
    #     if number_of_trigger_feeders < 1:
    #         raise Exception('Error. Your "data_schema.py" must have at least one instrument that triggers feeds')

    # # override
    # def _loop(self):
    #     loop = asyncio.get_event_loop()
    #     self._create_listeners(loop)
    #     self.__validate_downloaded_data_folder()
    #     if self.config.backtest:
    #         self.__get_data_to_download(self.__data_schema)
    #         self.__create_downloading_clients(self.__historical_sources_array, self.__data_schema, self.__data_sources)
    #         self.__validate_data_schema_instruments(self.__data_schema.data, loop)
    #         self.__validate_symbols_to_download(self.__data_schema, loop)
    #         self.__download_prepared_data(self.__data_schema, loop)

    #         data_parts = self.__prepare_loading_data_structure_2()
    #         loop.create_task(self.__historical_data_loop_ticks(data_parts))
    #     else:  
    #         self._log('backtest is off')
    #     loop.run_forever()
    #     loop.close()