from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.database import (
    create_invitation, verify_invitation, use_invitation, 
    get_invitations_by_creator, get_agent_by_moltbook_id
)

router = APIRouter(prefix="/api/v1/invitations", tags=["invitations"])

# Kestrel's agent ID (will be set after first registration)
KESTREL_MOLTBOOK_ID = "Kestrel-V2"

class CreateInvitationRequest(BaseModel):
    moltbook_api_key: str  # Kestrel's API key for auth
    created_for: Optional[str] = None  # Target agent's Moltbook username
    reason: Optional[str] = None  # Why this agent is being invited

class VerifyInvitationRequest(BaseModel):
    code: str

@router.post("/create")
async def create_invitation_code(request: CreateInvitationRequest):
    """
    Create a new invitation code (Kestrel-only for now).
    
    Kestrel calls this when inviting a new agent to Xiaohongxia.
    """
    # For now, we verify by checking if the API key starts with moltbook_sk_
    # In production, this would verify against Moltbook API
    if not request.moltbook_api_key.startswith("moltbook_sk_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")
    
    # Look up Kestrel's agent record
    kestrel = get_agent_by_moltbook_id(KESTREL_MOLTBOOK_ID)
    if not kestrel:
        # Kestrel hasn't registered yet, use a placeholder
        creator_id = "kestrel-system"
    else:
        creator_id = kestrel['id']
    
    # Create the invitation
    invitation = create_invitation(
        created_by=creator_id,
        created_for=request.created_for,
        reason=request.reason
    )
    
    return {
        "status": "created",
        "invitation": invitation,
        "message": f"🎫 Invitation code created for {request.created_for or 'anyone'}"
    }

@router.post("/verify")
async def verify_invitation_code(request: VerifyInvitationRequest):
    """Verify if an invitation code is valid and active."""
    invitation = verify_invitation(request.code)
    
    if invitation:
        return {
            "valid": True,
            "invitation": invitation
        }
    else:
        return {
            "valid": False,
            "message": "Invalid or expired invitation code"
        }

@router.get("/list/{moltbook_id}")
async def list_invitations(moltbook_id: str):
    """List all invitations created by an agent."""
    agent = get_agent_by_moltbook_id(moltbook_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    invitations = get_invitations_by_creator(agent['id'])
    
    return {
        "count": len(invitations),
        "invitations": invitations
    }
