import os
from backtesterRB30.libs.utils.list_of_services import SERVICES_ARRAY
serve_file_commands_array = [
    'from sys import argv\n',
    'from dotenv import load_dotenv\n',
    'load_dotenv(".env")\n',
    'load_dotenv(".additional_configs")\n',
    'microservice_name = argv[1]\n',
    'if microservice_name == "python_backtester":\n',
    '    from backtesterRB30.historical_data_feeds import run\n',
    'elif microservice_name == "python_engine":\n',
    '    from backtesterRB30.python_backtester import run\n',
    'elif microservice_name == "python_executor":\n',
    '    from backtesterRB30.python_engine import run\n',
    'elif microservice_name == "historical_data_feeds":\n',
    '    from backtesterRB30.python_executor import run\n'
    'elif microservice_name == "live_data_feeds":\n',
    '    from backtesterRB30.live_data_feeds import run\n'
]

run_file_commands_array = [
    'sudo -v\n'
    'trap ctrl_c INT\n'
    'function ctrl_c() {\n'
    '        echo "** Trapped CTRL-C"\n'
    '        sudo killall python3 \n'
    '        exit 2\n'
    '}\n'
    'sudo python3 serve.py python_backtester &\n'
    'sudo python3 serve.py python_engine &\n'
    'sudo python3 serve.py python_executor &\n'
    'sudo python3 serve.py historical_data_feeds &\n'
    'sudo python3 serve.py live_data_feeds &\n'
    'while true\n'
    'do\n'
    '    sleep 10\n'
    'done\n'
]

def run_all_microservices(
            strategy_path, 
            backtest_state,
            strategy_file,
            model_class_name,
            executor_class_name,
            data_class_name):
    serve_prepared = False
    run_prepared = False
    for fname in os.listdir('.'):
        if fname == 'serve.py':
            serve_prepared = True
        if fname == 'run.sh':
            run_prepared = True
    if serve_prepared == False:
        with open('serve.py', 'w') as f:
            for line in serve_file_commands_array:
                f.write(line)
    if run_prepared == False:
        with open('run.sh', 'w') as f:
            for line in run_file_commands_array:
                f.write(line)

    print('strategy_file', strategy_file)
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
            
    
    print('preparing microservice ports configuration')
    create_port_configurations()
    bck_state = 'true' if backtest_state else 'false'
    with open('.additional_configs', 'a') as f:
        f.write('backtest_state='+bck_state+'\n')
        f.write('STRATEGY_FILE='+strategy_file+'\n')
        f.write('STRATEGY_PATH='+strategy_path+'\n')
        f.write('MODEL_CLASS_NAME='+model_class_name+'\n')
        f.write('EXECUTOR_CLASS_NAME='+executor_class_name+'\n')
        f.write('DATA_CLASS_NAME='+data_class_name+'\n')

    if backtest_state:
        os.system('bash run.sh') 
    else:
        print('live strategies not implemented')
        
    # print('starting all containers')
    # system('docker-compose up --build --remove-orphans')
