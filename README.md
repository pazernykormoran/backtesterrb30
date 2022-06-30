# Engine-RB30

# Quick start

1. provide .env file with name of strategy existing in strategies folder like:
strategy=name_of_strategy

1. run with command: "python3 run_all.py"

# Strategy implementation using python engine

In folder strategies add folder with your strategy and create file "strategy.py"

Add necessery imports in the top of your strategy file. Under necessery imports you can import any other library as well.
~~~
from libs.necessery_imports.necessery_imports import *
~~~

Configure your data feeds schema and strategy interval using "DataSchema" interface and list of avaliable instruments avaliable in #TODO
~~~
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
~~~

Configure your event schema. Its interface between your model function and event function.
~~~
class EventSchema(BaseModel):
    value1:float
    value2:str
~~~

Configure your model what means your function that is triggered every interval you have choosen.
In this function, you can use "_trigger_event" function inheritet from Engine class.
~~~
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
~~~

Configure your trade executor function what is a function triggered while your model returns event using 
function self._trigger_event and pass to is object fitting EventSchema interface. In this function, you can use "_trade" function inheritet from Executor class.
~~~
class TradeExecutor(Executor):

    def __init__(self, config):
        super().__init__(config)

    #override
    def on_event(self, message):
        # your function body here
        trade_value = 30
        self._trade(trade_value)
~~~

# Library implementation

If you implement come piece of code that can be usefull in other strategies use "libs".
In "libs" folder create folder with your library and it will be avaliable to import froma any strategy code.

# Data feed implementation

in progress