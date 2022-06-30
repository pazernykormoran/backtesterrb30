from os import getenv
strategy_name = getenv('STRATEGY_NAME')
microservice_name = getenv('NAME')
sub_ports = [int(p) for p in getenv(microservice_name+'_subs').split(',')]
pub_ports = [int(p) for p in getenv(microservice_name+'_pubs').split(',')]

from historical_data_feeds.historical_data_feeds import HistoricalDataFeeds
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
service = HistoricalDataFeeds(config)
service.run()