from typing import Dict, Tuple, Type
import os
from dotenv import load_dotenv
import importlib
from libs.zmq.zmq import ZMQ
load_dotenv()
strategy_name = os.getenv('strategy')
print('trying run strategy name: ', strategy_name)
strategy_module = importlib.import_module('strategies.'+strategy_name+'.strategy')
config = {'name': 'test'}
model = strategy_module.Model(config)
executor = strategy_module.TradeExecutor(config)



services = [
    'historical_data_feeds',
    'live_data_feeds',
    'python_backtester',
    'python_engine',
    'python_executor'
]

def check_env():
    from os.path import exists
    file_exists = exists(".env")
    if not file_exists:
        print('Error: ".env" file does not exists. Create one and provide necessery information like: \nstrategy=name\nbacktest=true')
        exit()

def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def create_port_configurations(services):
    start_port = 1001
    assigned = False
    while not assigned:
        for port in range(start_port,start_port+50):
            if is_port_in_use(port):
                print('Port '+str(port)+ ' is already in use, changing port range.')
                start_port += 50
                break
        with open('.ports_config', 'w') as f:
            for service in services:
                f.write(service+'='+str(start_port)+','+str(start_port+1)+'\n')
                start_port += 2
        assigned = True
        
def validate_strategy(strategy):
    pass

print('checking env file')
check_env()
print('preparing microservice ports configuration')
create_port_configurations(services)
# print('starting all containers')
# os.system('sudo docker-compose up -d')
