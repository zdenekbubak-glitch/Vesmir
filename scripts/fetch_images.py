#!/usr/bin/env python3
"""Denní galerie: NASA APOD + ESA Hubble/Webb. Snímky se ukládají do assets/gallery/."""

import io
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests
from dateutil import parser as date_parser
from PIL import Image

DATA_FILE = Path("data/images.json")
GALLERY_DIR = Path("assets/gallery")
MAX_ITEMS = 16
APOD_DAYS = 12
MAX_EDGE = 1200
JPEG_QUALITY = 82
GEMINI_MODEL = "gemini-3.6-flash"

ESA_FEEDS = [
    ("ESA Hubble", "https://esahubble.org/images/feed/rss/"),
    ("ESA Webb", "https://esawebb.org/images/feed/rss/"),
]

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Kosmonovinky/1.0 (https://kosmonovinky.cz; gallery mirror)",
    "Accept": "image/*,*/*",
})


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


CZECH_WORDS = (
    "že", "který", "která", "které", "jsou", "bylo", "vesmír", "černá",
    "hmota", "energie", "výzkum", "studie", "autoři", "zajímavé",
)


def looks_czech_image(title_cs: str, caption_cs: str, original_title: str) -> bool:
    title_cs = (title_cs or "").strip()
    caption_cs = (caption_cs or "").strip()
    if len(title_cs) < 3 or len(caption_cs) < 20:
        return False
    if title_cs.casefold() == (original_title or "").strip().casefold():
        return False
    blob = title_cs + " " + caption_cs
    if re.search(r"[áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]", blob):
        return True
    low = blob.casefold()
    return sum(1 for w in CZECH_WORDS if w in low) >= 2


def translate_cs(client, title: str, caption: str, retry_wait: int = 7) -> tuple[str, str] | None:
    prompt = f"""Přelož astronomický popisek do češtiny. Vrať POUZE JSON:
{{"title_cs":"...","caption_cs":"..."}}
Titulek max 80 znaků, popisek 1–3 věty.

Title: {title}
Caption: {caption[:800]}
"""
    last_err = None
    for attempt in range(1, 4):
        try:
            chat = client.chats.create(model=GEMINI_MODEL)
            text = (chat.send_message(prompt).text or "").strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            data = json.loads(text)
            title_cs = (data.get("title_cs") or "").strip()[:120]
            caption_cs = (data.get("caption_cs") or "").strip()[:500]
            if not looks_czech_image(title_cs, caption_cs, title):
                raise ValueError("Odpověď nevypadá jako čeština")
            return title_cs, caption_cs
        except Exception as e:
            last_err = e
            print(f"Překlad obrázku pokus {attempt}/3 selhal: {e}")
            if attempt < 3:
                print(f"Čekám {retry_wait} s před dalším pokusem…")
                time.sleep(retry_wait)
    print(f"Překlad se nepodařil, snímek vynechávám: {(title or '')[:70]}")
    return None


def local_path_for(item_id: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", item_id).strip("-")[:80]
    return GALLERY_DIR / f"{safe}.jpg"


def is_remote(url: str) -> bool:
    return (url or "").startswith("http://") or (url or "").startswith("https://")


def alt_urls(url: str) -> list:
    out = [url]
    if "apod.nasa.gov" in url:
        out.append(url.replace("https://apod.nasa.gov", "https://www.apod.nasa.gov"))
        out.append(url.replace("https://", "http://", 1))
    seen = []
    for u in out:
        if u not in seen:
            seen.append(u)
    return seen


def download_bytes(url: str) -> bytes | None:
    if not url:
        return None
    last_err = None
    for candidate in alt_urls(url):
        for verify in (True, False):
            try:
                r = SESSION.get(candidate, timeout=45, verify=verify)
                r.raise_for_status()
                if len(r.content) < 800:
                    last_err = "soubor je moc malý"
                    continue
                if not verify:
                    print(f"Staženo bez ověření certifikátu: {candidate[:80]}")
                return r.content
            except Exception as e:
                last_err = e
                continue
    print(f"Stažení selhalo ({url[:80]}): {last_err}")
    return None


def save_resized(item_id: str, raw: bytes) -> str | None:
    try:
        im = Image.open(io.BytesIO(raw))
        im = im.convert("RGB")
        im.thumbnail((MAX_EDGE, MAX_EDGE), Image.Resampling.LANCZOS)
        GALLERY_DIR.mkdir(parents=True, exist_ok=True)
        dest = local_path_for(item_id)
        im.save(dest, "JPEG", quality=JPEG_QUALITY, optimize=True)
        print(f"Uloženo {dest} ({dest.stat().st_size} B, {im.size[0]}x{im.size[1]})")
        return dest.as_posix()
    except Exception as e:
        print(f"Zpracování snímku selhalo ({item_id}): {e}")
        return None


def store_local(item: dict) -> bool:
    dest = local_path_for(item["id"])
    if dest.exists() and dest.stat().st_size > 800:
        rel = dest.as_posix()
        item["thumb"] = rel
        item["image"] = rel
        return True
    candidates = []
    for key in ("image", "thumb"):
        url = item.get(key)
        if is_remote(url) and url not in candidates:
            candidates.append(url)
    for url in candidates:
        raw = download_bytes(url)
        if not raw:
            continue
        rel = save_resized(item["id"], raw)
        if rel:
            item["thumb"] = rel
            item["image"] = rel
            return True
    return False


def fetch_apod() -> list:
    key = os.environ.get("NASA_API_KEY", "DEMO_KEY")
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=APOD_DAYS)
    url = "https://api.nasa.gov/planetary/apod"
    try:
        r = SESSION.get(
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


def prune_gallery(keep_ids: set):
    if not GALLERY_DIR.exists():
        return
    for path in GALLERY_DIR.glob("*"):
        if not path.is_file():
            continue
        item_id = path.stem
        if item_id not in keep_ids:
            try:
                path.unlink()
                print(f"Smazán starý soubor {path}")
            except OSError:
                pass


def main():
    print("Stahuji denní astronomické snímky…")
    history = load_history()
    existing = {item.get("id") for item in history}

    candidates = fetch_apod() + fetch_esa()
    new_raw = [c for c in candidates if c["id"] not in existing]

    api_key = os.environ.get("GEMINI_API_KEY")
    client = None
    if api_key:
        from google import genai
        client = genai.Client(api_key=api_key)
    else:
        print("Chybí GEMINI_API_KEY – nové snímky se bez překladu neuloží.")

    now = datetime.now(timezone.utc).isoformat()
    new_items = []
    for item in new_raw[:MAX_ITEMS]:
        translated = translate_cs(client, item["title"], item["caption"]) if client else None
        if not translated:
            continue
        item["title"], item["caption"] = translated
        if not store_local(item):
            print(f"Snímek se nepodařilo uložit, vynechávám: {item['id']}")
            continue
        item["inserted_at"] = now
        new_items.append(item)
        print(f"Obrázek: {item['title'][:60]}")
        time.sleep(0.8)

    localized = 0
    for item in history:
        if is_remote(item.get("image") or "") or is_remote(item.get("thumb") or ""):
            if store_local(item):
                localized += 1
    if localized:
        print(f"Do repozitáře doplněno starších snímků: {localized}")

    merged = new_items + history
    seen = set()
    unique = []
    for it in merged:
        if it["id"] in seen:
            continue
        seen.add(it["id"])
        unique.append(it)
    unique = unique[:80]
    prune_gallery({it["id"] for it in unique})
    save_history(unique)
    print(f"Přidáno {len(new_items)} snímků. Celkem v galerii: {len(unique)}")


if __name__ == "__main__":
    main()
