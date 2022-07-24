from libs.list_of_services.list_of_services import SERVICES_ARRAY
from importlib import import_module
from sys import argv
from dotenv import load_dotenv
from os import environ
load_dotenv(".env")
load_dotenv(".additional_configs")
microservice_name = argv[1]
import_module(microservice_name + '.run')
