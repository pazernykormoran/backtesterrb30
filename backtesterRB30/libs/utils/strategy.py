
from backtesterRB30.libs.interfaces.utils.data_schema import DataSchema
from backtesterRB30.libs.utils.service import Service
from backtesterRB30.python_engine.engine import Engine
from backtesterRB30.python_executor.trade_executor import Executor
from backtesterRB30.historical_data_feeds.historical_data_feeds import HistoricalDataFeeds
from backtesterRB30.live_data_feeds.live_data_feeds import LiveDataFeeds
from backtesterRB30.python_backtester.python_backtester import Backtester
from backtesterRB30.libs.interfaces.utils.config import Config
from backtesterRB30.libs.asyncio_broker.asyncio_broker import AsyncioBroker
from backtesterRB30.libs.utils.list_of_services import SERVICES

import os
import asyncio


class Strategy():
    def __init__(self, model: Engine, executor: Executor, data_schema: DataSchema, backtest= True):
        self.__loop = asyncio.get_event_loop()
        self.__services = {}
        self.__data_schema = data_schema
        self.__backtest_state = backtest
        static_params = self.__backtest_state, self.__loop, self.__data_schema
        self.__services['python_engine'] = self.create_service('python_engine', model, *static_params)
        self.__services['python_exacutor'] = self.create_service('python_exacutor', executor, *static_params)
        self.__services['historical_data_feeds'] = self.create_service('historical_data_feeds', HistoricalDataFeeds, *static_params)
        self.__services['python_backtester'] = self.create_service('python_backtester', Backtester, *static_params)
        self.__services['live_data_feeds'] = self.create_service('live_data_feeds', LiveDataFeeds, *static_params)

    @staticmethod
    def create_service(microservice_name: str, service_class: Service, backtest_state, loop, data_schema) -> AsyncioBroker:
        here = os.getcwd()
        strategy_path = here
        config = {
            "name": microservice_name,
            "backtest": backtest_state,
            "strategy_path": strategy_path
        }
        service: AsyncioBroker = service_class(Config(**config), data_schema)
        service.register_event_loop(loop)
        return service

    def run(self):
        for name, service in self.__services.items():
            service: AsyncioBroker = service
            if name != service.name:
                service.register_service(SERVICES[name], service)

        for name, service in self.__services.items():
            service.run()
