from libs.utils.data_imports import *

# datetime_start = datetime(2021,5,1)
# datatime_finish = datetime(2022,8,1)

# datetime_start = datetime(2022,8,1)
# datatime_finish = datetime(2022,8,2)

# datetime_start = datetime(2020,8,4)
# datatime_finish = datetime(2022,8,6)

# datetime_start = datetime(2020,8,4)
# datatime_finish = datetime(2022,8,6)

# error in exante download length last timestamp:
datetime_start = datetime(2021,1,4)
datatime_finish = datetime(2021,12,6)

# datetime_start = datetime(2021,1,4)
# datatime_finish = datetime(2021,12,8)

data={
    'log_scale_valuation_chart': True,
    'data':[
        {
            'symbol': 'BTCUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': True,
            'backtest_date_start': datetime_start,
            'backtest_date_stop': datatime_finish,
            'trigger_feed': True,
            'interval': BINANCE_INTERVALS.day
        },
        {
            'symbol': 'iefususd',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
            'backtest_date_start': datetime_start,
            'backtest_date_stop': datatime_finish,
            'trigger_feed': True,
            'interval': DUKASCOPY_INTERVALS.day
        },
        {
            'symbol': 'AAPL.NASDAQ',
            'historical_data_source': HISTORICAL_SOURCES.exante,
            'main': False,
            'backtest_date_start': datetime_start,
            'backtest_date_stop': datatime_finish,
            'trigger_feed': True,
            'interval': EXANTE_INTERVALS.day
        }
    ]
}
DATA = validate_config(data)
