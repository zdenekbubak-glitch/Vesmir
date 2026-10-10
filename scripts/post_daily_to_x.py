#!/usr/bin/env python3
"""Zveřejní dnešní kartu na X a odpoví odkazem na web.

OAuth 2.0 user token. Secrets:
X_OAUTH2_ACCESS_TOKEN, X_OAUTH2_REFRESH_TOKEN, X_CLIENT_ID, X_CLIENT_SECRET
"""

import base64
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

NEWS = Path("data/news.json")
CARD = Path("assets/cards/daily.jpg")
UPLOAD_URL = "https://api.x.com/2/media/upload"
TWEET_URL = "https://api.x.com/2/tweets"
TOKEN_URL = "https://api.x.com/2/oauth2/token"
SITE = "https://kosmonovinky.cz"


def fit_text(title: str, summary: str) -> str:
    title = " ".join((title or "").split())
    summary = " ".join((summary or "").split())
    if len(title) > 270:
        return title[:269].rstrip() + "…"
    room = 280 - len(title) - 2
    if room < 16 or not summary:
        return title
    if len(summary) > room:
        summary = summary[: room - 1].rstrip() + "…"
    return f"{title}\n\n{summary}"


def latest_today():
    items = json.loads(NEWS.read_text(encoding="utf-8"))
    if not items:
        return None
    item = items[0]
    try:
        stamp = datetime.fromisoformat((item.get("inserted_at") or "").replace("Z", "+00:00"))
        day = stamp.astimezone(ZoneInfo("Europe/Prague")).date()
    except ValueError:
        return None
    if day != datetime.now(ZoneInfo("Europe/Prague")).date():
        print(f"Nejnovější příspěvek není z dneška ({day}). Na X neposílám.")
        return None
    return item


def refresh_access_token() -> str:
    client_id = (os.environ.get("X_CLIENT_ID") or "").strip()
    client_secret = (os.environ.get("X_CLIENT_SECRET") or "").strip()
    refresh = (os.environ.get("X_OAUTH2_REFRESH_TOKEN") or "").strip()
    if not (client_id and client_secret and refresh):
        raise SystemExit("Chybí X_CLIENT_ID, X_CLIENT_SECRET nebo X_OAUTH2_REFRESH_TOKEN")
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "refresh_token", "refresh_token": refresh},
        timeout=60,
    )
    if response.status_code >= 300:
        raise SystemExit(f"Obnova tokenu selhala {response.status_code}: {response.text[:400]}")
    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise SystemExit("Obnova nevrátila access_token")
    if payload.get("refresh_token"):
        print("X vrátilo nový refresh token. Uložte ho do X_OAUTH2_REFRESH_TOKEN, starý už neplatí.")
    print("Access token obnoven.")
    return token


def upload_card(token: str) -> str:
    response = requests.post(
        UPLOAD_URL,
        headers={"Authorization": f"Bearer {token}"},
        files={"media": ("daily.jpg", CARD.read_bytes(), "image/jpeg")},
        data={"media_category": "tweet_image"},
        timeout=60,
    )
    if response.status_code == 401:
        return ""
    if response.status_code >= 300:
        raise SystemExit(f"Nahrání obrázku selhalo {response.status_code}: {response.text[:500]}")
    payload = response.json()
    media_id = (payload.get("data") or {}).get("id") or payload.get("media_id_string")
    if not media_id:
        raise SystemExit(f"API nevrátilo media_id: {response.text[:400]}")
    print(f"Obrázek nahrán: {media_id}")
    return str(media_id)


def create_post(token: str, text: str, media_id: str | None = None, reply_to: str | None = None):
    body = {"text": text}
    if media_id:
        body["media"] = {"media_ids": [media_id]}
    if reply_to:
        body["reply"] = {"in_reply_to_tweet_id": reply_to}
    response = requests.post(
        TWEET_URL,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=body,
        timeout=60,
    )
    return response


def main():
    token = (os.environ.get("X_OAUTH2_ACCESS_TOKEN") or "").strip()
    if not token:
        token = refresh_access_token()
    if not CARD.exists():
        raise SystemExit("Chybí assets/cards/daily.jpg")
    item = latest_today()
    if not item:
        return
    text = fit_text(item.get("title") or "", item.get("summary") or "")
    print(f"Text ({len(text)} znaků): {text[:120]}")

    media_id = upload_card(token)
    if not media_id:
        print("Access token vypršel, obnovuji.")
        token = refresh_access_token()
        media_id = upload_card(token)
        if not media_id:
            raise SystemExit("Nahrání obrázku selhalo i po obnově tokenu")

    response = create_post(token, text, media_id=media_id)
    if response.status_code == 401:
        print("Access token vypršel při publikování, obnovuji.")
        token = refresh_access_token()
        response = create_post(token, text, media_id=media_id)
    if response.status_code >= 300:
        raise SystemExit(f"Příspěvek selhal {response.status_code}: {response.text[:500]}")
    post_id = response.json().get("data", {}).get("id")
    if not post_id:
        raise SystemExit(f"API nevrátilo id příspěvku: {response.text[:400]}")
    print(f"Příspěvek: https://x.com/ZdenekBubak/status/{post_id}")

    reply = create_post(token, SITE, reply_to=post_id)
    if reply.status_code >= 300:
        raise SystemExit(f"Odpověď selhala {reply.status_code}: {reply.text[:500]}")
    reply_id = reply.json().get("data", {}).get("id")
    print(f"Odpověď: https://x.com/ZdenekBubak/status/{reply_id}")


if __name__ == "__main__":
    main()
