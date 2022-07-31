from binance import Client
from datetime import datetime
from libs.data_feeds.data_feeds import STRATEGY_INTERVALS
import pandas as pd
from os.path import join
# from historical_data_feeds.modules.utils import validate_dataframe_timestamps

def _get_binance_interval(interval: str):
    if interval == 'minute': return Client.KLINE_INTERVAL_1MINUTE
    if interval == 'minute15': return Client.KLINE_INTERVAL_15MINUTE
    if interval == 'minute30': return Client.KLINE_INTERVAL_30MINUTE
    if interval == 'hour': return Client.KLINE_INTERVAL_1HOUR
    if interval == 'day': return Client.KLINE_INTERVAL_1DAY
    # if interval == 'week': return Client.KLINE_INTERVAL_1WEEK
    if interval == 'month': return Client.KLINE_INTERVAL_1MONTH


def validate_binance_instrument(client: Client, instrument: str, from_datetime: datetime, interval: STRATEGY_INTERVALS):
    # print('validation instrment', instrument, 'from_datetime', from_datetime, 'interval',interval)
    #validate if instrument exists:
    exchange_info = client.get_exchange_info()
    if instrument not in [s['symbol'] for s in exchange_info['symbols']]:
        print('Error. Instrument "'+instrument+'" does not exists on binance.')
        return False
    # #validate it timestamps perios is right:
    # from_datetime_timestamp = int(round(datetime.timestamp(from_datetime) * 1000))
    # binance_interval = _get_binance_interval(interval.value)
    # first_timestamp = client._get_earliest_valid_timestamp(instrument, binance_interval)
    # if first_timestamp > from_datetime_timestamp:
    #     print("Error. First avaliable date of " , instrument, "is" , datetime.fromtimestamp(first_timestamp/1000.0))
    #     return False
    return True

def download_binance_data(client: Client, downloaded_data_path: str, instrument_file_name:str, instrument: str, interval: str, time_start: int, time_stop: int):
    print('downloading binance data', instrument_file_name)
    binance_interval = _get_binance_interval(interval)
    klines = client.get_historical_klines(instrument, binance_interval, time_start, time_stop)
    df = pd.DataFrame(klines).iloc[:-1, [0,1]]
    print('downloaded data length', df.shape[0])
    # if interval != STRATEGY_INTERVALS.tick.value:
    #     df = validate_dataframe_timestamps(df, interval, time_start, time_stop)
    print('data length after validation', df.shape[0])
    df.to_csv(join(downloaded_data_path, instrument_file_name), index=False, header=False)