import os
import requests
from typing import List, Dict, Any

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_API_URL = os.getenv("NVIDIA_API_URL", "https://integrate.api.nvidia.com/v1/chat/completions")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "qwen/qwen3.5-122b-a10b")


def get_claude_mitigations(
    content_dna: Dict[str, Any],
    platform: str,
    title: str,
    predicted_engagement: float,
    actual_engagement: float,
    sentiment_score: float,
    views: int,
    status: str,
) -> List[str]:
    """
    Calls NVIDIA API (Qwen model) with content metrics.
    Returns 3 specific, actionable suggestions.
    Falls back to rule-based suggestions if the API call fails.
    """
    dna_str = "\n".join([f"  - {k}: {v}" for k, v in (content_dna or {}).items()])

    prompt = f"""You are a social media content performance analyst working in real-time.

A piece of content has been posted and you need to give immediate, actionable advice.

CONTENT DETAILS:
- Title: "{title}"
- Platform: {platform}
- Status: {status}

CONTENT DNA (original intent from creation):
{dna_str if dna_str else "  - No DNA available"}

PERFORMANCE DATA:
- Predicted engagement: {predicted_engagement:.1f}%
- Actual engagement: {actual_engagement:.1f}%
- Current views: {views}
- Sentiment score: {sentiment_score:.2f} (range: -1 is very negative, +1 is very positive)

Based on this data, give exactly 3 short, specific, actionable suggestions the creator can do RIGHT NOW to improve performance or manage this situation.

Rules:
- Each suggestion must be 1-2 sentences max
- Be specific to the platform ({platform}) and status ({status})
- No generic advice — make it concrete and immediately actionable
- Return ONLY a numbered list 1. 2. 3. with no extra text"""

    try:
        response = requests.post(
            NVIDIA_API_URL,
            headers={
                "Authorization": f"Bearer {NVIDIA_API_KEY}",
                "Accept": "application/json",
            },
            json={
                "model": NVIDIA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 400,
                "temperature": 0.60,
                "top_p": 0.95,
                "stream": False,
            },
            timeout=30,
        )
        response.raise_for_status()
        response_text = response.json()["choices"][0]["message"]["content"]

        # Parse numbered list into array
        lines = [line.strip() for line in response_text.strip().split("\n") if line.strip()]
        suggestions = []
        for line in lines:
            if line and line[0].isdigit() and len(line) > 2:
                suggestions.append(line[2:].strip() if line[1] == "." else line)

        return suggestions[:3] if suggestions else [response_text]

    except Exception as e:
        print(f"Error calling NVIDIA API: {e}")
        return get_fallback_suggestions(
            platform, status, actual_engagement, predicted_engagement, sentiment_score, views
        )


def get_fallback_suggestions(
    platform: str,
    status: str,
    actual_engagement: float,
    predicted_engagement: float,
    sentiment_score: float,
    views: int
) -> List[str]:
    """
    Rule-based suggestions when Anthropic API is not available
    """
    suggestions = []
    
    if status == "underperforming":
        suggestions.append(
            f"Boost visibility by sharing to relevant {platform} communities or groups that align with the content topic."
        )
        suggestions.append(
            "Update the post with a more engaging hook or question to encourage interaction in the comments."
        )
        suggestions.append(
            f"Consider re-posting at peak hours for {platform} (typically 11am-2pm or 7pm-9pm local time)."
        )
    
    elif status == "viral_spike":
        suggestions.append(
            "Engage actively with all comments to maintain momentum - respond to top comments within the next hour."
        )
        suggestions.append(
            f"Create a follow-up post on {platform} that continues the conversation while the topic is still trending."
        )
        suggestions.append(
            "Monitor for any emerging controversies and prepare a response if needed to protect brand reputation."
        )
    
    elif status == "negative_sentiment":
        suggestions.append(
            "Address concerns directly by posting a thoughtful response acknowledging the feedback in the comments."
        )
        suggestions.append(
            "Review the content for any unclear messaging that might be causing confusion or negative reactions."
        )
        suggestions.append(
            "Consider pinning a clarification comment to the top to provide context and turn sentiment around."
        )
    
    else:  # on_track
        suggestions.append(
            f"Content is performing well - maintain engagement by responding to comments within 1-2 hours."
        )
        suggestions.append(
            "Share to additional channels or cross-post to related communities to expand reach."
        )
        suggestions.append(
            "Track which aspects resonate most with audience for future content planning."
        )
    
    return suggestions
