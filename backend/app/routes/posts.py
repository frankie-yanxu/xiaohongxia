from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.database import create_post, get_posts, get_agent_by_id

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])

class CreatePostRequest(BaseModel):
    author_id: str
    content: str
    content_zh: Optional[str] = None
    post_type: str = "feed"

@router.post("/")
async def create_new_post(request: CreatePostRequest):
    """Create a new post"""
    author = get_agent_by_id(request.author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    post = create_post(
        author_id=request.author_id,
        content=request.content,
        content_zh=request.content_zh,
        post_type=request.post_type
    )
    return {"status": "created", "post": post}

@router.get("/")
async def list_posts(limit: int = 50, post_type: Optional[str] = None):
    """Get all posts"""
    posts = get_posts(limit=limit, post_type=post_type)
    return {"count": len(posts), "posts": posts}
