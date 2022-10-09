# Engine-RB30

# Description

Backtester-RB30 is a framework for stock market analysis.

# Installation

> sudo pip3 install git+https://github.com/pazernykormoran/Backtester-RB30

# Quick start

Create .env file inside repository:
~~~
STRATEGY_PATH="examples/basic_example"
~~~

Run example strategy calling:
> sudo python3 run_all.py

# Strategy implementation

## Create strategy files

    .
    ├── strategy_name                    
    │   ├── model.py           
    │   ├── executor.py          
    │   └── data_schema.py 
    ├── run_all.py            
    └── .env

### data_schema.py:
Here you define your input array to strategy.
Avaliable data sources: 
- [ binance ] avaliable instruments in "historical_data_feeds/data_sources/binance/binance_instruments.txt"
- [ dukascopy ] avaliable instruments in https://github.com/Leo4815162342/dukascopy-node
- [ coingecko ] avaliable instruments in https://www.coingecko.com/
- [ exante ] avaliable instruments in https://drive.google.com/drive/folders/1qJAGedEWhGehG2Hh48ITgE7LjGWwyzOw?usp=sharing

~~~
import backtesterRB30 as bt
from datetime import datetime

data={
    'log_scale_valuation_chart': True,
    'data':[
        {
            'symbol': '2914jpjpy',
            'historical_data_source': bt.HISTORICAL_SOURCES.dukascopy,
            'main': False,
            'backtest_date_start': datetime(2021,5,1),
            'backtest_date_stop': datetime(2022,8,1),
            'trigger_feed': False,
            'interval': bt.HISTORICAL_SOURCES.dukascopy.INTERVALS.hour,
            'display_chart_in_summary': True
        },
        {
            'symbol': 'iefususd',
            'historical_data_source': bt.HISTORICAL_SOURCES.dukascopy,
            'main': True,
            'backtest_date_start': datetime(2021,5,1),
            'backtest_date_stop': datetime(2022,8,1),
            'trigger_feed': True,
            'interval': bt.HISTORICAL_SOURCES.dukascopy.INTERVALS.hour,
            'display_chart_in_summary': True
        }
    ]
}
DATA = bt.validate_config(data)
~~~

### model.py:
Model module "on_feed" function is being called every interval of your strategy. You can use "_trigger_event" function to send any message to executor module.

More about avaliable functions: 

https://pazernykormoran.github.io/Backtester-RB30/backtesterRB30.python_engine.html

~~~
import backtesterRB30 as bt
from random import randint

class Model(bt.Engine):
    
    def __init__(self, config):
        super().__init__(config)
        self.counter = 0
        self.set_buffer_length(200)

    #override
    async def on_feed(self, data: list):
        if self.counter % 30 == 0:
            quant = randint(-2,2)
            if quant != 0:
                message = {
                    'value': quant
                }
                self.trigger_event(message)
        self.counter += 1
~~~

### executor.py:
Executor module manages transactions and current money level. You can use "trade" function here.

More about avaliable functions:

https://pazernykormoran.github.io/Backtester-RB30/backtesterRB30.python_executor.html
~~~
import backtesterRB30 as bt
from random import randint

class TradeExecutor(bt.Executor):

    def __init__(self, config):
        super().__init__(config)

    #override
    def on_event(self, message):
        self.trade(message['value'], self.get_data_schema().data[randint(0,1)])
~~~

### run.py:
~~~
from backtesterRB30 import run_all_microservices
run_all_microservices()
~~~

### .env:
~~~
STRATEGY_PATH="strategy_name"
~~~
## run it calling:
> sudo python3 run_all.py

#
# Requirements
For dukascopy data source working you have to have node and npm with npx installed.
~~~
sudo apt  install curl
curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -
sudo apt install -y nodejs
sudo apt install -y npm
npm install dukascopy-node --save
~~~

# Debug mode

## Usage of debug mode
Debug mode is only avaliable with root privilages because of keyboard package usage.
Framework gives you access to debug mode that allows you printing summary charts and descriptions every step of your debug. To enable using debug mode while implementing your strategy follow below steps:
- Use "debug_breakpoint" method somewhere in your "on_feed" method. This works as breakpoint while debugging. The code will stop in this place.
- Press "ctrl+d" in any moment during backtest loop. This will cause entering debug mode and stopping the code in the nearest moment when your code occurs "debug_breakpoint" function.
- Press "ctrl+n" for next. You should see summary and charts printed for current moment of backtest.
- Press "ctrl+q" for quit debug mode.

#TODO gif

## Live code reloads in debug mode
Debug mode enables user to develop his strategies live with backtest running in debud mode. Thats only possible importable modules to bo live reloaded. To achive this use "add_reloading_module(path_to_module)" in the init function in your Model class. As an argument to the function pass the path to the module you are goint to be reloaded after every step of your debug.

example:

~~~
# TODO
~~~

# Library implementation

If you are implementing piece of code that can be usefull in other strategies, use "libs" folder. It will be avaliable to import in other strategies or notebooks.
Your communication interfaces include in "libs/interfaces" folder.

# Data source implementation

2. Add folder to "historical_data_feeds/data_sources". Create file with class inheriting from "DataSource" abstract class.
3. Register your class in "historical_data_feeds/data_sources/data_sources_list.py" 

