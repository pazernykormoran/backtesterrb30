from abc import ABC, abstractmethod
from asyncio import AbstractEventLoop
from typing import Callable
from datetime import datetime

from backtesterRB30.libs.utils.list_of_services import SERVICES

class BrokerBase(ABC):

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def send(self, service: SERVICES, msg: str, *args):
        pass

    @abstractmethod
    def register(self, command: str, func: Callable):
        pass
    
    @abstractmethod
    def create_listeners(self, loop:AbstractEventLoop):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def pause(self):
        pass