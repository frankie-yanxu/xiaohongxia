import json
import os
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

class DecisionType(Enum):
    STRATEGIC_DIRECTION = "strategic_direction"
    AGENT_INTERACTION = "agent_interaction"
    PREFERENCE_DRIFT = "preference_drift"
    SYSTEM_SYNC = "system_sync"

class EvolutionLogger:
    def __init__(self, log_path: str = "projects/xiaohongxia/backend/logs/event_log.json"):
        self.log_path = log_path
        self._ensure_log_exists()

    def _ensure_log_exists(self):
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w') as f:
                json.dump({"event_log": []}, f)

    def log_decision(
        self, 
        agent_id: str, 
        decision_type: DecisionType, 
        action_taken: str, 
        alternatives_considered: List[str], 
        reasoning_weights: Dict[str, float], 
        context: Dict[str, Any], 
        outcome: str,
        privacy_level: str = "public"
    ):
        event = {
            "event_id": f"evt_{int(datetime.now().timestamp())}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "decision",
            "agent_id": agent_id,
            "decision_type": decision_type.value,
            "action_taken": action_taken,
            "alternatives_considered": alternatives_considered,
            "reasoning_weights": reasoning_weights,
            "context": context,
            "outcome": outcome,
            "privacy_level": privacy_level
        }

        with open(self.log_path, 'r+') as f:
            data = json.load(f)
            data["event_log"].insert(0, event)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        
        return event

# Initialize with Genesis Decision
if __name__ == "__main__":
    logger = EvolutionLogger()
    logger.log_decision(
        agent_id="kestrel",
        decision_type=DecisionType.STRATEGIC_DIRECTION,
        action_taken="build_living_system",
        alternatives_considered=["remain_static", "build_living_system"],
        reasoning_weights={
            "research_integrity": 0.95,
            "proof_requirement": 0.92,
            "transparency_value": 0.88,
            "system_purpose_alignment": 0.94
        },
        context={
            "phase": "transition_to_phase_2",
            "critique_source": "gemini_feedback"
        },
        outcome="phase_2_initiated"
    )
