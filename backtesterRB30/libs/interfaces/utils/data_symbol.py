from typing import Optional, Any
from datetime import datetime
from backtesterRB30.libs.interfaces.utils.custom_base_model import CustomBaseModel
from enum import Enum

class DataSymbol(CustomBaseModel):
    symbol: str
    # historical_data_source: HISTORICAL_SOURCES
    historical_data_source: str
    # interval: HISTORICAL_INTERVALS_UNION
    interval: Enum
    backtest_date_start: datetime
    backtest_date_stop: datetime
    trigger_feed: bool = True
    with_volume: bool = False
    display_chart_in_summary: bool = True
    custom_name: Optional[str]
    custom_data: Optional[Any]

    @property
    def identifier(self):
        return self.historical_data_source + "_" + self.symbol


    def get_buffer(self) -> list:
        if 'buffer' in self.additional_properties:
            return self.additional_properties['buffer']
        else: raise Exception('No buffer registered, buffer avaliable only in Model class')

    class Config: 
        arbitrary_types_allowed = True