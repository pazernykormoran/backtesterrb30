
from libs.necessery_imports.model_imports import *
from asyncio import sleep
import pandas as pd
# configure model =====================================

class Model(Engine):
    
    def __init__(self, config):
        super().__init__(config)
        self.counter = 0
        self._set_buffer_length(200)

    #override
    def on_feed(self, data: pd.DataFrame):
        
        if self.counter % 1000 == 0:
            print('feed received', self.counter)
            print('data len', len(data))
            for d in data:
                print(d)
    
        # self._trigger_event(message)
        self.counter += 1



