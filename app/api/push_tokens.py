"""
Push token routes for mobile device registration.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import PushDeviceToken
from app.schemas.business import PushTokenRegisterRequest, PushTokenResponse
from app.security.dependencies import CurrentUser, get_current_user


push_tokens_router = APIRouter(prefix="/api/push-tokens", tags=["push-tokens"])


def _apply_owner(token: PushDeviceToken, current_user: CurrentUser) -> None:
    token.user_id = None
    token.utility_mgr_id = None
    token.dma_mgr_id = None
    token.engineer_id = None

    if current_user.user_type in {"engineer", "team_leader"}:
        token.engineer_id = current_user.id
    elif current_user.user_type == "dma_manager":
        token.dma_mgr_id = current_user.id
    elif current_user.user_type == "utility_manager":
        token.utility_mgr_id = current_user.id
    else:
        token.user_id = current_user.id


def _scope_query(db: Session, current_user: CurrentUser):
    query = db.query(PushDeviceToken)
    if current_user.user_type in {"engineer", "team_leader"}:
        return query.filter(PushDeviceToken.engineer_id == current_user.id)
    if current_user.user_type == "dma_manager":
        return query.filter(PushDeviceToken.dma_mgr_id == current_user.id)
    if current_user.user_type == "utility_manager":
        return query.filter(PushDeviceToken.utility_mgr_id == current_user.id)
    return query.filter(PushDeviceToken.user_id == current_user.id)


@push_tokens_router.get("", response_model=list[PushTokenResponse])
async def list_push_tokens(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tokens = _scope_query(db, current_user).order_by(PushDeviceToken.updated_at.desc()).all()
    return tokens


@push_tokens_router.post("/register", response_model=PushTokenResponse, status_code=status.HTTP_201_CREATED)
async def register_push_token(
    payload: PushTokenRegisterRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token = (
        db.query(PushDeviceToken)
        .filter(PushDeviceToken.expo_push_token == payload.expo_push_token)
        .first()
    )

    if token is None and payload.device_id:
        token = _scope_query(db, current_user).filter(PushDeviceToken.device_id == payload.device_id).first()

    if token is None:
        token = PushDeviceToken(expo_push_token=payload.expo_push_token)
        db.add(token)

    _apply_owner(token, current_user)
    token.expo_push_token = payload.expo_push_token
    token.platform = payload.platform
    token.device_name = payload.device_name
    token.device_id = payload.device_id
    token.app_role = payload.app_role or current_user.role or current_user.user_type
    token.active = True
    token.last_registered_at = datetime.utcnow()

    db.commit()
    db.refresh(token)
    return token


@push_tokens_router.post("/deactivate")
async def deactivate_push_token(
    expo_push_token: str = Query(..., min_length=1),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token = _scope_query(db, current_user).filter(PushDeviceToken.expo_push_token == expo_push_token).first()
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Push token not found")

    token.active = False
    db.commit()
    return {"message": "Push token deactivated"}
