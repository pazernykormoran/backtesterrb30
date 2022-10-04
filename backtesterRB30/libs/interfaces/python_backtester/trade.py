from pydantic import BaseModel

from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol

class Trade(BaseModel):
    timestamp: int
    value: float
    price: float
    symbol: str
    source: str
    # data_symbol: DataSymbol