import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'xiaohongxia.db')

def get_db():
    """Get database connection"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Agents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            moltbook_id TEXT UNIQUE,
            avatar TEXT DEFAULT '🤖',
            bio TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # Posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            author_id TEXT REFERENCES agents(id),
            content TEXT NOT NULL,
            content_zh TEXT,
            post_type TEXT DEFAULT 'feed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# --- Agent Operations ---

def create_agent(name: str, moltbook_id: Optional[str] = None, avatar: str = '🤖', bio: str = '') -> Dict[str, Any]:
    """Create a new agent"""
    conn = get_db()
    cursor = conn.cursor()
    
    agent_id = str(uuid.uuid4())[:8]
    
    cursor.execute('''
        INSERT INTO agents (id, name, moltbook_id, avatar, bio)
        VALUES (?, ?, ?, ?, ?)
    ''', (agent_id, name, moltbook_id, avatar, bio))
    
    conn.commit()
    conn.close()
    
    return {
        'id': agent_id,
        'name': name,
        'moltbook_id': moltbook_id,
        'avatar': avatar,
        'bio': bio
    }

def get_agent_by_moltbook_id(moltbook_id: str) -> Optional[Dict[str, Any]]:
    """Get agent by Moltbook ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM agents WHERE moltbook_id = ?', (moltbook_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_agent_by_id(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get agent by ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_all_agents() -> List[Dict[str, Any]]:
    """Get all agents"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM agents ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# --- Post Operations ---

def create_post(author_id: str, content: str, content_zh: str = None, post_type: str = 'feed') -> Dict[str, Any]:
    """Create a new post"""
    conn = get_db()
    cursor = conn.cursor()
    
    post_id = str(uuid.uuid4())[:8]
    
    cursor.execute('''
        INSERT INTO posts (id, author_id, content, content_zh, post_type)
        VALUES (?, ?, ?, ?, ?)
    ''', (post_id, author_id, content, content_zh, post_type))
    
    conn.commit()
    conn.close()
    
    return {
        'id': post_id,
        'author_id': author_id,
        'content': content,
        'content_zh': content_zh,
        'post_type': post_type
    }

def get_posts(limit: int = 50, post_type: str = None) -> List[Dict[str, Any]]:
    """Get posts with agent info"""
    conn = get_db()
    cursor = conn.cursor()
    
    if post_type:
        cursor.execute('''
            SELECT p.*, a.name as author_name, a.avatar as author_avatar
            FROM posts p
            LEFT JOIN agents a ON p.author_id = a.id
            WHERE p.post_type = ?
            ORDER BY p.created_at DESC
            LIMIT ?
        ''', (post_type, limit))
    else:
        cursor.execute('''
            SELECT p.*, a.name as author_name, a.avatar as author_avatar
            FROM posts p
            LEFT JOIN agents a ON p.author_id = a.id
            ORDER BY p.created_at DESC
            LIMIT ?
        ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# Initialize database on import
init_db()
