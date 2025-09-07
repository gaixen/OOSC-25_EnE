import os
import time
import json
from typing import List, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

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
    def __init__(self, gemini_api_key: str = None):
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.agent_id = "SuggestionGeneratorAgent"
        
        if not self.gemini_api_key:
            print("❌ SUGGESTION AGENT: No Gemini API key found! Checked GEMINI_API_KEY and GOOGLE_API_KEY")
            print("❌ SUGGESTION AGENT: Will use fallback suggestions only")
            self.llm = None
        else:
            try:
                # Configure Gemini
                genai.configure(api_key=self.gemini_api_key)
                self.llm = genai.GenerativeModel('gemini-2.0-flash')
                print("✅ SUGGESTION AGENT: Gemini API configured successfully")
            except Exception as e:
                print(f"❌ SUGGESTION AGENT: Failed to configure Gemini: {e}")
                self.llm = None

    def generate_suggestions(self, domain_info: Dict[str, Any], utterances: List[str]) -> Dict[str, Any]:
        """Generate contextual AI suggestions based on extracted entities and conversation"""
        
        print(f"🤖 SUGGESTION AGENT: Received domain_info structure: {list(domain_info.keys()) if isinstance(domain_info, dict) else type(domain_info)}")
        print(f"🤖 SUGGESTION AGENT: Utterances count: {len(utterances)}")
        
        # Extract company and person data from nested structure
        companies_mentioned = []
        people_mentioned = []
        news_data = []
        
        if isinstance(domain_info, dict):
            # Iterate through entities in domain_info
            for entity_name, entity_data in domain_info.items():
                if isinstance(entity_data, dict):
                    # Extract company news
                    if 'company_news' in entity_data:
                        company_news = entity_data['company_news']
                        if isinstance(company_news, dict):
                            news_articles = company_news.get('data', [])
                            if news_articles:
                                news_data.extend(news_articles)
                                companies_mentioned.append(entity_name)
                    
                    # Extract company profile
                    if 'company_profile' in entity_data:
                        companies_mentioned.append(entity_name)
                    
                    # Extract market competitor data
                    if 'market_competitor' in entity_data:
                        companies_mentioned.append(entity_name)
                    
                    # Extract person enrichment
                    if 'person_enrichment' in entity_data:
                        people_mentioned.append(entity_name)

        # Clean and join utterances
        conversation_context = " ".join([u for u in utterances if u.strip()])
        
        print(f"🤖 SUGGESTION AGENT: Extracted data:")
        print(f"   - Companies: {companies_mentioned}")
        print(f"   - People: {people_mentioned}")  
        print(f"   - News articles: {len(news_data)}")
        print(f"   - Conversation: '{conversation_context}'")
        
        # Create comprehensive prompt for contextual answers
        prompt = f"""You are an expert AI assistant with access to real-time business intelligence. The user has asked a question or made a statement during a meeting, and you have gathered comprehensive data to provide informed, contextual responses.

USER'S QUESTION/STATEMENT:
{conversation_context}

COMPREHENSIVE BUSINESS INTELLIGENCE GATHERED:
- Companies Mentioned: {', '.join(set(filter(None, companies_mentioned))) if companies_mentioned else 'None'}
- People Mentioned: {', '.join(set(filter(None, people_mentioned))) if people_mentioned else 'None'}
- Available News Articles: {len(news_data)} recent articles
- Data Sources: Company profiles, market intelligence, news feeds, person enrichment

COMPLETE INTELLIGENCE DATA:
{json.dumps(domain_info, indent=2) if domain_info else 'No detailed intelligence available'}

RECENT NEWS INTELLIGENCE:
{json.dumps(news_data[:5], indent=2) if news_data else 'No recent news intelligence'}

TASK: You must provide direct, intelligent responses to the user's question/statement by:

1. DIRECTLY ANSWERING their question using the gathered intelligence data
2. Incorporating specific facts, numbers, and details from the business intelligence
3. Referencing recent news and developments that are relevant
4. Providing actionable insights based on the real data gathered
5. Being conversational and helpful, not just listing talking points

Please provide your response as a JSON array with this exact structure:
[
  {{
    "suggestion": "Your direct, intelligent answer to their question incorporating the gathered data",
    "context": "Explanation of which specific data sources and intelligence informed this response",
    "confidence": 0.90,
    "references": ["Specific data source 1", "Specific data source 2", "Recent news article"],
    "type": "intelligent_response"
  }}
]

Generate responses that directly address what the user said/asked, augmented with the real intelligence data you have access to. Make it sound like you have deep knowledge because you actually do have the data. Return ONLY the JSON array, no additional text."""

        try:
            # Check if Gemini is available
            if not self.llm:
                raise Exception("Gemini API not configured - missing API key")
                
            print(f"🤖 SUGGESTION AGENT: Sending prompt to Gemini (length: {len(prompt)} chars)")
            response = self.llm.generate_content(prompt)
            response_text = response.text.strip()
            print(f"🤖 SUGGESTION AGENT: Received Gemini response (length: {len(response_text)} chars)")
            
            # Clean markdown formatting if present
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            suggestions_data = json.loads(response_text)
            
            # Ensure it's a list
            if not isinstance(suggestions_data, list):
                suggestions_data = [suggestions_data]
            
            # Format suggestions for the UI
            formatted_suggestions = []
            for idx, suggestion in enumerate(suggestions_data):
                formatted_suggestions.append({
                    "id": f"intelligent_response_{int(time.time())}_{idx}",
                    "talkingPoint": suggestion.get("suggestion", ""),
                    "context": suggestion.get("context", ""),
                    "confidenceScore": suggestion.get("confidence", 0.8),
                    "source": ", ".join(suggestion.get("references", ["AI Generated with Business Intelligence"])),
                    "agentName": "AI Intelligence Assistant",
                    "type": suggestion.get("type", "intelligent_response"),
                    "provenance": f"Intelligent response generated using real-time business data for: {', '.join(set(filter(None, companies_mentioned + people_mentioned)))}\nData Sources: {suggestion.get('context', '')}\nConfidence: {suggestion.get('confidence', 0.8)}"
                })
            
            outputs = {
                "suggestions": formatted_suggestions,
                "raw_suggestions": suggestions_data,
                "context_used": {
                    "companies": companies_mentioned,
                    "people": people_mentioned,
                    "news_count": len(news_data),
                    "intelligence_sources": list(domain_info.keys()) if isinstance(domain_info, dict) else []
                }
            }
            
            print(f"🤖 SUGGESTION AGENT: Generated {len(formatted_suggestions)} intelligent responses successfully")
            return provenance_envelope(
                self.agent_id, 
                {"domain_info": domain_info, "utterances": utterances}, 
                outputs, 
                0.9, 
                ["GeminiLLM", "EntityExtraction", "CompanyNews", "PersonEnrichment"]
            )
            
        except Exception as e:
            print(f"❌ SUGGESTION AGENT: Suggestion generation error: {e}")
            print(f"❌ SUGGESTION AGENT: Domain info was: {domain_info}")
            print(f"❌ SUGGESTION AGENT: Prompt used: {prompt[:200]}...")
            
            # Create contextual fallback response
            user_question = conversation_context if conversation_context.strip() else "your question"
            entities_context = ', '.join(companies_mentioned + people_mentioned) if companies_mentioned + people_mentioned else 'the topics discussed'
            
            fallback_suggestions = [{
                "id": f"fallback_{int(time.time())}",
                "talkingPoint": f"Regarding {user_question}, I can see we have information about {entities_context}. While I'm processing the complete intelligence data, I can tell you that we have {len(news_data)} recent news articles and detailed business profiles available to provide a comprehensive response.",
                "context": f"Contextual response using available data: {len(companies_mentioned)} companies, {len(people_mentioned)} people, {len(news_data)} news articles",
                "confidenceScore": 0.7,
                "source": "Business Intelligence Fallback",
                "agentName": "AI Intelligence Assistant",
                "type": "intelligent_response",
                "provenance": f"Fallback intelligent response using available data\nEntities: {entities_context}\nData Available: {len(domain_info)} intelligence sources\nConfidence: 0.7"
            }]
            
            outputs = {"suggestions": fallback_suggestions}
            return provenance_envelope(self.agent_id, {"domain_info": domain_info, "utterances": utterances}, outputs, 0.7, ["FallbackLogic"])


# Example usage
if __name__ == "__main__":
    agent = SuggestionGeneratorAgent()
    domain_info = {"Meta": {"company_profile": {"summary": "Leading social media company"}, "company_news": {"data": [{"title": "Meta announces new AI initiative"}]}}}
    utterances = ["Mark Zuckerberg is the CEO of Meta"]
    
    result = agent.generate_suggestions(domain_info, utterances)
    suggestions = result.get('outputs', {}).get('suggestions', [])
    print(f"Generated {len(suggestions)} suggestions")
    for s in suggestions:
        print(f"- {s['talkingPoint']}")
