from typing import Union
from xmlrpc.client import DateTime
from binance import Client
from binance.helpers import interval_to_milliseconds
from datetime import datetime
import pandas as pd
from os.path import join
from backtesterRB30.historical_data_feeds.modules.data_source_base import DataSource
from backtesterRB30.libs.interfaces.historical_data_feeds.instrument_file import InstrumentFile
from backtesterRB30.libs.utils.historical_sources import BINANCE_INTERVALS
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
from backtesterRB30.historical_data_feeds.modules.utils import validate_dataframe_timestamps
from os import getenv
from backtesterRB30.libs.utils.singleton import singleton

@singleton
class BinanceDataSource(DataSource):
    def __init__(self, logger=print):
        super().__init__(False, logger)
        binance_api_secret=getenv("binance_api_secret")
        binance_api_key=getenv("binance_api_key")
        self.client = Client(binance_api_key, binance_api_secret)

    #override
    async def _validate_instrument_data(self, data: DataSymbol) -> bool:
        #validate if instrument exists:
        exchange_info = self.client.get_exchange_info()
        if data.symbol not in [s['symbol'] for s in exchange_info['symbols']]:
            self._log('Error. Instrument "'+data.symbol+'" does not exists on binance.')
            return False
        #validate it timestamps perios is right:
        from_datetime_timestamp = int(round(datetime.timestamp(data.backtest_date_start) * 1000))
        if data.interval == BINANCE_INTERVALS.tick:
            binance_interval = Client.KLINE_INTERVAL_1MINUTE
        else:
            binance_interval = self.__get_binance_interval(data.interval.value)
        first_timestamp = self.client._get_earliest_valid_timestamp(data.symbol, binance_interval)
        if first_timestamp > from_datetime_timestamp:
            self._log("Error. First avaliable date of " , data.symbol, "is" , datetime.utcfromtimestamp(first_timestamp/1000.0))
            return False
        return True
    
    #override
    async def _download_instrument_data(self,
                        downloaded_data_path: str, 
                        instrument_file: InstrumentFile) -> bool:
        self._log('Downloading binance data', instrument_file.to_filename())
        if instrument_file.interval == 'tick': 
            interval_timestamp = 1000*60*60
            trades_arr = []
            start_hour = instrument_file.time_start
            stop_hour = start_hour + interval_timestamp
            while stop_hour < instrument_file.time_stop:
                trades = self.client.get_aggregate_trades(symbol=instrument_file.instrument, 
                        startTime=start_hour, endTime=stop_hour)
                # print('trades', trades)
                trades_arr = trades_arr + trades
                start_hour += interval_timestamp
                stop_hour += interval_timestamp
            df = pd.DataFrame(trades_arr)
            df = df[['T','p']]
        else:
            binance_interval = self.__get_binance_interval(instrument_file.interval)
            klines = self.client.get_historical_klines(instrument_file.instrument, 
                    binance_interval, instrument_file.time_start, instrument_file.time_stop)
            df = pd.DataFrame(klines).iloc[:-1, [0,1]]
            # if interval != STRATEGY_INTERVALS.tick.value:
            #     df = validate_dataframe_timestamps(df, interval, time_start, time_stop)

            # print('binance shape after dl: ', df.shape)
            # print('head', str(df.head(1)))
            # print('tail', str(df.tail(1)))

        df.to_csv(join(downloaded_data_path, instrument_file.to_filename()), 
                index=False, header=False)


    def _get_interval_miliseconds(self, interval: str) -> Union[int,None]: 
        return interval_to_milliseconds(self.__get_binance_interval(interval))

    def __get_binance_interval(self, interval: str) -> str :
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
