from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from typing import Optional

class Agent(BaseAgent):
    def _get_agent_id(self) -> str:
        return "demand_analysis"
    
    def health_check(self) -> dict:
        return {"status": "ok", "agent_id": self.agent_id}
    
    def process(self, envelope: EventEnvelope) -> Optional[EventEnvelope]:
        return None
