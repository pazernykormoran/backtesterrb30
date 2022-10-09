from pydantic import BaseModel
from typing import List

class PriceEvent(BaseModel):
    price: float
    symbol_itentifier: str
    quantity: float

    

