#!/usr/bin/env python3
"""Denní vyhledávání českých příspěvků o kosmologii na X a příprava quote postů / draftů v Bufferu."""

import json
import os
import time
from datetime import datetime, timedelta, timezone

import requests

GEMINI_MODEL = "gemini-3.6-flash"
BUFFER_ORG_ID = "6acb6d788c32e5c34832aa32"
BUFFER_X_CHANNEL_ID = "6acb6eaa778b240e2fd5fb5d"

KEYWORDS = (
    '"černá díra" OR "černé díry" OR "temná hmota" OR "temná energie" OR '
    '"gravitační vlny" OR "neutronová hvězda" OR "reliktní záření" OR '
    '"Hubbleovo napětí" OR kosmologie OR "kvantová gravitace"'
)

def search_x(bearer: str, hours: int = 36) -> list:
    """Hledá recent posty na X (last 7 days max)."""
    if not bearer:
        print("Chybí X_BEARER_TOKEN – vyhledávání přeskočeno.")
        return []
    query = f"({KEYWORDS}) lang:cs -is:retweet -is:reply"
    url = "https://api.x.com/2/tweets/search/recent"
    params = {
        "query": query,
        "max_results": 15,
        "tweet.fields": "created_at,public_metrics,author_id,text",
        "expansions": "author_id",
        "user.fields": "username,name",
    }
    headers = {"Authorization": f"Bearer {bearer}"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"X search selhal: {e}")
        return []
    users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
    posts = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    for t in data.get("data", []):
        created = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
        if created < cutoff:
            continue
        author = users.get(t.get("author_id"), {})
        posts.append({
            "id": t["id"],
            "text": t.get("text", ""),
            "created_at": t["created_at"],
            "username": author.get("username", ""),
            "name": author.get("name", ""),
            "url": f"https://x.com/{author.get('username','')}/status/{t['id']}",
            "likes": t.get("public_metrics", {}).get("like_count", 0),
        })
    print(f"X search: {len(posts)} kandidátů")
    return posts


def score_relevance(client, posts: list) -> list:
    """Gemini vyhodnotí vědeckou relevanci. Vrátí seřazený seznam s score."""
    if not client or not posts:
        return posts
    scored = []
    for p in posts:
        prompt = f"""Je tento český příspěvek na X vědecky relevantní pro kosmologii
(černé díry, temná hmota/energie, gravitační vlny, neutronové hvězdy, reliktní záření,
Hubbleovo napětí, inflace vesmíru, kvantová gravitace)?
Metaforické použití („černá díra peněz“, politika, inflace ekonomická, vtipy) = NE.
Odpověz pouze JSON: {{"relevant": true/false, "reason": "krátké zdůvodnění", "score": 0-10}}

Příspěvek:
{p['text'][:500]}
"""
        try:
            chat = client.chats.create(model=GEMINI_MODEL)
            text = (chat.send_message(prompt).text or "").strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            data = json.loads(text)
            p["relevant"] = bool(data.get("relevant"))
            p["score"] = int(data.get("score", 0))
            p["reason"] = data.get("reason", "")
        except Exception as e:
            print(f"Skórování selhalo pro {p['id']}: {e}")
            p["relevant"] = False
            p["score"] = 0
        if p["relevant"] and p["score"] >= 5:
            scored.append(p)
        time.sleep(0.6)
    scored.sort(key=lambda x: x["score"], reverse=True)
    print(f"Relevantních po filtrování: {len(scored)}")
    return scored


def buffer_create_post(api_key: str, text: str, as_draft: bool = False) -> dict | None:
    """Vytvoří post v Bufferu (quote style přes URL v textu)."""
    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess { post { id status text } }
        ... on MutationError { message }
      }
    }
    """
    variables = {
        "input": {
            "channelId": BUFFER_X_CHANNEL_ID,
            "schedulingType": "automatic",
            "mode": "shareNow" if not as_draft else "addToQueue",
            "text": text,
            "saveToDraft": as_draft,
        }
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(
            "https://api.buffer.com",
            json={"query": mutation, "variables": variables},
            headers=headers,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        result = data.get("data", {}).get("createPost", {})
        if "message" in result:
            print(f"Buffer chyba: {result['message']}")
            return None
        post = result.get("post", {})
        print(f"Buffer: vytvořen {post.get('id')} (draft={as_draft})")
        return post
    except Exception as e:
        print(f"Buffer create selhal: {e}")
        return None


def main():
    print("Spouštím vyhledávání a přípravu quote postů…")
    x_bearer = os.environ.get("X_BEARER_TOKEN", "")
    buffer_key = os.environ.get("BUFFER_API_KEY", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")

    if not buffer_key:
        print("Chybí BUFFER_API_KEY – končím.")
        return

    posts = search_x(x_bearer)
    if not posts:
        print("Žádní kandidáti.")
        return

    client = None
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
        except Exception as e:
            print(f"Gemini client: {e}")

    relevant = score_relevance(client, posts)
    if not relevant:
        print("Žádné dostatečně relevantní příspěvky.")
        return

    # 1–2 nejlepší do fronty, zbytek (max 5) jako drafty
    auto = relevant[:2]
    drafts = relevant[2:7]

    for p in auto:
        comment = (
            f"Zajímavý pohled na {p['reason'][:80] if p.get('reason') else 'téma'}. "
            f"Více česky na kosmonovinky.cz"
        )
        text = f"{comment}\n\n{p['url']}"
        buffer_create_post(buffer_key, text, as_draft=False)
        time.sleep(1)

    for p in drafts:
        comment = (
            f"Možná relevantní: {p['text'][:100].replace(chr(10), ' ')}… "
            f"(skóre {p.get('score', 0)})"
        )
        text = f"{comment}\n\n{p['url']}"
        buffer_create_post(buffer_key, text, as_draft=True)
        time.sleep(1)

    print(f"Hotovo. Automaticky: {len(auto)}, drafty: {len(drafts)}")


if __name__ == "__main__":
    main()
