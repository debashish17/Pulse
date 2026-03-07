"""
POST /suggestions  — AI-powered improvement suggestions.
Accepts the same URL as POST /analyze.
Calls Claude with current metrics and returns 3 actionable suggestions.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from database import get_db
from models import Content, Metrics
from services.mitigation import get_claude_mitigations
from routers.analyze import parse_url

router = APIRouter(tags=["suggestions"])


class SuggestionsRequest(BaseModel):
    url: str


@router.post("/suggestions")
def get_suggestions(payload: SuggestionsRequest, db: Session = Depends(get_db)):
    """
    Get AI-powered improvement suggestions for a YouTube or Reddit post.

    Provide the same URL you used with POST /analyze.
    PULSE looks up the latest metrics and asks Claude for 3 specific,
    actionable suggestions based on how the content is performing.

    Tip: Call POST /analyze first to ensure fresh metrics are saved.
    """
    _, post_id = parse_url(payload.url)

    content = db.query(Content).filter(Content.post_id == post_id).first()
    if not content:
        raise HTTPException(
            status_code=404,
            detail="Content not found. Call POST /analyze with this URL first.",
        )

    latest = (
        db.query(Metrics)
        .filter(Metrics.content_id == str(content.id))
        .order_by(desc(Metrics.recorded_at))
        .first()
    )

    if not latest:
        raise HTTPException(
            status_code=404,
            detail="No metrics found yet. Call POST /analyze with this URL first.",
        )

    # Determine performance status
    predicted_eng = content.predicted_engagement or 5.0
    actual_eng = latest.engagement_rate
    diff_pct = ((actual_eng - predicted_eng) / predicted_eng * 100) if predicted_eng > 0 else 0

    if diff_pct < -30:
        status = "underperforming"
        reason = f"Engagement is {abs(diff_pct):.0f}% below predicted baseline of {predicted_eng:.1f}%"
    elif diff_pct > 50:
        status = "viral_spike"
        reason = f"Engagement is {diff_pct:.0f}% above predicted — possible viral trend"
    elif latest.sentiment_score < -0.3:
        status = "negative_sentiment"
        reason = f"Sentiment score is {latest.sentiment_score:.2f} — audience reaction is negative"
    else:
        status = "on_track"
        reason = "Content is performing within expected range"

    suggestions = get_claude_mitigations(
        content_dna=content.content_dna or {},
        platform=content.platform,
        title=content.title,
        predicted_engagement=predicted_eng,
        actual_engagement=actual_eng,
        sentiment_score=latest.sentiment_score,
        views=latest.views,
        status=status,
    )

    return {
        "content_id": str(content.id),
        "platform": content.platform,
        "title": content.title,
        "url": payload.url,
        "status": status,
        "reason": reason,
        "suggestions": suggestions,
    }

