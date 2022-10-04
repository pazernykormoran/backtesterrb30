import backtesterRB30 as bt
from random import randint

class TradeExecutor(bt.Executor):

    def __init__(self, config):
        super().__init__(config)

    #override
    def on_event(self, message):
        self._trade(message['value'], self._get_data_schema().data[randint(0,1)])

