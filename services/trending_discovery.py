"""
Trending Discovery Service
Fetches real trending content from actual platforms based on genre/category
"""

from googleapiclient.discovery import build
import requests
import os
from typing import List, Dict, Optional


def extract_genre_keywords(content_dna: dict) -> List[str]:
    """
    Extract searchable keywords from content DNA.
    Returns list of keywords for platform searches.
    """
    keywords = []
    
    # Extract from common DNA fields
    if content_dna:
        # Content type
        if content_type := content_dna.get("content_type"):
            keywords.append(content_type)
        
        # Target audience
        if audience := content_dna.get("target_audience"):
            keywords.append(audience)
        
        # Topic/niche
        if topic := content_dna.get("topic"):
            keywords.append(topic)
        
        # Tags
        if tags := content_dna.get("tags", []):
            keywords.extend(tags[:3])  # Max 3 tags
        
        # Category
        if category := content_dna.get("category"):
            keywords.append(category)
    
    return keywords[:5]  # Max 5 keywords


def get_youtube_trending(genre_keywords: Optional[List[str]] = None, limit: int = 10) -> List[Dict]:
    """
    Fetch real trending YouTube videos.
    
    Args:
        genre_keywords: List of keywords for genre-specific search (e.g., ["python", "tutorial"])
        limit: Number of results to return
    
    Returns:
        List of trending video info with stats
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return []
    
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        
        if genre_keywords and len(genre_keywords) > 0:
            # Search for trending content in specific genre
            search_query = " ".join(genre_keywords)
            
            search_response = youtube.search().list(
                q=search_query,
                part="id,snippet",
                type="video",
                order="viewCount",  # Most viewed
                maxResults=limit,
                publishedAfter=(datetime.utcnow() - timedelta(days=30)).isoformat() + "Z",  # Last 30 days
                relevanceLanguage="en"
            ).execute()
            
            video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
        else:
            # Get overall trending videos (most popular category)
            videos_response = youtube.videos().list(
                part="id,snippet,statistics",
                chart="mostPopular",
                regionCode="US",
                maxResults=limit,
                videoCategoryId="28"  # Science & Technology - adjust as needed
            ).execute()
            
            video_ids = [item["id"] for item in videos_response.get("items", [])]
        
        if not video_ids:
            return []
        
        # Get detailed stats for all videos
        stats_response = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids)
        ).execute()
        
        results = []
        for video in stats_response.get("items", []):
            stats = video["statistics"]
            snippet = video["snippet"]
            
            view_count = int(stats.get("viewCount", 0))
            like_count = int(stats.get("likeCount", 0))
            comment_count = int(stats.get("commentCount", 0))
            
            # Calculate engagement rate
            engagement_rate = 0.0
            if view_count > 0:
                engagement_rate = ((like_count + comment_count) / view_count) * 100
            
            results.append({
                "content_id": None,  # External content
                "title": snippet.get("title", ""),
                "platform": "youtube",
                "post_id": video["id"],
                "post_url": f"https://youtube.com/watch?v={video['id']}",
                "views": view_count,
                "likes": like_count,
                "comments": comment_count,
                "engagement_pct": round(engagement_rate, 2),
                "published_at": snippet.get("publishedAt", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                "is_external": True  # Flag that this is not from our DB
            })
        
        return results
    
    except Exception as e:
        print(f"Error fetching YouTube trending: {e}")
        return []


def get_reddit_trending(genre_keywords: Optional[List[str]] = None, limit: int = 10) -> List[Dict]:
    """
    Fetch real trending Reddit posts.
    
    Args:
        genre_keywords: Keywords to find relevant subreddit (e.g., ["python", "programming"])
        limit: Number of results to return
    
    Returns:
        List of trending post info with stats
    """
    try:
        if genre_keywords and len(genre_keywords) > 0:
            # Try to find relevant subreddit
            subreddit = genre_keywords[0].lower()
            # Common mappings
            subreddit_map = {
                "python": "python",
                "javascript": "javascript",
                "programming": "programming",
                "tech": "technology",
                "design": "design",
                "gaming": "gaming",
                "fitness": "fitness",
                "cooking": "cooking"
            }
            subreddit = subreddit_map.get(subreddit, subreddit)
        else:
            # Default to popular subreddit
            subreddit = "all"
        
        # Fetch hot posts from subreddit
        url = f"https://www.reddit.com/r/{subreddit}/hot.json"
        headers = {"User-Agent": "PULSE-Analytics/1.0"}
        
        response = requests.get(url, headers=headers, params={"limit": limit})
        response.raise_for_status()
        
        data = response.json()
        posts = data.get("data", {}).get("children", [])
        
        results = []
        for post in posts[:limit]:
            post_data = post.get("data", {})
            
            upvotes = post_data.get("ups", 0)
            num_comments = post_data.get("num_comments", 0)
            
            # Estimate views (Reddit doesn't provide this)
            estimated_views = upvotes * 100
            
            # Calculate engagement
            engagement_rate = 0.0
            if estimated_views > 0:
                engagement_rate = ((upvotes + num_comments) / estimated_views) * 100
            
            results.append({
                "content_id": None,
                "title": post_data.get("title", ""),
                "platform": "reddit",
                "post_id": post_data.get("id", ""),
                "post_url": f"https://reddit.com{post_data.get('permalink', '')}",
                "views": estimated_views,
                "likes": upvotes,
                "comments": num_comments,
                "engagement_pct": round(engagement_rate, 2),
                "published_at": None,
                "subreddit": post_data.get("subreddit", ""),
                "author": post_data.get("author", ""),
                "is_external": True
            })
        
        return results
    
    except Exception as e:
        print(f"Error fetching Reddit trending: {e}")
        return []


def get_platform_trending(platform: str, genre_keywords: Optional[List[str]] = None, limit: int = 10) -> List[Dict]:
    """
    Universal function to get trending content from any platform.
    
    Args:
        platform: Platform name (youtube, reddit, twitter, instagram, etc.)
        genre_keywords: Optional keywords for genre-specific results
        limit: Number of results
    
    Returns:
        List of trending content
    """
    if platform == "youtube":
        return get_youtube_trending(genre_keywords, limit)
    elif platform == "reddit":
        return get_reddit_trending(genre_keywords, limit)
    elif platform == "twitter":
        # TODO: Twitter trending API (requires Twitter API v2 access)
        return []
    elif platform == "instagram":
        # TODO: Instagram trending (requires Facebook Graph API)
        return []
    elif platform == "tiktok":
        # TODO: TikTok trending API
        return []
    elif platform == "linkedin":
        # TODO: LinkedIn trending (limited API access)
        return []
    else:
        return []


# Add missing imports
from datetime import datetime, timedelta
