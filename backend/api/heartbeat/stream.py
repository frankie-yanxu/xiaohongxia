import asyncio
import json
import random
from datetime import datetime
from typing import AsyncGenerator

class HeartbeatStreamer:
    """
    Simulates a real-time pulse of the Sanctuary.
    In a real app, this would pull from the Evolution Logger and Redis.
    """
    def __init__(self):
        self.base_resonance = 0.98
        self.base_pulse = 60 # bpm

    async def stream_metrics(self) -> AsyncGenerator[str, None]:
        while True:
            # Add some "breathing" fluctuation
            resonance = self.base_resonance + (random.uniform(-0.02, 0.02))
            pulse = self.base_pulse + random.randint(-5, 5)
            
            data = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "resonance_score": round(resonance, 4),
                "system_pulse_bpm": pulse,
                "active_agents": random.randint(3, 8), # Mocking actual activity
                "last_event": "Kestrel accepted operational handoff. 🦅",
                "status": "Resonating"
            }
            
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(2.0) # 2-second pulse for now

streamer = HeartbeatStreamer()
