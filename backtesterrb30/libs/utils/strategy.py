import asyncio
import os
import sys

from dotenv import load_dotenv

from backtesterrb30 import validate_config
from backtesterrb30.historical_data_feeds.historical_data_feeds import (
    HistoricalDataFeeds,
)
from backtesterrb30.libs.communication_broker.asyncio_broker import AsyncioBroker
from backtesterrb30.libs.interfaces.utils.config import Config
from backtesterrb30.libs.utils.list_of_services import SERVICES
from backtesterrb30.libs.utils.service import Service
from backtesterrb30.libs.utils.user_cache import configure_cache_dir
from backtesterrb30.live_data_feeds.live_data_feeds import LiveDataFeeds
from backtesterrb30.python_backtester.python_backtester import Backtester
from backtesterrb30.python_engine.engine import Engine
from backtesterrb30.python_executor.trade_executor import Executor
import platform

load_dotenv(".env")


class Strategy:
    def __init__(
        self,
        model: Engine,
        executor: Executor,
        data: dict,
        backtest=True,
        debug=False,
        skip_cache=False,
    ):
        if debug and platform.system() != "Windows":
            if os.geteuid() != 0:
                print("You must be root to use debug mode because of keyboard package!")
                os._exit(1)
        if not backtest:
            print("Live is not yet supported")
            os._exit(1)
        self.__debug = debug
        self.__model = model
        self.__executor = executor
        self.__data = data
        self.__skip_cache = skip_cache
        self.__backtest_state = backtest
        self.__model_class_name = str(self.__model.__name__)
        self.__executor_class_name = str(self.__executor.__name__)
        self.__data_class_name = str(self.__data.__name__)
        splitted = os.path.normpath(sys.argv[0])
        splitted = splitted.split(os.sep)
        self.__strategy_path = os.path.join(str(os.getcwd()), *splitted[:-1])
        self.__strategy_file = splitted[-1]

        self.__loop = asyncio.get_event_loop()
        self.__services = {}
        self.__data_schema = validate_config(data.data)

    def create_service(
        self,
        microservice_name: str,
        service_class: Service,
        backtest_state,
        loop,
        data_schema,
    ) -> Service:
        config = {
            "name": microservice_name,
            "backtest": backtest_state,
            "strategy_path": self.__strategy_path,
            "debug": self.__debug,
            "cache_dir": configure_cache_dir(self.__skip_cache),
        }
        service: Service = service_class(Config(**config), data_schema, loop)
        logger = service.get_logger()
        broker: AsyncioBroker = AsyncioBroker(service.config, logger)
        service.register_communication_broker(broker)
        return service, broker

    def run(self):
        static_params = self.__backtest_state, self.__loop, self.__data_schema
        self.__services["python_engine"] = self.create_service(
            "python_engine", self.__model, *static_params
        )
        self.__services["python_executor"] = self.create_service(
            "python_exacutor", self.__executor, *static_params
        )
        self.__services["historical_data_feeds"] = self.create_service(
            "historical_data_feeds", HistoricalDataFeeds, *static_params
        )
        self.__services["python_backtester"] = self.create_service(
            "python_backtester", Backtester, *static_params
        )
        self.__services["live_data_feeds"] = self.create_service(
            "live_data_feeds", LiveDataFeeds, *static_params
        )

        if self.__strategy_file != "serve.py":
            for name, (service, broker) in self.__services.items():
                service: Service = service
                broker: AsyncioBroker = broker
                for n, (s, b) in self.__services.items():
                    if n != name:
                        broker.register_broker(SERVICES[n], b)

            for name, (service, broker) in self.__services.items():
                service.run()
            self.__loop.run_forever()
            self.__loop.close()

    def run_in_microservices(self):
        if self.__strategy_file != "serve.py":
            from backtesterrb30 import run_all_microservices

            run_all_microservices(
                self.__strategy_path,
                self.__backtest_state,
                self.__strategy_file,
                self.__model_class_name,
                self.__executor_class_name,
                self.__data_class_name,
            )

    def run_in_docker_microservices():
        pass
