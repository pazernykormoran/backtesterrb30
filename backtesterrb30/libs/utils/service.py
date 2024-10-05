from abc import ABC, abstractmethod
from typing import Callable
from datetime import datetime

class Service(ABC):
    name: str
    __logger: Callable
    _broker: object

    def __init__(self, config, logger: Callable = print):
        self.name = config.name
        self.__logger = logger

    def run(self):
        if not self._broker: 
            raise Exception('No communication broker registered')
        self._log('Running service')
        self._configure()
        self._broker.run()
        self._loop()

    def get_logger(self):
        return self._log

    @abstractmethod
    def _loop(self):
        pass

    # @abstractmethod
    # def _send(self, msg: dict, pub: dict):
    #     pass
        
    def _configure(self):
        pass

    def register_communication_broker(self, broker):
        self._broker = broker

    def _log(self, *msg):
        time = str(datetime.now())
        msg = ' '.join(str(el) for el in msg)
        self.__logger(f'{time} [{self.name:>25}] {msg}')
        # self.__logger(f'{time}|  {msg}')
