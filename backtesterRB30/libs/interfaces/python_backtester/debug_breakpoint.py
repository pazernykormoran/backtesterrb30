from pydantic import BaseModel
from typing import Optional, List
from backtesterRB30.libs.interfaces.python_backtester.custom_chart import CustomChart


class DebugBreakpoint(BaseModel):
    last_timestamp: int
    main_instrument_price: float
    custom_charts: Optional[List[CustomChart]] = None