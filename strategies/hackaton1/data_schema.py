from libs.necessery_imports.data_imports import *

datetime_start = datetime(2020,6,1)

data={
    'data':[
        {
            'symbol': 'BTCUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': False,
            'backtest_date_start': datetime_start,
            'backtest_date_stop': datetime(2022,8,1),
            'trigger_feed': True,
            'interval': BINANCE_INTERVALS.hour
        },
        {
            'symbol': 'ETHUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': True,
            'backtest_date_start': datetime_start,
            'backtest_date_stop': datetime(2022,8,1),
            'trigger_feed': True,
            'interval': BINANCE_INTERVALS.hour
        },
        {
            'symbol': 'XRPUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': False,
            'backtest_date_start': datetime_start,
            'backtest_date_stop': datetime(2022,8,1),
            'trigger_feed': True,
            'interval': BINANCE_INTERVALS.hour
        },
        {
            'symbol': 'BNBUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': False,
            'backtest_date_start': datetime_start,
            'backtest_date_stop': datetime(2022,8,1),
            'trigger_feed': True,
            'interval': BINANCE_INTERVALS.hour
        },
        {
            'symbol': 'iefususd',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
            'backtest_date_start': datetime_start,
            'backtest_date_stop': datetime(2022,8,1),
            'trigger_feed': True,
            'interval': DUKASCOPY_INTERVALS.hour
        },
        {
            'symbol': 'iveususd',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
            'backtest_date_start': datetime_start,
            'backtest_date_stop': datetime(2022,8,1),
            'trigger_feed': True,
            'interval': DUKASCOPY_INTERVALS.hour
        },
        {
            'symbol': 'xauusd',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
            'backtest_date_start': datetime_start,
            'backtest_date_stop': datetime(2022,8,1),
            'trigger_feed': True,
            'interval': DUKASCOPY_INTERVALS.hour
        }
    ]
}
DATA = validate_config(data)
