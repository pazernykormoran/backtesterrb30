from pydantic import BaseModel
from typing import List

class DataStart(BaseModel):
    file_names: List[str]
    start_time: int
