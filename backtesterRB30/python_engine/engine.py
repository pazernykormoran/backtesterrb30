
from abc import abstractmethod
import asyncio
from typing import List, Union
from backtesterRB30.libs.communication_broker.broker_base import BrokerBase
from backtesterRB30.libs.interfaces.python_backtester.custom_chart import CustomChart
from backtesterRB30.libs.interfaces.python_backtester.data_finish import DataFinish 
from backtesterRB30.libs.interfaces.python_backtester.debug_breakpoint import DebugBreakpoint
from backtesterRB30.libs.interfaces.python_backtester.last_feed import LastFeed
from backtesterRB30.libs.interfaces.python_engine.custom_chart_element import CustomChartElement
from backtesterRB30.libs.interfaces.python_engine.price_event import PriceEvent
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
from backtesterRB30.libs.communication_broker.zmq_broker import ZMQ
from backtesterRB30.libs.communication_broker.asyncio_broker import AsyncioBroker
from backtesterRB30.libs.utils.list_of_services import SERVICES
from backtesterRB30.libs.interfaces.utils.data_schema import DataSchema
from backtesterRB30.libs.utils.module_loaders import import_spec_module, reload_spec_module
from backtesterRB30.libs.utils.json_serializable import JSONSerializable
from backtesterRB30.libs.utils.service import Service
from backtesterRB30.libs.interfaces.utils.config import Config, BROKERS



