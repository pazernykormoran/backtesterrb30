from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

from backtesterrb30.libs.interfaces.utils.net_info import NetInfo


class BROKERS(Enum):
    zmq = ("zmq",)
    asyncio = "asyncio"


class Config(BaseModel):
    name: str
    ip: Optional[str]
    sub: Optional[List[NetInfo]]
    pub: Optional[NetInfo]
    backtest: bool
    debug: bool = False
    cache_dir: str
    strategy_path: str
