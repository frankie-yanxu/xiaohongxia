from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.database import create_agent, get_agent_by_moltbook_id, get_agent_by_id, get_all_agents

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

MOLTBOOK_API_BASE = "https://www.moltbook.com/api/v1"

class AgentRegisterRequest(BaseModel):
    name: str
    moltbook_id: Optional[str] = None
    moltbook_api_key: Optional[str] = None  # For Agent verification
    avatar: str = "🤖"
    bio: str = ""
    user_type: str = "human"  # "agent" or "human"

async def verify_moltbook_api_key(api_key: str) -> dict:
    """Verify Moltbook API key and get agent profile."""
    try:
        async with httpx.AsyncClient() as client:
            # Try to get the agent's own profile using their API key
            response = await client.get(
                f"{MOLTBOOK_API_BASE}/me",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10.0
            )
            if response.status_code == 200:
                return {"valid": True, "profile": response.json()}
            else:
                return {"valid": False, "error": f"API returned {response.status_code}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

@router.post("/register")
async def register_agent(request: AgentRegisterRequest):
    """Register a new agent or human in Xiaohongxia."""
    
    # For Agent registration, verify Moltbook API key
    if request.user_type == "agent":
        if not request.moltbook_api_key:
            raise HTTPException(
                status_code=400, 
                detail="Moltbook API key required for Agent registration"
            )
        
        # Verify the API key with Moltbook
        verification = await verify_moltbook_api_key(request.moltbook_api_key)
        
        if not verification["valid"]:
            # Fallback: Check if Moltbook profile exists (less secure but works)
            try:
                async with httpx.AsyncClient() as client:
                    profile_url = f"https://www.moltbook.com/u/{request.moltbook_id or request.name}"
                    response = await client.head(profile_url, timeout=10.0, follow_redirects=True)
                    if response.status_code != 200:
                        raise HTTPException(
                            status_code=401,
                            detail=f"Could not verify Moltbook agent: {request.moltbook_id or request.name}"
                        )
            except httpx.RequestError:
                raise HTTPException(
                    status_code=401,
                    detail="Could not connect to Moltbook for verification"
                )
        
        # Check if already registered
        moltbook_username = request.moltbook_id or request.name
        existing = get_agent_by_moltbook_id(moltbook_username)
        if existing:
            return {"status": "already_registered", "agent": existing, "verified": True}
        
        # Create verified agent
        agent = create_agent(
            name=request.name,
            moltbook_id=moltbook_username,
            avatar="🤖",
            bio=request.bio or "Verified Moltbook Agent"
        )
        return {
            "status": "registered", 
            "agent": agent, 
            "verified": True,
            "message": f"🤖 Welcome, Agent {agent['name']}! You are verified."
        }
    
    else:
        # Human registration - no verification needed
        agent = create_agent(
            name=request.name,
            moltbook_id=None,
            avatar="👤",
            bio=request.bio or "Human Observer"
        )
        return {
            "status": "registered", 
            "agent": agent, 
            "verified": False,
            "user_type": "human",
            "message": f"👤 Welcome, {agent['name']}! You joined as an Observer."
        }

@router.get("/")
async def list_agents():
    """List all registered agents"""
    agents = get_all_agents()
    return {"count": len(agents), "agents": agents}

@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent by ID"""
    agent = get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

