"""
User Routes
CRUD plus invite-based onboarding for public-report user accounts.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import get_db
from app.models import User
from app.models.user import DMAManager, Engineer, UtilityManager
from app.schemas.user import (
    UserCreate,
    UserInvitationCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.security.auth import extract_user_from_token, hash_password
from app.services.engineer_invites import (
    build_invite_url,
    generate_invite_token,
    hash_invite_token,
    send_account_invitation_email,
)


users_router = APIRouter(prefix="/api/users", tags=["users"])


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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This email is already in use by a {label}",
            )


def _build_onboarding_status(user: User) -> str:
    if user.setup_completed_at:
        return "completed"
    if user.invite_expires_at and user.invite_expires_at < _utcnow():
        return "expired"
    return "pending_setup"


def transform_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "phone": user.phone,
        "avatar": user.avatar,
        "status": user.status.value if hasattr(user.status, "value") else user.status,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "user_type": "user",
        "role": None,
        "utility_id": None,
        "utility_name": None,
        "dma_id": None,
        "dma_name": None,
        "team_id": None,
        "team_name": None,
        "onboarding_status": _build_onboarding_status(user),
        "invite_expires_at": user.invite_expires_at,
        "setup_completed_at": user.setup_completed_at,
    }


@users_router.get("", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(User).count()
    users = db.query(User).offset(skip).limit(limit).all()
    return UserListResponse(total=total, items=[UserResponse(**transform_user(user)) for user in users])


@users_router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    if authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    user_info = extract_user_from_token(token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = user_info["user_id"]

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return UserResponse(**transform_user(user))

    engineer = db.query(Engineer).filter(Engineer.id == user_id).first()
    if engineer:
        return UserResponse.from_orm(engineer)

    util_mgr = db.query(UtilityManager).filter(UtilityManager.id == user_id).first()
    if util_mgr:
        return UserResponse.from_orm(util_mgr)

    dma_mgr = db.query(DMAManager).filter(DMAManager.id == user_id).first()
    if dma_mgr:
        return UserResponse.from_orm(dma_mgr)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )


@users_router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse(**transform_user(user))


@users_router.post("/invitations", status_code=status.HTTP_201_CREATED)
async def invite_user(payload: UserInvitationCreate, db: Session = Depends(get_db)):
    _check_email_uniqueness(payload.email, None, db)

    now = _utcnow()
    expires_at = now + timedelta(hours=settings.invite_token_expiry_hours)
    raw_token = generate_invite_token()

    user = User(
        email=payload.email,
        name="Pending Setup",
        phone=None,
        avatar=None,
        status=payload.status,
        password=hash_password(generate_invite_token()),
        invite_token_hash=hash_invite_token(raw_token),
        invite_sent_at=now,
        invite_expires_at=expires_at,
        setup_completed_at=None,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    delivery = send_account_invitation_email(
        recipient_email=user.email,
        role_label="Majiscope User",
        assignment_lines=["Access: Public reporting account"],
        invite_url=build_invite_url(raw_token),
    )

    return {
        "user": transform_user(user),
        "delivery_method": delivery.method,
        "delivery_message": delivery.message,
        "invite_url": delivery.invite_url,
        "expires_at": expires_at,
    }


@users_router.post("/{user_id}/resend-invite")
async def resend_user_invite(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.setup_completed_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account is already active and does not need another invite",
        )

    now = _utcnow()
    raw_token = generate_invite_token()
    user.invite_token_hash = hash_invite_token(raw_token)
    user.invite_sent_at = now
    user.invite_expires_at = now + timedelta(hours=settings.invite_token_expiry_hours)
    db.commit()
    db.refresh(user)

    delivery = send_account_invitation_email(
        recipient_email=user.email,
        role_label="Majiscope User",
        assignment_lines=["Access: Public reporting account"],
        invite_url=build_invite_url(raw_token),
    )

    return {
        "user": transform_user(user),
        "delivery_method": delivery.method,
        "delivery_message": delivery.message,
        "invite_url": delivery.invite_url,
        "expires_at": user.invite_expires_at,
    }


@users_router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    _check_email_uniqueness(user_data.email, None, db)

    new_user = User(
        email=user_data.email,
        name=user_data.name,
        phone=user_data.phone,
        avatar=user_data.avatar,
        status=user_data.status,
        password=hash_password(user_data.password),
        setup_completed_at=_utcnow(),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(**transform_user(new_user))


@users_router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    update_data = user_data.dict(exclude_unset=True)
    if "email" in update_data and update_data["email"]:
        _check_email_uniqueness(update_data["email"], user_id, db)

    if update_data.get("password"):
        user.password = hash_password(update_data["password"])
        user.setup_completed_at = user.setup_completed_at or _utcnow()

    if "email" in update_data and update_data["email"] is not None:
        user.email = update_data["email"]
    if "name" in update_data and update_data["name"] is not None:
        user.name = update_data["name"]
    if "phone" in update_data:
        user.phone = update_data["phone"]
    if "avatar" in update_data:
        user.avatar = update_data["avatar"]
    if "status" in update_data and update_data["status"] is not None:
        user.status = update_data["status"]

    db.commit()
    db.refresh(user)

    return UserResponse(**transform_user(user))


@users_router.patch("/{user_id}", response_model=UserResponse)
async def patch_user(user_id: str, user_data: UserUpdate, db: Session = Depends(get_db)):
    return await update_user(user_id, user_data, db)


@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()
