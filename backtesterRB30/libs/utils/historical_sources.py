# from enum import Enum
# from typing import Union

# class DUKASCOPY_INTERVALS(str, Enum):
#     tick: str='tick'
#     minute: str='minute'
#     minute5: str='minute5'
#     minute15: str='minute15'
#     minute30: str='minute30'
#     hour: str='hour'
#     hour4: str='hour4'
#     day: str='day'
#     month: str='month'

# class BINANCE_INTERVALS(str, Enum):
#     tick: str='tick'
#     minute: str='minute'
#     minute3: str='minute3'
#     minute5: str='minute5'
#     minute15: str='minute15'
#     minute30: str='minute30'
#     hour: str='hour'
#     hour2: str='hour2'
#     hour4: str='hour4'
#     hour6: str='hour6'
#     hour8: str='hour8'
#     hour12: str='hour12'
#     day: str='day'
#     day3: str='day3'
#     week: str='week'
#     month: str='month'


# class EXANTE_INTERVALS(str, Enum):
#     tick: str='tick'
#     minute: str='minute'
#     minute5: str='minute5'
#     minute30: str='minute30'
#     hour: str='hour'
#     day: str='day'


# class COINGECKO_INTERVALS(Enum):
#     day4='day4'

    # @classmethod
    # def get_small_intervals(cls):
    #     return []


# class HISTORICAL_SOURCES(str, Enum):
#     binance: str='binance'
#     ducascopy: str='ducascopy'
#     rb30disk: str='rb30disk'
#     exante: str='exante'
#     coingecko: str='coingecko'

# HISTORICAL_INTERVALS_UNION = Union[BINANCE_INTERVALS, DUKASCOPY_INTERVALS, EXANTE_INTERVALS, COINGECKO_INTERVALS]