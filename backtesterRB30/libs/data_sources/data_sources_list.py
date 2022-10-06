from backtesterRB30.libs.data_sources.binance.binance import BinanceDataSource
from backtesterRB30.libs.data_sources.dukascopy.dukascopy import DukascopyDataSource
from backtesterRB30.libs.data_sources.rb30.rb30_disk import RB30DataSource
from backtesterRB30.libs.data_sources.exante.exante import ExanteDataSource
from backtesterRB30.libs.data_sources.coingecko.coingecko import CoingeckoDataSource
from backtesterRB30.libs.data_sources.tradingview.tradingview import TradingView

class HISTORICAL_SOURCES():
    binance=BinanceDataSource
    dukascopy=DukascopyDataSource
    rb30disk=RB30DataSource
    exante=ExanteDataSource
    coingecko=CoingeckoDataSource
    tradingview= TradingView

# HISTORICAL_SOURCES_UNION = Union[BinanceDataSource, DukascopyDataSource, RB30DataSource, ExanteDataSource, CoingeckoDataSource]