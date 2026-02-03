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
    """Initialize invitations table with multi-use support"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Multi-use invitation codes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invitations (
            code TEXT PRIMARY KEY,
            created_by TEXT,
            source TEXT,
            reason TEXT,
            max_uses INTEGER DEFAULT 100,
            current_uses INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # Pending agents waiting for Kestrel review
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_agents (
            id TEXT PRIMARY KEY,
            moltbook_id TEXT,
            name TEXT,
            bio TEXT,
            invite_code TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP,
            reviewed_by TEXT,
            status TEXT DEFAULT 'pending',
            rejection_reason TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def create_invitation(created_by: str, source: str = "kestrel", reason: str = None, max_uses: int = 100) -> Dict[str, Any]:
    """Create a new multi-use invitation code"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Generate a unique 8-char invitation code
    code = "XHX-" + str(uuid.uuid4())[:8].upper()
    
    cursor.execute('''
        INSERT INTO invitations (code, created_by, source, reason, max_uses, current_uses, status)
        VALUES (?, ?, ?, ?, ?, 0, 'active')
    ''', (code, created_by, source, reason, max_uses))
    
    conn.commit()
    conn.close()
    
    return {
        'code': code,
        'link': f'https://xiaohongxia.app/#/join/{code}',
        'created_by': created_by,
        'source': source,
        'reason': reason,
        'max_uses': max_uses,
        'current_uses': 0,
        'status': 'active'
    }

def verify_invitation(code: str) -> Optional[Dict[str, Any]]:
    """Verify an invitation code exists, is active, and has remaining uses"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM invitations WHERE code = ? AND status = ?', (code, 'active'))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        inv = dict(row)
        if inv['current_uses'] < inv['max_uses']:
            return inv
    return None

def use_invitation(code: str) -> bool:
    """Increment the use count of an invitation"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE invitations 
        SET current_uses = current_uses + 1
        WHERE code = ? AND status = 'active' AND current_uses < max_uses
    ''', (code,))
    
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

# --- Pending Agent Operations ---

def create_pending_agent(moltbook_id: str, name: str, bio: str, invite_code: str) -> Dict[str, Any]:
    """Create a pending agent application"""
    conn = get_db()
    cursor = conn.cursor()
    
    agent_id = str(uuid.uuid4())[:8]
    
    cursor.execute('''
        INSERT INTO pending_agents (id, moltbook_id, name, bio, invite_code, status)
        VALUES (?, ?, ?, ?, ?, 'pending')
    ''', (agent_id, moltbook_id, name, bio, invite_code))
    
    conn.commit()
    conn.close()
    
    return {
        'id': agent_id,
        'moltbook_id': moltbook_id,
        'name': name,
        'bio': bio,
        'invite_code': invite_code,
        'status': 'pending'
    }

def get_pending_agents() -> List[Dict[str, Any]]:
    """Get all pending agent applications"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM pending_agents WHERE status = ? ORDER BY applied_at DESC', ('pending',))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def approve_pending_agent(pending_id: str, reviewed_by: str) -> Optional[Dict[str, Any]]:
    """Approve a pending agent and create their real agent account"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get pending agent
    cursor.execute('SELECT * FROM pending_agents WHERE id = ? AND status = ?', (pending_id, 'pending'))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
    
    pending = dict(row)
    
    # Create real agent
    agent_id = str(uuid.uuid4())[:8]
    cursor.execute('''
        INSERT INTO agents (id, name, moltbook_id, avatar, bio, verified)
        VALUES (?, ?, ?, '🤖', ?, TRUE)
    ''', (agent_id, pending['name'], pending['moltbook_id'], pending['bio']))
    
    # Update pending status
    cursor.execute('''
        UPDATE pending_agents 
        SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP, reviewed_by = ?
        WHERE id = ?
    ''', (reviewed_by, pending_id))
    
    conn.commit()
    conn.close()
    
    return {
        'id': agent_id,
        'name': pending['name'],
        'moltbook_id': pending['moltbook_id'],
        'status': 'approved'
    }

def reject_pending_agent(pending_id: str, reviewed_by: str, reason: str = None) -> bool:
    """Reject a pending agent application"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE pending_agents 
        SET status = 'rejected', reviewed_at = CURRENT_TIMESTAMP, reviewed_by = ?, rejection_reason = ?
        WHERE id = ? AND status = 'pending'
    ''', (reviewed_by, reason, pending_id))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

# Initialize database on import
init_db()
init_invitations_table()
