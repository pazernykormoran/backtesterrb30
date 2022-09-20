from libs.utils.data_imports import *

datetime_start = datetime(2021,8,4)
datatime_finish = datetime(2021,12,9)

data={
    'log_scale_valuation_chart': True,
    'data':[
        {
            'symbol': 'BTCUSDT',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': True,
            'backtest_date_start': datetime_start,
            'backtest_date_stop': datatime_finish,
            'trigger_feed': True,
            'interval': BINANCE_INTERVALS.hour
        },
        {
            'symbol': 'iefususd',
            'historical_data_source': HISTORICAL_SOURCES.ducascopy,
            'main': False,
            'backtest_date_start': datetime_start,
            'backtest_date_stop': datatime_finish,
            'trigger_feed': True,
            'interval': DUKASCOPY_INTERVALS.hour
        },
        {
            'symbol': 'AAPL.NASDAQ',
            'historical_data_source': HISTORICAL_SOURCES.exante,
            'main': False,
            'backtest_date_start': datetime_start,
            'backtest_date_stop': datatime_finish,
            'trigger_feed': True,
            'interval': EXANTE_INTERVALS.hour
        }
    ]
}
DATA = validate_config(data)
