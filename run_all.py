from typing import Dict, Tuple, Type
import os
from dotenv import load_dotenv
load_dotenv()
strategy_name = os.getenv('strategy')
import importlib
strategy = importlib.import_module('strategies.'+strategy_name+'strategy')
from libs.zmq.zmq import ZMQ


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
    start_port = 1000
    assigned = False
    while not assigned:
        for port in range(start_port,start_port+50):
            if is_port_in_use(port):
                start_port += 50
                break
            for service in services:
                service.set_ports(start_port)
        
def validate_strategy(strategy):
    pass

print('starting all containers')
os.system('sudo docker-compose up -d')
