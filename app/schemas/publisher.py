from pydantic import BaseModel, Field
from typing import Optional

class PublisherBase(BaseModel):
    publisher_name: str = Field(..., description="Publisher Name", example="People's Literature Publishing House")

class PublisherCreate(BaseModel):
    publisher_name: str

class PublisherUpdate(PublisherBase):
    pass

class PublisherResponse(BaseModel):
    """Model used when returning publisher information"""
    publisher_id: int
    publisher_name: str

    class Config:
        orm_mode = True
        json_schema_extra = {
            "example": {
                "publisher_id": 1,
                "publisher_name": "People's Literature Publishing House"
            }
        }
        from_attributes = True