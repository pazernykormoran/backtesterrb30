from libs.necessery_imports.data_imports import *

# configure data feed =====================================

data={

    'data':[
        {
            'interval': BINANCE_INTERVALS.tick,
            'backtest_date_start': datetime(2022,6,3),
            'backtest_date_stop': datetime(2022,6,4),
            'symbol': 'LTCUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': True,
            'trigger_feed': True
        },
        {
            'interval': DUKASCOPY_INTERVALS.tick,
            'backtest_date_start': datetime(2022,6,3),
            'backtest_date_stop': datetime(2022,6,4),
            'symbol': '2914jpjpy',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
            'trigger_feed': True
        }
    ]
}
DATA = validate_config(data)
