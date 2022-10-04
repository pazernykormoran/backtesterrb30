from importlib.machinery import SourceFileLoader
from os.path import join
import importlib.util

def import_data_schema(path_to_strategy: str):
    module = SourceFileLoader('data', join(path_to_strategy, 'data_schema.py')).load_module()
    return module.DATA

def import_model_module(path_to_strategy: str):
    module = SourceFileLoader('model', join(path_to_strategy, 'model.py')).load_module()
    return module

def import_executor_module(path_to_strategy: str):
    module = SourceFileLoader('executor', join(path_to_strategy, 'executor.py')).load_module()
    return module

def import_spec_module(path_to_module):
    spec=importlib.util.spec_from_file_location(path_to_module, path_to_module)
    module = importlib.util.module_from_spec(spec)
    return spec, module

def reload_spec_module(spec, module):
    spec.loader.exec_module(module)