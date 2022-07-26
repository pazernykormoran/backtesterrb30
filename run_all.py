from typing import Dict, Tuple, Type
from os import getenv, system
from dotenv import load_dotenv
import importlib
from libs.zmq.zmq import ZMQ
from enum import Enum
from sys import argv
from pydantic import BaseModel
import time
from libs.list_of_services.list_of_services import SERVICES_ARRAY
from libs.data_feeds.data_feeds import DataSchema, HISTORICAL_SOURCES, STRATEGY_INTERVALS
from datetime import datetime

#TODO hardcoded backtest mode: 
backtest_state='true'

args = argv
if len(args) > 1:
    if args[1] == '-backtest':
        backtest_state='true'


print('checking env file')
from os.path import exists
file_exists = exists(".env")
if not file_exists:
    print('Error: ".env" file does not exists. Create one and provide necessery information like: \nstrategy=name_of_strategy')
    exit()


load_dotenv()
strategy_name = getenv('STRATEGY_NAME')
if not strategy_name or strategy_name == '':
    print('Error: provide strategy name in .env file like: \nstrategy=name_of_strategy')
    exit()
print('running strategy name: ', strategy_name)


services_array = SERVICES_ARRAY

def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def create_port_configurations():
    start_port = 1000
    assigned = False
    while not assigned:
        port_in_use = False
        for port in range(start_port,start_port+50):
            if is_port_in_use(port):
                print('Port '+str(port)+ ' is already in use, changing port range.')
                start_port += 50
                port_in_use = True
                break
        if port_in_use == False:
            assigned = True
            
    with open('.additional_configs', 'w') as f:
        for i, service in enumerate(services_array):
            f.write(service+'_pubs='+str(start_port+i)+'\n')
            subs_str = service+'_subs='
            for j in range(len(services_array)):
                if j != i:
                    subs_str += str(start_port+j)+','
            subs_str = subs_str[:-1]
            subs_str += '\n'
            f.write(subs_str)
        
        
def validate_strategy(strategy_name):
    try:
        data_schema: DataSchema = importlib.import_module('strategies.'+strategy_name+'.data_schema').DATA
        model_module = importlib.import_module('strategies.'+strategy_name+'.model')
        executor_module = importlib.import_module('strategies.'+strategy_name+'.executor')
    except Exception as e:
        print('Excepted: ', e)
        print('Error. Excepted while loading modules. Check if all necessery files are in your strategy')
        print('Your strategy in folder strategies/'+strategy_name+'should contain files: "data_schema.py", "executor.py", "model.py"' )
        print('Read more in readme file')
        exit()
    if backtest_state:
        if data_schema.backtest_date_start == None:
            print('Error. You must provide "backtest_date_start" field in data_schema file while you are backtesting your strategy')
            exit()
        if data_schema.backtest_date_start >= data_schema.backtest_date_stop: 
            print('Error. You have provided "backtest_date_start" is equal or bigger than "backtest_date_start" ')
            exit()
        if data_schema.interval.value == STRATEGY_INTERVALS.tick.value: 
            print('Error. Tick interval is not implemented yet ')
            exit()

        if [data_schema.backtest_date_start.hour,
            data_schema.backtest_date_start.minute,
            data_schema.backtest_date_start.second,
            data_schema.backtest_date_start.microsecond] != [0,0,0,0]:
            print('Error. Provide your "backtest_date_start" and "backtest_date_stop" in a day accuracy like: "backtest_date_start": datetime(2020,6,1)')
            exit()

        number_of_mains = 0
        for data in data_schema.data:
            if data.historical_data_source.value not in (HISTORICAL_SOURCES.binance.value, HISTORICAL_SOURCES.ducascopy.value): 
                print('Error. This historical_data_source not implemented yet')
                exit()
            if data.main == True:
                number_of_mains += 1
        if number_of_mains != 1:
            print('Error. Yout "data_schema.py" must have one main instrument')
            exit()

    class Asd:
        name = "test",
        strategy_name = strategy_name
    config = Asd()
    model = model_module.Model(config)
    executor = executor_module.TradeExecutor(config)

print('validating strategy')
validate_strategy(strategy_name)
print('preparing microservice ports configuration')
create_port_configurations()
with open('.additional_configs', 'a') as f:
    f.write('backtest_state='+backtest_state)
if backtest_state:
    system('sudo bash run.sh') 
else:
    print('live strategies not implemented')
    
# print('starting all containers')
# system('sudo docker-compose up --build --remove-orphans')


"""

-sources:  
    - implement nasdaq api? https://blog.data.nasdaq.com/getting-started-with-the-nasdaq-data-link-api
                https://data.nasdaq.com/tools/python
    - yachoo finance - only day data od slower
    - 
- make tick data working.
ZROBIC DATA LOADER który: 
najpierw każde aktywo ma ustawiany swoja czestotliwość oraz parametr trigger feed. Jak czestotliwość w jakimkolwiek parametrze 
jest inna niż w reszcie to musisz pamiętać. że będzie ona uzupełnina. 
- jak danych jeszcze nie ma to zerami
- jak jakaś dana już była to tą właśnie daną. 
LODING DANYCH:
1. dla każdego okresu: 
    1.1 dla każdego aktwa z data_schema:
        1.1.1 pobierz dane w danym okresie. Jeśli nic nie pobrało. Zapisz pusty plik.
WCZYTYWANIE:   
2. dla każdego okresu:
    2.1 dla każdego aktywa z data schema:
        2.1.1 wczytaj wszystkie ramki do dataframeów. Jeśli nie ma jakiegokolwiek pliku to zwróć błąd.
        2.1.2 po kolei synchronizuj ramki i od razu wysyłaj aby oszczędzić pamięć.
            2.1.2.1 każdy kolejny najmniejszy timestamp spośród aktywów które mają trigger_feed = true.

- add checking if symbols are not duplicated in data_schema
- add checking in data_schema if historical source fits to the interval source.
- checking if all necessery keys are provoded in .env
- prepare ability to every chart has different time rane. 
- handle better checking avaliable times than in 'historical_data_feeds/temporary_ducascopy_list.json'
- handle scenario when your data is too big interval
zrobic validacje gludosci danych również przy wczytywanieu.
- interfaces for all functions
- make all other functions inpossible to use and override in model and executor class.
- add own interval and own data range for all the insruments in dataschema. it requires an inteligent data integration.
- what with strategies that wants to play on  many instruments? every instrument will be required to flag as main   
    and the trade function must be overriten for this case and getting one more argument which is instrument.
- add clean cache command
-Define that credentials are necessery. For example you dont need to pass binance credentials if you not using it.
"""
