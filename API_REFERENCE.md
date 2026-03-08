# PULSE API Reference

Base URL (local): `http://localhost:8003`  
Interactive docs: `/docs` (Swagger UI) · `/redoc` (ReDoc)

---

## Quick Reference

| Method | Path | Use |
|--------|------|-----|
| POST | `/analyze` | Analyze any YouTube or Reddit URL |
| POST | `/suggestions` | Get 3 AI suggestions for a URL |
| GET | `/analyze/{content_id}/history` | Historical snapshots for a content item |
| GET | `/analytics/summary` | KPI totals + % change vs prior period |
| GET | `/analytics/timeseries` | Daily metrics for charts |
| GET | `/analytics/by-platform` | Platform comparison |
| GET | `/analytics/discover-trending` | Live trending content from platforms |
| GET | `/health` | Health check |

---

## 1. `POST /analyze`

**Purpose:** One-stop URL analysis. Detects platform, auto-registers content (if new), fetches live metrics, and returns a performance verdict.

### Request Body

```json
{ "url": "https://www.youtube.com/watch?v=VIDEO_ID" }
```

Supported URL formats:
- YouTube: `youtube.com/watch?v=`, `youtu.be/`
- Reddit: `reddit.com/r/{subreddit}/comments/{post_id}/`

### Technical Flow

1. `parse_url()` runs regex to detect platform and extract `post_id`
2. Checks DB for existing `Content` record by `post_id`
3. Fetches live data from the platform:
   - **YouTube** — calls `videos().list(part="snippet,statistics")` + top 20 comments → VADER sentiment
   - **Reddit** — calls `reddit.com/comments/{post_id}.json` → estimates views as `upvotes × 100`, top 20 comments → VADER sentiment
4. If content is new → inserts a `Content` row
5. Always inserts a new `Metrics` snapshot row
6. Runs `determine_status()` — compares `actual_engagement` vs `predicted_engagement` (default baseline: 5.0%)

### Status Logic

| Condition | Status |
|-----------|--------|
| Actual engagement < 30% below predicted | `underperforming` |
| Actual engagement > 50% above predicted | `viral_spike` |
| Sentiment score < -0.3 | `negative_sentiment` |
| Otherwise | `on_track` |

### Response

```json
{
  "content_id": "uuid",
  "platform": "youtube",
  "title": "Video Title",
  "url": "https://...",
  "thumbnail": "https://i.ytimg.com/...",
  "channel": "Channel Name",
  "metrics": {
    "views": 123297,
    "likes": 7200,
    "comments": 1050,
    "engagement_rate": 6.69,
    "sentiment_score": 0.312,
    "sentiment_label": "positive",
    "recorded_at": "2025-07-15T10:00:00Z"
  },
  "status": "on_track",
  "reason": "Content is performing within expected range"
}
```

### Notes

- `content_id` in the response is needed for `/analyze/{content_id}/history`
- Each call to `/analyze` saves a new snapshot — calling it repeatedly builds history
- Reddit `thumbnail` will always be `null` (Reddit does not expose thumbnail URLs via public API)

---

## 2. `POST /suggestions`

**Purpose:** Returns 3 AI-generated improvement suggestions powered by NVIDIA Qwen. Requires the content to have been analyzed first via `POST /analyze`.

### Request Body

```json
{ "url": "https://www.youtube.com/watch?v=VIDEO_ID" }
```

Same URL format as `/analyze`.

### Technical Flow

1. Calls `parse_url()` to extract `post_id`
2. Looks up `Content` in DB — returns `404` if not found (must call `/analyze` first)
3. Gets most recent `Metrics` row (`ORDER BY recorded_at DESC LIMIT 1`)
4. Re-calculates performance status using same logic as `/analyze`
5. Sends prompt to NVIDIA API:
   - **Endpoint:** `https://integrate.api.nvidia.com/v1/chat/completions`
   - **Model:** `qwen/qwen3.5-122b-a10b`
   - **Settings:** max 16384 tokens, temperature 0.6, top_p 0.95
6. Parses numbered list from response and returns as array

### Response

```json
{
  "content_id": "uuid",
  "platform": "youtube",
  "title": "Video Title",
  "url": "https://...",
  "status": "underperforming",
  "reason": "Engagement is 40% below predicted baseline of 5.0%",
  "suggestions": [
    "1. Add timestamps in description to improve retention and discoverability...",
    "2. Pin a strategic comment within the first hour to boost early engagement...",
    "3. Share to relevant subreddits or communities within 48 hours of posting..."
  ]
}
```

### Errors

| Status | Condition |
|--------|-----------|
| `404` | Content not in DB — call `POST /analyze` first |
| `404` | No metrics on record — call `POST /analyze` first |

---

## 3. `GET /analyze/{content_id}/history`

**Purpose:** Returns all historical metric snapshots for a piece of content. Useful for tracking growth over time.

### Path Parameter

| Param | Type | Description |
|-------|------|-------------|
| `content_id` | UUID string | Returned by `POST /analyze` |

### Technical Flow

1. Looks up `Content` by `id` — returns `404` if not found
2. Queries all `Metrics` rows for that `content_id`, `ORDER BY recorded_at ASC`
3. Each call to `/analyze` with the same URL adds a new snapshot to this history

### Response

```json
{
  "content_id": "uuid",
  "title": "Video Title",
  "platform": "youtube",
  "url": "https://...",
  "snapshots": [
    {
      "views": 120000,
      "likes": 6800,
      "comments": 900,
      "engagement_rate": 6.42,
      "sentiment_score": 0.28,
      "sentiment_label": "positive",
      "recorded_at": "2025-07-14T09:00:00Z"
    },
    {
      "views": 123297,
      "likes": 7200,
      "comments": 1050,
      "engagement_rate": 6.69,
      "sentiment_score": 0.31,
      "sentiment_label": "positive",
      "recorded_at": "2025-07-15T10:00:00Z"
    }
  ]
}
```

