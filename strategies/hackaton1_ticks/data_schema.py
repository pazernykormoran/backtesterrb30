from libs.necessery_imports.data_imports import *

# configure data feed =====================================

data={

    'data':[
        {
            'interval': BINANCE_INTERVALS.week,
            'backtest_date_start': datetime(2018,6,1),
            'backtest_date_stop': datetime(2022,6,1),
            'symbol': 'LTCUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': True,
            'trigger_feed': False
        },
        {
            'interval': BINANCE_INTERVALS.week,
            'backtest_date_start': datetime(2020,6,1),
            'backtest_date_stop': datetime(2022,6,1),
            'symbol': 'BTCUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': False,
            'trigger_feed': True
        },
        {
            'interval': DUKASCOPY_INTERVALS.day,
            'backtest_date_start': datetime(2021,6,1),
            'backtest_date_stop': datetime(2022,6,1),
            'symbol': 'usiteur',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
            'trigger_feed': True
        },
        {
            'interval': DUKASCOPY_INTERVALS.day,
            'backtest_date_start': datetime(2019,6,1),
            'backtest_date_stop': datetime(2022,6,1),
            'symbol': '2914jpjpy',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
            'trigger_feed': False
        }
    ]
}
DATA = validate_config_ticks(data)
