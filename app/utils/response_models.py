"""
API Response Models
Standardized response formats for all API endpoints
"""

from typing import TypeVar, Generic, Optional, List, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


T = TypeVar('T')


class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class APIError(BaseModel):
    """Standard API error response"""
    success: bool = False
    error: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    path: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    success: bool = True
    data: List[T] = []
    total: int
    skip: int
    limit: int
    has_more: bool = Field(default=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def __init__(self, items: List[T], total: int, skip: int, limit: int, **kwargs):
        has_more = (skip + limit) < total
        super().__init__(
            data=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=has_more,
            **kwargs
        )


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