class Engine(Service):
    """Python Engine"""
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
        self.__data_buffer = [ [] for col in self.__columns]
        for sym, arr in zip(self.__data_schema.data, self.__data_buffer[1:]):
            sym.additional_properties['buffer'] = arr
            sym.additional_properties['price_events'] = []
        self.__buffer_length = 1
        self.__custom_charts: List[CustomChart] = []
        self.__debug_mode = False
        self.__debug_next_pressed = False
        self.__reloading_modules = []
        self.__send_breakpoint_after_feed = False
        self.__code_stopped_debug = False
        self.__breakpoint_display_charts = True

    # public methods:
    # ==================================================================

    @abstractmethod
    async def on_feed(self, data):
        """Function is being called when new data frame appears.
        While defining strategy you have to override this function
        and define your strategy logic here. 

        :param data: data buffer defined in :class:`DataSchema`
        :type data: list
        """
        pass

    def on_data_finish(self):
        """Function is being called in backtest mode when historical data are finished
        """
        pass


    def get_data_schema(self) -> DataSchema:
        """Returns data_schema defined in your strategy files in `data_schema.py`
        Data schema contains list of :class:`DataSymbol` objects. In every :class:`DataSymbol` object, 
        you can use `get_buffer()` function to get current buffer connected to this symbol.

        :return: :class:`DataSchema` object combined with this strategy.
        :rtype: DataSchema
        """
        return self.__data_schema


    def get_data_symbol_by_custom_name(self, custom_name: str) -> DataSymbol:
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


    def get_columns(self) -> List[str]:
        """Returns a list of instrument names based on all instruments in :class:`DataSchema`.
        Do not use it as identifiers! Names can be the same in other data sources.

        :return: List of returned :class:`str` objects
        :rtype: list
        """
        return self.__columns


    def set_buffer_length(self, length: int):
        """Sets data buffer length. Data provided to `on_feed()` function
        is going to have this length.

        :param length: buffer length
        :type length: int
        """
        if length < 1: 
            raise Exception('Buffer length must be bigget than 1')
        # if self.config.backtest == False and length > 1:
        #     raise Exception('Buffer longer than 1 not implemended in live mode')
        self.__buffer_length = length

 
    async def trigger_event(self, event: JSONSerializable):
        """Calling this function, you trigger `on_event()` function in 
        :class:`TradeExecutor`. You can provide any JSON serializable input
        to this method. 

        :param event: any JSON serializable data
        :type event: JSONSerializable
        """
        await self.__send_last_feed(SERVICES.python_executor)
        await self._broker.send(SERVICES.python_executor,'event', event)
    

    def add_custom_chart(self, 
                    chart: List[CustomChartElement], 
                    name: str, 
                    display_on_price_chart: Union[DataSymbol, None] = None, 
                    log_scale: Union[bool, None] = None, 
                    color: Union[str, None] = None):
        """Function adds custom chart printed under main charts in summary
        or in breakpoint debug event.

        :param chart: list of :class:`CustomChartElement`
        :type chart: list
        :param name: name of your custom name
        :type name: str
        :param display_on_price_chart: determining if chart is going to be displayed on other chart (on privided :class:`DataSymbol` chart) or it is going to be displayed alone
        :type display_on_price_chart: DataSymbol, optional
        :param log_scale: determines if chart is going to be in log scale
        :type log_scale: bool, optional
        :param color: a list of UUID strings, defaults to None
        :type color: str, optional
        """
        chart_obj = {
            'chart': chart,
            'display_on_price_chart': display_on_price_chart,
            'name': name
        }
        if display_on_price_chart: chart_obj['display_on_price_chart'] = display_on_price_chart
        if log_scale: chart_obj['log_scale'] = log_scale
        if color: chart_obj['color'] = color
        self.__custom_charts.append(chart_obj)

    
    async def debug_breakpoint(self, display_charts = True):
        """This function causes breakpoint triggered while you turn on debug mode.

        :param display_charts: determines if breakpoint should cause displaying charts
        :type display_charts: bool, optional
        """   
        self.__breakpoint_display_charts = display_charts
        if self.__debug_mode == True:
            self.__code_stopped_debug = True
            while True:
                if self.__debug_mode == False:
                    for spec, module in self.__reloading_modules:
                        # reload(module)
                        reload_spec_module(spec, module)
                        # spec.loader.exec_module(module)

                        # module = SourceFileLoader('strategies.hackaton1.reloading_module.reloading_methods', '/home/george/workspace/project/Retire-Before-30/Engine-RB30/strategies/hackaton1/reloading_module/reloading_methods.py')

                    self.__code_stopped_debug = False
                    return
                if self.__debug_next_pressed == True:
                    for spec, module in self.__reloading_modules:
                        # reload(module)
                        reload_spec_module(spec, module)
                        spec.loader.exec_module(module)
                        # module = SourceFileLoader('strategies.hackaton1.reloading_module.reloading_methods', '/home/george/workspace/project/Retire-Before-30/Engine-RB30/strategies/hackaton1/reloading_module/reloading_methods.py')

                    self.__debug_next_pressed = False
                    self.__send_breakpoint_after_feed = True
                    self.__code_stopped_debug = False
                    return 
                await asyncio.sleep(0.1)


    def add_reloading_module(self, module_path: str):
        """Adds module that is going to be reloaded 
        every step of your debug. Module must not save any state
        because while realoading this state is going to be refreshed.

        :param module_path: path to module
        :type module_path: str
        """
        spec, module = import_spec_module(module_path)
        self.__reloading_modules.append((spec, module))
        reload_spec_module(spec,module)
        return module

    # ==================================================================
    # end of public methods
    

    #private methods:

    def _loop(self):
        # self._broker.run()
        self._broker.create_listeners(self.__loop)
        if self.config.debug == True:
            self.__loop.create_task(self.__keyboard_listener())
        if self.__custom_event_loop:
            self.__loop.run_forever()
            self.__loop.close()

    # def _send(self, service: SERVICES, msg: str, *args):
    #     self._broker.send(service, msg, *args)

    def _configure(self):
        super()._configure()
        self._broker.register("data_feed", self.__data_feed_event)
        self._broker.register("historical_sending_locked", self.__historical_sending_locked_event)
        self._broker.register("data_finish", self.__data_finish_event)
        self._broker.register("engine_ready", self.__engine_ready_event)
        self._broker.register("get_buffer_length", self.__get_buffer_length_event)
        self._broker.register("register_price_event", self.__register_price_event)

    # def _send(): pass
    # def _register(): pass
    # def _create_listeners(): pass


    # # override
    # def _asyncio_loop(self, loop: asyncio.AbstractEventLoop):
    #     self._broker._create_listeners(loop)
    #     loop.create_task(self.__keyboard_listener())

    # # override
    # def _handle_zmq_message(self, message):
    #     pass


    async def __send_last_feed(self, service: SERVICES):
        last_feed = {
            'last_feed': [v[-1] for v in self.__data_buffer]
        }
        await self._broker.send(service, 'last_feed', LastFeed(**last_feed))


    async def __send_debug_breakpoint(self):
        breakpoint_params= {}
        breakpoint_params['custom_charts'] = self.__custom_charts
        breakpoint_params['display_charts'] = self.__breakpoint_display_charts 
        self._log('sending debug breakpoint')
        await self.__send_last_feed(SERVICES.python_executor)
        await self._broker.send(SERVICES.python_executor,'debug_breakpoint', DebugBreakpoint(**breakpoint_params))


    async def __keyboard_listener(self):
        import keyboard
        self._log('To enter debug mode press "ctrl+d"')
        while True:
            if keyboard.is_pressed('ctrl+d'): 
                if self.__debug_mode == False:
                    self._log('You have entered Debug mode \n\
                                 -> press "ctrl+n" to next step\n\
                                 -> press "ctrl+q" to leave debug mode')
                    self.__debug_mode = True
                while keyboard.is_pressed('d'):
                    await asyncio.sleep(0.1)
            if keyboard.is_pressed('ctrl+n'):
                if self.__debug_mode == True and self.__debug_next_pressed == False and self.__code_stopped_debug:
                    self._log('next step ... \n\
                                -> press "ctrl+q" to leave debug mode')
                    self.__debug_next_pressed = True
                while keyboard.is_pressed('n'):
                    await asyncio.sleep(0.1)
            if keyboard.is_pressed('ctrl+q'):
                if self.__debug_mode == True:
                    self._log('You have leaved Debug mode \n\
                                -> press "ctrl+d" to enter debug mode again')
                    self.__debug_mode = False
                while keyboard.is_pressed('q'):
                    await asyncio.sleep(0.1)
            await asyncio.sleep(0.1)


    #COMMANDS

    async def __data_feed_event(self, new_data_row):
        for i, v in enumerate(new_data_row):
            self.__data_buffer[i].append(v)
        if len(self.__data_buffer[0])>self.__buffer_length:
            for i, v in enumerate(new_data_row):
                self.__data_buffer[i].pop(0)
        if len(self.__data_buffer[0])>=self.__buffer_length:
            await self.on_feed(self.__data_buffer)
            if self.__send_breakpoint_after_feed: 
                await self.__send_debug_breakpoint()
                self.__send_breakpoint_after_feed = False

        
        
    async def __historical_sending_locked_event(self):
        await self._broker.send(SERVICES.historical_data_feeds,'unlock_historical_sending')

    
    async def __data_finish_event(self):
        self.on_data_finish()
        self.__debug_mode = False
        finish_params = {}
        finish_params['custom_charts'] = self.__custom_charts
        # finish_params['main_instrument_price'] = self.__get_main_intrument_price()
        await self.__send_last_feed(SERVICES.python_backtester)
        await self._broker.send(SERVICES.python_backtester, 'data_finish', DataFinish(**finish_params))

    async def __engine_ready_event(self, service_name):
        await self._broker.send(SERVICES[service_name], 'engine_ready_response')

        
    async def __get_buffer_length_event(self, service_name):
        await self._broker.send(SERVICES[service_name], 'engine_set_buffer_length', self.__buffer_length)


    async def __register_price_event(self, price_event):
        price_event = PriceEvent(**price_event)
        symbol: DataSymbol = [data for data in self.__data_schema.data if data.identifier == \
                price_event.symbol_itentifier][0]
        symbol.additional_properties['price_events'].append(price_event)