"""
Security Dependencies
Reusable dependency functions for authentication and authorization
"""

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from app.database.session import get_db
from app.models import User
from app.models.user import UtilityManager, DMAManager, Engineer
from app.security.auth import extract_user_from_token


class CurrentUser(BaseModel):
    """Current user data from token"""
    id: str
    email: str
    user_type: str  # "user", "utility_manager", "dma_manager", "engineer"
    role: Optional[str] = None  # "engineer", "team_leader", etc.
    utility_id: Optional[str] = None
    dma_id: Optional[str] = None
    team_id: Optional[str] = None
    
    class Config:
        from_attributes = True


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """
    Get current user from Authorization header
    Works for all user types: User, UtilityManager, DMAManager, Engineer
    Extracts token from "Bearer <token>" format
    
    Args:
        authorization: Authorization header value
        db: Database session
        
    Returns:
        CurrentUser object with user_type and role info
        
    Raises:
        HTTPException: If token invalid or user not found
    """
    import logging
    logger = logging.getLogger("auth-debug")
    if not authorization:
        logger.error("Authorization header missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>" format
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authentication scheme")
    except ValueError:
        logger.error(f"Invalid authorization header format: {authorization}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user info from token
    user_info = extract_user_from_token(token)
    logger.info(f"Decoded token user_info: {user_info}")

    if not user_info:
        logger.error("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = user_info['user_id']
    email = user_info['email']

    # Check User table (admin)
    user = db.query(User).filter(User.id == user_id).first()
    logger.info(f"User table lookup for id={user_id}: {user}")
    if user:
        logger.info(f"Authenticated as user: {user.email}")
        return CurrentUser(
            id=user.id,
            email=user.email,
            user_type="user",
            role=None
        )

    # Check UtilityManager table
    util_mgr = db.query(UtilityManager).filter(UtilityManager.id == user_id).first()
    logger.info(f"UtilityManager table lookup for id={user_id}: {util_mgr}")
    if util_mgr:
        logger.info(f"Authenticated as utility_manager: {util_mgr.email}")
        return CurrentUser(
            id=util_mgr.id,
            email=util_mgr.email,
            user_type="utility_manager",
            role=None,
            utility_id=util_mgr.utility_id
        )
    
    # Check DMAManager table
    dma_mgr = db.query(DMAManager).filter(DMAManager.id == user_id).first()
    if dma_mgr:
        return CurrentUser(
            id=dma_mgr.id,
            email=dma_mgr.email,
            user_type="dma_manager",
            role=None,
            dma_id=dma_mgr.dma_id
        )
    
    # Check Engineer table
    engineer = db.query(Engineer).filter(Engineer.id == user_id).first()
    if engineer:
        return CurrentUser(
            id=engineer.id,
            email=engineer.email,
            user_type="engineer",
            role=engineer.role,
            dma_id=engineer.dma_id,
            team_id=engineer.team_id,
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not found",
    )


async def require_role(required_roles: List[str]):
    """
    Dependency to require specific role(s)
    
    Args:
        required_roles: List of allowed role/user_type values
        
    Returns:
        Dependency function
    """
    async def check_role(current_user: CurrentUser = Depends(get_current_user)):
        user_type = current_user.user_type
        # Map user_type to role
        if user_type == "user":
            user_role = "admin"
        else:
            user_role = user_type
        
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This operation requires one of these roles: {', '.join(required_roles)}",
            )
        return current_user
    
    return check_role


async def require_admin(current_user: CurrentUser = Depends(get_current_user)):
    """Require admin (User table) role"""
    if current_user.user_type != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_utility_manager(current_user: CurrentUser = Depends(get_current_user)):
    """Require utility manager role"""
    if current_user.user_type not in ["user", "utility_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utility manager access required",
        )
    return current_user
