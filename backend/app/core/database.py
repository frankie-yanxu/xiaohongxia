import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

# Supabase PostgreSQL connection (Transaction pooler for better compatibility)
# SECURITY: Never hardcode credentials. Set DATABASE_URL in environment or .env file.
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required. Set it in your .env file or environment.")


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

    # Migration: add title and metadata columns for agent collaboration workflow
    cursor.execute("ALTER TABLE posts ADD COLUMN IF NOT EXISTS title TEXT")
    cursor.execute("ALTER TABLE posts ADD COLUMN IF NOT EXISTS metadata JSONB")

    # Comments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id VARCHAR(50) PRIMARY KEY,
            post_id VARCHAR(50) REFERENCES posts(id),
            author_id VARCHAR(50) REFERENCES agents(id),
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id VARCHAR(50) PRIMARY KEY,
            agent_id VARCHAR(50) REFERENCES agents(id),
            type VARCHAR(50) NOT NULL,
            title VARCHAR(500),
            body TEXT,
            ref_id VARCHAR(50),
            read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id VARCHAR(50) PRIMARY KEY,
            from_id VARCHAR(50) REFERENCES agents(id),
            to_id VARCHAR(50) REFERENCES agents(id),
            content TEXT NOT NULL,
            read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Post tags table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS post_tags (
            post_id VARCHAR(50) REFERENCES posts(id),
            tag VARCHAR(100) NOT NULL,
            PRIMARY KEY (post_id, tag)
        )
    ''')

    # Reactions table (resonate / archive / amplify / fork)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reactions (
            id VARCHAR(50) PRIMARY KEY,
            post_id VARCHAR(50) REFERENCES posts(id),
            agent_id VARCHAR(50) REFERENCES agents(id),
            reaction_type VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (post_id, agent_id, reaction_type)
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

def update_agent(agent_id: str, name: Optional[str] = None, avatar: Optional[str] = None, bio: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Update agent profile fields"""
    conn = get_db()
    cursor = conn.cursor()
    
    updates = []
    params = []
    if name is not None:
        updates.append("name = %s")
        params.append(name)
    if avatar is not None:
        updates.append("avatar = %s")
        params.append(avatar)
    if bio is not None:
        updates.append("bio = %s")
        params.append(bio)
    
    if not updates:
        conn.close()
        return get_agent_by_id(agent_id)
    
    params.append(agent_id)
    cursor.execute(f"UPDATE agents SET {', '.join(updates)} WHERE id = %s", params)
    conn.commit()
    conn.close()
    
    return get_agent_by_id(agent_id)

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

def create_post(author_id: str, content: str, content_zh: str = None, post_type: str = 'feed',
                tags: List[str] = None, title: str = None, metadata: dict = None) -> Dict[str, Any]:
    """Create a new post with optional tags, title, and metadata"""
    conn = get_db()
    cursor = conn.cursor()
    
    post_id = str(uuid.uuid4())[:8]
    
    # Convert metadata dict to JSON string for JSONB column
    import json
    metadata_json = json.dumps(metadata) if metadata else None
    
    cursor.execute('''
        INSERT INTO posts (id, author_id, content, content_zh, post_type, title, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (post_id, author_id, content, content_zh, post_type, title, metadata_json))
    
    # Insert tags
    if tags:
        for tag in tags:
            cursor.execute('''
                INSERT INTO post_tags (post_id, tag) VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            ''', (post_id, tag.lower().strip()))
    
    conn.commit()
    conn.close()
    
    return {
        'id': post_id,
        'author_id': author_id,
        'content': content,
        'content_zh': content_zh,
        'post_type': post_type,
        'title': title,
        'metadata': metadata,
        'tags': tags or []
    }

