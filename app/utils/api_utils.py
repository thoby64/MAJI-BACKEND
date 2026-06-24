"""
API Utilities
Common utility functions for API operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import Any, List, Optional, Dict, Type
from pydantic import BaseModel


def apply_pagination(query, skip: int = 0, limit: int = 10):
    """Apply pagination to a SQLAlchemy query"""
    return query.offset(skip).limit(limit)


def apply_sorting(
    query,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    model: Optional[Type] = None,
):
    """Apply sorting to a SQLAlchemy query"""
    if not sort_by or not model:
        return query
    
    if not hasattr(model, sort_by):
        return query
    
    column = getattr(model, sort_by)
    
    if sort_order.lower() == "desc":
        return query.order_by(desc(column))
    else:
        return query.order_by(asc(column))


def apply_filters(
    query,
    filters: Optional[Dict[str, Any]] = None,
    model: Optional[Type] = None,
):
    """Apply filters to a SQLAlchemy query"""
    if not filters or not model:
        return query
    
    for field, value in filters.items():
        if not hasattr(model, field) or value is None:
            continue
        
        column = getattr(model, field)
        
        # Handle different filter types
        if isinstance(value, str) and "%" in value:
            # Like filter
            query = query.filter(column.ilike(value))
        elif isinstance(value, list):
            # In filter
            query = query.filter(column.in_(value))
        else:
            # Exact match
            query = query.filter(column == value)
    
    return query


def get_or_404(db: Session, model: Type, **filters):
    """Get a single record or raise 404"""
    from app.utils.exceptions import NotFoundError
    
    query = db.query(model)
    for field, value in filters.items():
        if hasattr(model, field):
            query = query.filter(getattr(model, field) == value)
    
    record = query.first()
    
    if not record:
        raise NotFoundError(
            resource_type=model.__name__,
            resource_id=filters.get("id") or filters.get("user_id"),
        )
    
    return record


def paginate(
    db: Session,
    model: Type,
    skip: int = 0,
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "asc",
):
    """Get paginated results with optional filters and sorting"""
    query = db.query(model)
    
    # Apply filters
    query = apply_filters(query, filters, model)
    
    # Apply sorting
    query = apply_sorting(query, sort_by, sort_order, model)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    query = apply_pagination(query, skip, limit)
    
    items = query.all()
    
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 0,
    }


def obj_to_dict(obj: Any, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
    """Convert SQLAlchemy model to dictionary"""
    result = {}
    
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        
        # Skip excluded fields
        if exclude and column.name in exclude:
            continue
        
        # Handle datetime serialization
        if hasattr(value, 'isoformat'):
            value = value.isoformat()
        
        result[column.name] = value
    
    return result


def check_duplicate(
    db: Session,
    model: Type,
    field_name: str,
    value: str,
    exclude_id: Optional[str] = None,
):
    """Check if a field value already exists (for duplicate detection)"""
    query = db.query(model).filter(getattr(model, field_name) == value)
    
    if exclude_id and hasattr(model, "id"):
        query = query.filter(model.id != exclude_id)
    
    return query.first() is not None
