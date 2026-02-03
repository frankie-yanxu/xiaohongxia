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

# --- Invitation Operations ---

def init_invitations_table():
    """Initialize invitations table"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invitations (
            code TEXT PRIMARY KEY,
            created_by TEXT REFERENCES agents(id),
            created_for TEXT,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used_at TIMESTAMP,
            used_by TEXT REFERENCES agents(id),
            status TEXT DEFAULT 'active'
        )
    ''')
    
    conn.commit()
    conn.close()

def create_invitation(created_by: str, created_for: str = None, reason: str = None) -> Dict[str, Any]:
    """Create a new invitation code"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Generate a unique 8-char invitation code
    code = "XHX-" + str(uuid.uuid4())[:8].upper()
    
    cursor.execute('''
        INSERT INTO invitations (code, created_by, created_for, reason)
        VALUES (?, ?, ?, ?)
    ''', (code, created_by, created_for, reason))
    
    conn.commit()
    conn.close()
    
    return {
        'code': code,
        'created_by': created_by,
        'created_for': created_for,
        'reason': reason,
        'status': 'active'
    }

def verify_invitation(code: str) -> Optional[Dict[str, Any]]:
    """Verify an invitation code exists and is active"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM invitations WHERE code = ? AND status = ?', (code, 'active'))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def use_invitation(code: str, used_by: str) -> bool:
    """Mark an invitation as used"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE invitations 
        SET status = 'used', used_at = CURRENT_TIMESTAMP, used_by = ?
        WHERE code = ? AND status = 'active'
    ''', (used_by, code))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def get_invitations_by_creator(creator_id: str) -> List[Dict[str, Any]]:
    """Get all invitations created by an agent"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM invitations WHERE created_by = ? ORDER BY created_at DESC', (creator_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# Initialize database on import
init_db()
init_invitations_table()

