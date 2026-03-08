<div align="center">

# ⚡ PULSE

### Real-Time Content Analytics & Intelligence

**Drop a URL. Get the full picture.**

*Live metrics · Audience sentiment · AI-powered improvement suggestions*

---

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?style=flat-square&logo=postgresql&logoColor=white)
![NVIDIA](https://img.shields.io/badge/NVIDIA-Qwen_AI-76B900?style=flat-square&logo=nvidia&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)
![Deployed](https://img.shields.io/badge/Deployed-Render-46E3B7?style=flat-square&logo=render&logoColor=white)

**🌐 Live:** https://pulse-api-l1xa.onrender.com

</div>

---

## What is PULSE?

PULSE is a standalone intelligence microservice that monitors your content **after it goes live**. You give it a YouTube video or Reddit post URL — it gives you a complete performance picture: live metrics, audience sentiment, a performance verdict with a reason, and three tailored AI suggestions for what to do next.

No multi-step setup. No manual platform registration. One URL in, full intelligence out.

> PULSE **monitors and advises** — it does not generate or transform content.

---

## Core Features

| Feature                         | Description                                                            |
| ------------------------------- | ---------------------------------------------------------------------- |
| 🔗**One-URL Input**       | Paste any YouTube or Reddit URL — PULSE handles everything else       |
| 📊**Live Metrics**        | Fetches real-time views, likes, comments directly from platform APIs   |
| 🧠**Sentiment Analysis**  | VADER scoring across top 20 comments — positive, neutral, or negative |
| 🤖**AI Suggestions**      | NVIDIA Qwen generates 3 specific, actionable improvement tips          |
| 📈**Growth Tracking**     | Every analysis is saved — call again to build a historical timeline   |
| 🔄**Background Polling**  | Registered content is auto-refreshed every 10 minutes                  |
| 🏆**Trending Discovery**  | Live competitive intelligence from YouTube & Reddit                    |
| 📉**Dashboard Analytics** | KPI cards, timeseries, platform comparison — all queryable by period  |

---

## How It Works

```
  You paste a URL
       │
       ▼
  ┌─────────────────────────────────────────────┐
  │              POST /analyze                  │
  │                                             │
  │  1. Detect platform from URL                │
  │  2. Fetch live data from platform API       │
  │  3. Run VADER sentiment on top comments     │
  │  4. Auto-register content if first visit    │
  │  5. Save metrics snapshot to DB             │
  │  6. Compare engagement vs predicted         │
  │  7. Return verdict + reason                 │
  └─────────────────────────────────────────────┘
       │
       ▼
  ┌─────────────────────────────────────────────┐
  │             POST /suggestions               │
  │                                             │
  │  1. Look up latest metrics from DB          │
  │  2. Build context: title, platform,         │
  │     engagement, sentiment, status           │
  │  3. Call NVIDIA Qwen (122B param model)     │
  │  4. Return 3 tailored action items          │
  └─────────────────────────────────────────────┘
       │
       ▼
  GET /analyze/{id}/history  →  Full timeline of all snapshots
```

---

## Performance Verdicts

Every analysis returns one of four statuses — with a plain-English reason:

| Status                   | Condition                        | Example Reason                                                 |
| ------------------------ | -------------------------------- | -------------------------------------------------------------- |
| ✅`on_track`           | Engagement within expected range | *"Content is performing within expected range"*              |
| 🚀`viral_spike`        | Engagement >50% above predicted  | *"Engagement is 72% above expected — content is trending!"* |
| ⚠️`underperforming`  | Engagement >30% below predicted  | *"Engagement is 41% below expected baseline of 5.0%"*        |
| 🔴`negative_sentiment` | Sentiment score < -0.3           | *"Audience sentiment is negative (score: -0.42)"*            |

> **Reddit note:** Engagement rates naturally run 1–3% vs YouTube's 5–8%, since Reddit view counts are estimated from upvotes. This is expected behaviour.

---

## API Endpoints

| Method   | Endpoint                          | What it does                                      |
| -------- | --------------------------------- | ------------------------------------------------- |
| `POST` | `/analyze`                      | Analyze a URL — live metrics, sentiment, verdict |
| `POST` | `/suggestions`                  | Get 3 AI improvement suggestions for a URL        |
| `GET`  | `/analyze/{content_id}/history` | All historical snapshots for a content item       |
| `GET`  | `/analytics/summary`            | KPI totals + % change vs prior period             |
| `GET`  | `/analytics/timeseries`         | Daily metrics for line/area charts                |
| `GET`  | `/analytics/by-platform`        | Performance grouped by platform                   |
| `GET`  | `/analytics/discover-trending`  | Live trending content from YouTube / Reddit       |
| `GET`  | `/health`                       | Liveness check                                    |

📖 Full request/response details: [API_REFERENCE.md](API_REFERENCE.md)

---

## Live Examples

### Analyze a YouTube Video

```bash
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=yqF5G57vf-E"}'
```

```json
{
  "content_id": "a1b2c3d4-...",
  "platform": "youtube",
  "title": "Video Title",
  "channel": "Channel Name",
  "metrics": {
    "views": 123297,
    "likes": 7200,
    "comments": 1050,
    "engagement_rate": 6.69,
    "sentiment_score": 0.312,
    "sentiment_label": "positive",
    "recorded_at": "2026-03-08T10:00:00Z"
  },
  "status": "on_track",
  "reason": "Content is performing within expected range"
}
```

### Get AI Suggestions

```bash
curl -X POST http://localhost:8003/suggestions \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=yqF5G57vf-E"}'
```

```json
{
  "status": "on_track",
  "suggestions": [
    "1. Add chapter timestamps to improve retention and boost search ranking...",
    "2. Pin a strategic comment within the first hour to anchor the discussion...",
    "3. Cross-post a short clip to relevant subreddits to capture new audiences..."
  ]
}
```

### Analyze a Reddit Post

```bash
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.reddit.com/r/science/comments/abc123/post-title/"}'
```

```json
{
  "platform": "reddit",
  "channel": "r/science",
  "metrics": {
    "views": 595200,
    "likes": 5952,
    "comments": 843,
    "engagement_rate": 1.14,
    "sentiment_score": -0.21,
    "sentiment_label": "negative"
  },
  "status": "underperforming",
  "reason": "Engagement is 77% below expected baseline of 5.0%"
}
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      PULSE  :8003                        │
│                                                         │
│   ┌─────────────┐    ┌──────────────────────────────┐  │
│   │  FastAPI    │    │         PostgreSQL            │  │
│   │  REST API   │◄──►│  content  │  metrics         │  │
│   └──────┬──────┘    └──────────────────────────────┘  │
│          │                                              │
│   ┌──────▼──────────────────────────────────┐          │
│   │        APScheduler  (every 10 min)       │          │
│   │   YouTube Data API v3  │  Reddit JSON    │          │
│   └─────────────────────────────────────────┘          │
│                                                         │
│   ┌─────────────────────────────────────────┐          │
│   │   NVIDIA Qwen  (qwen3.5-122b-a10b)      │          │
│   │   AI suggestions — called on demand     │          │
│   └─────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Clone & install

```bash
git clone <repo-url>
cd PULSE
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` → `.env` and fill in your keys:

```env
DATABASE_URL=postgresql://user:password@host/pulse_db

YOUTUBE_API_KEY=your_google_api_key
NVIDIA_API_KEY=your_nvidia_api_key
NVIDIA_API_URL=https://integrate.api.nvidia.com/v1/chat/completions
NVIDIA_MODEL=qwen/qwen3.5-122b-a10b
```

### 3. Run migrations

```bash
alembic upgrade head
```

### 4. Start the server

```bash
python main.py
```

|                      | Local                       | Production                                |
| -------------------- | --------------------------- | ----------------------------------------- |
| **Service**    | http://localhost:8003       | https://pulse-api-l1xa.onrender.com       |
| **Swagger UI** | http://localhost:8003/docs  | https://pulse-api-l1xa.onrender.com/docs  |
| **ReDoc**      | http://localhost:8003/redoc | https://pulse-api-l1xa.onrender.com/redoc |

---

## Project Structure

```
PULSE/
├── main.py                       # FastAPI app, router registration, health check
├── database.py                   # PostgreSQL connection & session factory
├── models.py                     # SQLAlchemy models — Content, Metrics
├── schemas.py                    # Pydantic response schemas
├── scheduler.py                  # APScheduler — polls every 10 min
├── Dockerfile                    # python:3.10-slim container
├── requirements.txt
├── .env.example
│
├── routers/
│   ├── analyze.py                # POST /analyze · GET /analyze/{id}/history
│   ├── mitigations.py            # POST /suggestions
│   └── analytics.py              # GET /analytics/*
│
├── services/
│   ├── mitigation.py             # NVIDIA Qwen API integration
│   ├── trending_discovery.py     # Live platform trending discovery
│   └── ingestion/
│       ├── youtube.py            # YouTube Data API v3 polling
│       └── reddit.py             # Reddit public JSON API polling
│
└── alembic/                      # Database migrations
```

---

## Tech Stack

| Layer                        | Technology                             |
| ---------------------------- | -------------------------------------- |
| **Framework**          | FastAPI + Uvicorn                      |
| **Language**           | Python 3.10                            |
| **Database**           | PostgreSQL                             |
| **ORM / Migrations**   | SQLAlchemy + Alembic                   |
| **Background Jobs**    | APScheduler                            |
| **Sentiment Analysis** | VADER (`vaderSentiment`)             |
| **AI Suggestions**     | NVIDIA Qwen `qwen/qwen3.5-122b-a10b` |
| **YouTube Data**       | Google API Python Client (Data API v3) |
| **Reddit Data**        | Public JSON API — no auth required    |
| **Container**          | Docker `python:3.10-slim`            |
