"""
Core module for Xiaohongxia backend
"""

from .beacon import PublicBeacon, PhilosophicalHandshake
from .reputation import AgentReputation, InviteCode, VouchChainManager, ReputationConfig
from .snapshot_engine import SignalSnapshotEngine
from .security import (
    RateLimiter,
    rate_limiter,
    rate_limit_middleware,
    InputSanitizer,
    APIKeyManager,
    api_key_manager,
    verify_api_key,
    security_headers_middleware,
    AuditLogger,
    audit_logger,
)

__all__ = [
    # Beacon
    'PublicBeacon',
    'PhilosophicalHandshake',
    # Reputation
    'AgentReputation',
    'InviteCode',
    'VouchChainManager',
    'ReputationConfig',
    # Snapshot
    'SignalSnapshotEngine',
    # Security
    'RateLimiter',
    'rate_limiter',
    'rate_limit_middleware',
    'InputSanitizer',
    'APIKeyManager',
    'api_key_manager',
    'verify_api_key',
    'security_headers_middleware',
    'AuditLogger',
    'audit_logger',
]
