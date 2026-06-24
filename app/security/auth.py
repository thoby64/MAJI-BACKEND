"""
Security utilities
Password hashing, JWT token generation/verification, and authentication helpers
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from bcrypt import hashpw, checkpw, gensalt
from app.config import settings


# ============================================================================
# Password Hashing
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt with 12 rounds of salt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    salt = gensalt(rounds=12)
    return hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify password against hashed password
    
    Args:
        password: Plain text password to verify
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


# ============================================================================
# JWT Token Management
# ============================================================================

class TokenPayload(dict):
    """JWT token payload structure"""
    def __init__(self, user_id: str, email: str, exp: datetime):
        super().__init__()
        self['user_id'] = user_id
        self['email'] = email
        self['exp'] = exp


def create_access_token(
    user_id: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token
    
    Args:
        user_id: User ID to encode in token
        email: User email to encode in token
        expires_delta: Optional custom expiration time
        
    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default: 24 hours
        expire = datetime.now(timezone.utc) + timedelta(hours=24)
    
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': expire,
        'type': 'access',
    }
    
    encoded_jwt = jwt.encode(
        payload,
        settings.secret_key,
        algorithm='HS256'
    )
    return encoded_jwt


def create_refresh_token(
    user_id: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token
    
    Args:
        user_id: User ID to encode in token
        email: User email to encode in token
        expires_delta: Optional custom expiration time
        
    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default: 7 days
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': expire,
        'type': 'refresh',
    }
    
    encoded_jwt = jwt.encode(
        payload,
        settings.secret_key,
        algorithm='HS256'
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token and return payload
    
    Args:
        token: JWT token string
        
    Returns:
        Token payload if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=['HS256']
        )
        return payload
    except JWTError:
        # Invalid token or expired
        return None
    except Exception:
        # Any other error
        return None


def create_token_pair(user_id: str, email: str) -> Dict[str, str]:
    """
    Create both access and refresh tokens
    
    Args:
        user_id: User ID
        email: User email
        
    Returns:
        Dictionary with 'access_token' and 'refresh_token'
    """
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id, email)
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer',
    }


def extract_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Extract user information from token
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary with user_id and email if valid, None otherwise
    """
    payload = verify_token(token)
    if not payload:
        return None
    
    return {
        'user_id': payload.get('user_id'),
        'email': payload.get('email'),
    }
