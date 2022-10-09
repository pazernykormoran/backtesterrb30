from datetime import datetime
from random import randint
import backtesterRB30 as bt
import asyncio
from os.path import join

class Model(bt.Engine):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.state = {
            'counter': 0
        }
        self.set_buffer_length(200)
        self.live_reloading_module = self.add_reloading_module(
                join(self.config.strategy_path, 'live_reloading/live_reloading.py'))
        
    #override
    async def on_feed(self, data: list):
        await self.live_reloading_module.live_reloading_function(
                data, self.state, self.trigger_event, self.debug_breakpoint)


class TradeExecutor(bt.Executor):

    def __init__(self, *args):
        super().__init__(*args)

    #override
    async def on_event(self, message):
        await self.trade(message['value'], self.get_data_schema().data[randint(0,1)])




data={
    'log_scale_valuation_chart': True,
    'data':[
        {
            'symbol': '2914jpjpy',
            'historical_data_source': bt.HISTORICAL_SOURCES.dukascopy,
            # 'main': False,
            'backtest_date_start': datetime(2021,5,1),
            'backtest_date_stop': datetime(2022,8,1),
            'trigger_feed': False,
            'interval': bt.HISTORICAL_SOURCES.dukascopy.INTERVALS.hour,
            'display_chart_in_summary': True
        },
        {
            'symbol': 'iefususd',
            'historical_data_source': bt.HISTORICAL_SOURCES.dukascopy,
            # 'main': True,
            'backtest_date_start': datetime(2021,5,1),
            'backtest_date_stop': datetime(2022,8,1),
            'trigger_feed': True,
            'interval': bt.HISTORICAL_SOURCES.dukascopy.INTERVALS.hour,
            'display_chart_in_summary': True
        }
    ]
}
DATA = bt.validate_config(data)


strategy = bt.Strategy(Model, TradeExecutor, DATA)
strategy.run()