from os import getenv
from libs.utils.service import Service

def run_service(microservice_name: str, service_class: Service):
    strategy_name = getenv('STRATEGY_NAME')
    sub_ports = [int(p) for p in getenv(microservice_name+'_subs').split(',')]
    pub_port = int(getenv(microservice_name+'_pubs'))
    backtest_state = getenv('backtest_state')
    from libs.interfaces.utils.config import Config

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
        "strategy_name": strategy_name
    }

    service = service_class(Config(**config))
    service.run()