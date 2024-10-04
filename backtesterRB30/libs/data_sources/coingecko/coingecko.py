from typing import Union
from datetime import datetime
import pandas as pd
from os.path import join
from backtesterRB30.libs.data_sources.data_source_base import DataSource
from backtesterRB30.libs.interfaces.historical_data_feeds.instrument_file import InstrumentFile
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
# from backtesterRB30.libs.utils.historical_sources import COINGECKO_INTERVALS
from backtesterRB30.libs.utils.timestamps import datetime_to_timestamp, timestamp_to_datetime
from pycoingecko import CoinGeckoAPI
from backtesterRB30.libs.utils.singleton import singleton
import time
import asyncio
from enum import Enum

class COINGECKO_INTERVALS_2(Enum):
    day4='day4'

class CoingeckoDataSource(DataSource):
    INTERVALS= COINGECKO_INTERVALS_2
    NAME='coingecko'

    def __init__(self, logger=print):
        super().__init__(False, logger)
        self.client = CoinGeckoAPI()
        self.__last_request_time = 0

    #override
    async def _validate_instrument_data(self, data: DataSymbol) -> bool:
        try:
            candles = self.client.get_coin_ohlc_by_id(data.symbol, vs_currency='usd', days='365')
        except Exception as e:
            if e.args[0]['error'] == 'Could not find coin with the given id':
                raise e
        df = pd.DataFrame(candles)
        if datetime_to_timestamp(data.backtest_date_start) < df.iloc[0,0]:
            raise(Exception("Error. First avaliable date of " , data.symbol, "is" , timestamp_to_datetime(df.iloc[0,0])))
        if datetime_to_timestamp(data.backtest_date_stop) > df.iloc[-1,0]:
            raise Exception("Error. Last avaliable date of " , data.symbol, "is" , timestamp_to_datetime(df.iloc[0,0]))
        return True
    
    #override
    async def _download_instrument_data(self,
                    instrument: str, interval: str, time_start: int, time_stop: Union[int, None]) -> pd.DataFrame:
        self._log('Downloading coingecko data', instrument)
        if interval == COINGECKO_INTERVALS_2.day4.value:
            actual_time = time.time()
            if actual_time - self.__last_request_time < 0.025:
                self._log('waitin')
                await asyncio.sleep(0.025 - (actual_time - self.__last_request_time))
            candles = self.client.get_coin_ohlc_by_id(instrument, vs_currency='usd', days='365')
            df_orig = pd.DataFrame(candles)
            df = df_orig[df_orig[0] >= time_start]
            if time_stop == None:
                df = df_orig.iloc[:-1, [0,1]]
            else:
                df = df[df[0] <= time_stop]
                df = df.iloc[:-1, [0,1]]
        else:
            self._raise_error('No such interval')
        return df

    def get_current_price(self, data_symbol: DataSymbol):
        price =self.client.get_price(data_symbol.symbol,vs_currencies='USD')
        return price['polkadot']['usd']

    def _get_interval_miliseconds(self, interval: str) -> Union[int,None]: 
        if interval == COINGECKO_INTERVALS_2.day4.value: return 1000*60*60*24*4

