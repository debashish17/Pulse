"""
Test the enhanced top-content endpoint with platform filtering
"""
import requests
import json

BASE_URL = "http://localhost:8003"

def print_results(title, data):
    """Pretty print results"""
    print(f"\n{'='*80}")
    print(title)
    print('='*80)
    if not data:
        print("No content found")
        return
    
    for i, item in enumerate(data, 1):
        trend_emoji = "📈" if item['trend_direction'] == "up" else "📉" if item['trend_direction'] == "down" else "➡️"
        print(f"\n{i}. {item['title'][:60]}")
        print(f"   Platform: {item['platform']}")
        print(f"   Views: {item['views']:,}")
        print(f"   Engagement: {item['engagement_pct']}%")
        print(f"   Trend: {trend_emoji} {item['trend_pct']:+.1f}%")

print("\n🔍 Testing Top Content Endpoint with Platform Filtering")
print("="*80)

# Test 1: All platforms (original behavior)
print("\n[Test 1] All platforms (no filter)")
response = requests.get(f"{BASE_URL}/analytics/top-content?limit=10")
print_results("TOP CONTENT - ALL PLATFORMS", response.json())

# Test 2: YouTube only
print("\n[Test 2] YouTube only")
response = requests.get(f"{BASE_URL}/analytics/top-content?platform=youtube&limit=5")
print_results("TOP CONTENT - YOUTUBE ONLY", response.json())

# Test 3: Reddit only
print("\n[Test 3] Reddit only")
response = requests.get(f"{BASE_URL}/analytics/top-content?platform=reddit&limit=5")
print_results("TOP CONTENT - REDDIT ONLY", response.json())

# Test 4: Instagram only
print("\n[Test 4] Instagram only (mock data)")
response = requests.get(f"{BASE_URL}/analytics/top-content?platform=instagram&limit=5")
print_results("TOP CONTENT - INSTAGRAM ONLY", response.json())

# Test 5: Twitter only
print("\n[Test 5] Twitter only (mock data)")
response = requests.get(f"{BASE_URL}/analytics/top-content?platform=twitter&limit=5")
print_results("TOP CONTENT - TWITTER ONLY", response.json())

print("\n" + "="*80)
print("✅ All tests completed!")
print("="*80)
print("\nUsage:")
print("  All platforms:  GET /analytics/top-content?limit=10")
print("  YouTube only:   GET /analytics/top-content?platform=youtube&limit=5")
print("  Reddit only:    GET /analytics/top-content?platform=reddit&limit=5")
print("="*80 + "\n")
