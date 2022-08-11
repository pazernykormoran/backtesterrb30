
from abc import abstractmethod
import asyncio
from typing import List
from libs.zmq.zmq import ZMQ
from libs.list_of_services.list_of_services import SERVICES, SERVICES_ARRAY
from libs.data_feeds.data_feeds import STRATEGY_INTERVALS, HISTORICAL_SOURCES, DataSchemaTicks, DataSymbolTicks
from historical_data_feeds.modules.binance import *
from historical_data_feeds.modules.dukascopy import *
from historical_data_feeds.modules.rb30_disk import *
from libs.interfaces.config import Config
from importlib import import_module
from json import dumps
from datetime import datetime, timezone
from os import path, mkdir, getenv
from os import listdir
from os.path import isfile, join
from binance import Client
import pandas as pd
from os import mkdir
import time

import time as tm

class HistoricalDataFeeds(ZMQ):
    
    downloaded_data_path = '/var/opt/data_historical_downloaded'

    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.__data_schema: DataSchemaTicks = import_module('strategies.'+self.config.strategy_name+'.data_schema').DATA
        self.__columns=['timestamp']+[c.symbol for c in self.__data_schema.data]

        if HISTORICAL_SOURCES.binance in [data.historical_data_source for data in self.__data_schema.data]:
            binance_api_secret=getenv("binance_api_secret")
            binance_api_key=getenv("binance_api_key")
            self.__client = Client(binance_api_key, binance_api_secret)
            
        self.sending_locked = False
        if not self.__validate_data_schema_instruments(self.__data_schema.data): 
            self.__stop_all_services()
        self.__validate_downloaded_data_folder()
        self.file_names_to_load, self.data_to_download =  self.__check_if_all_data_exists(self.__data_schema.data)
        if len(self.data_to_download) > 0:
            self.__download_data(self.data_to_download)
        self.data_parts = self.__prepare_loading_data_structure(self.file_names_to_load)

        # register commands
        self.register("unlock_historical_sending", self.__unlock_historical_sending_event)

    # override
    def _loop(self):
        loop = asyncio.get_event_loop()
        self._create_listeners(loop)
        loop.create_task(self.__historical_data_loop_ticks())
        loop.run_forever()
        loop.close()

    # override
    def _handle_zmq_message(self, message):
        pass

    async def __historical_data_loop_ticks(self):
        self._log('waiting for all ports starts up')
        await asyncio.sleep(0.5)

        if self.__data_downloaded(self.data_to_download): 
            self._log('All data has been downloaded')
            
            sending_counter = 0
            self._log('Starting data loop')
            start_time = tm.time()
            last_row = []
            for _, one_year_array in self.data_parts.items():
                data_part = self.__load_data_frame_ticks(self.downloaded_data_path, last_row, one_year_array)
                self._log('=================== datapart has finished')

                for row in data_part:
                    last_row = row
                    # self._send(SERVICES.python_engine,'data_feed',dumps(list(last_row)))
                    # sending_counter += 1
                    # if sending_counter % 1000 == 0:
                    #     self.sending_locked = True
                    #     self._send(SERVICES.python_engine, 'historical_sending_locked')
                    #     while self.sending_locked:
                    #         await asyncio.sleep(0.01)

            self._log('Data has finished')
            
            finish_params = {
                'file_names': self.file_names_to_load,
                'start_time': start_time
            }
            self._send(SERVICES.python_engine, 'data_finish', dumps(finish_params))

        else:
            self._log("Error. Not all of the data has been downloaded, exiting")
            self._stop()

    def __validate_data_schema_instruments(self, data_symbol_array: List[DataSymbolTicks]):
        self._log('Data_schema validation')
        data_valid = True
        number_of_mains = 0
        number_of_trigger_feeders = 0
        for data in data_symbol_array:
            if data.historical_data_source == HISTORICAL_SOURCES.binance:
                if not validate_binance_instrument(self.__client, data.symbol, data.backtest_date_start, data.interval):
                    data_valid = False
            elif data.historical_data_source == HISTORICAL_SOURCES.ducascopy:
                if not validate_ducascopy_instrument(data.symbol, data.backtest_date_start): 
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
            if data.historical_data_source.value not in (HISTORICAL_SOURCES.binance.value, HISTORICAL_SOURCES.ducascopy.value): 
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

    def __validate_downloaded_data_folder(self):
        if not path.exists(self.downloaded_data_path):
            mkdir(self.downloaded_data_path)
    
    def __check_if_all_data_exists(self, data_symbol_array: DataSymbolTicks):
        """
        data scheme
        <instrument>__<source>__<interval>__<date-from>__<date-to>
        all instruments are downloaded in year files.
        """
        file_names: List[str] = []
        loading_structure = []
        for instrument in data_symbol_array:
            files = self.__get_file_names(instrument)
            loading_structure.append(file_names)
            file_names = file_names+files
        print('file names', file_names)
        files_in_directory = [f for f in listdir(self.downloaded_data_path) if isfile(join(self.downloaded_data_path, f))]
        files_to_download = list(set(file_names) - set(files_in_directory))
        return file_names, files_to_download


    def __get_file_names(self, symbol: DataSymbolTicks) -> List[str]:
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


    def __download_data(self, data_to_download):
        for instrument_file_name in data_to_download:
            data_instrument = instrument_file_name[:-4]
            source, instrment, interval, time_start, time_stop = tuple(data_instrument.split('__'))
            # print('data_splitted', source, instrment, interval, time_start, time_stop )
            if source == HISTORICAL_SOURCES.binance.value: 
                download_binance_data(self.__client, self.downloaded_data_path, instrument_file_name, instrment, interval, int(time_start), int(time_stop))
            if source == HISTORICAL_SOURCES.ducascopy.value: 
                download_ducascopy_data(self.downloaded_data_path, instrument_file_name, instrment, interval, int(time_start), int(time_stop))
            if source == HISTORICAL_SOURCES.rb30disk.value: 
                download_rb30_disk_data(self.downloaded_data_path, instrument_file_name, instrment, interval, int(time_start), int(time_stop))
        # if tick: get_aggregate_trades


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

    def __stop_all_services(self):
        for service in SERVICES_ARRAY:
            if service != self.name:
                self._send(getattr(SERVICES, service), 'stop')
        self._stop()

    def __map_raw_to_instruments(self, raw: list, instruments: list):
        last_raw_obj = {}
        if len(raw) != len(instrument):
            self._log('Error in map_raw_to_instruments. Lengths of raw and list of instruments are not equal')
            self._stop()
        for value, instrument in zip(raw, instruments):
            last_raw_obj[instrument] = value

        
    def __load_data_frame_ticks(self, downloaded_data_path: str, last_row: list, files_array: list) -> List[list]:
        print('last raw loading', last_row)
        """
        Function is geting files array from one period that are going to be loaded. 
        Function returns synchronized data in list of lists which are ready to send to engine.

        """
        list_of_dfs = []
        for data_element in self.__data_schema.data:
            columns = ['timestamp', data_element.symbol]
            file_name = 'none'
            loading_index = 0
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
                    last_raw_mapped = self.__map_raw_to_instruments(last_row, self.__columns)
                    last_raw_df = pd.DataFrame([last_raw_mapped["timestamp"], last_raw_mapped[data_element.symbol]], columns = columns)
                    pd.concat([last_raw_df, df], axis=0, ignore_index=True)
                    loading_index = 1
            list_of_dfs.append({
                "loading_index": loading_index,
                "trigger_feed": data_element.trigger_feed,
                "df": df
            })


        self._log('list of dfs len', len(list_of_dfs))
        print( list_of_dfs)

        data_finish = False
        rows = []
        while data_finish == False:
            time.sleep(0.1)
            row = [] 
            number_of_finished_arrays = 0
            # Finding lowest next timestamp. This is going to be the timestamp of new row
            feeding_next_timestamps = [df['df'].iloc[df['loading_index'], 0] for df in list_of_dfs if (df['trigger_feed'] == True and not df['df'].empty)]
            if len(feeding_next_timestamps) == 0:
                break
            min_timestamp = min(feeding_next_timestamps) 
            row.append(min_timestamp)
            for df_obj in list_of_dfs:
                if not df_obj['df'].empty:
                    print('timestamp', df_obj['df'].iloc[df_obj['loading_index'], 0])
                if df_obj['df'].empty:
                    # Frame is empty.
                    self._log('empty')
                    row.append(0)
                    continue
                if df_obj['df'].shape[0] - 1 == df_obj['loading_index']:
                    # Loading_index od next frame is in the end of dataframe, 
                    # that means data in this dataframe has finished.
                    row.append(df_obj['df'].iloc[df_obj['loading_index'], 1])
                    number_of_finished_arrays += 1
                    if number_of_finished_arrays == len([df for df in list_of_dfs if df['trigger_feed'] == True]):
                        # Data in all dataframes that trigers feed has finished.
                        data_finish = True
                    continue
                if min_timestamp == df_obj['df'].iloc[df_obj['loading_index'], 0]:
                    # Value with calculated timestamp exists in this dataframe.
                    row.append(df_obj['df'].iloc[df_obj['loading_index'], 1])
                    df_obj['loading_index'] += 1
                else:
                    # Value with calculated timestamp not exists in this dataframe. It's bigger.
                    if df_obj['loading_index'] == 0:
                        # Previous data in this dataframe does not exists.
                        row.append(0)
                        continue
                    else:
                        # Append previous value
                        row.append(df_obj['df'].iloc[df_obj['loading_index']-1, 1])
                        df_obj['loading_index'] += 1
            print('row: ', row)
            rows.append(row)
        return rows


    # COMMANDS
    
    def __unlock_historical_sending_event(self):
        self.sending_locked = False