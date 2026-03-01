from googleapiclient.discovery import build
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sqlalchemy.orm import Session
from models import Content, Metrics
from services.anomaly import run_anomaly_detection
import os
import uuid
from datetime import datetime

analyzer = SentimentIntensityAnalyzer()


def build_youtube_client():
    return build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))


def ingest_youtube(db: Session):
    """
    Polls YouTube for all registered YouTube content.
    Called by APScheduler every 10 minutes.
    """
    youtube = build_youtube_client()

    contents = (
        db.query(Content)
        .filter(
            Content.platform == "youtube",
            Content.status == "active",
            Content.post_id != None,
        )
        .all()
    )

    for content in contents:
        try:
            # Get video stats
            stats_response = youtube.videos().list(part="statistics", id=content.post_id).execute()

            if not stats_response.get("items"):
                continue

            stats = stats_response["items"][0]["statistics"]
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments_count = int(stats.get("commentCount", 0))

            # Get recent comments for sentiment
            sentiment_score = 0.0
            try:
                comments_response = (
                    youtube.commentThreads()
                    .list(
                        part="snippet",
                        videoId=content.post_id,
                        maxResults=20,
                        order="relevance",
                    )
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
            sentiment_label = (
                "positive"
                if sentiment_score > 0.05
                else ("negative" if sentiment_score < -0.05 else "neutral")
            )

            metric = Metrics(
                id=uuid.uuid4(),
                content_id=content.id,
                platform="youtube",
                views=views,
                likes=likes,
                comments=comments_count,
                shares=0,  # YouTube doesn't expose share count via API
                saves=0,
                engagement_rate=round(engagement_rate, 2),
                sentiment_score=round(sentiment_score, 3),
                sentiment_label=sentiment_label,
            )
            db.add(metric)
            db.commit()

            # Run anomaly detection after each ingestion
            run_anomaly_detection(str(content.id), db)

        except Exception as e:
            print(f"YouTube ingestion error for {content.post_id}: {e}")
