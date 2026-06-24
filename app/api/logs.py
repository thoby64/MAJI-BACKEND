"""
Activity log routes for auditable workflow history.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import ActivityLog
from app.schemas.business import (
    ActivityLogCreate,
    ActivityLogFilterRequest,
    ActivityLogListResponse,
    ActivityLogResponse,
)
from app.security.dependencies import CurrentUser, get_current_user
from app.services.activity_logs import create_activity_log

logs_router = APIRouter(prefix="/api/logs", tags=["activity-logs"])


def _serialize_log(log: ActivityLog) -> ActivityLogResponse:
    return ActivityLogResponse(
        id=log.id,
        user_id=log.user_id,
        utility_mgr_id=log.utility_mgr_id,
        dma_mgr_id=log.dma_mgr_id,
        engineer_id=log.engineer_id,
        user_name=log.user_name,
        user_role=log.user_role,
        action=log.action,
        entity=log.entity,
        entity_id=log.entity_id,
        details=log.details,
        utility_id=log.utility_id,
        dma_id=log.dma_id,
        timestamp=log.timestamp,
    )


def _apply_log_scope(query, current_user: CurrentUser):
    if current_user.user_type == "utility_manager" and current_user.utility_id:
        return query.filter(ActivityLog.utility_id == current_user.utility_id)
    if current_user.user_type == "dma_manager" and current_user.dma_id:
        return query.filter(ActivityLog.dma_id == current_user.dma_id)
    if current_user.user_type in {"engineer", "team_leader"}:
        return query.filter(ActivityLog.engineer_id == current_user.id)
    return query


@logs_router.get("", response_model=ActivityLogListResponse)
async def list_activity_logs(
    action: str | None = Query(None),
    entity: str | None = Query(None),
    entity_id: str | None = Query(None),
    utility_id: str | None = Query(None),
    dma_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = _apply_log_scope(db.query(ActivityLog), current_user)

    if action:
        query = query.filter(ActivityLog.action.ilike(f"%{action}%"))
    if entity:
        query = query.filter(ActivityLog.entity == entity)
    if entity_id:
        query = query.filter(ActivityLog.entity_id == entity_id)
    if utility_id:
        query = query.filter(ActivityLog.utility_id == utility_id)
    if dma_id:
        query = query.filter(ActivityLog.dma_id == dma_id)

    total = query.count()
    logs = query.order_by(ActivityLog.timestamp.desc()).offset(skip).limit(limit).all()
    return ActivityLogListResponse(total=total, items=[_serialize_log(log) for log in logs])


@logs_router.get("/report/{report_id}", response_model=ActivityLogListResponse)
async def list_report_activity_logs(
    report_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = _apply_log_scope(db.query(ActivityLog), current_user)
    logs = (
        query.filter(ActivityLog.entity == "report", ActivityLog.entity_id == report_id)
        .order_by(ActivityLog.timestamp.desc())
        .all()
    )
    return ActivityLogListResponse(total=len(logs), items=[_serialize_log(log) for log in logs])


@logs_router.get("/{log_id}", response_model=ActivityLogResponse)
async def get_activity_log(
    log_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log = _apply_log_scope(db.query(ActivityLog), current_user).filter(ActivityLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity log not found")
    return _serialize_log(log)


@logs_router.post("", response_model=ActivityLogResponse, status_code=status.HTTP_201_CREATED)
async def create_activity_log_entry(
    log_data: ActivityLogCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_log = create_activity_log(
        db,
        action=log_data.action,
        user_name=log_data.user_name,
        user_role=log_data.user_role,
        entity=log_data.entity,
        entity_id=log_data.entity_id,
        details=log_data.details,
        user_id=log_data.user_id,
        utility_mgr_id=log_data.utility_mgr_id,
        dma_mgr_id=log_data.dma_mgr_id,
        engineer_id=log_data.engineer_id,
        utility_id=log_data.utility_id,
        dma_id=log_data.dma_id,
        flush=False,
    )
    db.commit()
    db.refresh(new_log)
    return _serialize_log(new_log)


@logs_router.post("/filter", response_model=ActivityLogListResponse)
async def filter_activity_logs(
    filter_data: ActivityLogFilterRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = _apply_log_scope(db.query(ActivityLog), current_user)

    if filter_data.user_id:
        query = query.filter(ActivityLog.user_id == filter_data.user_id)
    if filter_data.action:
        query = query.filter(ActivityLog.action.ilike(f"%{filter_data.action}%"))
    if filter_data.entity:
        query = query.filter(ActivityLog.entity == filter_data.entity)
    if filter_data.entity_id:
        query = query.filter(ActivityLog.entity_id == filter_data.entity_id)
    if filter_data.utility_id:
        query = query.filter(ActivityLog.utility_id == filter_data.utility_id)
    if filter_data.dma_id:
        query = query.filter(ActivityLog.dma_id == filter_data.dma_id)
    if filter_data.start_date:
        query = query.filter(ActivityLog.timestamp >= filter_data.start_date)
    if filter_data.end_date:
        query = query.filter(ActivityLog.timestamp <= filter_data.end_date)

    total = query.count()
    logs = query.order_by(ActivityLog.timestamp.desc()).offset(filter_data.offset).limit(filter_data.limit).all()
    return ActivityLogListResponse(total=total, items=[_serialize_log(log) for log in logs])
