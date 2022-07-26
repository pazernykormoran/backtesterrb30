
from libs.data_feeds.data_feeds import BINANCE_INTERVALS, DUKASCOPY_INTERVALS
from libs.necessery_imports.data_imports import *

# configure data feed =====================================

data={

    'data':[
        {
            'interval': BINANCE_INTERVALS.hour,
            'backtest_date_start': datetime(2020,6,1),
            'backtest_date_stop': datetime(2022,6,1),
            'symbol': 'LTCUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': True,
            'trigger_feed': True
        },
        {
            'interval': DUKASCOPY_INTERVALS.hour,
            'backtest_date_start': datetime(2020,6,1),
            'backtest_date_stop': datetime(2022,6,1),
            'symbol': '0291hkhkd',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
        }
    ]
}
DATA = validate_config_ticks(data)
