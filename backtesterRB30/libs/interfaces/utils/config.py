from pydantic import BaseModel
from typing import List
from backtesterRB30.libs.interfaces.utils.net_info import NetInfo

class Config(BaseModel):
    name: str
    ip: str
    sub: List[NetInfo]
    pub: NetInfo
    backtest: bool
    strategy_path: str
