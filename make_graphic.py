"""Render a 1080x1080 breaking-news graphic with Pillow.

Template-based, so every post looks consistent and renders in under a
second. Swap the colors and PAGE_HANDLE to match your branding.
"""

import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1080
BG = (12, 14, 20)          # near-black
ACCENT = (230, 36, 41)     # red bar / BREAKING tag
TEXT = (245, 245, 245)
MUTED = (150, 155, 165)
PAGE_HANDLE = "@yourpagehandle"   # change me

LEAGUE_COLORS = {
    "nfl": (1, 51, 105),
    "nba": (200, 16, 46),
    "mlb": (0, 45, 114),
}

# Candidate font paths across platforms (Linux CI runner, Windows, macOS).
# The first one that exists on disk wins; falls back to Pillow's bundled
# default font if none are found so the pipeline never hard-crashes.
BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
REG_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def _first_existing(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None


FONT_BOLD = _first_existing(BOLD_CANDIDATES)
FONT_REG = _first_existing(REG_CANDIDATES)


def _load_font(path, size):
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def wrap_text(draw, text, font, max_width):
    words, lines, line = text.split(), [], ""
    for w in words:
        test = f"{line} {w}".strip()
        if draw.textlength(test, font=font) <= max_width:
            line = test
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def fit_headline(draw, text, max_width, max_height, start_size=92, min_size=48):
    """Shrink font size until the wrapped headline fits the box."""
    size = start_size
    while size >= min_size:
        font = _load_font(FONT_BOLD, size)
        lines = wrap_text(draw, text, font, max_width)
        line_h = int(size * 1.18)
        if len(lines) * line_h <= max_height:
            return font, lines, line_h
        size -= 4
    font = _load_font(FONT_BOLD, min_size)
    lines = wrap_text(draw, text, font, max_width)
    return font, lines[:6], int(min_size * 1.18)


def make_graphic(headline, league, source_note="via ESPN", out_path="output/post.png"):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    margin = 80

    # Left accent bar
    d.rectangle([0, 0, 18, H], fill=ACCENT)

    # BREAKING tag
    tag_font = _load_font(FONT_BOLD, 44)
    tag_text = "BREAKING"
    tw = d.textlength(tag_text, font=tag_font)
    d.rectangle([margin, 100, margin + tw + 48, 176], fill=ACCENT)
    d.text((margin + 24, 112), tag_text, font=tag_font, fill=TEXT)

    # League chip
    chip_font = _load_font(FONT_BOLD, 40)
    chip_text = league.upper()
    cw = d.textlength(chip_text, font=chip_font)
    cx = margin + tw + 72
    d.rectangle([cx, 100, cx + cw + 44, 176], fill=LEAGUE_COLORS.get(league, MUTED))
    d.text((cx + 22, 116), chip_text, font=chip_font, fill=TEXT)

    # Headline, auto-sized to fit
    font, lines, line_h = fit_headline(d, headline, W - 2 * margin, 560)
    y = 300
    for line in lines:
        d.text((margin, y), line, font=font, fill=TEXT)
        y += line_h

    # Footer: source credit and page handle
    foot_font = _load_font(FONT_REG, 36)
    d.line([margin, H - 170, W - margin, H - 170], fill=(50, 54, 62), width=3)
    d.text((margin, H - 130), source_note, font=foot_font, fill=MUTED)
    hw = d.textlength(PAGE_HANDLE, font=foot_font)
    d.text((W - margin - hw, H - 130), PAGE_HANDLE, font=foot_font, fill=MUTED)

    img.save(out_path)
    return out_path


if __name__ == "__main__":
    make_graphic(
        "CHIEFS ACQUIRE ALL-PRO WR IN BLOCKBUSTER TRADE WITH RAIDERS",
        "nfl",
    )
    print("saved output/post.png")
