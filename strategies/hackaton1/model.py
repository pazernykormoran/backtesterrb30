
from libs.necessery_imports.model_imports import *
from random import randint
# configure model =====================================

class Model(Engine):
    
    def __init__(self, config):
        super().__init__(config)
        self.counter = 0
        self._set_buffer_length(200)

    #override
    def on_feed(self, data: list):
        
        if self.counter % 300 == 0:
            self._log('feed received', self.counter)
            self._log('data len', len(data))
            quant = randint(-2,2)
            if quant != 0:
                message = {
                    'value': quant
                }
                self._trigger_event(message)
            # for d in data:
            #     print(d)
    
        # 
        self.counter += 1



