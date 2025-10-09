"""
OAuth2/JWT Authentication System
Secure authentication with JWT tokens and OAuth2 flow
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import redis
import json
import structlog

logger = structlog.get_logger()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Redis client for token blacklist and session management
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)


class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
    scopes: list = []


class User(BaseModel):
    """User model."""
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False
    scopes: list = []


class UserInDB(User):
    """User model with hashed password."""
    hashed_password: str


class UserCreate(BaseModel):
    """User registration model."""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class AuthManager:
    """Manage authentication and authorization."""
    
    def __init__(self):
        self.pwd_context = pwd_context
        self.redis_client = redis_client
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return self.pwd_context.hash(password)
    
    def get_user(self, username: str) -> Optional[UserInDB]:
        """Get user from database."""
        # In production, this would query your database
        # For now, using Redis as a simple store
        user_data = self.redis_client.get(f"user:{username}")
        if user_data:
            user_dict = json.loads(user_data)
            return UserInDB(**user_dict)
        return None
    
    def create_user(self, user_create: UserCreate) -> User:
        """Create a new user."""
        # Check if user exists
        if self.get_user(user_create.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Create user with hashed password
        hashed_password = self.get_password_hash(user_create.password)
        user_dict = {
            "username": user_create.username,
            "email": user_create.email,
            "full_name": user_create.full_name,
            "disabled": False,
            "scopes": ["chat", "view_dashboard"],  # Default scopes
            "hashed_password": hashed_password
        }
        
        # Store in Redis (in production, use proper database)
        self.redis_client.set(
            f"user:{user_create.username}",
            json.dumps(user_dict),
            ex=86400 * 30  # 30 days expiry
        )
        
        logger.info("User created", username=user_create.username)
        return User(**user_dict)
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user."""
        user = self.get_user(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        # Store token in Redis for tracking
        self.redis_client.set(
            f"token:access:{encoded_jwt[:20]}",
            json.dumps({"username": data.get("sub"), "exp": expire.isoformat()}),
            ex=int(expires_delta.total_seconds() if expires_delta else ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        )
        
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create a JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        # Store refresh token in Redis
        self.redis_client.set(
            f"token:refresh:{encoded_jwt[:20]}",
            json.dumps({"username": data.get("sub"), "exp": expire.isoformat()}),
            ex=86400 * REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        return encoded_jwt
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token by adding it to blacklist."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            exp = payload.get("exp")
            if exp:
                # Add to blacklist until expiry
                ttl = exp - datetime.utcnow().timestamp()
                if ttl > 0:
                    self.redis_client.set(f"blacklist:{token[:20]}", "1", ex=int(ttl))
                    logger.info("Token revoked", token_prefix=token[:20])
                    return True
        except JWTError:
            pass
        return False
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted."""
        return self.redis_client.exists(f"blacklist:{token[:20]}") > 0


# Global auth manager instance
auth_manager = AuthManager()


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check if token is blacklisted
    if auth_manager.is_token_blacklisted(token):
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None or token_type != "access":
            raise credentials_exception
        
        token_data = TokenData(username=username, scopes=payload.get("scopes", []))
        
    except JWTError:
        raise credentials_exception
    
    user = auth_manager.get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def check_scopes(required_scopes: list):
    """Check if user has required scopes."""
    async def scope_checker(current_user: User = Depends(get_current_active_user)):
        for scope in required_scopes:
            if scope not in current_user.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not enough permissions. Required scope: {scope}"
                )
        return current_user
    return scope_checker


# API Key authentication (for backwards compatibility)
class APIKeyAuth:
    """API Key authentication for service-to-service calls."""
    
    def __init__(self):
        self.api_keys = {}  # In production, store in database
    
    def create_api_key(self, service_name: str, scopes: list) -> str:
        """Create an API key for a service."""
        api_key = secrets.token_urlsafe(32)
        
        # Store API key
        self.api_keys[api_key] = {
            "service": service_name,
            "scopes": scopes,
            "created": datetime.utcnow().isoformat()
        }
        
        # Also store in Redis
        redis_client.set(
            f"api_key:{api_key[:10]}",
            json.dumps(self.api_keys[api_key]),
            ex=86400 * 365  # 1 year expiry
        )
        
        logger.info("API key created", service=service_name)
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key."""
        # Check in-memory first
        if api_key in self.api_keys:
            return self.api_keys[api_key]
        
        # Check Redis
        key_data = redis_client.get(f"api_key:{api_key[:10]}")
        if key_data:
            return json.loads(key_data)
        
        return None
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key in self.api_keys:
            del self.api_keys[api_key]
        
        redis_client.delete(f"api_key:{api_key[:10]}")
        logger.info("API key revoked", key_prefix=api_key[:10])
        return True


# Global API key auth instance
api_key_auth = APIKeyAuth()


# Session management
class SessionManager:
    """Manage user sessions."""
    
    def __init__(self):
        self.redis_client = redis_client
    
    def create_session(self, user: User, token: str) -> str:
        """Create a user session."""
        session_id = secrets.token_urlsafe(16)
        session_data = {
            "username": user.username,
            "token": token[:20],  # Store token prefix
            "created": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        # Store session
        self.redis_client.set(
            f"session:{session_id}",
            json.dumps(session_data),
            ex=3600  # 1 hour expiry
        )
        
        # Track user's active sessions
        self.redis_client.sadd(f"user_sessions:{user.username}", session_id)
        
        logger.info("Session created", username=user.username, session_id=session_id)
        return session_id
    
    def update_session_activity(self, session_id: str):
        """Update session last activity time."""
        session_data = self.redis_client.get(f"session:{session_id}")
        if session_data:
            data = json.loads(session_data)
            data["last_activity"] = datetime.utcnow().isoformat()
            self.redis_client.set(
                f"session:{session_id}",
                json.dumps(data),
                ex=3600  # Reset expiry
            )
    
    def end_session(self, session_id: str):
        """End a user session."""
        session_data = self.redis_client.get(f"session:{session_id}")
        if session_data:
            data = json.loads(session_data)
            username = data.get("username")
            
            # Remove session
            self.redis_client.delete(f"session:{session_id}")
            
            # Remove from user's sessions
            if username:
                self.redis_client.srem(f"user_sessions:{username}", session_id)
            
            logger.info("Session ended", session_id=session_id)
    
    def get_user_sessions(self, username: str) -> list:
        """Get all active sessions for a user."""
        session_ids = self.redis_client.smembers(f"user_sessions:{username}")
        sessions = []
        
        for session_id in session_ids:
            session_data = self.redis_client.get(f"session:{session_id}")
            if session_data:
                sessions.append(json.loads(session_data))
        
        return sessions
    
    def end_all_user_sessions(self, username: str):
        """End all sessions for a user."""
        session_ids = self.redis_client.smembers(f"user_sessions:{username}")
        
        for session_id in session_ids:
            self.end_session(session_id)
        
        logger.info("All user sessions ended", username=username)


# Global session manager instance
session_manager = SessionManager()
