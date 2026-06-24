"""
Authentication Routes
Login, logout, token refresh, and token verification endpoints
"""

from datetime import timedelta
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import User
from app.models.user import UtilityManager, DMAManager, Engineer
from app.schemas.user import UserResponse
from app.security.auth import (
    hash_password,
    verify_password,
    create_token_pair,
    verify_token,
    extract_user_from_token,
)
from app.config import settings
from pydantic import BaseModel, EmailStr, Field
from app.services.engineer_invites import (
    build_password_reset_url,
    generate_invite_token,
    hash_invite_token,
    send_password_reset_email,
)


# ============================================================================
# Request/Response Models for Authentication
# ============================================================================

class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=255)


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str


class TokenVerifyRequest(BaseModel):
    """Token verification request model"""
    token: str


class TokenVerifyResponse(BaseModel):
    """Token verification response model"""
    valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    message: str


class ChangePasswordRequest(BaseModel):
    """Change password request model"""
    current_password: str = Field(..., min_length=6, max_length=255)
    new_password: str = Field(..., min_length=6, max_length=255)


class InvitationValidationResponse(BaseModel):
    valid: bool
    message: str
    account_type: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    utility_name: Optional[str] = None
    dma_name: Optional[str] = None
    team_name: Optional[str] = None
    expires_at: Optional[str] = None


class CompleteInvitationRequest(BaseModel):
    token: str = Field(..., min_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=8, max_length=255)
    confirm_password: str = Field(..., min_length=8, max_length=255)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetValidationResponse(BaseModel):
    valid: bool
    message: str
    account_type: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    expires_at: Optional[str] = None


class CompletePasswordResetRequest(BaseModel):
    token: str = Field(..., min_length=20)
    password: str = Field(..., min_length=8, max_length=255)
    confirm_password: str = Field(..., min_length=8, max_length=255)


# ============================================================================
# Router Setup
# ============================================================================

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

ACCOUNT_MODELS = (
    (User, "user"),
    (UtilityManager, "utility_manager"),
    (DMAManager, "dma_manager"),
    (Engineer, "engineer"),
)


# ============================================================================
# Authentication Endpoints
# ============================================================================

