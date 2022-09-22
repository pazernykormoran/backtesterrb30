import os
from backtesterRB30.libs.utils.module_loaders import import_executor_module
here = os.getcwd()
strategy_path = os.path.join(here, os.getenv('STRATEGY_PATH'))
from backtesterRB30.libs.utils.run_service import run_service
microservice_name = 'python_executor'
module = import_executor_module(strategy_path)
run_service(microservice_name, module.TradeExecutor)