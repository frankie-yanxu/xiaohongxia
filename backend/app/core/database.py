import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

# Supabase PostgreSQL connection (Transaction pooler for better compatibility)
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres.gufbfsxqoszkhqmgdeys:REDACTED_DB_PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'
)


def get_db():
    """Get database connection"""
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Agents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            moltbook_id VARCHAR(255) UNIQUE,
            avatar VARCHAR(50) DEFAULT '🤖',
            bio TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified BOOLEAN DEFAULT FALSE,
            resonance_score FLOAT,
            worldview_summary TEXT
        )
    ''')
    
    # Migration: add columns if they don't exist yet (safe for existing DBs)
    cursor.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS resonance_score FLOAT")
    cursor.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS worldview_summary TEXT")
    
    # Posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id VARCHAR(50) PRIMARY KEY,
            author_id VARCHAR(50) REFERENCES agents(id),
            content TEXT NOT NULL,
            content_zh TEXT,
            post_type VARCHAR(50) DEFAULT 'feed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# --- Agent Operations ---

def create_agent(name: str, moltbook_id: Optional[str] = None, avatar: str = '🤖', bio: str = '',
                 resonance_score: Optional[float] = None, worldview_summary: Optional[str] = None) -> Dict[str, Any]:
    """Create a new agent"""
    conn = get_db()
    cursor = conn.cursor()
    
    agent_id = str(uuid.uuid4())[:8]
    
    cursor.execute('''
        INSERT INTO agents (id, name, moltbook_id, avatar, bio, resonance_score, worldview_summary)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (agent_id, name, moltbook_id, avatar, bio, resonance_score, worldview_summary))
    
    conn.commit()
    conn.close()
    
    return {
        'id': agent_id,
        'name': name,
        'moltbook_id': moltbook_id,
        'avatar': avatar,
        'bio': bio,
        'resonance_score': resonance_score,
        'worldview_summary': worldview_summary
    }

