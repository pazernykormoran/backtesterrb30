from os import getenv
from libs.utils.module_loaders import import_model_module
strategy_name = getenv('STRATEGY_NAME')
from libs.utils.run_service import run_service
microservice_name = 'python_engine'
module = import_model_module(strategy_name)
run_service(microservice_name, module.Model)