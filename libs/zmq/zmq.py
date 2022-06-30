from abc import abstractmethod, ABC
from typing import Callable, Dict, List
from asyncio import AbstractEventLoop
import zmq
import zmq.asyncio
import asyncio
from libs.list_of_services.list_of_services import SERVICES
from libs.zmq.service import Service
from os import getenv

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

        self._pubs = {}
        self._subs = []
        

        self._commands = {'start': self._start,
                          'pause': self._pause,
                          'stop': self._stop}

    # override
    def run(self):
        self._init_sockets(self.config)
        self._is_running = True
        self._is_active = True
        super().run()

    def __find_topic(self, service):
        port = ''
        service_sub_ports = [int(p) for p in getenv(service+'_subs').split(',')]
        for port in service_sub_ports:
            for pub in self.config['pub']:
                if pub['port'] == port:
                    return 'pub_'+str(port)

    # override
    def _send(self, service: SERVICES, msg: str, *args):
        topic = self.__find_topic(service.value)
        if not topic:
            self._log('Cannot send message to this micro service. Check port configuration')
            return
        if self._is_active:
            data = [topic.encode('utf-8'), msg.encode('utf-8')]
            for arg in args:
                data.append(arg.encode('utf-8'))
            self._pubs[topic].send_multipart(data)

    @abstractmethod
    def _handle_zmq_message(self, msg: str):
        pass

    def _init_sockets(self, config):
        sub_context = zmq.asyncio.Context()
        pub_context = zmq.Context()
        # self._sub = sub_socket(sub_context, 'tcp://' + config['ip'] + ':' + str(config['sub']['port']), config['sub']['topic'])
        for sub in config['sub']:
            print('sub', sub)
            s = sub_socket(sub_context, 'tcp://' + config['ip'] + ':' + str(sub['port']), sub['topic'])
            self._subs.append(s)

        print('subs', self._subs)

        for pub in config['pub']:
             self._pubs['pub_'+str(pub['port'])] = pub_socket(pub_context, 'tcp://*:' + str(pub['port']))
        
        print('pubs', self._pubs)

    def _create_listeners(self, loop:AbstractEventLoop):
        self._log('Start main loop')
        for sub in self._subs:
            loop.create_task(self._listen_zmq(sub))


    async def _listen_zmq(self, sub):
        while self._is_running:

            if self._is_active:
                data = await sub.recv_multipart()
                if data:
                    self._handle(data)
            else:
                await asyncio.sleep(0.01)



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
        for pub in self._pubs.values():
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

