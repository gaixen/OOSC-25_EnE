import time
from typing import List, Dict, Any

def provenance_envelope(agent_id: str, inputs: Dict[str, Any], outputs: Dict[str, Any], confidence: float, sources: List[str]) -> Dict[str, Any]:
    return {
        "agent_id": agent_id,
        "timestamp": time.time(),
        "inputs": inputs,
        "outputs": outputs,
        "confidence": confidence,
        "sources": sources,
    }

class RankingAgent:
    def __init__(self):
        self.agent_id = "RankingAgent"

    def rank_suggestions(self, suggestions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rank suggestions based on confidence scores and relevance"""
        
        if not suggestions:
            return provenance_envelope(self.agent_id, {"suggestions": []}, {"ranked_suggestions": []}, 0.0, ["RankingAgent"])
        
        # If suggestions are already formatted dictionaries, use them directly
        if isinstance(suggestions[0], dict) and 'confidenceScore' in suggestions[0]:
            ranked_suggestions = sorted(suggestions, key=lambda x: x.get('confidenceScore', 0), reverse=True)
        else:
            # Handle legacy format - convert simple strings to proper format
            ranked_suggestions = []
            for i, suggestion in enumerate(suggestions):
                if isinstance(suggestion, str):
                    ranked_suggestions.append({
                        "id": f"ranked_{int(time.time())}_{i}",
                        "talkingPoint": suggestion,
                        "context": "Legacy suggestion converted to new format",
                        "confidenceScore": 0.7,
                        "source": "Legacy System",
                        "agentName": "AI Suggestion Generator",
                        "type": "insight",
                        "provenance": f"Prompt: Converted legacy suggestion\nEvidence: {suggestion}\nConfidence: 0.7"
                    })
                else:
                    ranked_suggestions.append(suggestion)
            
            # Sort by confidence score
            ranked_suggestions = sorted(ranked_suggestions, key=lambda x: x.get('confidenceScore', 0), reverse=True)
        
        # Add ranking metadata
        for i, suggestion in enumerate(ranked_suggestions):
            suggestion['rank'] = i + 1
            suggestion['ranking_confidence'] = max(0.9 - (i * 0.1), 0.5)  # Decrease confidence for lower ranks
        
        outputs = {"ranked_suggestions": ranked_suggestions}
        
        print(f"📊 Ranked {len(ranked_suggestions)} suggestions by relevance and confidence")
        
        return provenance_envelope(
            self.agent_id, 
            {"suggestions": suggestions}, 
            outputs, 
            0.9, 
            ["RankingAgent", "ConfidenceScoring"]
        )

# Example usage
if __name__ == "__main__":
    agent = RankingAgent()
    suggestions = ["Acme's new product is innovative.", "Acme leads the widget market."]
    envelope = agent.rank_suggestions(suggestions)
    print(envelope)
