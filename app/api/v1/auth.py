"""
Authentication API routes.

Provides user registration, login, logout, and token validation.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import User
from app.schemas import TokenResponse, UserCreate, UserLogin, UserResponse
from app.utils.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    validate_email,
    validate_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user account.
    
    Args:
        user_data: Email, username, and password for new account.
        db: Database session.
        
    Returns:
        JWT access token for the new user.
        
    Raises:
        HTTPException 400: If email is invalid, password too weak, or email already exists.
    """
    # Validate email format
    if not validate_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Validate password strength
    is_valid, error_msg = validate_password(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already exists"
        )
    
    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    existing_username = result.scalar_one_or_none()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user with hashed password
    password_hash = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=password_hash,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    logger.info(f"New user registered: {user_data.email}")
    
    # Create access token
    access_token = create_access_token(data={"sub": str(new_user.id), "email": new_user.email})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(new_user.id)
    )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    
    Args:
        login_data: Email and password credentials.
        response: FastAPI response object for setting cookies.
        db: Database session.
        
    Returns:
        JWT access token for authenticated user.
        
    Raises:
        HTTPException 401: If credentials are invalid.
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"User logged in: {user.email}")
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    
    # Set httpOnly cookie for web clients
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # HTTPS only in production
        samesite="lax",
        max_age=86400 * 30,  # 30 days
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id)
    )


@router.post("/logout")
async def logout(response: Response):
    """
    Log out user by clearing the access token cookie.
    
    Args:
        response: FastAPI response object for clearing cookies.
        
    Returns:
        Success message.
    """
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
):
    """
    Get current authenticated user's information.
    
    Args:
        db: Database session.
        authorization: Bearer token from Authorization header.
        
    Returns:
        Current user's information.
        
    Raises:
        HTTPException 401: If not authenticated or token invalid.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )
