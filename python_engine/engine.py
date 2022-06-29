
from abc import abstractmethod
import asyncio
import json
from typing import Callable, List
from libs.zmq.zmq import ZMQ


class Engine(ZMQ):
    # override

    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.register("data_feed", self.__data_feed)

    @abstractmethod
    def on_feed(data):
        pass

    # override
    def _loop(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._listen_zmq())
        # loop.create_task(self._test_loop())
        loop.create_task(self._heartbeat())
        loop.run_forever()
        loop.close()

    # override
    def _handle_zmq_message(self, message):
        pass

    def __data_feed(self, msg):
        self._log(f"Received data feed: {msg}")
        self.on_feed(msg)
        
    
    def _trigger_event(self, event):
        pass