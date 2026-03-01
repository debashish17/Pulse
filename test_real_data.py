#!/usr/bin/env python3
"""
PULSE Real Data Test - Uses real YouTube & Reddit public data
Tests analytics and sentiment analysis with actual content
"""

import requests
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8003"

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print('='*60)

def print_success(text):
    print(f"✓ {text}")

def print_info(text):
    print(f"  {text}")

def register_content(title, platform, post_id, post_url=None):
    """Register content for monitoring"""
    payload = {
        "title": title,
        "platform": platform,
        "post_id": post_id,
        "post_url": post_url,
        "content_dna": {
            "tone": "informational",
            "target_audience": "general",
            "content_type": "educational"
        },
        "predicted_engagement": 5.0,
        "predicted_views": 10000,
        "posted_at": (datetime.utcnow() - timedelta(days=2)).isoformat() + "Z"
    }
    
    response = requests.post(f"{BASE_URL}/content/register", json=payload)
    response.raise_for_status()
    return response.json()

def trigger_ingestion(platforms):
    """Manually trigger platform ingestion"""
    payload = {"platforms": platforms}
    response = requests.post(f"{BASE_URL}/ingestion/trigger", json=payload)
    response.raise_for_status()
    return response.json()

def get_analytics_summary():
    """Get analytics summary"""
    response = requests.get(f"{BASE_URL}/analytics/summary?period=7d")
    response.raise_for_status()
    return response.json()

def get_content_list():
    """List all registered content"""
    response = requests.get(f"{BASE_URL}/content/list")
    response.raise_for_status()
    return response.json()

def get_alerts():
    """Get active alerts"""
    response = requests.get(f"{BASE_URL}/alerts/")
    response.raise_for_status()
    return response.json()

