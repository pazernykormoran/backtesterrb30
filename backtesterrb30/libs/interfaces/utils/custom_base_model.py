from pydantic import BaseModel

class CustomBaseModel(BaseModel):
    additional_properties: dict = {}
