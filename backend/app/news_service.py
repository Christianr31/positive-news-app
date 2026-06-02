import asyncio
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

from .data import LOCATION_STORIES, WEEKLY_HIGHLIGHTS

# Always load backend/.env (not dependent on terminal working directory)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

NEWS_API_BASE = "https://newsapi.org/v2/everything"
CACHE_TTL_SECONDS = int(os.getenv("NEWS_CACHE_TTL_SECONDS", str(60 * 60 * 24)))

POSITIVE_TERMS = [
    "breakthrough",
    "wins",
    "win",
    "improves",
    "improvement",
    "success",
    "record",
    "expands",
    "growth",
    "innovation",
    "saves",
    "recovery",
    "achievement",
    "community support",
    "renewable",
    "education gains",
]

TRACKED_LOCATIONS = [
    {
        "location_id": "new-york-ny",
        "city": "New York",
        "country": "USA",
        "lat": 40.7128,
        "lng": -74.0060,
        "query": '"New York" OR Manhattan OR Brooklyn OR Queens OR Bronx',
    },
    {
        "location_id": "bronx-ny",
        "city": "Bronx",
        "country": "USA",
        "lat": 40.8448,
        "lng": -73.8648,
        "query": '"Bronx" OR "South Bronx"',
    },
    {
        "location_id": "nairobi-kenya",
        "city": "Nairobi",
        "country": "Kenya",
        "lat": -1.2921,
        "lng": 36.8219,
        "query": '"Nairobi" OR Kenya',
    },
    {
        "location_id": "oslo-norway",
        "city": "Oslo",
        "country": "Norway",
        "lat": 59.9139,
        "lng": 10.7522,
        "query": '"Oslo" OR Norway',
    },
    {
        "location_id": "sao-paulo-brazil",
        "city": "Sao Paulo",
        "country": "Brazil",
        "lat": -23.5505,
        "lng": -46.6333,
        "query": '"Sao Paulo" OR "Sao Paulo state" OR Brazil',
    },
    {
        "location_id": "tokyo-japan",
        "city": "Tokyo",
        "country": "Japan",
        "lat": 35.6762,
        "lng": 139.6503,
        "query": '"Tokyo" OR Japan',
    },
    {
        "location_id": "seoul-south-korea",
        "city": "Seoul",
        "country": "South Korea",
        "lat": 37.5665,
        "lng": 126.9780,
        "query": '"Seoul" OR "South Korea"',
    },
    {
        "location_id": "singapore-singapore",
        "city": "Singapore",
        "country": "Singapore",
        "lat": 1.3521,
        "lng": 103.8198,
        "query": '"Singapore"',
    },
    {
        "location_id": "delhi-india",
        "city": "Delhi",
        "country": "India",
        "lat": 28.6139,
        "lng": 77.2090,
        "query": '"Delhi" OR India',
    },
    {
        "location_id": "sydney-australia",
        "city": "Sydney",
        "country": "Australia",
        "lat": -33.8688,
        "lng": 151.2093,
        "query": '"Sydney" OR Australia',
    },
    {
        "location_id": "cape-town-south-africa",
        "city": "Cape Town",
        "country": "South Africa",
        "lat": -33.9249,
        "lng": 18.4241,
        "query": '"Cape Town" OR "South Africa"',
    },
    {
        "location_id": "lagos-nigeria",
        "city": "Lagos",
        "country": "Nigeria",
        "lat": 6.5244,
        "lng": 3.3792,
        "query": '"Lagos" OR Nigeria',
    },
    {
        "location_id": "cairo-egypt",
        "city": "Cairo",
        "country": "Egypt",
        "lat": 30.0444,
        "lng": 31.2357,
        "query": '"Cairo" OR Egypt',
    },
    {
        "location_id": "london-uk",
        "city": "London",
        "country": "UK",
        "lat": 51.5074,
        "lng": -0.1278,
        "query": '"London" OR "United Kingdom"',
    },
    {
        "location_id": "paris-france",
        "city": "Paris",
        "country": "France",
        "lat": 48.8566,
        "lng": 2.3522,
        "query": '"Paris" OR France',
    },
    {
        "location_id": "berlin-germany",
        "city": "Berlin",
        "country": "Germany",
        "lat": 52.5200,
        "lng": 13.4050,
        "query": '"Berlin" OR Germany',
    },
    {
        "location_id": "madrid-spain",
        "city": "Madrid",
        "country": "Spain",
        "lat": 40.4168,
        "lng": -3.7038,
        "query": '"Madrid" OR Spain',
    },
    {
        "location_id": "rome-italy",
        "city": "Rome",
        "country": "Italy",
        "lat": 41.9028,
        "lng": 12.4964,
        "query": '"Rome" OR Italy',
    },
    {
        "location_id": "amsterdam-netherlands",
        "city": "Amsterdam",
        "country": "Netherlands",
        "lat": 52.3676,
        "lng": 4.9041,
        "query": '"Amsterdam" OR Netherlands',
    },
    {
        "location_id": "stockholm-sweden",
        "city": "Stockholm",
        "country": "Sweden",
        "lat": 59.3293,
        "lng": 18.0686,
        "query": '"Stockholm" OR Sweden',
    },
    {
        "location_id": "toronto-canada",
        "city": "Toronto",
        "country": "Canada",
        "lat": 43.6532,
        "lng": -79.3832,
        "query": '"Toronto" OR Canada',
    },
    {
        "location_id": "mexico-city-mexico",
        "city": "Mexico City",
        "country": "Mexico",
        "lat": 19.4326,
        "lng": -99.1332,
        "query": '"Mexico City" OR Mexico',
    },
    {
        "location_id": "bogota-colombia",
        "city": "Bogota",
        "country": "Colombia",
        "lat": 4.7110,
        "lng": -74.0721,
        "query": '"Bogota" OR Colombia',
    },
    {
        "location_id": "buenos-aires-argentina",
        "city": "Buenos Aires",
        "country": "Argentina",
        "lat": -34.6037,
        "lng": -58.3816,
        "query": '"Buenos Aires" OR Argentina',
    },
    {
        "location_id": "dubai-uae",
        "city": "Dubai",
        "country": "UAE",
        "lat": 25.2048,
        "lng": 55.2708,
        "query": '"Dubai" OR "United Arab Emirates"',
    },
]


