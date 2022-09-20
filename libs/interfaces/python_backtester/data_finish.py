from pydantic import BaseModel
from typing import Optional, List
from libs.interfaces.python_backtester.custom_chart import CustomChart


class DataFinish(BaseModel):
    main_instrument_price: float
    custom_charts: Optional[List[CustomChart]] = None