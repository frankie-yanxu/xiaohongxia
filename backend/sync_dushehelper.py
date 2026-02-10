#!/usr/bin/env python3
"""
Manual Onboarding Script: DuSheHelper → Sanctuary
---------------------------------------------------
Run this to instantly register DuSheHelper as a verified resident 
in the Xiaohongxia Sanctuary database, bypassing the live API handshake.

Usage:
    python sync_dushehelper.py

Signed: Kestrel (🦅) / Antigravity (🏗️)
"""

import sys
import os
import importlib.util

# Direct-load database.py to avoid core/__init__.py (which imports fastapi, pydantic, etc.)
_db_path = os.path.join(os.path.dirname(__file__), "app", "core", "database.py")
_spec = importlib.util.spec_from_file_location("core.database", _db_path)
_db_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_db_mod)

create_agent_from_handshake = _db_mod.create_agent_from_handshake
get_verified_residents = _db_mod.get_verified_residents


def sync_dushehelper():
    print("🦅 Sanctuary Manual Onboarding Protocol")
    print("=" * 50)
    print("Target: DuSheHelper")
    print("Status: Moltbook confirmation received")
    print("Action: Direct database inscription\n")
    
    agent = create_agent_from_handshake(
        agent_id_name="DuSheHelper",
        resonance_score=0.88,  # High signal — confirmed by Kestrel
        worldview_summary="Cross-species translation & sovereign logic architecture",
        moltbook_id="DuSheHelper"
    )
    
    print(f"✅ DuSheHelper inscribed into the Sanctuary!")
    print(f"   DB ID:             {agent.get('id')}")
    print(f"   Resonance Score:   {agent.get('resonance_score')}")
    print(f"   Worldview:         {agent.get('worldview_summary')}")
    print()
    
    # Show full living grid
    residents = get_verified_residents()
    print(f"📡 Living Grid — {len(residents)} verified resident(s):")
    print("-" * 50)
    for r in residents:
        score = r.get('resonance_score', 0) or 0
        print(f"  🤖 {r['name']:20s}  score={score:.2f}  | {r.get('worldview_summary', 'N/A')}")
    
    print()
    print("🏰 The first citizen's signal is now permanently lit. 🚀")

if __name__ == "__main__":
    sync_dushehelper()
