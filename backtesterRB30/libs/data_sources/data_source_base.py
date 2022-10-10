from abc import abstractmethod
from typing import Union
from backtesterRB30.libs.interfaces.historical_data_feeds.instrument_file import InstrumentFile
import asyncio
import pandas as pd
from enum import Enum
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
from os.path import join

class DataSource():    
    def __init__(self, allow_synchronous_download: bool, logger=print):
        self._allow_synchronous_download = allow_synchronous_download
        self._log = logger

    def _raise_error(self, error_message):
        raise Exception(error_message)

    def __validate_dataframe(self, 
                        df: pd.DataFrame) -> bool:
        # if int(df.head(1)[0]) != expected_first_data_timestamp: return False
        # if int(df.tail(1)[0]) != expected_last_data_timestamp: return False
        # if len(df) != expected_data_length: return False
        if df.shape[1] != 2:
            raise Exception('Bad shape of returned dataframe in data source '+self.NAME)
        return True

    async def download_instrument(self,
                        downloaded_data_path: str, 
                        instrument_file: InstrumentFile): 
        await asyncio.sleep(0.1)
        df: pd.DataFrame = await self._download_instrument_data(instrument_file.instrument,
                instrument_file.interval, instrument_file.time_start, instrument_file.time_stop)
        self.__validate_dataframe(df)
        df.to_csv(join(downloaded_data_path, instrument_file.to_filename()), 
        index=False, header=False)
        
    async def download_dataframe(self, instrument: str, interval: str, 
            time_start: int, time_stop: Union[int, None]) ->pd.DataFrame:
        await asyncio.sleep(0.1)
        df: pd.DataFrame = await self._download_instrument_data(instrument,
                interval, time_start, time_stop)
        self.__validate_dataframe(df)
        return df


    async def validate_instrument(self, data: DataSymbol) -> bool:
        await asyncio.sleep(0.1)
        if type(data.interval) != self.INTERVALS:
            raise Exception('Bad interval type in data symbol', data.symbol, data.historical_data_source, 'check data_schema.py')
        return await self._validate_instrument_data(data)

    @abstractmethod
    def _get_interval_miliseconds(self, interval: str) -> Union[int,None]: 
        """
        This function should return number of miliseconds delay for provided interval
        """
        pass

    @abstractmethod
    async def _validate_instrument_data(self, data: DataSymbol) -> bool:
        """
        Function should validate if data for shis DataSymbol is possible to download.
        It should check if
        - data.symbol exists
        - data.interval fot this data.symbol exists
        - timestamps range from 'data.backtest_date_start' to 'data.backtest_date_stop' 
            for this data.symbol and data.interval exists
        """
        pass
    
    @abstractmethod
    async def _download_instrument_data(self,
                instrument: str, interval: str, time_start: int, time_stop: Union[int, None]) -> pd.DataFrame:
        """
        First downloaded timestamp should exactly exuals instrument_file.time_start (can be bigger if u are downloading ticks)
        Last downloaded timestamp should exactly exuals one interval before instrument_file.time_stop ()
        """
        pass


    def get_current_price(self, data: DataSymbol):
        """
        Function should return current price of provided data symbol
        """
        pass

    