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
            'symbol': 'BTGETH',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': False,
        },
        {
            'symbol': 'IOTAETH',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': False,
        },
        {
            'symbol': 'saffreur',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
        },
        {
            'symbol': 'adsdeeur',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
        },
        {
            'symbol': 'bmwdeeur',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
        },
        {
            'symbol': '0291hkhkd',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
        }
    ]
}
DATA = validate_config(data)
