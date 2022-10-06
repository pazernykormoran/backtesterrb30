
from abc import abstractmethod
import asyncio
from typing import List, Union
from backtesterRB30.libs.interfaces.python_backtester.custom_chart import CustomChart
from backtesterRB30.libs.interfaces.python_backtester.data_finish import DataFinish 
from backtesterRB30.libs.interfaces.python_backtester.debug_breakpoint import DebugBreakpoint
from backtesterRB30.libs.interfaces.python_backtester.last_feed import LastFeed
from backtesterRB30.libs.interfaces.python_engine.custom_chart_element import CustomChartElement
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
from backtesterRB30.libs.zmq.zmq import ZMQ
from backtesterRB30.libs.utils.list_of_services import SERVICES
from backtesterRB30.libs.interfaces.utils.data_schema import DataSchema
from backtesterRB30.libs.utils.module_loaders import import_data_schema, import_spec_module, reload_spec_module
from backtesterRB30.libs.utils.json_serializable import JSONSerializable
import keyboard


class Engine(ZMQ):
    """Python Engine"""
    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.__data_schema: DataSchema = import_data_schema(self.config.strategy_path)
        self.__columns=['timestamp']+[c.symbol for c in self.__data_schema.data]
        self.__data_buffer = [ [] for col in self.__columns]
        for sym, arr in zip(self.__data_schema.data, self.__data_buffer[1:]):
            sym.additional_properties['buffer'] = arr
        self.__buffer_length = 100
        self.__custom_charts: List[CustomChart] = []
        self.__debug_mode = False
        self.__debug_next_pressed = False
        self.__reloading_modules = []
        self.__send_breakpoint_after_feed = False
        self.__code_stopped_debug = False

        super()._register("data_feed", self.__data_feed_event)
        super()._register("historical_sending_locked", self.__historical_sending_locked_event)
        super()._register("data_finish", self.__data_finish_event)

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
        :return: :class:`DataSymbol` object
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
        """Returns a list of instrument names based on all instruments in `DataSchema`.
        Do not use it as identifiers! Names can be the same in other data sources.

        :return: List of returned :class:`str` objects
        :rtype: list
        """
        return self.__columns


    def set_buffer_length(self, length: int):
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
        self.__buffer_length = length

 
    def trigger_event(self, event: JSONSerializable):

        self.__send_last_feed(SERVICES.python_executor)
        super()._send(SERVICES.python_executor,'event', event)
    

    def add_custom_chart(self, 
                    chart: List[CustomChartElement], 
                    name: str, 
                    display_on_price_chart: Union[bool, None] = None, 
                    log_scale: Union[bool, None] = None, 
                    color: Union[str, None] = None):

        chart_obj = {
            'chart': chart,
            'display_on_price_chart': display_on_price_chart,
            'name': name
        }
        if display_on_price_chart: chart_obj['display_on_price_chart'] = display_on_price_chart
        if log_scale: chart_obj['log_scale'] = log_scale
        if color: chart_obj['color'] = color
        self.__custom_charts.append(chart_obj)

    
    async def debug_breakpoint(self):

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

        spec, module = import_spec_module(module_path)
        self.__reloading_modules.append((spec, module))
        reload_spec_module(spec,module)
        return module

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
        loop.create_task(self.__keyboard_listener())
        loop.run_forever()
        loop.close()


    # override
    def _handle_zmq_message(self, message):
        pass


    def __send_last_feed(self, service: SERVICES):
        last_feed = {
            'last_feed': [v[-1] for v in self.__data_buffer]
        }
        super()._send(service, 'last_feed', LastFeed(**last_feed))


    def __send_debug_breakpoint(self):
        breakpoint_params= {}
        breakpoint_params['custom_charts'] = self.__custom_charts
        self._log('sending debug breakpoint')
        self.__send_last_feed(SERVICES.python_executor)
        super()._send(SERVICES.python_executor,'debug_breakpoint', DebugBreakpoint(**breakpoint_params))


    async def __keyboard_listener(self):
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
            await self.on_feed(self.__data_buffer)
            if self.__send_breakpoint_after_feed: 
                self.__send_debug_breakpoint()
                self.__send_breakpoint_after_feed = False
        
        
    async def __historical_sending_locked_event(self):
        super()._send(SERVICES.historical_data_feeds,'unlock_historical_sending')

    
    async def __data_finish_event(self):
        self.on_data_finish()
        self.__debug_mode = False
        finish_params = {}
        finish_params['custom_charts'] = self.__custom_charts
        # finish_params['main_instrument_price'] = self.__get_main_intrument_price()
        self.__send_last_feed(SERVICES.python_backtester)
        super()._send(SERVICES.python_backtester, 'data_finish', DataFinish(**finish_params))

