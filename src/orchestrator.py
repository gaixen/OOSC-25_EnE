import asyncio
import os
from typing import Dict, Any, List
from voice import AssemblyAIRealtimeTranscriber
from entityExtractor import InfoExtractionAgent
from companyProfileAgent import CompanyProfileAgent
from companyNews import CompanyNewsAgent
from marketCompetitor import CompetitorMarketAIAgent
from personEnrichment import PersonEnrichmentAgent
from suggestion_agent import SuggestionGeneratorAgent
from ranking_agent import RankingAgent
from ui_agent import UIAgent

# --- Config ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "demo-key")
WS_URL = os.getenv("UI_WS_URL", "ws://localhost:8000/ws")

# --- Orchestrator ---
class Orchestrator:
    def __init__(self):
        self.suggestion_agent = SuggestionGeneratorAgent(GEMINI_API_KEY)
        self.ranking_agent = RankingAgent()
        self.ui_agent = UIAgent(WS_URL)
        self.person_enrichment = PersonEnrichmentAgent()
        self.company_profile_agent = CompanyProfileAgent()
        self.company_news_agent = CompanyNewsAgent()
        self.competitor_agent = CompetitorMarketAIAgent()
        self.entity_extractor = InfoExtractionAgent()

    async def process_meeting(self, audio_path: str, session_id: str):
        # 1. Transcribe audio (assuming you have a method to get transcript from AssemblyAIRealtimeTranscriber)
        # For demo, let's assume you have a function to get transcript from a .wav file
        # Replace with your actual method if needed
        # Example: utterances = AssemblyAIRealtimeTranscriber(api_key).transcribe_file(audio_path)
        utterances = []  # TODO: Replace with actual transcription logic

        # 2. Extract entities
        entities_result = self.entity_extractor.process_text(" ".join(utterances))
        entities = entities_result.get("extracted_entities", [])

        # 3. Fetch domain/company info
        domain_info = {}
        for entity in entities:
            if entity["type"] == "ORG":
                profile = self.company_profile_agent.fetch_profile(session_id, entity["name"])
                news = self.company_news_agent.fetch_news(session_id, entity["name"])
                competitors = self.competitor_agent.fetch_competitors(session_id, entity["name"])
                domain_info = {
                    "profile": profile,
                    "news": news,
                    "competitors": competitors
                }
            elif entity["type"] == "PERSON":
                enrichment = self.person_enrichment.fetch_person_profile(session_id, entity["name"])
                domain_info = {"person": enrichment}

        # 4. Generate suggestions
        envelope = self.suggestion_agent.generate_suggestions(domain_info, utterances)
        suggestions = envelope["outputs"]["suggestions"]
        # 5. Rank suggestions
        ranked_envelope = self.ranking_agent.rank_suggestions(suggestions)
        ranked_suggestions = ranked_envelope["outputs"]["ranked_suggestions"]
        # 6. Send to UI agent
        await self.ui_agent.format_and_send(ranked_suggestions, session_id)

# --- Example usage ---
if __name__ == "__main__":
    orchestrator = Orchestrator()
    audio_path = "demo.wav"
    session_id = "sess_001"
    asyncio.run(orchestrator.process_meeting(audio_path, session_id))
