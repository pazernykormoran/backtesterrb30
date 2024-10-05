from datetime import datetime
from random import randint
import backtesterrb30 as bt

class Model(bt.Engine):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.counter = 0
        self.set_buffer_length(10)

    #override
    async def on_feed(self, data: list):
        # print('data first', data[0])
        if self.counter % 5 == 0:
            quant = randint(-2,2)
            if quant != 0:
                message = {
                    'value': quant
                }
                await self.trigger_event(message)
        self.counter += 1


class TradeExecutor(bt.Executor):

    def __init__(self, *args):
        super().__init__(*args)

    #override
    async def on_event(self, message):
        await self.trade(message['value'], \
                self.get_data_schema().data[randint(0,1)])

class Data:
    data: bt.DataSchema ={
        'log_scale_valuation_chart': True,
        'data':[
            {
                'symbol': 'BTCUSDT_BINANCE',
                'historical_data_source': bt.HISTORICAL_SOURCES.tradingview,
                'backtest_date_start': datetime(2020,5,1),
                'backtest_date_stop': datetime(2024,8,1),
                'interval': bt.HISTORICAL_SOURCES.tradingview.INTERVALS.in_daily,
            },
            {
                'symbol': 'ETHUSDT_BINANCE',
                'historical_data_source': bt.HISTORICAL_SOURCES.tradingview,
                'backtest_date_start': datetime(2020,5,1),
                'backtest_date_stop': datetime(2024,8,1),
                'interval': bt.HISTORICAL_SOURCES.tradingview.INTERVALS.in_daily,
            }
        ]
    }

strategy = bt.Strategy(Model, TradeExecutor, Data)

def main():
    strategy.run()
