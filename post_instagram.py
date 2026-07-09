"""Publish an image to Instagram via the Meta Graph API.

Requires three environment variables (set as GitHub Actions secrets):
  IG_USER_ID       your Instagram professional account ID
  IG_ACCESS_TOKEN  a long-lived access token
  IMAGE_BASE_URL   public base URL where images are hosted, e.g.
                   https://raw.githubusercontent.com/you/repo/main/output

The Graph API cannot accept a file upload directly. The image must
already live at a public URL, so the pipeline commits the PNG to the
repo first and references its raw URL.
"""

import os
import time
import requests

GRAPH = "https://graph.facebook.com/v21.0"


def post_to_instagram(image_filename, caption):
    user_id = os.environ["IG_USER_ID"]
    token = os.environ["IG_ACCESS_TOKEN"]
    image_url = f"{os.environ['IMAGE_BASE_URL']}/{image_filename}"

    # Step 1: create a media container
    r = requests.post(
        f"{GRAPH}/{user_id}/media",
        data={"image_url": image_url, "caption": caption, "access_token": token},
        timeout=30,
    )
    r.raise_for_status()
    container_id = r.json()["id"]

    # Step 2: wait briefly for Meta to fetch and process the image
    time.sleep(8)

    # Step 3: publish
    r = requests.post(
        f"{GRAPH}/{user_id}/media_publish",
        data={"creation_id": container_id, "access_token": token},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["id"]
