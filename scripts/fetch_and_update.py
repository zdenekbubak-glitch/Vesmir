#!/usr/bin/env python3
"""Denní agent pro kosmologické novinky – čeština."""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import arxiv
import feedparser
from google import genai
from dateutil import parser as date_parser

# Konfigurace
DATA_FILE = Path("data/news.json")
MAX_NEW_ITEMS = 8
LOOKBACK_HOURS = 36
GEMINI_MODEL = "gemini-3.6-flash"

ARXIV_QUERY = (
    '(cat:astro-ph.CO OR cat:astro-ph.HE OR cat:astro-ph.GA OR cat:gr-qc OR cat:hep-th OR cat:hep-ph) '
    'AND (ti:"dark matter" OR ti:"dark energy" OR ti:"black hole" OR ti:"black holes" '
    'OR ti:"neutron star" OR ti:"quantum field" OR ti:cosmology '
    'OR abs:"dark matter" OR abs:"dark energy" OR abs:"black hole" OR abs:cosmology)'
)

RSS_FEEDS = [
    "https://www.sciencedaily.com/rss/space_time/cosmology.xml",
    "https://www.skyandtelescope.org/astronomy-news/cosmology/feed/",
]

def load_history() -> list:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(items: list):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def get_existing_ids(history: list) -> set:
    return {item.get("id") for item in history if item.get("id")}

def summarize_czech(client, title: str, abstract: str, url: str) -> dict:
    prompt = f"""Jsi odborný popularizátor kosmologie. Napiš krátký článek v češtině pro laickou i odbornou veřejnost.

Titulek originálu: {title}

Abstrakt:
{abstract}

Požadavky:
1. Vytvoř poutavý český titulek (max 80 znaků).
2. Napiš shrnutí 80–140 slov – srozumitelně, přesně, bez zbytečného žargonu.
3. Na konci přidej jednu větu „Proč je to zajímavé“.
4. Vrať POUZE validní JSON v tomto formátu (žádný markdown):
{{
  "title_cs": "...",
  "summary_cs": "..."
}}
"""
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        return {
            "title_cs": data.get("title_cs", title)[:120],
            "summary_cs": data.get("summary_cs", abstract[:300]),
        }
    except Exception as e:
        print(f"Chyba při sumarizaci: {e}")
        return {
            "title_cs": title[:100],
            "summary_cs": abstract[:250] + "…",
        }

def fetch_arxiv(existing_ids: set) -> list:
    client = arxiv.Client(
        page_size=15,
        delay_seconds=6.0,
        num_retries=2
    )
    search = arxiv.Search(
        query=ARXIV_QUERY,
        max_results=20,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    new_items = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

    try:
        for paper in client.results(search):
            paper_id = paper.entry_id.split("/abs/")[-1]
            if paper_id in existing_ids:
                continue
            published = paper.published
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            if published < cutoff:
                continue

            new_items.append({
                "id": paper_id,
                "source": "arXiv",
                "original_title": paper.title,
                "abstract": paper.summary.replace("\n", " "),
                "url": paper.entry_id,
                "published": published.isoformat(),
            })
            if len(new_items) >= MAX_NEW_ITEMS:
                break
    except Exception as e:
        print(f"Varování: arXiv se nepodařilo stáhnout ({e}). Pokračuji jen s RSS.")

    return new_items

def fetch_rss(existing_ids: set) -> list:
    new_items = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:12]:
                entry_id = entry.get("id") or entry.get("link")
                if not entry_id or entry_id in existing_ids:
                    continue
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                elif entry.get("published"):
                    try:
                        published = date_parser.parse(entry.published).astimezone(timezone.utc)
                    except Exception:
                        published = None

                if published and published < cutoff:
                    continue

                abstract = entry.get("summary", "")[:800]
                new_items.append({
                    "id": entry_id,
                    "source": "RSS",
                    "original_title": entry.get("title", "Bez názvu"),
                    "abstract": abstract,
                    "url": entry.get("link", ""),
                    "published": published.isoformat() if published else datetime.now(timezone.utc).isoformat(),
                })
        except Exception as e:
            print(f"RSS chyba {feed_url}: {e}")
    return new_items

def main():
    print("Spouštím denní aktualizaci kosmologických novinek…")
    history = load_history()
    existing_ids = get_existing_ids(history)

    # 1. Stáhnout nové položky
    candidates = fetch_arxiv(existing_ids)
    candidates += fetch_rss(existing_ids)

    # Deduplikace a limit
    seen = set()
    unique = []
    for c in candidates:
        if c["id"] not in seen:
            seen.add(c["id"])
            unique.append(c)
    unique = unique[:MAX_NEW_ITEMS]

    if not unique:
        print("Žádné nové relevantní položky.")
        return

    # 2. Sumarizace přes Gemini
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Chybí GEMINI_API_KEY")

    client = genai.Client(api_key=api_key)
    now = datetime.now(timezone.utc).isoformat()

    new_posts = []
    for item in unique:
        print(f"Sumarizuji: {item['original_title'][:60]}…")
        summary = summarize_czech(
            client,
            item["original_title"],
            item["abstract"],
            item["url"],
        )
        post = {
            "id": item["id"],
            "title": summary["title_cs"],
            "summary": summary["summary_cs"],
            "url": item["url"],
            "source": item["source"],
            "original_title": item["original_title"],
            "published": item["published"],
            "inserted_at": now,
        }
        new_posts.append(post)
        time.sleep(1.5)

    # 3. Uložit (nové nahoře)
    history = new_posts + history
    history = history[:500]
    save_history(history)
    print(f"Přidáno {len(new_posts)} nových příspěvků. Celkem v historii: {len(history)}")

if __name__ == "__main__":
    main()
