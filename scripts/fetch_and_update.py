#!/usr/bin/env python3
"""Denní agent pro kosmologické novinky – čeština."""
import re
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
LOOKBACK_HOURS = 60
GEMINI_MODEL = "gemini-3.6-flash"

# Kratší query = méně 429 od arXiv
ARXIV_QUERY = (
    '(cat:astro-ph.CO OR cat:gr-qc OR cat:hep-th OR cat:hep-ph) '
    'AND ('
    '"dark matter" OR "dark energy" OR "black hole" OR "black holes" '
    'OR cosmology OR inflation OR "gravitational wave" OR "gravitational waves" '
    'OR "primordial black" OR "early universe" OR "modified gravity" '
    'OR "quantum gravity" OR "Hubble tension" OR "structure formation" '
    'OR quasar OR quasars OR supernova OR supernovae '
    'OR spacetime OR "space-time" '
    'OR "Lambda CDM" OR LCDM OR "ΛCDM" '
    'OR Higgs OR neutrino OR neutrinos OR "quantum field"'
    ')'
)
RSS_FEEDS = [
    "https://www.sciencedaily.com/rss/space_time/cosmology.xml",
    "https://www.skyandtelescope.org/astronomy-news/cosmology/feed/",
]

RSS_KEYWORDS = [
    "dark matter", "dark energy", "black hole", "black holes",
    "cosmology", "cosmological", "inflation", "gravitational wave",
    "primordial", "early universe", "quantum gravity", "modified gravity",
    "hubble", "cmb", "cosmic microwave", "neutron star", "singularity",
    "hawking", "event horizon", "big bang", "multiverse", "string theory",
    "universe", "vesmír",
    "quasar", "supernova", "spacetime", "space-time",
    "lambda cdm", "lcdm", "higgs", "neutrino", "quantum field",
]

