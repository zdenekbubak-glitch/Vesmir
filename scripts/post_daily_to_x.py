#!/usr/bin/env python3
"""Zveřejní dnešní kartu na X jako @ZdenekBubak a odpoví odkazem na web.

Secrets: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

NEWS = Path("data/news.json")
CARD = Path("assets/cards/daily.jpg")
UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"
TWEET_URL = "https://api.x.com/2/tweets"
SITE = "https://kosmonovinky.cz"


def enc(value: str) -> str:
    return urllib.parse.quote(str(value), safe="")


def oauth_header(method: str, url: str, extra: dict | None = None) -> str:
    oauth = {
        "oauth_consumer_key": os.environ["X_API_KEY"],
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": os.environ["X_ACCESS_TOKEN"],
        "oauth_version": "1.0",
    }
    params = {**oauth, **(extra or {})}
    param_str = "&".join(f"{enc(k)}={enc(params[k])}" for k in sorted(params))
    base = "&".join([method.upper(), enc(url), enc(param_str)])
    key = f"{enc(os.environ['X_API_SECRET'])}&{enc(os.environ['X_ACCESS_TOKEN_SECRET'])}"
    digest = hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()
    oauth["oauth_signature"] = base64.b64encode(digest).decode()
    return "OAuth " + ", ".join(f'{enc(k)}="{enc(oauth[k])}"' for k in sorted(oauth))


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
    inserted = item.get("inserted_at") or ""
    try:
        stamp = datetime.fromisoformat(inserted.replace("Z", "+00:00"))
        day = stamp.astimezone(ZoneInfo("Europe/Prague")).date()
    except ValueError:
        return None
    today = datetime.now(ZoneInfo("Europe/Prague")).date()
    if day != today:
        print(f"Nejnovější příspěvek není z dneška ({day}). Na X neposílám.")
        return None
    return item


def upload_card() -> str:
    data = CARD.read_bytes()
    headers = {"Authorization": oauth_header("POST", UPLOAD_URL)}
    response = requests.post(
        UPLOAD_URL,
        headers=headers,
        files={"media": ("daily.jpg", data, "image/jpeg")},
        timeout=60,
    )
    if response.status_code >= 300:
        raise SystemExit(f"Nahrání obrázku selhalo {response.status_code}: {response.text[:400]}")
    media_id = response.json().get("media_id_string")
    if not media_id:
        raise SystemExit(f"API nevrátilo media_id: {response.text[:400]}")
    print(f"Obrázek nahrán: {media_id}")
    return media_id


def create_post(text: str, media_id: str | None = None, reply_to: str | None = None) -> str:
    body = {"text": text}
    if media_id:
        body["media"] = {"media_ids": [media_id]}
    if reply_to:
        body["reply"] = {"in_reply_to_tweet_id": reply_to}
    headers = {
        "Authorization": oauth_header("POST", TWEET_URL),
        "Content-Type": "application/json",
    }
    response = requests.post(TWEET_URL, headers=headers, json=body, timeout=60)
    if response.status_code >= 300:
        raise SystemExit(f"Příspěvek selhal {response.status_code}: {response.text[:500]}")
    post_id = response.json().get("data", {}).get("id")
    if not post_id:
        raise SystemExit(f"API nevrátilo id příspěvku: {response.text[:400]}")
    return post_id


def main():
    missing = [k for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET") if not os.environ.get(k)]
    if missing:
        raise SystemExit("Chybí secrets: " + ", ".join(missing))
    if not CARD.exists():
        raise SystemExit("Chybí assets/cards/daily.jpg")
    item = latest_today()
    if not item:
        return
    text = fit_text(item.get("title") or "", item.get("summary") or "")
    print(f"Text ({len(text)} znaků): {text[:120]}")
    media_id = upload_card()
    post_id = create_post(text, media_id=media_id)
    print(f"Příspěvek: https://x.com/ZdenekBubak/status/{post_id}")
    reply_id = create_post(SITE, reply_to=post_id)
    print(f"Odpověď: https://x.com/ZdenekBubak/status/{reply_id}")


if __name__ == "__main__":
    main()
