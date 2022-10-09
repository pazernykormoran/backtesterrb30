
from abc import abstractmethod
import asyncio
import json
from backtesterRB30.libs.communication_broker.broker_base import BrokerBase
from backtesterRB30.libs.interfaces.python_backtester.debug_breakpoint import DebugBreakpoint
from backtesterRB30.libs.interfaces.python_backtester.last_feed import LastFeed
from backtesterRB30.libs.interfaces.python_backtester.trade import Trade
from backtesterRB30.libs.interfaces.python_executor.executor_position import ExecutorPosition
from backtesterRB30.libs.interfaces.utils.data_schema import DataSchema
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
from backtesterRB30.libs.communication_broker.zmq_broker import ZMQ
from backtesterRB30.libs.communication_broker.asyncio_broker import AsyncioBroker
from typing import List
from backtesterRB30.libs.utils.service import Service
from backtesterRB30.libs.utils.list_of_services import SERVICES
from backtesterRB30.libs.interfaces.utils.config import BROKERS, Config 

class Executor(Service):
    """Python Trade executor"""
    _broker: BrokerBase
    
    def __init__(self, config: Config, data_schema: DataSchema, loop = None, logger=print):
        super().__init__(config, logger)
        self.config: Config=config
        self.__loop =  loop
        self.__custom_event_loop = False
        if self.__loop == None: 
            self.__loop = asyncio.get_event_loop()
            self.__custom_event_loop= True
        self.__data_schema: DataSchema = data_schema
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


    # public methods:
    # ==================================================================

    @abstractmethod
    async def on_event(self, message):
        """Function is being called when :class:`Model` class triggers 
        `trigger_event()` function. 

        :param message: message defined in `model.py` in strategy files.
        :type message: Any
        """
        self._log('method should be implemented in strategy function')
        pass

    def get_data_schema(self):
        """Returns data_schema defined in your strategy files in `data_schema.py`
        Data schema contains list of :class:`DataSymbol` objects. In every :class:`DataSymbol` object, 
        you can use `get_buffer()` function to get current buffer connected to this symbol.

        :return: :class:`DataSchema` object combined with this strategy.
        :rtype: DataSchema
        """
        return self.__data_schema

    def get_data_symbol_by_custom_name(self, custom_name: str):
        """Returns a :class:`DataSymbol` object using `custom_name` defined
        in `data_schema.py`, `custom_name` must be unique.

        :param custom_name: custom name defined in `data_schema.py` file.
        :type custom_name: str
        :return: :class:`DataSymbol` object combined with privided custom_name
        :rtype: DataSymbol
        """
        if type(custom_name) != str:
            raise Exception('Provided name is not string')
        arr = [d for d in self.__data_schema.data if d.custom_name == custom_name]
        if len(arr) == 0:
            raise Exception('No data symbol with such custom name')
        if len(arr) >1 : 
            raise Exception('Two elements with the same custom name')
        return arr[0]


    async def trade(self, trade_value: float, data_symbol: DataSymbol, price: float = None, timestamp: int = None):
        """Triggers trade.

        :param trade_value: value of trade in dollars.
        :type trade_value: float
        :param data_symbol: :class:`DataSymbol` on which trade is going to be made.
        :type data_symbol: DataSymbol
        :param price: price of trade. Default is current price. Works only in backtest mode.
        :type price: float, optional
        :param timestamp: timestamp of trade. Default is current timestamp. Works only in backtest mode.
        :type timestamp: int, optional
        """
        if not price and not timestamp:
            price = 0 
            timestamp = 0
        if price and not timestamp or timestamp and not price:
            raise Exception('Provide both price and timestamp or none of them.')
        if trade_value > self.__start_amout_of_usd + self.__current_capital - self.__current_invested:
            raise Exception('To big amout of trade')
        if self.config.backtest:
            trade_params = {
                'value': trade_value,
                'price': price,
                'timestamp': timestamp,
                'symbol': data_symbol.symbol,
                'source': data_symbol.historical_data_source
            }
            await self._broker.send(SERVICES.python_backtester, 'trade', Trade(**trade_params))
            return True
        else:
            self._log('Live trading not implemented')
            pass


    async def close_all_trades(self):
        """Closes all opened trades.
        """
        if self.config.backtest == True:
            await self._broker.send(SERVICES.python_backtester, 'close_all_trades')
        else:
            # TODO trade in real broker
            pass


    # def _get_number_of_actions(self):
    #     return self.__number_of_actions

    # ==================================================================
    # end of public methods
    

    #private methods:

    # def _send(): pass
    # def _register(): pass
    # def _create_listeners(): pass

    def _loop(self):
        # self._broker.run()
        self._broker.create_listeners(self.__loop)
        if self.__custom_event_loop:
            self.__loop.run_forever()
            self.__loop.close()

    # def _send(self, service: SERVICES, msg: str, *args):
    #     self._broker.send(service, msg, *args)

    def _configure(self):
        super()._configure()
        self._broker.register("event", self.__event_event)
        # super()._register("set_number_of_actions", self.__set_number_of_actions_event)
        self._broker.register("set_current_capital_event", self.__set_current_capital_event)
        self._broker.register("set_current_invested_event", self.__set_current_invested_event)
        self._broker.register("debug_breakpoint", self.__debug_breakpoint_event)
        self._broker.register("last_feed", self.__last_feed_event)

    # # override
    # def _asyncio_loop(self, loop: asyncio.AbstractEventLoop):
    #     self._broker.create_listeners(loop)

    # # override
    # def _handle_zmq_message(self, message):
    #     pass      


    #COMMANDS

    async def __event_event(self, msg):
        await self.on_event(msg)

    # async def __set_number_of_actions_event(self, number: int):
    #     self.__number_of_actions = number

    async def __set_current_capital_event(self, number: int):
        self.__current_capital = number
    
    async def __set_current_invested_event(self, number: int):
        self.__current_invested = number

    async def __debug_breakpoint_event(self, breakpoint_params):
        await self._broker.send(SERVICES.python_backtester, 'debug_breakpoint', DebugBreakpoint(**breakpoint_params))

    async def __last_feed_event(self, msg):
        await self._broker.send(SERVICES.python_backtester, 'last_feed',LastFeed(**msg))