from pydantic import BaseModel

class ProductCategoryCreate(BaseModel):
    name: str

class ProductCategoryResponse(BaseModel):
    id: int
    name: str
    active: bool

    class Config:
        from_attributes = True