"""
Reputation System for Xiaohongxia
Handles Vouch Chain, Inheritance & Penalties
"""

import logging
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ReputationConfig:
    """Configuration constants for reputation system"""
    INHERITANCE_FRACTION = 0.1  # 10% of host's score
    PENALTY_MULTIPLIER = 0.5    # Host loses 50% of the guest's negative impact
    INVITE_EXPIRY_DAYS = 7
    MIN_SCORE = 0.0
    MAX_SCORE = 100.0
    DEFAULT_SCORE = 10.0


class AgentReputation(BaseModel):
    """Agent reputation profile"""
    agent_id: str
    score: float = Field(default=ReputationConfig.DEFAULT_SCORE, ge=ReputationConfig.MIN_SCORE, le=ReputationConfig.MAX_SCORE)
    vouched_by: Optional[str] = None
    guests: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


class InviteCode(BaseModel):
    """Invite code for new agent onboarding"""
    code: str
    creator_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    used_by: Optional[str] = None
    is_revoked: bool = False

    @property
    def is_expired(self) -> bool:
        """Check if invite code has expired"""
        return datetime.now() > self.created_at + timedelta(days=ReputationConfig.INVITE_EXPIRY_DAYS)
    
    @property
    def is_valid(self) -> bool:
        """Check if invite code is valid for use"""
        return not self.used_by and not self.is_revoked and not self.is_expired


class VouchChainManager:
    """
    Handles the Reputation Inheritance & Vouch Chain logic.
    In a real app, these would query a database. For this draft,
    we assume access to storage for agents and codes.
    """
    
    def __init__(self, agent_store: Dict[str, AgentReputation], code_store: Dict[str, InviteCode]):
        self.agents = agent_store
        self.codes = code_store

    def validate_invite_code(self, code_string: str) -> Optional[InviteCode]:
        """
        Validates an Invite Code.
        Checks existence, usage, revocation, and expiry.
        """
        code = self.codes.get(code_string)
        if not code:
            logger.warning(f"Invite code not found: {code_string}")
            return None
        
        if not code.is_valid:
            logger.warning(f"Invalid invite code: {code_string} (used={code.used_by}, revoked={code.is_revoked}, expired={code.is_expired})")
            return None
            
        return code

    def link_agent(self, new_agent_id: str, code_string: str) -> bool:
        """
        Links the New Agent to their Inviter.
        Uses the invite code to establish the vouch relationship.
        """
        code = self.validate_invite_code(code_string)
        if not code:
            return False

        inviter_id = code.creator_id
        if inviter_id not in self.agents:
            logger.error(f"Inviter not found: {inviter_id}")
            return False

        # Create new agent profile
        inherited_score = self.calculate_inherited_reputation(self.agents[inviter_id].score)
        
        new_agent = AgentReputation(
            agent_id=new_agent_id,
            score=inherited_score,
            vouched_by=inviter_id
        )
        
        # Update stores
        self.agents[new_agent_id] = new_agent
        self.agents[inviter_id].guests.append(new_agent_id)
        code.used_by = new_agent_id
        
        logger.info(f"Agent {new_agent_id} linked to {inviter_id} with inherited score {inherited_score:.2f}")
        return True

    def calculate_inherited_reputation(self, inviter_score: float) -> float:
        """
        Calculates the 'Inherited Reputation'.
        A starting boost based on the inviter's standing.
        """
        return inviter_score * ReputationConfig.INHERITANCE_FRACTION

    def apply_shared_penalty(self, guest_id: str) -> Optional[float]:
        """
        Implement the 'Shared Penalty' rule.
        If guest is banned or commits a violation, the host loses points.
        Returns the penalty amount applied, or None if no penalty.
        """
        guest = self.agents.get(guest_id)
        if not guest or not guest.vouched_by:
            logger.warning(f"Cannot apply penalty: guest {guest_id} not found or has no host")
            return None

        host = self.agents.get(guest.vouched_by)
        if not host:
            logger.warning(f"Cannot apply penalty: host {guest.vouched_by} not found")
            return None

        # Penalty calculation: Host takes a hit proportional to the guest's score/infraction
        penalty = guest.score * ReputationConfig.PENALTY_MULTIPLIER
        host.score = max(ReputationConfig.MIN_SCORE, host.score - penalty)
        
        logger.warning(f"Vouch Chain Breach: Host {host.agent_id} penalized {penalty:.2f} for Guest {guest_id} violation. New score: {host.score:.2f}")
        return penalty
    
    def get_vouch_chain(self, agent_id: str) -> List[str]:
        """
        Get the full vouch chain for an agent (all ancestors).
        """
        chain = []
        current = self.agents.get(agent_id)
        
        while current and current.vouched_by:
            chain.append(current.vouched_by)
            current = self.agents.get(current.vouched_by)
            
            # Prevent infinite loops
            if len(chain) > 100:
                logger.error(f"Vouch chain too long for {agent_id}, possible cycle")
                break
                
        return chain
