from os import getenv, system
from dotenv import load_dotenv
from backtesterRB30.libs.utils.module_loaders import import_data_schema, import_model_module, import_executor_module
from sys import argv
from backtesterRB30.libs.utils.list_of_services import SERVICES_ARRAY
from backtesterRB30.libs.interfaces.utils.data_schema import DataSchema

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
strategy_path = getenv('STRATEGY_PATH')
if not strategy_path or strategy_path == '':
    print('Error: provide strategy name in .env file like: \nstrategy=name_of_strategy')
    exit()
print('running strategy name: ', strategy_path)


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
        
        
def validate_strategy(strategy_path):
    data_schema: DataSchema = import_data_schema(strategy_path)
    model_module = import_model_module(strategy_path)
    executor_module = import_executor_module(strategy_path)
    class Asd:
        name = "test",
        strategy_path = strategy_path
    config = Asd()
    model = model_module.Model(config)
    executor = executor_module.TradeExecutor(config)

print('validating strategy')
validate_strategy(strategy_path)
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



