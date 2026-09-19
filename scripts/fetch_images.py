#!/usr/bin/env python3
"""Denní galerie: NASA APOD + ESA Hubble/Webb."""

import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests
from dateutil import parser as date_parser

DATA_FILE = Path("data/images.json")
MAX_ITEMS = 16
APOD_DAYS = 12
GEMINI_MODEL = "gemini-3.6-flash"

ESA_FEEDS = [
    ("ESA Hubble", "https://esahubble.org/images/feed/rss/"),
    ("ESA Webb", "https://esawebb.org/images/feed/rss/"),
]


def slug(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", (text or "").strip()).strip("-").lower()
    return text[:48] or "img"


def load_history() -> list:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(items: list):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def translate_cs(title: str, caption: str) -> tuple[str, str]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return title, caption[:400]
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        chat = client.chats.create(model=GEMINI_MODEL)
        prompt = f"""Přelož astronomický popisek do češtiny. Vrať POUZE JSON:
{{"title_cs":"...","caption_cs":"..."}}
Titulek max 80 znaků, popisek 1–3 věty.

Title: {title}
Caption: {caption[:800]}
"""
        text = chat.send_message(prompt).text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        return (
            data.get("title_cs", title)[:120],
            data.get("caption_cs", caption)[:500],
        )
    except Exception as e:
        print(f"Překlad obrázku selhal: {e}")
        return title, caption[:400]


def fetch_apod() -> list:
    key = os.environ.get("NASA_API_KEY", "DEMO_KEY")
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=APOD_DAYS)
    url = "https://api.nasa.gov/planetary/apod"
    try:
        r = requests.get(
            url,
            params={
                "api_key": key,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "thumbs": True,
            },
            timeout=30,
        )
        r.raise_for_status()
        rows = r.json()
        if isinstance(rows, dict):
            rows = [rows]
    except Exception as e:
        print(f"APOD chyba: {e}")
        return []

    items = []
    for row in reversed(rows):
        media = row.get("media_type")
        image = row.get("url")
        if media == "video":
            image = row.get("thumbnail_url")
        if not image:
            continue
        date = row.get("date") or end.isoformat()
        items.append({
            "id": f"apod-{date}",
            "title": row.get("title") or "Astronomy Picture of the Day",
            "caption": row.get("explanation") or "",
            "thumb": image,
            "image": row.get("hdurl") or image,
            "source": "NASA APOD",
            "url": f"https://apod.nasa.gov/apod/ap{date.replace('-', '')[2:]}.html",
            "published": date,
            "credit": row.get("copyright") or "NASA / APOD",
        })
    return items


def fetch_esa() -> list:
    items = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=21)
    for source, feed_url in ESA_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"ESA RSS chyba {feed_url}: {e}")
            continue
        for entry in feed.entries[:8]:
            title = (entry.get("title") or "").replace("\n", " ").strip()
            link = entry.get("link") or ""
            summary = entry.get("summary") or entry.get("description") or ""
            summary = re.sub(r"<[^>]+>", " ", summary)
            summary = re.sub(r"\s+", " ", summary).strip()

            image = None
            if entry.get("media_content"):
                image = entry.media_content[0].get("url")
            if not image and entry.get("media_thumbnail"):
                image = entry.media_thumbnail[0].get("url")
            if not image:
                m = re.search(r'<img[^>]+src=["\']([^"\']+)', entry.get("summary", ""))
                if m:
                    image = m.group(1)
            if not image:
                continue

            published = None
            if getattr(entry, "published_parsed", None):
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif entry.get("published"):
                try:
                    published = date_parser.parse(entry.published).astimezone(timezone.utc)
                except Exception:
                    published = None
            if published and published < cutoff:
                continue

            date = (published or datetime.now(timezone.utc)).date().isoformat()
            eid = slug(link.split("/")[-2] if link else title)
            items.append({
                "id": f"esa-{eid}",
                "title": title or source,
                "caption": summary[:600],
                "thumb": image,
                "image": image,
                "source": source,
                "url": link,
                "published": date,
                "credit": source,
            })
    return items


def main():
    print("Stahuji denní astronomické snímky…")
    history = load_history()
    existing = {item.get("id") for item in history}

    candidates = fetch_apod() + fetch_esa()
    new_raw = [c for c in candidates if c["id"] not in existing]

    now = datetime.now(timezone.utc).isoformat()
    new_items = []
    for item in new_raw[:MAX_ITEMS]:
        title_cs, caption_cs = translate_cs(item["title"], item["caption"])
        item["title"] = title_cs
        item["caption"] = caption_cs
        item["inserted_at"] = now
        new_items.append(item)
        print(f"Obrázek: {item['title'][:60]}")
        time.sleep(0.8)

    merged = new_items + history
    seen = set()
    unique = []
    for it in merged:
        if it["id"] in seen:
            continue
        seen.add(it["id"])
        unique.append(it)
    unique = unique[:80]
    save_history(unique)
    print(f"Přidáno {len(new_items)} snímků. Celkem v galerii: {len(unique)}")


if __name__ == "__main__":
    main()