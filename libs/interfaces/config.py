from pydantic import BaseModel
from typing import List

class NetInfo(BaseModel):
    topic: str
    port: int


class Config(BaseModel):
    name: str
    ip: str
    sub: List[NetInfo]
    pub: NetInfo
    backtest: bool
    strategy_name: str
