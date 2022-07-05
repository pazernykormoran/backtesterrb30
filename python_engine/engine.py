
from abc import abstractmethod
import asyncio
import json
from typing import Callable, List
from libs.zmq.zmq import ZMQ
from libs.list_of_services.list_of_services import SERVICES
import pandas as pd
from libs.data_feeds.data_feeds import DataSchema
from importlib import import_module


class Engine(ZMQ):
    # override

    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.data_schema: DataSchema = import_module('strategies.'+self.config.strategy_name+'.data_schema').DATA

        self.data_buffer = pd.DataFrame(columns=['timestamp']+[c.symbol for c in self.data_schema.data])

        self.register("data_feed", self.__data_feed)

    @abstractmethod
    def on_feed(data):
        pass

    # override
    def _loop(self):
        loop = asyncio.get_event_loop()
        # loop.create_task(self._listen_zmq())
        self._create_listeners(loop)
        loop.create_task(self.__some_loop())
        loop.run_forever()
        loop.close()

    async def __some_loop(self):
        while True:
            await asyncio.sleep(2)
            # self._log('somethind')

    # override
    def _handle_zmq_message(self, message):
        pass

    def __data_feed(self, new_data_row):
        self.data_buffer.loc[len(self.data_buffer)]=new_data_row
        self.on_feed(self.data_buffer)
        
    
    def _trigger_event(self, event):
        self._send(SERVICES.python_executor,'event',json.dumps(event))
