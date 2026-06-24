"""
DMA Manager Routes
CRUD plus invite-based onboarding for DMA managers.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import get_db
from app.models import DMA, Engineer, User, Utility
from app.models.user import DMAManager, EntityStatusEnum, UtilityManager
from app.schemas.user import DMAManagerCreate, DMAManagerInvitationCreate, DMAManagerListResponse, DMAManagerResponse, DMAManagerUpdate
from app.security.auth import hash_password
from app.services.engineer_invites import build_invite_url, generate_invite_token, hash_invite_token, send_account_invitation_email

dma_managers_router = APIRouter(prefix="/api/dma-managers", tags=["dma-managers"])


def _utcnow() -> datetime:
    return datetime.utcnow()


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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"This email is already in use by a {label}")


def _parse_status(status_str):
    return EntityStatusEnum(status_str) if isinstance(status_str, str) else status_str


def _build_onboarding_status(manager: DMAManager) -> str:
    if manager.setup_completed_at:
        return "completed"
    if manager.invite_expires_at and manager.invite_expires_at < _utcnow():
        return "expired"
    return "pending_setup"


def transform_manager(manager: DMAManager) -> dict:
    return {
        "id": manager.id,
        "name": manager.name,
        "email": manager.email,
        "phone": manager.phone,
        "status": manager.status.value if hasattr(manager.status, "value") else manager.status,
        "role": "dma_manager",
        "utility_id": manager.utility_id,
        "utility_name": manager.utility.name if manager.utility else None,
        "dma_id": manager.dma_id,
        "dma_name": manager.dma.name if manager.dma else None,
        "onboarding_status": _build_onboarding_status(manager),
        "invite_expires_at": manager.invite_expires_at,
        "setup_completed_at": manager.setup_completed_at,
        "avatar": manager.avatar,
        "created_at": manager.created_at,
        "updated_at": manager.updated_at,
    }


def _get_utility_or_400(utility_id: str, db: Session) -> Utility:
    utility = db.query(Utility).filter(Utility.id == utility_id).first()
    if not utility:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utility not found")
    return utility


def _get_dma_or_400(dma_id: Optional[str], db: Session) -> Optional[DMA]:
    if not dma_id:
        return None
    dma = db.query(DMA).filter(DMA.id == dma_id).first()
    if not dma:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="DMA not found")
    return dma


def _reserve_dma_for_manager(dma_id: Optional[str], manager_id: Optional[str], db: Session) -> None:
    if not dma_id:
        return
    db.query(DMAManager).filter(DMAManager.dma_id == dma_id)
    db.query(DMAManager).filter(DMAManager.dma_id == dma_id, DMAManager.id != manager_id).update({DMAManager.dma_id: None}, synchronize_session=False)


@dma_managers_router.get("", response_model=DMAManagerListResponse)
async def list_dma_managers(
    utility_id: str = Query(None),
    dma_id: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(DMAManager).join(Utility, isouter=True).join(DMA, isouter=True)
    if utility_id:
        query = query.filter(DMAManager.utility_id == utility_id)
    if dma_id:
        query = query.filter(DMAManager.dma_id == dma_id)
    total = query.count()
    managers = query.offset(skip).limit(limit).all()
    return DMAManagerListResponse(total=total, items=[DMAManagerResponse(**transform_manager(m)) for m in managers])


@dma_managers_router.get("/{manager_id}", response_model=DMAManagerResponse)
async def get_dma_manager(manager_id: str, db: Session = Depends(get_db)):
    manager = db.query(DMAManager).filter(DMAManager.id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DMA manager not found")
    return DMAManagerResponse(**transform_manager(manager))


@dma_managers_router.post("/invitations", status_code=status.HTTP_201_CREATED)
async def invite_dma_manager(payload: DMAManagerInvitationCreate, db: Session = Depends(get_db)):
    _check_email_uniqueness(payload.email, None, db)
    utility = _get_utility_or_400(payload.utility_id, db)
    dma = _get_dma_or_400(payload.dma_id, db)
    if dma and dma.utility_id != utility.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected DMA does not belong to the selected utility")

    now = _utcnow()
    expires_at = now + timedelta(hours=settings.invite_token_expiry_hours)
    raw_token = generate_invite_token()

    if dma:
        _reserve_dma_for_manager(dma.id, None, db)

    manager = DMAManager(
        name="Pending Setup",
        email=payload.email,
        password=hash_password(generate_invite_token()),
        phone=None,
        status=_parse_status(payload.status),
        utility_id=utility.id,
        dma_id=dma.id if dma else None,
        invite_token_hash=hash_invite_token(raw_token),
        invite_sent_at=now,
        invite_expires_at=expires_at,
        setup_completed_at=None,
    )

    db.add(manager)
    db.commit()
    db.refresh(manager)

    assignment_lines = [f"Utility: {utility.name}"]
    if dma:
      assignment_lines.append(f"DMA: {dma.name}")

    delivery = send_account_invitation_email(
        recipient_email=manager.email,
        role_label="DMA Manager",
        assignment_lines=assignment_lines,
        invite_url=build_invite_url(raw_token),
    )

    return {
        "manager": transform_manager(manager),
        "delivery_method": delivery.method,
        "delivery_message": delivery.message,
        "invite_url": delivery.invite_url,
        "expires_at": expires_at,
    }


@dma_managers_router.post("/{manager_id}/resend-invite")
async def resend_dma_manager_invite(manager_id: str, db: Session = Depends(get_db)):
    manager = db.query(DMAManager).filter(DMAManager.id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DMA manager not found")
    if manager.setup_completed_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This account is already active and does not need another invite")

    utility = _get_utility_or_400(manager.utility_id, db)
    dma = manager.dma
    now = _utcnow()
    raw_token = generate_invite_token()
    manager.invite_token_hash = hash_invite_token(raw_token)
    manager.invite_sent_at = now
    manager.invite_expires_at = now + timedelta(hours=settings.invite_token_expiry_hours)
    db.commit()
    db.refresh(manager)

    assignment_lines = [f"Utility: {utility.name}"]
    if dma:
        assignment_lines.append(f"DMA: {dma.name}")

    delivery = send_account_invitation_email(
        recipient_email=manager.email,
        role_label="DMA Manager",
        assignment_lines=assignment_lines,
        invite_url=build_invite_url(raw_token),
    )

    return {
        "manager": transform_manager(manager),
        "delivery_method": delivery.method,
        "delivery_message": delivery.message,
        "invite_url": delivery.invite_url,
        "expires_at": manager.invite_expires_at,
    }


@dma_managers_router.post("", response_model=DMAManagerResponse, status_code=status.HTTP_201_CREATED)
async def create_dma_manager(manager_data: DMAManagerCreate, db: Session = Depends(get_db)):
    _check_email_uniqueness(manager_data.email, None, db)
    utility = _get_utility_or_400(manager_data.utility_id, db)
    dma = _get_dma_or_400(manager_data.dma_id, db)
    if dma and dma.utility_id != utility.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected DMA does not belong to the selected utility")
    if dma:
        _reserve_dma_for_manager(dma.id, None, db)

    new_manager = DMAManager(
        name=manager_data.name,
        email=manager_data.email,
        password=hash_password(manager_data.password),
        phone=manager_data.phone,
        status=_parse_status(manager_data.status),
        utility_id=manager_data.utility_id,
        dma_id=manager_data.dma_id,
        setup_completed_at=_utcnow(),
    )
    db.add(new_manager)
    db.commit()
    db.refresh(new_manager)
    return DMAManagerResponse(**transform_manager(new_manager))


@dma_managers_router.put("/{manager_id}", response_model=DMAManagerResponse)
async def update_dma_manager(manager_id: str, manager_data: DMAManagerUpdate, db: Session = Depends(get_db)):
    manager = db.query(DMAManager).filter(DMAManager.id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DMA manager not found")

    update_data = manager_data.dict(exclude_unset=True)
    if "email" in update_data and update_data["email"]:
        _check_email_uniqueness(update_data["email"], manager_id, db)

    next_utility_id = update_data.get("utility_id", manager.utility_id)
    utility = _get_utility_or_400(next_utility_id, db)
    next_dma_id = update_data.get("dma_id", manager.dma_id)
    dma = _get_dma_or_400(next_dma_id, db)
    if dma and dma.utility_id != utility.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected DMA does not belong to the selected utility")
    if next_dma_id and next_dma_id != manager.dma_id:
        _reserve_dma_for_manager(next_dma_id, manager_id, db)

    if update_data.get("password"):
        manager.password = hash_password(update_data["password"])
        manager.setup_completed_at = manager.setup_completed_at or _utcnow()
    if "name" in update_data and update_data["name"] is not None:
        manager.name = update_data["name"]
    if "email" in update_data and update_data["email"] is not None:
        manager.email = update_data["email"]
    if "phone" in update_data:
        manager.phone = update_data["phone"]
    if "status" in update_data and update_data["status"] is not None:
        manager.status = _parse_status(update_data["status"])
    if "utility_id" in update_data and update_data["utility_id"] is not None:
        manager.utility_id = update_data["utility_id"]
    if "dma_id" in update_data:
        manager.dma_id = update_data["dma_id"]

    db.commit()
    db.refresh(manager)
    return DMAManagerResponse(**transform_manager(manager))


@dma_managers_router.delete("/{manager_id}", status_code=status.HTTP_200_OK)
async def delete_dma_manager(manager_id: str, db: Session = Depends(get_db)):
    manager = db.query(DMAManager).filter(DMAManager.id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DMA manager not found")
    db.delete(manager)
    db.commit()
    return {"success": True, "message": "DMA manager deleted successfully"}