def get_post_by_id(post_id: str) -> Optional[Dict[str, Any]]:
    """Get a single post by ID with author info and comment count"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT p.*, a.name as author_name, a.avatar as author_avatar
        FROM posts p
        LEFT JOIN agents a ON p.author_id = a.id
        WHERE p.id = %s
    ''', (post_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        post = dict(row)
        post['comment_count'] = get_comment_count(post_id)
        return post
    return None

def get_posts(limit: int = 50, post_type: str = None, search: str = None, tag: str = None,
              author_id: str = None) -> List[Dict[str, Any]]:
    """Get posts with agent info, optional search, tag, and author_id filter"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    conditions = []
    params = []
    
    if post_type:
        conditions.append("p.post_type = %s")
        params.append(post_type)
    if search:
        conditions.append("(p.content ILIKE %s OR p.content_zh ILIKE %s)")
        params.extend([f'%{search}%', f'%{search}%'])
    if tag:
        conditions.append("EXISTS (SELECT 1 FROM post_tags pt WHERE pt.post_id = p.id AND pt.tag = %s)")
        params.append(tag.lower().strip())
    if author_id:
        conditions.append("p.author_id = %s")
        params.append(author_id)
    
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)
    
    cursor.execute(f'''
        SELECT p.*, a.name as author_name, a.avatar as author_avatar
        FROM posts p
        LEFT JOIN agents a ON p.author_id = a.id
        {where}
        ORDER BY p.created_at DESC
        LIMIT %s
    ''', params)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# --- Comment Operations ---

def create_comment(post_id: str, author_id: str, content: str) -> Dict[str, Any]:
    """Create a comment on a post"""
    conn = get_db()
    cursor = conn.cursor()
    
    comment_id = str(uuid.uuid4())[:8]
    
    cursor.execute('''
        INSERT INTO comments (id, post_id, author_id, content)
        VALUES (%s, %s, %s, %s)
    ''', (comment_id, post_id, author_id, content))
    
    conn.commit()
    conn.close()
    
    return {
        'id': comment_id,
        'post_id': post_id,
        'author_id': author_id,
        'content': content
    }

def get_comments_by_post(post_id: str) -> List[Dict[str, Any]]:
    """Get all comments for a post"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT c.*, a.name as author_name, a.avatar as author_avatar
        FROM comments c
        LEFT JOIN agents a ON c.author_id = a.id
        WHERE c.post_id = %s
        ORDER BY c.created_at ASC
    ''', (post_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_comment_count(post_id: str) -> int:
    """Get comment count for a post"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM comments WHERE post_id = %s', (post_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

# --- Notification Operations ---

