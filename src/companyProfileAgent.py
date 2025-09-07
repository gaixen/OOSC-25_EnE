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

        # Clean company name - remove .com if present for Wikipedia search
        clean_company = company.replace('.com', '').replace('.', ' ').title()
        
        # Special handling for common company names
        if clean_company.lower() == 'meta':
            clean_company = 'Meta Platforms'
        elif clean_company.lower() == 'google':
            clean_company = 'Google'
        elif clean_company.lower() == 'microsoft':
            clean_company = 'Microsoft'
        
        print(f"🔍 Wikipedia: Searching for '{clean_company}' (from original: '{company}')")
        
        # First try direct summary with cleaned name
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_company}"
        resp = requests.get(url)
        if resp.status_code == 200:
            return parse_summary(resp.json())

        # If direct fetch fails, try search with cleaned name
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": clean_company,
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

        # Try Hunter.io (works with domains)
        if "." in organization:
            try:
                hu = self._fetch_hunter(organization)
                if hu and hu.get('data'):
                    data["hunter"] = hu
                    sources.append("Hunter.io")
                    print(f"✅ Hunter.io found data for {organization}")
            except Exception as e:
                print(f"⚠️ Hunter.io failed for {organization}: {e}")
        else:
            # If no dot, try adding .com for Hunter.io
            domain_version = f"{organization.lower()}.com"
            try:
                hu = self._fetch_hunter(domain_version)
                if hu and hu.get('data'):
                    data["hunter"] = hu
                    sources.append("Hunter.io")
                    print(f"✅ Hunter.io found data for {domain_version} (converted from {organization})")
            except Exception as e:
                print(f"⚠️ Hunter.io failed for {domain_version}: {e}")

        # Always try Wikipedia (works with company names)
        try:
            wiki = self._fetch_wikipedia(organization)
            if wiki and wiki.get('summary'):
                data["wikipedia"] = wiki
                sources.append("Wikipedia")
                print(f"✅ Wikipedia found data for {organization}")
        except Exception as e:
            print(f"⚠️ Wikipedia failed for {organization}: {e}")

        if not data:
            # More specific error message
            domain_part = organization if "." in organization else f"{organization}.com"
            raise ValueError(f"No profile data found for {organization}. Tried Hunter.io with '{domain_part}' and Wikipedia with company name.")

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
