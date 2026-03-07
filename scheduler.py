from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal
from services.ingestion.youtube import ingest_youtube
from services.ingestion.reddit import ingest_reddit


def run_ingestion():
    """Polls YouTube and Reddit every 10 minutes for registered content."""
    db = SessionLocal()
    try:
        ingest_youtube(db)
        ingest_reddit(db)
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler()
    # Poll every 10 minutes
    scheduler.add_job(run_ingestion, "interval", minutes=10, id="ingestion_job")
    scheduler.start()
    return scheduler
