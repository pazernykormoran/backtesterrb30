
from abc import abstractmethod
import asyncio
from typing import Callable, List
from libs.zmq.zmq import ZMQ
from libs.list_of_services.list_of_services import SERVICES

class HistoricalDataFeeds(ZMQ):
    # override

    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
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
        while True:
            await asyncio.sleep(5)
            self._log('historical data feeds sending some message')
            self._send(SERVICES.python_engine,'data_feed','message from histroical data')

    # override
    def _handle_zmq_message(self, message):
        print('handle message in data feeds')
        pass

    def __data_feed(self, msg):
        self._log(f"Received data feed: {msg}")

        
    
    def _trigger_event(self, event):
        pass