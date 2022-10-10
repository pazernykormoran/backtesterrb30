import os
from backtesterRB30.libs.utils.config_validator import validate_config
from backtesterRB30.libs.utils.module_loaders import import_data_schema
from backtesterRB30.libs.utils.service import Service
from backtesterRB30.libs.communication_broker.zmq_broker import ZMQ

def run_service(microservice_name: str, service_class: Service):
    here = os.getcwd()
    strategy_path = os.getenv('STRATEGY_PATH')
    sub_ports = [int(p) for p in os.getenv(microservice_name+'_subs').split(',')]
    pub_port = int(os.getenv(microservice_name+'_pubs'))
    strategy_file = os.getenv('STRATEGY_FILE')
    data_class_name = os.getenv('DATA_CLASS_NAME')
    backtest_state = os.getenv('backtest_state')
    from backtesterRB30.libs.interfaces.utils.config import Config

    config = {
        "name": microservice_name,
        "ip": "localhost",
        "sub": [
            {
            "topic": microservice_name,
            "port": p
            } for p in sub_ports
        ],
        "pub": {
                "topic": 'pub_'+str(pub_port),
                "port": pub_port
            } ,
        "backtest": True if backtest_state == 'true' else False,
        "debug": True,
        "strategy_path": strategy_path
    }
    data_class = import_data_schema(strategy_path, strategy_file, data_class_name)
    data_schema = validate_config(data_class.data)
    config = Config(**config)
    service: Service = service_class(config, data_schema)
    logger = service.get_logger()
    service.register_communication_broker(ZMQ(config, logger))
    service.run()