
from libs.necessery_imports.model_imports import *

# configure model =====================================

class Model(Engine):
    
    def __init__(self, config):
        super().__init__(config)

    #override
    def on_feed(self, data):

        message = {
            'value': 11.11,
            'direction': True
        }
        
        self._trigger_event(message)



