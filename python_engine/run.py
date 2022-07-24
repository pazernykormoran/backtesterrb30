from os import getenv
strategy_name = getenv('STRATEGY_NAME')
# microservice_name = getenv('NAME')
microservice_name = 'python_engine'
sub_ports = [int(p) for p in getenv(microservice_name+'_subs').split(',')]
pub_port = int(getenv(microservice_name+'_pubs'))

backtest_state = getenv('backtest_state')

import importlib

module = importlib.import_module('strategies.'+strategy_name+'.model')
from libs.interfaces.config import Config
config = {
    "name": microservice_name,
    "ip": "localhost",
    "sub": [
        {
        "topic": microservice_name,
        "port": p
        } for p in sub_ports
    ],
    "pub": 
        {
            "topic": 'pub_'+str(pub_port),
            "port": pub_port
        } 
    ,
    "backtest": True if backtest_state == 'true' else False,
    "strategy_name": strategy_name
}
service = module.Model(Config(**config))
service.run()