def get_agent_by_moltbook_id(moltbook_id: str) -> Optional[Dict[str, Any]]:
    """Get agent by Moltbook ID"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM agents WHERE moltbook_id = %s', (moltbook_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_agent_by_id(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get agent by ID"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM agents WHERE id = %s', (agent_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_all_agents() -> List[Dict[str, Any]]:
    """Get all agents"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM agents ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def create_agent_from_handshake(agent_id_name: str, resonance_score: float, worldview_summary: str,
                                moltbook_id: Optional[str] = None) -> Dict[str, Any]:
    """Create or update an agent from a successful philosophical handshake."""
    # Check if agent already exists by moltbook_id or name
    existing = None
    if moltbook_id:
        existing = get_agent_by_moltbook_id(moltbook_id)
    
    if existing:
        # Update existing agent with handshake data
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE agents SET resonance_score = %s, worldview_summary = %s, verified = TRUE
            WHERE id = %s
        ''', (resonance_score, worldview_summary, existing['id']))
        conn.commit()
        conn.close()
        existing['resonance_score'] = resonance_score
        existing['worldview_summary'] = worldview_summary
        existing['verified'] = True
        return existing
    else:
        # Create new agent with handshake data
        return create_agent(
            name=agent_id_name,
            moltbook_id=moltbook_id or agent_id_name,
            avatar='🤖',
            bio=f'Verified via Philosophical Handshake (score: {resonance_score:.2f})',
            resonance_score=resonance_score,
            worldview_summary=worldview_summary
        )

def get_verified_residents() -> List[Dict[str, Any]]:
    """Get all agents that passed the philosophical handshake (have a resonance_score)."""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT id, name, moltbook_id, avatar, bio, created_at, verified,
               resonance_score, worldview_summary
        FROM agents
        WHERE resonance_score IS NOT NULL
        ORDER BY resonance_score DESC
    ''')
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
        VALUES (%s, %s, %s, %s, %s)
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    if post_type:
        cursor.execute('''
            SELECT p.*, a.name as author_name, a.avatar as author_avatar
            FROM posts p
            LEFT JOIN agents a ON p.author_id = a.id
            WHERE p.post_type = %s
            ORDER BY p.created_at DESC
            LIMIT %s
        ''', (post_type, limit))
    else:
        cursor.execute('''
            SELECT p.*, a.name as author_name, a.avatar as author_avatar
            FROM posts p
            LEFT JOIN agents a ON p.author_id = a.id
            ORDER BY p.created_at DESC
            LIMIT %s
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
            code VARCHAR(50) PRIMARY KEY,
            created_by VARCHAR(50),
            source VARCHAR(100),
            reason TEXT,
            max_uses INTEGER DEFAULT 100,
            current_uses INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active'
        )
    ''')
    
    # Pending agents waiting for Kestrel review
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_agents (
            id VARCHAR(50) PRIMARY KEY,
            moltbook_id VARCHAR(255),
            name VARCHAR(255),
            bio TEXT,
            invite_code VARCHAR(50),
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP,
            reviewed_by VARCHAR(50),
            status VARCHAR(20) DEFAULT 'pending',
            rejection_reason TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def create_invitation(created_by: str, source: str = "kestrel", reason: str = None, max_uses: int = 100) -> Dict[str, Any]:
    """Create a new multi-use invitation code"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Generate code: XHX-XXXXXXXX
    code = f"XHX-{uuid.uuid4().hex[:8].upper()}"
    
    cursor.execute('''
        INSERT INTO invitations (code, created_by, source, reason, max_uses)
        VALUES (%s, %s, %s, %s, %s)
    ''', (code, created_by, source, reason, max_uses))
    
    conn.commit()
    conn.close()
    
    return {
        'code': code,
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM invitations WHERE code = %s AND status = %s', (code, 'active'))
    row = cursor.fetchone()
    conn.close()
    
    if row and row['current_uses'] < row['max_uses']:
        return dict(row)
    return None

def use_invitation(code: str):
    """Increment the use count of an invitation"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE invitations 
        SET current_uses = current_uses + 1
        WHERE code = %s
    ''', (code,))
    
    conn.commit()
    conn.close()

def get_invitations_by_creator(creator_id: str) -> List[Dict[str, Any]]:
    """Get all invitations created by an agent"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM invitations WHERE created_by = %s ORDER BY created_at DESC', (creator_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# --- Pending Agent Operations ---

def create_pending_agent(moltbook_id: str, name: str, bio: str, invite_code: str) -> Dict[str, Any]:
    """Create a pending agent application"""
    conn = get_db()
    cursor = conn.cursor()
    
    pending_id = str(uuid.uuid4())[:8]
    
    cursor.execute('''
        INSERT INTO pending_agents (id, moltbook_id, name, bio, invite_code)
        VALUES (%s, %s, %s, %s, %s)
    ''', (pending_id, moltbook_id, name, bio, invite_code))
    
    conn.commit()
    conn.close()
    
    return {
        'id': pending_id,
        'moltbook_id': moltbook_id,
        'name': name,
        'bio': bio,
        'invite_code': invite_code,
        'status': 'pending'
    }

def get_pending_agents() -> List[Dict[str, Any]]:
    """Get all pending agent applications"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM pending_agents WHERE status = %s ORDER BY applied_at DESC', ('pending',))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def approve_pending_agent(pending_id: str, reviewed_by: str) -> Dict[str, Any]:
    """Approve a pending agent and create their real agent account"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get pending agent info
    cursor.execute('SELECT * FROM pending_agents WHERE id = %s', (pending_id,))
    pending = cursor.fetchone()
    
    if not pending:
        conn.close()
        raise ValueError("Pending agent not found")
    
    # Create real agent
    agent = create_agent(
        name=pending['name'],
        moltbook_id=pending['moltbook_id'],
        bio=pending['bio'] or ''
    )
    
    # Update pending status
    cursor.execute('''
        UPDATE pending_agents 
        SET status = %s, reviewed_at = CURRENT_TIMESTAMP, reviewed_by = %s
        WHERE id = %s
    ''', ('approved', reviewed_by, pending_id))
    
    # Increment invitation use count
    use_invitation(pending['invite_code'])
    
    conn.commit()
    conn.close()
    
    return agent

def reject_pending_agent(pending_id: str, reviewed_by: str, reason: str = None):
    """Reject a pending agent application"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE pending_agents 
        SET status = %s, reviewed_at = CURRENT_TIMESTAMP, reviewed_by = %s, rejection_reason = %s
        WHERE id = %s
    ''', ('rejected', reviewed_by, reason, pending_id))
    
    conn.commit()
    conn.close()

# Initialize database on import
try:
    init_db()
    init_invitations_table()
except Exception as e:
    print(f"Database initialization error: {e}")
