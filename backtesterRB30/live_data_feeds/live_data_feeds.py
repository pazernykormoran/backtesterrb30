
from abc import abstractmethod
import asyncio
from backtesterRB30.libs.interfaces.historical_data_feeds.instrument_file import InstrumentFile
from backtesterRB30.libs.interfaces.utils.data_schema import DataSchema
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
from backtesterRB30.libs.data_sources.data_source_base import DataSource
from backtesterRB30.libs.zmq_broker.zmq import ZMQ
from backtesterRB30.libs.data_sources.data_sources_list import HISTORICAL_SOURCES
from backtesterRB30.libs.utils.list_of_services import SERVICES
from backtesterRB30.historical_data_feeds.functions import load_data_frame_ticks_2
from backtesterRB30.libs.utils.timestamps import timestamp_to_datetime
from os import getenv
from datetime import datetime
import time

class LiveDataFeeds(ZMQ):
    """Python Live data provider"""

    downloaded_data_path = '/var/opt/data_historical_downloaded'

    def __init__(self, config: dict, data_schema: DataSchema, logger=print):
        super().__init__(config, logger)
        self.__data_schema: DataSchema = data_schema
        self.__columns=['timestamp']+[c.symbol for c in self.__data_schema.data]
        self.__historical_sources_array = [i for i in dir(HISTORICAL_SOURCES) if not i.startswith('__')]
        self.__data_sources = {}
        self.__download_buffer = False
        self.__engine_ready = False
        self.__historical_rows = []
        self._register("engine_set_buffer_length", self.__engine_set_buffer_length_event)

    # override
    def _asyncio_loop(self, loop: asyncio.AbstractEventLoop):
        super()._create_listeners(loop)
        # TODO add data downloader
        if not self.config.backtest:
            self.__create_downloading_clients(self.__historical_sources_array, self.__data_schema, self.__data_sources, self._log)
            self.__combine_clients_and_symbols(self.__data_schema)
            interval = self.__find_loop_interval(self.__data_schema)
            loop.create_task(self.__main_loop(interval))


    # override
    def _handle_zmq_message(self, message):
        pass 

    async def __main_loop(self, interval):
        if self.__download_buffer == True:
            self._send(SERVICES.python_engine, 'get_buffer_length', SERVICES.live_data_feeds.value)
        else:
            self.__engine_ready = True
        while True:
            if self.__engine_ready:
                print('starting sendi')
                timestamp = await self.__get_proper_timestamp(self.__historical_rows, self.__data_schema, interval)
                for row in self.__historical_rows:
                    last_row = row
                    super()._send(SERVICES.python_engine,'data_feed',list(last_row))
                while True:
                    print('starting live')
                    row = []
                    row.append(timestamp)
                    sth_updated = False
                    for data_symbol in self.__data_schema.data:
                        price, updated = self.__get_symbol_price(timestamp, data_symbol)
                        if updated: sth_updated = True
                        row.append(price)
                    if sth_updated: 
                        print('sendin')
                        super()._send(SERVICES.python_engine,'data_feed',row)
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
        files = []
        for data_symbol in data_schema.data:
            file = InstrumentFile.from_params(
                data_symbol.historical_data_source, 
                data_symbol.symbol, 
                data_symbol.interval,
                timestamp_to_datetime(time_start),
                timestamp_to_datetime(time_stop)
            )
            client: DataSource = data_symbol.additional_properties['downloading_client']
            await client.download_instrument(self.downloaded_data_path, file)
            files.append(file)
        self.__historical_rows = load_data_frame_ticks_2(self.__data_schema, self.__columns, self.downloaded_data_path, [], files)
        print('data downloaded')

    async def __get_proper_timestamp(self, historical_rows, data_schema: DataSchema, interval: int):
        if historical_rows == []:
            return time.time() * 1000

        print('historical rows', historical_rows)
        smallest = self.__get_smallest_interval(data_schema)
        current_time_with_reserve = time.time()*1000 + 1000
        next_should_be_timestamp = historical_rows[-1][0] + smallest
        print(timestamp_to_datetime(next_should_be_timestamp))
        print('curren with reserve', timestamp_to_datetime(current_time_with_reserve))
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