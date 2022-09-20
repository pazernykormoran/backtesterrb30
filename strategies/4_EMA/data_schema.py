from libs.utils.data_imports import *

data={
    'data':[
        {
            'symbol': 'BTCUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': True,
            'backtest_date_start': datetime(2021,6,1),
            'backtest_date_stop': datetime(2022,8,16),
            'trigger_feed': True,
            'interval': BINANCE_INTERVALS.hour
        },
        # {
        #     'symbol': 'ETHUSDT',
        #     'historical_data_source': HISTORICAL_SOURCES.binance,
        #     'main': True,
        #     'backtest_date_start': datetime(2022,6,1),
        #     'backtest_date_stop': datetime(2022,8,1),
        #     'trigger_feed': True,
        #     'interval': BINANCE_INTERVALS.minute15
        # },
        # {
        #     'symbol': 'XRPUSDT',
        #     'historical_data_source': HISTORICAL_SOURCES.binance,
        #     'main': False,
        #     'backtest_date_start': datetime(2022,6,1),
        #     'backtest_date_stop': datetime(2022,8,1),
        #     'trigger_feed': True,
        #     'interval': BINANCE_INTERVALS.minute15
        # },
        # {
        #     'symbol': 'BNBUSDT',
        #     'historical_data_source': HISTORICAL_SOURCES.binance,
        #     'main': False,
        #     'backtest_date_start': datetime(2022,6,1),
        #     'backtest_date_stop': datetime(2022,8,1),
        #     'trigger_feed': True,
        #     'interval': BINANCE_INTERVALS.minute15
        # },
        # {
        #     'symbol': 'iefususd',
        #     'historical_data_source': HISTORICAL_SOURCES.ducascopy,
        #     'main': False,
        #     'backtest_date_start': datetime(2022,6,1),
        #     'backtest_date_stop': datetime(2022,8,1),
        #     'trigger_feed': True,
        #     'interval': DUKASCOPY_INTERVALS.minute15
        # },
        # {
        #     'symbol': 'nflxususd',
        #     'historical_data_source': HISTORICAL_SOURCES.ducascopy,
        #     'main': True,
        #     'backtest_date_start': datetime(2020,6,1),
        #     'backtest_date_stop': datetime(2022,8,1),
        #     'trigger_feed': True,
        #     'interval': DUKASCOPY_INTERVALS.day
        # },
        # {
        #     'symbol': 'xauusd',
        #     'historical_data_source': HISTORICAL_SOURCES.ducascopy,
        #     'main': False,
        #     'backtest_date_start': datetime(2022,6,1),
        #     'backtest_date_stop': datetime(2022,8,1),
        #     'trigger_feed': True,
        #     'interval': DUKASCOPY_INTERVALS.minute15
        # }
    ]
}
DATA = validate_config(data)
