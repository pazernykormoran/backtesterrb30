from xnt.http_api import HTTPApi, current_api, AuthMethods, CandleDurations, DataType
import pandas as pd
from os.path import join
from time import time, sleep
from datetime import datetime
from historical_data_feeds.modules.data_source_base import DataSource
from libs.utils.historical_sources import EXANTE_INTERVALS
from libs.interfaces.utils.data_symbol import DataSymbol
from libs.utils.singleton import singleton
from os import getenv
import asyncio

@singleton
class ExanteDataSource(DataSource):
    def __init__(self, logger=print):
        super().__init__(True, logger)
        exante_app_id=getenv("exante_app_id")
        exante_access_key=getenv("exante_access_key")
        self.client = HTTPApi(AuthMethods.BASIC, appid=exante_app_id, acckey=exante_access_key)

    def __get_exante_interval(self, interval: str):
        if interval == 'minute': return CandleDurations.MIN1
        if interval == 'minute5': return CandleDurations.MIN5
        if interval == 'minute30': return CandleDurations.MIN30
        if interval == 'hour': return CandleDurations.HOUR1
        if interval == 'day': return CandleDurations.DAY1

    #override
    async def validate_instrument_data(self, data: DataSymbol):
        #TODO check if volume necessery or not.
        data_type = DataType.TRADES

        start_validation_time = time()
        candles = None
        while True:
            candles = self.client.get_ohlc(symbol=data.symbol, 
                        duration=60, start=1, end=time()*1000, version='3.0', 
                        limit=1, agg_type=data_type)
            if candles != None or time() - start_validation_time > 61:
                break
            self._log('Performing validation, that is goint to take up to 1 minute')
            await asyncio.sleep(10)
        if candles == None:
            self._log('Error. Instrument "'+data.symbol+'" probably does not exists on exante.')
            return False
        # from_datetime_timestamp = int(from_datetime.timestamp() * 1000)
        first_datetime = candles[0].timestamp
        if first_datetime > data.backtest_date_start:
            self._log("Error. First avaliable date of " , data.symbol, "is" , first_datetime)
            return False
        return True

    def __wait(self):
        self._log('waiting for exante download 60s')
        sleep(60)

    #override
    def download_instrument_data(self, downloaded_data_path: str, instrument_file_name:str, instrument: str, interval: str, time_start: int, time_stop: int) -> bool:
        self._log('downloading exante data', instrument_file_name)
        try:
            self.__wait()
            if interval == 'tick': 
                # todo
                trades_arr=[]
                df = pd.DataFrame(trades_arr)
                df = df[['T','p']]
            else:
                limit = 5000
                exante_interval = self.__get_exante_interval(interval).value
                if abs(time_start - time_stop) > limit*exante_interval*1000:
                    #TODO
                    self._log('to big amout of candles')
                    return False

                klines = self.client.get_ohlc(symbol=instrument, duration=exante_interval, start = time_start, end = time_stop, limit = limit)
                
                klines_arr = klines
                
                klines_transformed = []
                for kl in klines_arr:
                    # klines_transformed.append([int(round(datetime.timestamp(kl.timestamp) * 1000)), kl.open_])
                    klines_transformed.append([int(kl.timestamp.timestamp() * 1000), kl.open_])
                df = pd.DataFrame(klines_transformed)
                df = df.iloc[::-1]

            df.to_csv(join(downloaded_data_path, instrument_file_name), index=False, header=False)

        except Exception as e: 
            self._log('Excepted', e)
            return False

        return True
