from os import getenv
from backtesterRB30.libs.utils.module_loaders import import_model_module
strategy_path = getenv('STRATEGY_PATH')
from backtesterRB30.libs.utils.run_service import run_service
microservice_name = 'python_engine'
module = import_model_module(strategy_path)
run_service(microservice_name, module.Model)