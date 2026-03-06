from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from typing import Optional
import json, os

class Agent(BaseAgent):
    def _get_agent_id(self) -> str:
        return "skills_extraction"
    
    def health_check(self) -> dict:
        path = "agents/data/fixtures/fallback_scrape_sample.json"
        return {"status": "ok" if os.path.exists(path) else "error", "agent_id": self.agent_id}
    
    def process(self, envelope: EventEnvelope) -> Optional[EventEnvelope]:
        return EventEnvelope.create(envelope.correlation_id, self.agent_id, envelope.payload)
