"""
Engineer Routes
CRUD plus invite-based onboarding for engineers in the DMA -> Team -> Engineer flow.
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database.session import get_db
from app.models import DMA, Engineer, Report, Team
from app.schemas.user import (
    EngineerCreate,
    EngineerInvitationBulkCreate,
    EngineerInvitationComplete,
    EngineerInvitationCreate,
    EngineerUpdate,
)
from app.security.auth import hash_password
from app.security.dependencies import CurrentUser, get_current_user
from app.services.engineer_invites import (
    build_invite_url,
    generate_invite_token,
    hash_invite_token,
    send_engineer_invitation_email,
)

engineers_router = APIRouter(prefix="/api/engineers", tags=["engineers"])


def _utcnow() -> datetime:
    return datetime.utcnow()


def _build_onboarding_status(engineer: Engineer) -> str:
    if engineer.setup_completed_at:
        return "completed"
    if engineer.invite_expires_at and engineer.invite_expires_at < _utcnow():
        return "expired"
    return "pending_setup"


def build_engineer_response(engineer: Engineer, assigned_reports: int | None = None) -> dict[str, Any]:
    """Build engineer response with live hierarchy details."""
    dma = engineer.dma
    team = engineer.team if engineer.team_id else None

    return {
        "id": engineer.id,
        "name": engineer.name,
        "email": engineer.email,
        "phone": engineer.phone,
        "dma_id": engineer.dma_id,
        "dma_name": dma.name if dma else None,
        "team_id": engineer.team_id,
        "team_name": team.name if team else None,
        "status": engineer.status.value if hasattr(engineer.status, "value") else engineer.status,
        "role": engineer.role,
        "assigned_reports": assigned_reports if assigned_reports is not None else (len(engineer.reports) if engineer.reports else 0),
        "onboarding_status": _build_onboarding_status(engineer),
        "invite_expires_at": engineer.invite_expires_at,
        "setup_completed_at": engineer.setup_completed_at,
        "created_at": engineer.created_at,
        "updated_at": engineer.updated_at,
    }


def _get_team_or_400(team_id: str, db: Session) -> Team:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team not found",
        )
    return team


def _sync_team_leadership(engineer: Engineer, team: Team | None, role: str) -> None:
    current_team = engineer.team

    if current_team and current_team.id != getattr(team, "id", None) and current_team.leader_id == engineer.id:
        current_team.leader_id = None

    if role != "team_leader":
        if team and team.leader_id == engineer.id:
            team.leader_id = None
        return

    if not team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team leaders must be assigned to a team",
        )

    if team.leader_id and team.leader_id != engineer.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This team already has a team leader assigned",
        )

    team.leader_id = engineer.id


def _create_invitation(
    invitation_data: EngineerInvitationCreate,
    db: Session,
) -> tuple[Engineer, dict[str, Any]]:
    existing = db.query(Engineer).filter(Engineer.email == invitation_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    team = _get_team_or_400(invitation_data.team_id, db)
    now = _utcnow()
    expires_at = now + timedelta(hours=settings.invite_token_expiry_hours)
    raw_token = generate_invite_token()
    invite_url = build_invite_url(raw_token)

    engineer = Engineer(
        name="Pending Setup",
        email=invitation_data.email,
        password=hash_password(generate_invite_token()),
        phone=None,
        dma_id=team.dma_id,
        team_id=team.id,
        role=invitation_data.role or "engineer",
        status=invitation_data.status,
        invite_token_hash=hash_invite_token(raw_token),
        invite_sent_at=now,
        invite_expires_at=expires_at,
        setup_completed_at=None,
    )

    db.add(engineer)
    db.flush()
    _sync_team_leadership(engineer, team, engineer.role)
    db.commit()
    db.refresh(engineer)

    delivery = send_engineer_invitation_email(
        recipient_email=engineer.email,
        role=engineer.role,
        team_name=team.name,
        dma_name=team.dma.name if team.dma else "Assigned DMA",
        invite_url=invite_url,
    )

    return engineer, {
        "delivery_method": delivery.method,
        "delivery_message": delivery.message,
        "invite_url": delivery.invite_url,
        "expires_at": expires_at,
    }


def _find_invited_engineer_by_token(token: str, db: Session) -> Engineer | None:
    token_hash = hash_invite_token(token)
    return db.query(Engineer).filter(Engineer.invite_token_hash == token_hash).first()


def _engineer_utility_id(engineer: Engineer, db: Session) -> str | None:
    dma = engineer.dma or db.query(DMA).filter(DMA.id == engineer.dma_id).first()
    return dma.utility_id if dma else None


def _ensure_engineer_read_access(current_user: CurrentUser, engineer: Engineer, db: Session) -> None:
    if current_user.user_type == "user":
        return

    if current_user.user_type == "dma_manager" and current_user.dma_id == engineer.dma_id:
        return

    if current_user.user_type == "utility_manager" and current_user.utility_id == _engineer_utility_id(engineer, db):
        return

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def _ensure_engineer_write_access(current_user: CurrentUser, dma_id: str) -> None:
    if current_user.user_type == "user":
        return

    if current_user.user_type == "dma_manager" and current_user.dma_id == dma_id:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only admins and DMA managers for this DMA can manage engineers",
    )


@engineers_router.post("/invitations", status_code=status.HTTP_201_CREATED)
async def invite_engineer(
    invitation_data: EngineerInvitationCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = _get_team_or_400(invitation_data.team_id, db)
    _ensure_engineer_write_access(current_user, team.dma_id)
    engineer, invitation_result = _create_invitation(invitation_data, db)
    return {
        "engineer": build_engineer_response(engineer),
        **invitation_result,
    }


@engineers_router.post("/invitations/bulk", status_code=status.HTTP_201_CREATED)
async def invite_engineers_bulk(
    payload: EngineerInvitationBulkCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items: list[dict[str, Any]] = []

    for invitation in payload.invitations:
        try:
            team = _get_team_or_400(invitation.team_id, db)
            _ensure_engineer_write_access(current_user, team.dma_id)
            engineer, invitation_result = _create_invitation(invitation, db)
            items.append(
                {
                    "ok": True,
                    "email": invitation.email,
                    "engineer": build_engineer_response(engineer),
                    **invitation_result,
                }
            )
        except HTTPException as exc:
            items.append(
                {
                    "ok": False,
                    "email": invitation.email,
                    "detail": exc.detail,
                }
            )

    return {
        "total": len(items),
        "items": items,
    }


@engineers_router.get("/invitations/validate")
async def validate_engineer_invitation(
    token: str = Query(..., min_length=20),
    db: Session = Depends(get_db),
):
    engineer = _find_invited_engineer_by_token(token, db)
    if not engineer:
        return {
            "valid": False,
            "message": "This invitation link is invalid or has already been replaced.",
        }

    if engineer.setup_completed_at:
        return {
            "valid": False,
            "message": "This invitation has already been completed. Please sign in instead.",
        }

    if engineer.invite_expires_at and engineer.invite_expires_at < _utcnow():
        return {
            "valid": False,
            "message": "This invitation has expired. Ask your manager to resend it.",
        }

    return {
        "valid": True,
        "message": "Invitation is valid.",
        "email": engineer.email,
        "role": engineer.role,
        "team_id": engineer.team_id,
        "team_name": engineer.team.name if engineer.team else None,
        "dma_id": engineer.dma_id,
        "dma_name": engineer.dma.name if engineer.dma else None,
        "expires_at": engineer.invite_expires_at,
    }


@engineers_router.post("/invitations/complete")
async def complete_engineer_invitation(
    payload: EngineerInvitationComplete,
    db: Session = Depends(get_db),
):
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    engineer = _find_invited_engineer_by_token(payload.token, db)
    if not engineer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation is invalid or has already been used",
        )

    if engineer.setup_completed_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has already been completed",
        )

    if engineer.invite_expires_at and engineer.invite_expires_at < _utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has expired. Ask your manager to resend it.",
        )

    engineer.name = payload.name.strip()
    engineer.phone = payload.phone.strip() if payload.phone else None
    engineer.password = hash_password(payload.password)
    engineer.setup_completed_at = _utcnow()
    engineer.invite_token_hash = None
    engineer.invite_expires_at = None

    if engineer.team:
        _sync_team_leadership(engineer, engineer.team, engineer.role)

    db.commit()
    db.refresh(engineer)

    return {
        "message": "Account setup completed successfully. You can now sign in.",
        "engineer": build_engineer_response(engineer),
    }


@engineers_router.post("/{engineer_id}/resend-invite")
async def resend_engineer_invitation(
    engineer_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engineer = db.query(Engineer).filter(Engineer.id == engineer_id).first()
    if not engineer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engineer not found",
        )

    _ensure_engineer_write_access(current_user, engineer.dma_id)

    if engineer.setup_completed_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account is already active and does not need another invite",
        )

    if not engineer.team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invited account is missing a team assignment",
        )

    now = _utcnow()
    raw_token = generate_invite_token()
    invite_url = build_invite_url(raw_token)
    engineer.invite_token_hash = hash_invite_token(raw_token)
    engineer.invite_sent_at = now
    engineer.invite_expires_at = now + timedelta(hours=settings.invite_token_expiry_hours)

    delivery = send_engineer_invitation_email(
        recipient_email=engineer.email,
        role=engineer.role,
        team_name=engineer.team.name,
        dma_name=engineer.dma.name if engineer.dma else "Assigned DMA",
        invite_url=invite_url,
    )

    db.commit()
    db.refresh(engineer)

    return {
        "engineer": build_engineer_response(engineer),
        "delivery_method": delivery.method,
        "delivery_message": delivery.message,
        "invite_url": delivery.invite_url,
        "expires_at": engineer.invite_expires_at,
    }


@engineers_router.get("")
async def list_engineers(
    team_id: str = Query(None),
    dma_id: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List engineers with optional team and DMA filters."""
    base_query = db.query(Engineer)

    if current_user.user_type == "dma_manager" and current_user.dma_id:
        base_query = base_query.filter(Engineer.dma_id == current_user.dma_id)
    elif current_user.user_type == "utility_manager" and current_user.utility_id:
        base_query = base_query.join(DMA, DMA.id == Engineer.dma_id).filter(DMA.utility_id == current_user.utility_id)
    elif team_id:
        base_query = base_query.filter(Engineer.team_id == team_id)

    if current_user.user_type in {"user", "utility_manager"} and dma_id:
        base_query = base_query.filter(Engineer.dma_id == dma_id)

    total = base_query.count()

    engineers = (
        base_query
        .options(
            joinedload(Engineer.dma),
            joinedload(Engineer.team),
        )
        .order_by(Engineer.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    engineer_ids = [engineer.id for engineer in engineers]
    assigned_report_counts = {}
    if engineer_ids:
        assigned_report_counts = dict(
            db.query(Report.assigned_engineer_id, func.count(Report.id))
            .filter(Report.assigned_engineer_id.in_(engineer_ids))
            .group_by(Report.assigned_engineer_id)
            .all()
        )

    return {
        "total": total,
        "items": [
            build_engineer_response(engineer, assigned_report_counts.get(engineer.id, 0))
            for engineer in engineers
        ],
    }


@engineers_router.get("/{engineer_id}")
async def get_engineer(
    engineer_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engineer = db.query(Engineer).filter(Engineer.id == engineer_id).first()
    if not engineer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engineer not found",
        )

    _ensure_engineer_read_access(current_user, engineer, db)
    return build_engineer_response(engineer)


@engineers_router.post("", status_code=status.HTTP_201_CREATED)
async def create_engineer(
    engineer_data: EngineerCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a fully configured engineer directly under a team."""
    existing = db.query(Engineer).filter(Engineer.email == engineer_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    team = _get_team_or_400(engineer_data.team_id, db)
    _ensure_engineer_write_access(current_user, team.dma_id)

    new_engineer = Engineer(
        name=engineer_data.name,
        email=engineer_data.email,
        password=hash_password(engineer_data.password),
        phone=engineer_data.phone,
        dma_id=team.dma_id,
        team_id=team.id,
        role=engineer_data.role or "engineer",
        status=engineer_data.status,
        setup_completed_at=_utcnow(),
    )

    db.add(new_engineer)
    db.flush()
    _sync_team_leadership(new_engineer, team, new_engineer.role)
    db.commit()
    db.refresh(new_engineer)

    return build_engineer_response(new_engineer)


@engineers_router.put("")
async def update_engineer(
    engineer_data: EngineerUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update engineer details."""
    engineer_id = getattr(engineer_data, "id", None)
    if not engineer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Engineer ID is required",
        )

    engineer = db.query(Engineer).filter(Engineer.id == engineer_id).first()
    if not engineer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engineer not found",
        )

    _ensure_engineer_write_access(current_user, engineer.dma_id)

    target_team = engineer.team
    next_role = engineer.role

    if engineer_data.name is not None:
        engineer.name = engineer_data.name

    if engineer_data.email is not None:
        existing = db.query(Engineer).filter(
            Engineer.email == engineer_data.email,
            Engineer.id != engineer_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        engineer.email = engineer_data.email

    if engineer_data.phone is not None:
        engineer.phone = engineer_data.phone

    if engineer_data.team_id is not None:
        if engineer_data.team_id == "":
            target_team = None
            engineer.team_id = None
        else:
            target_team = _get_team_or_400(engineer_data.team_id, db)
            _ensure_engineer_write_access(current_user, target_team.dma_id)
            engineer.team_id = target_team.id
            engineer.dma_id = target_team.dma_id

    if engineer_data.role is not None:
        engineer.role = engineer_data.role
        next_role = engineer_data.role

    if engineer_data.status is not None:
        engineer.status = engineer_data.status

    if hasattr(engineer_data, "password") and engineer_data.password:
        engineer.password = hash_password(engineer_data.password)
        engineer.setup_completed_at = engineer.setup_completed_at or _utcnow()

    _sync_team_leadership(engineer, target_team, next_role)

    db.commit()
    db.refresh(engineer)

    return build_engineer_response(engineer)


@engineers_router.delete("")
async def delete_engineer(
    id: str = Query(..., description="Engineer ID to delete"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engineer = db.query(Engineer).filter(Engineer.id == id).first()
    if not engineer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engineer not found",
        )

    _ensure_engineer_write_access(current_user, engineer.dma_id)

    if engineer.team and engineer.team.leader_id == engineer.id:
        engineer.team.leader_id = None

    db.delete(engineer)
    db.commit()

    return {"message": "Engineer deleted successfully"}
