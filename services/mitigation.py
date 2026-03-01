import os
from typing import List, Dict, Any

# Only initialize Anthropic client if API key is provided
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your_anthropic_key":
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    ANTHROPIC_ENABLED = True
else:
    client = None
    ANTHROPIC_ENABLED = False
    print("⚠️  Anthropic API key not configured - using fallback suggestions")


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
    Calls Claude API with content DNA and current performance metrics.
    Returns 3 specific, actionable mitigation suggestions.
    Falls back to rule-based suggestions if API key not available.
    """
    
    # If Anthropic is not configured, return rule-based suggestions
    if not ANTHROPIC_ENABLED:
        return get_fallback_suggestions(
            platform, status, actual_engagement, predicted_engagement, sentiment_score, views
        )

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
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = message.content[0].text

        # Parse numbered list into array
        lines = [line.strip() for line in response_text.strip().split("\n") if line.strip()]
        suggestions = []
        for line in lines:
            # Remove numbering like "1." "2." "3."
            if line and line[0].isdigit() and len(line) > 2:
                suggestions.append(line[2:].strip() if line[1] == "." else line)

        return suggestions[:3] if suggestions else [response_text]

    except Exception as e:
        print(f"Error calling Anthropic API: {e}")
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
