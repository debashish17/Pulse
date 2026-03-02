from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
from models import Content, Metrics
from schemas import SummaryResponse, TimeseriesPoint, PlatformPerformance, TopContentItem, TrendingContentItem
from typing import List, Optional
from datetime import datetime, timedelta
from services.trending_discovery import get_platform_trending, extract_genre_keywords

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_period_delta(period: str) -> timedelta:
    mapping = {"7d": 7, "14d": 14, "30d": 30, "90d": 90}
    days = mapping.get(period, 14)
    return timedelta(days=days)


@router.get("/summary", response_model=SummaryResponse)
def get_summary(
    period: str = Query("14d", enum=["7d", "14d", "30d", "90d"]),
    content_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Returns top-level KPI cards:
    Total views, avg engagement, total shares, saves — with % change vs previous period.
    """
    delta = get_period_delta(period)
    now = datetime.utcnow()
    current_start = now - delta
    prev_start = current_start - delta

    query = db.query(Metrics)
    if content_id:
        query = query.filter(Metrics.content_id == content_id)

    current = query.filter(Metrics.recorded_at >= current_start).all()
    previous = query.filter(Metrics.recorded_at >= prev_start, Metrics.recorded_at < current_start).all()

    def aggregate(rows):
        if not rows:
            return {"views": 0, "likes": 0, "comments": 0, "engagement": 0.0, "shares": 0, "saves": 0}
        return {
            "views": sum(r.views for r in rows),
            "likes": sum(r.likes for r in rows),
            "comments": sum(r.comments for r in rows),
            "engagement": sum(r.engagement_rate for r in rows) / len(rows),
            "shares": sum(r.shares for r in rows),
            "saves": sum(r.saves for r in rows),
        }

    def pct_change(curr, prev):
        if prev == 0:
            return 0.0
        return round((curr - prev) / prev * 100, 1)

    c = aggregate(current)
    p = aggregate(previous)

    return SummaryResponse(
        total_views=c["views"],
        total_likes=c["likes"],
        total_comments=c["comments"],
        avg_engagement=round(c["engagement"], 2),
        total_shares=c["shares"],
        saves=c["saves"],
        views_change_pct=pct_change(c["views"], p["views"]),
        engagement_change_pct=pct_change(c["engagement"], p["engagement"]),
        shares_change_pct=pct_change(c["shares"], p["shares"]),
        saves_change_pct=pct_change(c["saves"], p["saves"]),
    )


@router.get("/timeseries", response_model=List[TimeseriesPoint])
def get_timeseries(
    period: str = Query("14d"),
    content_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Returns daily views and engagement % for the line chart.
    Groups metrics by day.
    """
    delta = get_period_delta(period)
    since = datetime.utcnow() - delta

    query = db.query(
        func.date(Metrics.recorded_at).label("date"),
        func.sum(Metrics.views).label("views"),
        func.avg(Metrics.engagement_rate).label("engagement_pct"),
        func.avg(Metrics.sentiment_score).label("sentiment_score"),
        # Get most common sentiment label for the day
        func.max(Metrics.sentiment_label).label("sentiment_label"),
    ).filter(Metrics.recorded_at >= since)

    if content_id:
        query = query.filter(Metrics.content_id == content_id)

    rows = query.group_by(func.date(Metrics.recorded_at)).order_by("date").all()

    return [
        TimeseriesPoint(
            date=str(row.date),
            views=row.views or 0,
            engagement_pct=round(row.engagement_pct or 0.0, 2),
            sentiment_score=round(row.sentiment_score or 0.0, 3),
            sentiment_label=row.sentiment_label or "neutral",
        )
        for row in rows
    ]


@router.get("/by-platform", response_model=List[PlatformPerformance])
def get_by_platform(db: Session = Depends(get_db)):
    """
    Returns performance grouped by platform — for bar chart.
    """
    rows = (
        db.query(
            Metrics.platform,
            func.count(func.distinct(Metrics.content_id)).label("posts"),
            func.sum(Metrics.views).label("total_views"),
            func.sum(Metrics.likes).label("total_likes"),
            func.sum(Metrics.comments).label("total_comments"),
            func.avg(Metrics.engagement_rate).label("avg_engagement"),
            func.avg(Metrics.sentiment_score).label("avg_sentiment"),
        )
        .group_by(Metrics.platform)
        .all()
    )

    return [
        PlatformPerformance(
            platform=row.platform,
            posts=row.posts,
            total_views=row.total_views or 0,
            total_likes=row.total_likes or 0,
            total_comments=row.total_comments or 0,
            engagement_rate=round(row.avg_engagement or 0.0, 2),
            avg_sentiment=round(row.avg_sentiment or 0.0, 3),
        )
        for row in rows
    ]


@router.get("/top-content", response_model=List[TopContentItem])
def get_top_content(limit: int = 10, platform: str = None, db: Session = Depends(get_db)):
    """
    Returns top performing content items — for the table.
    Computes trend by comparing recent metrics to older metrics.
    
    Args:
        limit: Number of top items to return
        platform: Optional filter (e.g., 'youtube', 'reddit') - omit to see all platforms
    """
    query = db.query(Content).filter(Content.status == "active")
    
    # Apply platform filter if specified
    if platform:
        query = query.filter(Content.platform == platform)
    
    contents = query.all()
    results = []

    for content in contents:
        recent = (
            db.query(Metrics)
            .filter(Metrics.content_id == content.id)
            .order_by(desc(Metrics.recorded_at))
            .limit(5)
            .all()
        )

        if not recent:
            continue

        older = (
            db.query(Metrics)
            .filter(Metrics.content_id == content.id)
            .order_by(Metrics.recorded_at)
            .limit(5)
            .all()
        )

        recent_eng = sum(r.engagement_rate for r in recent) / len(recent)
        older_eng = sum(r.engagement_rate for r in older) / len(older) if older else recent_eng
        trend_pct = round((recent_eng - older_eng) / older_eng * 100, 1) if older_eng > 0 else 0.0
        trend_direction = "up" if trend_pct > 0.5 else ("down" if trend_pct < -0.5 else "stable")

        results.append(
            TopContentItem(
                content_id=str(content.id),
                title=content.title,
                platform=content.platform,
                views=sum(r.views for r in recent),
                engagement_pct=round(recent_eng, 1),
                trend_pct=trend_pct,
                trend_direction=trend_direction,
            )
        )

    results.sort(key=lambda x: x.views, reverse=True)
    return results[:limit]


@router.get("/discover-trending", response_model=List[TrendingContentItem])
def discover_trending_content(
    content_id: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Discover real trending content from actual platforms (YouTube, Reddit, etc.).
    
    This endpoint fetches LIVE trending content from the real platforms, not from your database.
    Use this for competitive intelligence and benchmarking.
    
    Args:
        content_id: Optional - Use your content as reference to find similar trending content
        platform: Optional - Specific platform (youtube, reddit). If omitted, uses platform from content_id
        limit: Number of trending items to return (default: 10)
    
    Returns:
        List of real trending content from the platform with stats
        
    Examples:
        GET /analytics/discover-trending?content_id=xxx  
            → Finds trending content in same genre as your content
        
        GET /analytics/discover-trending?platform=youtube&limit=5  
            → Top 5 trending YouTube videos overall
        
        GET /analytics/discover-trending?content_id=xxx&platform=youtube  
            → YouTube trending in your content's genre
    """
    genre_keywords = None
    target_platform = platform
    
    # If content_id provided, extract genre and platform
    if content_id:
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Extract genre keywords from content DNA
        if content.content_dna:
            genre_keywords = extract_genre_keywords(content.content_dna)
        
        # Use content's platform if not explicitly specified
        if not target_platform:
            target_platform = content.platform
    
    # Validate platform
    if not target_platform:
        raise HTTPException(
            status_code=400,
            detail="Either content_id or platform must be provided"
        )
    
    # Fetch trending content from the real platform
    trending_results = get_platform_trending(
        platform=target_platform,
        genre_keywords=genre_keywords,
        limit=limit
    )
    
    if not trending_results:
        # Return empty list with helpful message via exception
        if target_platform not in ["youtube", "reddit"]:
            raise HTTPException(
                status_code=501,
                detail=f"Trending discovery not yet implemented for {target_platform}. "
                       f"Currently supported: youtube, reddit"
            )
        else:
            # API might be down or no results
            return []
    
    return trending_results
