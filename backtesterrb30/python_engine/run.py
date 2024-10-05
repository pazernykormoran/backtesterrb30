import os

from backtesterrb30.libs.utils.module_loaders import import_model_module
from backtesterrb30.libs.utils.run_service import run_service

strategy_path = os.getenv("STRATEGY_PATH")
strategy_file = os.getenv("STRATEGY_FILE")
model_class_name = os.getenv("MODEL_CLASS_NAME")


microservice_name = "python_engine"
module = import_model_module(strategy_path, strategy_file, model_class_name)
run_service(microservice_name, module)
