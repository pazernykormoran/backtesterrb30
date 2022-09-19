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
    async def _validate_instrument_data(self, data: DataSymbol):
        #TODO check if volume necessery or not.
        data_type = DataType.QUOTES

        start_validation_time = time()
        candles = None
        while True:
            candles = self.client.get_ohlc(symbol=data.symbol, 
                        duration=60, start=1, end=time()*1000, version='3.0', 
                        limit=1, agg_type=data_type)
            if candles != None or time() - start_validation_time > 61:
                break
            self._log('Performing Exante instrument validation, that is goint to take up to 1 minute')
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

    async def __wait(self):
        self._log('waiting for exante download 60s')
        await asyncio.sleep(60)

    #override
    async def _download_instrument_data(self, downloaded_data_path: str, instrument_file_name:str, instrument: str, interval: str, time_start: int, time_stop: int):
        self._log('Downloading exante data', instrument_file_name)
        # try:
        await self.__wait()
        if interval == 'tick': 
            limit = 5000
            floating_start = time_start
            ticks_arr = []
            iteration_n = 0
            while True:
                if floating_start >= time_stop: break
                ticks = self.client.get_ticks(symbol=instrument, 
                                    start = floating_start, 
                                    end = time_stop, 
                                    limit = limit, 
                                    agg_type=DataType.QUOTES)
                if ticks == None:
                    self._raise_error("Error while downloading ticks")
                ticks_arr = ticks + ticks_arr
                if ticks == []:
                    if iteration_n == 0:
                        self._raise_error("Error while downloading ticks ...")
                if len(ticks) == 5000:
                    floating_start = int(ticks[0].timestamp.timestamp() * 1000) + 1

                if len(ticks)<5000:
                    break
                iteration_n += 1
                await self.__wait()
            
            ticks_transformed = []
            for tck in ticks_arr:
                ticks_transformed.append([int(tck.timestamp.timestamp() * 1000), tck.ask[0].price])
            df = pd.DataFrame(ticks_transformed)
            df = df.iloc[::-1]

        else:
            limit = 5000
            exante_interval = self.__get_exante_interval(interval).value
            floating_start = time_start
            klines_arr = []
            iteration_n = 0
            while True:
                if floating_start >= time_stop: break
                klines = self.client.get_ohlc(symbol=instrument, 
                                    duration=exante_interval, 
                                    start = floating_start, 
                                    end = time_stop, 
                                    limit = limit, 
                                    agg_type=DataType.QUOTES)
                if klines == None:
                    self._raise_error("Error while downloading klines")
                klines_arr = klines + klines_arr
                if klines == []:
                    if iteration_n == 0:
                        self._raise_error("Error while downloading klines ...")
                if len(klines) == 5000:
                    floating_start = int(klines[0].timestamp.timestamp() * 1000) + (exante_interval * 1000)

                if len(klines)<5000:
                    break
                iteration_n += 1
                await self.__wait()
            
            # klines_transformed = []
            # for kl in klines_arr:
            #     # klines_transformed.append([int(round(datetime.timestamp(kl.timestamp) * 1000)), kl.open_])
            #     klines_transformed.append([int(kl.timestamp.timestamp() * 1000), kl.open_])
            # df = pd.DataFrame(klines_transformed)
            # df = df.iloc[::-1]

            klines_transformed = []
            exante_interval = CandleDurations.HOUR1.value
            prev_kl = None
            for kl in reversed(klines_arr):
                if prev_kl and kl.timestamp.timestamp() * 1000 - prev_kl.timestamp.timestamp() * 1000 >= exante_interval * 1000*2:
                    new_timestamp = int(prev_kl.timestamp.timestamp() * 1000)+ (exante_interval * 1000)
                    new_datetime = datetime.utcfromtimestamp(new_timestamp/1000)
                    klines_transformed.append([new_datetime, new_timestamp, prev_kl.close]) 
                klines_transformed.append([kl.timestamp, int(kl.timestamp.timestamp() * 1000), kl.open_])
                prev_kl = kl
            df = pd.DataFrame(klines_transformed)

        df.to_csv(join(downloaded_data_path, instrument_file_name), index=False, header=False)

