from typing import Union
from datetime import datetime
import pandas as pd
from os.path import join
from backtesterRB30.historical_data_feeds.modules.data_source_base import DataSource
from backtesterRB30.libs.interfaces.historical_data_feeds.instrument_file import InstrumentFile
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
from backtesterRB30.libs.utils.historical_sources import COINGECKO_INTERVALS
from backtesterRB30.libs.utils.timestamps import datetime_to_timestamp, timestamp_to_datetime
from pycoingecko import CoinGeckoAPI
from backtesterRB30.libs.utils.singleton import singleton
import time
import asyncio

@singleton
class CoingeckoDataSource(DataSource):
    def __init__(self, logger=print):
        super().__init__(False, logger)
        self.client = CoinGeckoAPI()
        self.__last_request_time = 0

    #override
    async def _validate_instrument_data(self, data: DataSymbol) -> bool:
        try:
            candles = self.client.get_coin_ohlc_by_id(data.symbol, vs_currency='usd', days='max')
        except Exception as e:
            if e.args[0]['error'] == 'Could not find coin with the given id':
                self._log('Could not find coin with the given id')
                return False
        df = pd.DataFrame(candles)
        if datetime_to_timestamp(data.backtest_date_start) < df.iloc[0,0]:
            self._log("Error. First avaliable date of " , data.symbol, "is" , timestamp_to_datetime(df.iloc[0,0]))
            return False
        if datetime_to_timestamp(data.backtest_date_stop) > df.iloc[-1,0]:
            self._log("Error. Last avaliable date of " , data.symbol, "is" , timestamp_to_datetime(df.iloc[0,0]))
            return False
        return True
    
    #override
    async def _download_instrument_data(self,
                        downloaded_data_path: str, 
                        instrument_file: InstrumentFile) -> bool:
        self._log('Downloading coingecko data', instrument_file.to_filename())
        if instrument_file.interval == COINGECKO_INTERVALS.day4.value:
            actual_time = time.time()
            if actual_time - self.__last_request_time < 0.025:
                self._log('waitin')
                await asyncio.sleep(0.025 - (actual_time - self.__last_request_time))
            candles = self.client.get_coin_ohlc_by_id(instrument_file.instrument, vs_currency='usd', days='max')
            df = pd.DataFrame(candles)
            df = df[df[0] >= instrument_file.time_start]
            df = df[df[0] <= instrument_file.time_stop]
            df = df.iloc[:-1, [0,1]]
        else:
            self._raise_error('No such interval')

        df.to_csv(join(downloaded_data_path, instrument_file.to_filename()), 
                index=False, header=False)

    def _get_interval_miliseconds(self, interval: str) -> Union[int,None]: 
        if interval == COINGECKO_INTERVALS.day4.value: return 1000*60*60*24*4

