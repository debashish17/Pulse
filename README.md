# PULSE — Real-Time Content Analytics & Intelligence

> **Standalone Microservice for Content Performance Monitoring**  
> Other services call PULSE via REST API to monitor content performance and get AI-powered insights

---

## 🌐 Standalone Service Architecture

**PULSE is a standalone microservice** that:
- Accepts content registration from any service via REST API
- Polls social platforms (YouTube, Reddit, Twitter, etc.) for metrics every 10 minutes
- Detects anomalies and generates AI-powered suggestions
- Returns analytics and insights via REST endpoints

**No tight coupling:** Other services (Genesis, Forge, Orbit) call PULSE endpoints but don't need to run simultaneously.

**Standalone Mode:** Set `ENABLE_EXTERNAL_SERVICES=false` in `.env` to run independently without calling other services.

---

## 🚀 Quick Start

### ⚡ Using Python Scripts (Easiest)
```powershell
# First time only
python setup_pulse.py

# Daily startup
python start_pulse.py
```

### 📋 Or Manual Commands
```powershell
# First time setup
pip install -r requirements.txt
docker-compose up -d
alembic upgrade head
python -c "import nltk; nltk.download('vader_lexicon')"

# Daily startup (run these 2 commands)
docker-compose up -d
python main.py
```

**Service runs on:** http://localhost:8003  
**API Docs:** http://localhost:8003/docs  
**Quick Commands:** See [COMMANDS.txt](COMMANDS.txt)

---

## 🎯 What PULSE Does

PULSE monitors content **after it has been posted** and provides:

1. **Real-Time Analytics** — Views, engagement, sentiment across all platforms
2. **Anomaly Detection** — Automatically flags underperforming or viral content
3. **AI Mitigations** — Claude-powered suggestions for immediate action
4. **Feedback Loop** — Sends performance learnings back to Genesis & Orbit

**PULSE does NOT generate or transform content.** It only monitors, analyzes, and suggests.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   PULSE Service                      │
│                                                      │
│  ┌──────────────┐      ┌─────────────────┐         │
│  │  FastAPI     │◄────►│   PostgreSQL    │         │
│  │  REST API    │      │   (3 tables)    │         │
│  └──────┬───────┘      └─────────────────┘         │
│         │                                            │
│         │                                            │
│  ┌──────▼───────────────────────────────┐           │
│  │     APScheduler (10 min polling)      │           │
│  │                                       │           │
│  │  ┌─────────────┐  ┌──────────────┐  │           │
│  │  │  YouTube    │  │   Reddit     │  │           │
│  │  │  (Real API) │  │  (Real API)  │  │           │
│  │  └─────────────┘  └──────────────┘  │           │
│  │                                       │           │
│  │  ┌─────────────────────────────────┐ │           │
│  │  │ Mock Platforms (Twitter, IG,    │ │           │
│  │  │ LinkedIn, TikTok)               │ │           │
│  │  └─────────────────────────────────┘ │           │
│  └───────────────────────────────────────┘           │
│                                                      │
│  ┌──────────────────────────────────────┐           │
│  │   Anomaly Detection + Claude AI      │           │
│  └──────────────────────────────────────┘           │
└─────────────────────────────────────────────────────┘
```

---

## 📡 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| **Content** |
| `POST` | `/content/register` | Register content for monitoring |
| `GET` | `/content/list` | List all monitored content |
| `POST` | `/content/dna-update` | Update DNA with learnings || **Ingestion** |
| `POST` | `/ingestion/trigger` | Manually trigger platform polling |
| `GET` | `/ingestion/status` | Get last ingestion timestamps || **Analytics** |
| `GET` | `/analytics/summary` | KPI cards (views, engagement, etc.) |
| `GET` | `/analytics/timeseries` | Daily performance data |
| `GET` | `/analytics/by-platform` | Platform comparison |
| `GET` | `/analytics/top-content` | Top performing content |
| **Alerts** |
| `GET` | `/alerts/` | Get active alerts |
| `POST` | `/alerts/{id}/resolve` | Dismiss alert |
| **Mitigations** |
| `GET` | `/mitigations/{content_id}` | AI suggestions |
| **Health** |
| `GET` | `/health` | Service status |

📖 **Full API Docs:** http://localhost:8003/docs (after starting)

---

## 🗄️ Database Schema

- **`content`** — Registered content items
- **`metrics`** — Performance data (collected every 10 min)
- **`alerts`** — Anomaly alerts with AI suggestions

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (Python) |
| Database | PostgreSQL |
| ORM | SQLAlchemy + Alembic |
| Scheduler | APScheduler |
| Sentiment | VADER (NLTK) |
| AI | Anthropic Claude API |
| Real APIs | YouTube Data API v3, Reddit PRAW |

---

## 🐳 Docker vs Local PostgreSQL

### ✅ **Recommended: Docker PostgreSQL**
**Pros:**
- Quick setup (one command: `docker-compose up -d`)
- No system-wide install needed
- Easy to reset/clean
- Consistent across environments
- Isolated from other projects

**Cons:**
- Requires Docker Desktop (~500MB download)

### Local PostgreSQL
**Pros:**
- Full PostgreSQL features
- Better for production-like testing

**Cons:**
- More complex installation
- System-wide configuration
- Potential port conflicts

**Verdict:** Use Docker for development/hackathon. Switch to managed PostgreSQL (AWS RDS, Azure, etc.) for production.

---

## 🧪 Testing

### 1. Start the service
```powershell
python main.py
```

### 2. Health check
```powershell
curl http://localhost:8003/health
```

### 3. Register content
```powershell
curl -X POST http://localhost:8003/content/register \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Test Video",
    "platform": "youtube",
    "post_id": "dQw4w9WgXcQ",
    "content_dna": {"tone": "educational"},
    "predicted_engagement": 5.0,
    "posted_at": "2026-03-01T10:00:00Z"
  }'
