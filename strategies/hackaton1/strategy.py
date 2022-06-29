
from libs.necessery_imports.necessery_imports import *


# configure data feed =====================================

data={
    'interval':STRATEGY_INTERVALS.hour,
    'data':[
        {
            'symbol': 'name1',
            'main': False
        },
        {
            'symbol': 'name2',
            'trigger_feed': False,
            'main': True,
        }
    ]
}
DATA = DataSchema(**data)



# configure model =====================================

class EventSchema(BaseModel):
    value1:float
    value2:str


class Model(Engine):
    
    def __init__(self, config):
        super().__init__(config)

    #override
    def on_feed(self, data):

        message = {
            'value1': 11.11,
            'value2': 'v2'
        }
        
        self._trigger_event(EventSchema(**message))



# configure trade executor =====================================

class TradeExecutor(Executor):

    def __init__(self, config):
        super().__init__(config)

    #override
    def on_event(self, message):
        pass

