from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import Alert
from schemas import AlertResponse
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=List[AlertResponse])
def get_alerts(content_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns all unresolved alerts, optionally filtered by content."""
    query = db.query(Alert).filter(Alert.is_resolved == False)
    if content_id:
        query = query.filter(Alert.content_id == content_id)
    alerts = query.order_by(desc(Alert.created_at)).all()

    return [
        AlertResponse(
            alert_id=str(a.id),
            content_id=str(a.content_id),
            alert_type=a.alert_type,
            severity=a.severity,
            message=a.message,
            mitigation_suggestions=a.mitigation_suggestions,
            is_resolved=a.is_resolved,
            created_at=a.created_at,
        )
        for a in alerts
    ]


@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: str, db: Session = Depends(get_db)):
    """Marks an alert as resolved."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return {"error": "Alert not found"}
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    db.commit()
    return {"message": "Alert resolved"}
