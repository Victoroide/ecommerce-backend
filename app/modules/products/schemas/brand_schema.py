from pydantic import BaseModel
from typing import Optional

class BrandCreate(BaseModel):
    name: str
    warranty_policy: Optional[str]

class BrandResponse(BaseModel):
    id: int
    name: str
    warranty_policy: Optional[str]
    active: bool

    class Config:
        orm_mode = True