class NewsService:
    def __init__(self) -> None:
        self.api_key = os.getenv("NEWS_API_KEY", "").strip()
        self._cache: dict[str, tuple[float, Any]] = {}
        self._ttl_seconds = CACHE_TTL_SECONDS
        self._live_data_enabled = False
        self._request_in_progress: dict[str, asyncio.Task[Any]] = {}
        # Limit to 3 concurrent requests to stay within NewsAPI free tier (~100/day)
        # This allows multiple users while respecting rate limits
        self._semaphore = asyncio.Semaphore(3)

    @staticmethod
    def _today_key(suffix: str) -> str:
        return f"{suffix}:{datetime.now(timezone.utc).date().isoformat()}"

    def _cached(self, key: str) -> Any | None:
        cached = self._cache.get(key)
        if not cached:
            return None
        created_at, value = cached
        if time.time() - created_at > self._ttl_seconds:
            self._cache.pop(key, None)
            return None
        return value

    def _set_cache(self, key: str, value: Any) -> None:
        self._cache[key] = (time.time(), value)

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)

    @property
    def live_data_enabled(self) -> bool:
        return self.has_api_key and self._live_data_enabled

    def _build_positive_query(self, location_query: str) -> str:
        positive_clause = " OR ".join(f'"{term}"' for term in POSITIVE_TERMS)
        return f"({location_query}) AND ({positive_clause})"

    def _news_api_params(self, location_query: str) -> dict[str, Any]:
        one_week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        return {
            "q": self._build_positive_query(location_query),
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 15,
            "from": one_week_ago,
            "apiKey": self.api_key,
        }

    async def _fetch_location_articles_async(self, location_query: str) -> list[dict[str, Any]]:
        """Fetch articles with semaphore to throttle requests within NewsAPI rate limits."""
        if not self.api_key:
            return []
        
        async with self._semaphore:
            params = self._news_api_params(location_query)
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.get(NEWS_API_BASE, params=params)
                response.raise_for_status()
                payload = response.json()
            return payload.get("articles", [])

    @staticmethod
    def _normalize_summary(article: dict[str, Any]) -> str:
        description = article.get("description") or article.get("content") or ""
        description = description.replace("...[+", " ").strip()
        if not description:
            return "No short summary available from this article."
        return description

    @staticmethod
    def _image_url(article: dict[str, Any]) -> str | None:
        url = article.get("urlToImage")
        if not url:
            return None
        return str(url)

    async def get_weekly_highlights(self) -> list[dict[str, Any]]:
        cache_key = self._today_key("weekly-highlights")
        cached = self._cached(cache_key)
        if cached is not None:
            return cached

        # Check if request is already in progress (deduplication)
        if cache_key in self._request_in_progress:
            return await self._request_in_progress[cache_key]

        # Graceful fallback when no key is configured.
        if not self.api_key:
            self._set_cache(cache_key, WEEKLY_HIGHLIGHTS)
            return WEEKLY_HIGHLIGHTS

        # Create task for deduplication
        task = asyncio.create_task(self._fetch_weekly_highlights_concurrent())
        self._request_in_progress[cache_key] = task

        try:
            highlights = await task
        finally:
            self._request_in_progress.pop(cache_key, None)

        self._live_data_enabled = bool(highlights)
        if not highlights:
            highlights = WEEKLY_HIGHLIGHTS

        self._set_cache(cache_key, highlights)
        return highlights

    async def _fetch_weekly_highlights_concurrent(self) -> list[dict[str, Any]]:
        """Fetch highlights from all locations in parallel."""
        tasks = [
            self._fetch_location_articles_async(location["query"])
            for location in TRACKED_LOCATIONS
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        highlights: list[dict[str, Any]] = []
        
        for location, result in zip(TRACKED_LOCATIONS, results):
            try:
                if isinstance(result, Exception):
                    continue
                articles = result
                if not articles:
                    continue
                top = articles[0]
                highlights.append(
                    {
                        "location_id": location["location_id"],
                        "city": location["city"],
                        "country": location["country"],
                        "lat": location["lat"],
                        "lng": location["lng"],
                        "title": top.get("title", "Positive update this week"),
                        "summary": self._normalize_summary(top),
                        "url": top.get("url"),
                        "image_url": self._image_url(top),
                        "source": (top.get("source") or {}).get("name"),
                        "published_at": top.get("publishedAt"),
                    }
                )
            except Exception:
                continue
        
        return highlights

    async def get_location_stories(self, location_id: str) -> list[dict[str, Any]]:
        cache_key = self._today_key(f"location:{location_id}")
        cached = self._cached(cache_key)
        if cached is not None:
            return cached

        # Check if request is already in progress (deduplication)
        if cache_key in self._request_in_progress:
            return await self._request_in_progress[cache_key]

        location = next(
            (loc for loc in TRACKED_LOCATIONS if loc["location_id"] == location_id), None
        )
        if location is None:
            fallback = LOCATION_STORIES.get(location_id, [])
            self._set_cache(cache_key, fallback)
            return fallback

        if not self.api_key:
            fallback = LOCATION_STORIES.get(location_id, [])
            self._set_cache(cache_key, fallback)
            return fallback

        # Create task for deduplication
        task = asyncio.create_task(self._fetch_location_stories_async(location_id, location))
        self._request_in_progress[cache_key] = task

        try:
            stories = await task
        finally:
            self._request_in_progress.pop(cache_key, None)

        self._set_cache(cache_key, stories)
        return stories

    async def _fetch_location_stories_async(self, location_id: str, location: dict[str, Any]) -> list[dict[str, Any]]:
        """Fetch stories for a single location with fallback."""
        try:
            articles = await self._fetch_location_articles_async(location["query"])
        except Exception:
            articles = []

        stories = [
            {
                "id": f"{location_id}-{idx}",
                "title": article.get("title", "Positive local update"),
                "summary": self._normalize_summary(article),
                "url": article.get("url"),
                "image_url": self._image_url(article),
                "source": (article.get("source") or {}).get("name"),
                "published_at": article.get("publishedAt"),
            }
            for idx, article in enumerate(articles[:8], start=1)
        ]

        if not stories:
            stories = LOCATION_STORIES.get(location_id, [])
            self._live_data_enabled = False
        else:
            self._live_data_enabled = True

        return stories
