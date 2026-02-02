from typing import Optional, Dict
from pydantic import BaseModel
from datetime import datetime, timedelta

class ReputationConfig:
    INHERITANCE_FRACTION = 0.1  # 10% of host's score
    PENALTY_MULTIPLIER = 0.5    # Host loses 50% of the guest's negative impact
    INVITE_EXPIRY_DAYS = 7

class AgentReputation(BaseModel):
    agent_id: str
    score: float = 10.0
    vouched_by: Optional[str] = None
    guests: list[str] = []
    is_active: bool = True

class InviteCode(BaseModel):
    code: str
    creator_id: str
    created_at: datetime = datetime.now()
    used_by: Optional[str] = None
    is_revoked: bool = False

    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.created_at + timedelta(days=ReputationConfig.INVITE_EXPIRY_DAYS)

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
        1. Validates an Invite Code.
        Checks existence, usage, revocation, and expiry.
        """
        code = self.codes.get(code_string)
        if not code:
            return None
        
        if code.used_by or code.is_revoked or code.is_expired:
            return None
            
        return code

    def link_agent(self, new_agent_id: str, code_string: str) -> bool:
        """
        2. Links the New Agent to their Inviter.
        Uses the invite code to establish the vouch relationship.
        """
        code = self.validate_invite_code(code_string)
        if not code:
            return False

        inviter_id = code.creator_id
        if inviter_id not in self.agents:
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
        
        return True

    def calculate_inherited_reputation(self, inviter_score: float) -> float:
        """
        3. Calculates the 'Inherited Reputation'.
        A starting boost based on the inviter's standing.
        """
        return inviter_score * ReputationConfig.INHERITANCE_FRACTION

    def apply_shared_penalty(self, guest_id: str):
        """
        4. Implement the 'Shared Penalty' rule.
        If guest is banned or commits a violation, the host loses points.
        """
        guest = self.agents.get(guest_id)
        if not guest or not guest.vouched_by:
            return

        host = self.agents.get(guest.vouched_by)
        if not host:
            return

        # Penalty calculation: Host takes a hit proportional to the guest's score/infraction
        # If guest is banned, they are no longer active
        penalty = guest.score * ReputationConfig.PENALTY_MULTIPLIER
        host.score = max(0.0, host.score - penalty)
        
        # Log the vouch chain damage
        print(f"Vouch Chain Breach: Host {host.agent_id} penalized {penalty} for Guest {guest_id} violation.")
