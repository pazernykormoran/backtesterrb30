from os import getenv
strategy_name = getenv('strategy')
microservice_name = getenv('name')
sub_port = int(getenv(microservice_name).split(',')[0])
pob_port = int(getenv(microservice_name).split(',')[1])

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
            "port": pob_port
        }
    ]
}

executor = module.TradeExecutor(config).run()