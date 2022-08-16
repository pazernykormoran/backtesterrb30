from libs.necessery_imports.data_imports import *

# configure data feed =====================================

data={
    'interval':STRATEGY_INTERVALS.minute15,
    'backtest_date_start': datetime(2022,6,1),
    'backtest_date_stop': datetime(2022,8,1),
    'data':[
        {
            'symbol': 'BTCUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': False,
        },
        {
            'symbol': 'ETHUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': True,
        },
        {
            'symbol': 'XRPUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': False,
        },
        {
            'symbol': 'BNBUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': False,
        },
        {
            'symbol': 'iefususd',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
        },
        {
            'symbol': 'iveususd',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
        },
        {
            'symbol': 'xauusd',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
        }
    ]
}
DATA = validate_config(data)
