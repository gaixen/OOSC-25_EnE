# 🚀 How to Run: python competitor_market_ai_agent.py
# 📦 Requirements: pip install requests feedparser beautifulsoup4 google-generativeai
#                  export GEMINI_API_KEY=your_key_here

import os
import json
import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import quote
from typing import Dict, Any, List
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class CompetitorMarketAIAgent:
    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=self.gemini_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    # --------- Cache Helpers --------- #
    def _get_cache(self, key: str):
        return self.cache.get(key)

    def _set_cache(self, key: str, value: Dict[str, Any]):
        self.cache[key] = value

    # --------- Data Sources --------- #
    def _fetch_wikipedia_summary(self, company: str) -> str:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(company)}"
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.json().get("extract", "")
        return ""

    def _scrape_wikipedia_page(self, company: str) -> str:
        """Scrape raw text from Wikipedia page for extra signals."""
        url = f"https://en.wikipedia.org/wiki/{quote(company)}"
        resp = requests.get(url)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            paragraphs = " ".join([p.get_text() for p in soup.select("p")[:5]])
            return paragraphs
        return ""

    def _google_news_competitors(self, company: str) -> List[str]:
        rss_url = f"https://news.google.com/rss/search?q=competitors+of+{quote(company)}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(rss_url)
        return [entry.get("title", "") for entry in feed.entries[:10]]

    # --------- AI Reasoning --------- #
    def _ask_gemini(self, company: str, signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ask Gemini to synthesize competitor and market landscape insights.
        """
        prompt = f"""
You are a market research assistant. Based on the following signals, 
identify the **top 2–4 real competitors** for {company} and 
summarize the overall market landscape.

Company: {company}

--- Wikipedia Summary ---
{signals.get("wiki_summary", "")}

--- Wikipedia Page Text ---
{signals.get("wiki_page", "")}

--- News Headlines ---
{signals.get("news_headlines", [])}

Return JSON with this structure:
{{
  "competitors": ["Competitor1", "Competitor2"],
  "market_trends": ["Short bullet insight 1", "Short bullet insight 2"]
}}
"""
        response = self.model.generate_content(prompt)
        try:
            return json.loads(response.text)
        except Exception:
            # fallback: return raw text wrapped
            return {"competitors": [], "market_trends": [response.text.strip()]}

    # --------- Main Fetch Logic --------- #
    def fetch_competitors(self, session_id: str, organization: str) -> Dict[str, Any]:
        cache_key = f"competitors:{organization.lower()}"
        cached = self._get_cache(cache_key)
        if cached:
            return {
                "event": "domain.competitors.fetched",
                "session_id": session_id,
                "company_name": organization,
                "data": cached,
                "sources": ["cache"],
                "confidence": 0.9,
            }

        signals: Dict[str, Any] = {}
        sources: List[str] = []

        # Wikipedia
        summary = self._fetch_wikipedia_summary(organization)
        if summary:
            signals["wiki_summary"] = summary
            sources.append("Wikipedia Summary")

        page = self._scrape_wikipedia_page(organization)
        if page:
            signals["wiki_page"] = page
            sources.append("Wikipedia Page")

        # Google News
        headlines = self._google_news_competitors(organization)
        if headlines:
            signals["news_headlines"] = headlines
            sources.append("Google News RSS")

        # AI synthesis
        insights = self._ask_gemini(organization, signals)
        data = {
            "competitors": insights.get("competitors", []),
            "market_trends": insights.get("market_trends", []),
        }

        if not data["competitors"] and not data["market_trends"]:
            raise ValueError(f"No competitor/market data found for {organization}")

        self._set_cache(cache_key, data)

        return {
            "event": "domain.competitors.fetched",
            "session_id": session_id,
            "company_name": organization,
            "data": data,
            "sources": sources + ["Gemini AI reasoning"],
            "confidence": 0.85,
        }


# ---------------- Example Usage ---------------- #
if __name__ == "__main__":
    agent = CompetitorMarketAIAgent()
    session = "sess_001"
    org = "Tesla"

    result = agent.fetch_competitors(session, org)
    print(json.dumps(result, indent=2))
