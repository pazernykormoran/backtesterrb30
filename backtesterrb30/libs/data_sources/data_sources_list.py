from backtesterrb30.libs.data_sources.binance.binance import BinanceDataSource
from backtesterrb30.libs.data_sources.coingecko.coingecko import CoingeckoDataSource
from backtesterrb30.libs.data_sources.dukascopy.dukascopy import DukascopyDataSource
from backtesterrb30.libs.data_sources.exante.exante import ExanteDataSource
from backtesterrb30.libs.data_sources.rb30.rb30_disk import RB30DataSource
from backtesterrb30.libs.data_sources.tradingview.tradingview import TradingView


class HISTORICAL_SOURCES:
    binance = BinanceDataSource
    dukascopy = DukascopyDataSource
    rb30disk = RB30DataSource
    exante = ExanteDataSource
    coingecko = CoingeckoDataSource
    tradingview = TradingView


# HISTORICAL_SOURCES_UNION = Union[BinanceDataSource, DukascopyDataSource, RB30DataSource, ExanteDataSource, CoingeckoDataSource]
