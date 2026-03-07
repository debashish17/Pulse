from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base
from routers import analytics, mitigations
from routers import analyze as analyze_router
from scheduler import start_scheduler
import uvicorn

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PULSE — Real-Time Analytics & Content Intelligence",
    description=(
        "Drop a YouTube or Reddit URL and get instant performance analysis, "
        "sentiment, and AI-powered improvement suggestions. "
        "Endpoints: POST /analyze · POST /suggestions · GET /analytics/*"
    ),
    version="2.0.0",
)

# Allow calls from other services and frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core endpoints
app.include_router(analyze_router.router)   # POST /analyze, GET /analyze/{id}/history
app.include_router(mitigations.router)      # POST /suggestions
app.include_router(analytics.router)        # GET /analytics/summary|timeseries|by-platform|discover-trending


# Health check
@app.get("/health")
def health():
    return {"status": "ok", "service": "pulse"}


# Start background polling scheduler
scheduler = start_scheduler()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
