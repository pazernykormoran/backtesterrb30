from enum import Enum
from typing import Union

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

    @classmethod
    def get_small_intervals(cls):
        return [cls.tick,
                cls.minute,
               cls.minute5]

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

    @classmethod
    def get_small_intervals(cls):
        return [cls.tick,
                cls.minute,
               cls.minute3,
               cls.minute5]

class EXANTE_INTERVALS(Enum):
    tick='tick'
    minute='minute'
    minute5='minute5'
    minute30='minute30'
    hour='hour'
    day='day'

    @classmethod
    def get_small_intervals(cls):
        return [cls.tick,
                cls.minute,
               cls.minute5]

class COINGECKO_INTERVALS(Enum):
    day4='day4'

    @classmethod
    def get_small_intervals(cls):
        return []


class HISTORICAL_SOURCES(Enum):
    binance='binance'
    ducascopy='ducascopy'
    rb30disk='rb30disk'
    exante='exante'
    coingecko='coingecko'

HISTORICAL_INTERVALS_UNION = Union[BINANCE_INTERVALS, DUKASCOPY_INTERVALS, EXANTE_INTERVALS, COINGECKO_INTERVALS]