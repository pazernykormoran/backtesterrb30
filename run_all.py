from typing import Dict, Tuple, Type
from os import getenv, system
from dotenv import load_dotenv
import importlib
from libs.zmq.zmq import ZMQ
from enum import Enum
from sys import argv
from pydantic import BaseModel
import time
from libs.utils.list_of_services import SERVICES_ARRAY
from libs.interfaces.utils.data_schema import DataSchema
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
    data_schema: DataSchema = importlib.import_module('strategies.'+strategy_name+'.data_schema').DATA
    model_module = importlib.import_module('strategies.'+strategy_name+'.model')
    executor_module = importlib.import_module('strategies.'+strategy_name+'.executor')
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



