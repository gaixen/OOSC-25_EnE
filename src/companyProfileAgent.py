import os
import json
import redis
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class CompanyProfileAgent:
    def __init__(self):
        self.hunter_key = os.getenv("HUNTER_API_KEY")
        self.cache: Dict[str, Dict[str, Any]] = {}

    def _get_cache(self, key: str) -> Optional[Dict[str, Any]]:
        return self.cache.get(key)

    def _set_cache(self, key: str, value: Dict[str, Any]):
        self.cache[key] = value

    
    def _fetch_hunter(self, domain: str) -> Optional[Dict[str, Any]]:
        """Fetch domain info from Hunter.io"""
        if not self.hunter_key:
            return None
        url = "https://api.hunter.io/v2/domain-search"
        params = {"domain": domain, "api_key": self.hunter_key}
        resp = requests.get(url, params=params)
        return resp.json() if resp.status_code == 200 else None

    def _fetch_wikipedia(self, company: str) -> Optional[Dict[str, Any]]:
        """Fetch structured info from Wikipedia with search fallback"""
        def parse_summary(resp_json):
            return {
                "title": resp_json.get("title"),
                "description": resp_json.get("description"),
                "summary": resp_json.get("extract"),
                "url": resp_json.get("content_urls", {}).get("desktop", {}).get("page"),
            }

        # First try direct summary
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{company}"
        resp = requests.get(url)
        if resp.status_code == 200:
            return parse_summary(resp.json())

        # If direct fetch fails, try search
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": company,
            "format": "json",
        }
        search_resp = requests.get(search_url, params=params)
        if search_resp.status_code == 200:
            search_data = search_resp.json()
            if search_data.get("query", {}).get("search"):
                best_match = search_data["query"]["search"][0]["title"]
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{best_match}"
                sum_resp = requests.get(summary_url)
                if sum_resp.status_code == 200:
                    return parse_summary(sum_resp.json())

        return None

    # --------- Main Fetch Logic --------- #
    def fetch_profile(self, session_id: str, organization: str) -> Dict[str, Any]:
        """
        Fetch company profile from Hunter.io (domain) and Wikipedia (company name).
        Returns a dict in the `domain.company_profile.fetched` format.
        """
        cache_key = f"profile:{organization.lower()}"
        cached = self._get_cache(cache_key)
        if cached:
            return {
                "event": "domain.company_profile.fetched",
                "session_id": session_id,
                "company_name": organization,
                "data": cached,
                "sources": ["cache"],
                "confidence": 0.9,
            }

        data: Dict[str, Any] = {}
        sources: List[str] = []

        # Try Hunter.io (works best if org is a domain)
        if "." in organization:
            hu = self._fetch_hunter(organization)
            if hu:
                data["hunter"] = hu
                sources.append("Hunter.io")

        # Wikipedia fallback
        wiki = self._fetch_wikipedia(organization)
        if wiki:
            data["wikipedia"] = wiki
            sources.append("Wikipedia")


        if not data:
            raise ValueError(f"No profile data found for {organization}")

        # Cache for next time
        self._set_cache(cache_key, data)

        return {
            "event": "domain.company_profile.fetched",
            "session_id": session_id,
            "company_name": organization,
            "data": data,
            "sources": sources,
            "confidence": 0.8 + 0.05 * len(sources),
        }


if __name__ == "__main__":
    agent = CompanyProfileAgent()
    session = "sess_001"

    # Try a domain (Hunter works best with domains)
    org = "openai.com"

    try:
        profile = agent.fetch_profile(session, org)
        print(json.dumps(profile, indent=2))
    except Exception as e:
        print("Error:", e)
