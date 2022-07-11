
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
        self.__data_schema: DataSchema = import_module('strategies.'+self.config.strategy_name+'.data_schema').DATA
        self.__columns=['timestamp']+[c.symbol for c in self.__data_schema.data]
        # self.__data_buffer = pd.DataFrame(self.__columns)
        self.__data_buffer = []
        self.__buffer_length = 100

        self.register("data_feed", self.__data_feed)
        self.register("historical_sending_locked", self.__historical_sending_locked)

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

    def _set_buffer_length(self, length: int):
        self.__buffer_length = length

    def _trigger_event(self, event):
        self._send(SERVICES.python_executor,'event',json.dumps(event))

    #COMMANDS
    # def __data_feed(self, new_data_row):
    #     new_data_row = json.loads(new_data_row)
    #     if self.__data_buffer.shape[0]>self.__buffer_length:
    #         self.__data_buffer.drop(self.__data_buffer.head(1).index,inplace=True)
    #     # self.__data_buffer.loc[self.__data_buffer.shape[0]]=new_data_row
    #     self.__data_buffer.append({k:v for k, v in zip(new_data_row, self.__columns)}, ignore_index=True)
    #     self.on_feed(self.__data_buffer)

    def __data_feed(self, new_data_row):
        new_data_row = json.loads(new_data_row)
        self.__data_buffer.append(new_data_row)
        if len(self.__data_buffer)>self.__buffer_length:
            self.__data_buffer.pop(0)
            self.on_feed(self.__data_buffer)
        
        
    def __historical_sending_locked(self):
        self._send(SERVICES.historical_data_feeds,'unlock_historical_sending')

