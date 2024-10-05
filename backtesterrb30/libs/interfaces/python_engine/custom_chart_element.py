from pydantic import BaseModel


class CustomChartElement(BaseModel):
    timestamp: int
    value: float
