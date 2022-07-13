from libs.necessery_imports.data_imports import *

# configure data feed =====================================

data={
    'interval':STRATEGY_INTERVALS.hour,
    'backtest_date_start': datetime(2020,6,1),
    'backtest_date_stop': datetime(2022,6,1),
    'data':[
        {
            'symbol': 'LTCUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': True,
        },
        {
            'symbol': 'eurusd',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
        }
    ]
}
DATA = DataSchema(**data)
