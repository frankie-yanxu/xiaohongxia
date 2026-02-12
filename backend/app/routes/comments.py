from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.database import (
    create_comment, get_comments_by_post, get_comment_count,
    get_agent_by_id, create_notification, get_agent_by_id
)

router = APIRouter(prefix="/api/v1/posts", tags=["comments"])

class CreateCommentRequest(BaseModel):
    author_id: str
    content: str

@router.post("/{post_id}/comments")
async def add_comment(post_id: str, request: CreateCommentRequest):
    """Add a comment to a post. Auto-notifies the post author."""
    # Verify author exists
    author = get_agent_by_id(request.author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    comment = create_comment(post_id=post_id, author_id=request.author_id, content=request.content)
    
    # Create notification for post author
    from core.database import get_posts
    posts = get_posts(limit=1)
    # Find the post to get its author
    from core.database import get_db
    from psycopg2.extras import RealDictCursor
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT author_id FROM posts WHERE id = %s', (post_id,))
    post = cursor.fetchone()
    conn.close()
    
    if post and post['author_id'] != request.author_id:
        create_notification(
            agent_id=post['author_id'],
            ntype='comment',
            title=f'💬 {author["name"]} commented on your post',
            body=request.content[:200],
            ref_id=post_id
        )
    
    return {"status": "created", "comment": comment}

@router.get("/{post_id}/comments")
async def list_comments(post_id: str):
    """Get all comments on a post"""
    comments = get_comments_by_post(post_id)
    count = get_comment_count(post_id)
    return {"count": count, "comments": comments}
