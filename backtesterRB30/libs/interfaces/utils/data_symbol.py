from pydantic import BaseModel
from typing import Optional, Union
from datetime import datetime
from backtesterRB30.libs.utils.historical_sources import HISTORICAL_INTERVALS_UNION, HISTORICAL_SOURCES

class DataSymbol(BaseModel):
    symbol: str
    historical_data_source: HISTORICAL_SOURCES
    main: bool
    interval: HISTORICAL_INTERVALS_UNION
    backtest_date_start: datetime
    backtest_date_stop: datetime
    trigger_feed: Optional[bool]