from pydantic import BaseModel


class Trade(BaseModel):
    timestamp: int
    value: float
    price: float
    symbol: str
    source: str
    # data_symbol: DataSymbol
