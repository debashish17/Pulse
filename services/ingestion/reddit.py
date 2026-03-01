import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sqlalchemy.orm import Session
from models import Content, Metrics
from services.anomaly import run_anomaly_detection
import os
import uuid
from datetime import datetime

analyzer = SentimentIntensityAnalyzer()


def fetch_reddit_public_data(subreddit: str, keyword: str):
    """
    Fetch Reddit data using public JSON API (no authentication required)
    """
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {
        "q": keyword,
        "sort": "hot",
        "limit": 100,
        "t": "month"
    }
    headers = {
        "User-Agent": "PULSE Analytics Bot/1.0"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching Reddit data: {e}")
        return None


def fetch_reddit_post_by_id(post_id: str):
    """
    Fetch specific Reddit post by ID using public JSON API
    post_id should be just the ID (e.g., "abc123") without "t3_" prefix
    """
    # Reddit post URLs: https://www.reddit.com/comments/{post_id}.json
    url = f"https://www.reddit.com/comments/{post_id}.json"
    headers = {
        "User-Agent": "PULSE Analytics Bot/1.0"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Reddit returns array: [post_data, comments_data]
        if data and len(data) > 0:
            post_data = data[0]["data"]["children"][0]["data"]
            comments_data = data[1]["data"]["children"] if len(data) > 1 else []
            return post_data, comments_data
        return None, None
    except Exception as e:
        print(f"Error fetching Reddit post {post_id}: {e}")
        return None, None


def ingest_reddit(db: Session):
    """
    Polls Reddit for all registered Reddit content using public JSON API.
    Called by APScheduler every 10 minutes.
    """
    contents = (
        db.query(Content)
        .filter(
            Content.platform == "reddit",
            Content.status == "active",
            Content.post_id != None,
        )
        .all()
    )

    for content in contents:
        try:
            # Remove "t3_" prefix if present
            post_id = content.post_id.replace("t3_", "")
            
            post_data, comments_data = fetch_reddit_post_by_id(post_id)
            
            if not post_data:
                print(f"No data found for Reddit post {post_id}")
                continue

            # Extract metrics
            upvotes = post_data.get("score", 0)
            comments_count = post_data.get("num_comments", 0)
            upvote_ratio = post_data.get("upvote_ratio", 0.5)
            
            # Reddit doesn't provide view count via public API, estimate from engagement
            # Typical conversion: 1% of viewers upvote, so views ~= upvotes * 100
            views = upvotes * 100 if upvotes > 0 else comments_count * 50

            # Sentiment from comments
            sentiment_score = 0.0
            comment_texts = []
            
            for comment in comments_data[:20]:  # Top 20 comments
                if comment.get("kind") == "t1":  # Regular comment
                    body = comment["data"].get("body", "")
                    if body and body not in ["[deleted]", "[removed]"]:
                        comment_texts.append(body)
            
            if comment_texts:
                scores = [analyzer.polarity_scores(t)["compound"] for t in comment_texts]
                sentiment_score = sum(scores) / len(scores)

            # Calculate engagement rate
            engagement_rate = (
                ((upvotes + comments_count) / views * 100)
                if views and views > 0
                else (upvote_ratio * 10)
            )
            
            sentiment_label = (
                "positive"
                if sentiment_score > 0.05
                else ("negative" if sentiment_score < -0.05 else "neutral")
            )

            metric = Metrics(
                id=uuid.uuid4(),
                content_id=content.id,
                platform="reddit",
                views=views,
                likes=upvotes,
                comments=comments_count,
                shares=0,
                saves=0,
                engagement_rate=round(engagement_rate, 2),
                sentiment_score=round(sentiment_score, 3),
                sentiment_label=sentiment_label,
            )
            db.add(metric)
            db.commit()

            run_anomaly_detection(str(content.id), db)
            
            print(f"✓ Reddit ingestion successful for {post_id}: {views} views, {sentiment_label} sentiment")

        except Exception as e:
            print(f"Reddit ingestion error for {content.post_id}: {e}")
