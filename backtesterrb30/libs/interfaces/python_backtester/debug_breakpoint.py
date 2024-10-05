from typing import List, Optional

from pydantic import BaseModel

from backtesterrb30.libs.interfaces.python_backtester.custom_chart import CustomChart


class DebugBreakpoint(BaseModel):
    custom_charts: Optional[List[CustomChart]] = None
    display_charts: Optional[bool] = True
