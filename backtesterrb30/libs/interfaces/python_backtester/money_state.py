from pydantic import BaseModel

class MoneyState(BaseModel):
    timestamp: int
    value: float