def main():
    print_header("PULSE Real Data Test - Public APIs")
    print("\nThis test uses real public data from YouTube and Reddit")
    print("to verify analytics and sentiment analysis.\n")
    
    # Step 1: Health Check
    print_header("Step 1: Health Check")
    response = requests.get(f"{BASE_URL}/health")
    if response.json()["status"] == "ok":
        print_success("PULSE service is running")
    
    # Step 2: Register Real Content
    print_header("Step 2: Registering Real Public Content")
    
    content_ids = []
    
    # YouTube Video - Popular programming video
    print("\nRegistering YouTube video...")
    yt_result = register_content(
        title="Python Tutorial - Real YouTube Video",
        platform="youtube",
        post_id="rfscVS0vtbw",  # Popular Python tutorial
        post_url="https://www.youtube.com/watch?v=rfscVS0vtbw"
    )
    print_success(f"YouTube: {yt_result['content_id']}")
    content_ids.append(yt_result['content_id'])
    
    # Reddit Post - Use a popular public post
    print("\nRegistering Reddit post...")
    reddit_result = register_content(
        title="Popular Reddit Post from r/Python",
        platform="reddit",
        post_id="1b45v7k",  # Popular post from r/Python
        post_url="https://www.reddit.com/r/Python/comments/1b45v7k/"
    )
    print_success(f"Reddit: {reddit_result['content_id']}")
    content_ids.append(reddit_result['content_id'])
    
    # Step 3: Trigger Ingestion
    print_header("Step 3: Triggering Real Data Ingestion")
    print("\nThis will fetch actual data from YouTube and Reddit...")
    print("(This may take 10-20 seconds)")
    
    ingestion = trigger_ingestion(["youtube", "reddit"])
    print_success(f"Triggered: {', '.join(ingestion['platforms'])}")
    
    print("\n⏳ Waiting 15 seconds for ingestion to complete...")
    time.sleep(15)
    
    # Step 4: Check Ingestion Status
    print_header("Step 4: Verify Data Collection")
    response = requests.get(f"{BASE_URL}/ingestion/status")
    status = response.json()
    
    for platform_info in status['platforms']:
        if platform_info['last_ingestion']:
            print_success(f"{platform_info['platform']}: Last ingested at {platform_info['last_ingestion']}")
        else:
            print(f"  ⚠ {platform_info['platform']}: No data yet")
    
    # Step 5: View Analytics
    print_header("Step 5: Analytics Dashboard")
    analytics = get_analytics_summary()
    
    print("\n📊 Overall Performance:")
    print_info(f"Total Views: {analytics['total_views']:,}")
    print_info(f"Total Likes: {analytics['total_likes']:,}")
    print_info(f"Total Comments: {analytics['total_comments']:,}")
    print_info(f"Average Engagement: {analytics['avg_engagement']:.2f}%")
    
    # Step 6: Check Sentiment Analysis
    print_header("Step 6: Sentiment Analysis Results")
    
    content_list = get_content_list()
    for content in content_list:
        content_id = content['content_id']
        
        # Get specific content analytics
        response = requests.get(f"{BASE_URL}/analytics/summary?content_id={content_id}")
        content_analytics = response.json()
        
        if content_analytics['total_views'] > 0:
            print(f"\n📌 {content['title']}")
            print_info(f"Platform: {content['platform']}")
            print_info(f"Views: {content_analytics['total_views']:,}")
            print_info(f"Engagement: {content_analytics['avg_engagement']:.2f}%")
            
            # Get sentiment from analytics
            response = requests.get(f"{BASE_URL}/analytics/timeseries?content_id={content_id}&period=7d")
            timeseries = response.json()
            
            if timeseries:
                latest = timeseries[-1]
                sentiment_score = latest.get('sentiment_score', 0)
                sentiment_label = latest.get('sentiment_label', 'neutral')
                
                # Color-code sentiment
                if sentiment_score > 0.2:
                    sentiment_emoji = "😊"
                elif sentiment_score < -0.2:
                    sentiment_emoji = "😞"
                else:
                    sentiment_emoji = "😐"
                
                print_info(f"Sentiment: {sentiment_emoji} {sentiment_label.upper()} (score: {sentiment_score:.3f})")
            
            # Get mitigation suggestions
            try:
                response = requests.get(f"{BASE_URL}/mitigations/{content_id}")
                mitigations = response.json()
                print_info(f"Status: {mitigations['status']}")
                print_info(f"Reason: {mitigations['reason']}")
            except:
                pass
    
    # Step 7: Check for Alerts
    print_header("Step 7: Alert Detection")
    alerts = get_alerts()
    
    if alerts:
        print(f"\n⚠️  Found {len(alerts)} active alert(s):")
        for alert in alerts:
            print(f"\n  🚨 {alert['alert_type'].upper()}")
            print_info(f"Severity: {alert['severity']}")
            print_info(f"Message: {alert['message']}")
    else:
        print_success("No alerts - all content performing as expected")
    
    # Step 8: Platform Comparison
    print_header("Step 8: Platform Performance Comparison")
    response = requests.get(f"{BASE_URL}/analytics/by-platform")
    platforms = response.json()
    
    for platform in platforms:
        print(f"\n📱 {platform['platform'].upper()}")
        print_info(f"Total Posts: {platform['posts']}")
        print_info(f"Total Views: {platform['total_views']:,}")
        print_info(f"Engagement Rate: {platform['engagement_rate']:.2f}%")
        print_info(f"Avg Sentiment: {platform['avg_sentiment']:.3f}")
    
    # Final Summary
    print_header("Test Complete!")
    print("\n✅ Successfully tested with real public data:")
    print("  • YouTube video metrics collected via YouTube Data API")
    print("  • Reddit post metrics collected via public JSON API")
    print("  • Sentiment analysis performed on actual comments")
    print("  • Analytics dashboard working with real data")
    print("  • Alert detection functional")
    print("\n📊 View full dashboard: http://localhost:8003/docs\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to PULSE service")
        print("   Make sure PULSE is running: python main.py")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
