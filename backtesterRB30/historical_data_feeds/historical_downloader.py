from backtesterRB30.libs.interfaces.utils.data_schema import DataSchema
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
from backtesterRB30.libs.data_sources.data_source_base import DataSource
from backtesterRB30.libs.interfaces.historical_data_feeds.instrument_file import InstrumentFile
from backtesterRB30.historical_data_feeds.functions import create_downloading_clients, check_symbol_data_exists
import asyncio
from typing import List


class HistoricalDownloader():
    def __init__(self, data_schema: DataSchema, historical_sources_array, downloaded_data_path, logger=print):
        self._log = logger
        self.__data_schema: DataSchema = data_schema
        self.__historical_sources_array = historical_sources_array
        self.__data_sources = {}
        self.__data_to_download_2 = None
        self.__downloaded_data_path = downloaded_data_path


    def run(self, loop):
        self.__get_data_to_download(self.__data_schema)
        create_downloading_clients(self.__historical_sources_array, self.__data_schema, self.__data_sources, self._log)
        self.__validate_data_schema_instruments(self.__data_schema.data, loop)
        self.__validate_symbols_to_download(self.__data_schema, loop)
        self.__download_prepared_data(self.__data_schema, loop)
        return self.__data_to_download_2


    def __get_data_to_download(self, data_schema: DataSchema):
        for data_symbol in data_schema.data:
            data_symbol.additional_properties['files_to_download']: List[InstrumentFile] = []
            data_symbol.additional_properties['files_to_download'] = check_symbol_data_exists(data_symbol, self.__downloaded_data_path)
            if self.__data_to_download_2 == None:
                self.__data_to_download_2 = []
            self.__data_to_download_2 = self.__data_to_download_2 + data_symbol.additional_properties['files_to_download']


    def __validate_symbols_to_download(self,data_schema: DataSchema, loop: asyncio.AbstractEventLoop):
        self._log('validating symbols before download')
        for symbol in data_schema.data:
            if symbol.additional_properties['files_to_download'] != []:
                data_source_client: DataSource = self.__get_data_source_client(symbol.historical_data_source)
                res = loop.run_until_complete(data_source_client.validate_instrument(symbol))
                if not res:
                    raise Exception('Error while validation symbol.')

    def __download_prepared_data(self, data_schema: DataSchema, loop: asyncio.AbstractEventLoop):
        for symbol in data_schema.data:
            if symbol.additional_properties['files_to_download'] != []:
                loop.create_task(self.__download_symbol_data(symbol))


    def __validate_data_schema_instruments(self, data_symbol_array: List[DataSymbol], loop: asyncio.AbstractEventLoop):
        self._log('Data_schema validation')
        #check for duplicates:
        seen = []
        for x in data_symbol_array:
            data = str(x.symbol)+str(x.historical_data_source)
            if data in seen:
                raise Exception('Duplicate data symbols')
            else:
                seen.append(data)
        #check other
        number_of_trigger_feeders = 0
        for data in data_symbol_array:
            if data.backtest_date_start == None:
                raise Exception('Error. You must provide "backtest_date_start" field in data_schema file while you are backtesting your strategy')
            if data.backtest_date_start >= data.backtest_date_stop: 
                raise Exception('Error. You have provided "backtest_date_start" is equal or bigger than "backtest_date_start" ')
            if [data.backtest_date_start.hour,
                data.backtest_date_start.minute,
                data.backtest_date_start.second,
                data.backtest_date_start.microsecond] != [0,0,0,0]:
                raise Exception('Error. Provide your "backtest_date_start" and "backtest_date_stop" in a day accuracy like: "backtest_date_start": datetime(2020,6,1)')
            if data.historical_data_source not in self.__historical_sources_array: 
                raise Exception('Error. This historical_data_source not implemented yet')
            if data.trigger_feed == True:
                number_of_trigger_feeders += 1
        if number_of_trigger_feeders < 1:
            raise Exception('Error. Your "data_schema.py" must have at least one instrument that triggers feeds')
    
    def __get_data_source_client(self, historical_source: str) -> DataSource:
        client = self.__data_sources[historical_source]
        if not client:
                raise Exception('Error, no registered source client')
        return client

    async def __download_symbol_data(self, symbol: DataSymbol):
        files_to_download: List[InstrumentFile] = symbol.additional_properties['files_to_download']
        await self.__download_symbol_files(files_to_download, symbol.historical_data_source)

    async def __download_symbol_files(self, files: List[InstrumentFile], source: str):
        data_source_client: DataSource = self.__get_data_source_client(source)
        for file in files:
            await data_source_client.download_instrument(self.__downloaded_data_path, file)
