from libs.necessery_imports.executor_imports import *

# configure trade executor =====================================

class TradeExecutor(Executor):

    def __init__(self, config):
        super().__init__(config)

    #override
    def on_event(self, message):
        self._log('handling on event method in exeturor', message)
        self._trade(message['value'], message['direction'])

