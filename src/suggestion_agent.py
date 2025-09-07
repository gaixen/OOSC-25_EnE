import os
import time
from typing import List, Dict, Any
import requests

# Provenance envelope structure
def provenance_envelope(agent_id: str, inputs: Dict[str, Any], outputs: Dict[str, Any], confidence: float, sources: List[str]) -> Dict[str, Any]:
    return {
        "agent_id": agent_id,
        "timestamp": time.time(),
        "inputs": inputs,
        "outputs": outputs,
        "confidence": confidence,
        "sources": sources,
    }

class SuggestionGeneratorAgent:
    def __init__(self, gemini_api_key: str):
        self.gemini_api_key = gemini_api_key
        self.agent_id = "SuggestionGeneratorAgent"

    def generate_suggestions(self, domain_info: Dict[str, Any], utterances: List[str]) -> Dict[str, Any]:
        prompt = f"Domain Info: {domain_info}\nUtterances: {utterances}\nGenerate 1-3 talking points."
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 256}
        }
        params = {"key": self.gemini_api_key}
        response = requests.post(url, headers=headers, params=params, json=data)
        suggestions = []
        if response.status_code == 200:
            result = response.json()
            text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            suggestions = [s.strip() for s in text.split("\n") if s.strip()]
        outputs = {"suggestions": suggestions}
        return provenance_envelope(self.agent_id, {"domain_info": domain_info, "utterances": utterances}, outputs, 0.8, ["DomainAgent", "GeminiLLM"])

# Example usage
if __name__ == "__main__":
    gemini_api_key = os.getenv("GEMINI_API_KEY", "demo-key")
    agent = SuggestionGeneratorAgent(gemini_api_key)
    domain_info = {"summary": "Acme is a leading provider of widgets. Recent news: new product launch."}
    utterances = ["Tell me about Acme's new product."]
    envelope = agent.generate_suggestions(domain_info, utterances)
    print(envelope)
