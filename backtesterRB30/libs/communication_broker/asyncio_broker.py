from abc import abstractmethod, ABC
from typing import Callable, Dict
from asyncio import AbstractEventLoop
import zmq
import zmq.asyncio
import asyncio
from backtesterRB30.libs.utils.list_of_services import SERVICES
from backtesterRB30.libs.utils.service import Service
from backtesterRB30.libs.interfaces.utils.config import Config
from os import _exit
from pydantic import BaseModel
from json import dumps, loads
from backtesterRB30.libs.communication_broker.broker_base import BrokerBase


class AsyncioBroker(BrokerBase):
    __is_running: bool
    __is_active: bool

    __commands: Dict[str, Callable]
    # override
    def __init__(self, config: Config, logger=print):
        self.config=config
        self.__log = logger
        self.__is_running = False
        self.__is_active = False
        self.__brokers = {}

        self.__commands = {'start': self.start,
                          'pause': self.pause,
                          'stop': self.stop}

    # override
    def run(self):
        # self.__init_sockets(self.config)
        self.__is_running = True
        self.__is_active = True

    # override
    async def send(self, service: SERVICES, msg: str, *args):
        if self.__is_active:
            new_args = []
            # data = [service.value.encode('utf-8'), msg.encode('utf-8')]
            for arg in args:
                if isinstance(arg,BaseModel):
                    arg = arg.dict()
                    new_args.append(arg)
        #         arg = dumps(arg, default=str)
        #         data.append(arg.encode('utf-8'))
        #     self.__pub.send_multipart(data)

        service: AsyncioBroker = self.__find_service(service)
        # print('new args ', new_args)
        if len(new_args) > 0:
            await service.handle(msg, *new_args)
        else:
            await service.handle(msg, *args)
        await asyncio.sleep(0.00001)
    # @abstractmethod
    # def _handle_zmq_message(self, msg: str):
    #     pass

    # @abstractmethod
    # def _asyncio_loop(self, loop:asyncio.AbstractEventLoop):
    #     pass
    
    # def _loop(self):
    #     self._asyncio_loop(self.__loop)

    def __find_service(self, service: SERVICES):
        return self.__brokers[service.value]

    def register(self, command: str, func: Callable):
        self.__commands[command] = func

    def register_broker(self, service: SERVICES, service_object):
        self.__brokers[service.value] = service_object

    def create_listeners(self, loop:AbstractEventLoop):
        self.__log('Start main loop')
        # for sub in self.__subs:
        #     loop.create_task(self.__listen_zmq(sub))
        pass

    # async def __listen_zmq(self, sub):
    #     while self.__is_running:

    #         if self.__is_active:
    #             data = await sub.recv_multipart()
    #             if data:
    #                 await self.__handle(data)
    #             await asyncio.sleep(0.00001)
    #         else:
    #             await asyncio.sleep(0.01)
    #     self.__deinit()


    # def __init_sockets(self, config: Config):
    #     sub_context = zmq.asyncio.Context()
    #     pub_context = zmq.Context()
    #     for sub in config.sub:
    #         s = sub_socket(sub_context, 'tcp://' + config.ip + ':' + str(sub.port), sub.topic)
    #         self.__subs.append(s)
    #     self.__pub = pub_socket(pub_context, 'tcp://*:' + str(config.pub.port))


    async def handle(self, cmd, *args):
        func = self.__commands.get(cmd)
        if func:
            # self.__log(f'Receive "{cmd}" command')
            if args:
                await func(*args)
            else:
                await func()
        else:
            self.__log(f"Command '{cmd}' not registered")


    def stop(self):
        self.__log("Service stoped")
        self.__is_running = False
        _exit(1)


    def start(self):
        self.__log("Service started")
        self.__is_active = True


    def pause(self):
        self.__log("Service paused")
        self.__is_active = False


# def sub_socket(context: zmq.asyncio.Context(), url: str, topic: str):
#     sub = context.socket(zmq.SUB)
#     sub.connect(url)
#     sub.subscribe(topic)
#     return sub

# def pub_socket(context: zmq.Context(), url: str):
#     pub = context.socket(zmq.PUB)
#     ret = pub.bind(url)
#     return pub

