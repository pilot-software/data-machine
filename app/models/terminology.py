from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ICD10Code(BaseModel):
    code: str
    term: str
    chapter: Optional[str] = None
    parent_code: Optional[str] = None
    active: bool = True
    
    # Clinical coding information
    billable: bool = True
    code_type: str = 'diagnosis'
    laterality: Optional[str] = None
    severity: Optional[str] = None
    episode: Optional[str] = None
    
    # Clinical notes
    includes_notes: Optional[str] = None
    excludes1_notes: Optional[str] = None
    excludes2_notes: Optional[str] = None
    code_first_notes: Optional[str] = None
    use_additional_notes: Optional[str] = None
    
    # Metadata
    age_range: Optional[str] = None
    gender_specific: Optional[str] = None


class LoincCode(BaseModel):
    code: str
    component: str
    property: Optional[str] = None
    system: Optional[str] = None
    method: Optional[str] = None
    unit: Optional[str] = None
    active: bool = True


class AutocompleteRequest(BaseModel):
    query: str
    limit: int = 10


class AutocompleteResponse(BaseModel):
    suggestions: List[dict]
    total_count: int
    query_time_ms: float