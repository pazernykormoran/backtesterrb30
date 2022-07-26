
from abc import abstractmethod
import asyncio
from typing import Callable, List
from libs.zmq.zmq import ZMQ
from libs.list_of_services.list_of_services import SERVICES
from libs.data_feeds.data_feeds import STRATEGY_INTERVALS, HISTORICAL_SOURCES, DataSchemaTicks, DataSymbolTicks
from libs.interfaces.config import Config
from importlib import import_module
from json import dumps, load
from datetime import datetime, timezone
from os import path, mkdir, getenv
from os import listdir
from os.path import isfile, join
from binance import Client, AsyncClient
import pandas as pd
from os import system, remove, mkdir
import shutil
import time as tm

class HistoricalDataFeeds(ZMQ):
    
    downloaded_data_path = '/var/opt/data_historical_downloaded'

    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.data_schema: DataSchemaTicks = import_module('strategies.'+self.config.strategy_name+'.data_schema').DATA
        try:
            mkdir(self.downloaded_data_path)
        except:
            pass
        if HISTORICAL_SOURCES.binance in [data.historical_data_source for data in self.data_schema.data]:
            binance_api_secret=getenv("binance_api_secret")
            binance_api_key=getenv("binance_api_key")
            self.client = Client(binance_api_key, binance_api_secret)
        self.sending_locked = False

        
        self.register("unlock_historical_sending", self.__unlock_historical_sending_event)

    # override
    def _loop(self):
        loop = asyncio.get_event_loop()

        if not self.validate_data_schema_instruments(self.data_schema): 
            self._stop()
        self.validate_downloaded_data_folder()
        self.file_names_to_load, self.data_to_download =  self.check_if_all_data_exists(self.data_schema)
        if len(self.data_to_download) > 0:
            self.download_data(self.data_to_download)
        self._create_listeners(loop)
        # loop.create_task(self._listen_zmq())
        loop.create_task(self.__historical_data_loop_ticks())
        loop.run_forever()
        loop.close()

    # override
    def _handle_zmq_message(self, message):
        pass

    # async def __historical_data_loop(self):
    #     self._log('waiting for all ports starts up')
    #     await asyncio.sleep(0.5)
    #     while True:
    #         if self.data_downloaded(self.data_to_download): 
    #             self._log('All data has been downloaded')
    #             # timestamp = datetime.timestamp(self.data_schema.backtest_date_start)
    #             # step_timestamp = self.__get_interval_step_seconds(self.data_schema.interval)
    #             data_parts = self.prepare_loading_data_structure(self.file_names_to_load)
    #             sending_counter = 0
    #             self._log('Starting data loop')
    #             start_time = tm.time()
    #             for time, array in data_parts.items():

    #                 data_part = self.__load_data_frame(array)
    #                 for index, row in data_part.iterrows():

    #                     self._send(SERVICES.python_engine,'data_feed',dumps(list(row)))
    #                     sending_counter += 1
    #                     if sending_counter % 1000 == 0:
    #                         self.sending_locked = True
    #                         self._send(SERVICES.python_engine, 'historical_sending_locked')
    #                         while self.sending_locked:
    #                             await asyncio.sleep(0.01)
    #                         # self._log('historical sendig unlocked')

    #             self._log('Data has finished')
                
    #             finish_params = {
    #                 'file_names': self.file_names_to_load,
    #                 'start_time': start_time
    #             }
    #             self._send(SERVICES.python_engine, 'data_finish', dumps(finish_params))
    #             break
    #         else:
    #             print("Error. Not all of the data has been downloaded, exiting")
    #             self._stop()

    async def __historical_data_loop_ticks(self):
        self._log('waiting for all ports starts up')
        await asyncio.sleep(0.5)
        while True:
            if self.data_downloaded(self.data_to_download): 
                self._log('All data has been downloaded')
                # timestamp = datetime.timestamp(self.data_schema.backtest_date_start)
                # step_timestamp = self.__get_interval_step_seconds(self.data_schema.interval)
                data_parts = self.prepare_loading_data_structure(self.file_names_to_load)
                sending_counter = 0
                self._log('Starting data loop')
                start_time = tm.time()
                last_row = []
                for time, array in data_parts.items():

                    data_part = self.__load_data_frame_ticks(last_row, array)
                    for index, row in data_part.iterrows():
                        last_row = row
                        self._send(SERVICES.python_engine,'data_feed',dumps(list(last_row)))
                        sending_counter += 1
                        if sending_counter % 1000 == 0:
                            self.sending_locked = True
                            self._send(SERVICES.python_engine, 'historical_sending_locked')
                            while self.sending_locked:
                                await asyncio.sleep(0.01)
                            # self._log('historical sendig unlocked')

                self._log('Data has finished')
                
                finish_params = {
                    'file_names': self.file_names_to_load,
                    'start_time': start_time
                }
                self._send(SERVICES.python_engine, 'data_finish', dumps(finish_params))
                break
            else:
                print("Error. Not all of the data has been downloaded, exiting")
                self._stop()

    def validate_data_schema_instruments(self, data_schema: DataSchemaTicks):
        self._log('Data_schema validation')
        data_valid = True
        for data in data_schema.data:
            if data.historical_data_source == HISTORICAL_SOURCES.binance:
                if not self.validate_binance_instrument(data.symbol, data.backtest_date_start, data.interval):
                    data_valid = False
            elif data.historical_data_source == HISTORICAL_SOURCES.ducascopy:
                if not self.validate_ducascopy_instrument(data.symbol, data.backtest_date_start): 
                    data_valid = False
        return data_valid


    def validate_binance_instrument(self, instrument: str, from_datetime: datetime, interval: STRATEGY_INTERVALS):
        # print('validation instrment', instrument, 'from_datetime', from_datetime, 'interval',interval)
        #validate if instrument exists:
        exchange_info = self.client.get_exchange_info()
        if instrument not in [s['symbol'] for s in exchange_info['symbols']]:
            self._log('Error. Instrument "'+instrument+'" does not exists on binance.')
            return False
        #validate it timestamps perios is right:
        from_datetime_timestamp = int(round(datetime.timestamp(from_datetime) * 1000))
        binance_interval = self.__get_binance_interval(interval.value)
        first_timestamp = self.client._get_earliest_valid_timestamp(instrument, binance_interval)
        if first_timestamp > from_datetime_timestamp:
            self._log("Error. First avaliable date of " , instrument, "is" , datetime.fromtimestamp(first_timestamp/1000.0))
            return False
        return True

    def validate_ducascopy_instrument(self, instrument: str, from_datetime: datetime):
        # https://raw.githubusercontent.com/Leo4815162342/dukascopy-node/master/src/utils/instrument-meta-data/generated/raw-meta-data-2022-04-23.json
        # response = requests.get("http://api.open-notify.org/astros.json")
        from_datetime_timestamp = int(round(datetime.timestamp(from_datetime) * 1000))
        f = open('historical_data_feeds/temporary_ducascopy_list.json')
        instrument_list = load(f)['instruments']
        #validate if instrument exists:
        if instrument.upper() not in [v['historical_filename'] for k, v in instrument_list.items()]:
            self._log('Error. Instrument "'+instrument+'" does not exists on ducascopy.')
            return False

        #validate it timestamps perios is right:
        for k, v in instrument_list.items():
            if v["historical_filename"] == instrument.upper():
                first_timestamp = int(v["history_start_day"])
                if first_timestamp > from_datetime_timestamp:
                    self._log("Error. First avaliable date of " , instrument, "is" , datetime.fromtimestamp(first_timestamp/1000.0))
                    return False
        return True

    def data_downloaded(self, full_data_to_download):
        files_in_directory = [f for f in listdir(self.downloaded_data_path) if isfile(join(self.downloaded_data_path, f))]
        data_to_download = list(set(full_data_to_download) - set(files_in_directory))
        # self._log('Data is being downloaded ...', str( (len(full_data_to_download) - len(data_to_download) ) / len(full_data_to_download) * 100 )+'%')
        return data_to_download == []

    def validate_downloaded_data_folder(self):
        if not path.exists(self.downloaded_data_path):
            mkdir(self.downloaded_data_path)

    def get_next_value(self):
        return False

    def validate_loaded_data(self):
        pass
    
    def check_if_all_data_exists(self, data_schema: DataSchemaTicks):
        """
        data scheme
        <instrument>__<source>__<interval>__<date-from>__<date-to>
        all instruments are downloaded in year files.
        """
        file_names: List[str] = []
        loading_structure = []
        for instrument in data_schema.data:
            files = self.__get_file_names(instrument)
            loading_structure.append(file_names)
            file_names = file_names+files
        print('file names', file_names)
        files_in_directory = [f for f in listdir(self.downloaded_data_path) if isfile(join(self.downloaded_data_path, f))]
        files_to_download = list(set(file_names) - set(files_in_directory))
        return file_names, files_to_download

    def download_data(self, data_to_download):
        for instrument_file_name in data_to_download:
            data_instrument = instrument_file_name[:-4]
            source, instrment, interval, time_start, time_stop = tuple(data_instrument.split('__'))
            # print('data_splitted', source, instrment, interval, time_start, time_stop )
            if source == HISTORICAL_SOURCES.binance.value: 
                self._download_binance_data(instrument_file_name, instrment, interval, int(time_start), int(time_stop))
            if source == HISTORICAL_SOURCES.ducascopy.value: 
                self._download_ducascopy_data(instrument_file_name, instrment, interval, int(time_start), int(time_stop))
            if source == HISTORICAL_SOURCES.rb30disk.value: 
                self._download_rb30_disk_data(instrument_file_name, instrment, interval, int(time_start), int(time_stop))

        # if tick: get_aggregate_trades

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

    def _download_binance_data(self, instrument_file_name:str, instrument: str, interval: str, time_start: int, time_stop: int):
        self._log('downloading binance data', instrument_file_name)
        binance_interval = self.__get_binance_interval(interval)
        klines = self.client.get_historical_klines(instrument, binance_interval, time_start, time_stop)
        if len(klines) == 0:
            self._log('Error. Klines downloaded has len = 0. Check if',instrument,'has not been deleted from the exachange.')
            self._stop()
        df = pd.DataFrame(klines).iloc[:-1, [0,1]]
        self._log('downloaded data length', df.shape[0])
        df = self.validate_dataframe_timestamps(df, interval, time_start, time_stop)
        self._log('data length after validation', df.shape[0])
        df.to_csv(join(self.downloaded_data_path, instrument_file_name), index=False, header=False)


    def _download_ducascopy_data(self, instrument_file_name:str, instrument: str, interval: str, time_start: int, time_stop: int):
        self._log('_download_ducascopy_data', instrument_file_name)
        """
        documentation: 
        https://github.com/Leo4815162342/dukascopy-node
        """
        duca_interval = self.__get_ducascopy_interval(interval)
        from_param = datetime.fromtimestamp(time_start//1000.0).strftime("%Y-%m-%d")
        to_param = datetime.fromtimestamp(time_stop//1000.0).strftime("%Y-%m-%d")
        string_params = [
            ' -i '+ instrument,
            ' -from '+ from_param,
            ' -to '+ to_param,
            ' -s',
            ' -t ' + duca_interval,
            ' -fl', 
            ' -f csv',
            ' -dir ./cache' 
        ]
        command = 'npx dukascopy-node'
        for param in string_params:
            command += param
        print('running command', command)
        system(command)
        name_of_created_file = instrument+'-'+duca_interval+'-bid-'+from_param+'-'+to_param+'.csv'
        shutil.move('./cache/'+name_of_created_file, join(self.downloaded_data_path, instrument_file_name))
        df = pd.read_csv(join(self.downloaded_data_path, instrument_file_name), index_col=None, header=None)
        df = df.iloc[1:, [0,1]]
        self._log('downloaded data length', df.shape[0])
        remove(join(self.downloaded_data_path, instrument_file_name))
        df = self.validate_dataframe_timestamps(df, interval, time_start, time_stop)
        self._log('data length after validation', df.shape[0])
        df.to_csv(join(self.downloaded_data_path, instrument_file_name), index=False, header=False)
        

    def _download_rb30_disk_data(self, instrument_file_name:str, instrument: str, interval: str, time_start: int, time_stop: int):
        # TODO
        print('_download_rb30_disk_data')
        pass

    def prepare_loading_data_structure(self, file_names_to_load):
        files_collection = {}
        for instrument_file_name in file_names_to_load:
            
            data_instrument = instrument_file_name[:-4]
            source, instrument, interval, time_start, time_stop = tuple(data_instrument.split('__'))
            if not time_start in files_collection:
                files_collection[time_start] = []
            for symbol in self.data_schema.data:
                if instrument == symbol.symbol:
                    trigger_feed = symbol.trigger_feed
                    if trigger_feed == None:
                        trigger_feed = False
                    files_collection[time_start].append([instrument, instrument_file_name, trigger_feed])
                    break
        print('lading files collection', files_collection)
        return files_collection


    def __load_data_frame(self, files_array: list):
        array_of_arrays = pd.DataFrame()
        for file in files_array:
            df = pd.read_csv(join(self.downloaded_data_path, file[1]), index_col=None, header=None, names=['timestamp', file[0]])
            if len(array_of_arrays) == 0:
                array_of_arrays = df
            else:
                if(array_of_arrays.shape[0] == df.shape[0]):
                    array_of_arrays[file[0]] = df.iloc[:, [1]]
                else:
                    self._log('Error! Length of loading data parts is not equal. Name of file:', file[1], str(array_of_arrays.shape[0]) , "!=", str(df.shape[0]))
                    self._stop()
        return array_of_arrays
        
    def __load_data_frame_ticks(self, last_row: list, files_array: list):
        array_of_arrays = pd.DataFrame()
        list_of_dfs = []
        # load dfs
        for i, file in enumerate(files_array):
            df = pd.read_csv(join(self.downloaded_data_path, file[1]), index_col=None, header=None, names=['timestamp', file[0]])
            loading_index = 0
            # append last raw it if exists
            if last_row != []:
                pd.concat([last_row, df], axis=0, ignore_index=True)
                loading_index = 1

            list_of_dfs.append({
                "loading_index": loading_index,
                "trigger_feed": file[2],
                "df": df
            })

        print('list of dfsh len', len(list_of_dfs))

        data_finish = False
        rows = []
        while data_finish == False:
            arr = []
            
            # find lowest next timestamp
            min_timestamp = min([df['df'].iloc[df['loading_index'], 0] for df in list_of_dfs if (df['trigger_feed'] == True and not df['df'].empty)]) 
            arr.append(min_timestamp)
            for df_obj in list_of_dfs:
                number_of_finished_arrays = 0
                if df_obj['df'].empty:
                    #handle if all frame is empty.
                    arr.append(0)
                    continue
                if df_obj['df'].shape[0] == df_obj['loading_index']:
                    #handle if loading_index od next frame is in the end of dataframe.
                    arr.append(df_obj['df'].iloc[df_obj['loading_index'], 1])
                    number_of_finished_arrays += 1
                    if number_of_finished_arrays == len(list_of_dfs):
                        data_finish = True
                    continue
                if min_timestamp== df_obj['df'].iloc[df_obj['loading_index'], 0]:
                    #handle if new timestamp of next frame equals minimal next timestamp.
                    arr.append(df_obj['df'].iloc[df_obj['loading_index'], 1])
                    df_obj['loading_index'] += 1
                else:
                    #handle if next timestamp is not equal (bigger) than minimal timestamp.
                    if df_obj['loading_index'] == 0:
                        # situation where previous data not exists.
                        arr.append(0)
                        continue
                    arr.append(df_obj['df'].iloc[df_obj['loading_index']-1, 1])
                    df_obj['loading_index'] += 1
            print('row: ', arr)
            rows.append(arr)

            #TODO

    def __get_interval_step_miliseconds(self, interval: str):
        if interval == STRATEGY_INTERVALS.minute.value: return 60*1000
        if interval == STRATEGY_INTERVALS.minute15.value: return 60*15*1000
        if interval == STRATEGY_INTERVALS.minute30.value: return 60*30*1000
        if interval == STRATEGY_INTERVALS.hour.value: return 60*60*1000
        if interval == STRATEGY_INTERVALS.day.value: return 60*60*24*1000
        # if interval == 'minute15': return 60*60*24*7
        if interval == STRATEGY_INTERVALS.month.value: return 60*60*24*7*30*1000
 

    def __get_binance_interval(self, interval: str):
        if interval == 'minute': return Client.KLINE_INTERVAL_1MINUTE
        if interval == 'minute15': return Client.KLINE_INTERVAL_15MINUTE
        if interval == 'minute30': return Client.KLINE_INTERVAL_30MINUTE
        if interval == 'hour': return Client.KLINE_INTERVAL_1HOUR
        if interval == 'day': return Client.KLINE_INTERVAL_1DAY
        # if interval == 'week': return Client.KLINE_INTERVAL_1WEEK
        if interval == 'month': return Client.KLINE_INTERVAL_1MONTH


    def __get_ducascopy_interval(self, interval: str):
        if interval == 'minute': return 'm1'
        if interval == 'minute15': return 'm15'
        if interval == 'minute30': return 'm30'
        if interval == 'hour': return 'h1'
        if interval == 'day': return 'd1'
        # if interval == 'week': return 'm1'
        if interval == 'month': return 'mn1'


    def validate_dataframe_timestamps(self, df: pd.DataFrame, interval: str, time_start: int, time_stop: int):
        # print('starting validation: ', 'interval',interval , 'time_start',time_start , 'time_stop', time_stop)
        # print('-start in file name', datetime.fromtimestamp(time_start / 1000))
        # print('-stop in file name', datetime.fromtimestamp(time_stop / 1000))
        # print('is dividable???' ,( time_stop - time_start )/ timestamp_interval)
        # print('list timestamps first: ', list_timestamps[0], 'last: ', list_timestamps[-1])
        # print('-start in list', datetime.fromtimestamp(list_timestamps[0] / 1000))
        # print('-stop in list', datetime.fromtimestamp(list_timestamps[-1] / 1000))
        # print('proper len', len(list_timestamps))
        # print('head', df.head(2))
        # print('tail', df.tail(2))
        # print(df.dtypes)
        # print('iterating------')
        timestamp_interval = self.__get_interval_step_miliseconds(interval)
        list_timestamps = range(time_start, time_stop, timestamp_interval)
        for i, timestamp in enumerate(list_timestamps):
            count = 0
            while int(df.iloc[i][0]) != int(timestamp):
                count+= 1
                df = pd.concat([df.iloc[:i],df.iloc[i-1:i],df.iloc[i:]], ignore_index=True)
                df.iloc[i,0] = int(timestamp)

        for i, timestamp in enumerate(list_timestamps):
            if int(df.iloc[i][0]) != int(timestamp):
                self._log('Error during second validation of data. Timestamps are not equal. Stopping')
                self._stop()

        if df.shape[0] != len(list_timestamps):
            self._log('Error. Data frame length is not proper after validation. Check "validate_dataframe_timestamps" function')
            self._stop()
        return df


    # COMMANDS
    
    def __unlock_historical_sending_event(self):
        self.sending_locked = False