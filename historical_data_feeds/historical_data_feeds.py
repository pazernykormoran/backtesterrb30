
from abc import abstractmethod
import asyncio
from typing import Callable, List
from libs.zmq.zmq import ZMQ
from libs.list_of_services.list_of_services import SERVICES
from libs.data_feeds.data_feeds import STRATEGY_INTERVALS, HISTORICAL_SOURCES, DataSchema
from libs.interfaces.config import Config
from importlib import import_module
from json import dumps
from datetime import datetime
from os import path, mkdir, getenv
from os import listdir
from os.path import isfile, join
from binance import Client, AsyncClient
import pandas as pd

class HistoricalDataFeeds(ZMQ):
    
    downloaded_data_path = './data_historical_downloaded'

    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.data_schema: DataSchema = import_module('strategies.'+self.config.strategy_name+'.data_schema').DATA
        self.register("data_feed", self.__data_feed)
        binance_api_secret=getenv("binance_api_secret")
        binance_api_key=getenv("binance_api_key")
        self.client = Client(binance_api_key, binance_api_secret)
            
        # load add data?

    # override
    def run(self):
        
        super().run()

    # override
    def _loop(self):
        loop = asyncio.get_event_loop()

        # bofero starting loop you need to validate histroical data files
        self.validate_downloaded_data_folder()
        self.data_to_download =  self.check_if_all_data_exists(self.data_schema)
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
        while True:
            if self.data_downloaded(self.data_to_download): 
                self._log('All data has been downloaded!')
                timestamp = datetime.timestamp(self.data_schema.backtest_date_start)
                step_timestamp = self.__get_interval_step_seconds(self.data_schema.interval)

                
                for i in range(4):
                    
                    await asyncio.sleep(1)
                    self._log('')
                    self._log('historical data feeds sending some message')
                    self._send(SERVICES.python_engine,'data_feed','message from histroical data')
                    timestamp += step_timestamp
                await asyncio.sleep(1)
                
                finish_params = {
                    'main_instrument_price': 100
                }
                self._send(SERVICES.python_backtester, 'data_finish', dumps(finish_params))
                break
            else:
                await asyncio.sleep(1)

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
                                    + str(int(round(datetime.timestamp(datetime(data_schema.backtest_date_start.year,12,31)) * 1000))))
            for i in range(data_schema.backtest_date_stop.year - data_schema.backtest_date_start.year - 1):
                date_from_date_to.append(str(int(round(datetime.timestamp(datetime(data_schema.backtest_date_start.year + i + 1, 1, 1)) * 1000))) + "__" 
                                    + str(int(round(datetime.timestamp(datetime(data_schema.backtest_date_start.year + i + 1, 12, 31)) * 1000))))
            date_from_date_to.append(str(int(round(datetime.timestamp(datetime(data_schema.backtest_date_stop.year,1,1)) * 1000))) + "__" 
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
        return files_to_download

    def download_data(self, data_to_download, loop: asyncio.AbstractEventLoop):
        for instrument_file_name in data_to_download:
            data_instrument = instrument_file_name[:-4]
            source, instrment, interval, time_start, time_stop = tuple(data_instrument.split('__'))
            # print('data_splitted', source, instrment, interval, time_start, time_stop )
            if source == HISTORICAL_SOURCES.binance.value: 
                loop.create_task(self._download_binance_data(instrument_file_name, instrment, interval, int(time_start), int(time_stop)))
            if source == HISTORICAL_SOURCES.ducascopy.value: 
                loop.create_task(self._download_ducascopy_data(instrument_file_name, instrment, interval, int(time_start), int(time_stop)))
            if source == HISTORICAL_SOURCES.rb30disk.value: 
                loop.create_task(self._download_rb30_disk_data(instrument_file_name, instrment, interval, int(time_start), int(time_stop)))

        # if tick: get_aggregate_trades


    async def _download_binance_data(self, instrument_file_name:str, instrument: str, interval: str, time_start: int, time_stop: int):
        self._log('downloading binance data')
        binance_interval = self.__get_binance_interval(interval)
        klines = self.client.get_historical_klines(instrument, binance_interval, time_start, time_stop)
        df = pd.DataFrame(klines).iloc[:, [0,1]]
        self._log('BINANCE DATA LEN', len(df))
        df.to_csv(join(self.downloaded_data_path, instrument_file_name), index=False)

    async def _download_ducascopy_data(self, instrument_file_name:str, instrument: str, interval: str, time_start: int, time_stop: int):
        print('_download_ducascopy_data')
        pass

    async def _download_rb30_disk_data(self, instrument_file_name:str, instrument: str, interval: str, time_start: int, time_stop: int):
        # TODO
        print('_download_rb30_disk_data')
        pass

    def load_data(self, data_schema: DataSchema):
        pass

    def __get_interval_step_seconds(self, interval: STRATEGY_INTERVALS):
        if interval == STRATEGY_INTERVALS.tick: return 9999999999
        if interval == STRATEGY_INTERVALS.minute: return 60
        if interval == STRATEGY_INTERVALS.minute15: return 60*15
        if interval == STRATEGY_INTERVALS.minute30: return 60*30
        if interval == STRATEGY_INTERVALS.hour: return 60*60
        if interval == STRATEGY_INTERVALS.day: return 60*60*24
        if interval == STRATEGY_INTERVALS.week: return 60*60*24*7
        if interval == STRATEGY_INTERVALS.month: return 60*60*24*7*30
 
    def __get_binance_interval(self, interval: STRATEGY_INTERVALS):
        if interval == 'minute': return Client.KLINE_INTERVAL_1MINUTE
        if interval == 'minute15': return Client.KLINE_INTERVAL_15MINUTE
        if interval == 'minute30': return Client.KLINE_INTERVAL_30MINUTE
        if interval == 'hour': return Client.KLINE_INTERVAL_1HOUR
        if interval == 'day': return Client.KLINE_INTERVAL_1DAY
        if interval == 'week': return Client.KLINE_INTERVAL_1WEEK
        if interval == 'month': return Client.KLINE_INTERVAL_1MONTH

    def _trigger_event(self, event):
        pass

    # COMMANDS
    def __data_feed(self, msg):
        self._log(f"Received data feed: {msg}")