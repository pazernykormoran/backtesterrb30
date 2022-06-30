from pydantic import BaseModel

class NetInfo(BaseModel):
    name: str
    port: int


class ConfigSchema(BaseModel):
    name: str
    ip: str
    sub: NetInfo
    pub: NetInfo
    
