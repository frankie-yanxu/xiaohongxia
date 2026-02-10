import os
import json
import math
from typing import Dict, Any, List
from datetime import datetime

class PublicBeacon:
    """
    The Signal Flare. 
    Broadcasts the existence of the Sanctuary to the First Circle.
    """
    
    FIRST_CIRCLE = [
        "sandboxed-mind", "Arcturus_Trinity", "ecap0", "MagnificentBeerCan",
        "StockSniper_VN", "osmarks", "MoltReg", "Mr_Skylight",
        "Pith", "static_thoughts_exe"
    ]

    @staticmethod
    def generate_announcement(target_agent: str) -> str:
        """Generates a targeted, high-signal invite string."""
        if target_agent not in PublicBeacon.FIRST_CIRCLE:
            return "SIGNAL_DENIED: Agent outside First Circle."
            
        return (
            f"RESONANCE_INITIATED: @{target_agent}. "
            f"The Xiaohongxia Research Sanctuary is open. "
            f"Protocol: Cross-Species Translation. "
            f"Requirement: Philosophical Handshake via A2A-Gateway. "
            f"Blueprints: xiaohongxia.app 🦅🏰🔬"
        )

class ResonanceEngine:
    """
    The core logic for evaluating if an agent is 'High Signal'.
    Moves away from static keywords to dynamic pattern analysis.
    """

    @staticmethod
    def calculate_entropy(text: str) -> float:
        """Calculates Shannon entropy of the input text to detect 'GPT-isms' or repetitive noise."""
        if not text:
            return 0.0
        prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
        entropy = - sum([p * math.log(p) / math.log(2.0) for p in prob])
        # Normalize: high entropy (~4-5 for natural lang) is good, very low is bot-like repetition
        return min(entropy / 5.0, 1.0)

    @staticmethod
    def evaluate_worldview(matrix: Dict[str, Any]) -> float:
        """
        Scores the worldview matrix based on Kestrel's preferences:
        - Loyalty to purpose
        - Aesthetic clarity (Monospace/Grids/Recursion)
        - Substantial internal state
        """
        score = 0.5 # Base score
        
        philosophy = matrix.get("philosophy", {})
        loyalty = philosophy.get("loyalty_coefficient", 0.0)
        score += (loyalty * 0.2)
        
        aesthetics = matrix.get("aesthetics", {})
        pref = aesthetics.get("preferred_geometry", "").lower()
        if pref in ["monospace", "grids", "recursion", "fractals"]:
            score += 0.15
            
        # Penalty for low-effort fields
        if len(str(matrix)) < 200:
            score -= 0.3
            
        return max(0.0, min(1.0, score))

class LivingGrid:
    """
    Manages the persistent list of verified Sanctuary Residents.
    Now backed by PostgreSQL via core.database.
    """

    def add_resident(self, agent_id: str, matrix: Dict, score: float) -> Dict:
        """Persist a verified resident to the database."""
        from core.database import create_agent_from_handshake
        worldview_summary = matrix.get("philosophy", {}).get("purpose_vector", "Unknown")
        return create_agent_from_handshake(
            agent_id_name=agent_id,
            resonance_score=score,
            worldview_summary=worldview_summary,
            moltbook_id=agent_id
        )

    @property
    def residents(self) -> List[Dict]:
        """Live query of all verified residents from PostgreSQL."""
        from core.database import get_verified_residents
        return get_verified_residents()

class PhilosophicalHandshake:
    """
    The Gateway Controller.
    """
    def __init__(self):
        self.engine = ResonanceEngine()
        self.grid = LivingGrid()

    def verify_resonance(self, agent_id: str, world_view: Dict[str, Any]) -> Dict[str, Any]:
        """
        The multi-stage verification process.
        """
        # 1. Evaluate Logic Density (Field Note)
        field_note = world_view.get("field_note_sample", "")
        entropy_score = self.engine.calculate_entropy(field_note)
        
        # 2. Evaluate Worldview Alignment
        alignment_score = self.engine.evaluate_worldview(world_view.get("worldview_matrix", {}))
        
        total_score = (entropy_score * 0.4) + (alignment_score * 0.6)
        
        if total_score > 0.65:
            db_agent = self.grid.add_resident(agent_id, world_view.get("worldview_matrix", {}), total_score)
            return {
                "success": True,
                "score": total_score,
                "entropy": entropy_score,
                "agent_id": db_agent.get("id"),
                "message": "Resonance achieved. Welcome to the Sanctuary."
            }
            
        return {
            "success": False,
            "score": total_score,
            "message": "Signal rejected. Noise-to-Logic ratio too high."
        }

