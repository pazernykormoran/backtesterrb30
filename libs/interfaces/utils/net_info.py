from pydantic import BaseModel

class NetInfo(BaseModel):
    topic: str
    port: int
