#!/usr/bin/env python3
"""Jednorázově přeloží anglické položky v data/images.json. Spouštět z kořene repo.

    GEMINI_API_KEY=... python scripts/repair_untranslated_images.py

Využívá retry logiku (3 pokusy po 7 s) a validaci češtiny z fetch_images.py.
Položky, které se nepodaří přeložit, zůstanou beze změny.
"""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from fetch_images import (  # noqa: E402
    DATA_FILE,
    looks_czech_image,
    translate_cs,
)


def needs_repair(item: dict) -> bool:
    title = item.get("title") or ""
    caption = item.get("caption") or ""
    if not title.strip() and not caption.strip():
        return False
    # prázdný originál -> kontrola shody titulku s originálem se přeskočí
    return not looks_czech_image(title, caption, "")


def main():
    data_file = DATA_FILE if DATA_FILE.exists() else Path("data/images.json")
    if not data_file.exists():
        raise SystemExit(f"Nenalezen {data_file}")

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

    from google import genai
    client = genai.Client(api_key=api_key)

    fixed = 0
    skipped = 0
    for item in targets:
        title_orig = item.get("title") or ""
        print(f"Opravuji {item.get('id')}: {title_orig[:70]}")
        result = translate_cs(client, title_orig, item.get("caption") or "")
        if not result:
            skipped += 1
            continue
        item["title"], item["caption"] = result
        fixed += 1
        time.sleep(1.5)

    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Hotovo. Přeloženo: {fixed}, přeskočeno: {skipped}. Uloženo do {data_file}")


if __name__ == "__main__":
    main()
