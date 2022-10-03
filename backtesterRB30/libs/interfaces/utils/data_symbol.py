from pydantic import BaseModel
from typing import Optional, Union
from datetime import datetime
from backtesterRB30.libs.interfaces.utils.custom_base_model import CustomBaseModel
# from backtesterRB30.libs.utils.historical_sources import HISTORICAL_INTERVALS_UNION, HISTORICAL_SOURCES
from backtesterRB30.historical_data_feeds.data_sources.data_source_base import DataSource
from enum import Enum

class DataSymbol(CustomBaseModel):
    custom_name: Optional[str]
    symbol: str
    # historical_data_source: HISTORICAL_SOURCES
    historical_data_source: str
    # interval: HISTORICAL_INTERVALS_UNION
    interval: Enum
    backtest_date_start: datetime
    backtest_date_stop: datetime
    trigger_feed: bool = False
    with_volume: bool = False
    display_chart_in_summary: bool = False

    def get_buffer(self) -> list:
        if 'buffer' in self.additional_properties:
            return self.additional_properties['buffer']
        else: raise Exception('No buffer registered, buffer avaliable only in Model class')

    class Config: 
        arbitrary_types_allowed = True