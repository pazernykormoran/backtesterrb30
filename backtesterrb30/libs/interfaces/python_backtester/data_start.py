from typing import List

from pydantic import BaseModel

from backtesterrb30.libs.interfaces.historical_data_feeds.instrument_file import (
    InstrumentFile,
)


class DataStartFiles(BaseModel):
    files: List[InstrumentFile]
    symbol: str
    source: str


class DataStart(BaseModel):
    file_names: List[DataStartFiles]
    start_time: float
