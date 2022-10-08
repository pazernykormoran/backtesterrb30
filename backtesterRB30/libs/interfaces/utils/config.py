from pydantic import BaseModel
from typing import List
from backtesterRB30.libs.interfaces.utils.net_info import NetInfo
from typing import Optional

class Config(BaseModel):
    name: str
    ip: Optional[str]
    sub: Optional[List[NetInfo]]
    pub: Optional[NetInfo]
    backtest: bool
    strategy_path: str
