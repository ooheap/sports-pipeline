"""Publish everything in pending.json to Instagram, then clear the queue.

Runs as the last workflow step, after the generated images have been
committed and pushed, so their raw.githubusercontent.com URLs resolve.
Skips silently if Instagram secrets are not configured yet, which lets
you run the whole pipeline before the Meta setup is finished.
"""

import json
import os

from post_instagram import post_to_instagram


def main():
    if not os.environ.get("IG_ACCESS_TOKEN"):
        print("Instagram secrets not set, skipping publish")
        return

    try:
        with open("pending.json") as f:
            pending = json.load(f)
    except FileNotFoundError:
        pending = []

    if not pending:
        print("nothing to publish")
        return

    remaining = []
    for item in pending:
        try:
            media_id = post_to_instagram(item["filename"], item["caption"])
            print(f"published {item['filename']} -> {media_id}")
        except Exception as e:
            print(f"failed {item['filename']}: {e}")
            remaining.append(item)  # retry next run

    with open("pending.json", "w") as f:
        json.dump(remaining, f, indent=2)


if __name__ == "__main__":
    main()
