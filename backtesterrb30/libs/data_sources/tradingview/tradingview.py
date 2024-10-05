from os import getenv
from typing import Union

import pandas as pd

from backtesterrb30.libs.data_sources.data_source_base import DataSource
from backtesterrb30.libs.data_sources.tradingview.downloader import (
    Interval as TRADINGVIEW_INTERVALS,
)
from backtesterrb30.libs.data_sources.tradingview.downloader import (
    TradingviewDownloader,
)
from backtesterrb30.libs.interfaces.utils.data_symbol import DataSymbol
from backtesterrb30.libs.utils.timestamps import datetime_to_timestamp


class TradingView(DataSource):
    INTERVALS = TRADINGVIEW_INTERVALS
    NAME = "tradingview"

    def __init__(self, logger=print):
        super().__init__(False, logger)
        trading_view_user = getenv("trading_view_user")
        trading_view_password = getenv("trading_view_password")
        if trading_view_user is None or trading_view_password is None:
            raise Exception(self.NAME + " No authorization heys provided")
        self.client = TradingviewDownloader(trading_view_user, trading_view_password)
        self.df_to_clip = None

    # override
    async def _validate_instrument_data(self, data: DataSymbol) -> bool:
        symbol, exchange, fut_contract = self.get_symbol_params(data.symbol)
        self.df_to_clip: pd.DataFrame = await self.client.get_hist(
            symbol,
            datetime_to_timestamp(data.backtest_date_start),
            exchange,
            data.interval,
            fut_contract,
        )
        return True

    # override
    async def _download_instrument_data(
        self,
        instrument: str,
        interval: str,
        time_start: int,
        time_stop: Union[int, None],
    ) -> pd.DataFrame:
        self._log("Downloading tradingview data", instrument, interval)
        if time_stop is None:
            df_orig = df[df["timestamp"] >= time_start]
            df = df_orig.iloc[:, [0, 1]]
            milis = self._get_interval_miliseconds(interval)
            if type(milis) != int or milis == 0:
                self._log("Warning, binance cannot get close price")
            else:
                df_close = df_orig.iloc[-1:, [0, 4]]
                df_close.columns = df.columns
            df = pd.concat([df, df_close])
        else:
            df = self.__clip_df(time_start, time_stop, self.df_to_clip)
        return df

    def _get_interval_miliseconds(self, interval: str) -> Union[int, None]:
        interval_map = {
            "1": 60 * 1000,
            "3": 3 * 60 * 1000,
            "5": 5 * 60 * 1000,
            "15": 15 * 60 * 1000,
            "30": 30 * 60 * 1000,
            "45": 45 * 60 * 1000,
            "1H": 60 * 60 * 1000,
            "2H": 2 * 60 * 60 * 1000,
            "3H": 3 * 60 * 60 * 1000,
            "4H": 4 * 60 * 60 * 1000,
            "1D": 24 * 60 * 60 * 1000,
            "1W": 7 * 24 * 60 * 60 * 1000,
            "1M": 30 * 24 * 60 * 60 * 1000,  # Approximation
        }
        return interval_map.get(interval, None)

    def __clip_df(self, time_start: int, time_stop: int, df: pd.DataFrame):
        df = df[df["timestamp"] >= time_start]
        df = df[df["timestamp"] <= time_stop]
        df = df.iloc[:-1, [1, 2]]
        return df

    @staticmethod
    def create_symbol_name(symbol: str, exchange: str, fut_contract: str = ""):
        if not symbol or symbol == "":
            raise Exception("bad symbol name")
        if not exchange or exchange == "":
            raise Exception("bad exchange name")
        return (
            f"{symbol}_{exchange}_{fut_contract}"
            if fut_contract and fut_contract != ""
            else f"{symbol}_{exchange}"
        )

    @staticmethod
    def get_symbol_params(symbol: str):
        value = symbol.split("_")
        if len(value) < 2:
            raise Exception("Bad symbol")
        if len(value) == 2:
            value.append(None)
        return tuple(value)
