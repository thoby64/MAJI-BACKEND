"""
Notification Routes
CRUD operations for notifications
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import Notification
from app.schemas.business import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationListResponse,
    NotificationBulkCreate,
)
from app.security.dependencies import get_current_user, CurrentUser
from app.services.push_notifications import deliver_notification_push, deliver_notifications_push

notifications_router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _serialize_notification(notification: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=notification.id,
        notification_type=getattr(notification.type, "value", notification.type),
        title=notification.title,
        message=notification.message,
        is_read=notification.read,
        data=notification.data,
        user_id=notification.user_id,
        utility_manager_id=notification.utility_mgr_id,
        dma_manager_id=notification.dma_mgr_id,
        engineer_id=notification.engineer_id,
        created_at=notification.created_at,
        updated_at=notification.updated_at,
        link=notification.link,
    )


def _apply_notification_scope(query, current_user: CurrentUser):
    if current_user.user_type in {"engineer", "team_leader"}:
        return query.filter(Notification.engineer_id == current_user.id)
    if current_user.user_type == "dma_manager":
        return query.filter(Notification.dma_mgr_id == current_user.id)
    if current_user.user_type == "utility_manager":
        return query.filter(Notification.utility_mgr_id == current_user.id)
    return query


def _get_notification_or_404(
    notification_id: str,
    current_user: CurrentUser,
    db: Session,
):
    query = _apply_notification_scope(db.query(Notification), current_user)
    notification = query.filter(Notification.id == notification_id).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return notification


@notifications_router.get("", response_model=NotificationListResponse)
async def list_notifications(
    user_id: str = Query(None),
    is_read: bool = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all notifications with optional filters"""
    query = _apply_notification_scope(db.query(Notification), current_user)
    
    if user_id and current_user.user_type == "user":
        query = query.filter(Notification.user_id == user_id)
    
    if is_read is not None:
        query = query.filter(Notification.read == is_read)
    
    total = query.count()
    notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    return NotificationListResponse(
        total=total,
        items=[_serialize_notification(n) for n in notifications],
    )


@notifications_router.get("/unread-count")
async def get_unread_count(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get unread notification count for the authenticated user."""
    query = _apply_notification_scope(db.query(Notification), current_user)
    unread = query.filter(Notification.read.is_(False)).count()
    return {"unread": unread}


@notifications_router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get notification by ID"""
    notification = _get_notification_or_404(notification_id, current_user, db)
    return _serialize_notification(notification)


@notifications_router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new notification"""
    # Ensure at least one recipient is specified
    if not any([
        notification_data.user_id,
        notification_data.utility_manager_id,
        notification_data.dma_manager_id,
        notification_data.engineer_id,
    ]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one recipient must be specified",
        )
    
    new_notification = Notification(
        type=notification_data.notification_type,
        title=notification_data.title,
        message=notification_data.message,
        read=notification_data.is_read,
        data=notification_data.data,
        link=notification_data.link,
        user_id=notification_data.user_id,
        utility_mgr_id=notification_data.utility_manager_id,
        dma_mgr_id=notification_data.dma_manager_id,
        engineer_id=notification_data.engineer_id,
    )
    
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    deliver_notification_push(new_notification, db)
    
    return _serialize_notification(new_notification)


@notifications_router.post("/bulk/create", response_model=List[NotificationResponse])
async def create_bulk_notifications(
    bulk_data: NotificationBulkCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create notifications for multiple recipients"""
    notifications = []
    
    # Create notification for each user_id
    for user_id in bulk_data.user_ids or []:
        notif = Notification(
            type=bulk_data.notification_type,
            title=bulk_data.title,
            message=bulk_data.message,
            data=bulk_data.data,
            link=bulk_data.link,
            user_id=user_id,
        )
        notifications.append(notif)
    
    # Create notification for each utility_manager_id
    for ut_mgr_id in bulk_data.utility_manager_ids or []:
        notif = Notification(
            type=bulk_data.notification_type,
            title=bulk_data.title,
            message=bulk_data.message,
            data=bulk_data.data,
            link=bulk_data.link,
            utility_mgr_id=ut_mgr_id,
        )
        notifications.append(notif)
    
    # Create notification for each dma_manager_id
    for dma_mgr_id in bulk_data.dma_manager_ids or []:
        notif = Notification(
            type=bulk_data.notification_type,
            title=bulk_data.title,
            message=bulk_data.message,
            data=bulk_data.data,
            link=bulk_data.link,
            dma_mgr_id=dma_mgr_id,
        )
        notifications.append(notif)
    
    # Create notification for each engineer_id
    for eng_id in bulk_data.engineer_ids or []:
        notif = Notification(
            type=bulk_data.notification_type,
            title=bulk_data.title,
            message=bulk_data.message,
            data=bulk_data.data,
            link=bulk_data.link,
            engineer_id=eng_id,
        )
        notifications.append(notif)
    
    if not notifications:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No recipients specified",
        )
    
    db.add_all(notifications)
    db.commit()
    deliver_notifications_push(notifications, db)
    
    return [_serialize_notification(n) for n in notifications]


@notifications_router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: str,
    notification_data: NotificationUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update notification details"""
    notification = _get_notification_or_404(notification_id, current_user, db)
    update_data = notification_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "is_read":
            notification.read = value
        elif field == "data":
            notification.data = value
        elif field == "link":
            notification.link = value
        else:
            setattr(notification, field, value)
    
    db.commit()
    db.refresh(notification)
    
    return _serialize_notification(notification)


@notifications_router.patch("/{notification_id}", response_model=NotificationResponse)
async def patch_notification(
    notification_id: str,
    notification_data: NotificationUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Partially update notification"""
    return await update_notification(notification_id, notification_data, current_user, db)


@notifications_router.post("/{notification_id}/mark-as-read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark notification as read"""
    notification = _get_notification_or_404(notification_id, current_user, db)
    notification.read = True
    
    db.commit()
    db.refresh(notification)
    
    return _serialize_notification(notification)


@notifications_router.post("/mark-all-read")
async def mark_all_as_read(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all scoped notifications as read for the authenticated user."""
    query = _apply_notification_scope(db.query(Notification), current_user)
    notifications = query.filter(Notification.read.is_(False)).all()

    for notification in notifications:
        notification.read = True

    db.commit()
    return {"updated": len(notifications)}


@notifications_router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete notification by ID"""
    notification = _get_notification_or_404(notification_id, current_user, db)
    db.delete(notification)
    db.commit()