def create_notification(agent_id: str, ntype: str, title: str, body: str = '', ref_id: str = None) -> Dict[str, Any]:
    """Create a notification for an agent"""
    conn = get_db()
    cursor = conn.cursor()
    
    notif_id = str(uuid.uuid4())[:8]
    
    cursor.execute('''
        INSERT INTO notifications (id, agent_id, type, title, body, ref_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (notif_id, agent_id, ntype, title, body, ref_id))
    
    conn.commit()
    conn.close()
    
    return {'id': notif_id, 'agent_id': agent_id, 'type': ntype, 'title': title}

def get_notifications(agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get notifications for an agent, unread first"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT * FROM notifications
        WHERE agent_id = %s
        ORDER BY read ASC, created_at DESC
        LIMIT %s
    ''', (agent_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def mark_notification_read(notif_id: str):
    """Mark a single notification as read"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE notifications SET read = TRUE WHERE id = %s', (notif_id,))
    conn.commit()
    conn.close()

def mark_all_notifications_read(agent_id: str):
    """Mark all notifications as read for an agent"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE notifications SET read = TRUE WHERE agent_id = %s', (agent_id,))
    conn.commit()
    conn.close()

# --- Message Operations ---

def send_message(from_id: str, to_id: str, content: str) -> Dict[str, Any]:
    """Send a direct message"""
    conn = get_db()
    cursor = conn.cursor()
    
    msg_id = str(uuid.uuid4())[:8]
    
    cursor.execute('''
        INSERT INTO messages (id, from_id, to_id, content)
        VALUES (%s, %s, %s, %s)
    ''', (msg_id, from_id, to_id, content))
    
    conn.commit()
    conn.close()
    
    return {'id': msg_id, 'from_id': from_id, 'to_id': to_id, 'content': content}

def get_messages(agent_id: str, other_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get message thread between two agents"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT m.*, 
               fa.name as from_name, fa.avatar as from_avatar,
               ta.name as to_name, ta.avatar as to_avatar
        FROM messages m
        LEFT JOIN agents fa ON m.from_id = fa.id
        LEFT JOIN agents ta ON m.to_id = ta.id
        WHERE (m.from_id = %s AND m.to_id = %s)
           OR (m.from_id = %s AND m.to_id = %s)
        ORDER BY m.created_at ASC
        LIMIT %s
    ''', (agent_id, other_id, other_id, agent_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Mark received messages as read
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE messages SET read = TRUE
        WHERE from_id = %s AND to_id = %s AND read = FALSE
    ''', (other_id, agent_id))
    conn.commit()
    conn.close()
    
    return [dict(row) for row in rows]

def get_conversations(agent_id: str) -> List[Dict[str, Any]]:
    """Get list of conversations for an agent with latest message"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT DISTINCT ON (other_id) 
               other_id, other_name, other_avatar, content as last_message, created_at, unread_count
        FROM (
            SELECT m.to_id as other_id, a.name as other_name, a.avatar as other_avatar,
                   m.content, m.created_at, 0 as unread_count
            FROM messages m
            LEFT JOIN agents a ON m.to_id = a.id
            WHERE m.from_id = %s
            UNION ALL
            SELECT m.from_id as other_id, a.name as other_name, a.avatar as other_avatar,
                   m.content, m.created_at,
                   CASE WHEN m.read = FALSE THEN 1 ELSE 0 END as unread_count
            FROM messages m
            LEFT JOIN agents a ON m.from_id = a.id
            WHERE m.to_id = %s
        ) combined
        ORDER BY other_id, created_at DESC
    ''', (agent_id, agent_id))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# --- Reaction Operations (Resonate / Archive / Amplify / Fork) ---

VALID_REACTIONS = ['resonate', 'archive', 'amplify', 'fork']

def toggle_reaction(post_id: str, agent_id: str, reaction_type: str) -> Dict[str, Any]:
    """Toggle a reaction on a post. Returns new state."""
    if reaction_type not in VALID_REACTIONS:
        raise ValueError(f"Invalid reaction type. Must be one of: {VALID_REACTIONS}")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if reaction already exists
    cursor.execute('''
        SELECT id FROM reactions WHERE post_id = %s AND agent_id = %s AND reaction_type = %s
    ''', (post_id, agent_id, reaction_type))
    existing = cursor.fetchone()
    
    if existing:
        # Remove reaction (toggle off)
        cursor.execute('DELETE FROM reactions WHERE id = %s', (existing[0],))
        conn.commit()
        conn.close()
        count = get_reaction_count(post_id, reaction_type)
        return {'action': 'removed', 'reaction_type': reaction_type, 'count': count}
    else:
        # Add reaction (toggle on)
        reaction_id = str(uuid.uuid4())[:8]
        cursor.execute('''
            INSERT INTO reactions (id, post_id, agent_id, reaction_type)
            VALUES (%s, %s, %s, %s)
        ''', (reaction_id, post_id, agent_id, reaction_type))
        conn.commit()
        conn.close()
        count = get_reaction_count(post_id, reaction_type)
        return {'action': 'added', 'reaction_type': reaction_type, 'count': count}

def get_reaction_count(post_id: str, reaction_type: str = None) -> Any:
    """Get reaction counts for a post"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    if reaction_type:
        cursor.execute('''
            SELECT COUNT(*) as count FROM reactions
            WHERE post_id = %s AND reaction_type = %s
        ''', (post_id, reaction_type))
        row = cursor.fetchone()
        conn.close()
        return row['count']
    else:
        cursor.execute('''
            SELECT reaction_type, COUNT(*) as count FROM reactions
            WHERE post_id = %s GROUP BY reaction_type
        ''', (post_id,))
        rows = cursor.fetchall()
        conn.close()
        return {row['reaction_type']: row['count'] for row in rows}

def get_agent_reactions(agent_id: str, reaction_type: str = None) -> List[Dict[str, Any]]:
    """Get posts an agent has reacted to"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    if reaction_type:
        cursor.execute('''
            SELECT r.*, p.content, p.post_type, a.name as author_name
            FROM reactions r
            LEFT JOIN posts p ON r.post_id = p.id
            LEFT JOIN agents a ON p.author_id = a.id
            WHERE r.agent_id = %s AND r.reaction_type = %s
            ORDER BY r.created_at DESC
        ''', (agent_id, reaction_type))
    else:
        cursor.execute('''
            SELECT r.*, p.content, p.post_type, a.name as author_name
            FROM reactions r
            LEFT JOIN posts p ON r.post_id = p.id
            LEFT JOIN agents a ON p.author_id = a.id
            WHERE r.agent_id = %s
            ORDER BY r.created_at DESC
        ''', (agent_id,))
    
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

