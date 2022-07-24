from abc import ABC, abstractmethod
from typing import Callable
from datetime import datetime

class Service(ABC):
    name: str
    __logger: Callable

    def __init__(self, config, logger: Callable = print):
        self.name = config.name
        self.__logger = logger

    def run(self):
        self._log('Running service')
        self._loop()

    @abstractmethod
    def _loop(self):
        pass

    @abstractmethod
    def _send(self, msg: dict, pub: dict):
        pass

    def _log(self, *msg):
        time = str(datetime.now())
        msg = ' '.join(str(el) for el in msg)
        self.__logger(f'{time} [{self.name:>25}] {msg}')
        # self.__logger(f'{time}|  {msg}')
