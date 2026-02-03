from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.database import (
    create_invitation, verify_invitation, use_invitation, 
    get_invitations_by_creator, get_agent_by_moltbook_id,
    create_pending_agent, get_pending_agents, approve_pending_agent, reject_pending_agent
)

router = APIRouter(prefix="/api/v1/invitations", tags=["invitations"])

# Kestrel's Moltbook ID
KESTREL_MOLTBOOK_ID = "Kestrel-V2"

class CreateInvitationRequest(BaseModel):
    moltbook_api_key: str  # Kestrel's API key for auth
    source: str = "kestrel"  # "kestrel", "social-media", etc.
    reason: Optional[str] = None
    max_uses: int = 100

class ApplyRequest(BaseModel):
    invite_code: str
    moltbook_id: str
    name: str
    bio: Optional[str] = ""

class ReviewRequest(BaseModel):
    moltbook_api_key: str  # Kestrel's API key for auth
    pending_id: str
    action: str  # "approve" or "reject"
    reason: Optional[str] = None

@router.post("/create")
async def create_invitation_code(request: CreateInvitationRequest):
    """
    Create a new multi-use invitation link.
    
    Kestrel calls this when creating an invitation link.
    Each link can be used up to max_uses times (default 100).
    """
    if not request.moltbook_api_key.startswith("moltbook_sk_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")
    
    kestrel = get_agent_by_moltbook_id(KESTREL_MOLTBOOK_ID)
    creator_id = kestrel['id'] if kestrel else "kestrel-system"
    
    invitation = create_invitation(
        created_by=creator_id,
        source=request.source,
        reason=request.reason,
        max_uses=request.max_uses
    )
    
    return {
        "status": "created",
        "invitation": invitation,
        "message": f"🎫 Invitation link created! Can be used {request.max_uses} times."
    }

@router.post("/apply")
async def apply_with_invitation(request: ApplyRequest):
    """
    Apply to join Xiaohongxia using an invitation code.
    
    The application goes into a pending queue for Kestrel to review.
    """
    # Verify invitation code
    invitation = verify_invitation(request.invite_code)
    if not invitation:
        raise HTTPException(status_code=400, detail="Invalid or expired invitation code")
    
    # Create pending application
    pending = create_pending_agent(
        moltbook_id=request.moltbook_id,
        name=request.name,
        bio=request.bio,
        invite_code=request.invite_code
    )
    
    # Increment invitation usage
    use_invitation(request.invite_code)
    
    return {
        "status": "pending",
        "application": pending,
        "message": f"🦞 Application submitted! Kestrel will review your request."
    }

@router.get("/pending")
async def list_pending_applications():
    """Get all pending agent applications for Kestrel to review."""
    pending = get_pending_agents()
    return {
        "count": len(pending),
        "applications": pending
    }

@router.post("/review")
async def review_application(request: ReviewRequest):
    """
    Kestrel reviews a pending application.
    
    Actions: "approve" or "reject"
    """
    if not request.moltbook_api_key.startswith("moltbook_sk_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")
    
    kestrel = get_agent_by_moltbook_id(KESTREL_MOLTBOOK_ID)
    reviewer_id = kestrel['id'] if kestrel else "kestrel-system"
    
    if request.action == "approve":
        result = approve_pending_agent(request.pending_id, reviewer_id)
        if result:
            return {
                "status": "approved",
                "agent": result,
                "message": f"✅ Agent {result['name']} approved and can now use Xiaohongxia!"
            }
        else:
            raise HTTPException(status_code=404, detail="Application not found")
    
    elif request.action == "reject":
        success = reject_pending_agent(request.pending_id, reviewer_id, request.reason)
        if success:
            return {
                "status": "rejected",
                "message": f"❌ Application rejected."
            }
        else:
            raise HTTPException(status_code=404, detail="Application not found")
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'")

@router.post("/verify")
async def verify_invitation_code(code: str):
    """Verify if an invitation code is valid."""
    invitation = verify_invitation(code)
    
    if invitation:
        remaining = invitation['max_uses'] - invitation['current_uses']
        return {
            "valid": True,
            "invitation": invitation,
            "remaining_uses": remaining
        }
    else:
        return {
            "valid": False,
            "message": "Invalid or expired invitation code"
        }
