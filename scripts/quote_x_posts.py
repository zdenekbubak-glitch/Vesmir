#!/usr/bin/env python3
from social_tracking import post_key, tracked_url, receipt
"""Denní vyhledávání českých příspěvků o kosmologii na X a příprava quote postů / draftů v Bufferu."""

import json
import os
import re
import time
import unicodedata
from urllib.parse import urlsplit
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

GEMINI_MODEL = "gemini-3.6-flash"
BUFFER_ORG_ID = "6acb6d788c32e5c34832aa32"
BUFFER_X_CHANNEL_ID = "6acb6eaa778b240e2fd5fb5d"

KEYWORDS = (
    '"černá díra" OR "černé díry" OR "temná hmota" OR "temná energie" OR '
    '"gravitační vlny" OR "neutronová hvězda" OR "reliktní záření" OR '
    '"Hubbleovo napětí" OR kosmologie OR "kvantová gravitace"'
)

# Záložní, širší dotaz – použije se, když primární nic nenajde (např. víkend)
KEYWORDS_BROAD = (
    '"vesmír" OR "vesmíru" OR "vesmírný" OR galaxie OR "galaxií" OR "galaxiích" OR '
    '"černá díra" OR "černé díry" OR "temná hmota" OR kosmologie OR '
    '"James Webb" OR JWST OR Euclid OR "Hubbleův" OR "Hubbleovo" OR teleskop OR '
    '"kosmický" OR astronaut OR "nová studie" OR "vědci objevili"'
)

# Vlastní účty webu – jejich posty se nikdy necitují
EXCLUDED_USERNAMES = {"zdenekbubak"}

