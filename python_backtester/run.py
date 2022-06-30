from os import getenv
strategy_name = getenv('STRATEGY_NAME')
microservice_name = getenv('NAME')
sub_ports = [int(p) for p in getenv(microservice_name+'_subs').split(',')]
pub_ports = [int(p) for p in getenv(microservice_name+'_pubs').split(',')]

from python_backtester.python_backtester import Backtester
config = {
    "name": microservice_name,
    "ip": "localhost",
    "sub": [
        {
        "topic": "",
        "port": p
        } for p in sub_ports
    ],
    "pub": [
        {
            "topic": 'pub_'+str(p),
            "port": p
        } for p in pub_ports
    ]
}
service = Backtester(config)
service.run()