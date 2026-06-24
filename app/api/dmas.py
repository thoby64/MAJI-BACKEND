"""
DMA Routes
CRUD operations for District Metering Areas (DMAs)
Includes manager and utility info for proper frontend integration
"""

import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import DMA, DMAManager, Engineer, Report, Team
from app.schemas.user import (
    DMACreate,
    DMAUpdate,
    DMAResponse,
    DMAListResponse,
)
from app.security.dependencies import get_current_user, require_admin, CurrentUser

dmas_router = APIRouter(prefix="/api/dmas", tags=["dmas"])


def _serialize_boundary_geojson(boundary_geojson: Optional[dict[str, Any]]) -> Optional[str]:
    if boundary_geojson is None:
        return None

    if not isinstance(boundary_geojson, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="DMA boundary must be a valid GeoJSON polygon object.",
        )

    if boundary_geojson.get("type") != "Polygon":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="DMA boundary must use GeoJSON Polygon geometry.",
        )

    coordinates = boundary_geojson.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="DMA boundary polygon must include coordinate rings.",
        )

    outer_ring = coordinates[0]
    if not isinstance(outer_ring, list):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="DMA boundary polygon must include an outer coordinate ring.",
        )

    normalized_ring: list[list[float]] = []
    distinct_points: set[tuple[float, float]] = set()

    for raw_point in outer_ring:
        if not isinstance(raw_point, (list, tuple)) or len(raw_point) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Each DMA boundary point must contain longitude and latitude values.",
            )

        try:
            longitude = float(raw_point[0])
            latitude = float(raw_point[1])
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="DMA boundary points must be valid numeric coordinates.",
            ) from None

        if longitude < -180 or longitude > 180 or latitude < -90 or latitude > 90:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="DMA boundary coordinates must be within valid longitude and latitude ranges.",
            )

        normalized_ring.append([longitude, latitude])
        distinct_points.add((longitude, latitude))

    if len(distinct_points) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="DMA boundary polygon must contain at least three distinct points.",
        )

    if normalized_ring[0] != normalized_ring[-1]:
        normalized_ring.append(normalized_ring[0])

    return json.dumps({"type": "Polygon", "coordinates": [normalized_ring]})


def _deserialize_boundary_geojson(raw_value: Optional[str]) -> Optional[dict[str, Any]]:
    if not raw_value:
        return None

    try:
        payload = json.loads(raw_value)
    except json.JSONDecodeError:
        return None

    return payload if isinstance(payload, dict) else None


def transform_dma(dma: DMA) -> dict:
    """Transform DMA to response format with manager and utility info"""
    # Get manager info
    manager_id = None
    manager_name = None
    if dma.manager:
        manager_id = dma.manager.id
        manager_name = dma.manager.name
    
    # Get utility name
    utility_name = dma.utility.name if dma.utility else None
    
    # Count related entities
    teams_count = len(dma.teams) if dma.teams else 0
    engineers_count = len(dma.engineers) if dma.engineers else 0
    reports_count = len(dma.reports) if dma.reports else 0
    
    return {
        "id": dma.id,
        "utility_id": dma.utility_id,
        "utility_name": utility_name,
        "name": dma.name,
        "description": dma.description,
        "center_latitude": dma.center_latitude,
        "center_longitude": dma.center_longitude,
        "boundary_geojson": _deserialize_boundary_geojson(dma.boundary_geojson),
        "status": dma.status.value if hasattr(dma.status, 'value') else dma.status,
        "manager_id": manager_id,
        "manager_name": manager_name,
        "teams_count": teams_count,
        "engineers_count": engineers_count,
        "reports_count": reports_count,
        "created_at": dma.created_at,
        "updated_at": dma.updated_at,
    }


@dmas_router.get("", response_model=DMAListResponse)
async def list_dmas(
    utility_id: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all DMAs with optional utility filter (requires authentication)"""
    query = db.query(DMA)
    
    # Utility managers can only see their own utility's DMAs
    if current_user.user_type == "utility_manager" and current_user.utility_id:
        query = query.filter(DMA.utility_id == current_user.utility_id)
    elif utility_id:
        query = query.filter(DMA.utility_id == utility_id)
    # Admins see all
    
    total = query.count()
    dmas = query.offset(skip).limit(limit).all()
    
    # Transform to include manager and utility info
    transformed = [transform_dma(d) for d in dmas]
    
    return DMAListResponse(
        total=total,
        items=[DMAResponse(**t) for t in transformed],
    )


@dmas_router.get("/{dma_id}", response_model=DMAResponse)
async def get_dma(
    dma_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get DMA by ID (requires authentication)"""
    dma = db.query(DMA).filter(DMA.id == dma_id).first()
    
    if not dma:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DMA not found",
        )
    
    # Utility managers can only access their own utility's DMAs
    if current_user.user_type == "utility_manager" and current_user.utility_id:
        if dma.utility_id != current_user.utility_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this DMA",
            )
    
    return DMAResponse(**transform_dma(dma))


