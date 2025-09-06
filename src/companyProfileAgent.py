import os
import json
import redis
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()


class CompanyProfileAgent:
    def __init__(self):
        # API keys
        self.clearbit_key = os.getenv("CLEARBIT_API_KEY")
        self.crunchbase_key = os.getenv("CRUNCHBASE_API_KEY")
        self.hunter_key = os.getenv("HUNTER_API_KEY")

        # Redis setup
        self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True,
        )

    # --------- Cache Helpers --------- #
    def _get_cache(self, key: str) -> Optional[Dict[str, Any]]:
        cached = self.redis.get(key)
        return json.loads(cached) if cached else None

    def _set_cache(self, key: str, value: Dict[str, Any]):
        self.redis.setex(key, 86400, json.dumps(value))  # 1 day

    # --------- Data Sources --------- #
    def _fetch_clearbit(self, domain: str) -> Optional[Dict[str, Any]]:
        if not self.clearbit_key:
            return None
        url = f"https://company.clearbit.com/v2/companies/find?domain={domain}"
        resp = requests.get(url, auth=(self.clearbit_key, ""))
        return resp.json() if resp.status_code == 200 else None

    def _fetch_crunchbase(self, company: str) -> Optional[Dict[str, Any]]:
        if not self.crunchbase_key:
            return None
        url = f"https://api.crunchbase.com/v3.1/organizations/{company}"
        params = {"user_key": self.crunchbase_key}
        resp = requests.get(url, params=params)
        return resp.json() if resp.status_code == 200 else None

    def _fetch_hunter(self, domain: str) -> Optional[Dict[str, Any]]:
        if not self.hunter_key:
            return None
        url = "https://api.hunter.io/v2/domain-search"
        params = {"domain": domain, "api_key": self.hunter_key}
        resp = requests.get(url, params=params)
        return resp.json() if resp.status_code == 200 else None

    def _fetch_wikipedia(self, company: str) -> Optional[str]:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{company}"
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.json().get("extract")
        return None

    # --------- Main Fetch Logic --------- #
    def fetch_profile(self, session_id: str, organization: str) -> Dict[str, Any]:
        """
        Fetch company profile from multiple sources.
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

        # Try Clearbit (only if org looks like a domain)
        if "." in organization:
            cb = self._fetch_clearbit(organization)
            if cb:
                data["clearbit"] = cb
                sources.append("Clearbit")

        # Try Crunchbase
        cr = self._fetch_crunchbase(organization)
        if cr:
            data["crunchbase"] = cr
            sources.append("Crunchbase")

        # Try Hunter.io (only if domain provided)
        if "." in organization:
            hu = self._fetch_hunter(organization)
            if hu:
                data["hunter"] = hu
                sources.append("Hunter.io")

        # Wikipedia fallback
        wiki = self._fetch_wikipedia(organization)
        if wiki:
            data["wikipedia_summary"] = wiki
            sources.append("Wikipedia")

        if not data:
            raise ValueError(f"No profile data found for {organization}")

        # Cache it
        self._set_cache(cache_key, data)

        return {
            "event": "domain.company_profile.fetched",
            "session_id": session_id,
            "company_name": organization,
            "data": data,
            "sources": sources,
            "confidence": 0.8 + 0.05 * len(sources),
        }


# ---------------- Example Usage ---------------- #
if __name__ == "__main__":
    agent = CompanyProfileAgent()
    session = "sess_123"
    org = "openai"  # can also try "openai.com"

    try:
        profile = agent.fetch_profile(session, org)
        print(json.dumps(profile, indent=2))
    except Exception as e:
        print("Error:", e)
