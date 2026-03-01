from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import Content, Metrics, Alert
from schemas import MitigationResponse
from services.mitigation import get_claude_mitigations

router = APIRouter(prefix="/mitigations", tags=["mitigations"])


@router.get("/{content_id}", response_model=MitigationResponse)
def get_mitigations(content_id: str, db: Session = Depends(get_db)):
    """
    Calls Claude API with content DNA + current metrics to generate
    specific actionable mitigation suggestions.
    """
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    recent_metrics = (
        db.query(Metrics)
        .filter(Metrics.content_id == content_id)
        .order_by(desc(Metrics.recorded_at))
        .limit(10)
        .all()
    )

    if not recent_metrics:
        raise HTTPException(status_code=404, detail="No metrics found yet for this content")

    latest = recent_metrics[0]

    # Determine status
    predicted_eng = content.predicted_engagement or 5.0
    actual_eng = latest.engagement_rate
    diff_pct = ((actual_eng - predicted_eng) / predicted_eng * 100) if predicted_eng > 0 else 0

    if diff_pct < -30:
        status = "underperforming"
        reason = f"Engagement is {abs(diff_pct):.0f}% below predicted baseline of {predicted_eng}%"
    elif diff_pct > 50:
        status = "viral_spike"
        reason = f"Engagement is {diff_pct:.0f}% above predicted — possible viral trend"
    elif latest.sentiment_score < -0.3:
        status = "negative_sentiment"
        reason = f"Sentiment score is {latest.sentiment_score:.2f} — audience reaction is negative"
    else:
        status = "on_track"
        reason = "Content is performing within expected range"

    # Get Claude suggestions
    suggestions = get_claude_mitigations(
        content_dna=content.content_dna,
        platform=content.platform,
        title=content.title,
        predicted_engagement=predicted_eng,
        actual_engagement=actual_eng,
        sentiment_score=latest.sentiment_score,
        views=latest.views,
        status=status,
    )

    # Store suggestions in latest alert if exists
    alert = (
        db.query(Alert)
        .filter(
            Alert.content_id == content_id,
            Alert.is_resolved == False,
        )
        .order_by(desc(Alert.created_at))
        .first()
    )

    if alert:
        alert.mitigation_suggestions = suggestions
        db.commit()

    return MitigationResponse(
        content_id=content_id,
        status=status,
        reason=reason,
        suggestions=suggestions,
    )
