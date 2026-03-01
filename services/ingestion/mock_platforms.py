"""
Mock ingestion for Twitter, Instagram, LinkedIn, TikTok.
Generates realistic data with slight random variation each cycle.
Used in demo when real API keys aren't available.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import Content, Metrics
from services.anomaly import run_anomaly_detection
import uuid
import random
from datetime import datetime

PLATFORM_BASELINES = {
    "twitter": {
        "views_range": (500, 5000),
        "engagement_range": (1.0, 6.0),
        "sentiment_range": (0.1, 0.4),
    },
    "instagram": {
        "views_range": (1000, 15000),
        "engagement_range": (3.0, 12.0),
        "sentiment_range": (0.2, 0.6),
    },
    "linkedin": {
        "views_range": (300, 8000),
        "engagement_range": (2.0, 10.0),
        "sentiment_range": (0.1, 0.5),
    },
    "tiktok": {
        "views_range": (2000, 50000),
        "engagement_range": (5.0, 15.0),
        "sentiment_range": (0.1, 0.5),
    },
}


def ingest_mock(db: Session, platform: str):
    """
    Generates simulated metrics for a given platform.
    Adds slight variation on each cycle to simulate live data.
    """
    if platform not in PLATFORM_BASELINES:
        return

    baseline = PLATFORM_BASELINES[platform]
    contents = (
        db.query(Content)
        .filter(
            Content.platform == platform,
            Content.status == "active",
        )
        .all()
    )

    for content in contents:
        # Get previous metric for continuity
        prev = (
            db.query(Metrics)
            .filter(Metrics.content_id == content.id)
            .order_by(desc(Metrics.recorded_at))
            .first()
        )

        if prev:
            # Grow or shrink slightly from previous
            variation = random.uniform(0.9, 1.15)
            views = int(prev.views * variation)
            engagement_rate = round(max(0.1, prev.engagement_rate * random.uniform(0.85, 1.2)), 2)
            sentiment_score = round(
                min(1.0, max(-1.0, prev.sentiment_score + random.uniform(-0.05, 0.05))), 3
            )
        else:
            views = random.randint(*baseline["views_range"])
            engagement_rate = round(random.uniform(*baseline["engagement_range"]), 2)
            sentiment_score = round(random.uniform(*baseline["sentiment_range"]), 3)

        likes = int(views * engagement_rate / 100 * 0.7)
        comments_count = int(views * engagement_rate / 100 * 0.3)
        sentiment_label = (
            "positive"
            if sentiment_score > 0.05
            else ("negative" if sentiment_score < -0.05 else "neutral")
        )

        metric = Metrics(
            id=uuid.uuid4(),
            content_id=content.id,
            platform=platform,
            views=views,
            likes=likes,
            comments=comments_count,
            shares=int(likes * 0.1),
            saves=int(likes * 0.05),
            engagement_rate=engagement_rate,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
        )
        db.add(metric)
        db.commit()
        run_anomaly_detection(str(content.id), db)
