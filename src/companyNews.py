# python comapnyNews.py
# Requirements: pip install feedparser requests
import os
import json
import feedparser
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import quote


class CompanyNewsAgent:
    def __init__(self):
        # simple in-memory cache per run
        self.cache: Dict[str, Any] = {}

    # --------- Cache Helpers --------- #
    def _get_cache(self, key: str) -> Optional[Dict[str, Any]]:
        return self.cache.get(key)

    def _set_cache(self, key: str, value: Dict[str, Any]):
        self.cache[key] = value

    # --------- Data Sources --------- #
    def _fetch_yahoo(self, ticker_or_company: str) -> List[Dict[str, Any]]:
        rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={quote(ticker_or_company)}&region=US&lang=en-US"
        feed = feedparser.parse(rss_url)

        articles = []
        for entry in feed.entries[:10]:
            articles.append({
                "title": entry.get("title"),
                "snippet": entry.get("summary"),
                "url": entry.get("link"),
                "date": entry.get("published", str(datetime.utcnow()))
            })
        return articles

    def _fetch_bloomberg(self, company: str) -> List[Dict[str, Any]]:
        rss_url = f"https://www.bloomberg.com/search?query={quote(company)}&rss"
        feed = feedparser.parse(rss_url)

        articles = []
        for entry in feed.entries[:10]:
            articles.append({
                "title": entry.get("title"),
                "snippet": entry.get("summary"),
                "url": entry.get("link"),
                "date": entry.get("published", str(datetime.utcnow()))
            })
        return articles

    def _fetch_google_news(self, company: str) -> List[Dict[str, Any]]:
        rss_url = f"https://news.google.com/rss/search?q={quote(company)}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(rss_url)

        articles = []
        for entry in feed.entries[:10]:
            articles.append({
                "title": entry.get("title"),
                "snippet": entry.get("summary"),
                "url": entry.get("link"),
                "date": entry.get("published", str(datetime.utcnow()))
            })
        return articles

    # --------- Deduplication Helper --------- #
    def _deduplicate(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        unique_articles = []
        for art in articles:
            key = art.get("url") or art.get("title")
            if key and key not in seen:
                seen.add(key)
                unique_articles.append(art)
        return unique_articles

    # --------- Main Fetch Logic --------- #
    def fetch_news(self, session_id: str, organization: str) -> Dict[str, Any]:
        cache_key = f"news:{organization.lower()}"
        cached = self._get_cache(cache_key)
        if cached:
            return {
                "event": "domain.company_news.fetched",
                "session_id": session_id,
                "company_name": organization,
                "data": cached,
                "sources": ["cache"],
                "confidence": 0.9,
            }

        data: List[Dict[str, Any]] = []
        sources: List[str] = []

        try:
            yahoo_news = self._fetch_yahoo(organization)
            if yahoo_news:
                data.extend(yahoo_news)
                sources.append("Yahoo Finance RSS")
        except Exception as e:
            print("⚠️ Yahoo fetch failed:", e)

        try:
            bloomberg_news = self._fetch_bloomberg(organization)
            if bloomberg_news:
                data.extend(bloomberg_news)
                sources.append("Bloomberg RSS")
        except Exception as e:
            print("⚠️ Bloomberg fetch failed:", e)

        if not data:  # fallback
            try:
                google_news = self._fetch_google_news(organization)
                if google_news:
                    data.extend(google_news)
                    sources.append("Google News RSS")
            except Exception as e:
                print("⚠️ Google News fetch failed:", e)

        if not data:
            raise ValueError(f"No news found for {organization}")

        # Deduplicate news
        data = self._deduplicate(data)

        # Cache
        self._set_cache(cache_key, data)

        return {
            "event": "domain.company_news.fetched",
            "session_id": session_id,
            "company_name": organization,
            "data": data,
            "sources": sources,
            "confidence": 0.7 + 0.1 * len(sources),
        }


# ---------------- Example Usage ---------------- #
if __name__ == "__main__":
    agent = CompanyNewsAgent()
    session = "sess_456"
    org = "OpenAI"  # try also "MSFT" for Microsoft

    try:
        news = agent.fetch_news(session, org)
        print(json.dumps(news, indent=2))
    except Exception as e:
        print("Error:", e)
