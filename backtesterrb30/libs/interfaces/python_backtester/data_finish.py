from typing import List, Optional

from pydantic import BaseModel

from backtesterrb30.libs.interfaces.python_backtester.custom_chart import CustomChart


class DataFinish(BaseModel):
    # main_instrument_price: float
    custom_charts: Optional[List[CustomChart]] = None
