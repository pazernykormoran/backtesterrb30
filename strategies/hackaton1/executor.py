from libs.necessery_imports.executor_imports import *

class TradeExecutor(Executor):

    def __init__(self, config):
        super().__init__(config)
        
        self.trade_counter = 0

    #override
    def on_event(self, message):
        # self._log('handling on event method in executor', message)
        self.trade_counter += 1
        # if self.trade_counter == 17:
        #     self._close_all_trades()
        self._trade(message['value'], message['trade_timestamp'])

