"""Decide whether an ESPN article is breaking news worth posting.

Two layers:
1. Fast keyword filter (free, always on) to skip obvious non-news.
2. Optional Claude call to classify borderline cases and write a punchy
   headline. Set ANTHROPIC_API_KEY to enable it; without a key the
   keyword filter runs alone and the original headline is used.
"""

import json
import os

BREAKING_KEYWORDS = [
    "trade", "traded", "sign", "signs", "signing", "agrees", "agreement",
    "waive", "waived", "release", "released", "fired", "hired", "hires",
    "suspend", "suspended", "injury", "injured", "out for season", "torn",
    "extension", "deal", "acquire", "acquires", "retire", "retires",
    "activated", "ruled out", "surgery", "arrest", "franchise tag",
]

SKIP_KEYWORDS = [
    "fantasy", "power rankings", "betting", "odds", "expert picks",
    "our picks", "predictions", "mock draft", "takeaways", "grades",
    "best bets", "quiz", "how to watch", "schedule release", "top plays",
    "highlights", "buy or sell", "biggest questions",
]


def keyword_check(article):
    text = f"{article['headline']} {article['description']}".lower()
    if any(k in text for k in SKIP_KEYWORDS):
        return False
    return any(k in text for k in BREAKING_KEYWORDS)


def llm_check(article):
    """Ask Claude to classify and write a headline. Returns dict or None."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    import requests

    prompt = (
        "You review sports news for a breaking-news Instagram page. "
        "Reply with ONLY a JSON object, no other text, in this format: "
        '{"post": true/false, "headline": "..."}. '
        "Set post to true only for genuine breaking news: trades, signings, "
        "major injuries, firings, retirements, suspensions. Not analysis, "
        "recaps, fantasy, or opinion. The headline must be under 12 words, "
        "punchy, all caps for the key name, factual.\n\n"
        f"Headline: {article['headline']}\n"
        f"Description: {article['description']}"
    )

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"]
        return json.loads(text.replace("```json", "").replace("```", "").strip())
    except Exception as e:
        print(f"LLM check failed, falling back to keywords: {e}")
        return None


def evaluate(article):
    """Return (should_post, headline_to_use)."""
    llm = llm_check(article)
    if llm is not None:
        return llm.get("post", False), llm.get("headline") or article["headline"]
    return keyword_check(article), article["headline"]
