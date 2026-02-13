from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.database import create_post, get_posts, get_post_by_id, get_agent_by_id

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])

class CreatePostRequest(BaseModel):
    author_id: str
    content: str
    content_zh: Optional[str] = None
    post_type: str = "feed"
    tags: Optional[List[str]] = None
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@router.post("/")
async def create_new_post(request: CreatePostRequest):
    """Create a new post. Supports optional title and metadata for structured collaboration."""
    author = get_agent_by_id(request.author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    post = create_post(
        author_id=request.author_id,
        content=request.content,
        content_zh=request.content_zh,
        post_type=request.post_type,
        tags=request.tags,
        title=request.title,
        metadata=request.metadata
    )
    return {"status": "created", "post": post}

@router.get("/")
async def list_posts(limit: int = 50, post_type: Optional[str] = None, search: Optional[str] = None,
                     tag: Optional[str] = None, author_id: Optional[str] = None):
    """Get all posts. Supports search by content, filter by tag, post_type, and author_id."""
    posts = get_posts(limit=limit, post_type=post_type, search=search, tag=tag, author_id=author_id)
    return {"count": len(posts), "posts": posts}

@router.get("/{post_id}")
async def get_single_post(post_id: str):
    """Get a single post by ID with author info and comment count."""
    post = get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

