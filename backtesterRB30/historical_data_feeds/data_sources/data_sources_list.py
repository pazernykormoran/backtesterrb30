from backtesterRB30.historical_data_feeds.data_sources.binance.binance import BinanceDataSource
from backtesterRB30.historical_data_feeds.data_sources.dukascopy.dukascopy import DukascopyDataSource
from backtesterRB30.historical_data_feeds.data_sources.rb30.rb30_disk import RB30DataSource
from backtesterRB30.historical_data_feeds.data_sources.exante.exante import ExanteDataSource
from backtesterRB30.historical_data_feeds.data_sources.coingecko.coingecko import CoingeckoDataSource
from typing import Union

class HISTORICAL_SOURCES():
    binance=BinanceDataSource
    dukascopy=DukascopyDataSource
    rb30disk=RB30DataSource
    exante=ExanteDataSource
    coingecko=CoingeckoDataSource

# HISTORICAL_SOURCES_UNION = Union[BinanceDataSource, DukascopyDataSource, RB30DataSource, ExanteDataSource, CoingeckoDataSource]