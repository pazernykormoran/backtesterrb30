
from abc import abstractmethod
from concurrent.futures import Executor

import asyncio
import json
from typing import Callable, List
from libs.zmq.zmq import ZMQ
import time

from libs.list_of_services.list_of_services import SERVICES

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
        self._create_listeners(loop)
        # loop.create_task(self._listen_zmq())
        loop.create_task(self.__broker_connection_monitor())
        loop.run_forever()
        loop.close()

    # override
    def _handle_zmq_message(self, message):
        pass        

    async def __broker_connection_monitor(self):
        while True:
            await asyncio.sleep(5)
            if self.config.backtest == False:
                print('broker connection monitor')
            # self._log('trade executor sending some message')
            # self._send(SERVICES.python_engine,'message from trade executor')

    def _trade(self, trade_quantity: float, price: float):
        trade_params = {
            'quantity': trade_quantity,
            'price': price,
            'timestamp': time.time()
        }
        if self.config.backtest == True:
            self._send(SERVICES.python_backtester,'trade', json.dumps(trade_params))
        else:
            # TODO trade in real broker
            pass

    def _close_all_trades():
        pass

    def __event(self, data):
        msg = json.loads(data)
        self.on_event(msg)
        pass
