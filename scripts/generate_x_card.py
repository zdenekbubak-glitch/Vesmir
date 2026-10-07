#!/usr/bin/env python3
"""Vygeneruje denní X kartu z data/news.json. Schválený vzhled 1200x675."""
import json
import random
import re
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

NEWS_FILE = Path("data/news.json")
OUT_PATH = Path("assets/cards/daily.jpg")
PREVIEW_PATH = Path("assets/cards/daily-preview.jpg")
LOGO_CANDIDATES = [
    Path("assets/logo-icon-square.png"),
    Path("assets/logo-icon-square.jpg"),
    Path("assets/logo-icon.jpg"),
]
SITE_URL = "kosmonovinky.cz"

W, H = 1200, 675
BG = (11, 15, 25)
TEXT = (232, 238, 247)
MUTED = (154, 168, 199)
ACCENT = (110, 168, 254)
BORDER = (30, 41, 59)
LOGO_SIZE = 88

BODY_SIZE = 26
BODY_LEADING = 38
BODY_MAX_WIDTH = W - 120
FOOTER_Y = H - 92
BODY_BOTTOM = FOOTER_Y - 28


def load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/SlidesCarnival/google/Noto Sans/static/NotoSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/SlidesCarnival/google/Noto Sans/static/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap(text, font, max_width, draw):
    words = (text or "").split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def pick_item(items):
    if not items:
        return None
    today = datetime.now().date().isoformat()
    today_items = [i for i in items if (i.get("inserted_at") or "")[:10] == today]
    pool = today_items or items
    for item in pool:
        if item.get("lang") != "en" and not item.get("needs_translation"):
            return item
    return pool[0]


def _strip_tex(text: str) -> str:
    text = re.sub(r"\$[^$]*\$", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def body_text(summary: str) -> str:
    """Celé shrnutí bez závěrečné věty „Proč je to zajímavé“."""
    text = _strip_tex((summary or "").strip())
    if "Proč je to zajímavé:" in text:
        text = text.split("Proč je to zajímavé:")[0].strip()
    return text


def fit_body(text, font, draw, max_lines):
    """Vyplní daný počet řádků. Když se text nevejde celý, končí třemi tečkami."""
    lines = wrap(text, font, BODY_MAX_WIDTH, draw)
    if len(lines) <= max_lines:
        return lines

    lines = lines[:max_lines]
    last = lines[-1].rstrip(" .,;:")
    ellipsis = "..."
    while last and draw.textlength(last + ellipsis, font=font) > BODY_MAX_WIDTH:
        last = last.rsplit(" ", 1)[0]
    lines[-1] = (last + ellipsis) if last else ellipsis
    return lines


def paste_rounded_logo(img, logo_path, xy, size):
    logo = Image.open(logo_path).convert("RGB").resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=12, fill=255)
    base = img.convert("RGBA")
    layer = Image.new("RGBA", (size, size))
    layer.paste(logo, (0, 0))
    layer.putalpha(mask)
    base.alpha_composite(layer, xy)
    return base.convert("RGB")


def generate(item=None, out_path=OUT_PATH):
    if item is None:
        if not NEWS_FILE.exists():
            print("Chybí data/news.json — karta se nevygenerovala.")
            return
        items = json.loads(NEWS_FILE.read_text(encoding="utf-8"))
        item = pick_item(items)
        if not item:
            print("Žádné novinky pro kartu.")
            return

    img = Image.new("RGB", (W, H), BG)
    rnd = random.Random(7)
    px = img.load()
    for _ in range(140):
        x = rnd.randint(0, W - 1)
        y = rnd.randint(0, H - 1)
        c = rnd.randint(70, 160)
        px[x, y] = (c, c + 10, min(255, c + 40))

    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((24, 24, W - 24, H - 24), radius=26, outline=BORDER, width=2)

    logo_file = next((p for p in LOGO_CANDIDATES if p.exists()), None)
    if logo_file:
        img = paste_rounded_logo(img, logo_file, (52, 46), LOGO_SIZE)
        draw = ImageDraw.Draw(img)

    font_brand = load_font(30)
    font_title = load_font(36, bold=True)
    font_body = load_font(BODY_SIZE)
    font_footer = load_font(24)

    draw.text((160, 70), "Kosmologické novinky", font=font_brand, fill=MUTED)

    title = item.get("title") or "Denní kosmologická novinka"
    title_lines = wrap(title, font_title, W - 120, draw)[:3]
    y = 168
    for line in title_lines:
        draw.text((56, y), line, font=font_title, fill=TEXT)
        y += 48

    body_y = y + 18
    max_lines = max(1, (BODY_BOTTOM - body_y) // BODY_LEADING)
    hook = body_text(item.get("summary", ""))
    hook_lines = fit_body(hook, font_body, draw, max_lines)
    for line in hook_lines:
        draw.text((56, body_y), line, font=font_body, fill=MUTED)
        body_y += BODY_LEADING

    draw.text((56, FOOTER_Y), "Celé shrnutí  ->  " + SITE_URL, font=font_footer, fill=ACCENT)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=92)
    if out_path == OUT_PATH:
        img.save(PREVIEW_PATH, quality=92)
    print(f"Karta uložena: {out_path}")
    print(f"Titulek: {title}")
    print(f"Řádků textu: {len(hook_lines)} / {max_lines}")
    return img


if __name__ == "__main__":
    generate()
