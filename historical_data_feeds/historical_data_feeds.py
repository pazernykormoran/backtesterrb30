
from abc import abstractmethod
import asyncio
from typing import Callable, List
from libs.zmq.zmq import ZMQ
from libs.list_of_services.list_of_services import SERVICES
from libs.data_feeds.data_feeds import STRATEGY_INTERVALS, HISTORICAL_SOURCES, DataSchema
from libs.interfaces.config import Config
from importlib import import_module
from json import dumps
from datetime import datetime, timezone
from os import path, mkdir, getenv
from os import listdir
from os.path import isfile, join
from binance import Client, AsyncClient
import pandas as pd
from os import system, remove
import shutil


class HistoricalDataFeeds(ZMQ):
    
    downloaded_data_path = '/var/opt/data_historical_downloaded'

    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.data_schema: DataSchema = import_module('strategies.'+self.config.strategy_name+'.data_schema').DATA
        
        binance_api_secret=getenv("binance_api_secret")
        binance_api_key=getenv("binance_api_key")
        self.client = Client(binance_api_key, binance_api_secret)
        self.sending_locked = False
    
        self.register("unlock_historical_sending", self.__unlock_historical_sending)

    # override
    def run(self):
        
        super().run()

    # override
    def _loop(self):
        loop = asyncio.get_event_loop()

        # bofero starting loop you need to validate histroical data files
        self.validate_downloaded_data_folder()
        self.file_names_to_load, self.data_to_download =  self.check_if_all_data_exists(self.data_schema)
        if len(self.data_to_download) > 0:
            self.download_data(self.data_to_download, loop)
        self._create_listeners(loop)
        # loop.create_task(self._listen_zmq())
        loop.create_task(self.__historical_data_loop())
        loop.run_forever()
        loop.close()

    # override
    def _handle_zmq_message(self, message):
        pass

    async def __historical_data_loop(self):
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
                for time, array in data_parts.items():

                    data_part = self.__load_data_frame(array)
                    for index, row in data_part.iterrows():

                        self._send(SERVICES.python_engine,'data_feed',dumps(list(row)))
                        sending_counter += 1
                        if sending_counter % 1000 == 0:
                            self.sending_locked = True
                            self._send(SERVICES.python_engine, 'historical_sending_locked')
                            while self.sending_locked:
                                await asyncio.sleep(0.01)
                            # self._log('historical sendig unlocked')

                self._log('Data has finished')
                
                finish_params = {
                    'file_names': self.file_names_to_load
                }
                self._send(SERVICES.python_engine, 'data_finish', dumps(finish_params))
                break
            else:
                print("Error. Not all of the data has been downloaded, exiting")
                self._stop()

    def data_downloaded(self, full_data_to_download):
        files_in_directory = [f for f in listdir(self.downloaded_data_path) if isfile(join(self.downloaded_data_path, f))]
        data_to_download = list(set(full_data_to_download) - set(files_in_directory))
        # self._log('Data is being downloaded ...', str( (len(full_data_to_download) - len(data_to_download) ) / len(full_data_to_download) * 100 )+'%')
        return data_to_download == []

    def validate_downloaded_data_folder(self):
        if not path.exists(self.downloaded_data_path):
            mkdir(self.downloaded_data_path)

    def get_next_value(self):
        pass

    def validate_loaded_data(self):
        pass
    
    def check_if_all_data_exists(self, data_schema: DataSchema):
        """
        data scheme
        <instrument>__<source>__<interval>__<date-from>__<date-to>
        all instruments are downloaded in year files.

        #TODO write tests
        """
        date_from_date_to: List[str] = []
        file_names: List[str] = []
        if data_schema.backtest_date_start.year < data_schema.backtest_date_stop.year:
            date_from_date_to.append(str(int(round(datetime.timestamp(data_schema.backtest_date_start) * 1000))) + "__"
                                    + str(int(round(datetime.timestamp(datetime(data_schema.backtest_date_start.year+1,1,1, tzinfo=timezone.utc)) * 1000))))
            for i in range(data_schema.backtest_date_stop.year - data_schema.backtest_date_start.year - 1):
                date_from_date_to.append(str(int(round(datetime.timestamp(datetime(data_schema.backtest_date_start.year + i + 1, 1, 1, tzinfo=timezone.utc)) * 1000))) + "__" 
                                    + str(int(round(datetime.timestamp(datetime(data_schema.backtest_date_start.year + i + 2, 1, 1, tzinfo=timezone.utc)) * 1000))))
            date_from_date_to.append(str(int(round(datetime.timestamp(datetime(data_schema.backtest_date_stop.year,1,1, tzinfo=timezone.utc)) * 1000))) + "__" 
                                    + str(int(round(datetime.timestamp(data_schema.backtest_date_stop) * 1000))))
        else:
            date_from_date_to.append(str(int(round(datetime.timestamp(data_schema.backtest_date_start) * 1000))) + "__" 
                                    + str(int(round(datetime.timestamp(data_schema.backtest_date_stop) * 1000))))
        for instrument in data_schema.data:
            for dates in date_from_date_to:
                file_names.append(instrument.historical_data_source.value + "__" 
                                    + instrument.symbol + "__" 
                                    + data_schema.interval.value + "__" 
                                    + dates + '.csv')
        # print('file_names', file_names)
        files_in_directory = [f for f in listdir(self.downloaded_data_path) if isfile(join(self.downloaded_data_path, f))]
        # print('files_in_directory',files_in_directory)
        files_to_download = list(set(file_names) - set(files_in_directory))
        # print('files_to_download', files_to_download)
        return file_names, files_to_download

    def download_data(self, data_to_download, loop: asyncio.AbstractEventLoop):
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


    def _download_binance_data(self, instrument_file_name:str, instrument: str, interval: str, time_start: int, time_stop: int):
        self._log('downloading binance data', instrument_file_name)
        binance_interval = self.__get_binance_interval(interval)
        klines = self.client.get_historical_klines(instrument, binance_interval, time_start, time_stop)
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
            files_collection[time_start].append([instrument, instrument_file_name])
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
                    self._log('Error! Length of loading data parts is not equal. Name of file:', file[1])
                    self._stop()
        return array_of_arrays
        

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
    
    def __unlock_historical_sending(self):
        self.sending_locked = False