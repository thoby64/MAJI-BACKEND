"""
Team Routes
CRUD operations for teams in the simplified DMA -> Team -> Engineer flow.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.database.session import get_db
from app.models import DMA, Engineer, Report, Team, Utility
from app.models.user import EntityStatusEnum
from app.schemas.user import TeamCreate, TeamResponse, TeamUpdate
from app.security.dependencies import CurrentUser, get_current_user

teams_router = APIRouter(prefix="/api/teams", tags=["teams"])


class TeamListResponse(BaseModel):
    total: int
    items: List[TeamResponse]


class TeamWithDetails(TeamResponse):
    dma_name: Optional[str] = None
    utility_id: Optional[str] = None
    utility_name: Optional[str] = None
    leader_id: Optional[str] = None
    leader_name: Optional[str] = None
    leader_email: Optional[str] = None
    leader_phone: Optional[str] = None
    member_count: int = 0
    active_reports: int = 0
    engineer_ids: List[str] = []


class TeamListWithDetailsResponse(BaseModel):
    total: int
    items: List[TeamWithDetails]


def _build_team_with_details(team: Team, db: Session) -> TeamWithDetails:
    dma = team.dma or db.query(DMA).filter(DMA.id == team.dma_id).first()
    utility = dma.utility if dma and getattr(dma, "utility", None) else (
        db.query(Utility).filter(Utility.id == dma.utility_id).first() if dma else None
    )
    leader = team.leader if team.leader_id else None
    members = sorted(list(team.engineers or []), key=lambda engineer: engineer.name or "")
    active_reports = sum(
        1
        for report in (team.reports or [])
        if str(getattr(getattr(report, "status", None), "value", getattr(report, "status", ""))).lower()
        in {"new", "assigned", "in_progress", "pending_approval"}
    )

    return TeamWithDetails(
        id=team.id,
        name=team.name,
        description=team.description,
        dma_id=team.dma_id,
        status=team.status,
        created_at=team.created_at,
        updated_at=team.updated_at,
        dma_name=dma.name if dma else None,
        utility_id=dma.utility_id if dma else None,
        utility_name=utility.name if utility else None,
        leader_id=team.leader_id,
        leader_name=leader.name if leader else None,
        leader_email=leader.email if leader else None,
        leader_phone=leader.phone if leader else None,
        member_count=len(members),
        active_reports=active_reports,
        engineer_ids=[member.id for member in members],
    )


def _get_team_utility_id(team: Team, db: Session) -> Optional[str]:
    dma = db.query(DMA).filter(DMA.id == team.dma_id).first()
    return dma.utility_id if dma else None


def _ensure_team_read_access(current_user: CurrentUser, team: Team, db: Session) -> None:
    if current_user.user_type == "user":
        return

    if current_user.user_type == "dma_manager" and current_user.dma_id == team.dma_id:
        return

    if current_user.user_type == "utility_manager" and current_user.utility_id == _get_team_utility_id(team, db):
        return

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def _ensure_team_write_access(current_user: CurrentUser, dma_id: str) -> None:
    if current_user.user_type == "user":
        return

    if current_user.user_type == "dma_manager" and current_user.dma_id == dma_id:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only admins and DMA managers for this DMA can manage teams",
    )


@teams_router.get("", response_model=TeamListWithDetailsResponse)
async def list_teams(
    dma_id: str = Query(None),
    utility_id: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List teams with optional DMA and utility filters."""
    query = db.query(Team).options(
        joinedload(Team.dma).joinedload(DMA.utility),
        joinedload(Team.leader),
        selectinload(Team.engineers),
        selectinload(Team.reports),
    )

    if current_user.user_type == "dma_manager" and current_user.dma_id:
        query = query.filter(Team.dma_id == current_user.dma_id)
    elif current_user.user_type == "utility_manager" and current_user.utility_id:
        query = query.join(DMA, DMA.id == Team.dma_id).filter(DMA.utility_id == current_user.utility_id)
    elif dma_id:
        query = query.filter(Team.dma_id == dma_id)
    elif utility_id:
        query = query.join(DMA, DMA.id == Team.dma_id).filter(DMA.utility_id == utility_id)

    total = query.count()
    teams = query.offset(skip).limit(limit).all()

    return TeamListWithDetailsResponse(
        total=total,
        items=[_build_team_with_details(team, db) for team in teams],
    )


