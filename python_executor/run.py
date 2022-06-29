from os import environ
strategy_name = environ('strategy')
import importlib
module = importlib.import_module('strategies.'+strategy_name+'.strategy')
engine = module.Model().run()