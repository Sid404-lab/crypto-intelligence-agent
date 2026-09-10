import os
from groq import Groq
from config import ROOT


def generate_ai_briefing(markets, news, listings):
    """
    Generate AI morning briefing using Groq API.
    
    Returns dict with:
    - morning_summary: Daily market overview
    - market_sentiment: Overall market mood (bullish/bearish/neutral)
    - things_to_watch: List of key items to monitor
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return {
            "morning_summary": "AI briefing unavailable - GROQ_API_KEY not configured",
            "market_sentiment": "unknown",
            "things_to_watch": ["Configure GROQ_API_KEY to enable AI briefing"]
        }
    
    try:
        client = Groq(api_key=api_key)
        
        # Prepare context for the AI
        market_context = "\n".join([
            f"{m['symbol']}: ${m['price']:.2f} ({m['change_24h']:+.2f}%) - {m.get('source', 'unknown')}"
            for m in (markets or [])[:10]
        ])
        
        news_context = "\n".join([
            f"- {item['title']} ({item['source']})"
            for item in (news or [])[:8]
        ])
        
        listings_context = "\n".join([
            f"- {item['name']} ({item['symbol']}): {item['note']}"
            for item in (listings or [])[:5]
        ])
        
        prompt = f"""You are a crypto market intelligence analyst. Generate a concise morning briefing based on the following data:

MARKET DATA:
{market_context if market_context else "No market data available"}

RECENT NEWS:
{news_context if news_context else "No news available"}

NEW LISTINGS:
{listings_context if listings_context else "No listings available"}

Return your response as a JSON object with exactly these keys:
- morning_summary: 2-3 sentences summarizing the overall market situation
- market_sentiment: one word only - "bullish", "bearish", or "neutral"
- things_to_watch: an array of 3-5 specific items to monitor today (short, actionable items)

Be concise, professional, and focus on actionable insights. JSON format only, no other text."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a crypto market analyst. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024,
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        
        # Validate and normalize the response
        return {
            "morning_summary": result.get("morning_summary", "AI briefing generation incomplete"),
            "market_sentiment": result.get("market_sentiment", "neutral").lower(),
            "things_to_watch": result.get("things_to_watch", [])
        }
        
    except Exception as e:
        return {
            "morning_summary": f"AI briefing error: {str(e)}",
            "market_sentiment": "unknown",
            "things_to_watch": ["AI briefing generation failed"]
        }
