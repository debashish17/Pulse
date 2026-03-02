"""
Test the new Trending Discovery feature
Fetches REAL trending content from YouTube/Reddit based on genre
"""

import requests
import json

BASE_URL = "http://localhost:8003"

def print_trending(title, data):
    """Pretty print trending results"""
    print(f"\n{'='*100}")
    print(title)
    print('='*100)
    
    if not data:
        print("❌ No trending content found")
        return
    
    for i, item in enumerate(data, 1):
        print(f"\n{i}. {item['title'][:80]}")
        print(f"   🌐 Platform: {item['platform'].upper()}")
        print(f"   🔗 URL: {item['post_url']}")
        print(f"   📊 Views: {item['views']:,}")
        print(f"   👍 Likes: {item['likes']:,}")
        print(f"   💬 Comments: {item['comments']:,}")
        print(f"   📈 Engagement: {item['engagement_pct']:.2f}%")
        
        if item.get('channel_title'):
            print(f"   📺 Channel: {item['channel_title']}")
        if item.get('subreddit'):
            print(f"   📱 Subreddit: r/{item['subreddit']}")
        if item.get('is_external'):
            print(f"   ✨ Source: REAL platform data (live trending)")

print("\n🔥 PULSE - Trending Discovery Feature")
print("="*100)
print("This feature fetches REAL trending content from YouTube, Reddit, etc.")
print("Perfect for competitive intelligence and benchmarking!")
print("="*100)

# First, get a content_id from our database to use as reference
print("\n📋 Step 1: Get registered content to use as reference...")
response = requests.get(f"{BASE_URL}/content/list")
contents = response.json()

if not contents:
    print("❌ No content registered. Please register some content first.")
    exit(1)

# Find a YouTube video
youtube_content = next((c for c in contents if c['platform'] == 'youtube'), None)

if youtube_content:
    content_id = youtube_content['content_id']
    print(f"✅ Found YouTube content: {youtube_content['title']}")
    print(f"   Content ID: {content_id}")
else:
    print("⚠️  No YouTube content found. Using first available content.")
    content_id = contents[0]['content_id']

# Test 1: Get trending based on our content's genre
print("\n\n" + "="*100)
print("TEST 1: Discover trending content in same genre as our video")
print("="*100)
print(f"Using content_id: {content_id}")
print("The system will analyze your content's DNA and fetch trending videos in the same genre...")

try:
    response = requests.get(
        f"{BASE_URL}/analytics/discover-trending",
        params={"content_id": content_id, "limit": 5}
    )
    if response.status_code == 200:
        print_trending("🎯 TRENDING IN YOUR GENRE", response.json())
    else:
        print(f"❌ Error: {response.status_code} - {response.json()}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Get overall YouTube trending
print("\n\n" + "="*100)
print("TEST 2: Discover top trending YouTube videos (overall)")
print("="*100)

try:
    response = requests.get(
        f"{BASE_URL}/analytics/discover-trending",
        params={"platform": "youtube", "limit": 5}
    )
    if response.status_code == 200:
        print_trending("🔥 TOP TRENDING ON YOUTUBE", response.json())
    else:
        print(f"❌ Error: {response.status_code} - {response.json()}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Get Reddit trending
print("\n\n" + "="*100)
print("TEST 3: Discover trending Reddit posts")
print("="*100)

try:
    response = requests.get(
        f"{BASE_URL}/analytics/discover-trending",
        params={"platform": "reddit", "limit": 5}
    )
    if response.status_code == 200:
        print_trending("🔥 TRENDING ON REDDIT", response.json())
    else:
        print(f"❌ Error: {response.status_code} - {response.json()}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Get genre-specific trending using our content
if youtube_content:
    print("\n\n" + "="*100)
    print("TEST 4: Discover trending with explicit platform override")
    print("="*100)
    
    try:
        response = requests.get(
            f"{BASE_URL}/analytics/discover-trending",
            params={
                "content_id": content_id,
                "platform": "youtube",
                "limit": 3
            }
        )
        if response.status_code == 200:
            print_trending("🎯 YOUTUBE TRENDING (GENRE-SPECIFIC)", response.json())
        else:
            print(f"❌ Error: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")

# Summary
print("\n\n" + "="*100)
print("✅ TRENDING DISCOVERY TEST COMPLETE!")
print("="*100)
print("\n📚 Usage Guide:")
print("   1. GET /analytics/discover-trending?content_id=xxx")
print("      → Finds trending content in same genre as your content")
print()
print("   2. GET /analytics/discover-trending?platform=youtube&limit=10")
print("      → Top 10 trending videos on YouTube (overall)")
print()
print("   3. GET /analytics/discover-trending?content_id=xxx&platform=reddit")
print("      → Reddit trending in your content's genre")
print()
print("\n🎯 Use Cases:")
print("   • Competitive intelligence: See what's trending in your niche")
print("   • Benchmarking: Compare your content to top performers")
print("   • Inspiration: Discover successful content patterns")
print("   • Timing: Identify trending topics to capitalize on")
print("="*100 + "\n")
