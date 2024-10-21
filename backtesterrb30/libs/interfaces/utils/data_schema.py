from typing import List, Optional

from pydantic import BaseModel

from backtesterrb30.libs.interfaces.utils.data_symbol import DataSymbol


class DataSchema(BaseModel):
    log_scale_valuation_chart: Optional[bool] = True
    custom_data: Optional[dict]
    data: List[DataSymbol]
