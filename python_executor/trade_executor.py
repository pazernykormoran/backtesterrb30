
from abc import abstractmethod
import asyncio
import json
from libs.interfaces.python_backtester.close_all_trades import CloseAllTrades
from libs.interfaces.python_backtester.trade import Trade
from libs.zmq.zmq import ZMQ

from libs.list_of_services.list_of_services import SERVICES

class Executor(ZMQ):
    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.__event_price = 0
        self.__event_timestamp = 0
        self.__number_of_actions = 0

        self.register("event", self.__event_event)
        self.register("set_number_of_actions", self.__set_number_of_actions_event)


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

    def _trade(self, trade_quantity: float, price = None, timestamp = None) -> bool:
        if price == None: price = self.__event_price
        if timestamp == None: timestamp = self.__event_timestamp
        if self.config.backtest == True:
            trade_params = {
                'quantity': trade_quantity,
                'price': price,
                'timestamp': timestamp
            }
            self._send(SERVICES.python_backtester, 'trade', Trade(**trade_params))
            return True
        else:
            # TODO trade in real broker
            pass

    def _close_all_trades(self):
        if self.config.backtest == True:
            close_all_trades_params = {
                'price': self.__event_price,
                'timestamp': self.__event_timestamp
            }
            
            self._send(SERVICES.python_backtester, 'close_all_trades', CloseAllTrades(**close_all_trades_params))
        else:
            # TODO trade in real broker
            pass

    def _get_number_of_actions(self):
        return self.__number_of_actions

    #COMMANDS

    def __event_event(self, msg):
        self.__event_price = msg['price']
        self.__event_timestamp = msg['timestamp']
        self.on_event(msg['message'])

    def __set_number_of_actions_event(self, number: int):
        self.__number_of_actions = number