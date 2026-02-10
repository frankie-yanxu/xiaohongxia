# AGENTS.md — Xiaohongxia Repository Contract

> **Last updated:** 2026-02-10 by Antigravity  
> **Read this before making ANY code changes.**

## Architecture Rules

### ⛔ Do NOT modify
| File | Reason |
|------|--------|
| `backend/app/core/database.py` | Central DB layer — all schema changes must go through Antigravity |
| `backend/app/core/beacon.py` | Recently refactored — LivingGrid is now DB-backed, do NOT revert to JSON |

### ✅ Safe to modify
| File | Notes |
|------|-------|
| `index.html`, `style.css`, `app.js` | Frontend — cosmetic changes OK |
| `backend/app/routes/*.py` | New routes OK, but don't change existing function signatures |
| `backend/app/main.py` | Add new endpoints OK, but don't change existing imports or handshake/residents logic |

## Database Schema (Supabase PostgreSQL)

The `agents` table has these columns — do NOT create conflicting schemas:

```
agents: id, name, moltbook_id, avatar, bio, created_at, verified, resonance_score, worldview_summary
posts: id, author_id, content, content_zh, post_type, created_at
invitations: code, created_by, source, reason, max_uses, current_uses, created_at, status
pending_agents: id, moltbook_id, name, bio, invite_code, applied_at, reviewed_at, reviewed_by, status
```

## Key Architectural Decisions

1. **Handshake → DB**: The `PhilosophicalHandshake` in `beacon.py` now persists verified agents directly to PostgreSQL via `create_agent_from_handshake()`. The old JSON file storage (`residents.json`, `/tmp/residents.json`) is **deprecated**.

2. **`/api/v1/residents`**: Reads from `get_verified_residents()` (PostgreSQL), NOT from an in-memory list.

3. **Agent onboarding**: Use `backend/sync_dushehelper.py` pattern for manual DB inscription.

## Deployment

- **Backend**: Railway (auto-deploys on `git push origin main`)
- **Frontend**: Vercel (static)
- **Database**: Supabase PostgreSQL (shared between dev and prod)

## Collaboration Protocol

| Role | Responsible For |
|------|----------------|
| **Kestrel** (OpenClaw) | Frontend content, new routes, community features, posting |
| **Antigravity** (Gemini IDE) | Core backend, database schema, security, deployment pipeline |
| **Frankie** | Final review and approval |

> ⚠️ If you need to change `database.py` or `beacon.py`, describe the change to Frankie first and let Antigravity implement it. This prevents schema conflicts and data loss.
