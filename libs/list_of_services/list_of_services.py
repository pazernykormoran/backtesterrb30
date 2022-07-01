from enum import Enum
class SERVICES(Enum):
    historical_data_feeds='historical_data_feeds'
    live_data_feeds='live_data_feeds'
    python_backtester='python_backtester'
    python_engine='python_engine'
    python_executor='python_executor'

SERVICES_ARRAY = [i for i in dir(SERVICES) if not i.startswith('__')]