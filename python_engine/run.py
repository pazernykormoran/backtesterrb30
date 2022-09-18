from os import getenv
import importlib
strategy_name = getenv('STRATEGY_NAME')
from libs.utils.run_service import run_service
microservice_name = 'python_engine'
module = importlib.import_module('strategies.'+strategy_name+'.model')
run_service(microservice_name, module.Model)