@teams_router.get("/{team_id}", response_model=TeamWithDetails)
async def get_team(
    team_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    _ensure_team_read_access(current_user, team, db)
    return _build_team_with_details(team, db)


@teams_router.post("", response_model=TeamWithDetails, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dma = db.query(DMA).filter(DMA.id == team_data.dma_id).first()
    if not dma:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DMA not found",
        )

    _ensure_team_write_access(current_user, dma.id)

    new_team = Team(
        dma_id=dma.id,
        name=team_data.name,
        description=team_data.description,
        status=team_data.status,
    )

    db.add(new_team)
    db.commit()
    db.refresh(new_team)

    return _build_team_with_details(new_team, db)


@teams_router.put("/{team_id}", response_model=TeamWithDetails)
async def update_team(
    team_id: str,
    team_data: TeamUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    _ensure_team_write_access(current_user, team.dma_id)

    update_data = team_data.dict(exclude_unset=True)

    if "dma_id" in update_data and update_data["dma_id"]:
        dma = db.query(DMA).filter(DMA.id == update_data["dma_id"]).first()
        if not dma:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="DMA not found",
            )
        _ensure_team_write_access(current_user, dma.id)
        team.dma_id = dma.id

    if "name" in update_data:
        team.name = update_data["name"]
    if "description" in update_data:
        team.description = update_data["description"]
    if "status" in update_data and update_data["status"] is not None:
        team.status = update_data["status"]

    db.commit()
    db.refresh(team)

    return _build_team_with_details(team, db)


@teams_router.patch("/{team_id}", response_model=TeamWithDetails)
async def patch_team(
    team_id: str,
    team_data: TeamUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await update_team(team_id, team_data, current_user, db)


@teams_router.get("/{team_id}/members")
async def get_team_members(
    team_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    _ensure_team_read_access(current_user, team, db)

    dma = db.query(DMA).filter(DMA.id == team.dma_id).first()
    leader_engineer = db.query(Engineer).filter(Engineer.id == team.leader_id).first() if team.leader_id else None

    leader = None
    if leader_engineer:
        leader = {
            "id": leader_engineer.id,
            "name": leader_engineer.name,
            "email": leader_engineer.email,
            "phone": leader_engineer.phone,
            "role": leader_engineer.role,
            "status": leader_engineer.status.value if hasattr(leader_engineer.status, "value") else leader_engineer.status,
        }

    members = db.query(Engineer).filter(Engineer.team_id == team_id).order_by(Engineer.name).all()
    eligible_query = db.query(Engineer).filter(
        Engineer.dma_id == team.dma_id,
        Engineer.status == EntityStatusEnum.ACTIVE,
        or_(Engineer.team_id == None, Engineer.team_id == team_id),
    ).order_by(Engineer.name)

    return {
        "team": {
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "dma_id": team.dma_id,
            "dma_name": dma.name if dma else None,
            "leader_id": team.leader_id,
            "leader": leader,
            "status": team.status.value if hasattr(team.status, "value") else team.status,
            "engineers": [
                {
                    "id": member.id,
                    "name": member.name,
                    "email": member.email,
                    "phone": member.phone,
                    "role": member.role,
                    "status": member.status.value if hasattr(member.status, "value") else member.status,
                    "team_id": member.team_id,
                }
                for member in members
            ],
            "created_at": team.created_at,
            "updated_at": team.updated_at,
        },
        "eligibleEngineers": [
            {
                "id": engineer.id,
                "name": engineer.name,
                "email": engineer.email,
                "phone": engineer.phone,
                "role": engineer.role,
                "status": engineer.status.value if hasattr(engineer.status, "value") else engineer.status,
                "team_id": engineer.team_id,
                "dma_id": engineer.dma_id,
            }
            for engineer in eligible_query.all()
        ],
        "currentMemberIds": [member.id for member in members],
    }


class AddMembersRequest(BaseModel):
    engineer_ids: List[str] = Field(alias="engineerIds")

    class Config:
        populate_by_name = True


@teams_router.post("/{team_id}/members", response_model=TeamWithDetails)
async def add_team_members(
    team_id: str,
    data: AddMembersRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not data.engineer_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Engineer IDs are required",
        )

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    _ensure_team_write_access(current_user, team.dma_id)

    engineers = db.query(Engineer).filter(Engineer.id.in_(data.engineer_ids)).all()
    if len(engineers) != len(data.engineer_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more engineers not found",
        )

    ineligible = []
    for engineer in engineers:
        if engineer.dma_id != team.dma_id or (engineer.team_id is not None and engineer.team_id != team_id):
            ineligible.append(engineer.name)

    if ineligible:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Engineers must be in the same DMA and not belong to another team. Ineligible: {', '.join(ineligible)}",
        )

    for engineer in engineers:
        engineer.team_id = team_id
        engineer.dma_id = team.dma_id

    db.commit()
    return _build_team_with_details(team, db)


@teams_router.delete("/{team_id}/members", response_model=TeamWithDetails)
async def remove_team_members(
    team_id: str,
    engineerIds: str = Query(..., alias="engineerIds", description="Comma-separated engineer IDs"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ids = engineerIds.split(",") if engineerIds else []
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Engineer IDs are required",
        )

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    _ensure_team_write_access(current_user, team.dma_id)

    for engineer_id in ids:
        if team.leader_id == engineer_id:
            team.leader_id = None
            db.query(Engineer).filter(Engineer.id == engineer_id).update(
                {"team_id": None, "role": "engineer"}
            )
        else:
            db.query(Engineer).filter(Engineer.id == engineer_id).update({"team_id": None})

    db.commit()
    return _build_team_with_details(team, db)


@teams_router.get("/{team_id}/leader")
async def get_team_leader(
    team_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    _ensure_team_read_access(current_user, team, db)

    leader_engineer = db.query(Engineer).filter(Engineer.id == team.leader_id).first() if team.leader_id else None
    leader = None
    if leader_engineer:
        leader = {
            "id": leader_engineer.id,
            "name": leader_engineer.name,
            "email": leader_engineer.email,
            "phone": leader_engineer.phone,
            "role": leader_engineer.role,
            "status": leader_engineer.status.value if hasattr(leader_engineer.status, "value") else leader_engineer.status,
        }

    eligible_query = db.query(Engineer).filter(
        Engineer.dma_id == team.dma_id,
        Engineer.status == EntityStatusEnum.ACTIVE,
        or_(Engineer.team_id == None, Engineer.team_id == team_id),
    ).order_by(Engineer.name)

    return {
        "leader": leader,
        "eligibleLeaders": [
            {
                "id": engineer.id,
                "name": engineer.name,
                "email": engineer.email,
                "phone": engineer.phone,
                "role": engineer.role,
                "status": engineer.status.value if hasattr(engineer.status, "value") else engineer.status,
                "team_id": engineer.team_id,
                "dma_id": engineer.dma_id,
            }
            for engineer in eligible_query.all()
        ],
        "team": {
            "id": team.id,
            "name": team.name,
            "dma_id": team.dma_id,
        },
    }


class AssignLeaderRequest(BaseModel):
    engineer_id: str = Field(alias="engineerId")

    class Config:
        populate_by_name = True


@teams_router.put("/{team_id}/leader", response_model=TeamWithDetails)
async def assign_team_leader(
    team_id: str,
    data: AssignLeaderRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not data.engineer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Engineer ID is required",
        )

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    _ensure_team_write_access(current_user, team.dma_id)

    engineer = db.query(Engineer).filter(Engineer.id == data.engineer_id).first()
    if not engineer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engineer not found",
        )

    if engineer.dma_id != team.dma_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Engineer must be from the same DMA as the team",
        )

    if engineer.status != EntityStatusEnum.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Engineer must be active",
        )

    if engineer.team_id and engineer.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Engineer is already a member of another team",
        )

    if team.leader_id and team.leader_id != data.engineer_id:
        db.query(Engineer).filter(Engineer.id == team.leader_id).update({"role": "engineer"})

    if not engineer.team_id:
        engineer.team_id = team_id
    engineer.role = "team_leader"
    engineer.dma_id = team.dma_id
    team.leader_id = data.engineer_id

    db.commit()
    return _build_team_with_details(team, db)


@teams_router.delete("/{team_id}/leader", response_model=TeamWithDetails)
async def remove_team_leader(
    team_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    _ensure_team_write_access(current_user, team.dma_id)

    if not team.leader_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No team leader assigned",
        )

    db.query(Engineer).filter(Engineer.id == team.leader_id).update({"role": "engineer"})
    team.leader_id = None
    db.commit()

    return _build_team_with_details(team, db)


@teams_router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    _ensure_team_write_access(current_user, team.dma_id)

    db.query(Engineer).filter(Engineer.team_id == team_id).update({"team_id": None})
    db.delete(team)
    db.commit()