```

### 4. Check analytics
```powershell
curl http://localhost:8003/analytics/summary?period=7d
```

---

## 🔗 Integration with Synapse Services

| Service | Port | Role |
|---------|------|------|
| **Genesis** | 8001 | Receives performance feedback |
| **Forge** | 8002 | Sends registered content to PULSE |
| **PULSE** | 8003 | This service |
| **Orbit** | 8004 | Receives timing insights |

Configure URLs in `.env`:
```env
GENESIS_SERVICE_URL=http://localhost:8001
FORGE_SERVICE_URL=http://localhost:8002
ORBIT_SERVICE_URL=http://localhost:8004
```

---

## 📁 Project Structure

```
pulse/
├── main.py                 # FastAPI entry point
├── database.py             # PostgreSQL connection
├── models.py               # SQLAlchemy ORM models
├── schemas.py              # Pydantic schemas
├── scheduler.py            # APScheduler polling
├── routers/
│   ├── content.py         # Content registration
│   ├── analytics.py       # Performance analytics
│   ├── alerts.py          # Alert management
│   └── mitigations.py     # AI suggestions
├── services/
│   ├── anomaly.py         # Anomaly detection
│   ├── mitigation.py      # Claude API
│   ├── dna_updater.py     # Feedback to Genesis/Orbit
│   └── ingestion/
│       ├── youtube.py     # YouTube Data API
│       ├── reddit.py      # Reddit PRAW
│       └── mock_platforms.py  # Mock data
└── alembic/               # Database migrations
```

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| Database connection error | Check `docker ps` or verify local PostgreSQL is running |
| NLTK error | Run `python -c "import nltk; nltk.download('vader_lexicon')"` |
| Port 8003 in use | Change port in `main.py` or kill existing process |
| No metrics collecting | Verify `post_id` is correct (YouTube video ID, not URL) |
| Claude API error | Check `ANTHROPIC_API_KEY` in `.env` |

Full troubleshooting guide: [SETUP.md](SETUP.md#troubleshooting)

---

## 📝 Environment Variables

Required in `.env`:
```env
DATABASE_URL=postgresql://pulse_user:pulse_password@localhost:5432/pulse_db
ANTHROPIC_API_KEY=your_key_here
YOUTUBE_API_KEY=your_key_here
REDDIT_CLIENT_ID=your_key_here
REDDIT_CLIENT_SECRET=your_key_here
REDDIT_USER_AGENT=pulse_monitor/1.0
```

---

## 📄 License

MIT License — Synapse Hackathon 2026

---

## 🚦 Status

**Service Port:** `8003`  
**Polling Interval:** Every 10 minutes  
**Database:** PostgreSQL 15+  
**Python:** 3.10+

---

**Ready to start?** Run `.\setup.ps1` or see [SETUP.md](SETUP.md) for details.
