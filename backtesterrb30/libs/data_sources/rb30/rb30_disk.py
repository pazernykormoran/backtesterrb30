from typing import Union

# from backtesterrb30.historical_data_feeds.modules.utils import validate_dataframe_timestamps
import pandas as pd

from backtesterrb30.libs.data_sources.data_source_base import DataSource
from backtesterrb30.libs.interfaces.utils.data_symbol import DataSymbol


class RB30DataSource(DataSource):
    INTERVALS = {}
    NAME = "rb30disk"

    def __init__(self, logger=print):
        super().__init__(False, logger)

    def _get_interval_miliseconds(self, interval: str) -> Union[int, None]:
        pass

    async def _validate_instrument_data(self, data: DataSymbol) -> bool:
        return True

    async def _download_instrument_data(
        self,
        instrument: str,
        interval: str,
        time_start: int,
        time_stop: Union[int, None],
    ) -> pd.DataFrame:
        return True
