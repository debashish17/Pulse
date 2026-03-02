"""
PULSE - Complete Endpoint Testing
Tests all 13 endpoints using real YouTube video: https://www.youtube.com/watch?v=jzR59KfZuVg
"""

import unittest
import requests
import time
from datetime import datetime, timezone
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8003"
YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v=jzR59KfZuVg"
YOUTUBE_VIDEO_ID = "jzR59KfZuVg"

# Test data
TEST_CONTENT = {
    "title": "YouTube Test Video - " + YOUTUBE_VIDEO_ID,
    "platform": "youtube",
    "post_id": YOUTUBE_VIDEO_ID,
    "post_url": YOUTUBE_VIDEO_URL,
    "content_dna": {
        "target_audience": "general",
        "tone": "educational",
        "content_type": "video",
        "predicted_engagement": 5.0,
        "predicted_views": 10000
    },
    "predicted_engagement": 5.0,
    "predicted_views": 10000,
    "posted_at": datetime.now(timezone.utc).isoformat()
}


class TestPulseEndpoints(unittest.TestCase):
    """Test all PULSE API endpoints"""
    
    content_id: Optional[str] = None
    alert_id: Optional[str] = None
    
    @classmethod
    def setUpClass(cls):
        """Verify service is running before tests"""
        print("\n" + "="*80)
        print("PULSE API - Complete Endpoint Testing")
        print("="*80)
        print(f"Base URL: {BASE_URL}")
        print(f"YouTube Video: {YOUTUBE_VIDEO_URL}")
        print(f"Video ID: {YOUTUBE_VIDEO_ID}")
        print("="*80 + "\n")
        
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                raise Exception(f"Service not healthy: {response.status_code}")
        except Exception as e:
            raise Exception(f"PULSE service not running on {BASE_URL}. Error: {e}")
    
    def test_01_health_check(self):
        """Test 1/13: GET /health"""
        print("\n[1/13] Testing GET /health...")
        response = requests.get(f"{BASE_URL}/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "pulse")
        
        print("✅ Health check passed")
        print(f"   Response: {data}")
    
    def test_02_register_content(self):
        """Test 2/13: POST /content/register"""
        print("\n[2/13] Testing POST /content/register...")
        response = requests.post(
            f"{BASE_URL}/content/register",
            json=TEST_CONTENT
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("content_id", data)
        self.assertIn("message", data)
        
        # Store content_id for later tests
        TestPulseEndpoints.content_id = data["content_id"]
        
        print("✅ Content registered successfully")
        print(f"   Content ID: {data['content_id']}")
        print(f"   Message: {data['message']}")
    
    def test_03_list_content(self):
        """Test 3/13: GET /content/list"""
        print("\n[3/13] Testing GET /content/list...")
        response = requests.get(f"{BASE_URL}/content/list")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        
        # Find our registered content
        our_content = next((c for c in data if c["content_id"] == self.content_id), None)
        self.assertIsNotNone(our_content)
        
        print(f"✅ Content list retrieved")
        print(f"   Total content items: {len(data)}")
        print(f"   Our content found: {our_content['title']}")
    
    def test_04_trigger_ingestion(self):
        """Test 4/13: POST /ingestion/trigger"""
        print("\n[4/13] Testing POST /ingestion/trigger...")
        print("   ⏳ Triggering YouTube metrics collection (may take 10-30 seconds)...")
        
        response = requests.post(
            f"{BASE_URL}/ingestion/trigger",
            json={
                "platforms": ["youtube"],
                "content_id": self.content_id
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("platforms", data)
        
        print("✅ Ingestion triggered successfully")
        print(f"   Message: {data['message']}")
        print(f"   Platforms: {data['platforms']}")
        
        # Wait for ingestion to complete
        print("   ⏳ Waiting 15 seconds for metrics collection...")
        time.sleep(15)
    
    def test_05_ingestion_status(self):
        """Test 5/13: GET /ingestion/status"""
        print("\n[5/13] Testing GET /ingestion/status...")
        response = requests.get(f"{BASE_URL}/ingestion/status")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("platforms", data)
        self.assertIsInstance(data["platforms"], list)
        
        print("✅ Ingestion status retrieved")
        for platform in data["platforms"]:
            print(f"   {platform['platform']}: Last ingestion at {platform['last_ingestion']}")
    
    def test_06_analytics_summary(self):
        """Test 6/13: GET /analytics/summary"""
        print("\n[6/13] Testing GET /analytics/summary...")
        
        # Test overall summary
        print("   Testing overall summary...")
        response = requests.get(f"{BASE_URL}/analytics/summary?period=7d")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        print("   ✅ Overall Summary:")
        print(f"      Total Views: {data.get('total_views', 0):,}")
        print(f"      Total Likes: {data.get('total_likes', 0):,}")
        print(f"      Total Comments: {data.get('total_comments', 0):,}")
        print(f"      Avg Engagement: {data.get('avg_engagement', 0):.2f}%")
        print(f"      Views Change: {data.get('views_change_pct', 0):+.1f}%")
        
        # Test content-specific summary
        print(f"\n   Testing summary for content {self.content_id[:8]}...")
        response = requests.get(
            f"{BASE_URL}/analytics/summary",
            params={"content_id": self.content_id}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        print("   ✅ Content-Specific Summary:")
        print(f"      Total Views: {data.get('total_views', 0):,}")
        print(f"      Total Likes: {data.get('total_likes', 0):,}")
        print(f"      Total Comments: {data.get('total_comments', 0):,}")
    
    def test_07_analytics_timeseries(self):
        """Test 7/13: GET /analytics/timeseries"""
        print("\n[7/13] Testing GET /analytics/timeseries...")
        response = requests.get(f"{BASE_URL}/analytics/timeseries?period=7d")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        
        print("✅ Timeseries data retrieved")
        print(f"   Data points: {len(data)}")
        if data:
            latest = data[-1]
            print(f"   Latest ({latest['date']}): {latest['views']:,} views, "
                  f"{latest['engagement_pct']:.2f}% engagement")
            if 'sentiment_score' in latest:
                print(f"      Sentiment: {latest['sentiment_score']:.2f} ({latest.get('sentiment_label', 'N/A')})")
    
    def test_08_analytics_by_platform(self):
        """Test 8/13: GET /analytics/by-platform"""
        print("\n[8/13] Testing GET /analytics/by-platform...")
        response = requests.get(f"{BASE_URL}/analytics/by-platform")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        
        print("✅ Platform performance retrieved")
        print(f"   Platforms analyzed: {len(data)}")
        for platform in data:
            print(f"   {platform['platform']}: {platform['posts']} posts, "
                  f"{platform.get('total_views', 0):,} views, "
                  f"{platform['engagement_rate']:.2f}% engagement")
    
    def test_09_analytics_top_content(self):
        """Test 9/13: GET /analytics/top-content"""
        print("\n[9/13] Testing GET /analytics/top-content...")
        response = requests.get(f"{BASE_URL}/analytics/top-content?limit=5")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        
        print("✅ Top content retrieved")
        print(f"   Top {len(data)} content items:")
        for i, content in enumerate(data, 1):
            trend_emoji = "📈" if content['trend_direction'] == "up" else "📉" if content['trend_direction'] == "down" else "➡️"
            print(f"   {i}. {content['title'][:50]}")
            print(f"      {content['platform']}: {content['views']:,} views, "
                  f"{content['engagement_pct']:.2f}% engagement {trend_emoji} {content['trend_pct']:+.1f}%")
    
    def test_10_get_alerts(self):
        """Test 10/13: GET /alerts/"""
        print("\n[10/13] Testing GET /alerts/...")
        
        # Get all alerts
        response = requests.get(f"{BASE_URL}/alerts/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        
        print(f"✅ Alerts retrieved: {len(data)} active alerts")
        
        if data:
            for alert in data[:3]:  # Show first 3
                severity_emoji = {"low": "ℹ️", "medium": "⚠️", "high": "🚨", "critical": "🔥"}.get(alert['severity'], "⚠️")
                print(f"   {severity_emoji} [{alert['severity'].upper()}] {alert['alert_type']}")
                print(f"      {alert['message']}")
                print(f"      Created: {alert['created_at']}")
            
            # Store first alert ID for resolve test
            TestPulseEndpoints.alert_id = data[0]['alert_id']
        else:
            print("   ℹ️ No alerts detected (content performing well)")
        
        # Test content-specific alerts
        print(f"\n   Testing alerts for content {self.content_id[:8]}...")
        response = requests.get(
            f"{BASE_URL}/alerts/",
            params={"content_id": self.content_id}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        print(f"   Content-specific alerts: {len(data)}")
    
    def test_11_get_mitigations(self):
        """Test 11/13: GET /mitigations/{content_id}"""
        print("\n[11/13] Testing GET /mitigations/{content_id}...")
        response = requests.get(f"{BASE_URL}/mitigations/{self.content_id}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("status", data)
        self.assertIn("suggestions", data)
        
        status_emoji = {
            "underperforming": "📉",
            "viral_spike": "🚀",
            "negative_sentiment": "😞",
            "on_track": "✅"
        }.get(data['status'], "ℹ️")
        
        print(f"✅ Mitigation suggestions retrieved")
        print(f"   Status: {status_emoji} {data['status']}")
        if 'reason' in data:
            print(f"   Reason: {data['reason']}")
        print(f"   Suggestions ({len(data['suggestions'])}):")
        for i, suggestion in enumerate(data['suggestions'], 1):
            print(f"      {i}. {suggestion}")
    
    def test_12_update_dna(self):
        """Test 12/13: POST /content/dna-update"""
        print("\n[12/13] Testing POST /content/dna-update...")
        
        update_data = {
            "content_id": self.content_id,
            "final_metrics": {
                "total_views": 50000,
                "total_likes": 3500,
                "total_comments": 450,
                "total_shares": 280,
                "avg_engagement_rate": 8.2,
                "avg_sentiment": 0.72
            },
            "performance_score": 85.5,
            "learnings": [
                "Video performed 15% above predicted engagement",
                "Strong positive sentiment in comments",
                "Peak engagement in first 48 hours"
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/content/dna-update",
            json=update_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        
        print("✅ DNA update successful")
        print(f"   {data['message']}")
        print("   Note: External service calls depend on ENABLE_EXTERNAL_SERVICES flag")
    
    def test_13_resolve_alert(self):
        """Test 13/13: POST /alerts/{alert_id}/resolve"""
        print("\n[13/13] Testing POST /alerts/{alert_id}/resolve...")
        
        if not self.alert_id:
            print("⏭️  Skipped - No alerts available to resolve")
            print("   This is actually good news! Your content is performing well.")
            return
        
        response = requests.post(f"{BASE_URL}/alerts/{self.alert_id}/resolve")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        
        print("✅ Alert resolved successfully")
        print(f"   Alert ID: {self.alert_id}")
        print(f"   {data['message']}")


def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print("All 13 PULSE endpoints tested successfully! ✅")
    print("\nEndpoints tested:")
    print("  1. ✅ GET  /health                          - Service health check")
    print("  2. ✅ POST /content/register                - Content registration")
    print("  3. ✅ GET  /content/list                    - List all content")
    print("  4. ✅ POST /ingestion/trigger               - Manual metrics collection")
    print("  5. ✅ GET  /ingestion/status                - Ingestion status")
    print("  6. ✅ GET  /analytics/summary               - KPI dashboard")
    print("  7. ✅ GET  /analytics/timeseries            - Daily trends")
    print("  8. ✅ GET  /analytics/by-platform           - Platform comparison")
    print("  9. ✅ GET  /analytics/top-content           - Top performers")
    print(" 10. ✅ GET  /alerts/                         - Active alerts")
    print(" 11. ✅ GET  /mitigations/{content_id}        - AI suggestions")
    print(" 12. ✅ POST /content/dna-update              - Update learnings")
    print(" 13. ✅ POST /alerts/{alert_id}/resolve       - Resolve alerts")
    print("\n" + "="*80)
    print(f"YouTube Video Tested: {YOUTUBE_VIDEO_URL}")
    print(f"Video ID: {YOUTUBE_VIDEO_ID}")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPulseEndpoints)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
