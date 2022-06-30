from typing import Dict, Tuple, Type
from os import getenv, system
from dotenv import load_dotenv
import importlib
from libs.zmq.zmq import ZMQ
from enum import Enum
from sys import argv

#TODO hardcoded backtest mode: 
backtest_state='true'

args = argv
if len(args) > 1:
    if args[1] == '-backtest':
        backtest_state='true'


def check_env():
    from os.path import exists
    file_exists = exists(".env")
    if not file_exists:
        print('Error: ".env" file does not exists. Create one and provide necessery information like: \nstrategy=name_of_strategy')
        exit()
print('checking env file')
check_env()

load_dotenv()
strategy_name = getenv('STRATEGY_NAME')
if not strategy_name or strategy_name == '':
    print('Error: provide strategy name in .env file like: \nstrategy=name_of_strategy')
    exit()
print('running strategy name: ', strategy_name)
model_module = importlib.import_module('strategies.'+strategy_name+'.model')
executor_module = importlib.import_module('strategies.'+strategy_name+'.executor')
config = {'name': 'test'}
model = model_module.Model(config)
executor = executor_module.TradeExecutor(config)

from libs.list_of_services.list_of_services import SERVICES

def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def create_port_configurations():
    start_port = 1000
    assigned = False
    while not assigned:
        for port in range(start_port,start_port+50):
            if is_port_in_use(port):
                print('Port '+str(port)+ ' is already in use, changing port range.')
                start_port += 50
                break
        with open('.additional_configs', 'w') as f:
            f.write(SERVICES.historical_data_feeds.value+'_pubs='+str(start_port+1)+'\n')
            f.write(SERVICES.historical_data_feeds.value+'_subs='+str(start_port+4)+'\n')
            # f.write(SERVICES.live_data_feeds.value+'_pubs='+str(start_port+1)+','+str(start_port+1)+'\n')
            # f.write(SERVICES.live_data_feeds.value+'_subs='+str(start_port+1)+','+str(start_port+1)+'\n')
            f.write(SERVICES.python_engine.value+'_pubs='+str(start_port+3)+'\n')
            f.write(SERVICES.python_engine.value+'_subs='+str(start_port+1)+'\n')
            f.write(SERVICES.python_backtester.value+'_pubs='+str(start_port+6)+'\n')
            f.write(SERVICES.python_backtester.value+'_subs='+str(start_port+5)+'\n')
            f.write(SERVICES.python_executor.value+'_pubs='+str(start_port+5)+'\n')
            f.write(SERVICES.python_executor.value+'_subs='+str(start_port+3)+'\n')
        assigned = True
        
def validate_strategy(strategy):
    pass

print('preparing microservice ports configuration')
create_port_configurations()
with open('.additional_configs', 'a') as f:
    f.write('backtest_state='+backtest_state)
print('starting all containers')
system('sudo docker-compose up --build')
