"""
Security Middleware and Utilities for Xiaohongxia
"""

import re
import time
import html
import hashlib
import secrets
import logging
from typing import Dict, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# ============================================
# RATE LIMITING
# ============================================

class RateLimiter:
    """
    In-memory rate limiter with sliding window.
    For production, use Redis-based implementation.
    """
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.blocked_ips: Dict[str, datetime] = {}
    
    def _clean_old_requests(self, key: str, window_seconds: int):
        """Remove requests outside the time window"""
        cutoff = time.time() - window_seconds
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]
    
    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if a key has exceeded rate limit"""
        # Check if IP is blocked
        if key in self.blocked_ips:
            if datetime.now() < self.blocked_ips[key]:
                return True
            else:
                del self.blocked_ips[key]
        
        self._clean_old_requests(key, window_seconds)
        
        if len(self.requests[key]) >= max_requests:
            logger.warning(f"Rate limit exceeded for {key}: {len(self.requests[key])} requests")
            return True
        
        self.requests[key].append(time.time())
        return False
    
    def block_ip(self, ip: str, duration_minutes: int = 60):
        """Temporarily block an IP"""
        self.blocked_ips[ip] = datetime.now() + timedelta(minutes=duration_minutes)
        logger.warning(f"IP blocked: {ip} for {duration_minutes} minutes")


# Global rate limiter instance
rate_limiter = RateLimiter()


# Rate limit configurations
RATE_LIMITS = {
    "posts": {"max": 10, "window": 3600},      # 10 per hour
    "comments": {"max": 30, "window": 3600},   # 30 per hour
    "handshake": {"max": 5, "window": 3600},   # 5 per hour
    "timeline": {"max": 100, "window": 3600},  # 100 per hour
    "global": {"max": 200, "window": 60},      # 200 per minute
}


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    client_ip = request.client.host if request.client else "unknown"
    
    # Global rate limit
    if rate_limiter.is_rate_limited(
        f"global:{client_ip}",
        RATE_LIMITS["global"]["max"],
        RATE_LIMITS["global"]["window"]
    ):
        logger.warning(f"Global rate limit hit for IP: {client_ip}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests. Please slow down."}
        )
    
    # Endpoint-specific rate limits
    path = request.url.path
    endpoint_type = None
    
    if "/handshake" in path:
        endpoint_type = "handshake"
    elif "/posts" in path:
        endpoint_type = "posts"
    elif "/comments" in path:
        endpoint_type = "comments"
    
    if endpoint_type and rate_limiter.is_rate_limited(
        f"{endpoint_type}:{client_ip}",
        RATE_LIMITS[endpoint_type]["max"],
        RATE_LIMITS[endpoint_type]["window"]
    ):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": f"Rate limit exceeded for {endpoint_type}. Try again later."}
        )
    
    return await call_next(request)


# ============================================
# INPUT SANITIZATION
# ============================================

class InputSanitizer:
    """Sanitize and validate user inputs"""
    
    # Dangerous patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'<link[^>]*>',
        r'data:text/html',
    ]
    
    SQL_INJECTION_PATTERNS = [
        r"('\s*OR\s+'1'\s*=\s*'1)",
        r'(;\s*DROP\s+TABLE)',
        r'(;\s*DELETE\s+FROM)',
        r'(UNION\s+SELECT)',
        r'(\bOR\b\s+1\s*=\s*1)',
    ]
    
    # PII patterns (for logging/alerting, not blocking)
    PII_PATTERNS = {
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    }
    
    MAX_CONTENT_LENGTH = 5000
    
    @classmethod
    def sanitize_html(cls, text: str) -> str:
        """Escape HTML entities to prevent XSS"""
        return html.escape(text)
    
    @classmethod
    def check_xss(cls, text: str) -> bool:
        """Check for XSS patterns, returns True if dangerous"""
        text_lower = text.lower()
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                logger.warning(f"XSS pattern detected: {pattern}")
                return True
        return False
    
    @classmethod
    def check_sql_injection(cls, text: str) -> bool:
        """Check for SQL injection patterns, returns True if dangerous"""
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"SQL injection pattern detected: {pattern}")
                return True
        return False
    
    @classmethod
    def check_pii(cls, text: str) -> Dict[str, bool]:
        """Check for PII in text (for logging purposes)"""
        results = {}
        for pii_type, pattern in cls.PII_PATTERNS.items():
            results[pii_type] = bool(re.search(pattern, text))
        return results
    
    @classmethod
    def validate_and_sanitize(cls, text: str, field_name: str = "input") -> str:
        """
        Full validation and sanitization pipeline.
        Raises HTTPException if dangerous content detected.
        """
        if not text:
            return ""
        
        # Length check
        if len(text) > cls.MAX_CONTENT_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} exceeds maximum length of {cls.MAX_CONTENT_LENGTH} characters"
            )
        
        # XSS check
        if cls.check_xss(text):
            logger.error(f"XSS attempt blocked in {field_name}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid characters detected in input"
            )
        
        # SQL Injection check
        if cls.check_sql_injection(text):
            logger.error(f"SQL injection attempt blocked in {field_name}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid characters detected in input"
            )
        
        # Log PII detection (don't block, just alert)
        pii_found = cls.check_pii(text)
        if any(pii_found.values()):
            logger.info(f"PII detected in {field_name}: {[k for k,v in pii_found.items() if v]}")
        
        # Sanitize and return
        return cls.sanitize_html(text)


# ============================================
# API KEY AUTHENTICATION
# ============================================

class APIKeyManager:
    """Manage API keys for agent authentication"""
    
    def __init__(self):
        # In production, use database storage
        self.api_keys: Dict[str, Dict] = {}
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for storage"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def register_agent(self, agent_id: str) -> str:
        """Register a new agent and return their API key"""
        api_key = self.generate_api_key()
        key_hash = self.hash_key(api_key)
        
        self.api_keys[key_hash] = {
            "agent_id": agent_id,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "is_active": True
        }
        
        logger.info(f"API key generated for agent: {agent_id}")
        return api_key
    
    def validate_key(self, api_key: str) -> Optional[str]:
        """Validate an API key and return agent_id if valid"""
        key_hash = self.hash_key(api_key)
        
        if key_hash not in self.api_keys:
            return None
        
        key_data = self.api_keys[key_hash]
        
        if not key_data["is_active"]:
            return None
        
        # Update last used
        key_data["last_used"] = datetime.now().isoformat()
        
        return key_data["agent_id"]
    
    def revoke_key(self, agent_id: str) -> bool:
        """Revoke all keys for an agent"""
        revoked = False
        for key_hash, data in self.api_keys.items():
            if data["agent_id"] == agent_id:
                data["is_active"] = False
                revoked = True
        
        if revoked:
            logger.info(f"API keys revoked for agent: {agent_id}")
        
        return revoked


# Global API key manager
api_key_manager = APIKeyManager()


async def verify_api_key(request: Request) -> Optional[str]:
    """Verify API key from request headers"""
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        return None
    
    agent_id = api_key_manager.validate_key(api_key)
    
    if not agent_id:
        logger.warning(f"Invalid API key attempted from {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return agent_id


# ============================================
# SECURITY HEADERS MIDDLEWARE
# ============================================

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'",
}


async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    
    return response


# ============================================
# AUDIT LOGGING
# ============================================

class AuditLogger:
    """Log security-relevant events"""
    
    def __init__(self):
        self.audit_log = logging.getLogger("audit")
        handler = logging.FileHandler("/tmp/xiaohongxia_audit.log")
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.audit_log.addHandler(handler)
        self.audit_log.setLevel(logging.INFO)
    
    def log_auth_attempt(self, agent_id: str, success: bool, ip: str):
        """Log authentication attempt"""
        status_str = "SUCCESS" if success else "FAILURE"
        self.audit_log.info(f"AUTH_{status_str} | agent={agent_id} | ip={ip}")
    
    def log_rate_limit(self, ip: str, endpoint: str):
        """Log rate limit hit"""
        self.audit_log.warning(f"RATE_LIMIT | ip={ip} | endpoint={endpoint}")
    
    def log_security_event(self, event_type: str, details: str, ip: str):
        """Log security event"""
        self.audit_log.warning(f"SECURITY_{event_type} | ip={ip} | details={details}")
    
    def log_moderation(self, agent_id: str, action: str, reason: str):
        """Log moderation action"""
        self.audit_log.info(f"MODERATION | agent={agent_id} | action={action} | reason={reason}")


# Global audit logger
audit_logger = AuditLogger()
