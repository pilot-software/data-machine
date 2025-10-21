from pydantic import BaseModel, Field, validator
from typing import Optional, List
import re

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=100, description="Search query")
    limit: int = Field(10, ge=1, le=50, description="Maximum results")
    chapter: Optional[str] = Field(None, max_length=20, description="Chapter filter")
    
    @validator('query')
    def validate_query(cls, v):
        # Remove dangerous characters and sanitize
        sanitized = re.sub(r'[<>"\';\\]', '', v.strip())
        if not sanitized:
            raise ValueError('Query cannot be empty after sanitization')
        return sanitized
    
    @validator('chapter')
    def validate_chapter(cls, v):
        if v is None:
            return v
        # Allow only alphanumeric, hyphens, and dots
        if not re.match(r'^[A-Za-z0-9\-\.]+$', v):
            raise ValueError('Invalid chapter format')
        return v.strip()

class CodeRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=20, description="Medical code")
    
    @validator('code')
    def validate_code(cls, v):
        # Sanitize and validate medical code format
        sanitized = re.sub(r'[^A-Za-z0-9\.\-]', '', v.strip().upper())
        if not sanitized:
            raise ValueError('Invalid code format')
        return sanitized

class ClinicalQuery(BaseModel):
    symptoms: List[str] = Field(..., min_items=1, max_items=10)
    patient_age: Optional[int] = Field(None, ge=0, le=150)
    patient_gender: Optional[str] = Field(None, pattern=r'^(male|female|other)$')
    
    @validator('symptoms')
    def validate_symptoms(cls, v):
        sanitized = []
        for symptom in v:
            clean = re.sub(r'[<>"\';\\]', '', symptom.strip())
            if clean and len(clean) >= 2:
                sanitized.append(clean[:100])  # Limit length
        if not sanitized:
            raise ValueError('At least one valid symptom required')
        return sanitized