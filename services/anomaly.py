from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import Content, Metrics, Alert
from typing import Optional
import uuid
from datetime import datetime


def run_anomaly_detection(content_id: str, db: Session):
    """
    Runs after each ingestion cycle for a content item.
    Checks for 4 anomaly types:
      1. underperforming     — engagement < 70% of predicted
      2. viral_spike         — engagement > 150% of predicted
      3. negative_sentiment  — sentiment score < -0.3
      4. sudden_drop         — engagement dropped > 40% in last 2 readings
    """
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        return

    recent = (
        db.query(Metrics)
        .filter(Metrics.content_id == content_id)
        .order_by(desc(Metrics.recorded_at))
        .limit(10)
        .all()
    )

    if not recent:
        return

    latest = recent[0]
    predicted_eng = content.predicted_engagement or 5.0

    # --- Check 1: Underperforming ---
    if latest.engagement_rate < (predicted_eng * 0.7) and latest.views > 50:
        _create_alert_if_not_exists(
            db,
            content_id,
            "underperforming",
            "high",
            f"'{content.title}' engagement ({latest.engagement_rate:.1f}%) is below predicted ({predicted_eng:.1f}%)",
        )

    # --- Check 2: Viral Spike ---
    elif latest.engagement_rate > (predicted_eng * 1.5):
        _create_alert_if_not_exists(
            db,
            content_id,
            "viral_spike",
            "medium",
            f"'{content.title}' is trending — engagement {latest.engagement_rate:.1f}% vs predicted {predicted_eng:.1f}%",
        )

    # --- Check 3: Negative Sentiment ---
    if latest.sentiment_score < -0.3:
        _create_alert_if_not_exists(
            db,
            content_id,
            "negative_sentiment",
            "critical",
            f"Negative audience sentiment detected (score: {latest.sentiment_score:.2f}) on '{content.title}'",
        )

    # --- Check 4: Sudden Drop ---
    if len(recent) >= 2:
        prev_eng = recent[1].engagement_rate
        if prev_eng > 0:
            drop_pct = (prev_eng - latest.engagement_rate) / prev_eng * 100
            if drop_pct > 40:
                _create_alert_if_not_exists(
                    db,
                    content_id,
                    "sudden_drop",
                    "high",
                    f"Engagement dropped {drop_pct:.0f}% in the last cycle for '{content.title}'",
                )


def _create_alert_if_not_exists(db, content_id, alert_type, severity, message):
    """Only creates alert if same type isn't already open."""
    existing = (
        db.query(Alert)
        .filter(
            Alert.content_id == content_id,
            Alert.alert_type == alert_type,
            Alert.is_resolved == False,
        )
        .first()
    )

    if not existing:
        alert = Alert(
            id=uuid.uuid4(),
            content_id=content_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
        )
        db.add(alert)
        db.commit()
