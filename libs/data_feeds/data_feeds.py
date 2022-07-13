from enum import Enum
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class STRATEGY_INTERVALS(Enum):
    tick='tick'
    minute='minute'
    minute15='minute15'
    minute30='minute30'
    hour='hour'
    day='day'
    month='month'

class HISTORICAL_SOURCES(Enum):
    binance='binance'
    ducascopy='ducascopy'
    rb30disk='rb30disk'

class DataSymbol(BaseModel):
    symbol: str
    historical_data_source: HISTORICAL_SOURCES
    trigger_feed: Optional[bool]
    main: bool


class DataSchema(BaseModel):
    interval: STRATEGY_INTERVALS
    backtest_date_start: datetime
    backtest_date_stop: datetime
    data: List[DataSymbol]

"""
example of data:

data={
    'interval':STRATEGY_INTERVALS.hour,
    'backtest_date_start': datetime(2020,6,1),
    'backtest_date_stop': datetime(2022,6,1),
    'data':[
        {
            'symbol': 'BTCUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': False
        },
        {
            'symbol': 'ETHUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'trigger_feed': False,
            'main': True,
        }
    ]
}
"""
