
import asyncio
from typing import List
from backtesterRB30.historical_data_feeds.modules.coingecko import CoingeckoDataSource
from backtesterRB30.libs.interfaces.python_backtester.data_start import DataStart
from backtesterRB30.libs.zmq.zmq import ZMQ
from backtesterRB30.libs.utils.list_of_services import SERVICES, SERVICES_ARRAY
from backtesterRB30.libs.interfaces.utils.data_schema import DataSchema
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
from backtesterRB30.libs.utils.historical_sources import HISTORICAL_SOURCES
from backtesterRB30.historical_data_feeds.modules.binance import *
from backtesterRB30.historical_data_feeds.modules.dukascopy import *
from backtesterRB30.historical_data_feeds.modules.rb30_disk import *
from backtesterRB30.historical_data_feeds.modules.exante import *
from backtesterRB30.libs.interfaces.utils.config import Config
from backtesterRB30.libs.interfaces.historical_data_feeds.instrument_file import InstrumentFile
from backtesterRB30.libs.utils.timestamps import datetime_to_timestamp
from backtesterRB30.libs.utils.module_loaders import import_data_schema
from datetime import datetime, timezone
from os import path, mkdir, getenv
from os import listdir
from os.path import isfile, join
from binance import Client
import pandas as pd
from os import mkdir
import time as tm

