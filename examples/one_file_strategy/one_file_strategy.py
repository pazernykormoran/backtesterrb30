from datetime import datetime
from random import randint
import backtesterRB30 as bt
import asyncio

from backtesterRB30.libs.interfaces.utils.data_schema import DataSchema

class Model(bt.Engine):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.counter = 0
        self.set_buffer_length(200)

    #override
    async def on_feed(self, data: list):
        if self.counter % 30 == 0:
            quant = randint(-2,2)
            if quant != 0:
                message = {
                    'value': quant
                }
                # await asyncio.sleep(0.01)
                await self.debug_breakpoint()
                await self.trigger_event(message)
        self.counter += 1


class TradeExecutor(bt.Executor):

    def __init__(self, *args):
        super().__init__(*args)

    #override
    async def on_event(self, message):
        await self.trade(message['value'], self.get_data_schema().data[randint(0,1)])

class Data:
    data: DataSchema ={
        'log_scale_valuation_chart': True,
        'data':[
            {
                'symbol': '2914jpjpy',
                'historical_data_source': bt.HISTORICAL_SOURCES.dukascopy,
                'main': False,
                'backtest_date_start': datetime(2021,5,1),
                'backtest_date_stop': datetime(2022,8,1),
                'trigger_feed': False,
                'interval': bt.HISTORICAL_SOURCES.dukascopy.INTERVALS.hour,
                'display_chart_in_summary': True
            },
            {
                'symbol': 'iefususd',
                'historical_data_source': bt.HISTORICAL_SOURCES.dukascopy,
                'main': True,
                'backtest_date_start': datetime(2021,5,1),
                'backtest_date_stop': datetime(2022,8,1),
                'trigger_feed': True,
                'interval': bt.HISTORICAL_SOURCES.dukascopy.INTERVALS.hour,
                'display_chart_in_summary': True
            }
        ]
    }

strategy = bt.Strategy(Model, TradeExecutor, Data)
# strategy.run()
strategy.run_in_microservices()