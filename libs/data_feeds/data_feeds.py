from enum import Enum
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime
from datetime import timezone

class DUKASCOPY_INTERVALS(Enum):
    tick='tick'
    minute='minute'
    minute5='minute5'
    minute15='minute15'
    minute30='minute30'
    hour='hour'
    hour4='hour4'
    day='day'
    month='month'

class BINANCE_INTERVALS(Enum):
    tick='tick'
    minute='minute'
    minute3='minute3'
    minute5='minute5'
    minute15='minute15'
    minute30='minute30'
    hour='hour'
    hour2='hour2'
    hour4='hour4'
    hour6='hour6'
    hour8='hour8'
    hour12='hour12'
    day='day'
    day3='day3'
    week='week'
    month='month'

# class STRATEGY_INTERVALS(Enum):
#     tick='tick'
#     minute='minute'
#     minute15='minute15'
#     minute30='minute30'
#     hour='hour'
#     day='day'
#     month='month'

class HISTORICAL_SOURCES(Enum):
    binance='binance'
    ducascopy='ducascopy'
    rb30disk='rb30disk'

# class DataSymbol(BaseModel):
#     symbol: str
#     historical_data_source: HISTORICAL_SOURCES
#     trigger_feed: Optional[bool]
#     main: bool


# class DataSchema(BaseModel):
#     interval: STRATEGY_INTERVALS
#     backtest_date_start: datetime
#     backtest_date_stop: datetime
#     data: List[DataSymbol]


class DataSymbolTicks(BaseModel):
    symbol: str
    historical_data_source: HISTORICAL_SOURCES
    main: bool
    interval: Union[BINANCE_INTERVALS, DUKASCOPY_INTERVALS]
    backtest_date_start: datetime
    backtest_date_stop: datetime
    trigger_feed: Optional[bool]


class DataSchemaTicks(BaseModel):
    data: List[DataSymbolTicks]


# def validate_config(config: dict):
#     cfg = DataSchema(**config)
#     cfg.backtest_date_start = cfg.backtest_date_start.replace(tzinfo=timezone.utc)
#     cfg.backtest_date_stop = cfg.backtest_date_stop.replace(tzinfo=timezone.utc)
#     return cfg

def validate_config_ticks(config: dict):
    cfg = DataSchemaTicks(**config)
    for symbol in cfg.data:
        symbol.backtest_date_start = symbol.backtest_date_start.replace(tzinfo=timezone.utc)
        symbol.backtest_date_stop = symbol.backtest_date_stop.replace(tzinfo=timezone.utc)
    return cfg
