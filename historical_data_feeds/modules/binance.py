from binance import Client
from datetime import datetime
import pandas as pd
from os.path import join
# from historical_data_feeds.modules.utils import validate_dataframe_timestamps

def _get_binance_interval(interval: str):
    if interval == 'minute': return Client.KLINE_INTERVAL_1MINUTE
    if interval == 'minute3': return Client.KLINE_INTERVAL_3MINUTE
    if interval == 'minute5': return Client.KLINE_INTERVAL_5MINUTE
    if interval == 'minute15': return Client.KLINE_INTERVAL_15MINUTE
    if interval == 'minute30': return Client.KLINE_INTERVAL_30MINUTE
    if interval == 'hour': return Client.KLINE_INTERVAL_1HOUR
    if interval == 'hour2': return Client.KLINE_INTERVAL_2HOUR
    if interval == 'hour4': return Client.KLINE_INTERVAL_4HOUR
    if interval == 'hour6': return Client.KLINE_INTERVAL_6HOUR
    if interval == 'hour8': return Client.KLINE_INTERVAL_8HOUR
    if interval == 'hour12': return Client.KLINE_INTERVAL_12HOUR
    if interval == 'day': return Client.KLINE_INTERVAL_1DAY
    if interval == 'day3': return Client.KLINE_INTERVAL_3DAY
    if interval == 'week': return Client.KLINE_INTERVAL_1WEEK
    if interval == 'month': return Client.KLINE_INTERVAL_1MONTH


def validate_binance_instrument(client: Client, instrument: str):
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

def download_binance_data(client: Client, downloaded_data_path: str, instrument_file_name:str, instrument: str, interval: str, time_start: int, time_stop: int) -> bool:
    print('downloading binance data', instrument_file_name)
    try:
        if interval == 'tick': 

            interval_timestamp = 1000*60*60
            trades_arr = []
            start_hour = time_start
            stop_hour = start_hour + interval_timestamp
            while stop_hour < time_stop:
                trades = client.get_aggregate_trades(symbol=instrument, startTime=start_hour, endTime=stop_hour)
                # print('trades', trades)
                trades_arr = trades_arr + trades
                start_hour += interval_timestamp
                stop_hour += interval_timestamp
            df = pd.DataFrame(trades_arr)
            df = df[['T','p']]
        else:
            binance_interval = _get_binance_interval(interval)
            klines = client.get_historical_klines(instrument, binance_interval, time_start, time_stop)
            df = pd.DataFrame(klines).iloc[:-1, [0,1]]
            # if interval != STRATEGY_INTERVALS.tick.value:
            #     df = validate_dataframe_timestamps(df, interval, time_start, time_stop)

        df.to_csv(join(downloaded_data_path, instrument_file_name), index=False, header=False)

    except Exception as e: 
        print('Excepted', e)
        return False

    return True