"""
Push notification and notification-record helpers.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

import httpx
from sqlalchemy.orm import Session

from app.models import Notification, NotificationTypeEnum, PushDeviceToken


EXPO_PUSH_API_URL = "https://exp.host/--/api/v2/push/send"


def create_notification_record(
    db: Session,
    *,
    title: str,
    message: str,
    notification_type: NotificationTypeEnum = NotificationTypeEnum.INFO,
    data: Optional[dict[str, Any]] = None,
    link: Optional[str] = None,
    user_id: Optional[str] = None,
    utility_manager_id: Optional[str] = None,
    dma_manager_id: Optional[str] = None,
    engineer_id: Optional[str] = None,
    flush: bool = True,
) -> Notification:
    notification = Notification(
        title=title,
        message=message,
        type=notification_type,
        read=False,
        data=data,
        link=link,
        user_id=user_id,
        utility_mgr_id=utility_manager_id,
        dma_mgr_id=dma_manager_id,
        engineer_id=engineer_id,
    )
    db.add(notification)
    if flush:
        db.flush()
    return notification


def create_bulk_notifications(
    db: Session,
    *,
    recipients: Iterable[dict[str, Optional[str]]],
    title: str,
    message: str,
    notification_type: NotificationTypeEnum = NotificationTypeEnum.INFO,
    data: Optional[dict[str, Any]] = None,
    link: Optional[str] = None,
) -> list[Notification]:
    notifications: list[Notification] = []
    for recipient in recipients:
        notifications.append(
            create_notification_record(
                db,
                title=title,
                message=message,
                notification_type=notification_type,
                data=data,
                link=link,
                user_id=recipient.get("user_id"),
                utility_manager_id=recipient.get("utility_manager_id"),
                dma_manager_id=recipient.get("dma_manager_id"),
                engineer_id=recipient.get("engineer_id"),
                flush=False,
            )
        )
    db.flush()
    return notifications


def deliver_notification_push(notification: Notification, db: Session) -> None:
    tokens = _get_notification_tokens(notification, db)
    if not tokens:
        return

    payloads = [
        {
            "to": token.expo_push_token,
            "sound": "default",
            "title": notification.title,
            "body": notification.message,
            "data": notification.data or {},
        }
        for token in tokens
    ]

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(EXPO_PUSH_API_URL, json=payloads)
            response.raise_for_status()
            response_data = response.json()
    except Exception as error:
        print(f"[push_notifications] Failed to send Expo push payloads: {error}")
        return

    ticket_items = response_data.get("data", []) if isinstance(response_data, dict) else response_data
    for token, ticket in zip(tokens, ticket_items):
        details = ticket.get("details") if isinstance(ticket, dict) else None
        if not details:
            continue
        if details.get("error") == "DeviceNotRegistered":
            token.active = False


def deliver_notifications_push(notifications: Iterable[Notification], db: Session) -> None:
    for notification in notifications:
        deliver_notification_push(notification, db)


def _get_notification_tokens(notification: Notification, db: Session) -> list[PushDeviceToken]:
    query = db.query(PushDeviceToken).filter(PushDeviceToken.active.is_(True))
    if notification.engineer_id:
        return query.filter(PushDeviceToken.engineer_id == notification.engineer_id).all()
    if notification.dma_mgr_id:
        return query.filter(PushDeviceToken.dma_mgr_id == notification.dma_mgr_id).all()
    if notification.utility_mgr_id:
        return query.filter(PushDeviceToken.utility_mgr_id == notification.utility_mgr_id).all()
    if notification.user_id:
        return query.filter(PushDeviceToken.user_id == notification.user_id).all()
    return []