### Errors

| Status | Condition |
|--------|-----------|
| `404` | `content_id` not found in DB |

---

## 4. `GET /analytics/summary`

**Purpose:** Top-level KPI cards for the dashboard — total views, avg engagement, shares, saves — with % change vs prior period.

### Query Parameters

| Param | Type | Default | Options |
|-------|------|---------|---------|
| `period` | string | `14d` | `7d`, `14d`, `30d`, `90d` |
| `content_id` | string | none | UUID to filter to one piece of content |

### Technical Flow

1. Splits time into `current_period` (last N days) and `previous_period` (the N days before that)
2. Aggregates `Metrics` rows in each period
3. Computes `pct_change = (curr - prev) / prev × 100` for each KPI

### Response

```json
{
  "total_views": 500000,
  "total_views_change": 12.4,
  "avg_engagement": 5.8,
  "avg_engagement_change": -3.1,
  "total_shares": 2400,
  "total_shares_change": 0.0,
  "total_saves": 890,
  "total_saves_change": 8.7
}
```

`_change` values are percentage points vs the previous equivalent period.

---

## 5. `GET /analytics/timeseries`

**Purpose:** Daily aggregated metrics for line/area charts.

### Query Parameters

| Param | Type | Default | Options |
|-------|------|---------|---------|
| `period` | string | `14d` | `7d`, `14d`, `30d`, `90d` |
| `content_id` | string | none | UUID to scope to one piece of content |

### Technical Flow

Groups all `Metrics` rows by `DATE(recorded_at)`, aggregates views, engagement rate, and sentiment per day.

### Response

```json
[
  {
    "date": "2025-07-10",
    "views": 45000,
    "engagement_pct": 6.1,
    "sentiment_score": 0.21,
    "sentiment_label": "positive"
  },
  {
    "date": "2025-07-11",
    "views": 48200,
    "engagement_pct": 6.4,
    "sentiment_score": 0.19,
    "sentiment_label": "positive"
  }
]
```

Results are ordered by date ascending (oldest → newest).

---

## 6. `GET /analytics/by-platform`

**Purpose:** Aggregated performance broken down by platform — for bar chart comparisons.

### Query Parameters

None. Covers all data in the database.

### Technical Flow

Groups `Metrics` by `platform`, sums views/likes/comments, averages engagement rate and sentiment score.

### Response

```json
[
  {
    "platform": "youtube",
    "posts": 3,
    "total_views": 450000,
    "total_likes": 28000,
    "total_comments": 5200,
    "engagement_rate": 6.5,
    "avg_sentiment": 0.24
  },
  {
    "platform": "reddit",
    "posts": 2,
    "total_views": 95000,
    "total_likes": 5900,
    "total_comments": 1100,
    "engagement_rate": 1.8,
    "avg_sentiment": -0.12
  }
]
```

> **Note:** Reddit engagement rates naturally run 1–3% because view counts are estimated (upvotes × 100). YouTube rates of 5–8% are typical.

---

## 7. `GET /analytics/discover-trending`

**Purpose:** Fetches **live** trending content from actual platforms for competitive intelligence. Data comes from YouTube/Reddit APIs directly — not from your database.

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `platform` | string | none | `youtube` or `reddit` — required if no `content_id` |
| `content_id` | string | none | Uses your content's platform + extracts genre keywords from DNA |
| `limit` | int | `10` | Number of trending items to return |

### Technical Flow

1. If `content_id` provided: looks up content, extracts `genre_keywords` from `content_dna`, inherits platform if `platform` not explicitly set
2. Validates that a platform is known
3. Calls `get_platform_trending(platform, genre_keywords, limit)` — live API call
4. Returns results directly from the platform

### Example Requests

```
# Top 5 trending YouTube videos overall
GET /analytics/discover-trending?platform=youtube&limit=5

# Trending YouTube videos in the same genre as your content
GET /analytics/discover-trending?content_id=uuid&platform=youtube

# Use your content's platform automatically
GET /analytics/discover-trending?content_id=uuid
```

### Response

```json
[
  {
    "title": "Trending Video Title",
    "platform": "youtube",
    "url": "https://youtube.com/watch?v=...",
    "views": 2400000,
    "engagement_rate": 7.2,
    "published_at": "2025-07-14T00:00:00Z"
  }
]
```

### Errors

| Status | Condition |
|--------|-----------|
| `400` | Neither `content_id` nor `platform` provided |
| `404` | `content_id` not found in DB |
| `501` | Platform is not `youtube` or `reddit` |

Returns `[]` if the platform API is temporarily unavailable.

---

## 8. `GET /health`

**Purpose:** Liveness/readiness check for Render, Docker, and uptime monitors.

### Response

```json
{ "status": "ok" }
```

Always returns HTTP `200` if the server is running.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `YOUTUBE_API_KEY` | Yes | Google Cloud API key with YouTube Data API v3 |
| `NVIDIA_API_KEY` | Yes | NVIDIA API key for AI suggestions |
| `NVIDIA_API_URL` | Yes | `https://integrate.api.nvidia.com/v1/chat/completions` |
| `NVIDIA_MODEL` | No | Defaults to `qwen/qwen3.5-122b-a10b` |

---

## Typical Frontend Flow

```
User pastes URL
     │
     ▼
POST /analyze          ← get content_id, metrics, status, reason
     │
     ▼
POST /suggestions      ← get 3 AI improvement tips (same URL)
     │
     ▼
GET  /analyze/{id}/history   ← show growth chart over time
```
