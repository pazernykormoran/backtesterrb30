from abc import abstractmethod, ABC
from typing import Callable, Dict, List

import zmq
import zmq.asyncio
import asyncio

from lib.service import Service

class ZMQ(Service, ABC):

    _is_running: bool
    _is_active: bool

    _sub: zmq.Socket
    _pub: dict

    _commands: Dict[str, Callable]

    # override
    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)

        self._is_running = False
        self._is_active = False

        self._pub = {}
        self._init_sockets(config)

        self._commands = {'start': self._start,
                          'pause': self._pause,
                          'stop': self._stop}

    # override
    def run(self):
        self._is_running = True
        self._is_active = True
        super().run()

    # override
    def _send(self, topic: str, msg: str, *args):
        if self._is_active:
            data = [topic.encode('utf-8'), msg.encode('utf-8')]
            for arg in args:
                data.append(arg.encode('utf-8'))
            self._pub[topic].send_multipart(data)

    @abstractmethod
    def _handle_zmq_message(self, msg: str):
        pass

    def _init_sockets(self, config):
        sub_context = zmq.asyncio.Context()
        pub_context = zmq.Context()
        self._sub = sub_socket(sub_context, 'tcp://' + config['ip'] + ':' + str(config['sub']['port']), config['sub']['topic'])

        for pub in config['pub']:
             self._pub[pub['topic']] = pub_socket(pub_context, 'tcp://*:' + str(pub['port']))

    async def _listen_zmq(self):
        self._log('Start main loop')
        while self._is_running:
            try:
                if self._is_active:
                    data = await self._sub.recv_multipart()
                    if data:
                        self._handle(data)
                else:
                    await asyncio.sleep(0.01)

            except Exception as e:
                self._log('Handled exception in zmq service: ', e)

        self._deinit()

    def _handle(self, data):
        data = [x.decode('utf-8') for x in data]
        if len(data) >= 2:
            topic, cmd, *args = data
            func = self._commands.get(cmd)
            if func:
                self._log(f'Receive {cmd} command')
                if args:
                    func(*args)
                else:
                    func()
            else:
                self._log(f"Command '{cmd}' not registered")

        self._handle_zmq_message(data)

    def _deinit(self):
        self._sub.close()
        for pub in self._pub.values():
            pub.close()

    def _stop(self):
        self._log("Service stoped")
        self._is_running = False

    def _start(self):
        self._log("Service started")
        self._is_active = True

    def _pause(self):
        self._log("Service paused")
        self._is_active = False

    def register(self, command: str, func: Callable):
        self._commands[command] = func

def sub_socket(context: zmq.asyncio.Context(), url: str, topic: str):
    sub = context.socket(zmq.SUB)
    sub.connect(url)
    sub.subscribe(topic)
    return sub

def pub_socket(context: zmq.Context(), url: str):
    pub = context.socket(zmq.PUB)
    ret = pub.bind(url)
    return pub

