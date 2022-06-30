
from abc import abstractmethod
from concurrent.futures import Executor

import asyncio
import json
from typing import Callable, List
from libs.zmq.zmq import ZMQ

class Executor(ZMQ):
    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.register("event", self.__event)

    @abstractmethod
    def on_event(self, message):
        self._log('method should be implemented in strategy function')
        pass

    # override
    def _loop(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._listen_zmq())
        loop.run_forever()
        loop.close()

    # override
    def _handle_zmq_message(self, message):
        self.on_event(message)

    def _trade(trade_value: float, direction: bool):
        pass

    def _close_all_trades():
        pass

    def __event(self):
        pass
