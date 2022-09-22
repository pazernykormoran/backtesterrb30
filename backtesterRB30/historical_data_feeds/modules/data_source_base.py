from abc import abstractmethod
from typing import Union
from backtesterRB30.libs.interfaces.historical_data_feeds.instrument_file import InstrumentFile
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
import asyncio
import pandas as pd

class DataSource():

    def __init__(self, allow_synchronous_download: bool, logger=print):
        self._allow_synchronous_download = allow_synchronous_download
        self._log = logger

    def _raise_error(self, error_message):
        raise Exception(error_message)

    def __validate_dataframe(self, 
                        df: pd.DataFrame,
                        expected_first_data_timestamp: int,
                        expected_last_data_timestamp: int,
                        expected_data_length: int) -> bool:
        if int(df.head(1)[0]) != expected_first_data_timestamp: return False
        if int(df.tail(1)[0]) != expected_last_data_timestamp: return False
        if len(df) != expected_data_length: return False
        return True

    async def download_instrument(self,
                        downloaded_data_path: str, 
                        instrument_file: InstrumentFile): 
        await asyncio.sleep(0.1)
        await self._download_instrument_data(downloaded_data_path, instrument_file)
        

    async def validate_instrument(self, data: DataSymbol) -> bool:
        await asyncio.sleep(0.1)
        return await self._validate_instrument_data(data)

    @abstractmethod
    def _get_interval_miliseconds(self, interval: str) -> Union[int,None]: 
        pass

    @abstractmethod
    async def _validate_instrument_data(self, data: DataSymbol) -> bool:
        pass
    
    @abstractmethod
    async def _download_instrument_data(self,
                        downloaded_data_path: str, 
                        instrument_file: InstrumentFile):
        """
        First downloaded timestamp should exactly exuals instrument_file.time_start (can be bigger if u are downloading ticks)
        Last downloaded timestamp should exactly exuals one interval before instrument_file.time_stop ()
        """
        pass