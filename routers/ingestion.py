"""
Manual Ingestion Trigger Endpoints
Allows other services to trigger platform data collection on-demand
"""

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from database import get_db

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


class TriggerIngestionRequest(BaseModel):
    platforms: Optional[List[str]] = None  # If None, ingest all platforms
    content_id: Optional[str] = None  # If provided, only ingest for this content


class TriggerIngestionResponse(BaseModel):
    message: str
    platforms: List[str]
    triggered_at: str


@router.post("/trigger", response_model=TriggerIngestionResponse)
async def trigger_ingestion(
    request: TriggerIngestionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Manually trigger platform data ingestion
    
    - **platforms**: List of platforms to ingest (youtube, reddit, twitter, etc.)
    - **content_id**: Optional - Currently not supported, will ingest all content
    
    This endpoint allows other services (Genesis, Orbit) to trigger
    on-demand metrics collection without waiting for scheduled polling.
    """
    from services.ingestion.youtube import ingest_youtube
    from services.ingestion.reddit import ingest_reddit
    from services.ingestion.mock_platforms import ingest_mock
    
    # Default to all platforms if none specified
    platforms = request.platforms or ["youtube", "reddit", "twitter", "instagram", "linkedin", "tiktok"]
    
    # Validate platforms
    valid_platforms = ["youtube", "reddit", "twitter", "instagram", "linkedin", "tiktok"]
    invalid = [p for p in platforms if p not in valid_platforms]
    if invalid:
        raise HTTPException(400, f"Invalid platforms: {invalid}")
    
    # Schedule ingestion in background
    def run_ingestion():
        for platform in platforms:
            try:
                if platform == "youtube":
                    ingest_youtube(db)
                elif platform == "reddit":
                    ingest_reddit(db)
                else:
                    # Mock platforms (twitter, instagram, linkedin, tiktok)
                    ingest_mock(db, platform)
            except Exception as e:
                print(f"Error ingesting {platform}: {e}")
    
    background_tasks.add_task(run_ingestion)
    
    return TriggerIngestionResponse(
        message=f"Ingestion triggered for {len(platforms)} platform(s)",
        platforms=platforms,
        triggered_at=datetime.utcnow().isoformat() + "Z"
    )


@router.get("/status")
async def ingestion_status(db: Session = Depends(get_db)):
    """
    Get the status of the last ingestion cycle
    Returns the most recent metrics timestamp per platform
    """
    from models import Metrics, Content
    from sqlalchemy import func
    
    # Get latest metrics per platform
    latest_metrics = (
        db.query(
            Content.platform,
            func.max(Metrics.recorded_at).label("last_ingestion")
        )
        .join(Content, Metrics.content_id == Content.id)
        .group_by(Content.platform)
        .all()
    )
    
    return {
        "platforms": [
            {
                "platform": row.platform,
                "last_ingestion": row.last_ingestion.isoformat() + "Z" if row.last_ingestion else None
            }
            for row in latest_metrics
        ]
    }
