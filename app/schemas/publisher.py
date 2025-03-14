from pydantic import BaseModel, Field
from typing import Optional

class PublisherBase(BaseModel):
    publisher_name: str = Field(..., description="Publisher Name", example="People's Literature Publishing House")

class PublisherCreate(PublisherBase):
    pass
class PublisherUpdate(PublisherBase):
    pass

class PublisherResponse(PublisherBase):
    """Model used when returning publisher information"""
    publisher_id: int

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "publisher_id": 1,
                "publisher_name": "People's Literature Publishing House"
            }
        }