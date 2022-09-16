from libs.utils.data_imports import *

# configure data feed =====================================

data={

    'data':[
        {
            'interval': BINANCE_INTERVALS.tick,
            'backtest_date_start': datetime(2022,6,3),
            'backtest_date_stop': datetime(2022,6,4),
            'symbol': 'LTCUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': False,
            'trigger_feed': True
        },
        {
            'interval': BINANCE_INTERVALS.tick,
            'backtest_date_start': datetime(2022,6,2),
            'backtest_date_stop': datetime(2022,6,4),
            'symbol': 'LTCBNB',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': False,
            'trigger_feed': True
        },
        {
            'interval': BINANCE_INTERVALS.tick,
            'backtest_date_start': datetime(2022,6,1),
            'backtest_date_stop': datetime(2022,6,4),
            'symbol': 'XRPUSDT',
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
        },
        {
            'symbol': 'iefususd',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
            'backtest_date_start': datetime(2022,6,1),
            'backtest_date_stop': datetime(2022,6,4),
            'trigger_feed': False,
            'interval': DUKASCOPY_INTERVALS.minute15
        },
        {
            'symbol': 'iveususd',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
            'backtest_date_start': datetime(2022,6,1),
            'backtest_date_stop': datetime(2022,6,4),
            'trigger_feed': False,
            'interval': DUKASCOPY_INTERVALS.minute15
        },
        {
            'symbol': 'xauusd',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
            'backtest_date_start': datetime(2022,6,2),
            'backtest_date_stop': datetime(2022,6,4),
            'trigger_feed': True,
            'interval': DUKASCOPY_INTERVALS.tick
        }
    ]
}
DATA = validate_config(data)
