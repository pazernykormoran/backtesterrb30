
from python_engine.engine import Engine
from pydantic import BaseModel
from libs.data_feeds.data_feeds import IntervalConfigurator, STRATEGY_INTERVALS

IntervalConfigurator.set_strategy_interval(STRATEGY_INTERVALS.hour)
IntervalConfigurator.add_symbol()


class EventSchema(BaseModel):
    value1:float
    value2:str


class Model(Engine):

    
    def __init__(self):
        super().__init__()

    #override
    def on_feed(self, data):
        super
        message = {
            'value1': 11.11,
            'value2': 'v2'
        }
        
        self._trigger_event(EventSchema(**message))


class Trade_executor():

    #override
    def on_event():
        pass

