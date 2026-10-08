#!/usr/bin/env python3
"""Pondělní výběr 5 článků a koncept newsletteru v Buttondownu.

Okno: úterý 0:00 až pondělí 10:00, čas Praha.
Secrets: BUTTONDOWN_API_KEY, GEMINI_API_KEY
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from google import genai

NEWS = Path("data/news.json")
PRAGUE = ZoneInfo("Europe/Prague")
GEMINI_MODEL = "gemini-3.6-flash"
BUTTONDOWN_URL = "https://api.buttondown.com/v1/emails"
PICK = 5
# draft = jen koncept. Až bude výběr sedět, změň na "about".
EMAIL_STATUS = "draft"


def week_window(now: datetime) -> tuple[datetime, datetime]:
    monday = now.replace(hour=10, minute=0, second=0, microsecond=0)
    if now.weekday() != 0 or now < monday:
        monday = (now - timedelta(days=(now.weekday() - 0) % 7)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        if now < monday:
            monday -= timedelta(days=7)
    start = (monday - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, monday


def parse_inserted(value: str) -> datetime | None:
    if not value:
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=PRAGUE)
    return stamp.astimezone(PRAGUE)


def czech_date(day: datetime) -> str:
    months = (
        "ledna", "února", "března", "dubna", "května", "června",
        "července", "srpna", "září", "října", "listopadu", "prosince",
    )
    return f"{day.day}. {months[day.month - 1]}"


def candidates(start: datetime, end: datetime) -> list[dict]:
    items = json.loads(NEWS.read_text(encoding="utf-8"))
    picked = []
    for item in items:
        stamp = parse_inserted(item.get("inserted_at") or "")
        if not stamp or stamp < start or stamp > end:
            continue
        if not (item.get("title") and item.get("summary")):
            continue
        picked.append(item)
    czech = [i for i in picked if i.get("lang") == "cs"]
    return czech or picked


def pick_ids(client, items: list[dict]) -> list[str]:
    if len(items) <= PICK:
        return [i["id"] for i in items]
    lines = []
    for item in items:
        summary = " ".join((item.get("summary") or "").split())[:280]
        lines.append(f"ID: {item['id']}\nTITULEK: {item.get('title')}\nSOUHRN: {summary}")
    prompt = (
        "Jsi editor českého newsletteru Kosmologické novinky. "
        f"Vyber {PICK} různých příspěvků, které jsou pro laického čtenáře "
        "nejzajímavější. Preferuj kosmologii, temnou hmotu a energii, černé díry, "
        "gravitační vlny a raný vesmír. Nevybírej čistě matematické práce bez "
        "jasného výsledku, pokud je z čeho vybírat.\n"
        "Vrať pouze JSON pole id v pořadí od nejzajímavějšího, žádný markdown:\n"
        '{"ids": ["...", "..."]}\n\n'
        + "\n\n".join(lines)
    )
    chat = client.chats.create(model=GEMINI_MODEL)
    text = (chat.send_message(prompt).text or "").strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    data = json.loads(text)
    wanted = [str(i) for i in data.get("ids") or []]
    known = {i["id"]: i for i in items}
    chosen = [i for i in wanted if i in known]
    for item in items:
        if len(chosen) >= PICK:
            break
        if item["id"] not in chosen:
            chosen.append(item["id"])
    return chosen[:PICK]


def build_email(items: list[dict], start: datetime, end: datetime) -> tuple[str, str]:
    subject = (
        f"Kosmologické novinky: {czech_date(start)} – {czech_date(end)} {end.year}"
    )
    parts = [
        "Týdenní výběr pěti příspěvků, které se za uplynulý týden objevily na kosmonovinky.cz.",
        "",
    ]
    for index, item in enumerate(items, start=1):
        url = item.get("url") or "https://kosmonovinky.cz"
        parts.extend([
            f"## {index}. {item.get('title')}",
            "",
            item.get("summary") or "",
            "",
            f"[Celý zdroj]({url})",
            "",
        ])
    parts.append("Další příspěvky: [kosmonovinky.cz](https://kosmonovinky.cz)")
    return subject, "\n".join(parts)


def main():
    button_key = os.environ.get("BUTTONDOWN_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not button_key:
        raise SystemExit("Chybí BUTTONDOWN_API_KEY")
    now = datetime.now(PRAGUE)
    start, end = week_window(now)
    pool = candidates(start, end)
    print(f"Okno {start.isoformat()} – {end.isoformat()}, kandidátů {len(pool)}")
    if not pool:
        print("Za týden není co poslat.")
        return
    if gemini_key and len(pool) > PICK:
        try:
            client = genai.Client(api_key=gemini_key)
            ids = pick_ids(client, pool)
        except Exception as exc:
            print(f"Výběr Gemini selhal, beru nejnovější: {exc}")
            ids = [i["id"] for i in pool[:PICK]]
    else:
        ids = [i["id"] for i in pool[:PICK]]
    by_id = {i["id"]: i for i in pool}
    selected = [by_id[i] for i in ids if i in by_id]
    subject, body = build_email(selected, start, end)
    print(f"Předmět: {subject}")
    for item in selected:
        print(f"- {item.get('title')}")
    response = requests.post(
        BUTTONDOWN_URL,
        headers={"Authorization": f"Token {button_key}", "Content-Type": "application/json"},
        json={"subject": subject, "body": body, "status": EMAIL_STATUS},
        timeout=60,
    )
    if response.status_code >= 300:
        raise SystemExit(f"Buttondown {response.status_code}: {response.text[:500]}")
    email_id = response.json().get("id")
    print(f"Uloženo jako {EMAIL_STATUS}: {email_id}")


if __name__ == "__main__":
    main()
