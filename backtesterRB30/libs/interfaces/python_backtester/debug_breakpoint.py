from pydantic import BaseModel
from typing import Optional, List
from backtesterRB30.libs.interfaces.python_backtester.custom_chart import CustomChart


class DebugBreakpoint(BaseModel):
    custom_charts: Optional[List[CustomChart]] = None
    display_charts: Optional[bool] = True