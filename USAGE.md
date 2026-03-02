# PULSE API Usage Guide

**Version:** 1.0.0
**Service:** Real-Time Content Analytics & Intelligence (Standalone Microservice)
**Base URL:** `http://localhost:8003`

---

## 🌐 Standalone Service

**PULSE is a standalone microservice.** Other services (Genesis, Forge, Orbit) can call PULSE via REST API, but they don't need to be running for PULSE to function.

### Configuration Modes

**Standalone Mode (Default):**

```env
ENABLE_EXTERNAL_SERVICES=false
```

- PULSE runs independently
- DNA updates are logged but not sent to Genesis/Orbit
- Perfect for development, testing, and demos

**Integrated Mode:**

```env
ENABLE_EXTERNAL_SERVICES=true
```

- PULSE calls Genesis and Orbit services when available
- Used in full Synapse ecosystem deployment

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [Content Management](#content-management)
4. [Ingestion Management](#ingestion-management)
5. [Analytics Endpoints](#analytics-endpoints)
6. [Alert Management](#alert-management)
7. [AI Mitigation Suggestions](#ai-mitigation-suggestions)
8. [Complete Workflows](#complete-workflows)
9. [Response Formats](#response-formats)
10. [Error Handling](#error-handling)
11. [Best Practices](#best-practices)

---

## Quick Start

### Verify Service is Running

```bash
curl http://localhost:8003/health
```

**Response:**

```json
{
  "status": "ok",
  "service": "pulse"
}
```

### Access API Documentation

Open in browser: **http://localhost:8003/docs**

Interactive API testing available via Swagger UI.

---

## Authentication

**Current Version:** No authentication required (development mode)

**Production:** Add API key authentication to all endpoints.

---

## Content Management

### 1. Register Content for Monitoring

**Endpoint:** `POST /content/register`

**When to call:** Immediately after content is posted to any platform (called by Forge service).

**Request Body:**

```json
{
  "title": "10 Tips for Better Productivity",
  "platform": "youtube",
  "post_id": "dQw4w9WgXcQ",
  "post_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "content_dna": {
    "target_audience": "tech professionals",
    "tone": "educational",
    "content_type": "tutorial",
    "predicted_engagement": 6.5,
    "predicted_views": 15000
  },
  "predicted_engagement": 6.5,
  "predicted_views": 15000,
  "posted_at": "2026-03-01T10:30:00Z"
}
```

**Field Descriptions:**

| Field                    | Type     | Required | Description                                                                                 |
| ------------------------ | -------- | -------- | ------------------------------------------------------------------------------------------- |
| `title`                | string   | ✓       | Content title or headline                                                                   |
| `platform`             | string   | ✓       | Platform name:`youtube`, `reddit`, `twitter`, `instagram`, `linkedin`, `tiktok` |
| `post_id`              | string   | ✓       | Platform-native ID (YouTube video ID, Reddit post ID, etc.)                                 |
| `post_url`             | string   | ✗       | Full URL to the post                                                                        |
| `content_dna`          | object   | ✓       | Complete DNA object from Genesis/Forge                                                      |
| `predicted_engagement` | float    | ✗       | Expected engagement % (can be in content_dna)                                               |
| `predicted_views`      | integer  | ✗       | Expected view count (can be in content_dna)                                                 |
| `posted_at`            | datetime | ✓       | ISO 8601 timestamp when content was posted                                                  |

**Response:**

```json
{
  "content_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "message": "Content '10 Tips for Better Productivity' registered for monitoring on youtube"
}
```

**Example curl:**

```bash
curl -X POST http://localhost:8003/content/register \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Video",
    "platform": "youtube",
    "post_id": "dQw4w9WgXcQ",
    "content_dna": {"tone": "casual"},
    "predicted_engagement": 5.0,
    "posted_at": "2026-03-01T10:00:00Z"
  }'
```

**PowerShell Example:**

```powershell
$body = @{
    title = "My First Video"
    platform = "youtube"
    post_id = "dQw4w9WgXcQ"
    content_dna = @{ tone = "casual" }
    predicted_engagement = 5.0
    posted_at = "2026-03-01T10:00:00Z"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8003/content/register" `
  -Method Post -Body $body -ContentType "application/json"
```

---

### 2. List All Monitored Content

**Endpoint:** `GET /content/list`

**Purpose:** View all active content being monitored.

**Response:**

```json
[
  {
    "content_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
    "title": "10 Tips for Better Productivity",
    "platform": "youtube",
    "posted_at": "2026-03-01T10:30:00Z"
  },
  {
    "content_id": "b2c3d4e5-6789-01bc-def0-234567890abc",
    "title": "Best Coding Practices in 2026",
    "platform": "reddit",
    "posted_at": "2026-02-28T14:20:00Z"
  }
]
```

**Example:**

```bash
curl http://localhost:8003/content/list
```

---

### 3. Update Content DNA with Learnings

**Endpoint:** `POST /content/dna-update`

**When to call:** After content lifecycle completes (e.g., after 30 days or when campaign ends).

**Request Body:**

```json
{
  "content_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "final_metrics": {
    "total_views": 45230,
    "total_likes": 2890,
    "total_comments": 456,
    "total_shares": 234,
    "avg_engagement_rate": 7.8,
    "avg_sentiment": 0.65
  },
  "performance_score": 82.5,
  "learnings": [
    "Tutorial format performed 40% above predicted",
    "Engagement peaked between 2-4 PM EST",
    "Positive sentiment correlated with code examples",
    "Thumbnail A/B test: version B performed 25% better"
  ]
}
```

**Response:**

```json
{
  "message": "DNA updated and feedback dispatched"
}
```

**What happens:**

1. Content status changed to `archived`
2. Learnings stored in content DNA
3. Feedback sent to Genesis service (for better future ideation) — *only if ENABLE_EXTERNAL_SERVICES=true*
4. Performance insights sent to Orbit service (for better scheduling) — *only if ENABLE_EXTERNAL_SERVICES=true*

---

## Ingestion Management

### 1. Manually Trigger Platform Polling

**Endpoint:** `POST /ingestion/trigger`

**When to call:** When you want immediate metrics collection instead of waiting for the 10-minute automatic polling cycle.

**Request Body:**

```json
{
  "platforms": ["youtube", "reddit", "twitter"],
  "content_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab"
}
```

**Field Descriptions:**

| Field          | Type   | Required | Description                                                                          |
| -------------- | ------ | -------- | ------------------------------------------------------------------------------------ |
| `platforms`  | array  | ✗       | List of platforms to poll. If omitted, polls ALL platforms                           |
| `content_id` | string | ✗       | Only collect metrics for this specific content. If omitted, polls all active content |

**Supported Platforms:**

- `youtube` — Real API (YouTube Data API v3)
- `reddit` — Real API (PRAW)
- `twitter` — Mock data
- `instagram` — Mock data
- `linkedin` — Mock data
- `tiktok` — Mock data

**Response:**

```json
{
  "message": "Ingestion triggered for 3 platform(s)",
  "platforms": ["youtube", "reddit", "twitter"],
  "triggered_at": "2026-03-01T14:30:00Z"
}
```

**cURL Example:**

```bash
# Trigger all platforms for all content
curl -X POST http://localhost:8003/ingestion/trigger \
  -H "Content-Type: application/json" \
  -d '{}'

# Trigger specific platforms for specific content
curl -X POST http://localhost:8003/ingestion/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["youtube", "reddit"],
    "content_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab"
  }'
```

**PowerShell Example:**

```powershell
# Trigger all platforms
Invoke-RestMethod -Uri "http://localhost:8003/ingestion/trigger" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{}'

# Trigger specific platforms
$body = @{
    platforms = @("youtube", "reddit")
    content_id = "a1b2c3d4-5678-90ab-cdef-1234567890ab"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8003/ingestion/trigger" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**Note:** Ingestion runs in the background. The API returns immediately. Check `/ingestion/status` to see when last polling completed.

---

### 2. Get Ingestion Status

**Endpoint:** `GET /ingestion/status`

**Purpose:** Check when each platform was last polled for metrics.

**Response:**

```json
{
  "platforms": [
    {
      "platform": "youtube",
      "last_ingestion": "2026-03-01T14:25:00Z"
    },
    {
      "platform": "reddit",
      "last_ingestion": "2026-03-01T14:24:00Z"
    },
    {
      "platform": "twitter",
      "last_ingestion": "2026-03-01T14:23:00Z"
    }
  ]
}
```

**cURL Example:**

```bash
curl http://localhost:8003/ingestion/status
```

**Usage Tip:** Call this endpoint to verify that automatic polling is working or to confirm that a manual trigger completed successfully.

---

## Analytics Endpoints

### 1. Summary Dashboard (KPI Cards)

**Endpoint:** `GET /analytics/summary`

**Query Parameters:**

| Parameter      | Type   | Default | Options                           | Description                 |
| -------------- | ------ | ------- | --------------------------------- | --------------------------- |
| `period`     | string | `14d` | `7d`, `14d`, `30d`, `90d` | Time period for analysis    |
| `content_id` | string | none    | UUID                              | Filter for specific content |

**Response:**

```json
{
  "total_views": 127450,
  "avg_engagement": 6.8,
  "total_shares": 3420,
  "saves": 890,
  "views_change_pct": 12.5,
  "engagement_change_pct": -3.2,
  "shares_change_pct": 8.7,
  "saves_change_pct": 15.3
}
```

**Field Descriptions:**

- `*_change_pct`: Percentage change compared to previous period (negative = decrease)

**Examples:**

```bash
# Dashboard for last 7 days
curl http://localhost:8003/analytics/summary?period=7d

# Performance of specific content
curl "http://localhost:8003/analytics/summary?content_id=a1b2c3d4-5678-90ab-cdef-1234567890ab"

# Last 30 days overview
curl http://localhost:8003/analytics/summary?period=30d
```

---

### 2. Timeseries Data (Line Chart)

**Endpoint:** `GET /analytics/timeseries`

**Query Parameters:**

- `period` (string): `7d`, `14d`, `30d`, `90d` (default: `14d`)
- `content_id` (string, optional): Filter for specific content

**Response:**

```json
[
  {
    "date": "2026-02-20",
    "views": 12450,
    "engagement_pct": 6.2
  },
  {
    "date": "2026-02-21",
    "views": 13890,
    "engagement_pct": 6.8
  },
  {
    "date": "2026-02-22",
    "views": 15230,
    "engagement_pct": 7.1
  }
]
```

**Example:**

```bash
curl http://localhost:8003/analytics/timeseries?period=14d
```

**Use Case:** Plot daily performance trends on a line graph.

---

### 3. Platform Performance Comparison

**Endpoint:** `GET /analytics/by-platform`

**Response:**

```json
[
  {
    "platform": "youtube",
    "posts": 15,
    "engagement_rate": 7.2
  },
  {
    "platform": "instagram",
    "posts": 23,
    "engagement_rate": 9.8
  },
  {
    "platform": "twitter",
    "posts": 48,
    "engagement_rate": 3.4
  }
]
```

**Example:**

```bash
curl http://localhost:8003/analytics/by-platform
```

**Use Case:** Bar chart comparing performance across platforms.

---

### 4. Top Performing Content

**Endpoint:** `GET /analytics/top-content`

**Purpose:** View your best performing content from your database.

**Query Parameters:**

| Parameter    | Type    | Default | Description                                         |
| ------------ | ------- | ------- | --------------------------------------------------- |
| `limit`    | integer | `10`  | Number of results to return                         |
| `platform` | string  | none    | Filter by platform (youtube, reddit, twitter, etc.) |

**Response:**

```json
[
  {
    "content_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
    "title": "10 Tips for Better Productivity",
    "platform": "youtube",
    "views": 45230,
    "engagement_pct": 8.5,
    "trend_pct": 12.3,
    "trend_direction": "up"
  },
  {
    "content_id": "b2c3d4e5-6789-01bc-def0-234567890abc",
    "title": "Python Tutorial Series",
    "platform": "youtube",
    "views": 38920,
    "engagement_pct": 7.9,
    "trend_pct": -2.1,
    "trend_direction": "down"
  }
]
```

**Field Descriptions:**

- `trend_pct`: % change in engagement (recent vs older metrics)
- `trend_direction`: `up`, `down`, or `stable`

**Examples:**

```bash
# Top 5 across all platforms
curl http://localhost:8003/analytics/top-content?limit=5

# Top 10 YouTube videos only
curl http://localhost:8003/analytics/top-content?platform=youtube&limit=10
```

---

### 5. Discover Trending Content (Market Intelligence)

**Endpoint:** `GET /analytics/discover-trending`

**Purpose:** Fetch real-time trending content from actual platforms (YouTube, Reddit, etc.) for competitive intelligence and benchmarking. This endpoint queries live platform APIs, not your database.

**Query Parameters:**

| Parameter      | Type    | Required | Description                                                    |
| -------------- | ------- | -------- | -------------------------------------------------------------- |
| `content_id` | string  | ✗*      | Your content ID to find similar trending content in same genre |
| `platform`   | string  | ✗*      | Platform to search (youtube, reddit)                           |
| `limit`      | integer | ✗       | Number of results (default: 10)                                |

*Either `content_id` or `platform` must be provided.

**Response:**

```json
[
  {
    "content_id": null,
    "title": "Unlock iPhone Without Touching it 🤣",
    "platform": "youtube",
    "post_id": "ln6t18Uoscs",
    "post_url": "https://youtube.com/watch?v=ln6t18Uoscs",
    "views": 7627163,
    "likes": 117524,
    "comments": 3107,
    "engagement_pct": 1.58,
    "published_at": "2026-02-15T10:30:00Z",
    "channel_title": "Speed McQueen",
    "thumbnail": "https://i.ytimg.com/vi/ln6t18Uoscs/hqdefault.jpg",
    "is_external": true
  },
  {
    "content_id": null,
    "title": "Samsung's Secret Screen Feature",
    "platform": "youtube",
    "post_id": "McE6el9mn_I",
    "post_url": "https://youtube.com/watch?v=McE6el9mn_I",
    "views": 7244935,
    "likes": 396059,
    "comments": 7715,
    "engagement_pct": 5.57,
    "published_at": "2026-02-20T14:20:00Z",
    "channel_title": "Marques Brownlee",
    "is_external": true
  }
]
```

**Field Descriptions:**

- `is_external`: Always `true` (indicates data from live platform, not your DB)
- `content_id`: Always `null` (external content)
- YouTube-specific: `channel_title`, `thumbnail`
- Reddit-specific: `subreddit`, `author`

**Use Cases:**

1. **Genre-Based Discovery** — Find trending content in your niche:

```bash
# Analyze your content's genre and find similar trending content
curl "http://localhost:8003/analytics/discover-trending?content_id=a1b2c3d4-5678-90ab-cdef&limit=10"
```

2. **Overall Trending** — See what's hot on a platform:

```bash
# Top trending YouTube videos right now
curl "http://localhost:8003/analytics/discover-trending?platform=youtube&limit=5"

# Hot Reddit posts
curl "http://localhost:8003/analytics/discover-trending?platform=reddit&limit=10"
```

3. **Platform Override** — Search specific platform for your genre:

```bash
# Find YouTube trending in your content's category
curl "http://localhost:8003/analytics/discover-trending?content_id=xxx&platform=youtube"
```

**How It Works:**

1. **Genre Extraction:** System analyzes your content's DNA for keywords (content_type, target_audience, tags, category)
2. **Live API Calls:** Queries YouTube/Reddit APIs for trending content matching those keywords
3. **Sorting:** Returns results sorted by view count (YouTube) or upvotes (Reddit)
4. **Real-Time:** Data is fresh from the platform, updated in real-time

**Supported Platforms:**

- ✅ **YouTube** — Search by genre + sort by views (published in last 30 days)
- ✅ **Reddit** — Hot posts from relevant subreddits
- ⏭️ Twitter, Instagram, TikTok, LinkedIn — Coming soon (returns HTTP 501)

**Performance Notes:**

- Response time: 1-3 seconds (external API calls)
- Caching recommended: Cache results for 30-60 minutes
- API quotas: Uses YouTube API quota (10,000 units/day default)

**Example Scenarios:**

**Scenario 1: Competitive Intelligence**

```bash
# You posted a Python tutorial. What's trending in Python right now?
curl "http://localhost:8003/analytics/discover-trending?content_id=my_python_video&limit=20"

# Response shows top 20 Python videos with millions of views
# Use insights: Check their titles, thumbnails, engagement patterns
```

**Scenario 2: Market Research**

```bash
# What's trending in tech on YouTube today?
curl "http://localhost:8003/analytics/discover-trending?platform=youtube&limit=10"

# What's hot on Reddit's front page?
curl "http://localhost:8003/analytics/discover-trending?platform=reddit&limit=15"
```

**Scenario 3: Benchmarking**

```bash
# Compare your engagement to trending content in your niche
# 1. Get your stats
curl "http://localhost:8003/analytics/top-content?content_id=xxx"

# 2. Get trending in your genre
curl "http://localhost:8003/analytics/discover-trending?content_id=xxx&limit=10"

# 3. Compare engagement rates
```

**Error Responses:**

```json
// No content_id or platform provided
{
  "detail": "Either content_id or platform must be provided"
}

// Platform not supported yet
{
  "detail": "Trending discovery not yet implemented for twitter. Currently supported: youtube, reddit"
}

// Content not found
{
  "detail": "Content not found"
}
```

---

## Alert Management

### 1. Get Active Alerts

**Endpoint:** `GET /alerts/`

**Query Parameters:**

- `content_id` (string, optional): Filter alerts for specific content

**Response:**

```json
[
  {
    "alert_id": "f1e2d3c4-5678-90ab-cdef-1234567890ab",
    "content_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
    "alert_type": "underperforming",
    "severity": "high",
    "message": "'10 Tips for Better Productivity' engagement (3.2%) is below predicted (6.5%)",
    "mitigation_suggestions": [
      "Re-share with updated thumbnail highlighting key benefit",
      "Post community discussion thread asking for feedback",
      "Create 1-minute teaser clip for social media cross-promotion"
    ],
    "is_resolved": false,
    "created_at": "2026-03-01T15:30:00Z"
  }
]
```

**Alert Types:**

- `underperforming`: Engagement < 70% of predicted
- `viral_spike`: Engagement > 150% of predicted
- `negative_sentiment`: Sentiment score < -0.3
- `sudden_drop`: Engagement dropped > 40% in last cycle

**Severity Levels:**

- `low`: Minor issue, informational
- `medium`: Attention recommended
- `high`: Immediate attention needed
- `critical`: Urgent action required

**Examples:**

```bash
# All active alerts
curl http://localhost:8003/alerts/

# Alerts for specific content
curl "http://localhost:8003/alerts/?content_id=a1b2c3d4-5678-90ab-cdef-1234567890ab"
```

---

### 2. Resolve Alert

**Endpoint:** `POST /alerts/{alert_id}/resolve`

**Purpose:** Mark an alert as resolved after taking action.

**Response:**

```json
{
  "message": "Alert resolved"
}
```

**Example:**

```bash
curl -X POST http://localhost:8003/alerts/f1e2d3c4-5678-90ab-cdef-1234567890ab/resolve
```

**PowerShell:**

```powershell
Invoke-RestMethod -Uri "http://localhost:8003/alerts/f1e2d3c4-5678-90ab-cdef-1234567890ab/resolve" `
  -Method Post
```

---

## AI Mitigation Suggestions

### Get Claude-Powered Suggestions

**Endpoint:** `GET /mitigations/{content_id}`

**Purpose:** Get AI-generated, actionable suggestions to improve underperforming content or manage viral content.

**Response:**

```json
{
  "content_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "underperforming",
  "reason": "Engagement is 51% below predicted baseline of 6.5%",
  "suggestions": [
    "Re-upload video with a more compelling thumbnail that shows the end result clearly",
    "Pin a comment asking viewers a specific question to boost engagement",
    "Share on Reddit's r/productivity and r/GetStudents with context about the tutorial approach"
  ]
}
```

**Status Types:**

- `underperforming`: Content not meeting expectations
- `viral_spike`: Content trending unexpectedly
- `negative_sentiment`: Audience reaction is negative
- `on_track`: Content performing as expected

**Example:**

```bash
curl http://localhost:8003/mitigations/a1b2c3d4-5678-90ab-cdef-1234567890ab
```

**Note:** Requires `ANTHROPIC_API_KEY` in `.env`. Without it, returns generic fallback suggestions.

---

## Complete Workflows

### Workflow 1: Register & Monitor New Content

```bash
# Step 1: Register content after posting
CONTENT_ID=$(curl -X POST http://localhost:8003/content/register \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Getting Started with FastAPI",
    "platform": "youtube",
    "post_id": "abc123xyz",
    "content_dna": {"tone": "educational", "target_audience": "developers"},
    "predicted_engagement": 5.5,
    "posted_at": "2026-03-01T10:00:00Z"
  }' | jq -r '.content_id')

echo "Registered content: $CONTENT_ID"

# Step 2: Wait 10 minutes for first ingestion (automatic via APScheduler)
# Or manually trigger: python -c "from scheduler import run_ingestion; run_ingestion()"

# Step 3: Check for alerts
curl "http://localhost:8003/alerts/?content_id=$CONTENT_ID"

# Step 4: Get AI suggestions if underperforming
curl "http://localhost:8003/mitigations/$CONTENT_ID"

# Step 5: View performance
curl "http://localhost:8003/analytics/summary?content_id=$CONTENT_ID"
```

---

### Workflow 2: Daily Performance Review

```bash
# Get 7-day summary
curl http://localhost:8003/analytics/summary?period=7d > summary.json

# Get all active alerts
curl http://localhost:8003/alerts/ > alerts.json

# Get top 10 performing content
curl http://localhost:8003/analytics/top-content?limit=10 > top_content.json

# Check platform performance
curl http://localhost:8003/analytics/by-platform > platforms.json

# Discover what's trending in your niche
curl "http://localhost:8003/analytics/discover-trending?platform=youtube&limit=10" > trending.json
```

---

### Workflow 3: Competitive Intelligence & Benchmarking

```bash
# 1. Get your registered content
CONTENT_LIST=$(curl http://localhost:8003/content/list)
CONTENT_ID=$(echo $CONTENT_LIST | jq -r '.[0].content_id')

# 2. Check your performance
curl "http://localhost:8003/analytics/top-content?content_id=$CONTENT_ID"

# 3. Find trending content in same genre
curl "http://localhost:8003/analytics/discover-trending?content_id=$CONTENT_ID&limit=20" > trending_competitors.json

# 4. Compare your engagement with trending content
# Manually review both results to identify gaps and opportunities
```

---

### Workflow 4: Handle Alert

```bash
# 1. Get all alerts
ALERTS=$(curl http://localhost:8003/alerts/)

# 2. Get first alert ID
ALERT_ID=$(echo $ALERTS | jq -r '.[0].alert_id')
CONTENT_ID=$(echo $ALERTS | jq -r '.[0].content_id')

# 3. Get AI suggestions
curl "http://localhost:8003/mitigations/$CONTENT_ID"

# 4. After taking action, resolve alert
curl -X POST "http://localhost:8003/alerts/$ALERT_ID/resolve"
```

---

## Response Formats

### Success Response

```json
{
  "content_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "message": "Content registered successfully"
}
```

### Error Response

```json
{
  "detail": "Content not found"
}
```

**HTTP Status Codes:**

- `200` - Success
- `404` - Resource not found
- `422` - Validation error (invalid request body)
- `500` - Internal server error

---

## Error Handling

### Common Errors

**1. Content Not Found**

```json
{
  "detail": "Content not found"
}
```

**Solution:** Verify `content_id` is correct and content is registered.

**2. No Metrics Available**

```json
{
  "detail": "No metrics found yet for this content"
}
```

**Solution:** Wait for first ingestion cycle (runs every 10 minutes) or manually trigger ingestion.

**3. Validation Error**

```json
{
  "detail": [
    {
      "loc": ["body", "platform"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Solution:** Check request body matches schema. See `/docs` for field requirements.

---

## Best Practices

### 1. Registering Content

- ✓ Register immediately after posting
- ✓ Include complete `content_dna` object
- ✓ Use correct platform-native `post_id` (not URL)
- ✓ Set accurate `predicted_engagement` for better anomaly detection

### 2. Monitoring Frequency

- Analytics: Poll every 5-15 minutes for dashboards
- Alerts: Check every 10 minutes or use webhooks (future feature)
- Top content: Refresh once per hour

### 3. Platform-Specific post_id Format

| Platform  | post_id Example            | How to Get                                                  |
| --------- | -------------------------- | ----------------------------------------------------------- |
| YouTube   | `dQw4w9WgXcQ`            | Extract from URL:`youtube.com/watch?v=dQw4w9WgXcQ`        |
| Reddit    | `abc123`                 | Extract from URL:`reddit.com/r/sub/comments/abc123/title` |
| Twitter   | Mock platform (any string) | Use Tweet ID                                                |
| Instagram | Mock platform (any string) | Use Post ID                                                 |
| LinkedIn  | Mock platform (any string) | Use Post ID                                                 |
| TikTok    | Mock platform (any string) | Use Video ID                                                |

### 4. Alert Management

- Review alerts daily
- Get AI suggestions before taking action
- Mark alerts as resolved after implementing fixes
- Track which suggestions work best

### 5. Performance Analysis

- Compare `predicted_engagement` vs actual regularly
- Use timeseries to identify posting time patterns
- Cross-reference platform performance with content types
- Archive old content after 30-90 days to keep data relevant

### 6. Using Trending Discovery

- Check trending weekly to stay informed about your niche
- Cache trending results for 30-60 minutes (expensive API calls)
- Compare your content's engagement to market average
- Use trending titles/topics for content inspiration
- Monitor competitor performance in your category

### 7. API Quota Management

- YouTube API: 10,000 units/day default quota
- Each `/discover-trending` call uses ~100 units
- Cache trending results to avoid quota exhaustion
- Use `/top-content` for frequent checks (no quota cost)
- Reserve `/discover-trending` for strategic analysis

---

## Integration Examples

### React Dashboard Component

```javascript
// Fetch summary data
const fetchDashboard = async (period = '14d') => {
  const response = await fetch(
    `http://localhost:8003/analytics/summary?period=${period}`
  );
  return await response.json();
};

// Fetch trending content for competitive insights
const fetchTrending = async (contentId, limit = 10) => {
  const response = await fetch(
    `http://localhost:8003/analytics/discover-trending?content_id=${contentId}&limit=${limit}`
  );
  return await response.json();
};

// Usage
const DashboardView = () => {
  const [data, setData] = useState(null);
  const [trending, setTrending] = useState([]);
  
  useEffect(() => {
    // Load your performance
    fetchDashboard('14d').then(setData);
  
    // Load trending in your niche
    const contentId = "your-content-id";
    fetchTrending(contentId, 5).then(setTrending);
  }, []);
  
  return (
    <div>
      <h2>Your Performance</h2>
      <KPICard title="Views" value={data?.total_views} change={data?.views_change_pct} />
      <KPICard title="Engagement" value={`${data?.avg_engagement}%`} change={data?.engagement_change_pct} />
    
      <h2>What's Trending in Your Niche</h2>
      <TrendingList items={trending} />
    </div>
  );
};
```

### Python Integration

```python
import requests

class PulseClient:
    def __init__(self, base_url="http://localhost:8003"):
        self.base_url = base_url
  
    def register_content(self, title, platform, post_id, content_dna, posted_at):
        response = requests.post(f"{self.base_url}/content/register", json={
            "title": title,
            "platform": platform,
            "post_id": post_id,
            "content_dna": content_dna,
            "posted_at": posted_at,
        })
        return response.json()
  
    def get_alerts(self, content_id=None):
        params = {"content_id": content_id} if content_id else {}
        response = requests.get(f"{self.base_url}/alerts/", params=params)
        return response.json()
  
    def get_top_content(self, limit=10, platform=None):
        params = {"limit": limit}
        if platform:
            params["platform"] = platform
        response = requests.get(f"{self.base_url}/analytics/top-content", params=params)
        return response.json()
  
    def discover_trending(self, content_id=None, platform=None, limit=10):
        """Fetch real trending content from platforms"""
        params = {"limit": limit}
        if content_id:
            params["content_id"] = content_id
        if platform:
            params["platform"] = platform
        response = requests.get(f"{self.base_url}/analytics/discover-trending", params=params)
        return response.json()

# Usage
pulse = PulseClient()

# Register content
result = pulse.register_content(
    title="My Video",
    platform="youtube",
    post_id="abc123",
    content_dna={"tone": "casual", "content_type": "tutorial"},
    posted_at="2026-03-01T10:00:00Z"
)
print(f"Registered: {result['content_id']}")

# Get your top content
my_top = pulse.get_top_content(limit=5, platform="youtube")
print(f"My top content: {len(my_top)} items")

# Discover trending in your genre
trending = pulse.discover_trending(content_id=result['content_id'], limit=10)
print(f"Found {len(trending)} trending items in your niche")
for item in trending[:3]:
    print(f"  - {item['title']}: {item['views']:,} views")
```

---

## Troubleshooting

### No data in analytics?

- Verify content is registered: `curl http://localhost:8003/content/list`
- Check if ingestion ran: View logs in service terminal
- For YouTube/Reddit: Verify API keys in `.env`
- For mock platforms: Data generates automatically

### Alerts not triggering?

- Ensure `predicted_engagement` is set when registering content
- Wait for at least 2 ingestion cycles (20 minutes)
- Check if engagement variance is within thresholds (see Alert Types)

### AI suggestions not working?

- Verify `ANTHROPIC_API_KEY` is set in `.env`
- Check API key validity at https://console.anthropic.com/
- Fallback suggestions will appear if API fails

### Trending discovery returning empty results?

- Verify `YOUTUBE_API_KEY` is set in `.env` for YouTube trending
- Check API key quota at https://console.cloud.google.com/
- Ensure either `content_id` or `platform` parameter is provided
- Reddit trending works without authentication
- Twitter/Instagram/TikTok not yet supported (returns HTTP 501)

### Trending discovery slow or timing out?

- Normal response time: 1-3 seconds (external API calls)
- YouTube API quota exhausted? Check quota usage
- Implement caching: Cache results for 30-60 minutes
- Reduce `limit` parameter to fetch fewer results faster

---

## API Rate Limits

**Current:** Unlimited (development)

**Recommended Production Limits:**

- Content registration: 100/hour per user
- Analytics: 1000/hour per user
- Alerts: 500/hour per user
- Mitigations (Claude API): 20/minute (Anthropic API limits)

---

## Support & Documentation

- **API Docs:** http://localhost:8003/docs
- **Setup Guide:** [SETUP.md](SETUP.md)
- **README:** [README.md](README.md)

---

**Last Updated:** March 2, 2026
**PULSE Version:** 1.0.0
**Total Endpoints:** 14
**Synapse Hackathon Project**
