from os import getenv
strategy_name = getenv('STRATEGY_NAME')
microservice_name = getenv('NAME')
sub_port = int(getenv(microservice_name).split(',')[0])
pub_port = int(getenv(microservice_name).split(',')[1])
from libs.necessery_imports.necessery_imports import *
import importlib
module = importlib.import_module('strategies.'+strategy_name+'.strategy')
config = {
    "name": microservice_name,
    "ip": "localhost",
    "sub": {
        "topic": microservice_name,
        "port": sub_port
    },
    "pub": [
        {
            "topic": "python_executor",
            "port": pub_port
        }
    ]
}
print('calling run')
engine = module.Model(config).run()