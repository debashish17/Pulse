from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Content
from schemas import ContentRegisterRequest, ContentRegisterResponse, DNAUpdateRequest
from datetime import datetime
import uuid

router = APIRouter(prefix="/content", tags=["content"])


@router.post("/register", response_model=ContentRegisterResponse)
def register_content(payload: ContentRegisterRequest, db: Session = Depends(get_db)):
    """
    Called by Forge after content is posted.
    Registers content for monitoring.
    """
    content = Content(
        id=uuid.uuid4(),
        title=payload.title,
        platform=payload.platform.lower(),
        post_url=payload.post_url,
        post_id=payload.post_id,
        content_dna=payload.content_dna,
        predicted_engagement=payload.predicted_engagement or payload.content_dna.get("predicted_engagement"),
        predicted_views=payload.predicted_views or payload.content_dna.get("predicted_views"),
        posted_at=payload.posted_at,
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    return ContentRegisterResponse(
        content_id=str(content.id),
        message=f"Content '{payload.title}' registered for monitoring on {payload.platform}",
    )


@router.get("/list")
def list_content(db: Session = Depends(get_db)):
    """Returns all registered active content."""
    items = db.query(Content).filter(Content.status == "active").all()
    return [
        {"content_id": str(c.id), "title": c.title, "platform": c.platform, "posted_at": c.posted_at}
        for c in items
    ]


@router.post("/dna-update")
async def update_dna(payload: DNAUpdateRequest, db: Session = Depends(get_db)):
    """
    Called after content lifecycle completes.
    Stores updated DNA and pushes learnings to Genesis + Orbit.
    """
    from services.dna_updater import push_dna_update_to_genesis, push_timing_to_orbit

    content = db.query(Content).filter(Content.id == payload.content_id).first()
    if not content:
        return {"error": "Content not found"}

    # Merge learnings into existing DNA
    updated_dna = {
        **(content.content_dna or {}),
        "performance_score": payload.performance_score,
        "learnings": payload.learnings,
    }
    content.content_dna = updated_dna
    content.status = "archived"
    db.commit()

    # Push feedback to sibling services (non-blocking)
    await push_dna_update_to_genesis(payload.content_id, payload.final_metrics)
    await push_timing_to_orbit(payload.content_id, "TBD", payload.performance_score)

    return {"message": "DNA updated and feedback dispatched"}
