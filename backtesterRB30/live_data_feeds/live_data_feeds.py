
from abc import abstractmethod
import asyncio
from backtesterRB30.libs.communication_broker.broker_base import BrokerBase
from backtesterRB30.libs.interfaces.historical_data_feeds.instrument_file import InstrumentFile
from backtesterRB30.libs.interfaces.utils.data_schema import DataSchema
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
from backtesterRB30.libs.data_sources.data_source_base import DataSource
from backtesterRB30.libs.communication_broker.zmq_broker import ZMQ
from backtesterRB30.libs.data_sources.data_sources_list import HISTORICAL_SOURCES
from backtesterRB30.libs.utils.list_of_services import SERVICES
from backtesterRB30.historical_data_feeds.functions import load_data_frame_with_dfs
from backtesterRB30.libs.utils.service import Service
from backtesterRB30.libs.utils.timestamps import timestamp_to_datetime
from backtesterRB30.libs.interfaces.utils.config import Config, BROKERS
from os import getenv
from datetime import datetime
import time
from appdirs import user_cache_dir

class LiveDataFeeds(Service):
    """Python Live data provider"""

    downloaded_data_path = user_cache_dir('rb30_cache')
    _broker: BrokerBase
    
    def __init__(self, config: dict, data_schema: DataSchema, loop = None, logger=print):
        super().__init__(config, logger)
        self.config: Config=config
        self.__loop =  loop
        self.__custom_event_loop = False
        if self.__loop == None: 
            self.__loop = asyncio.get_event_loop()
            self.__custom_event_loop= True
        self.__data_schema: DataSchema = data_schema
        self.__columns=['timestamp']+[c.symbol for c in self.__data_schema.data]
        self.__historical_sources_array = [i for i in dir(HISTORICAL_SOURCES) if not i.startswith('__')]
        self.__data_sources = {}
        self.__download_buffer = True
        self.__engine_ready = False
        self.__historical_rows = []

    # override
    def _loop(self):
        self._broker.create_listeners(self.__loop)
        # TODO add data downloader
        if not self.config.backtest:
            self.__create_downloading_clients(self.__historical_sources_array, self.__data_schema, self.__data_sources, self._log)
            self.__combine_clients_and_symbols(self.__data_schema)
            interval = self.__find_loop_interval(self.__data_schema)
            self.__loop.create_task(self.__main_loop(interval))
        if self.__custom_event_loop:
            self.__loop.run_forever()
            self.__loop.close()

    def _configure(self):
        super()._configure()
        self._broker.register("engine_set_buffer_length", self.__engine_set_buffer_length_event)

    # def _send(self, service: SERVICES, msg: str, *args):
    #     self._broker.send(service, msg, *args)

    # # override
    # def _handle_zmq_message(self, message):
    #     pass 

    async def __main_loop(self, interval):
        if self.__download_buffer == True:
            await self._broker.send(SERVICES.python_engine, 'get_buffer_length', SERVICES.live_data_feeds.value)
        else:
            self.__engine_ready = True
        while True:
            if self.__engine_ready:
                timestamp = await self.__get_proper_timestamp(self.__historical_rows, self.__data_schema)
                for row in self.__historical_rows:
                    last_row = row
                    await self._broker.send(SERVICES.python_engine,'data_feed',list(last_row))
                while True:
                    row = []
                    row.append(timestamp)
                    sth_updated = False
                    for data_symbol in self.__data_schema.data:
                        price, updated = self.__get_symbol_price(timestamp, data_symbol)
                        if updated: sth_updated = True
                        row.append(price)
                    if sth_updated: 
                        await self._broker.send(SERVICES.python_engine,'data_feed',row)
                    await asyncio.sleep(interval/1000)
                    timestamp += interval
            await asyncio.sleep(2)

    def __get_smallest_interval(self, data_schema: DataSchema):
        smallest = 9999999999999
        for data_symbol in data_schema.data:
            client: DataSource = data_symbol.additional_properties['downloading_client']
            milis = client._get_interval_miliseconds(data_symbol.interval.value)
            if not milis or not (1000*60 <= milis <= 1000*60*60*24*6 ):
                raise Exception(data_symbol.symbol, 'Cant run live with this interval')
            if milis < smallest:
                smallest = milis
        return smallest

    async def __download_data(self, buffer_length: int, data_schema: DataSchema):
        buffer_length = buffer_length
        smallest = self.__get_smallest_interval(data_schema)
        time_stop = int(time.time()) * 1000 + smallest
        time_start = time_stop - 4 * smallest * buffer_length
        if time_stop - time_start < 1000*60*60*24: 
            time_start = time_stop - 1000*60*60*24
        dfs = []
        for data_symbol in data_schema.data:
            client: DataSource = data_symbol.additional_properties['downloading_client']
            df = await client.download_dataframe(
                    data_symbol.symbol,
                    data_symbol.interval.value,
                    time_start,
                    None)
            df.columns = ['timestamp', data_symbol.identifier]
            dfs.append(df)
        self.__historical_rows = load_data_frame_with_dfs(self.__data_schema, self.__columns, [], dfs)
        self.__historical_rows= self.__historical_rows[-buffer_length-1:]

    async def __get_proper_timestamp(self, historical_rows, data_schema: DataSchema):
        if historical_rows == []:
            return time.time() * 1000
        smallest = self.__get_smallest_interval(data_schema)
        current_time_with_reserve = time.time()*1000 + 1000
        next_should_be_timestamp = historical_rows[-1][0] + smallest
        if next_should_be_timestamp < current_time_with_reserve: 
            raise Exception('Did not managed to download historical buffer this time. Trying again')
        await asyncio.sleep(abs(next_should_be_timestamp - time.time()* 1000)/1000)
        return next_should_be_timestamp

    def __find_loop_interval(self, data_schema: DataSchema) -> int:
        smallest = self.__get_smallest_interval(data_schema)
        for data_symbol in data_schema.data:
            client: DataSource = data_symbol.additional_properties['downloading_client']
            milis = client._get_interval_miliseconds(data_symbol.interval.value)
            num = (milis / smallest ) % 1000
            if int(num) != num:
                raise Exception('Bad intervals... All intervals should be divisible by smallest one.')
        return smallest

    def __get_symbol_price(self, timestamp: int, symbol: DataSymbol):
        updated = False
        price = 0
        client: DataSource = symbol.additional_properties['downloading_client']
        if not 'last_price_timestamp' in symbol.additional_properties:
            symbol.additional_properties['last_price_timestamp'] = timestamp
            updated = True
        if not 'last_price' in symbol.additional_properties:
            symbol.additional_properties['last_price'] = client.get_current_price(symbol)
            updated = True
        milis = client._get_interval_miliseconds(symbol.interval.value)
        if timestamp - symbol.additional_properties['last_price_timestamp'] < milis:
            price = symbol.additional_properties['last_price']
        if timestamp - symbol.additional_properties['last_price_timestamp'] == milis:
            price = client.get_current_price(symbol)
            symbol.additional_properties['last_price_timestamp'] = timestamp
            symbol.additional_properties['last_price'] = price
            updated = True
        if timestamp - symbol.additional_properties['last_price_timestamp'] > milis:
            raise Exception('Error. Bad timestamp Such situation should not happen')
        return price, updated


    def __create_downloading_clients(self, historical_sources_array: list, data_schema: DataSchema, data_sources: dict, log = print):
        for source in historical_sources_array:
            if source in [data.historical_data_source for data in data_schema.data]:
                data_sources[source]: DataSource = getattr(HISTORICAL_SOURCES, source)(log)
            

    def __combine_clients_and_symbols(self, data_schema: DataSchema):
        for data_symbol in data_schema.data:
            data_symbol.additional_properties['downloading_client'] = self.__get_data_source_client(data_symbol.historical_data_source)

    def __get_data_source_client(self, historical_source: str) -> DataSource:
        client = self.__data_sources[historical_source]
        if not client:
                raise Exception('Error, no registered source client')
        return client
        
    #COMMANDS

    async def __engine_set_buffer_length_event(self, buffer_length: int):
        self.__buffer_length = buffer_length
        await self.__download_data(buffer_length, self.__data_schema)
        self.__engine_ready = True