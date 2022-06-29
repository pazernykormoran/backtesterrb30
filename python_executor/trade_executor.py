
from concurrent.futures import Executor

import asyncio
import json
from typing import Callable, List
from libs.zmq.zmq import ZMQ

class Executor(ZMQ):
    def __init__(self):
        pass