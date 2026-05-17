from pydantic import BaseModel
from typing import Optional, List


class QueryRequest(BaseModel):
    query: str


class ExtractedIntelligence(BaseModel):
    intent:      Optional[str]       = None
    geography:   Optional[str]       = None
    domain:      Optional[str]       = None
    entity_type: Optional[str]       = None
    keywords:    Optional[List[str]] = None
    temporal:    Optional[str]       = None


class QueryResponse(BaseModel):
    id:         str
    raw_query:  str
    extracted:  ExtractedIntelligence
    created_at: str