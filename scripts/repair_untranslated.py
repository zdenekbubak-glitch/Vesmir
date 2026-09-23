#!/usr/bin/env python3
"""Jednorázově přeloží anglické položky v data/news.json. Spouštět z kořene repo.

    GEMINI_API_KEY=... python scripts/repair_untranslated.py
"""
import json
import os
import re
import sys
import time
from pathlib import Path

import arxiv
from google import genai

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from fetch_and_update import (  # noqa: E402
    DATA_FILE,
    DailyQuotaExhausted,
    looks_czech,
    summarize_czech,
)


def needs_repair(item: dict) -> bool:
    if item.get("lang") == "en" or item.get("needs_translation"):
        return True
    title = item.get("title") or ""
    summary = item.get("summary") or ""
    original = item.get("original_title") or ""
    return not looks_czech(title, summary, original)


def fetch_abstract(item: dict) -> str:
    summary = (item.get("summary") or "").strip()
    source = item.get("source") or ""
    item_id = item.get("id") or ""
    if source == "arXiv" or re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", item_id):
        paper_id = item_id
        try:
            client = arxiv.Client(page_size=1, delay_seconds=3.0, num_retries=2)
            search = arxiv.Search(id_list=[paper_id])
            paper = next(client.results(search), None)
            if paper and paper.summary:
                return paper.summary.replace("\n", " ").strip()
        except Exception as e:
            print(f"  arXiv abstrakt se nepovedl ({paper_id}): {e}")
    if len(summary) >= 80:
        return summary
    return title_or_empty(item)


def title_or_empty(item: dict) -> str:
    return item.get("original_title") or item.get("title") or ""


def main():
    if DATA_FILE.exists():
        data_file = DATA_FILE
    else:
        alt = Path("data/news.json")
        if alt.exists():
            data_file = alt
        else:
            raise SystemExit(f"Nenalezen {DATA_FILE}")

    items = json.loads(data_file.read_text(encoding="utf-8"))
    targets = [it for it in items if needs_repair(it)]
    print(f"Položek celkem: {len(items)}")
    print(f"K opravě: {len(targets)}")
    if not targets:
        print("Nic k překladu.")
        return

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("Chybí GEMINI_API_KEY")

    client = genai.Client(api_key=api_key)
    fixed = 0
    skipped = 0

    for item in targets:
        orig = title_or_empty(item)
        print(f"Opravuji {item.get('id')}: {orig[:70]}")
        abstract = fetch_abstract(item)
        try:
            result = summarize_czech(client, orig, abstract, item.get("url") or "")
        except DailyQuotaExhausted:
            print("Denní kvóta Gemini je vyčerpaná – končím, už přeložené uložím.")
            skipped += 1
            break
        if not result:
            skipped += 1
            continue
        item["title"] = result["title_cs"]
        item["summary"] = result["summary_cs"]
        item["lang"] = "cs"
        item["needs_translation"] = False
        fixed += 1
        time.sleep(1.5)

    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Hotovo. Přeloženo: {fixed}, přeskočeno: {skipped}. Uloženo do {data_file}")


if __name__ == "__main__":
    main()
