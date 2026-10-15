#!/usr/bin/env python3
"""Týdenní výběr na LinkedIn přes Buffer."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

PRAGUE = ZoneInfo("Europe/Prague")
LINKEDIN_CHANNEL = "6acba1b1778b240e2fd7e2c9"
MAX_CHARS = 2900


def week_window(now: datetime):
    """Okno od úterý 0:00 do pondělí 10:00 Praha."""
    now = now.astimezone(PRAGUE)
    # Najdi poslední pondělí 10:00
    days_since_monday = now.weekday()  # 0 = pondělí
    monday = now.replace(hour=10, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
    if now < monday:
        monday -= timedelta(days=7)
    tuesday = monday - timedelta(days=6)
    tuesday = tuesday.replace(hour=0, minute=0, second=0, microsecond=0)
    return tuesday, monday


def main():
    api_key = os.environ.get("BUFFER_API_KEY")
    if not api_key:
        print("Chybí BUFFER_API_KEY")
        return

    news_path = Path("data/news.json")
    if not news_path.exists():
        print("news.json nenalezen")
        return

    items = json.loads(news_path.read_text())
    now = datetime.now(PRAGUE)
    start, end = week_window(now)
    print(f"Okno: {start.date()} – {end.date()}")

    candidates = []
    for item in items:
        inserted = item.get("inserted_at")
        if not inserted:
            continue
        try:
            ts = datetime.fromisoformat(inserted.replace("Z", "+00:00")).astimezone(PRAGUE)
        except Exception:
            continue
        if start <= ts <= end and item.get("title") and item.get("summary"):
            if item.get("lang") == "cs" or not item.get("needs_translation"):
                candidates.append(item)

    if not candidates:
        print("Žádné příspěvky v okně.")
        return

    # Vezmi nejnovějších max 5
    candidates = candidates[:5]
    months = ["ledna", "února", "března", "dubna", "května", "června",
              "července", "srpna", "září", "října", "listopadu", "prosince"]
    header = (f"Týdenní výběr Kosmologických novinek: "
              f"{start.day}. {months[start.month-1]} – {end.day}. {months[end.month-1]} {end.year}")

    lines = [header, ""]
    for i, item in enumerate(candidates, 1):
        title = item.get("title", "").strip()
        summary = item.get("summary", "").strip()
        if "Proč je to zajímavé:" in summary:
            summary = summary.split("Proč je to zajímavé:")[0].strip()
        if len(summary) > 220:
            summary = summary[:217].rsplit(" ", 1)[0] + "…"
        lines.append(f"{i}. {title}")
        lines.append(summary)
        lines.append("")

    lines.append("Další příspěvky: https://kosmonovinky.cz")
    text = "\n".join(lines).strip()
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS - 3] + "…"
    print(f"Délka textu: {len(text)}")

    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess { post { id status } }
        ... on MutationError { message }
      }
    }
    """
    variables = {
        "input": {
            "channelId": LINKEDIN_CHANNEL,
            "schedulingType": "automatic",
            "mode": "shareNow",
            "text": text,
        }
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    r = requests.post("https://api.buffer.com", json={"query": mutation, "variables": variables}, headers=headers, timeout=30)
    print(f"Buffer HTTP {r.status_code}")
    print(r.text[:800])
    try:
        data = r.json()
        if data.get("errors"):
            print(f"GraphQL errors: {data['errors']}")
        result = data.get("data", {}).get("createPost", {})
        if "message" in result:
            print(f"Buffer chyba: {result['message']}")
        else:
            print(f"Post odeslán: {result.get('post', {}).get('id')}")
    except Exception as e:
        print(f"Chyba parsování: {e}")


if __name__ == "__main__":
    main()
