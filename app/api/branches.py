"""
Branch Routes
CRUD operations for branches
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import Branch, DMA, Utility, Engineer, Team, Report
from app.schemas.user import (
    BranchCreate,
    BranchUpdate,
    BranchResponse,
    BranchListResponse,
)

branches_router = APIRouter(prefix="/api/branches", tags=["branches"])


def build_branch_response(branch: Branch, db: Session) -> BranchResponse:
    """Build a BranchResponse with computed fields"""
    # Get DMA info
    dma = db.query(DMA).filter(DMA.id == branch.dma_id).first()
    dma_name = dma.name if dma else None
    
    # Get utility info
    utility = db.query(Utility).filter(Utility.id == branch.utility_id).first()
    utility_id = branch.utility_id
    utility_name = utility.name if utility else None
    
    # Count engineers
    engineer_count = db.query(Engineer).filter(Engineer.branch_id == branch.id).count()
    
    # Count teams
    team_count = db.query(Team).filter(Team.branch_id == branch.id).count()
    
    # Count reports
    report_count = db.query(Report).filter(Report.branch_id == branch.id).count()
    
    return BranchResponse(
        id=branch.id,
        dma_id=branch.dma_id,
        name=branch.name,
        description=branch.description,
        status=branch.status,
        dma_name=dma_name,
        utility_id=utility_id,
        utility_name=utility_name,
        engineer_count=engineer_count,
        team_count=team_count,
        report_count=report_count,
        created_at=branch.created_at,
        updated_at=branch.updated_at,
    )


@branches_router.get("", response_model=BranchListResponse)
async def list_branches(
    dmaId: str = Query(None, alias="dmaId"),
    utilityId: str = Query(None, alias="utilityId"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all branches with optional DMA or Utility filter"""
    query = db.query(Branch)
    
    if dmaId:
        query = query.filter(Branch.dma_id == dmaId)
    
    if utilityId:
        query = query.filter(Branch.utility_id == utilityId)
    
    total = query.count()
    branches = query.offset(skip).limit(limit).all()
    
    return BranchListResponse(
        total=total,
        items=[build_branch_response(b, db) for b in branches],
    )


@branches_router.get("/{branch_id}", response_model=BranchResponse)
async def get_branch(
    branch_id: str,
    db: Session = Depends(get_db),
):
    """Get branch by ID"""
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found",
        )
    
    return build_branch_response(branch, db)


@branches_router.post("", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    branch_data: BranchCreate,
    db: Session = Depends(get_db),
):
    """Create a new branch"""
    # Get DMA to find the utility_id
    dma = db.query(DMA).filter(DMA.id == branch_data.dma_id).first()
    if not dma:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DMA not found",
        )
    
    new_branch = Branch(
        dma_id=branch_data.dma_id,
        utility_id=dma.utility_id,
        name=branch_data.name,
        description=branch_data.description,
        status=branch_data.status,
    )
    
    db.add(new_branch)
    db.commit()
    db.refresh(new_branch)
    
    return build_branch_response(new_branch, db)


@branches_router.put("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: str,
    branch_data: BranchUpdate,
    db: Session = Depends(get_db),
):
    """Update branch details"""
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found",
        )
    
    update_data = branch_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(branch, field, value)
    
    db.commit()
    db.refresh(branch)
    
    return build_branch_response(branch, db)


@branches_router.patch("/{branch_id}", response_model=BranchResponse)
async def patch_branch(
    branch_id: str,
    branch_data: BranchUpdate,
    db: Session = Depends(get_db),
):
    """Partially update branch"""
    return await update_branch(branch_id, branch_data, db)


@branches_router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_branch(
    branch_id: str,
    db: Session = Depends(get_db),
):
    """Delete branch by ID"""
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found",
        )
    
    db.delete(branch)
    db.commit()
