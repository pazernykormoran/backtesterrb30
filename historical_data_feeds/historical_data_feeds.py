
from abc import abstractmethod
import asyncio
from typing import Callable, List
from libs.zmq.zmq import ZMQ
from libs.list_of_services.list_of_services import SERVICES
from libs.data_feeds.data_feeds import DataSchema
from libs.interfaces.config import Config
from importlib import import_module
from json import dumps

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
        loop.create_task(self.__some_loop())
        loop.run_forever()
        loop.close()

    async def __some_loop(self):
        for i in range(4):
            await asyncio.sleep(1)
            self._log('')
            self._log('historical data feeds sending some message')
            self._send(SERVICES.python_engine,'data_feed','message from histroical data')
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

        
    
    def _trigger_event(self, event):
        pass