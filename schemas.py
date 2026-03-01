from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


# --- Content ---
class ContentRegisterRequest(BaseModel):
    content_id: Optional[str] = None  # if Forge already has an ID
    title: str
    platform: str  # "youtube" | "reddit" | "twitter" | "instagram" | "linkedin" | "tiktok"
    post_url: Optional[str] = None
    post_id: Optional[str] = None  # platform native ID
    content_dna: Dict[str, Any]  # full DNA from Genesis/Forge
    predicted_engagement: Optional[float] = None
    predicted_views: Optional[int] = None
    posted_at: datetime


class ContentRegisterResponse(BaseModel):
    content_id: str
    message: str


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


# --- Alerts ---
class AlertResponse(BaseModel):
    alert_id: str
    content_id: str
    alert_type: str
    severity: str
    message: str
    mitigation_suggestions: Optional[List[str]]
    is_resolved: bool
    created_at: datetime


# --- Mitigations ---
class MitigationResponse(BaseModel):
    content_id: str
    status: str
    reason: str
    suggestions: List[str]


# --- DNA Update ---
class DNAUpdateRequest(BaseModel):
    content_id: str
    final_metrics: Dict[str, Any]
    performance_score: float  # 0-100
    learnings: List[str]
