
from abc import abstractmethod
import asyncio
import json
from backtesterRB30.libs.interfaces.python_backtester.close_all_trades import CloseAllTrades
from backtesterRB30.libs.interfaces.python_backtester.debug_breakpoint import DebugBreakpoint
from backtesterRB30.libs.interfaces.python_backtester.trade import Trade
from backtesterRB30.libs.zmq.zmq import ZMQ

from backtesterRB30.libs.utils.list_of_services import SERVICES

class Executor(ZMQ):
    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.__event_price = 0
        self.__event_timestamp = 0
        self.__number_of_actions = 0

        super()._register("event", self.__event_event)
        super()._register("set_number_of_actions", self.__set_number_of_actions_event)
        super()._register("debug_breakpoint", self.__debug_breakpoint_event)

    # public methods:
    # ==================================================================

    @abstractmethod
    def on_event(self, message):
        self._log('method should be implemented in strategy function')
        pass


    def _trade(self, trade_quantity: float, price = None, timestamp = None) -> bool:
        if price == None: price = self.__event_price
        if timestamp == None: timestamp = self.__event_timestamp
        if self.config.backtest == True:
            trade_params = {
                'quantity': trade_quantity,
                'price': price,
                'timestamp': timestamp
            }
            super()._send(SERVICES.python_backtester, 'trade', Trade(**trade_params))
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
            
            super()._send(SERVICES.python_backtester, 'close_all_trades', CloseAllTrades(**close_all_trades_params))
        else:
            # TODO trade in real broker
            pass


    def _get_number_of_actions(self):
        return self.__number_of_actions

    # ==================================================================
    # end of public methods
    

    #private methods:

    def _send(): pass
    def _register(): pass
    def _create_listeners(): pass


    # override
    def _loop(self):
        loop = asyncio.get_event_loop()
        super()._create_listeners(loop)
        loop.run_forever()
        loop.close()


    # override
    def _handle_zmq_message(self, message):
        pass      


    #COMMANDS

    async def __event_event(self, msg):
        self.__event_price = msg['price']
        self.__event_timestamp = msg['timestamp']
        self.on_event(msg['message'])

    async def __set_number_of_actions_event(self, number: int):
        self.__number_of_actions = number

    async def __debug_breakpoint_event(self, breakpoint_params):
        super()._send(SERVICES.python_backtester, 'debug_breakpoint', DebugBreakpoint(**breakpoint_params))