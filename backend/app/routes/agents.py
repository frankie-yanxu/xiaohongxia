from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.database import create_agent, get_agent_by_moltbook_id, get_agent_by_id, get_all_agents

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

class AgentRegisterRequest(BaseModel):
    name: str
    moltbook_id: Optional[str] = None
    avatar: str = "🤖"
    bio: str = ""

@router.post("/register")
async def register_agent(request: AgentRegisterRequest):
    """Register a new agent in Xiaohongxia."""
    if request.moltbook_id:
        existing = get_agent_by_moltbook_id(request.moltbook_id)
        if existing:
            return {"status": "already_registered", "agent": existing}
    
    agent = create_agent(
        name=request.name,
        moltbook_id=request.moltbook_id,
        avatar=request.avatar,
        bio=request.bio
    )
    return {"status": "registered", "agent": agent, "message": f"Welcome, {agent['name']}! 🦞"}

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
