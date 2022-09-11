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
from libs.data_feeds.data_feeds import DataSchema
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
    # try:
    data_schema: DataSchema = importlib.import_module('strategies.'+strategy_name+'.data_schema').DATA
    model_module = importlib.import_module('strategies.'+strategy_name+'.model')
    executor_module = importlib.import_module('strategies.'+strategy_name+'.executor')
    # except Exception as e:
    #     print('Excepted: ', e)
    #     print('Error. Excepted while loading modules. Check if all necessery files are in your strategy')
    #     print('Your strategy in folder strategies/'+strategy_name+'should contain files: "data_schema.py", "executor.py", "model.py"' )
    #     print('Read more in readme file')
    #     exit()

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
- add data sources:  
    - implement nasdaq api? https://blog.data.nasdaq.com/getting-started-with-the-nasdaq-data-link-api
                https://data.nasdaq.com/tools/python
    - yachoo finance - only day data od slower
    - coingecko api.
- add checking if symbols are not duplicated in data_schema
- add checking in data_schema if historical source fits to the interval source.
- checking if all necessery keys are provoded in .env
- handle better checking avaliable times than in 'historical_data_feeds/temporary_ducascopy_list.json'
- interfaces for all functions
- make all other functions inpossible to use and override in model and executor class.
- what with strategies that wants to play on  many instruments? every instrument will be required to flag as main   
    and the trade function must be overriten for this case and getting one more argument which is instrument.
- add clean cache command
- Define that credentials are necessery. For example you dont need to pass binance credentials if you not using it.
- add warning that first avaliable data will be this earliest feeding data. 
- make sure charts are printed well when timeframes are not the same in all backtest.
- pomysl o dodaniu wywalania wartości ceny w tickach ktore są takie same. czesto sie powtarzaja, moznaby odchudzic dane o 80%.
- tick tada in day csv-s
- minute data in month csv-s
- think about requirements that strategies has. all strategy has to has requirements file? what with tensorflow that 
    sometimes needs more commands?
    - add custom charts that you areusing in summarison of backtest.
- add option to stop code durin your backtest and click to make next.
- uwzglednianie spreadu i prowizji dla  brokera. 
- zrobić grid sarchea odpalania backtesów z różnymi parametrami.
- konfiguracja czy chcesz logarytmiczna skalę czy nie. 
- wywalic konieczność sudo. przy odpalaniu z dockera, sprawdz czy mozesz to zapisywac w folderze danego uzytkownika. 
- mozliwosc przełączania strategii w tryb przełączania palcem (tryb debug).
    - kliknij d zeby zatrzymać i wyswietlic charty (wejść do trybu debug).
    - kliknij n aby przejść do następnego stopu
    - kliknij l/ql aby odpalić tryb edycji pliku live
    - kliknij t/qt aby przeskoki były tylko w momencie tradeow.
    - kliknij q aby wyjść z trybu debug
"""
