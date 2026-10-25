from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    category_name: str = Field(..., max_length=120)
    type: str = Field("public", description="public | private")


class CategoryUpdate(BaseModel):
    category_name: str | None = Field(None, max_length=120)
    type: str | None = Field(None, description="public | private")


class CategoryOut(BaseModel):
    category_id: int
    category_name: str
    type: str
