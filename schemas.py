from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# --- Analytics ---
class SummaryResponse(BaseModel):
    total_views: int
    total_likes: int
    total_comments: int
    avg_engagement: float
    total_shares: int
    saves: int
    views_change_pct: float
    engagement_change_pct: float
    shares_change_pct: float
    saves_change_pct: float


class TimeseriesPoint(BaseModel):
    date: str
    views: int
    engagement_pct: float
    sentiment_score: float
    sentiment_label: str


class PlatformPerformance(BaseModel):
    platform: str
    posts: int
    total_views: int
    total_likes: int
    total_comments: int
    engagement_rate: float
    avg_sentiment: float


class TopContentItem(BaseModel):
    content_id: str
    title: str
    platform: str
    views: int
    engagement_pct: float
    trend_pct: float
    trend_direction: str  # "up" | "down" | "stable"


# --- Trending Discovery (analytics/discover-trending) ---
class TrendingContentItem(BaseModel):
    content_id: Optional[str] = None  # None for external content
    title: str
    platform: str
    post_id: str
    post_url: str
    views: int
    likes: int
    comments: int
    engagement_pct: float
    published_at: Optional[str] = None
    is_external: bool = True  # True = from real platform, False = from our DB
    
    # Platform-specific fields
    channel_title: Optional[str] = None  # YouTube
    thumbnail: Optional[str] = None  # YouTube
    subreddit: Optional[str] = None  # Reddit
    author: Optional[str] = None  # Reddit
