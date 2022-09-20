from pydantic import BaseModel
from typing import Optional, List
from libs.interfaces.utils.data_symbol import DataSymbol

class DataSchema(BaseModel):
    log_scale_valuation_chart: Optional[bool] = True
    data: List[DataSymbol]
