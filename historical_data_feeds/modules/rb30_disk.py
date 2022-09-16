from historical_data_feeds.modules.data_source_base import DataSource
from datetime import datetime
from libs.interfaces.utils.data_symbol import DataSymbol
from os import getenv
from libs.utils.singleton import singleton
# from historical_data_feeds.modules.utils import validate_dataframe_timestamps

@singleton
class RB30DataSource(DataSource):
    def __init__(self, logger=print):
        super().__init__(False, logger)

    async def validate_instrument_data(self, data: DataSymbol):
        return True

    def download_instrument_data(self, downloaded_data_path: str, instrument_file_name:str, instrument: str, interval: str, time_start: int, time_stop: int):
        return True
