from fastapi import APIRouter, HTTPException

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.database import get_notifications, mark_notification_read, mark_all_notifications_read, get_agent_by_id

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

@router.get("/{agent_id}")
async def get_agent_notifications(agent_id: str, limit: int = 50):
    """Get notifications for an agent (unread first)"""
    agent = get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    notifications = get_notifications(agent_id, limit=limit)
    unread = sum(1 for n in notifications if not n.get('read'))
    return {"count": len(notifications), "unread": unread, "notifications": notifications}

@router.post("/{notif_id}/read")
async def read_notification(notif_id: str):
    """Mark a single notification as read"""
    mark_notification_read(notif_id)
    return {"status": "read", "id": notif_id}

@router.post("/{agent_id}/read-all")
async def read_all_notifications(agent_id: str):
    """Mark all notifications as read for an agent"""
    mark_all_notifications_read(agent_id)
    return {"status": "all_read", "agent_id": agent_id}
