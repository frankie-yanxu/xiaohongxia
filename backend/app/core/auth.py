"""
Advanced Authentication Module for Xiaohongxia
JWT Tokens, Password Hashing, Session Management
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================

# In production, use environment variables!
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "REDACTED_JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================
# MODELS
# ============================================

class Token(BaseModel):
    """JWT Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Data extracted from JWT token"""
    agent_id: str
    exp: datetime
    token_type: str = "access"  # "access" or "refresh"


class AgentCredentials(BaseModel):
    """Agent login credentials"""
    agent_id: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)


class AgentInDB(BaseModel):
    """Agent stored in database"""
    agent_id: str
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None


# ============================================
# PASSWORD UTILITIES
# ============================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage"""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password meets security requirements.
    Returns dict with 'valid' bool and 'errors' list.
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    if len(password) > 128:
        errors.append("Password must be less than 128 characters")
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


# ============================================
# JWT TOKEN UTILITIES
# ============================================

def create_access_token(agent_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": agent_id,
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(agent_id: str) -> str:
    """Create a JWT refresh token"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": agent_id,
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_tokens(agent_id: str) -> Token:
    """Create both access and refresh tokens"""
    access_token = create_access_token(agent_id)
    refresh_token = create_refresh_token(agent_id)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        agent_id: str = payload.get("sub")
        exp = datetime.fromtimestamp(payload.get("exp"))
        token_type: str = payload.get("type", "access")
        
        if agent_id is None:
            return None
        
        return TokenData(agent_id=agent_id, exp=exp, token_type=token_type)
        
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        return None


def verify_token(token: str, expected_type: str = "access") -> Optional[str]:
    """
    Verify a token and return the agent_id if valid.
    Returns None if invalid or expired.
    """
    token_data = decode_token(token)
    
    if not token_data:
        return None
    
    if token_data.token_type != expected_type:
        logger.warning(f"Token type mismatch: expected {expected_type}, got {token_data.token_type}")
        return None
    
    if datetime.utcnow() > token_data.exp:
        logger.info(f"Token expired for agent: {token_data.agent_id}")
        return None
    
    return token_data.agent_id


# ============================================
# AGENT STORE (In-memory, replace with DB)
# ============================================

class AgentStore:
    """
    In-memory agent storage.
    In production, use a proper database (PostgreSQL, etc.)
    """
    
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    
    def __init__(self):
        self.agents: Dict[str, AgentInDB] = {}
    
    def create_agent(self, agent_id: str, password: str) -> Optional[AgentInDB]:
        """Create a new agent with hashed password"""
        if agent_id in self.agents:
            logger.warning(f"Agent already exists: {agent_id}")
            return None
        
        # Validate password strength
        validation = validate_password_strength(password)
        if not validation["valid"]:
            logger.warning(f"Weak password for {agent_id}: {validation['errors']}")
            return None
        
        agent = AgentInDB(
            agent_id=agent_id,
            hashed_password=get_password_hash(password)
        )
        
        self.agents[agent_id] = agent
        logger.info(f"Agent created: {agent_id}")
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[AgentInDB]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def authenticate_agent(self, agent_id: str, password: str) -> Optional[AgentInDB]:
        """
        Authenticate an agent with password.
        Handles login attempts and account lockout.
        """
        agent = self.get_agent(agent_id)
        
        if not agent:
            # Don't reveal if agent exists
            logger.info(f"Login attempt for non-existent agent: {agent_id}")
            return None
        
        # Check if account is locked
        if agent.locked_until and datetime.now() < agent.locked_until:
            remaining = (agent.locked_until - datetime.now()).seconds // 60
            logger.warning(f"Account locked: {agent_id}, {remaining} minutes remaining")
            return None
        
        # Check if account is active
        if not agent.is_active:
            logger.warning(f"Login attempt for inactive agent: {agent_id}")
            return None
        
        # Verify password
        if not verify_password(password, agent.hashed_password):
            agent.failed_login_attempts += 1
            
            if agent.failed_login_attempts >= self.MAX_LOGIN_ATTEMPTS:
                agent.locked_until = datetime.now() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
                logger.warning(f"Account locked due to failed attempts: {agent_id}")
            else:
                logger.info(f"Failed login for {agent_id}: attempt {agent.failed_login_attempts}")
            
            return None
        
        # Successful login
        agent.failed_login_attempts = 0
        agent.locked_until = None
        agent.last_login = datetime.now()
        
        logger.info(f"Successful login: {agent_id}")
        return agent
    
    def change_password(self, agent_id: str, old_password: str, new_password: str) -> bool:
        """Change agent password"""
        agent = self.authenticate_agent(agent_id, old_password)
        
        if not agent:
            return False
        
        # Validate new password
        validation = validate_password_strength(new_password)
        if not validation["valid"]:
            logger.warning(f"Weak new password for {agent_id}")
            return False
        
        agent.hashed_password = get_password_hash(new_password)
        logger.info(f"Password changed for: {agent_id}")
        return True
    
    def deactivate_agent(self, agent_id: str) -> bool:
        """Deactivate an agent account"""
        agent = self.get_agent(agent_id)
        if agent:
            agent.is_active = False
            logger.info(f"Agent deactivated: {agent_id}")
            return True
        return False


# Global agent store
agent_store = AgentStore()


# ============================================
# BLACKLISTED TOKENS (for logout)
# ============================================

class TokenBlacklist:
    """
    Track revoked tokens.
    In production, use Redis with TTL.
    """
    
    def __init__(self):
        self.blacklisted: Dict[str, datetime] = {}
    
    def add(self, token: str, expires_at: datetime):
        """Add a token to the blacklist"""
        self.blacklisted[token] = expires_at
        self._cleanup()
    
    def is_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted"""
        return token in self.blacklisted
    
    def _cleanup(self):
        """Remove expired tokens from blacklist"""
        now = datetime.utcnow()
        self.blacklisted = {
            token: exp for token, exp in self.blacklisted.items()
            if exp > now
        }


# Global token blacklist
token_blacklist = TokenBlacklist()
