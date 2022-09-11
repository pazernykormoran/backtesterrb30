from pydantic import BaseModel, validator
from typing import Optional, List

class CustomChart(BaseModel):
    name: str
    display_on_price_chart: Optional[bool] = False
    log_scale: Optional[bool] = False
    color: Optional[str] = 'orange'
    chart: List[list]

class DataFinish(BaseModel):
    file_names: List[str]
    start_time: int
    main_instrument_price: float
    custom_charts: Optional[List[CustomChart]] = None