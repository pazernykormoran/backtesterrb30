
from abc import abstractmethod
import asyncio
import json
from backtesterRB30.libs.interfaces.python_backtester.debug_breakpoint import DebugBreakpoint
from backtesterRB30.libs.interfaces.python_backtester.last_feed import LastFeed
from backtesterRB30.libs.interfaces.python_backtester.trade import Trade
from backtesterRB30.libs.interfaces.python_executor.executor_position import ExecutorPosition
from backtesterRB30.libs.interfaces.utils.data_schema import DataSchema
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
from backtesterRB30.libs.utils.module_loaders import import_data_schema
from backtesterRB30.libs.zmq.zmq import ZMQ
from typing import List

from backtesterRB30.libs.utils.list_of_services import SERVICES

class Executor(ZMQ):
    """Python Trade executor"""
    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.__data_schema: DataSchema = import_data_schema(self.config.strategy_path)
        self.__columns=['timestamp']+[c.symbol for c in self.__data_schema.data]
        # self.__event_price = 0
        # self.__event_timestamp = 0
        # self.__event_last_feed = []
        # self.__number_of_actions = 0
        self.__current_capital = 0
        self.__current_invested = 0
        self.__start_amout_of_usd = 10000
        
        self.__positions: List[ExecutorPosition] = [{
            'instrument': 'inst',
            'number_of_actions': 123,
            'current_value': 12
        }]

        super()._register("event", self.__event_event)
        # super()._register("set_number_of_actions", self.__set_number_of_actions_event)
        super()._register("set_current_capital_event", self.__set_current_capital_event)
        super()._register("set_current_invested_event", self.__set_current_invested_event)
        super()._register("debug_breakpoint", self.__debug_breakpoint_event)
        super()._register("last_feed", self.__last_feed_event)


    # public methods:
    # ==================================================================

    @abstractmethod
    def on_event(self, message):
        """Returns a list containing :class:`bluepy.btle.Characteristic`
        objects for the peripheral. If no arguments are given, will return all
        characteristics. If startHnd and/or endHnd are given, the list is
        restricted to characteristics whose handles are within the given range.

        :param startHnd: Start index, defaults to 1
        :type startHnd: int, optional
        :param endHnd: End index, defaults to 0xFFFF
        :type endHnd: int, optional
        :param uuids: a list of UUID strings, defaults to None
        :type uuids: list, optional
        :return: List of returned :class:`bluepy.btle.Characteristic` objects
        :rtype: list
        """
        self._log('method should be implemented in strategy function')
        pass

    def get_data_schema(self):
        return self.__data_schema

    def get_data_symbol_by_custom_name(self, custom_name: str):
        if type(custom_name) != str:
            raise Exception('Provided name is not string')
        arr = [d for d in self.__data_schema.data if d.custom_name == custom_name]
        if len(arr) == 0:
            raise Exception('No data symbol with such custom name')
        if len(arr) >1 : 
            raise Exception('Two elements with the same custom name')
        return arr[0]


    def trade(self, trade_value: float, data_symbol: DataSymbol, price = None, timestamp = None) -> bool:
        if not price and not timestamp:
            price = 0 
            timestamp = 0
        if price and not timestamp or timestamp and not price:
            raise Exception('Provide both price and timestamp or none of them.')
        if trade_value > self.__start_amout_of_usd + self.__current_capital - self.__current_invested:
            raise Exception('To big amout of trade')
        if self.config.backtest == True:
            trade_params = {
                'value': trade_value,
                'price': price,
                'timestamp': timestamp,
                'symbol': data_symbol.symbol,
                'source': data_symbol.historical_data_source
            }
            super()._send(SERVICES.python_backtester, 'trade', Trade(**trade_params))
            return True
        else:
            # TODO trade in real broker
            pass


    def close_all_trades(self):
        if self.config.backtest == True:
            super()._send(SERVICES.python_backtester, 'close_all_trades')
        else:
            # TODO trade in real broker
            pass


    # def _get_number_of_actions(self):
    #     return self.__number_of_actions

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
        self.on_event(msg)

    # async def __set_number_of_actions_event(self, number: int):
    #     self.__number_of_actions = number

    async def __set_current_capital_event(self, number: int):
        self.__current_capital = number
    
    async def __set_current_invested_event(self, number: int):
        self.__current_invested = number

    async def __debug_breakpoint_event(self, breakpoint_params):
        super()._send(SERVICES.python_backtester, 'debug_breakpoint', DebugBreakpoint(**breakpoint_params))

    async def __last_feed_event(self, msg):
        super()._send(SERVICES.python_backtester, 'last_feed',LastFeed(**msg))