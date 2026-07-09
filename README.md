# Sports News Instagram Pipeline

Automated pipeline: ESPN breaking news -> branded graphic -> Instagram post.

## How it works

1. `espn_fetcher.py` polls ESPN's public JSON news endpoints (NFL, NBA, MLB)
   and tracks what it has already seen in `posted.json`.
2. `news_filter.py` decides what counts as breaking news. Keyword filter by
   default; add an `ANTHROPIC_API_KEY` secret to enable smarter LLM
   classification and punchier headlines.
3. `make_graphic.py` renders a 1080x1080 template graphic with Pillow.
4. Images are committed to the repo so they have a public raw URL, then
   `publish_pending.py` posts them through the Meta Graph API.
5. GitHub Actions runs the whole thing every 5 minutes for free.

## Setup

### 1. Repo

Create a new PUBLIC GitHub repo (public so raw image URLs work), push these
files, and enable Actions.

### 2. Test locally first

```
pip install requests pillow
python pipeline.py        # dry run, generates graphics, publishes nothing
```

Check `output/` to see what it would have posted. Tweak the filter keywords
and template colors until you like it.

### 3. Instagram / Meta setup (the manual part)

1. Convert your Instagram account to a Professional account (Creator or
   Business) in the Instagram app settings.
2. Create a Facebook Page (it can be empty) and link it to the Instagram
   account: Instagram settings -> Business tools -> Connect a Facebook Page.
3. Go to developers.facebook.com, create an app (type: Business).
4. In the app dashboard, add the "Instagram" product / Instagram Graph API.
5. Use the Graph API Explorer to generate a User token with these
   permissions: instagram_basic, instagram_content_publish, pages_show_list.
6. Exchange it for a long-lived token (about 60 days) and note your
   Instagram user ID. Meta's "Content Publishing" docs walk through both.
7. Long-lived tokens expire, so plan to refresh roughly monthly. This can
   be automated later with a refresh call in the workflow.

### 4. GitHub secrets

Repo -> Settings -> Secrets and variables -> Actions. Add:

- `IG_USER_ID`: your Instagram professional account ID
- `IG_ACCESS_TOKEN`: the long-lived token
- `IMAGE_BASE_URL`: `https://raw.githubusercontent.com/YOURNAME/YOURREPO/main/output`
- `ANTHROPIC_API_KEY`: optional, enables the LLM filter

### 5. Go live

Push, then trigger the workflow manually from the Actions tab to test.
The publish step skips itself until the Instagram secrets exist, so you
can run everything else safely first.

## Knobs worth tuning

- `MAX_POSTS_PER_RUN` in `pipeline.py` (Instagram caps API publishing at
  50 posts per 24 hours; you will not get close at 3 per run)
- `LEAGUES` dict in `espn_fetcher.py` to add or drop sports
- `BREAKING_KEYWORDS` / `SKIP_KEYWORDS` in `news_filter.py`
- Colors, fonts, and `PAGE_HANDLE` in `make_graphic.py`

## Known limits

- ESPN's endpoints are unofficial. They have been stable for years but can
  change without notice, so the fetcher fails gracefully per league.
- GitHub Actions scheduled runs are best-effort; expect roughly 5 to 15
  minutes of latency on a "*/5" cron. Fine for Instagram.
- Do not use ESPN's article images in your graphics. They are licensed
  photos. The template avoids photos entirely for this reason.
