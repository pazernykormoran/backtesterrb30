# Backtester-RB30

## Description

Backtester-RB30 is a framework for stock market analysis.

## Installation

> pip3 install backtesterRB30

## Quick start

### Basic example
Basic strategy example making random trades.
> python3 examples/basic_example/basic_example.py

### Advanced example
More advanced example with debug mode enabled, live debug code reloads  and more data sources with not equal intervals. 
> sudo python3 examples/live_reloading_example/live_reloading_strategy.py
Root privilages are required.

### Issues:
If matplotlib plots doesn't works in virtual environment try:
>sudo apt-get install python3-tk


# Strategy implementation

## Define input data
List of instruments provided every step of your strategy.
Avaliable data sources: 
- [ binance ] avaliable instruments in "historical_data_feeds/data_sources/binance/binance_instruments.txt"
- [ dukascopy ] avaliable instruments in https://github.com/Leo4815162342/dukascopy-node
- [ coingecko ] avaliable instruments in https://www.coingecko.com/
- [ exante ] avaliable instruments in https://drive.google.com/drive/folders/1qJAGedEWhGehG2Hh48ITgE7LjGWwyzOw?usp=sharing
- [ tradingview ] avaliable instruments in https://www.tradingview.com/

Dictionary must fit to bt.DataSchema interface
~~~
import backtesterRB30 as bt
from datetime import datetime

class Data:
    data={
        'log_scale_valuation_chart': True,
        'data':[
            {
                'symbol': 'bitcoin',
                'historical_data_source': bt.HISTORICAL_SOURCES.coingecko,
                'backtest_date_start': datetime(2019,5,1),
                'backtest_date_stop': datetime(2022,8,1),
                'interval': bt.HISTORICAL_SOURCES.coingecko.INTERVALS.day4,
            },
            {
                'symbol': 'ethereum',
                'historical_data_source': bt.HISTORICAL_SOURCES.coingecko,
                'backtest_date_start': datetime(2019,5,1),
                'backtest_date_stop': datetime(2022,8,1),
                'interval': bt.HISTORICAL_SOURCES.coingecko.INTERVALS.day4,
            }
        ]
    }
~~~

## Define Engine class
Engine class "on_feed()" function is being called every interval of your strategy. attribute "data" provided to "on_feed()" is an array with timestamp and symbols values. In this example data will look like:

~~~
data = [[timestamps array with 100 elements],
        [bitcoin prices array with 100 elements],
        [ethereum prices array with 100 elements]]
~~~
Number of elements in arrays (buffer length) are being defined by set_buffer_length() method.
You can use "_trigger_event()" function to send any message to executor module.
More about avaliable methods: 

https://pazernykormoran.github.io/Backtester-RB30/backtesterRB30.python_engine.html

Below example sending messages with random values:

~~~
import backtesterRB30 as bt
from random import randint

class Engine(bt.Engine):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.counter = 0
        self.set_buffer_length(100)

    #override
    async def on_feed(self, data: list):
        if self.counter % 5 == 0:
            quant = randint(-2,2)
            if quant != 0:
                message = {
                    'value': quant
                }
                await self.trigger_event(message)
        self.counter += 1
~~~

## Define Executor class
Executor class manages transactions and current money level. You can use "trade()" function here. Method "on_event" is being triggered by Engine class. Making trade, you have to provide instrument on which to do trade. One of instruments defined in Data class.

More about avaliable methods:

https://pazernykormoran.github.io/Backtester-RB30/backtesterRB30.python_executor.html
~~~
import backtesterRB30 as bt
from random import randint

class TradeExecutor(bt.Executor):

    def __init__(self, *args):
        super().__init__(*args)

    #override
    async def on_event(self, message):
        await self.trade(message['value'], \
                self.get_data_schema().data[randint(0,1)])
~~~

## Strategy run
~~~
strategy = bt.Strategy(Model, TradeExecutor, Data)
strategy.run()
~~~

By default strategy is being run in backtest mode.
Full code example is in folder "examples/basic_example/basic_example.py"


# Data Sources

Some data sources requires providing authentication keys which you have to find on your own. For this puropuse you have to provide ".env" file in the folder which from you are running your strategy. Example:
~~~
KEY="value"
KEY2="value2"
KEY3="value3"
~~~

## Descriptions:

1. Coingecko

Coingecko is working without any keys.

2. Dukascopy

For dukascopy no keys are required. But for this data source working, you have to have node and npm with npx installed.
~~~
sudo apt  install curl
curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -
sudo apt install -y nodejs
sudo apt install -y npm
npm install dukascopy-node --save
~~~

3. Binance

~~~
binance_api_secret="value"
binance_api_key="value"
~~~

4. Exante

In exante you have to privide keys for basic auth. Now working only with live accounts.
~~~
exante_app_id='value'
exante_access_key = 'value'
~~~

5. Tradingview

In tradingview you have to provide login and password to tradingview account.
~~~
trading_view_user='value'
trading_view_password='value'
~~~

# Debug mode

## Usage of debug mode
Debug mode is only avaliable with root privilages because of keyboard package usage. To run your strategy with allowed debugging , provide debug parameter to Strategy class constructor.
~~~
import backtesterRB30 as bt
strategy = bt.Strategy(Engine, TradeExecutor, Data, debug=True)
strategy.run()
~~~

Framework gives you access to debug mode that allows you printing summary charts and descriptions every step of your debug. To enable using debug mode while implementing your strategy follow below steps:
- Use "debug_breakpoint()" method somewhere in your "on_feed" method. This works as breakpoint while debugging.
- Press "ctrl+d" in any moment during backtest loop. This will cause entering debug mode and stopping the code in the nearest moment when your code occurs "debug_breakpoint" function.
- Press "ctrl+n" for next. You should see summary and charts printed for current moment of backtest.
- Press "ctrl+q" for quit debug mode.


## Live code reloads in debug mode
Debug mode enables user to develop his strategies live with backtest running in debud mode. Thats only possible importable modules to bo live reloaded. To achive this use "add_reloading_module(path_to_module)" in the init function in your Engine class. As an argument to the function pass the path to the module you are goint to be reloaded after every step of your debug. Path to the module is absoule path but you can use your "self.config.strategy_path + relative path".


# Data source implementation

TODO. 

