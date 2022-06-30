# Engine-RB30

# Quick start

1. provide .env file with name of strategy existing in strategies folder like:
strategy=name_of_strategy

1. run with command: "python3 run_all.py"

# Strategy implementation using python engine

In folder strategies add folder with your strategy and create three files: "data_schema.py", "executor.py", "model.py"

In "data_schema.py" configure your input data schema and strategy interval using "DataSchema" interface and list of avaliable instruments avaliable in #TODO
~~~
from libs.necessery_imports.data_imports import *

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

In "model.py" configure your model class named Model ingeriting from Engine.
Model has to contain "on_feed" function which is triggered every interval you have choosen.
In this class, you can use "_trigger_event" function inheritet from Engine class.
~~~
from libs.necessery_imports.model_imports import *

class Model(Engine):
    
    def __init__(self, config):
        super().__init__(config)

    #override
    def on_feed(self, data):

        message = {
            'value1': 11.11,
            'value2': 'v2'
        }
        
        self._trigger_event(message)
~~~

Configure your trade executor class named TradeExecutor inheriting from Executor.
TradeExecutor contains function "on_event" triggered while your model returns event using 
function self._trigger_event. In this function, you can use "_trade" function inheritet from Executor class.
~~~
from libs.necessery_imports.executor_imports import *

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