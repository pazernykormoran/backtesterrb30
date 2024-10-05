from importlib.machinery import SourceFileLoader
from os.path import join
import importlib.util


def import_data_schema(path_to_strategy: str,strategy_file: str, data_class_name: str):
    module = SourceFileLoader('data', path_to_strategy+'/'+strategy_file).load_module()
    data_class = getattr(module, data_class_name)
    return data_class

def import_model_module(path_to_strategy: str,strategy_file: str, model_class_name: str):
    module = SourceFileLoader('model', path_to_strategy+'/'+strategy_file).load_module()
    model_class = getattr(module, model_class_name)
    return model_class

def import_executor_module(path_to_strategy: str, strategy_file: str, executor_class_name: str):
    module = SourceFileLoader('executor', path_to_strategy+'/'+strategy_file).load_module()
    executor_class = getattr(module, executor_class_name)
    return executor_class

def import_spec_module(path_to_module):
    spec=importlib.util.spec_from_file_location(path_to_module, path_to_module)
    module = importlib.util.module_from_spec(spec)
    return spec, module

def reload_spec_module(spec, module):
    spec.loader.exec_module(module)