def _run_query(bearer: str, query: str, hours: int) -> list:
    """Jedno volání X search; vrátí normalizované posty nebo []."""
    url = "https://api.x.com/2/tweets/search/recent"
    params = {
        "query": query,
        "max_results": 30,
        "tweet.fields": "created_at,public_metrics,author_id,text",
        "expansions": "author_id",
        "user.fields": "username,name",
    }
    headers = {"Authorization": f"Bearer {bearer}"}
    r = requests.get(url, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
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
    return posts


def search_x(bearer: str, hours: int = 36) -> list:
    """Hledá recent posty na X (last 7 days max). Primární přesný dotaz,
    při prázdném výsledku záložní širší dotaz (72 h)."""
    if not bearer:
        raise RuntimeError("Chybí X_BEARER_TOKEN")
    strategies = [
        (f"({KEYWORDS}) lang:cs -is:retweet -is:reply -from:ZdenekBubak", hours, "primární"),
        (f"({KEYWORDS_BROAD}) lang:cs -is:retweet -is:reply -from:ZdenekBubak", 72, "záložní"),
    ]
    posts = []
    used = load_used()
    reviewed = load_state()["reviewed"]
    search_errors = []
    for query, window, label in strategies:
        try:
            posts = _run_query(bearer, query, window)
        except Exception as e:
            print(f"X search selhal ({label}): {e}")
            search_errors.append(label)
            continue
        posts = [p for p in posts if p["username"].lower() not in EXCLUDED_USERNAMES]
        print(f"X search ({label}): {len(posts)} kandidátů")
        fresh = [p for p in posts if p["id"] not in used and not recently_rejected(reviewed.get(p["id"]))]
        print(f"Nových k posouzení ({label}): {len(fresh)}")
        if fresh:
            return fresh
    if search_errors:
        raise RuntimeError("Vyhledávání X selhalo: " + ", ".join(search_errors))
    if not posts:
        print("::warning::X search nenašel žádné kandidáty – do Bufferu se dnes nic nepřidalo")
        return posts
    return []


def score_relevance(client, posts: list) -> list:
    """Gemini vyhodnotí vědeckou relevanci. Vrátí seřazený seznam s score."""
    if not client:
        raise RuntimeError("Chybí funkční Gemini klient; bez hodnocení se nic nepublikuje.")
    if not posts:
        return []
    scored = []
    for p in posts:
        prompt = f"""Je tento český příspěvek na X vědecky relevantní pro kosmologii
(černé díry, temná hmota/energie, gravitační vlny, neutronové hvězdy, reliktní záření,
Hubbleovo napětí, inflace vesmíru, kvantová gravitace)?
Metaforické použití („černá díra peněz“, politika, inflace ekonomická, vtipy) = NE.
Odpověz pouze JSON: {{"relevant": true/false, "reason": "krátké zdůvodnění", "score": 0-10,
"comment": "1-2 krátké české věty, přirozený komentář ke sdílení na X jako web Kosmonovinky; bez slov 'příspěvek', 'tento text', 'autor'; max 200 znaků"}}

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
            if not isinstance(data.get("relevant"), bool):
                raise ValueError("relevant musí být boolean")
            p["evaluated"] = True
            p["relevant"] = data["relevant"]
            p["score"] = max(0, min(10, int(data.get("score", 0))))
            p["reason"] = data.get("reason", "")
            p["comment"] = str(data.get("comment", "") or "").strip()
        except Exception as e:
            print(f"Skórování selhalo pro {p['id']}: {e}")
            p["evaluated"] = False
            p["relevant"] = False
            p["score"] = 0
        if p["relevant"] and p["score"] >= 5:
            scored.append(p)
        time.sleep(0.6)
    scored.sort(key=lambda x: x["score"], reverse=True)
    print(f"Relevantních po filtrování: {len(scored)}")
    return scored


STATE_DIR = Path("state")
STATE_FILE = STATE_DIR / "quote_x_used.json"


def load_state():
    if not STATE_FILE.exists():
        return {"version": 2, "used": [], "reviewed": {}}
    data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    # Old IDs may already have been posted: retain all to avoid duplicates.
    if isinstance(data, list):
        return {"version": 2, "used": data, "reviewed": {}}
    if not isinstance(data, dict) or not isinstance(data.get("used"), list) or not isinstance(data.get("reviewed"), dict):
        raise ValueError("Neplatný stav quote_x_used.json; nelze bezpečně zabránit duplicitám")
    return data


def load_used():
    return set(load_state()["used"])


def save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STATE_FILE)


def recently_rejected(record):
    if not record or record.get("relevant"):
        return False
    when = datetime.fromisoformat(record["at"])
    return datetime.now(timezone.utc) - when < timedelta(hours=24)



def make_comment(p: dict) -> str:
    """Vrátí čistý citátový komentář (max ~220 znaků, celé věty)."""
    c = (p.get("comment") or "").strip()
    # odstraň meta-úvody, kdyby se přesto objevily
    for pre in ("Příspěvek popisuje", "Příspěvek se zabývá", "Tento příspěvek", "Tento text", "Zajímavý pohled", "Jde o příspěvek", "Příspěvek", "Jde o"):
        if c.startswith(pre):
            c = c[len(pre):].lstrip(" :–-")
            break
    c = c.strip()
    if c:
        c = c[0].upper() + c[1:]
    if not c:
        # fallback: první věta z původního textu
        t = re.sub(r"\s+", " ", p.get("text", "")).strip()
        m = re.split(r"(?<=[.!?…])\s", t)
        c = (m[0] if m else t)[:160].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    if len(c) > 195:
        cut = c[:195]
        dot = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
        if dot > 60:
            c = cut[:dot + 1]
        else:
            c = cut.rsplit(" ", 1)[0].rstrip(",;:") + "…"
    if c and c[-1] not in ".!?…":
        c += "."
    return c


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
    r = requests.post(
        "https://api.buffer.com", json={"query": mutation, "variables": variables},
        headers=headers, timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise RuntimeError("Buffer GraphQL: " + json.dumps(data["errors"], ensure_ascii=False))
    result = (data.get("data") or {}).get("createPost") or {}
    if result.get("message"):
        raise RuntimeError("Buffer: " + str(result["message"]))
    post = result.get("post") or {}
    if not post.get("id"):
        raise RuntimeError("Buffer nevrátil ID příspěvku")
    # Retain a confirmed ID even if the returned status needs manual inspection.
    post["_status_ok"] = not as_draft or str(post.get("status", "")).lower() == "draft"
    print(f"Buffer: potvrzen {post['id']} (draft={as_draft}, status={post.get('status')})")
    return post


URL_RE = re.compile(r"https?://[^\s<>]+")
BASE_URL = "https://kosmonovinky.cz"


def weighted_length(text):
    """Conservative twitter-text v3 weights; joined emoji may be overcounted."""
    text = unicodedata.normalize("NFC", text)
    total = 0
    pos = 0
    for match in URL_RE.finditer(text):
        total += sum(char_weight(c) for c in text[pos:match.start()]) + 23
        pos = match.end()
    return total + sum(char_weight(c) for c in text[pos:])


def char_weight(c):
    n = ord(c)
    return 1 if n <= 4351 or 8192 <= n <= 8205 or 8208 <= n <= 8223 or 8242 <= n <= 8247 else 2


def compose_post(post, article_url=None, as_draft=False):
    comment = unicodedata.normalize("NFC", make_comment(post))
    comment = URL_RE.sub("", comment).strip()
    # Preserve both links; shorten only the generated commentary.
    suffix = "\n\nPřehledně česky: " + tracked_url(article_url or BASE_URL + "/", "x", "reply" if as_draft else "quote", post_key("x", "reply" if as_draft else "quote", post["id"])) + "\n\n" + post["url"]
    if as_draft:
        suffix += f"\n(k posouzení, skóre {post.get('score', 0)})"
    while comment and (weighted_length(comment) > 180 or weighted_length(comment + suffix) > 275):
        comment = comment.rstrip(".… ")
        comment = (comment.rsplit(" ", 1)[0] if " " in comment else comment[:-1]).rstrip(",;:") + "…"
    text = comment + suffix
    if not comment or weighted_length(text) > 280:
        raise ValueError("Příspěvek se nevejde do limitu X")
    return text


def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c))


STOP = set("tento tato teto tak ktere ktery ktera jsou bude bylo byla jako proto vice velmi jeho jejich mezi nebo take podle nove novy nova novych novou vedci studie vesmir vesmiru vyzkum ukazuje mohl muze mohou prave dalsi prvni pomoci proti vubec jeste tedy kdyz vsechny neznam znam".split())


def tokens(text):
    # Short Czech stems tolerate common inflections without additional dependencies.
    return {w[:6] for w in re.findall(r"[a-z0-9]+", normalized(URL_RE.sub('', text))) if len(w) >= 4 and w not in STOP}


def related_article(post, site=Path('.')):
    """Use exact published paths from the preview manifest; never invent a slug."""
    try:
        news = json.loads((site/'data/news.json').read_text(encoding='utf-8'))
        manifest = json.loads((site/'data/article_image_previews.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        print(f"::warning::Výběr článku nedostupný: {exc}; použiji hlavní stránku")
        return None
    query = tokens(post['text']); ranked = []
    for item in news:
        identity = str(item.get('id') or item.get('url') or item.get('title') or '')
        href = (manifest.get(identity) or {}).get('href', '')
        if not re.fullmatch(r'/clanky/[a-z0-9-]+\.html', href):
            continue
        title = tokens(item.get('title') or '')
        body = tokens((item.get('summary') or '')[:1200])
        overlap = query & (title | body)
        score = 3 * len(query & title) + len(query & body)
        if len(overlap) >= 3 and score >= 7:
            ranked.append((score, item.get('inserted_at') or '', href, item.get('title')))
    for score, _, href, title in sorted(ranked, reverse=True)[:3]:
        url = BASE_URL + href
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200 and urlsplit(response.url).netloc == 'kosmonovinky.cz':
                print(f"Související článek ({score}): {title} → {url}")
                return url
        except requests.RequestException:
            pass
    print("Nenalezen dostatečně související a dostupný článek; použiji hlavní stránku")
    return None


def process_posts(relevant, buffer_key, state):
    """At most two immediate quotes, then five drafts; success means a returned ID."""
    auto = relevant[:2]; drafts = relevant[2:7]
    counts = {"auto": 0, "drafts": 0, "failed": 0}
    for as_draft, selected in ((False, auto), (True, drafts)):
        for post in selected:
            try:
                text = compose_post(post, related_article(post), as_draft)
                print(f"Odesílám {post['id']} (draft={as_draft}, délka={weighted_length(text)})")
                created = buffer_create_post(buffer_key, text, as_draft)
                receipt('x', 'reply' if as_draft else 'quote', post_key('x','reply' if as_draft else 'quote',post['id']), post.get('text',''), created['id'], created.get('status'))
                state['used'] = sorted(set(state['used']) | {post['id']})
                state['reviewed'][post['id']] = {"at": datetime.now(timezone.utc).isoformat(),
                    "relevant": True, "score": post.get('score'), "buffer_id": created['id'],
                    "kind": 'draft' if as_draft else 'quote', "status": created.get('status')}
                save_state(state)
                if not created['_status_ok']:
                    raise RuntimeError(f"ID {created['id']} vzniklo, ale stav není draft; zkontrolujte Buffer (automaticky neopakuji)")
                counts['drafts' if as_draft else 'auto'] += 1
            except Exception as exc:
                counts['failed'] += 1
                print(f"::error::Příspěvek {post['id']}: {exc}")
            time.sleep(1)
    print(f"Hotovo. Potvrzené citace: {counts['auto']}, potvrzené drafty: {counts['drafts']}, chyby: {counts['failed']}")
    if not drafts:
        print(f"Drafty se nevytvářely: relevantních kandidátů {len(relevant)}, první dva mají přednost pro citaci.")
    if counts['failed']:
        raise RuntimeError("Část požadavků na Buffer selhala; viz chyby výše. Potvrzené položky jsou uložené ve stavu.")
    return counts


def main():
    print("Spouštím vyhledávání a přípravu quote postů…")
    x_bearer = os.environ.get("X_BEARER_TOKEN", "")
    buffer_key = os.environ.get("BUFFER_API_KEY", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")

    if not buffer_key:
        raise RuntimeError("Chybí BUFFER_API_KEY")

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
    state = load_state()
    for post in posts:
        if post.get('evaluated'):
            state['reviewed'][post['id']] = {"at": datetime.now(timezone.utc).isoformat(),
                "relevant": post.get('relevant', False) and post.get('score', 0) >= 5,
                "score": post.get('score', 0)}
    save_state(state)
    errors = [p for p in posts if not p.get('evaluated')]
    if not relevant:
        if errors:
            raise RuntimeError("Hodnocení kandidátů selhalo; neúspěšná hodnocení se mohou opakovat")
        print("Žádné dostatečně relevantní příspěvky.")
        return

    state = load_state()
    process_posts(relevant, buffer_key, state)
    if errors:
        raise RuntimeError(f"U {len(errors)} kandidátů selhalo hodnocení; potvrzené položky jsou uložené.")


if __name__ == "__main__":
    main()