@dmas_router.post("", response_model=DMAResponse, status_code=status.HTTP_201_CREATED)
async def create_dma(
    dma_data: DMACreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new DMA (admin or utility manager of that utility)"""
    # Only admins and utility managers can create DMAs
    if current_user.user_type not in ("user", "utility_manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and utility managers can create DMAs",
        )
    
    # Utility managers can only create DMAs for their own utility
    if current_user.user_type == "utility_manager":
        if dma_data.utility_id != current_user.utility_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Utility managers can only create DMAs for their own utility",
            )
    
    new_dma = DMA(
        utility_id=dma_data.utility_id,
        name=dma_data.name,
        description=dma_data.description,
        center_latitude=dma_data.center_latitude,
        center_longitude=dma_data.center_longitude,
        boundary_geojson=_serialize_boundary_geojson(dma_data.boundary_geojson),
        status=dma_data.status,
    )
    
    db.add(new_dma)
    db.commit()
    db.refresh(new_dma)
    
    return DMAResponse(**transform_dma(new_dma))


@dmas_router.put("/{dma_id}", response_model=DMAResponse)
async def update_dma(
    dma_id: str,
    dma_data: DMAUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update DMA details (admin or utility manager of that utility)"""
    dma = db.query(DMA).filter(DMA.id == dma_id).first()
    
    if not dma:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DMA not found",
        )
    
    # Only admins and utility managers can update DMAs
    if current_user.user_type not in ("user", "utility_manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and utility managers can update DMAs",
        )
    
    # Utility managers can only update DMAs in their own utility
    if current_user.user_type == "utility_manager":
        if dma.utility_id != current_user.utility_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Utility managers can only update DMAs in their own utility",
            )
    
    update_data = dma_data.model_dump(exclude_unset=True)
    if "boundary_geojson" in update_data:
        dma.boundary_geojson = _serialize_boundary_geojson(update_data.pop("boundary_geojson"))
    for field, value in update_data.items():
        setattr(dma, field, value)
    
    db.commit()
    db.refresh(dma)
    
    return DMAResponse(**transform_dma(dma))


@dmas_router.patch("/{dma_id}", response_model=DMAResponse)
async def patch_dma(
    dma_id: str,
    dma_data: DMAUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Partially update DMA (admin or utility manager of that utility)"""
    dma = db.query(DMA).filter(DMA.id == dma_id).first()
    
    if not dma:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DMA not found",
        )
    
    # Only admins and utility managers can update DMAs
    if current_user.user_type not in ("user", "utility_manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and utility managers can update DMAs",
        )
    
    # Utility managers can only update DMAs in their own utility
    if current_user.user_type == "utility_manager":
        if dma.utility_id != current_user.utility_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Utility managers can only update DMAs in their own utility",
            )
    
    update_data = dma_data.model_dump(exclude_unset=True)
    if "boundary_geojson" in update_data:
        dma.boundary_geojson = _serialize_boundary_geojson(update_data.pop("boundary_geojson"))
    for field, value in update_data.items():
        setattr(dma, field, value)
    
    db.commit()
    db.refresh(dma)
    
    return DMAResponse(**transform_dma(dma))


@dmas_router.delete("/{dma_id}", status_code=status.HTTP_200_OK)
async def delete_dma(
    dma_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete DMA by ID (admin or utility manager of that utility)"""
    dma = db.query(DMA).filter(DMA.id == dma_id).first()
    
    if not dma:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DMA not found",
        )
    
    # Only admins and utility managers can delete DMAs
    if current_user.user_type not in ("user", "utility_manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and utility managers can delete DMAs",
        )
    
    # Utility managers can only delete DMAs from their own utility
    if current_user.user_type == "utility_manager":
        if dma.utility_id != current_user.utility_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Utility managers can only delete DMAs from their own utility",
            )
    
    db.delete(dma)
    db.commit()
    
    return {"success": True, "message": "DMA deleted successfully"}
