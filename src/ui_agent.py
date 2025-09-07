import time
from typing import List, Dict, Any
import json
import asyncio
import websockets

def provenance_envelope(agent_id: str, inputs: Dict[str, Any], outputs: Dict[str, Any], confidence: float, sources: List[str]) -> Dict[str, Any]:
    return {
        "agent_id": agent_id,
        "timestamp": time.time(),
        "inputs": inputs,
        "outputs": outputs,
        "confidence": confidence,
        "sources": sources,
    }

class UIAgent:
    def __init__(self, ws_url: str):
        self.agent_id = "UIAgent"
        self.ws_url = ws_url

    async def send_event(self, event: Dict[str, Any]):
        async with websockets.connect(self.ws_url) as websocket:
            await websocket.send(json.dumps(event))

    async def format_and_send(self, ranked_suggestions: List[Dict[str, Any]], session_id: str):
        outputs = {"suggestions": ranked_suggestions}
        envelope = provenance_envelope(self.agent_id, {"session_id": session_id}, outputs, 0.8, ["UIAgent"])
        await self.send_event(envelope)

# Example usage
if __name__ == "__main__":
    ws_url = "ws://localhost:8000/ws"
    agent = UIAgent(ws_url)
    ranked_suggestions = [
        {"suggestion": "Acme's new product is innovative.", "confidence": 0.8, "provenance": ["DomainAgent", "LLMPlanner"]},
        {"suggestion": "Acme leads the widget market.", "confidence": 0.8, "provenance": ["DomainAgent", "LLMPlanner"]}
    ]
    session_id = "sess_123"
    asyncio.run(agent.format_and_send(ranked_suggestions, session_id))
