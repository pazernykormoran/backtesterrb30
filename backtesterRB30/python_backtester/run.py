from backtesterRB30.libs.utils.run_service import run_service
microservice_name = 'python_backtester'
from backtesterRB30.python_backtester.python_backtester import Backtester
run_service(microservice_name, Backtester)