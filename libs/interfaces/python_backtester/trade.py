from pydantic import BaseModel

class Trade(BaseModel):
    timestamp: int
    quantity: float
    price: float