class HistoricalDataFeeds(ZMQ):
    
    downloaded_data_path = '/var/opt/data_historical_downloaded'

    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.__data_schema: DataSchema = import_data_schema(self.config.strategy_path)
        self.__columns=['timestamp']+[c.symbol for c in self.__data_schema.data]
        self.__historical_sources_array = [i for i in dir(HISTORICAL_SOURCES) if not i.startswith('__')]
        self.__data_sources_classes = {}
        self.__data_sources = {}
        self.__sending_locked = False
        self.__start_time = 0
        self.__data_to_download_2 = None

        #register data sources classes
        self.__register_data_source(HISTORICAL_SOURCES.binance, BinanceDataSource)
        self.__register_data_source(HISTORICAL_SOURCES.exante, ExanteDataSource)
        self.__register_data_source(HISTORICAL_SOURCES.ducascopy, DukascopyDataSource)
        self.__register_data_source(HISTORICAL_SOURCES.rb30disk, RB30DataSource)
        self.__register_data_source(HISTORICAL_SOURCES.coingecko, CoingeckoDataSource)

        # register commands
        self._register("unlock_historical_sending", self.__unlock_historical_sending_event)

    # override
    def _loop(self):
        loop = asyncio.get_event_loop()
        self._create_listeners(loop)
        self.__validate_and_download(loop)
        loop.create_task(self.__historical_data_loop_ticks())
        loop.run_forever()
        loop.close()

    # override
    def _handle_zmq_message(self, message):
        pass


    def __validate_and_download(self, loop: asyncio.AbstractEventLoop):
        for source in self.__historical_sources_array:
            if source in [data.historical_data_source.value for data in self.__data_schema.data]:
                self.__data_sources[source]: DataSource = self.__data_sources_classes[source](self._log)
        if not self.__validate_data_schema_instruments(self.__data_schema.data, loop): 
            self.__stop_all_services()
        self.__validate_downloaded_data_folder()

        # self.__file_names_to_load, self.__data_to_download =  self.__check_if_all_data_exists(self.__data_schema.data)
        # if len(self.__data_to_download) > 0:
        #     if not self.__download_data(self.__data_to_download, loop):
        #         self._log('Error while downloading')
        #         self.__stop_all_services()
        for symbol in self.__data_schema.data:
            loop.create_task(self.__download_symbol_data(symbol))

        # self.data_parts = self.__prepare_loading_data_structure(self.__file_names_to_load)
        self.data_parts = self.__prepare_loading_data_structure_2()

    def __register_data_source(self, source_name: HISTORICAL_SOURCES, data_source_class):
        self.__data_sources_classes[source_name.value] = data_source_class

    def __get_data_source_client(self, historical_source: str) -> DataSource:
        client = self.__data_sources[historical_source]
        if not client:
                self._log('Error, no registered source client')
                self.__stop_all_services()
        return client

    async def __historical_data_loop_ticks(self):
        # waiting for zero mq ports starts up
        await asyncio.sleep(0.5)
        while True:
            # if self.__data_downloaded(self.__data_to_download): 
            if self.__data_downloaded_2(self.__data_to_download_2): 
                self._log('All data has been downloaded')
                
                sending_counter = 0
                self._log('Starting data loop')
                self.__start_time = tm.time()
                
                start_params = {
                    'file_names': [file.to_filename() for file in self.__get_instrument_files([symbol for symbol in self.__data_schema.data if symbol.main == True][0])],
                    'start_time': self.__start_time
                }
                super()._send(SERVICES.python_backtester, 'data_start', DataStart(**start_params))

                last_row = []
                for _, one_year_array in self.data_parts.items():
                    self._log('Synchronizing part of data')
                    data_part = self.__load_data_frame_ticks_2(self.downloaded_data_path, last_row, one_year_array)
                    for row in data_part:
                        last_row = row
                        super()._send(SERVICES.python_engine,'data_feed',list(last_row))
                        sending_counter += 1
                        if sending_counter % 1000 == 0:
                            self.__sending_locked = True
                            super()._send(SERVICES.python_engine, 'historical_sending_locked')
                            while self.__sending_locked:
                                await asyncio.sleep(0.01)

                super()._send(SERVICES.python_engine, 'data_finish')
                break
            await asyncio.sleep(5)

    def __validate_data_schema_instruments(self, data_symbol_array: List[DataSymbol], loop: asyncio.AbstractEventLoop):
        self._log('Data_schema validation')
        data_valid = True
        number_of_mains = 0
        number_of_trigger_feeders = 0
        for data in data_symbol_array:
            data_source_client: DataSource = self.__get_data_source_client(data.historical_data_source.value)
            res = loop.run_until_complete(data_source_client.validate_instrument(data))
            if not res:
                self._log('Error while validation.')
                data_valid = False
            if data.backtest_date_start == None:
                self._log('Error. You must provide "backtest_date_start" field in data_schema file while you are backtesting your strategy')
                data_valid = False
            if data.backtest_date_start >= data.backtest_date_stop: 
                self._log('Error. You have provided "backtest_date_start" is equal or bigger than "backtest_date_start" ')
                data_valid = False
            if [data.backtest_date_start.hour,
                data.backtest_date_start.minute,
                data.backtest_date_start.second,
                data.backtest_date_start.microsecond] != [0,0,0,0]:
                self._log('Error. Provide your "backtest_date_start" and "backtest_date_stop" in a day accuracy like: "backtest_date_start": datetime(2020,6,1)')
                data_valid = False
            if data.historical_data_source.value not in self.__historical_sources_array: 
                self._log('Error. This historical_data_source not implemented yet')
                data_valid = False
            if data.main == True:
                number_of_mains += 1
            if data.trigger_feed == True:
                number_of_trigger_feeders += 1

        if number_of_mains != 1:
            self._log('Error. Your "data_schema.py" must have one main instrument')
            data_valid = False
        if number_of_trigger_feeders < 1:
            self._log('Error. Your "data_schema.py" must have at least one instrument that triggers feeds')
            data_valid = False

        return data_valid


    def __data_downloaded(self, full_data_to_download):
        files_in_directory = [f for f in listdir(self.downloaded_data_path) if isfile(join(self.downloaded_data_path, f))]
        data_to_download = list(set(full_data_to_download) - set(files_in_directory))
        # self._log('Data is being downloaded ...', str( (len(full_data_to_download) - len(data_to_download) ) / len(full_data_to_download) * 100 )+'%')
        return data_to_download == []


    def __data_downloaded_2(self, files_to_download: List[InstrumentFile]):
        if files_to_download == None:
            return False
        files_in_directory = [f for f in listdir(self.downloaded_data_path) if isfile(join(self.downloaded_data_path, f))]
        data_to_download = list(set([f.to_filename() for f in files_to_download]) - set(files_in_directory))
        return data_to_download == []

    def __validate_downloaded_data_folder(self):
        if not path.exists(self.downloaded_data_path):
            mkdir(self.downloaded_data_path)
    
    def __check_if_all_data_exists(self, data_symbol_array: DataSymbol):
        """
        data scheme
        <symbol>__<source>__<interval>__<date-from>__<date-to>
        all instruments are downloaded in year files.
        """
        file_names: List[str] = []
        loading_structure = []
        for symbol in data_symbol_array:
            files = self.__get_file_names(symbol)
            loading_structure.append(file_names)
            file_names = file_names+files
        self._log('file names', file_names)
        files_in_directory = [f for f in listdir(self.downloaded_data_path) if isfile(join(self.downloaded_data_path, f))]
        files_to_download = list(set(file_names) - set(files_in_directory))
        return file_names, files_to_download

    def __check_symbol_data_exists(self, data_symbol: DataSymbol) -> List[InstrumentFile]:
        """
        data scheme
        <symbol>__<source>__<interval>__<date-from>__<date-to>
        all instruments are downloaded in year files.
        """
        files: List[InstrumentFile] = self.__get_instrument_files(data_symbol)
        # self._log('files to download "'+str(data_symbol.symbol)+'" :', files)
        files_in_directory = [f for f in listdir(self.downloaded_data_path) if isfile(join(self.downloaded_data_path, f))]
        files_to_download = list(set([f.to_filename() for f in files]) - set(files_in_directory))
        files_to_download = [InstrumentFile.from_filename(file) for file in files_to_download]
        return files_to_download

    def __get_instrument_files(self, symbol: DataSymbol) -> List[str]:
        instrument_files: List[InstrumentFile] = []
        params_touple = (symbol.historical_data_source, symbol.symbol, symbol.interval)

        if symbol.backtest_date_start.year < symbol.backtest_date_stop.year:
            instrument_files.append(InstrumentFile.from_params(
                        *params_touple,
                        symbol.backtest_date_start,
                        datetime(symbol.backtest_date_start.year+1,1,1)))

            for i in range(symbol.backtest_date_stop.year - symbol.backtest_date_start.year - 1):
                instrument_files.append(InstrumentFile.from_params(
                            *params_touple,
                            datetime(symbol.backtest_date_start.year + i + 1, 1, 1),
                            datetime(symbol.backtest_date_start.year + i + 2, 1, 1)))
            
            instrument_files.append(InstrumentFile.from_params(
                        *params_touple,
                        datetime(symbol.backtest_date_stop.year,1,1),
                        symbol.backtest_date_stop))
        else:
            instrument_files.append(InstrumentFile.from_params(
                        *params_touple,
                        symbol.backtest_date_start,
                        symbol.backtest_date_stop))
        return instrument_files
     
    def __get_file_names(self, symbol: DataSymbol) -> List[str]:
        date_from_date_to: List[str] = []
        file_names: List[str] = []
        if symbol.backtest_date_start.year < symbol.backtest_date_stop.year:
            date_from_date_to.append(str(int(round(datetime.timestamp(symbol.backtest_date_start) * 1000))) + "__"
                                    + str(int(round(datetime.timestamp(datetime(symbol.backtest_date_start.year+1,1,1, tzinfo=timezone.utc)) * 1000))))
            for i in range(symbol.backtest_date_stop.year - symbol.backtest_date_start.year - 1):
                date_from_date_to.append(str(int(round(datetime.timestamp(datetime(symbol.backtest_date_start.year + i + 1, 1, 1, tzinfo=timezone.utc)) * 1000))) + "__" 
                                    + str(int(round(datetime.timestamp(datetime(symbol.backtest_date_start.year + i + 2, 1, 1, tzinfo=timezone.utc)) * 1000))))
            date_from_date_to.append(str(int(round(datetime.timestamp(datetime(symbol.backtest_date_stop.year,1,1, tzinfo=timezone.utc)) * 1000))) + "__" 
                                    + str(int(round(datetime.timestamp(symbol.backtest_date_stop) * 1000))))
        else:
            date_from_date_to.append(str(int(round(datetime.timestamp(symbol.backtest_date_start) * 1000))) + "__" 
                                    + str(int(round(datetime.timestamp(symbol.backtest_date_stop) * 1000))))

        for dates in date_from_date_to:
            file_names.append(symbol.historical_data_source.value + "__" 
                                + symbol.symbol + "__" 
                                + symbol.interval.value + "__" 
                                + dates + '.csv')
        return file_names


    def __download_data(self, data_to_download, loop: asyncio.AbstractEventLoop) -> bool:
        print('len data to downlod', len(data_to_download))
        for instrument_file_name in data_to_download:
            data_instrument = instrument_file_name[:-4]
            source, instrment, interval, time_start, time_stop = tuple(data_instrument.split('__'))
            data_source_client: DataSource = self.__get_data_source_client(source)
            loop.create_task(data_source_client.download_instrument(self.downloaded_data_path, 
                                                            instrument_file_name, 
                                                            instrment, interval, 
                                                            int(time_start), 
                                                            int(time_stop)))
        return True

    async def __download_symbol_data(self, symbol: DataSymbol):
        files_to_download: List[InstrumentFile] = self.__check_symbol_data_exists(symbol)
        if self.__data_to_download_2 == None:
            self.__data_to_download_2 = []
        self.__data_to_download_2 = self.__data_to_download_2 + files_to_download
        await self.__download_symbol_files(files_to_download, symbol.historical_data_source)


    async def __download_symbol_files(self, files: List[InstrumentFile], source: HISTORICAL_SOURCES):
        data_source_client: DataSource = self.__get_data_source_client(source.value)
        for file in files:
            await data_source_client.download_instrument(self.downloaded_data_path, file)


    def __prepare_loading_data_structure(self, file_names_to_load) -> dict:
        files_collection = {}
        for instrument_file_name in file_names_to_load:
            data_instrument = instrument_file_name[:-4]
            source, instrument, interval, time_start, time_stop = tuple(data_instrument.split('__'))
            if not time_stop in files_collection:
                files_collection[time_stop] = []
            files_collection[time_stop].append({
                "instrument": instrument, 
                "instrument_file_name": instrument_file_name
                }) 
        return files_collection

    def __prepare_loading_data_structure_2(self) -> dict:
        files_collection = {}
        for symbol in self.__data_schema.data:
            files: List[InstrumentFile] = self.__get_instrument_files(symbol)
            for f in files:
                if not f.time_stop in files_collection:
                    files_collection[f.time_stop]: List[InstrumentFile] = []
                files_collection[f.time_stop].append(f)
        return files_collection


    def __stop_all_services(self):
        for service in SERVICES_ARRAY:
            if service != self.name:
                super()._send(getattr(SERVICES, service), 'stop')
        super()._stop()

    def __map_raw_to_instruments(self, raw: list, instruments: list):
        last_raw_obj = {}
        if len(raw) != len(instruments):
            self._log('Error in map_raw_to_instruments. Lengths of raw and list of instruments are not equal')
            super()._stop()
        for value, instrument in zip(raw, instruments):
            last_raw_obj[instrument] = value
        return last_raw_obj


    def __prepare_dataframes_to_synchronize_2(self, downloaded_data_path: str, 
                    last_row: list, files_array: List[InstrumentFile]) -> List[dict]:
        list_of_dfs = []
        for data_element in self.__data_schema.data:
            columns = ['timestamp', data_element.symbol]
            file_name = 'none'
            actual_raw = [0,0]
            prev_raw = [0,0]
            for element in files_array:
                if data_element.symbol == element.instrument:
                    file_name = element.to_filename()
            if file_name == 'none':
                # No file in this period for this instrument. Set empty dataframe.
                df = pd.DataFrame([], columns=columns)
            else:
                # File exists. Load dataframe.
                df = pd.read_csv(join(downloaded_data_path, file_name), index_col=None, header=None, names=columns)
                # append last raw it if exists
                if last_row != []:
                    # self._log('appending last row')
                    last_raw_mapped = self.__map_raw_to_instruments(last_row, self.__columns)
                    prev_raw[0] = last_raw_mapped["timestamp"]
                    prev_raw[1] = last_raw_mapped[data_element.symbol]
            obj = {
                "trigger_feed": data_element.trigger_feed,
                "rows_iterator": df.iterrows(),
                "actual_raw": actual_raw,
                "prev_raw": prev_raw,
                "consumed": False
            }            
            #prepare to load:
            if obj['actual_raw'][0] == 0:
                try:
                    i, v = next(obj['rows_iterator'])
                    obj['actual_raw'] = list(v)
                except StopIteration:
                    obj['consumed'] = True
            list_of_dfs.append(obj)
        return list_of_dfs


    def __prepare_dataframes_to_synchronize(self, downloaded_data_path: str, last_row: list, files_array: list) -> List[dict]:
        list_of_dfs = []
        for data_element in self.__data_schema.data:
            columns = ['timestamp', data_element.symbol]
            file_name = 'none'
            actual_raw = [0,0]
            prev_raw = [0,0]
            for element in files_array:
                if data_element.symbol == element['instrument']:
                    file_name = element['instrument_file_name']
            if file_name == 'none':
                # No file in this period for this instrument. Set empty dataframe.
                df = pd.DataFrame([], columns=columns)
            else:
                # File exists. Load dataframe.
                df = pd.read_csv(join(downloaded_data_path, file_name), index_col=None, header=None, names=columns)
                # append last raw it if exists
                if last_row != []:
                    # self._log('appending last row')
                    last_raw_mapped = self.__map_raw_to_instruments(last_row, self.__columns)
                    prev_raw[0] = last_raw_mapped["timestamp"]
                    prev_raw[1] = last_raw_mapped[data_element.symbol]
            obj = {
                "trigger_feed": data_element.trigger_feed,
                "rows_iterator": df.iterrows(),
                "actual_raw": actual_raw,
                "prev_raw": prev_raw,
                "consumed": False
            }            
            #prepare to load:
            if obj['actual_raw'][0] == 0:
                try:
                    i, v = next(obj['rows_iterator'])
                    obj['actual_raw'] = list(v)
                except StopIteration:
                    obj['consumed'] = True
            list_of_dfs.append(obj)
        return list_of_dfs

    def __synchronize_dataframes(self, list_of_dfs: List[dict], last_row: list) -> List[list]:
        rows = []
        c = 0
        while True:
            c += 1
            row = [] 
            feeding_next_timestamps = [df['actual_raw'][0] for df in list_of_dfs if df['trigger_feed'] == True and not df['consumed']]
            if len(feeding_next_timestamps) == 0:
                break
            min_timestamp = min(feeding_next_timestamps) 
            row.append(int(min_timestamp))
            for df_obj in list_of_dfs:
                while True:
                    if df_obj['actual_raw'][0] > min_timestamp:
                        row.append(df_obj['prev_raw'][1])
                        break
                    elif df_obj['actual_raw'][0] == min_timestamp:
                        row.append(df_obj['actual_raw'][1])
                        try:
                            df_obj['prev_raw'] = df_obj['actual_raw']
                            i, v = next(df_obj['rows_iterator'])
                            df_obj['actual_raw'] = list(v)
                        except StopIteration:
                            df_obj['consumed'] = True
                        break
                    else: 
                        try:
                            df_obj['prev_raw'] = df_obj['actual_raw']
                            i, v = next(df_obj['rows_iterator'])
                            df_obj['actual_raw'] = list(v)
                        except StopIteration:
                            row.append(df_obj['actual_raw'][1])
                            df_obj['consumed'] = True
                            break
            if len(last_row) == 0 or row[0] != last_row[0]:
                rows.append(row)
                # print(row)
        return rows
        
    def __load_data_frame_ticks(self, downloaded_data_path: str, last_row: list, files_array: list) -> List[list]:
        """
        Function is geting files array from one period that are going to be loaded. 
        Function returns synchronized data in list of lists which are ready to send to engine.
        """
        list_of_dfs = self.__prepare_dataframes_to_synchronize(downloaded_data_path, last_row, files_array)
        rows = self.__synchronize_dataframes(list_of_dfs, last_row)
        return rows

    def __load_data_frame_ticks_2(self, downloaded_data_path: str, last_row: list, files_array: List[InstrumentFile]) -> List[list]:
        """
        Function is geting files array from one period that are going to be loaded. 
        Function returns synchronized data in list of lists which are ready to send to engine.
        """
        list_of_dfs = self.__prepare_dataframes_to_synchronize_2(downloaded_data_path, last_row, files_array)
        rows = self.__synchronize_dataframes(list_of_dfs, last_row)
        return rows


    # COMMANDS
    
    async def __unlock_historical_sending_event(self):
        self.__sending_locked = False