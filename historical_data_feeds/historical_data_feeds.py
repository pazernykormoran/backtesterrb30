
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

class HistoricalDataFeeds(ZMQ):
    # override

    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.data_schema: DataSchema = import_module('strategies.'+self.config.strategy_name+'.data_schema').DATA
        self.register("data_feed", self.__data_feed)
        

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
        step_timestamp = self.__get_interval_stop_seconds(self.data_schema.interval)
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

    def __data_feed(self, msg):
        self._log(f"Received data feed: {msg}")

    def __get_interval_stop_seconds(self, interval: STRATEGY_INTERVALS):
        if interval == STRATEGY_INTERVALS.tick: return 9999999999
        if interval == STRATEGY_INTERVALS.second: return 1
        if interval == STRATEGY_INTERVALS.minute: return 60
        if interval == STRATEGY_INTERVALS.minute15: return 60*15
        if interval == STRATEGY_INTERVALS.minute30: return 60*30
        if interval == STRATEGY_INTERVALS.hour: return 60*60
        if interval == STRATEGY_INTERVALS.day: return 60*60*24
        if interval == STRATEGY_INTERVALS.week: return 60*60*24*7
        if interval == STRATEGY_INTERVALS.month: return 60*60*24*7*30
 
        """
            tick='tick'
            second='second'
            minute='minute'
            minute15='minute15'
            minute30='minute30'
            hour='hour'
            day='day'
            week='week'
            month='month'
        """
    
    def _trigger_event(self, event):
        pass