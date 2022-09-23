import backtesterRB30 as bt
from datetime import datetime

data={
    'log_scale_valuation_chart': True,
    'data':[
        {
            'symbol': '2914jpjpy',
            'historical_data_source': bt.HISTORICAL_SOURCES.ducascopy,
            'main': False,
            'backtest_date_start': datetime(2021,5,1),
            'backtest_date_stop': datetime(2022,8,1),
            'trigger_feed': False,
            'interval': bt.DUKASCOPY_INTERVALS.hour,
        },
        {
            'symbol': 'iefususd',
            'historical_data_source': bt.HISTORICAL_SOURCES.ducascopy,
            'main': True,
            'backtest_date_start': datetime(2021,5,1),
            'backtest_date_stop': datetime(2022,8,1),
            'trigger_feed': True,
            'interval': bt.DUKASCOPY_INTERVALS.hour
        }
    ]
}
DATA = bt.validate_config(data)