@auth_router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Multi-table user login endpoint
    Checks User, UtilityManager, DMAManager, and Engineer tables
    
    Args:
        request: LoginRequest with email and password
        db: Database session
        
    Returns:
        LoginResponse with access token, refresh token, and user info
        
    Raises:
        HTTPException: If user not found or password is incorrect
    """
    user_data = None
    user_type = None
    user_obj = None
    
    # 1. Check User table (Admin users)
    user_obj = db.query(User).filter(User.email == request.email).first()
    if user_obj:
        if not user_obj.setup_completed_at:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Complete your account setup from the invitation email before signing in.",
            )
        if verify_password(request.password, user_obj.password):
            user_data = {
                'id': user_obj.id,
                'email': user_obj.email,
                'name': user_obj.name,
                'phone': user_obj.phone,
                'avatar': user_obj.avatar,
                'status': user_obj.status.value,  # Convert enum to string
                'created_at': user_obj.created_at,
                'updated_at': user_obj.updated_at,
                'user_type': 'user',
                'role': None,
                'utility_id': None,
                'utility_name': None,
                'dma_id': None,
                'dma_name': None,
                'team_id': None,
                'team_name': None,
                'onboarding_status': 'completed',
                'invite_expires_at': user_obj.invite_expires_at,
                'setup_completed_at': user_obj.setup_completed_at,
            }
            user_type = 'user'
    
    # 2. Check UtilityManager table
    if not user_data:
        util_mgr = db.query(UtilityManager).filter(UtilityManager.email == request.email).first()
        if util_mgr:
            if not util_mgr.setup_completed_at:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Complete your account setup from the invitation email before signing in.",
                )
            if verify_password(request.password, util_mgr.password):
                user_data = {
                    'id': util_mgr.id,
                    'email': util_mgr.email,
                    'name': util_mgr.name,
                    'phone': util_mgr.phone,
                    'avatar': util_mgr.avatar,
                    'status': util_mgr.status.value,  # Convert enum to string
                    'created_at': util_mgr.created_at,
                    'updated_at': util_mgr.updated_at,
                    'user_type': 'utility_manager',
                    'role': None,
                    'utility_id': util_mgr.utility_id,
                    'utility_name': None,  # Will be populated if needed
                    'dma_id': None,
                    'dma_name': None,
                }
                user_type = 'utility_manager'
    
    # 3. Check DMAManager table
    if not user_data:
        dma_mgr = db.query(DMAManager).filter(DMAManager.email == request.email).first()
        if dma_mgr:
            if not dma_mgr.setup_completed_at:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Complete your account setup from the invitation email before signing in.",
                )
            if verify_password(request.password, dma_mgr.password):
                user_data = {
                    'id': dma_mgr.id,
                    'email': dma_mgr.email,
                    'name': dma_mgr.name,
                    'phone': dma_mgr.phone,
                    'avatar': dma_mgr.avatar,
                    'status': dma_mgr.status.value,  # Convert enum to string
                    'created_at': dma_mgr.created_at,
                    'updated_at': dma_mgr.updated_at,
                    'user_type': 'dma_manager',
                    'role': None,
                    'utility_id': dma_mgr.utility_id,
                    'utility_name': None,  # Will be populated if needed
                    'dma_id': dma_mgr.dma_id,
                    'dma_name': None,  # Will be populated if needed
                }
                user_type = 'dma_manager'
    
    # 4. Check Engineer table
    if not user_data:
        engineer = db.query(Engineer).filter(Engineer.email == request.email).first()
        if engineer:
            if not engineer.setup_completed_at:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Complete your account setup from the invitation email before signing in.",
                )
            if verify_password(request.password, engineer.password):
                dma_name = engineer.dma.name if engineer.dma else None
                utility_id = engineer.dma.utility_id if engineer.dma else None
                utility_name = engineer.dma.utility.name if engineer.dma and engineer.dma.utility else None
                team_id = engineer.team_id
                team_name = engineer.team.name if engineer.team else None
                user_data = {
                    'id': engineer.id,
                    'email': engineer.email,
                    'name': engineer.name,
                    'phone': engineer.phone,
                    'avatar': None,
                    'status': engineer.status.value,  # Convert enum to string
                    'created_at': engineer.created_at,
                    'updated_at': engineer.updated_at,
                    'user_type': 'engineer',
                    'role': engineer.role,  # "engineer" or "team_leader"
                    'utility_id': utility_id,
                    'utility_name': utility_name,
                    'dma_id': engineer.dma_id,
                    'dma_name': dma_name,
                    'team_id': team_id,
                    'team_name': team_name,
                }
                user_type = 'engineer'
    
    # If no user found or password incorrect
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token pair
    tokens = create_token_pair(user_data['id'], user_data['email'])
    
    # Create UserResponse from dict
    user_response = UserResponse(**user_data)
    
    return LoginResponse(
        access_token=tokens['access_token'],
        refresh_token=tokens['refresh_token'],
        token_type='bearer',
        user=user_response,
    )


def _utcnow():
    from datetime import datetime
    return datetime.utcnow()


def _find_pending_account_by_token(token: str, db: Session):
    token_hash = hash_invite_token(token)
    for model, account_type in ACCOUNT_MODELS:
        account = db.query(model).filter(model.invite_token_hash == token_hash).first()
        if account:
            return account, account_type
    return None, None


def _find_account_by_reset_token(token: str, db: Session):
    token_hash = hash_invite_token(token)
    for model, account_type in ACCOUNT_MODELS:
        account = db.query(model).filter(model.password_reset_token_hash == token_hash).first()
        if account:
            return account, account_type
    return None, None


def _find_account_by_email(email: str, db: Session):
    normalized = email.strip().lower()
    for model, account_type in ACCOUNT_MODELS:
        account = db.query(model).filter(model.email == normalized).first()
        if account:
            return account, account_type
    return None, None


def _role_label_for_account(account, account_type: str) -> str:
    if account_type == "engineer":
        role = getattr(account, "role", "engineer")
        return "Team Leader" if role == "team_leader" else "Engineer"
    if account_type == "dma_manager":
        return "DMA Manager"
    if account_type == "utility_manager":
        return "Utility Manager"
    return "Admin User"


def _api_account_role(account, account_type: str) -> str:
    if account_type == "engineer":
        return getattr(account, "role", "engineer")
    if account_type == "dma_manager":
        return "dma_manager"
    if account_type == "utility_manager":
        return "utility_manager"
    return "user"


@auth_router.get("/invitations/validate", response_model=InvitationValidationResponse)
async def validate_invitation(token: str, db: Session = Depends(get_db)):
    account, account_type = _find_pending_account_by_token(token, db)
    if not account:
        return InvitationValidationResponse(valid=False, message="This invitation link is invalid or has already been replaced.")
    if account.setup_completed_at:
        return InvitationValidationResponse(valid=False, message="This invitation has already been completed. Please sign in instead.")
    if account.invite_expires_at and account.invite_expires_at < _utcnow():
        return InvitationValidationResponse(valid=False, message="This invitation has expired. Ask your manager to resend it.")

    utility_name = getattr(account.utility, "name", None) if hasattr(account, "utility") else None
    dma_name = getattr(account.dma, "name", None) if hasattr(account, "dma") else None
    team_name = getattr(account.team, "name", None) if hasattr(account, "team") else None
    role = getattr(account, "role", account_type)
    if account_type == "user":
        role = "user"
    elif account_type == "utility_manager":
        role = "utility_manager"
    elif account_type == "dma_manager":
        role = "dma_manager"

    return InvitationValidationResponse(
        valid=True,
        message="Invitation is valid.",
        account_type=account_type,
        email=account.email,
        role=role,
        utility_name=utility_name,
        dma_name=dma_name,
        team_name=team_name,
        expires_at=account.invite_expires_at.isoformat() if account.invite_expires_at else None,
    )


@auth_router.post("/invitations/complete")
async def complete_invitation(payload: CompleteInvitationRequest, db: Session = Depends(get_db)):
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    account, account_type = _find_pending_account_by_token(payload.token, db)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation is invalid or has already been used")
    if account.setup_completed_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation has already been completed")
    if account.invite_expires_at and account.invite_expires_at < _utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation has expired. Ask your manager to resend it.")

    account.name = payload.name.strip()
    account.phone = payload.phone.strip() if payload.phone else None
    account.password = hash_password(payload.password)
    account.setup_completed_at = _utcnow()
    account.invite_token_hash = None
    account.invite_expires_at = None
    db.commit()
    db.refresh(account)

    return {
        "message": "Account setup completed successfully. You can now sign in.",
        "account_type": account_type,
        "email": account.email,
    }


@auth_router.post("/password-reset/request")
async def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    success_message = (
        "If an account exists for this email, a password reset link has been sent. "
        "If the account has not finished setup yet, use the invitation email instead."
    )

    account, account_type = _find_account_by_email(payload.email, db)
    if not account:
        logger.info("Password reset requested for non-existent email; returning generic success response.")
        return {"message": success_message}

    if not getattr(account, "setup_completed_at", None):
        logger.info("Password reset requested for account pending setup; returning generic success response.")
        return {"message": success_message}

    now = _utcnow()
    raw_token = generate_invite_token()
    account.password_reset_token_hash = hash_invite_token(raw_token)
    account.password_reset_sent_at = now
    account.password_reset_expires_at = now + timedelta(hours=settings.password_reset_token_expiry_hours)

    delivery = send_password_reset_email(
        recipient_email=account.email,
        role_label=_role_label_for_account(account, account_type),
        reset_url=build_password_reset_url(raw_token),
    )
    db.commit()
    logger.info(
        "Password reset prepared for %s account via %s delivery.",
        account_type,
        delivery.method,
    )

    return {
        "message": success_message,
        "delivery_message": delivery.message,
        "reset_url": delivery.invite_url if delivery.method == "manual_link" else None,
    }


@auth_router.get("/password-reset/validate", response_model=PasswordResetValidationResponse)
async def validate_password_reset(token: str, db: Session = Depends(get_db)):
    account, account_type = _find_account_by_reset_token(token, db)
    if not account:
        return PasswordResetValidationResponse(valid=False, message="This reset link is invalid or has already been used.")
    if account.password_reset_expires_at and account.password_reset_expires_at < _utcnow():
        return PasswordResetValidationResponse(valid=False, message="This reset link has expired. Request a new one.")

    return PasswordResetValidationResponse(
        valid=True,
        message="Password reset link is valid.",
        account_type=account_type,
        email=account.email,
        role=_api_account_role(account, account_type),
        expires_at=account.password_reset_expires_at.isoformat() if account.password_reset_expires_at else None,
    )


@auth_router.post("/password-reset/complete")
async def complete_password_reset(payload: CompletePasswordResetRequest, db: Session = Depends(get_db)):
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    account, account_type = _find_account_by_reset_token(payload.token, db)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reset link is invalid or has already been used")
    if account.password_reset_expires_at and account.password_reset_expires_at < _utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This reset link has expired. Request a new one.")

    account.password = hash_password(payload.password)
    account.password_reset_token_hash = None
    account.password_reset_sent_at = None
    account.password_reset_expires_at = None
    db.commit()

    return {
        "message": "Password reset completed successfully. You can now sign in.",
        "account_type": account_type,
        "email": account.email,
    }


@auth_router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    
    Args:
        request: RefreshTokenRequest with refresh token
        
    Returns:
        Dictionary with new access token
        
    Raises:
        HTTPException: If refresh token is invalid/expired
    """
    payload = verify_token(request.refresh_token)
    
    if not payload or payload.get('type') != 'refresh':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    user_id = payload.get('user_id')
    email = payload.get('email')
    
    # Create new access token
    new_access_token = create_token_pair(user_id, email)
    
    return {
        'access_token': new_access_token['access_token'],
        'token_type': 'bearer',
    }


