from datetime import datetime
from random import randint
import backtesterrb30 as bt
from os.path import join

class Model(bt.Engine):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.state = {
            'counter': 0
        }
        self.set_buffer_length(100)
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



class Data:
    data={
        'log_scale_valuation_chart': True,
        'data':[
            {
                'symbol': '2914jpjpy',
                'historical_data_source': bt.HISTORICAL_SOURCES.dukascopy,
                'backtest_date_start': datetime(2021,5,1),
                'backtest_date_stop': datetime(2022,8,1),
                'trigger_feed': False,
                'interval': bt.HISTORICAL_SOURCES.dukascopy.INTERVALS.hour,
                'display_chart_in_summary': True
            },
            {
                'symbol': 'iefususd',
                'historical_data_source': bt.HISTORICAL_SOURCES.dukascopy,
                'backtest_date_start': datetime(2021,5,1),
                'backtest_date_stop': datetime(2022,8,1),
                'trigger_feed': True,
                'interval': bt.HISTORICAL_SOURCES.dukascopy.INTERVALS.hour,
            },
            {
                'symbol': 'bitcoin',
                'historical_data_source': bt.HISTORICAL_SOURCES.coingecko,
                'backtest_date_start': datetime(2019,5,1),
                'backtest_date_stop': datetime(2022,8,1),
                'interval': bt.HISTORICAL_SOURCES.coingecko.INTERVALS.day4,
                'display_chart_in_summary': True
            },
            {
                'symbol': 'ethereum',
                'historical_data_source': bt.HISTORICAL_SOURCES.coingecko,
                'backtest_date_start': datetime(2019,5,1),
                'backtest_date_stop': datetime(2022,8,1),
                'interval': bt.HISTORICAL_SOURCES.coingecko.INTERVALS.day4,
            }
        ]
    }

strategy = bt.Strategy(Model, TradeExecutor, Data, debug= True)
strategy.run()