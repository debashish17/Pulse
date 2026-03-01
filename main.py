from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base
from routers import analytics, alerts, content, mitigations, ingestion
from scheduler import start_scheduler
import uvicorn

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PULSE — Real-Time Analytics & Content Intelligence",
    description="Standalone microservice for monitoring content performance across social platforms. "
                "Other services call PULSE via REST API to register content, retrieve analytics, and get AI-powered suggestions.",
    version="1.0.0",
)

# Allow calls from other services (Genesis, Orbit, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(content.router)
app.include_router(analytics.router)
app.include_router(alerts.router)
app.include_router(mitigations.router)
app.include_router(ingestion.router)


# Health check
@app.get("/health")
def health():
    return {"status": "ok", "service": "pulse"}


# Start background polling scheduler
scheduler = start_scheduler()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
