from sys import argv
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".additional_configs")
microservice_name = argv[1]
if microservice_name == 'python_backtester':
    from backtesterRB30.historical_data_feeds import run
elif microservice_name == 'python_engine':
    from backtesterRB30.python_backtester import run
elif microservice_name == 'python_executor':
    from backtesterRB30.python_engine import run
elif microservice_name == 'historical_data_feeds':
    from backtesterRB30.python_executor import run
