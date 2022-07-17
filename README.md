# Engine-RB30

# Description

Engine-RB30 is a framework to backtest and run live your market strategies.

# Quick start

1. provide .env file with name of strategy existing in strategies folder like:
~~~
strategy="folder name with strategy"
binance_api_secret="binance api secret"
binance_api_key="binance api key"
~~~
1. To install dependencies locally run: "bash install_dependencies_locally.sh"

2. Run local backtest with command: "python3 run_all.py"

# Strategy implementation using python engine

In folder "strategies" add folder with your strategy name and create three files: "data_schema.py", "executor.py", "model.py"

In "data_schema.py" configure your input data schema and strategy interval using "DataSchema" interface and list of avaliable instruments avaliable in adequate data source.
Avaliable data sources: 
- [ binance ] avaliable instruments in "historical_data_feeds/binance_instruments.txt"
- [ ducascopy ] avaliable instruments in "https://github.com/Leo4815162342/dukascopy-node"
~~~
from libs.necessery_imports.data_imports import *

data={
    'interval':STRATEGY_INTERVALS.hour,
    'data':[
        {
            'symbol': 'name1',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'main': False
        },
        {
            'symbol': 'name2',
            'historical_data_source': HISTORICAL_SOURCES.binance,
            'trigger_feed': False,
            'main': True,
        }
    ]
}
DATA = DataSchema(**data)
~~~

In "model.py" configure your model class named Model ingeriting from Engine.
Override "on_feed" function which is triggered every interval you have choosen.
In this class, you can use "_trigger_event" function inheritet from Engine class. This function triggers your "on_event" method in executor file.
In this class, you can use "_set_buffer_length" which sets buffer length that is provided to on_feed method.

All avaliable methods: 
- "_set_buffer_length"
- "_trigger_event"
- "_log"
~~~
from libs.necessery_imports.model_imports import *

class Model(Engine):
    
    def __init__(self, config):
        super().__init__(config)
        self._set_buffer_length(200)

    #override
    def on_feed(self, buffer):

        message = {
            'value1': 11.11,
            'value2': 'v2'
        }
        
        self._trigger_event(message)
~~~

In "executor.py" configure your trade executor class named TradeExecutor inheriting from Executor.
Override "on_event" triggered while your implemented model returns event. In this class, you can use "_trade" function inheritet from Executor class.

All avaliable methods: 
- "_trade"
- "_close_all_trades"
- "_get_number_of_actions"
- "_log"
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

If you are implementing piece of code that can be usefull in other strategies, use "libs" folder. It will be avaliable to import in other strategies or notebooks.
Your communication interfaces include in "libs/interfaces" folder.

# Microservice implementation

1. Add your folder with microservice named as your microservice name.
2. Add your microservice to libs/list_of_services enum.
3. Add your microservice in run.sh

Scheme of run file:
~~~
#TODO
~~~

Scheme of service file:
~~~
#TODO
~~~

# Features TODO

1. Live data feeds. Necessery is integration with fix api and real broker.
2. Trades executor with real broker. 
3. Possibility to trade in more than one instrument
4. Different intervals and time scopes for added to strategy instruments
5. Add more data sources 