
from abc import abstractmethod
import asyncio
from typing import Callable, List
from libs.zmq.zmq import ZMQ
from libs.list_of_services.list_of_services import SERVICES
from libs.data_feeds.data_feeds import DataSchema
from libs.data_feeds.data_feeds import STRATEGY_INTERVALS
from libs.interfaces.config import Config
from importlib import import_module
from json import dumps
from datetime import datetime
from os import path, mkdir

class HistoricalDataFeeds(ZMQ):
    
    downloaded_data_path = './data_historical_downloaded'

    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.data_schema: DataSchema = import_module('strategies.'+self.config.strategy_name+'.data_schema').DATA
        self.register("data_feed", self.__data_feed)
        self.historical_data = []

        self.validate_downloaded_data_folder()
        data_exists, data_to_download =  self.check_if_all_data_exists(self.data_schema)
        if not data_exists:
            self.download_data(data_to_download)
        self.load_data(self.data_schema)
            
        # load add data?

    # override
    def _loop(self):
        loop = asyncio.get_event_loop()
        self._create_listeners(loop)
        # loop.create_task(self._listen_zmq())
        loop.create_task(self.__historical_data_loop())
        loop.run_forever()
        loop.close()

    async def __historical_data_loop(self):
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

    # override
    def _handle_zmq_message(self, message):
        pass

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
        <instrument>__<interval>_<date-from>_<date-to>
        all instruments are downloaded in year files.

        function returns 
        """
        date_from_date_to: List[str] = []
        file_names: List[str] = []
        if data_schema.backtest_date_start.year < data_schema.backtest_date_stop.year:
            date_from_date_to.append(data_schema.backtest_date_start.strftime('%Y-%m-%d')+"_"+str(data_schema.backtest_date_start.year)+"-12-31")
            for i in range(data_schema.backtest_date_stop.year - data_schema.backtest_date_start.year - 1):
                date_from_date_to.append(str(data_schema.backtest_date_start.year + i + 1)+"-01-01" + "_" + str(data_schema.backtest_date_start.year + i + 1)+"-12-31")
            date_from_date_to.append(str(data_schema.backtest_date_stop.year)+"-01-01" + "_" + data_schema.backtest_date_stop.strftime('%Y-%m-%d'))
        else:
            date_from_date_to.append(data_schema.backtest_date_start.strftime('%Y-%m-%d') + "_" + data_schema.backtest_date_stop.strftime('%Y-%m-%d'))
        for instrument in data_schema.data:
            for dates in date_from_date_to:
                file_names.append(str(instrument.symbol) + "_" + str(data_schema.interval.value) + "_" + dates)
        print('file names: ', file_names)
        #TODO
        return True, file_names

    def download_data(self, data_schema: DataSchema):
        pass

    def load_data(self, data_schema: DataSchema):
        pass

    def __get_interval_step_seconds(self, interval: STRATEGY_INTERVALS):
        if interval == STRATEGY_INTERVALS.tick: return 9999999999
        if interval == STRATEGY_INTERVALS.second: return 1
        if interval == STRATEGY_INTERVALS.minute: return 60
        if interval == STRATEGY_INTERVALS.minute15: return 60*15
        if interval == STRATEGY_INTERVALS.minute30: return 60*30
        if interval == STRATEGY_INTERVALS.hour: return 60*60
        if interval == STRATEGY_INTERVALS.day: return 60*60*24
        if interval == STRATEGY_INTERVALS.week: return 60*60*24*7
        if interval == STRATEGY_INTERVALS.month: return 60*60*24*7*30
 

    def _trigger_event(self, event):
        pass

    # COMMANDS
    def __data_feed(self, msg):
        self._log(f"Received data feed: {msg}")