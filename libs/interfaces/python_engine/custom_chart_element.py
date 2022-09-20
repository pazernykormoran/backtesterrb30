from pydantic import BaseModel
from typing import List

class CustomChartElement(BaseModel):
    timestamp: int
    value: float

    

