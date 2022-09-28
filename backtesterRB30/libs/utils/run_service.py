import os
from backtesterRB30.libs.utils.service import Service

def run_service(microservice_name: str, service_class: Service):
    here = os.getcwd()
    strategy_path = os.path.join(here, os.getenv('STRATEGY_PATH'))
    sub_ports = [int(p) for p in os.getenv(microservice_name+'_subs').split(',')]
    pub_port = int(os.getenv(microservice_name+'_pubs'))
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
        "strategy_path": strategy_path
    }

    service = service_class(Config(**config))
    service.run()