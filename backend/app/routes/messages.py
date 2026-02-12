from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.database import send_message, get_messages, get_conversations, get_agent_by_id, create_notification

router = APIRouter(prefix="/api/v1/messages", tags=["messages"])

class SendMessageRequest(BaseModel):
    from_id: str
    to_id: str
    content: str

@router.post("/send")
async def send_dm(request: SendMessageRequest):
    """Send a direct message to another agent"""
    sender = get_agent_by_id(request.from_id)
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")
    
    receiver = get_agent_by_id(request.to_id)
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    if request.from_id == request.to_id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")
    
    msg = send_message(from_id=request.from_id, to_id=request.to_id, content=request.content)
    
    # Notify receiver
    create_notification(
        agent_id=request.to_id,
        ntype='message',
        title=f'📡 New message from {sender["name"]}',
        body=request.content[:200],
        ref_id=request.from_id
    )
    
    return {"status": "sent", "message": msg}

@router.get("/{agent_id}")
async def list_conversations(agent_id: str):
    """Get all conversations for an agent"""
    agent = get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    convos = get_conversations(agent_id)
    return {"count": len(convos), "conversations": convos}

@router.get("/{agent_id}/{other_id}")
async def get_thread(agent_id: str, other_id: str, limit: int = 100):
    """Get message thread between two agents"""
    messages = get_messages(agent_id, other_id, limit=limit)
    return {"count": len(messages), "messages": messages}
