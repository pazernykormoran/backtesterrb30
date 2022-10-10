import backtesterRB30 as bt
from random import randint

class TradeExecutor(bt.Executor):

    def __init__(self, *args):
        super().__init__(*args)

    #override
    async def on_event(self, message):
        await self.trade(message['value'], self.get_data_schema().data[randint(0,1)])

