from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal
from services.ingestion.youtube import ingest_youtube
from services.ingestion.reddit import ingest_reddit
from services.ingestion.mock_platforms import ingest_mock


def run_ingestion():
    """Runs all platform ingestion jobs."""
    db = SessionLocal()
    try:
        ingest_youtube(db)
        ingest_reddit(db)
        for platform in ["twitter", "instagram", "linkedin", "tiktok"]:
            ingest_mock(db, platform)
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler()
    # Poll every 10 minutes
    scheduler.add_job(run_ingestion, "interval", minutes=10, id="ingestion_job")
    scheduler.start()
    return scheduler
