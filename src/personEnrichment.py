# 🚀 How to Run: python person_enrichment_agent.py
# 📦 Requirements: pip install requests beautifulsoup4 duckduckgo-search

import os
import json
import requests
from typing import Dict, Any, List, Optional
from urllib.parse import quote
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from dotenv import load_dotenv

load_dotenv()


class PersonEnrichmentAgent:
    def __init__(self):
        self.hunter_key = os.getenv("HUNTER_API_KEY")
        self.cache: Dict[str, Any] = {}

    # --------- Cache Helpers --------- #
    def _get_cache(self, key: str) -> Optional[Dict[str, Any]]:
        return self.cache.get(key)

    def _set_cache(self, key: str, value: Dict[str, Any]):
        self.cache[key] = value

    # --------- Hunter.io --------- #
    def _fetch_hunter(self, person_name: str, domain: Optional[str] = None) -> Dict[str, Any]:
        if not self.hunter_key or not domain:
            return {}
        url = "https://api.hunter.io/v2/email-finder"
        first_last = person_name.split(" ", 1)
        if len(first_last) != 2:
            return {}
        params = {"first_name": first_last[0], "last_name": first_last[1], "domain": domain, "api_key": self.hunter_key}
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            return {"email": data.get("email"), "linkedin_profile": data.get("linkedin"), "position": data.get("position")}
        return {}

    # --------- Wikipedia --------- #
    def _fetch_wikipedia(self, person_name: str) -> Dict[str, Any]:
        base_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        search_url = "https://en.wikipedia.org/w/api.php"
        result = {}
        # Direct lookup
        resp = requests.get(base_url + quote(person_name))
        if resp.status_code == 200:
            data = resp.json()
            if "extract" in data:
                result["summary"] = data["extract"]
                result["wikipedia_url"] = data.get("content_urls", {}).get("desktop", {}).get("page")
                return result
        # Fallback search API
        params = {"action": "opensearch", "search": person_name, "limit": 1, "namespace": 0, "format": "json"}
        resp = requests.get(search_url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            if len(data) >= 4 and data[1]:
                result["summary"] = data[2][0] if data[2] else None
                result["wikipedia_url"] = data[3][0] if data[3] else None
        return result

    # --------- DuckDuckGo Search --------- #
    def _ddg_search(self, person_name: str, company: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Search DDG for the person and extract top results (title, snippet, URL)
        """
        query = person_name
        if company:
            query += f" {company}"
        extracted = []
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=10)
            for r in results:
                extracted.append({"title": r.get("title"), "snippet": r.get("body"), "url": r.get("href")})
        return extracted

    # --------- LinkedIn --------- #
    def _linkedin_search_url(self, person_name: str) -> str:
        return f"https://www.linkedin.com/search/results/people/?keywords={quote(person_name)}"

    # --------- Main --------- #
    def fetch_person_profile(self, session_id: str, person_name: str, company_domain: Optional[str] = None, company_name: Optional[str] = None) -> Dict[str, Any]:
        cache_key = f"person:{person_name.lower()}"
        cached = self._get_cache(cache_key)
        if cached:
            return {
                "event": "person.profile.fetched",
                "session_id": session_id,
                "person_name": person_name,
                "data": cached,
                "sources": ["cache"],
                "confidence": 0.9,
            }

        data: Dict[str, Any] = {}
        sources: List[str] = []

        # Hunter.io
        hunter_data = self._fetch_hunter(person_name, company_domain)
        if hunter_data:
            data.update(hunter_data)
            sources.append("Hunter.io")

        # Wikipedia
        wiki_data = self._fetch_wikipedia(person_name)
        if wiki_data:
            data.update(wiki_data)
            sources.append("Wikipedia")

        # DDG search
        ddg_results = self._ddg_search(person_name, company_name)
        if ddg_results:
            data["ddg_results"] = ddg_results
            sources.append("DuckDuckGo Search")

        # LinkedIn public search
        data["linkedin_search_url"] = self._linkedin_search_url(person_name)
        sources.append("LinkedIn Search URL")

        # Confidence estimation
        confidence = 0.7 + 0.1 * len(sources)
        self._set_cache(cache_key, data)

        return {
            "event": "person.profile.fetched",
            "session_id": session_id,
            "person_name": person_name,
            "data": data,
            "sources": sources,
            "confidence": min(confidence, 0.95),
        }


# ---------------- Example Usage ---------------- #
if __name__ == "__main__":
    agent = PersonEnrichmentAgent()
    session = "sess_999"
    person_name = "Elon Musk"
    company_domain = "tesla.com"
    company_name = "Tesla"

    profile = agent.fetch_person_profile(session, person_name, company_domain, company_name)
    print(json.dumps(profile, indent=2))
