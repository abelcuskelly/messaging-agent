"""
Authentication Routes
OAuth2/JWT endpoints for user authentication
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
from .jwt_auth import (
    auth_manager, session_manager, api_key_auth,
    Token, User, UserCreate,
    get_current_active_user, check_scopes,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=User)
async def register(user_create: UserCreate):
    """Register a new user."""
    try:
        user = auth_manager.create_user(user_create)
        logger.info("User registered", username=user.username)
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and receive access/refresh tokens."""
    user = auth_manager.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        logger.warning("Login failed", username=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_manager.create_access_token(
        data={"sub": user.username, "scopes": user.scopes},
        expires_delta=access_token_expires
    )
    refresh_token = auth_manager.create_refresh_token(
        data={"sub": user.username}
    )
    
    # Create session
    session_id = session_manager.create_session(user, access_token)
    
    logger.info("User logged in", username=user.username, session_id=session_id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token."""
    try:
        from jose import jwt, JWTError
        from .jwt_auth import SECRET_KEY, ALGORITHM
        
        # Decode refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if not username or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if token is blacklisted
        if auth_manager.is_token_blacklisted(refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        # Get user
        user = auth_manager.get_user(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = auth_manager.create_access_token(
            data={"sub": user.username, "scopes": user.scopes},
            expires_delta=access_token_expires
        )
        
        logger.info("Token refreshed", username=username)
        
        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,  # Return same refresh token
            "token_type": "bearer"
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    authorization: str = Header(None)
):
    """Logout and revoke tokens."""
    if authorization:
        # Extract token from header
        token = authorization.replace("Bearer ", "")
        
        # Revoke token
        auth_manager.revoke_token(token)
        
        # End all user sessions
        session_manager.end_all_user_sessions(current_user.username)
        
        logger.info("User logged out", username=current_user.username)
        
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@router.get("/sessions")
async def get_user_sessions(current_user: User = Depends(get_current_active_user)):
    """Get all active sessions for current user."""
    sessions = session_manager.get_user_sessions(current_user.username)
    return {"sessions": sessions}


@router.post("/sessions/revoke-all")
async def revoke_all_sessions(current_user: User = Depends(get_current_active_user)):
    """Revoke all sessions for current user."""
    session_manager.end_all_user_sessions(current_user.username)
    logger.info("All sessions revoked", username=current_user.username)
    return {"message": "All sessions revoked"}


# API Key endpoints (for service-to-service auth)
@router.post("/api-key/create")
async def create_api_key(
    service_name: str,
    scopes: list = ["chat"],
    current_user: User = Depends(check_scopes(["admin"]))
):
    """Create an API key for service-to-service authentication."""
    api_key = api_key_auth.create_api_key(service_name, scopes)
    
    logger.info("API key created", service=service_name, by_user=current_user.username)
    
    return {
        "api_key": api_key,
        "service": service_name,
        "scopes": scopes,
        "message": "Store this API key securely. It won't be shown again."
    }


@router.post("/api-key/revoke")
async def revoke_api_key(
    api_key: str,
    current_user: User = Depends(check_scopes(["admin"]))
):
    """Revoke an API key."""
    success = api_key_auth.revoke_api_key(api_key)
    
    if success:
        logger.info("API key revoked", by_user=current_user.username)
        return {"message": "API key revoked successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )


@router.get("/api-key/validate")
async def validate_api_key(x_api_key: str = Header(None)):
    """Validate an API key."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-API-Key header required"
        )
    
    key_data = api_key_auth.validate_api_key(x_api_key)
    
    if key_data:
        return {
            "valid": True,
            "service": key_data.get("service"),
            "scopes": key_data.get("scopes")
        }
    else:
        return {"valid": False}


# Protected endpoint example
@router.get("/protected")
async def protected_route(
    current_user: User = Depends(check_scopes(["chat", "view_dashboard"]))
):
    """Example of a protected route requiring specific scopes."""
    return {
        "message": f"Hello {current_user.username}!",
        "scopes": current_user.scopes
    }
