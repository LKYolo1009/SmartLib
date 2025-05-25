from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional
from datetime import datetime


class StudentBase(BaseModel):
    """Student's Basic Information"""
    matric_number: str = Field(
        ..., 
        description="Matric Number (A + 8 digits + any letter)",
        example="A12345678H"
    )
    full_name: str = Field(..., description="Full Name", example="John Doe")
    email: EmailStr = Field(..., description="Email", example="john.doe@u.nus.edu")
    status: Optional[str] = Field("active", description="Status", example="active")
    
    @field_validator('matric_number')
    def validate_matric_number(cls, v):
        """Validate matric number format: A + 8 digits + any letter"""
        if not (len(v) == 10 and 
                v[0] == 'A' and 
                v[1:9].isdigit() and 
                v[9].isalpha()):
            raise ValueError('Matric number format must be: A + 8 digits + any letter (e.g., A12345678B, A23456789C)')
        return v
    
    @field_validator('status')
    def validate_status(cls, v):
        """Validate status for valid values"""
        valid_statuses = ["active", "inactive", "suspended"]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v


class StudentCreate(StudentBase):
    """Model used when creating a student"""
    pass


class StudentUpdate(BaseModel):
    """Model used when updating a student - all fields optional"""
    matric_number: Optional[str] = Field(
        None, 
        description="Matric Number (A + 7 digits + any letter)",
        example="A12345678H"
    )
    full_name: Optional[str] = Field(None, description="Full Name", example="John Doe")
    email: Optional[EmailStr] = Field(None, description="Email", example="john.doe@u.nus.edu")
    status: Optional[str] = Field(None, description="Status", example="active")
    
    @field_validator('matric_number')
    def validate_matric_number(cls, v):
        """Validate matric number format: A + 8 digits + any letter"""
        if v is None:
            return v
        if not (len(v) == 10 and 
                v[0] == 'A' and 
                v[1:9].isdigit() and 
                v[9].isalpha()):
            raise ValueError('Matric number format must be: A + 8 digits + any letter (e.g., A12345678B, A23456789C)')
        return v
    
    @field_validator('status')
    def validate_status(cls, v):
        """Validate status for valid values"""
        if v is None:
            return v
        valid_statuses = ["active", "inactive", "suspended"]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v


class StudentResponse(StudentBase):
    """Model used when returning student information"""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "matric_number": "A12345678Z",
                "full_name": "John Doe",
                "email": "john.doe@u.nus.edu",
                "status": "active",
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-01T12:00:00"
            }
        }