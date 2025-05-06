from pydantic import BaseModel, Field, field_validator
from typing import Optional

class LanguageBase(BaseModel):
    """Language's Basic Information"""
    language_code: str = Field(..., description="Language Code", example="CHS")
    language_name: str = Field(..., description="Language Name", example="Simplified Chinese")
    
    @field_validator('language_code')
    def validate_language_code(cls, v):
        """Validate language code length is 3 characters"""
        if len(v) != 3:
            raise ValueError('Language code must be 3 characters long')
        return v

class LanguageCreate(LanguageBase):
    """Model used when creating a language"""
    pass

class LanguageUpdate(LanguageBase):
    pass
class LanguageResponse(LanguageBase):
    """Model used when returning language information"""
    class Config:
        orm_mode = True
        json_schema_extra = {
            "example": {
                "language_code": "CHS",
                "language_name": "Simplified Chinese"
            }
        }