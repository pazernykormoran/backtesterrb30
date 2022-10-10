from typing import Union
from xmlrpc.client import DateTime
from binance import Client
from binance.helpers import interval_to_milliseconds
from datetime import datetime
import pandas as pd
from os.path import join
from backtesterRB30.libs.data_sources.data_source_base import DataSource
from backtesterRB30.libs.interfaces.historical_data_feeds.instrument_file import InstrumentFile
# from backtesterRB30.libs.utils.historical_sources import BINANCE_INTERVALS
# from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
from backtesterRB30.libs.data_sources.utils import validate_dataframe_timestamps
from os import getenv
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
from backtesterRB30.libs.utils.singleton import singleton
from enum import Enum

class BINANCE_INTERVALS_2(str, Enum):
    tick: str='tick'
    minute: str='minute'
    minute3: str='minute3'
    minute5: str='minute5'
    minute15: str='minute15'
    minute30: str='minute30'
    hour: str='hour'
    hour2: str='hour2'
    hour4: str='hour4'
    hour6: str='hour6'
    hour8: str='hour8'
    hour12: str='hour12'
    day: str='day'
    day3: str='day3'
    week: str='week'
    month: str='month'

class BinanceDataSource(DataSource):
    INTERVALS= BINANCE_INTERVALS_2
    NAME='binance'

    def __init__(self, logger=print):
        super().__init__(False, logger)
        binance_api_secret=getenv("binance_api_secret")
        binance_api_key=getenv("binance_api_key")
        if binance_api_secret == None or binance_api_key == None:
            raise Exception(self.NAME + ' No authorization heys provided')
        self.client = Client(binance_api_key, binance_api_secret)
        self._test_counter = 0

    #override
    async def _validate_instrument_data(self, data: DataSymbol) -> bool:
        #validate if instrument exists:
        exchange_info = self.client.get_exchange_info()
        if data.symbol not in [s['symbol'] for s in exchange_info['symbols']]:
            self._log('Error. Instrument "'+data.symbol+'" does not exists on binance.')
            return False
        #validate it timestamps perios is right:
        from_datetime_timestamp = int(round(datetime.timestamp(data.backtest_date_start) * 1000))
        if data.interval == BINANCE_INTERVALS_2.tick:
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
                        instrument: str, interval: str, time_start: int, time_stop: Union[int, None]) -> pd.DataFrame:
        self._log('Downloading binance data', instrument)
        if interval == 'tick': 
            interval_timestamp = 1000*60*60
            trades_arr = []
            start_hour = time_start
            stop_hour = start_hour + interval_timestamp
            while stop_hour < time_stop:
                trades = self.client.get_aggregate_trades(symbol=instrument, 
                        startTime=start_hour, endTime=stop_hour)
                # print('trades', trades)
                trades_arr = trades_arr + trades
                start_hour += interval_timestamp
                stop_hour += interval_timestamp
            df = pd.DataFrame(trades_arr)
            df = df[['T','p']]
        else:
            binance_interval = self.__get_binance_interval(interval)
            klines = self.client.get_historical_klines(instrument, 
                    binance_interval, time_start, time_stop)
            df_orig = pd.DataFrame(klines)
            df = df_orig.iloc[:-1, [0,1]]
            if time_stop == None:
                df = df_orig.iloc[:, [0,1]]
                milis = self._get_interval_miliseconds(interval)
                if type(milis) != int or milis == 0:
                    self._log('Warning, binance cannot get close price')
                else:
                    df_close = df_orig.iloc[-1:, [0,4]] 
                    df_close.columns = df.columns
                df = pd.concat([df, df_close])

            # if interval != STRATEGY_INTERVALS.tick.value:
            #     df = validate_dataframe_timestamps(df, interval, time_start, time_stop)

            # print('binance shape after dl: ', df.shape)
            # print('head', str(df.head(1)))
            # print('tail', str(df.tail(1)))

        return df

    def get_current_price(self, symbol: DataSymbol):
        # self._test_counter += 1
        # print('binance get curren price', self._test_counter)
        price = self.client.get_symbol_ticker(symbol = symbol.symbol)
        return price['price']

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
