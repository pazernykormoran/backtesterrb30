from backtesterrb30.libs.utils.run_service import run_service
from backtesterrb30.python_backtester.python_backtester import Backtester

microservice_name = "python_backtester"

run_service(microservice_name, Backtester)
