from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .news_service import NewsService

app = FastAPI(title="Positive News API", version="0.1.0")
news_service = NewsService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"ok": True}


@app.get("/api/news/status")
def get_news_status():
    return {
        "provider": "NewsAPI",
        "live_data_enabled": news_service.live_data_enabled,
        "message": (
            "Live NewsAPI is enabled."
            if news_service.live_data_enabled
            else (
                "Live NewsAPI key is present, but API requests are currently failing or rate-limited. "
                "Using fallback demo stories."
            )
        ),
    }


@app.get("/api/news/weekly-highlights")
async def get_weekly_highlights():
    return {
        "highlights": await news_service.get_weekly_highlights(),
        "live_data_enabled": news_service.live_data_enabled,
    }


@app.get("/api/news/location-stories")
async def get_location_stories(location_id: str = Query(...)):
    return {
        "location_id": location_id,
        "stories": await news_service.get_location_stories(location_id),
        "live_data_enabled": news_service.live_data_enabled,
    }
