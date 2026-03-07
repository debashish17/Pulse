"""
POST /analyze  — One-step content analysis.
User provides a YouTube or Reddit URL.
PULSE auto-detects platform, registers content if new,
fetches live metrics, and returns full analysis.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import Content, Metrics
import re
import uuid
import os
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

router = APIRouter(tags=["analyze"])
analyzer = SentimentIntensityAnalyzer()


class AnalyzeRequest(BaseModel):
    url: str


def parse_url(url: str) -> tuple:
    """Detect platform and extract post_id from a URL."""

    # YouTube: youtube.com/watch?v=VIDEO_ID or youtu.be/VIDEO_ID
    yt = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    if yt:
        return "youtube", yt.group(1)

    # Reddit: reddit.com/r/sub/comments/POST_ID/...
    rd = re.search(r"reddit\.com/r/\w+/comments/([a-z0-9]+)", url)
    if rd:
        return "reddit", rd.group(1)

    raise HTTPException(
        status_code=400,
        detail="Unsupported URL. Supported platforms: YouTube, Reddit",
    )


def fetch_youtube_data(post_id: str) -> dict:
    """Fetch title, thumbnail, and live metrics for a YouTube video."""
    from googleapiclient.discovery import build

    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="YOUTUBE_API_KEY not configured")

    youtube = build("youtube", "v3", developerKey=api_key)

    # Fetch snippet + stats in one API call
    response = youtube.videos().list(part="snippet,statistics", id=post_id).execute()

    if not response.get("items"):
        raise HTTPException(status_code=404, detail=f"YouTube video not found: {post_id}")

    item = response["items"][0]
    snippet = item["snippet"]
    stats = item["statistics"]

    title = snippet.get("title", "Unknown")
    thumbnail = snippet.get("thumbnails", {}).get("high", {}).get("url", "")
    channel = snippet.get("channelTitle", "")
    published_at = snippet.get("publishedAt", datetime.utcnow().isoformat())

    views = int(stats.get("viewCount", 0))
    likes = int(stats.get("likeCount", 0))
    comments_count = int(stats.get("commentCount", 0))

    # Sentiment from top comments
    sentiment_score = 0.0
    try:
        comments_response = (
            youtube.commentThreads()
            .list(part="snippet", videoId=post_id, maxResults=20, order="relevance")
            .execute()
        )
        comment_texts = [
            item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            for item in comments_response.get("items", [])
        ]
        if comment_texts:
            scores = [analyzer.polarity_scores(c)["compound"] for c in comment_texts]
            sentiment_score = sum(scores) / len(scores)
    except Exception:
        pass  # Comments might be disabled

    engagement_rate = ((likes + comments_count) / views * 100) if views > 0 else 0.0

    return {
        "title": title,
        "thumbnail": thumbnail,
        "channel": channel,
        "published_at": published_at,
        "views": views,
        "likes": likes,
        "comments": comments_count,
        "shares": 0,
        "saves": 0,
        "engagement_rate": round(engagement_rate, 2),
        "sentiment_score": round(sentiment_score, 3),
        "sentiment_label": (
            "positive" if sentiment_score > 0.05 else ("negative" if sentiment_score < -0.05 else "neutral")
        ),
    }


def fetch_reddit_data(post_id: str) -> dict:
    """Fetch title and live metrics for a Reddit post."""
    from services.ingestion.reddit import fetch_reddit_post_by_id

    post_data, comments_data = fetch_reddit_post_by_id(post_id)
    if not post_data:
        raise HTTPException(status_code=404, detail=f"Reddit post not found: {post_id}")

    title = post_data.get("title", "Unknown")
    subreddit = post_data.get("subreddit", "")
    upvotes = post_data.get("score", 0)
    comments_count = post_data.get("num_comments", 0)
    upvote_ratio = post_data.get("upvote_ratio", 0.5)

    # Reddit doesn't expose view count publicly — estimate from engagement
    views = upvotes * 100 if upvotes > 0 else comments_count * 50

    # Sentiment from top comments
    sentiment_score = 0.0
    comment_texts = []
    for comment in (comments_data or [])[:20]:
        if comment.get("kind") == "t1":
            body = comment["data"].get("body", "")
            if body and body not in ["[deleted]", "[removed]"]:
                comment_texts.append(body)

    if comment_texts:
        scores = [analyzer.polarity_scores(t)["compound"] for t in comment_texts]
        sentiment_score = sum(scores) / len(scores)

    engagement_rate = (
        ((upvotes + comments_count) / views * 100) if views > 0 else (upvote_ratio * 10)
    )

    return {
        "title": title,
        "thumbnail": None,
        "channel": f"r/{subreddit}",
        "published_at": datetime.utcnow().isoformat(),
        "views": views,
        "likes": upvotes,
        "comments": comments_count,
        "shares": 0,
        "saves": 0,
        "engagement_rate": round(engagement_rate, 2),
        "sentiment_score": round(sentiment_score, 3),
        "sentiment_label": (
            "positive" if sentiment_score > 0.05 else ("negative" if sentiment_score < -0.05 else "neutral")
        ),
    }


def determine_status(actual_eng: float, predicted_eng: float, sentiment_score: float) -> tuple:
    """Returns (status, reason) based on engagement vs prediction and sentiment."""
    diff_pct = ((actual_eng - predicted_eng) / predicted_eng * 100) if predicted_eng > 0 else 0

    if diff_pct < -30:
        return (
            "underperforming",
            f"Engagement ({actual_eng:.1f}%) is {abs(diff_pct):.0f}% below expected baseline of {predicted_eng:.1f}%",
        )
    elif diff_pct > 50:
        return (
            "viral_spike",
            f"Engagement ({actual_eng:.1f}%) is {diff_pct:.0f}% above expected — content is trending!",
        )
    elif sentiment_score < -0.3:
        return (
            "negative_sentiment",
            f"Audience sentiment is negative (score: {sentiment_score:.2f})",
        )
    else:
        return "on_track", "Content is performing within expected range"


@router.post("/analyze")
def analyze_url(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    One-step analysis. Provide a YouTube or Reddit URL — PULSE does the rest.

    - Auto-detects platform from URL
    - Auto-registers content if seen for the first time
    - Fetches live metrics from the platform API
    - Returns metrics, performance status, and reason

    To get AI improvement suggestions, call POST /suggestions with the same URL.
    """
    platform, post_id = parse_url(payload.url)

    # Check if content is already registered
    content = db.query(Content).filter(Content.post_id == post_id).first()

    # Fetch live data from platform
    if platform == "youtube":
        data = fetch_youtube_data(post_id)
    else:
        data = fetch_reddit_data(post_id)

    # Auto-register on first sight
    if not content:
        content = Content(
            id=uuid.uuid4(),
            title=data["title"],
            platform=platform,
            post_id=post_id,
            post_url=payload.url,
            content_dna={},
            posted_at=datetime.utcnow(),
        )
        db.add(content)
        db.commit()
        db.refresh(content)

    # Save new metrics snapshot to DB
    metric = Metrics(
        id=uuid.uuid4(),
        content_id=content.id,
        platform=platform,
        views=data["views"],
        likes=data["likes"],
        comments=data["comments"],
        shares=data["shares"],
        saves=data["saves"],
        engagement_rate=data["engagement_rate"],
        sentiment_score=data["sentiment_score"],
        sentiment_label=data["sentiment_label"],
    )
    db.add(metric)
    db.commit()

    # Determine performance status
    predicted = content.predicted_engagement or 5.0
    status, reason = determine_status(data["engagement_rate"], predicted, data["sentiment_score"])

    return {
        "content_id": str(content.id),
        "platform": platform,
        "title": data["title"],
        "url": payload.url,
        "thumbnail": data.get("thumbnail"),
        "channel": data.get("channel"),
        "metrics": {
            "views": data["views"],
            "likes": data["likes"],
            "comments": data["comments"],
            "engagement_rate": data["engagement_rate"],
            "sentiment_score": data["sentiment_score"],
            "sentiment_label": data["sentiment_label"],
            "recorded_at": datetime.utcnow().isoformat() + "Z",
        },
        "status": status,
        "reason": reason,
    }


@router.get("/analyze/{content_id}/history")
def get_history(content_id: str, db: Session = Depends(get_db)):
    """
    Returns historical metric snapshots for a previously analyzed content item.
    Use the content_id returned from POST /analyze.
    """
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    metrics = (
        db.query(Metrics)
        .filter(Metrics.content_id == content_id)
        .order_by(Metrics.recorded_at.asc())
        .all()
    )

    return {
        "content_id": content_id,
        "title": content.title,
        "platform": content.platform,
        "url": content.post_url,
        "snapshots": [
            {
                "views": m.views,
                "likes": m.likes,
                "comments": m.comments,
                "engagement_rate": m.engagement_rate,
                "sentiment_score": m.sentiment_score,
                "sentiment_label": m.sentiment_label,
                "recorded_at": m.recorded_at.isoformat() + "Z",
            }
            for m in metrics
        ],
    }
