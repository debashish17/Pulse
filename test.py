#!/usr/bin/env python3
"""
PULSE Service - Complete API Test Suite (Python)
Tests all endpoints to verify service functionality
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import sys

BASE_URL = "http://localhost:8003"
tests_passed = 0
tests_failed = 0


def print_header(text: str, color_code: str = "36"):
    """Print colored header"""
    print(f"\n\033[{color_code}m{text}\033[0m")


def print_success(text: str):
    """Print success message"""
    print(f"\033[32m{text}\033[0m")


def print_error(text: str):
    """Print error message"""
    print(f"\033[31m{text}\033[0m")


def print_info(text: str):
    """Print info message"""
    print(f"\033[90m{text}\033[0m")


def test_endpoint(name: str, test_func) -> Optional[Any]:
    """Execute test and track results"""
    global tests_passed, tests_failed
    
    print(f"\033[33mTesting: {name}\033[0m", end=" ")
    try:
        result = test_func()
        print("\033[32m✓\033[0m")
        tests_passed += 1
        return result
    except Exception as e:
        print("\033[31m✗\033[0m")
        print_error(f"  Error: {str(e)}")
        tests_failed += 1
        return None


def main():
    """Main test suite"""
    global tests_passed, tests_failed
    
    print_header("=" * 40)
    print_header("   PULSE Service - API Test Suite", "36")
    print_header("=" * 40)
    print(f"\nBase URL: {BASE_URL}\n")
    
    content_ids = []
    
    # Test 1: Health Check
    print_header("[1/10] Health Check", "36")
    print_header("-" * 40, "90")
    
    def test_health():
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "ok":
            raise Exception("Health check failed")
        return data
    
    health = test_endpoint("GET /health", test_health)
    if health:
        print_info(f"  Status: {health['status']}")
        print_info(f"  Service: {health['service']}")
    
    # Test 2: Register Content
    print_header("\n[2/10] Content Registration", "36")
    print_header("-" * 40, "90")
    
    # YouTube content
    def test_youtube_register():
        payload = {
            "title": "Test YouTube Video - Productivity Tips",
            "platform": "youtube",
            "post_id": "dQw4w9WgXcQ",
            "post_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "content_dna": {
                "tone": "educational",
                "target_audience": "professionals",
                "predicted_engagement": 6.5
            },
            "predicted_engagement": 6.5,
            "predicted_views": 10000,
            "posted_at": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z"
        }
        response = requests.post(f"{BASE_URL}/content/register", json=payload)
        response.raise_for_status()
        return response.json()
    
    youtube = test_endpoint("POST /content/register (YouTube)", test_youtube_register)
    if youtube:
        print_info(f"  YouTube Content ID: {youtube['content_id']}")
        content_ids.append(youtube['content_id'])
    
    # Twitter content
    def test_twitter_register():
        payload = {
            "title": "Test Tweet - Coding Best Practices",
            "platform": "twitter",
            "post_id": "tweet123456",
            "content_dna": {
                "tone": "casual",
                "target_audience": "developers",
                "predicted_engagement": 4.2
            },
            "predicted_engagement": 4.2,
            "predicted_views": 5000,
            "posted_at": (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
        }
        response = requests.post(f"{BASE_URL}/content/register", json=payload)
        response.raise_for_status()
        return response.json()
    
    twitter = test_endpoint("POST /content/register (Twitter)", test_twitter_register)
    if twitter:
        print_info(f"  Twitter Content ID: {twitter['content_id']}")
        content_ids.append(twitter['content_id'])
    
    # Instagram content
    def test_instagram_register():
        payload = {
            "title": "Test Instagram Post - Design Inspiration",
            "platform": "instagram",
            "post_id": "insta789xyz",
            "content_dna": {
                "tone": "inspiring",
                "target_audience": "designers",
                "predicted_engagement": 8.5
            },
            "predicted_engagement": 8.5,
            "predicted_views": 15000,
            "posted_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat() + "Z"
        }
        response = requests.post(f"{BASE_URL}/content/register", json=payload)
        response.raise_for_status()
        return response.json()
    
    instagram = test_endpoint("POST /content/register (Instagram)", test_instagram_register)
    if instagram:
        print_info(f"  Instagram Content ID: {instagram['content_id']}")
        content_ids.append(instagram['content_id'])
    
    # Test 3: List Content
    print_header("\n[3/10] List Content", "36")
    print_header("-" * 40, "90")
    
    def test_list_content():
        response = requests.get(f"{BASE_URL}/content/list")
        response.raise_for_status()
        data = response.json()
        if len(data) == 0:
            raise Exception("No content found")
        return data
    
    content_list = test_endpoint("GET /content/list", test_list_content)
    if content_list:
        print_info(f"  Total Content Items: {len(content_list)}")
        for item in content_list[:3]:
            print_info(f"    - {item['title']} [{item['platform']}]")
    
    # Test 4: Trigger Ingestion
    print_header("\n[4/10] Manual Ingestion Trigger", "36")
    print_header("-" * 40, "90")
    
    def test_ingestion():
        payload = {
            "platforms": ["twitter", "instagram", "youtube", "reddit"]
        }
        response = requests.post(f"{BASE_URL}/ingestion/trigger", json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Wait for background ingestion to complete
        import time
        time.sleep(3)
        return data
    
    ingestion_result = test_endpoint("POST /ingestion/trigger", test_ingestion)
    if ingestion_result:
        print_info(f"  Message: {ingestion_result['message']}")
        print_info(f"  Platforms: {', '.join(ingestion_result['platforms'])}")
    
    def test_ingestion_status():
        response = requests.get(f"{BASE_URL}/ingestion/status")
        response.raise_for_status()
        return response.json()
    
    test_endpoint("GET /ingestion/status", test_ingestion_status)
    
    # Test 5: Analytics - Summary
    print_header("\n[5/10] Analytics - Summary", "36")
    print_header("-" * 40, "90")
    
    def test_summary():
        response = requests.get(f"{BASE_URL}/analytics/summary?period=7d")
        response.raise_for_status()
        return response.json()
    
    summary = test_endpoint("GET /analytics/summary?period=7d", test_summary)
    if summary:
        print_info(f"  Total Views: {summary['total_views']}")
        print_info(f"  Avg Engagement: {summary['avg_engagement']}%")
        print_info(f"  Total Shares: {summary['total_shares']}")
        print_info(f"  Views Change: {summary['views_change_pct']}%")
    
    if content_ids:
        def test_summary_specific():
            response = requests.get(f"{BASE_URL}/analytics/summary?content_id={content_ids[0]}")
            response.raise_for_status()
            return response.json()
        
        test_endpoint("GET /analytics/summary?content_id=...", test_summary_specific)
    
    # Test 6: Analytics - Timeseries
    print_header("\n[6/10] Analytics - Timeseries", "36")
    print_header("-" * 40, "90")
    
    def test_timeseries():
        response = requests.get(f"{BASE_URL}/analytics/timeseries?period=7d")
        response.raise_for_status()
        return response.json()
    
    timeseries = test_endpoint("GET /analytics/timeseries?period=7d", test_timeseries)
    if timeseries:
        print_info(f"  Data Points: {len(timeseries)}")
        if len(timeseries) > 0:
            latest = timeseries[-1]
            print_info(f"  Latest: {latest['date']} - {latest['views']} views, {latest['engagement_pct']}% engagement")
    
    # Test 7: Analytics - By Platform
    print_header("\n[7/10] Analytics - By Platform", "36")
    print_header("-" * 40, "90")
    
    def test_platforms():
        response = requests.get(f"{BASE_URL}/analytics/by-platform")
        response.raise_for_status()
        return response.json()
    
    platforms = test_endpoint("GET /analytics/by-platform", test_platforms)
    if platforms:
        print_info(f"  Platforms: {len(platforms)}")
        for platform in platforms:
            print_info(f"    {platform['platform']}: {platform['posts']} posts, {platform['engagement_rate']}% engagement")
    
    # Test 8: Analytics - Top Content
    print_header("\n[8/10] Analytics - Top Content", "36")
    print_header("-" * 40, "90")
    
    def test_top_content():
        response = requests.get(f"{BASE_URL}/analytics/top-content?limit=5")
        response.raise_for_status()
        return response.json()
    
    top_content = test_endpoint("GET /analytics/top-content?limit=5", test_top_content)
    if top_content:
        print_info(f"  Top Content Items: {len(top_content)}")
        for item in top_content[:3]:
            print_info(f"    {item['title']}: {item['views']} views, trend: {item['trend_direction']}")
    
    # Test 9: Alerts
    print_header("\n[9/10] Alert Management", "36")
    print_header("-" * 40, "90")
    
    def test_alerts():
        response = requests.get(f"{BASE_URL}/alerts/")
        response.raise_for_status()
        return response.json()
    
    alerts = test_endpoint("GET /alerts/", test_alerts)
    if alerts is not None:
        print_info(f"  Active Alerts: {len(alerts)}")
        if len(alerts) > 0:
            first_alert = alerts[0]
            print_info(f"    Alert Type: {first_alert['alert_type']}")
            print_info(f"    Severity: {first_alert['severity']}")
            print_info(f"    Message: {first_alert['message']}")
            
            # Test resolve alert
            def test_resolve():
                response = requests.post(f"{BASE_URL}/alerts/{first_alert['alert_id']}/resolve")
                response.raise_for_status()
                return response.json()
            
            test_endpoint("POST /alerts/{id}/resolve", test_resolve)
        else:
            print_info("    No active alerts (this is good!)")
    
    if content_ids:
        def test_alerts_filtered():
            response = requests.get(f"{BASE_URL}/alerts/?content_id={content_ids[0]}")
            response.raise_for_status()
            return response.json()
        
        test_endpoint("GET /alerts/?content_id=...", test_alerts_filtered)
    
    # Test 10: Mitigations
    print_header("\n[10/10] AI Mitigation Suggestions", "36")
    print_header("-" * 40, "90")
    
    if content_ids:
        def test_mitigations():
            response = requests.get(f"{BASE_URL}/mitigations/{content_ids[0]}")
            response.raise_for_status()
            return response.json()
        
        mitigations = test_endpoint("GET /mitigations/{content_id}", test_mitigations)
        if mitigations:
            print_info(f"  Status: {mitigations['status']}")
            print_info(f"  Reason: {mitigations['reason']}")
            print_info("  Suggestions:")
            for suggestion in mitigations['suggestions']:
                print_info(f"    • {suggestion}")
    
    # Bonus: DNA Update
    print_header("\n[Bonus] DNA Update", "36")
    print_header("-" * 40, "90")
    
    if content_ids:
        def test_dna_update():
            payload = {
                "content_id": content_ids[0],
                "final_metrics": {
                    "total_views": 45230,
                    "total_likes": 2890,
                    "avg_engagement_rate": 7.8
                },
                "performance_score": 82.5,
                "learnings": [
                    "Content performed above expectations",
                    "Engagement peaked during afternoon hours"
                ]
            }
            response = requests.post(f"{BASE_URL}/content/dna-update", json=payload)
            response.raise_for_status()
            return response.json()
        
        test_endpoint("POST /content/dna-update", test_dna_update)
    
    # Summary
    print_header("\n" + "=" * 40, "36")
    print_header("          Test Summary", "36")
    print_header("=" * 40, "36")
    print()
    
    print("Tests Passed: ", end="")
    print_success(str(tests_passed))
    print("Tests Failed: ", end="")
    if tests_failed == 0:
        print_success(str(tests_failed))
    else:
        print_error(str(tests_failed))
    print()
    
    total_tests = tests_passed + tests_failed
    success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    
    print("Success Rate: ", end="")
    rate_str = f"{success_rate:.1f}%"
    if success_rate == 100:
        print_success(rate_str)
    elif success_rate >= 80:
        print(f"\033[33m{rate_str}\033[0m")
    else:
        print_error(rate_str)
    print()
    
    if tests_failed == 0:
        print_success("✓ All tests passed! PULSE service is fully functional.")
    else:
        print(f"\033[33m⚠ Some tests failed. Check errors above.\033[0m")
    
    print()
    print_header("API Documentation: http://localhost:8003/docs", "36")
    print_header("=" * 40, "36")
    print()
    
    return tests_failed


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_error("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nFatal error: {str(e)}")
        sys.exit(1)
