from libs.necessery_imports.data_imports import *

# configure data feed =====================================

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
            'main': True,
        },
        {
            'symbol': 'LTCUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': False,
        },
        {
            'symbol': 'TRXUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': False,
        }
    ]
}
DATA = DataSchema(**data)
