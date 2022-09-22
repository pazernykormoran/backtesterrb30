from pydantic import BaseModel
from typing import Optional, List
from backtesterRB30.libs.interfaces.python_engine.custom_chart_element import CustomChartElement


class CustomChart(BaseModel):
    name: str
    display_on_price_chart: Optional[bool] = False
    log_scale: Optional[bool] = False
    color: Optional[str] = 'orange'
    chart: List[CustomChartElement]