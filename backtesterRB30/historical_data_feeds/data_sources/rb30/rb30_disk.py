from typing import Union
from backtesterRB30.historical_data_feeds.data_sources.data_source_base import DataSource
from datetime import datetime
from backtesterRB30.libs.interfaces.historical_data_feeds.instrument_file import InstrumentFile
from os import getenv
from backtesterRB30.libs.utils.singleton import singleton
# from backtesterRB30.historical_data_feeds.modules.utils import validate_dataframe_timestamps

class RB30DataSource(DataSource):
    INTERVALS= {}
    NAME='rb30disk'
    
    def __init__(self, logger=print):
        super().__init__(False, logger)

    def _get_interval_miliseconds(self, interval: str) -> Union[int,None]: 
        pass

    async def _validate_instrument_data(self, data) -> bool:
        return True

    async def _download_instrument_data(self, 
                        downloaded_data_path: str, 
                        instrument_file: InstrumentFile):
        return True
