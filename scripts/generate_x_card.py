#!/usr/bin/env python3
"""Vygeneruje denní X kartu z data/news.json. Schválený vzhled 1200x675."""
import json
import random
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

NEWS_FILE = Path("data/news.json")
OUT_PATH = Path("assets/cards/daily.jpg")
LOGO_CANDIDATES = [
    Path("assets/logo-icon-square.png"),
    Path("assets/logo-icon-square.jpg"),
    Path("assets/logo-icon.jpg"),
]
SITE_URL = "zdenekbubak-glitch.github.io/Vesmir"

W, H = 1200, 675
BG = (11, 15, 25)
TEXT = (232, 238, 247)
MUTED = (154, 168, 199)
ACCENT = (110, 168, 254)
LOGO_SIZE = 96


def load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
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
    for item in items:
        inserted = (item.get("inserted_at") or "")[:10]
        if inserted == today:
            return item
    return items[0]


def hook_from_summary(summary, max_len=220):
    text = (summary or "").strip()
    if "Proč je to zajímavé:" in text:
        parts = text.split("Proč je to zajímavé:")
        text = parts[0].strip()
    first = text.split(". ")
    if len(first) >= 2:
        text = first[0].strip() + ". " + first[1].strip()
        if not text.endswith("."):
            text += "."
    if len(text) > max_len:
        text = text[: max_len - 1].rsplit(" ", 1)[0] + "…"
    return text


def generate():
    items = json.loads(NEWS_FILE.read_text(encoding="utf-8"))
    item = pick_item(items)
    if not item:
        print("Žádné novinky pro kartu.")
        return

    img = Image.new("RGB", (W, H), BG)
    rnd = random.Random(7)
    px = img.load()
    for _ in range(120):
        x = rnd.randint(0, W - 1)
        y = rnd.randint(0, H - 1)
        c = rnd.randint(70, 160)
        px[x, y] = (c, c + 10, min(255, c + 40))

    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((24, 24, W - 24, H - 24), radius=26, outline=(30, 41, 59), width=2)

    logo_file = next((p for p in LOGO_CANDIDATES if p.exists()), None)
    if logo_file:
        logo = Image.open(logo_file).convert("RGB").resize((LOGO_SIZE, LOGO_SIZE))
        img.paste(logo, (52, 44))

    font_brand = load_font(32)
    font_title = load_font(38, bold=True)
    font_body = load_font(24)
    font_footer = load_font(20)

    draw.text((168, 72), "Kosmologické novinky", font=font_brand, fill=MUTED)

    title = item.get("title") or "Denní kosmologická novinka"
    title_lines = wrap(title, font_title, W - 120, draw)[:3]
    y = 170
    for line in title_lines:
        draw.text((56, y), line, font=font_title, fill=TEXT)
        y += 50

    hook = hook_from_summary(item.get("summary", ""))
    hook_lines = wrap(hook, font_body, W - 120, draw)[:4]
    y = 300
    for line in hook_lines:
        draw.text((56, y), line, font=font_body, fill=MUTED)
        y += 36

    draw.text((56, H - 92), "Celé shrnutí  →  " + SITE_URL, font=font_footer, fill=ACCENT)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT_PATH, quality=92)
    print(f"Karta uložena: {OUT_PATH}")
    print(f"Titulek: {title}")


if __name__ == "__main__":
    generate()
