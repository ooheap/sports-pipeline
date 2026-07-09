"""Fetch recent news from ESPN's public JSON endpoints and return new stories."""

import json
import os
import requests

LEAGUES = {
    "nfl": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/news",
    "nba": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/news",
    "mlb": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/news",
}

SEEN_FILE = "posted.json"


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    # Keep the file from growing forever; 2000 ids is plenty of history
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen)[-2000:], f, indent=2)


def parse_article(raw, league):
    """Pull the fields we care about out of one ESPN article object."""
    return {
        "id": str(raw.get("dataSourceIdentifier") or raw.get("links", {})
                  .get("web", {}).get("href", raw.get("headline", ""))),
        "league": league,
        "headline": raw.get("headline", ""),
        "description": raw.get("description", ""),
        "published": raw.get("published", ""),
        "type": raw.get("type", ""),
        "url": raw.get("links", {}).get("web", {}).get("href", ""),
    }


def fetch_new_articles():
    """Return articles we have not seen before, across all leagues."""
    seen = load_seen()
    new_articles = []

    for league, url in LEAGUES.items():
        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
        except (requests.RequestException, ValueError) as e:
            print(f"[{league}] fetch failed: {e}")
            continue

        for raw in articles:
            art = parse_article(raw, league)
            if art["id"] and art["id"] not in seen:
                new_articles.append(art)
                seen.add(art["id"])

    save_seen(seen)
    return new_articles


if __name__ == "__main__":
    for a in fetch_new_articles():
        print(f"[{a['league'].upper()}] {a['headline']}")
        print(f"    {a['description'][:100]}")
        print()
