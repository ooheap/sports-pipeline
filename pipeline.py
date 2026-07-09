"""Full pipeline: fetch ESPN news -> filter -> graphic -> Instagram.

Run modes:
  python pipeline.py            dry run: fetches, filters, makes graphics,
                                prints what it WOULD post. Safe to test.
  python pipeline.py --live     actually publishes to Instagram.
"""

import json
import re
import sys
import time

from espn_fetcher import fetch_new_articles
from news_filter import evaluate
from make_graphic import make_graphic

MAX_POSTS_PER_RUN = 3  # avoid flooding if the pipeline was down for a while


def slugify(text, max_len=40):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:max_len]


def build_caption(article, headline):
    tags = {
        "nfl": "#nfl #football #breakingnews",
        "nba": "#nba #basketball #breakingnews",
        "mlb": "#mlb #baseball #breakingnews",
    }
    parts = [headline]
    if article["description"]:
        parts.append(article["description"])
    parts.append("(via ESPN)")
    parts.append(tags.get(article["league"], "#sports #breakingnews"))
    return "\n\n".join(parts)


def run(live=False):
    articles = fetch_new_articles()
    print(f"{len(articles)} new articles found")

    posted = 0
    for art in articles:
        if posted >= MAX_POSTS_PER_RUN:
            break

        should_post, headline = evaluate(art)
        if not should_post:
            continue

        filename = f"{int(time.time())}-{slugify(headline)}.png"
        make_graphic(headline, art["league"], out_path=f"output/{filename}")
        caption = build_caption(art, headline)

        print(f"\n--- POST ({art['league'].upper()}) ---")
        print(f"headline: {headline}")
        print(f"image:    output/{filename}")

        if live:
            from post_instagram import post_to_instagram
            media_id = post_to_instagram(filename, caption)
            print(f"published: {media_id}")
        else:
            queue_post(filename, caption)
            print("queued in pending.json")

        posted += 1

    print(f"\ndone: {posted} post(s) {'published' if live else 'prepared'}")


def queue_post(filename, caption):
    """Add a prepared post to pending.json for publish_pending.py."""
    try:
        with open("pending.json") as f:
            pending = json.load(f)
    except FileNotFoundError:
        pending = []
    pending.append({"filename": filename, "caption": caption})
    with open("pending.json", "w") as f:
        json.dump(pending, f, indent=2)


if __name__ == "__main__":
    run(live="--live" in sys.argv)