ARXIV_RSS_FEEDS = [
    "https://rss.arxiv.org/rss/astro-ph.CO",
    "https://rss.arxiv.org/rss/gr-qc",
    "https://rss.arxiv.org/rss/hep-th",
    "https://rss.arxiv.org/rss/hep-ph",
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


def looks_czech(title_cs: str, summary_cs: str, original_title: str) -> bool:
    """Hrubá kontrola, že Gemini opravdu vrátil češtinu, ne originál."""
    title_cs = (title_cs or "").strip()
    summary_cs = (summary_cs or "").strip()
    if len(title_cs) < 8 or len(summary_cs) < 40:
        return False
    if title_cs.casefold() == (original_title or "").strip().casefold():
        return False
    blob = title_cs + " " + summary_cs
    if re.search(r"[áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]", blob):
        return True
    czech_words = (
        "že", "který", "která", "které", "jsou", "bylo", "vesmír", "černá",
        "hmota", "energie", "výzkum", "studie", "autoři", "zajímavé",
    )
    low = blob.casefold()
    return sum(1 for w in czech_words if w in low) >= 2


def summarize_czech(client, title: str, abstract: str, url: str) -> dict | None:
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
    last_err = None
    for attempt in range(1, 4):
        try:
            chat = client.chats.create(model=GEMINI_MODEL)
            response = chat.send_message(prompt)
            text = (response.text or "").strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            data = json.loads(text)
            title_cs = (data.get("title_cs") or "").strip()[:120]
            summary_cs = (data.get("summary_cs") or "").strip()
            if not looks_czech(title_cs, summary_cs, title):
                raise ValueError("Odpověď nevypadá jako čeština")
            return {"title_cs": title_cs, "summary_cs": summary_cs}
        except Exception as e:
            last_err = e
            print(f"Sumarizace pokus {attempt}/3 selhal: {e}")
            if attempt < 3:
                print("Čekám 7 s před dalším pokusem…")
                time.sleep(7)
    print(f"Překlad se nepodařil, položku vynechávám: {title[:70]}")
    return None


def fetch_arxiv(existing_ids: set) -> list:
    """Nejdřív API s retry při 429, při neúspěchu fallback na arXiv RSS."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    new_items = []

    # --- 1) Pokus přes oficiální API s backoffem ---
    client = arxiv.Client(
        page_size=5,
        delay_seconds=15.0,
        num_retries=1,  # retry řešíme sami
    )
    search = arxiv.Search(
        query=ARXIV_QUERY,
        max_results=12,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    delays = [5, 45, 90]  # sekundy mezi pokusy
    api_ok = False
    for attempt, wait in enumerate(delays, start=1):
        try:
            time.sleep(wait)
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
            api_ok = True
            print(f"arXiv API OK (pokus {attempt}), nalezeno kandidátů: {len(new_items)}")
            break
        except Exception as e:
            err = str(e)
            print(f"arXiv API pokus {attempt}/{len(delays)} selhal: {err}")
            if "429" not in err and attempt == len(delays):
                break
            if attempt < len(delays):
                print(f"Čekám před dalším pokusem…")
            continue

    if api_ok and new_items:
        return new_items

    # --- 2) Fallback: arXiv RSS (méně rate-limitované) ---
    print("Přepínám na arXiv RSS fallback…")
    keywords = [
        "dark matter", "dark energy", "black hole", "black holes",
        "cosmology", "inflation", "gravitational wave", "primordial",
        "early universe", "modified gravity", "quantum gravity",
        "hubble tension", "structure formation",
        "quasar", "supernova", "spacetime", "space-time",
        "lambda cdm", "lcdm", "higgs", "neutrino", "quantum field",
    ]

    for feed_url in ARXIV_RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:25]:
                # id ve tvaru http://arxiv.org/abs/2609.12345
                link = entry.get("link") or entry.get("id") or ""
                paper_id = link.rstrip("/").split("/")[-1]
                if not paper_id or paper_id in existing_ids:
                    continue

                title = entry.get("title", "").replace("\n", " ")
                summary = entry.get("summary", entry.get("description", ""))
                # RSS často obsahuje HTML – zjednodušeně ořízneme tagy
                summary = re.sub(r"<[^>]+>", " ", summary)
                summary = re.sub(r"\s+", " ", summary).strip()

                text = (title + " " + summary).lower()
                if not any(kw in text for kw in keywords):
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

                new_items.append({
                    "id": paper_id,
                    "source": "arXiv",
                    "original_title": title,
                    "abstract": summary[:1200],
                    "url": f"https://arxiv.org/abs/{paper_id}",
                    "published": (published or datetime.now(timezone.utc)).isoformat(),
                })
                if len(new_items) >= MAX_NEW_ITEMS:
                    break
        except Exception as e:
            print(f"arXiv RSS chyba {feed_url}: {e}")

        if len(new_items) >= MAX_NEW_ITEMS:
            break

    # deduplikace
    seen = set()
    unique = []
    for it in new_items:
        if it["id"] not in seen:
            seen.add(it["id"])
            unique.append(it)

    print(f"arXiv celkem kandidátů po fallbacku: {len(unique)}")
    return unique

def fetch_rss(existing_ids: set) -> list:
    new_items = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:15]:
                entry_id = entry.get("id") or entry.get("link")
                if not entry_id or entry_id in existing_ids:
                    continue

                title = entry.get("title", "")
                summary = entry.get("summary", "")
                text = (title + " " + summary).lower()

                if not any(kw in text for kw in RSS_KEYWORDS):
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

                new_items.append({
                    "id": entry_id,
                    "source": "RSS",
                    "original_title": title or "Bez názvu",
                    "abstract": summary[:800],
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

    candidates = fetch_arxiv(existing_ids)
    candidates += fetch_rss(existing_ids)

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
        if not summary:
            continue
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

    if not new_posts:
        print("Žádný příspěvek se nepodařilo přeložit. Historie beze změny.")
        return

    history = new_posts + history
    history = history[:500]
    save_history(history)
    print(f"Přidáno {len(new_posts)} nových příspěvků. Celkem v historii: {len(history)}")


if __name__ == "__main__":
    main()
