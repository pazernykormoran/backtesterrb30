from pydantic import BaseModel
from typing import List

class DataFinish(BaseModel):
    file_names: List[str]
    start_time: int
