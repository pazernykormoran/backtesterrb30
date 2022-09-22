from backtesterRB30.libs.utils.executor_imports import *

class TradeExecutor(Executor):

    def __init__(self, config):
        super().__init__(config)

    #override
    def on_event(self, message):
        self._trade(message['value'])

