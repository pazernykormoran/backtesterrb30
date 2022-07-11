
from libs.necessery_imports.model_imports import *
from asyncio import sleep
# configure model =====================================

class Model(Engine):
    
    def __init__(self, config):
        super().__init__(config)
        self.counter = 0

    #override
    def on_feed(self, data):
        
        if self.counter % 100 == 0:
            print('feed received', self.counter)
        
        if self.counter == 0:
            message = {
                'value': 10,
                'price': 200
            }
        if self.counter == 1:
            message = {
                'value': 10,
                'price': 200
            }
        if self.counter == 2:
            message = {
                'value': -10,
                'price': 100
            }
        if self.counter == 3:
            message = {
                'value': 0,
                'price': 100
            }


        # self._trigger_event(message)
        self.counter += 1



