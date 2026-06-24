"""
Utility Manager Routes
CRUD plus invite-based onboarding for utility managers.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import get_db
from app.models import Engineer, User, Utility, UtilityManager
from app.models.user import DMAManager, EntityStatusEnum
from app.schemas.user import (
    UtilityManagerCreate,
    UtilityManagerInvitationCreate,
    UtilityManagerListResponse,
    UtilityManagerResponse,
    UtilityManagerUpdate,
)
from app.security.auth import hash_password
from app.services.engineer_invites import (
    build_invite_url,
    generate_invite_token,
    hash_invite_token,
    send_account_invitation_email,
)

utility_managers_router = APIRouter(prefix="/api/utility-managers", tags=["utility-managers"])


def _utcnow() -> datetime:
    return datetime.utcnow()


def _build_onboarding_status(manager: UtilityManager) -> str:
    if manager.setup_completed_at:
        return "completed"
    if manager.invite_expires_at and manager.invite_expires_at < _utcnow():
        return "expired"
    return "pending_setup"


def _transform_manager(manager: UtilityManager) -> dict:
    return {
        "id": manager.id,
        "name": manager.name,
        "email": manager.email,
        "phone": manager.phone,
        "status": manager.status.value if hasattr(manager.status, "value") else manager.status,
        "utility_id": manager.utility_id,
        "onboarding_status": _build_onboarding_status(manager),
        "invite_expires_at": manager.invite_expires_at,
        "setup_completed_at": manager.setup_completed_at,
        "avatar": manager.avatar,
        "created_at": manager.created_at,
        "updated_at": manager.updated_at,
    }


def _check_email_uniqueness(email: str, exclude_id: Optional[str], db: Session) -> None:
    for model, label in (
        (User, "user"),
        (UtilityManager, "utility_manager"),
        (DMAManager, "dma_manager"),
        (Engineer, "engineer"),
    ):
        query = db.query(model).filter(model.email == email)
        if exclude_id and hasattr(model, "id"):
            query = query.filter(model.id != exclude_id)
        if query.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This email is already in use by a {label}",
            )


def _parse_status(value):
    return EntityStatusEnum(value) if isinstance(value, str) else value


def _get_utility_or_400(utility_id: Optional[str], db: Session) -> Utility:
    if not utility_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utility is required",
        )

    utility = db.query(Utility).filter(Utility.id == utility_id).first()
    if not utility:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utility not found",
        )
    return utility


@utility_managers_router.get("", response_model=UtilityManagerListResponse)
async def list_utility_managers(
    utility_id: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(UtilityManager)
    if utility_id:
        query = query.filter(UtilityManager.utility_id == utility_id)

    total = query.count()
    managers = query.offset(skip).limit(limit).all()
    return UtilityManagerListResponse(
        total=total,
        items=[UtilityManagerResponse(**_transform_manager(manager)) for manager in managers],
    )


@utility_managers_router.get("/{manager_id}", response_model=UtilityManagerResponse)
async def get_utility_manager(manager_id: str, db: Session = Depends(get_db)):
    manager = db.query(UtilityManager).filter(UtilityManager.id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utility manager assignment not found")
    return UtilityManagerResponse(**_transform_manager(manager))


@utility_managers_router.post("/invitations", status_code=status.HTTP_201_CREATED)
async def invite_utility_manager(
    payload: UtilityManagerInvitationCreate,
    db: Session = Depends(get_db),
):
    _check_email_uniqueness(payload.email, None, db)
    utility = _get_utility_or_400(payload.utility_id, db)

    now = _utcnow()
    expires_at = now + timedelta(hours=settings.invite_token_expiry_hours)
    raw_token = generate_invite_token()

    manager = UtilityManager(
        name="Pending Setup",
        email=payload.email,
        password=hash_password(generate_invite_token()),
        phone=None,
        status=_parse_status(payload.status),
        utility_id=utility.id,
        invite_token_hash=hash_invite_token(raw_token),
        invite_sent_at=now,
        invite_expires_at=expires_at,
        setup_completed_at=None,
    )

    db.add(manager)
    db.commit()
    db.refresh(manager)

    delivery = send_account_invitation_email(
        recipient_email=manager.email,
        role_label="Utility Manager",
        assignment_lines=[f"Utility: {utility.name}"],
        invite_url=build_invite_url(raw_token),
    )

    return {
        "manager": _transform_manager(manager),
        "delivery_method": delivery.method,
        "delivery_message": delivery.message,
        "invite_url": delivery.invite_url,
        "expires_at": expires_at,
    }


@utility_managers_router.post("/{manager_id}/resend-invite")
async def resend_utility_manager_invite(manager_id: str, db: Session = Depends(get_db)):
    manager = db.query(UtilityManager).filter(UtilityManager.id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utility manager assignment not found")
    if manager.setup_completed_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This account is already active and does not need another invite")
    utility = _get_utility_or_400(manager.utility_id, db)

    now = _utcnow()
    raw_token = generate_invite_token()
    manager.invite_token_hash = hash_invite_token(raw_token)
    manager.invite_sent_at = now
    manager.invite_expires_at = now + timedelta(hours=settings.invite_token_expiry_hours)
    db.commit()
    db.refresh(manager)

    delivery = send_account_invitation_email(
        recipient_email=manager.email,
        role_label="Utility Manager",
        assignment_lines=[f"Utility: {utility.name}"],
        invite_url=build_invite_url(raw_token),
    )

    return {
        "manager": _transform_manager(manager),
        "delivery_method": delivery.method,
        "delivery_message": delivery.message,
        "invite_url": delivery.invite_url,
        "expires_at": manager.invite_expires_at,
    }


@utility_managers_router.post("", response_model=UtilityManagerResponse, status_code=status.HTTP_201_CREATED)
async def create_utility_manager(
    manager_data: UtilityManagerCreate,
    db: Session = Depends(get_db),
):
    from sqlalchemy.exc import IntegrityError

    try:
        _check_email_uniqueness(manager_data.email, None, db)
        _get_utility_or_400(manager_data.utility_id, db)

        new_manager = UtilityManager(
            name=manager_data.name,
            email=manager_data.email,
            password=hash_password(manager_data.password),
            phone=manager_data.phone,
            status=_parse_status(manager_data.status),
            utility_id=manager_data.utility_id,
            setup_completed_at=_utcnow(),
        )

        db.add(new_manager)
        db.commit()
        db.refresh(new_manager)
        return UtilityManagerResponse(**_transform_manager(new_manager))
    except IntegrityError as exc:
        db.rollback()
        if "UNIQUE constraint failed" in str(exc) or "duplicate key value" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This utility already has an assigned manager. Unassign the existing manager first.",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Database constraint violation")


@utility_managers_router.put("/{manager_id}", response_model=UtilityManagerResponse)
async def update_utility_manager(
    manager_id: str,
    manager_data: UtilityManagerUpdate,
    db: Session = Depends(get_db),
):
    from sqlalchemy.exc import IntegrityError

    try:
        manager = db.query(UtilityManager).filter(UtilityManager.id == manager_id).first()
        if not manager:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utility manager not found")

        _check_email_uniqueness(manager_data.email, manager_id, db)
        if manager_data.utility_id:
            _get_utility_or_400(manager_data.utility_id, db)

        manager.name = manager_data.name
        manager.email = manager_data.email
        manager.phone = manager_data.phone
        manager.status = _parse_status(manager_data.status)
        manager.utility_id = manager_data.utility_id
        if manager_data.password:
            manager.password = hash_password(manager_data.password)
            manager.setup_completed_at = manager.setup_completed_at or _utcnow()

        db.commit()
        db.refresh(manager)
        return UtilityManagerResponse(**_transform_manager(manager))
    except IntegrityError as exc:
        db.rollback()
        if "UNIQUE constraint failed" in str(exc) or "duplicate key value" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This utility already has an assigned manager. Unassign the existing manager first.",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Database constraint violation")


@utility_managers_router.delete("/{manager_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_utility_manager(manager_id: str, db: Session = Depends(get_db)):
    manager = db.query(UtilityManager).filter(UtilityManager.id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utility manager assignment not found")
    db.delete(manager)
    db.commit()