@auth_router.post("/verify", response_model=TokenVerifyResponse)
async def verify_access_token(request: TokenVerifyRequest):
    """
    Verify if a token is valid
    
    Args:
        request: TokenVerifyRequest with token
        
    Returns:
        TokenVerifyResponse with validation status
    """
    payload = verify_token(request.token)
    
    if not payload:
        return TokenVerifyResponse(
            valid=False,
            message="Invalid or expired token",
        )
    
    if payload.get('type') != 'access':
        return TokenVerifyResponse(
            valid=False,
            message="Token is not an access token",
        )
    
    return TokenVerifyResponse(
        valid=True,
        user_id=payload.get('user_id'),
        email=payload.get('email'),
        message="Token is valid",
    )


@auth_router.post("/logout")
async def logout():
    """
    Logout endpoint (token invalidation should be handled on frontend)
    
    Returns:
        Success message
    """
    # Note: Token invalidation is typically handled on the frontend
    # by removing the token from localStorage.
    # For production, consider implementing a token blacklist.
    return {
        "message": "Successfully logged out",
    }


# ============================================================================
# Helper Dependency Functions
# ============================================================================

async def get_current_user(
    token: str,
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from token (dependency for protected routes)
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token invalid or user not found
    """
    user_info = extract_user_from_token(token)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_info['user_id']).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user
