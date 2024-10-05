from pydantic import BaseModel


class PriceEvent(BaseModel):
    price: float
    symbol_itentifier: str
    quantity: float
