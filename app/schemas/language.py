from pydantic import BaseModel, Field, validator
from typing import Optional

class LanguageBase(BaseModel):
    """语言的基本信息"""
    language_code: str = Field(..., description="语言代码", example="CHS")
    language_name: str = Field(..., description="语言名称", example="简体中文")
    
    @validator('language_code')
    def validate_language_code(cls, v):
        """验证语言代码长度为3个字符"""
        if len(v) != 3:
            raise ValueError('语言代码必须是3个字符长')
        return v

class LanguageCreate(LanguageBase):
    """创建语言时使用的模型"""
    pass

class LanguageResponse(LanguageBase):
    """返回语言信息时使用的模型"""
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "language_code": "CHS",
                "language_name": "简体中文"
            }
        }