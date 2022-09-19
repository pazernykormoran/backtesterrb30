from abc import abstractmethod
from libs.interfaces.utils.data_symbol import DataSymbol
import asyncio

class DataSource():

    def __init__(self, allow_synchronous_download: bool, logger=print):
        self._allow_synchronous_download = allow_synchronous_download
        self._log = logger

    def _raise_error(error_message):
        raise Exception(error_message)

    async def download_instrument(self,
                        downloaded_data_path: str, 
                        instrument_file_name:str, 
                        instrument: str, 
                        interval: str, 
                        time_start: int, 
                        time_stop: int): 
        await asyncio.sleep(0.5)
        await self._download_instrument_data(downloaded_data_path,instrument_file_name,instrument,interval,time_start,time_stop)

    async def validate_instrument(self, data: DataSymbol) -> bool:
        await asyncio.sleep(0.5)
        return await self._validate_instrument_data(data)

    @abstractmethod
    async def _validate_instrument_data(self, data: DataSymbol) -> bool:
        pass
    
    @abstractmethod
    async def _download_instrument_data(self,
                        downloaded_data_path: str, 
                        instrument_file_name:str, 
                        instrument: str, 
                        interval: str, 
                        time_start: int, 
                        time_stop: int):
        pass