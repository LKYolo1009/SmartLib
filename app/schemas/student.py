from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional
from datetime import datetime

class StudentBase(BaseModel):
    """Student's Basic Information"""
    matric_number: str = Field(..., description="Matric Number", example="S12345678Z")
    full_name: str = Field(..., description="Full Name", example="John Doe")
    email: EmailStr = Field(..., description="Email", example="john.doe@example.com")
    status: Optional[str] = Field("active", description="Status", example="active")
    
    @validator('matric_number')
    def validate_matric_number(cls, v):
        """Validate matric number format: 1 uppercase letter + 8 digits + 1 uppercase letter"""
        if not (len(v) == 10 and v[0].isupper() and v[1:8].isdigit() and v[8].isupper()):
            raise ValueError('Matric number format must be: 1 uppercase letter + 8 digits + 1 uppercase letter')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status for valid values"""
        valid_statuses = ["active", "inactive", "suspended"]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of the following: {", ".join(valid_statuses)}')
        return v

class StudentCreate(StudentBase):
    """Model used when creating a student"""
    pass
class StudentUpdate(StudentBase):
    pass
class StudentResponse(StudentBase):
    """Model used when returning student information"""
    student_id: int
    created_at: datetime

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "student_id": 1,
                "matric_number": "S12345678Z",
                "full_name": "John Doe",
                "email": "john.doe@example.com",
                "status": "active",
                "created_at": "2023-01-01T12:00:00"
            }
        }