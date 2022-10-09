from pydantic import BaseModel
from typing import List
from backtesterRB30.libs.interfaces.utils.net_info import NetInfo
from typing import Optional
from enum import Enum

class BROKERS(Enum):
    zmq = 'zmq', 
    asyncio = 'asyncio'

class Config(BaseModel):
    name: str
    ip: Optional[str]
    sub: Optional[List[NetInfo]]
    pub: Optional[NetInfo]
    backtest: bool
    debug: bool = False
    strategy_path: str
