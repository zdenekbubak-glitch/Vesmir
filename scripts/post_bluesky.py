#!/usr/bin/env python3
"""Daily Bluesky post with a clickable article card. No Buffer or extra state commit.

One deterministic AT Protocol TID per UTC day prevents duplicates on reruns,
including concurrent runs or a lost createRecord response. Publication is confirmed
only after a public AppView read; pending visibility is a warning, not a failed
write. --dry-run makes no publishing API calls.
"""
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
from io import BytesIO
import json
import os
from pathlib import Path
import time
import re
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

from social_tracking import post_key, tracked_url, receipt, article_url, pick_daily_link_item

SITE_URL = 'https://kosmonovinky.cz'
COLLECTION = 'app.bsky.feed.post'
PUBLIC_APPVIEW = 'https://public.api.bsky.app'
VISIBILITY_ATTEMPTS = 3
VISIBILITY_RETRY_SECONDS = 15
MAX_IMAGE_BYTES = 1_000_000  # Conservative limit, also accepted by older PDS versions.


def clean(value):
    return unicodedata.normalize('NFC', re.sub(r'\s+', ' ', str(value or '')).strip())


def shorten(text, limit):
    if len(text) <= limit:
        return text
    part = text[:limit - 1]
    if ' ' in part:
        part = part.rsplit(' ', 1)[0]
    # Do not end immediately before an isolated combining mark.
    return part.rstrip(' ,;:–—-') + '…'


def compose(item, target, day):
    title = clean(item.get('title')) or 'Kosmologické novinky'
    summary = clean(item.get('summary')).split('Proč je to zajímavé:')[0].strip()
    budget = 300 - len('\n\n' + SITE_URL)
    # Codepoint counting is conservative: a grapheme can contain several codepoints.
    heading = shorten(title, budget)
    remaining = budget - len(heading) - 2
    body = heading
    if summary and remaining >= 35:
        body += '\n\n' + shorten(summary, remaining)
    text = body + '\n\n' + SITE_URL
    start = len(text[:-len(SITE_URL)].encode('utf-8'))
    facets = [{
        'index': {'byteStart': start, 'byteEnd': len(text.encode('utf-8'))},
        'features': [{'$type': 'app.bsky.richtext.facet#link', 'uri': tracked_url(target, 'bluesky', 'daily', post_key('bluesky', 'daily', day))}],
    }]
    return text, facets


def daily_key(day):
    # A valid 13-character TID (microseconds since epoch + 10 clock-id bits).
    # Fixed time/clock make this key identical across all runs for the same day.
    stamp = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
    value = (int(stamp.timestamp()) * 1_000_000 << 10) | 341
    alphabet = '234567abcdefghijklmnopqrstuvwxyz'
    chars = []
    for _ in range(13):
        chars.append(alphabet[value & 31])
        value >>= 5
    return ''.join(reversed(chars))


class OpenGraphImage(HTMLParser):
    image = None

    def handle_starttag(self, tag, attrs):
        if tag == 'meta':
            attributes = dict(attrs)
            if attributes.get('property') == 'og:image' and not self.image:
                self.image = attributes.get('content')


def prepare_image(target):
    from PIL import Image, ImageOps
    with urlopen(target, timeout=20) as response:
        parser = OpenGraphImage()
        parser.feed(response.read().decode('utf-8'))
    if not parser.image:
        return None

    url = urljoin(target, parser.image)
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.netloc != 'kosmonovinky.cz':
        raise RuntimeError('Obrázek článku nemá očekávanou adresu.')
    with urlopen(url, timeout=20) as response:
        data = response.read(10_000_001)
    if len(data) > 10_000_000:
        raise RuntimeError('Obrázek článku je příliš velký.')
    with Image.open(BytesIO(data)) as original:
        image = ImageOps.exif_transpose(original).convert('RGB')
        image.thumbnail((1200, 1200))
        for quality in (90, 80, 65):
            buf = BytesIO()
            image.save(buf, format='JPEG', quality=quality, optimize=True)
            data = buf.getvalue()
            if len(data) <= MAX_IMAGE_BYTES:
                return data
    raise RuntimeError('Obrázek článku je i po kompresi příliš velký.')


def article_embed(item, target, day):
    return {
        '$type': 'app.bsky.embed.external',
        'external': {
            'uri': tracked_url(target, 'bluesky', 'daily', post_key('bluesky', 'daily', day)),
            'title': clean(item.get('title')) or 'Kosmologické novinky',
            'description': shorten(clean(item.get('summary')).split('Proč je to zajímavé:')[0].strip(), 240),
        },
    }


class ApiError(RuntimeError):
    def __init__(self, method, status, code):
        self.status, self.code = status, code
        super().__init__(f'Bluesky {method}: HTTP {status}, {code}')


def api(base, method, *, token=None, payload=None, data=None, params=None, timeout=45):
    url = base.rstrip('/') + '/xrpc/' + method
    if params:
        url += '?' + urlencode(params)
    headers = {'Accept': 'application/json', 'User-Agent': 'Kosmonovinky-Daily/1.0'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    elif data is not None:
        headers['Content-Type'] = 'image/jpeg'
    request = Request(url, data=data, headers=headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except HTTPError as exc:
        # Never print raw responses, tokens, authentication payloads or headers.
        try:
            code = json.loads(exc.read()).get('error', 'ApiError')
        except (ValueError, AttributeError):
            code = 'ApiError'
        code = re.sub(r'[^A-Za-z0-9_]', '', str(code))[:80]
        raise ApiError(method, exc.code, code) from None
    except (URLError, TimeoutError, OSError):
        raise RuntimeError(f'Bluesky {method}: síťová chyba nebo vypršel čas.') from None


def get_existing(pds, token, did, key):
    try:
        return api(pds, 'com.atproto.repo.getRecord', token=token,
                   params={'repo': did, 'collection': COLLECTION, 'rkey': key})
    except ApiError as exc:
        if exc.code == 'RecordNotFound':
            return None
        raise


def public_visibility(uri):
    """Read only: distinguish an absent post from an unavailable public API."""
    absent = False
    for attempt in range(VISIBILITY_ATTEMPTS):
        try:
            response = api(PUBLIC_APPVIEW, 'app.bsky.feed.getPosts',
                           params={'uris': uri}, timeout=15)
            posts = response.get('posts') if isinstance(response, dict) else None
            if isinstance(posts, list):
                if any(isinstance(post, dict) and post.get('uri') == uri for post in posts):
                    return 'visible'
                absent = True
        except RuntimeError:
            # api() sanitizes errors; never log headers, tokens or raw responses.
            pass
        if attempt + 1 < VISIBILITY_ATTEMPTS:
            time.sleep(VISIBILITY_RETRY_SECONDS)
    return 'not_visible' if absent else 'unverified'


def confirm_publication(item, day, did, key, target):
    """Call only after the record has been confirmed on the account's PDS."""
    uri = f'at://{did}/{COLLECTION}/{key}'
    link = f'https://bsky.app/profile/{did}/post/{key}'
    print(f'Bluesky: příspěvek je uložen na serveru účtu: {link}')
    visibility = public_visibility(uri)
    status = {'visible': 'published', 'not_visible': 'stored_pending_visibility',
              'unverified': 'stored_visibility_unverified'}[visibility]
    receipt('bluesky', 'daily', post_key('bluesky', 'daily', day),
            item.get('title', ''), uri, status, target=target)
    if visibility == 'visible':
        print('Bluesky: příspěvek je uložen a jeho veřejná dostupnost je ověřena.')
        return
    if visibility == 'not_visible':
        message = ('Bluesky: příspěvek je uložen, ale veřejné rozhraní jej zatím '
                   'nevrací ani po opakované kontrole. Nevytvářím duplicitu.')
    else:
        message = ('Bluesky: příspěvek je uložen, ale dostupnost ve veřejném '
                   'rozhraní se nepodařilo ověřit. Nevytvářím duplicitu.')
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        print('::warning::' + message)
    else:
        print(message)
    # A confirmed PDS write succeeded; AppView lag is not a publication error.
    return


def publish(item, day, handle, password, target):
    session = api('https://bsky.social', 'com.atproto.server.createSession',
                  payload={'identifier': handle, 'password': password})
    did, token = session['did'], session['accessJwt']
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        for field in ('accessJwt', 'refreshJwt'):
            if session.get(field):
                print('::add-mask::' + session[field])
    services = session.get('didDoc', {}).get('service', [])
    pds = next((s.get('serviceEndpoint') for s in services
                if s.get('id', '').endswith('#atproto_pds')), None)
    if not isinstance(pds, str):
        raise RuntimeError('Přihlášení nevrátilo adresu Bluesky PDS serveru.')
    endpoint = urlsplit(pds)
    if (endpoint.scheme != 'https' or not endpoint.hostname or endpoint.username
            or endpoint.password or endpoint.query or endpoint.fragment):
        raise RuntimeError('Neplatná adresa Bluesky PDS serveru.')
    key = daily_key(day)
    existing = get_existing(pds, token, did, key)
    if existing:
        print(f'Bluesky: denní příspěvek {day} už existuje, znovu jej neposílám.')
        # On reruns record the destination of the already stored post, not a new one.
        stored_target = SITE_URL
        for facet in existing.get('value', {}).get('facets', []):
            for feature in facet.get('features', []):
                uri = feature.get('uri', '')
                parsed = urlsplit(uri)
                if parsed.scheme == 'https' and parsed.hostname == 'kosmonovinky.cz':
                    stored_target = SITE_URL + (parsed.path or '/')
        confirm_publication(item, day, did, key, stored_target)
        return
    embed = article_embed(item, target, day)
    try:
        data = prepare_image(target)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f'::warning::Bluesky: náhled obrázku není dostupný ({exc}).')
        data = None
    if data:
        uploaded = api(pds, 'com.atproto.repo.uploadBlob', token=token, data=data)
        blob = uploaded.get('blob')
        if not blob or blob.get('mimeType') != 'image/jpeg':
            raise RuntimeError('Bluesky nepotvrdilo nahrání náhledu článku.')
        embed['external']['thumb'] = blob
    else:
        print('Bluesky: zveřejním klikací kartu bez náhledu obrázku.')
    text, facets = compose(item, target, day)
    record = {
        '$type': COLLECTION, 'text': text, 'facets': facets, 'langs': ['cs'],
        'createdAt': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'embed': embed,
    }
    try:
        result = api(pds, 'com.atproto.repo.createRecord', token=token, payload={
            'repo': did, 'collection': COLLECTION, 'rkey': key, 'record': record,
        })
        expected = f'at://{did}/{COLLECTION}/{key}'
        if result.get('uri') != expected or not result.get('cid'):
            raise RuntimeError('Bluesky nevrátilo potvrzení vytvořeného příspěvku.')
    except RuntimeError:
        # Handles a lost response or a parallel run winning the same record key.
        if not get_existing(pds, token, did, key):
            raise
        print('Bluesky: příspěvek byl ověřen na serveru po nejednoznačné odpovědi.')
    confirm_publication(item, day, did, key, target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--site-dir', type=Path, default=Path('.'))
    args = parser.parse_args()
    root = args.site_dir
    day = datetime.now(timezone.utc).date().isoformat()
    items = json.loads((root / 'data/news.json').read_text(encoding='utf-8'))
    item = pick_daily_link_item(items, day)
    if not item:
        print('Bluesky: dnes není způsobilý český článek.')
        return
    source = 'článek z karty X' if item.get('daily_card_selected') else 'první způsobilý český článek'
    print(f"Bluesky: {source} – {item['title']}")
    target = article_url(item, items)
    text, _ = compose(item, target, day)
    if args.dry_run:
        data = prepare_image(target)
        print(f'NÁHLED – nic se neodesílá. Klíč dne: {daily_key(day)}')
        print(f'Náhled: {len(data) if data else 0} bajtů; text: {len(text)}/300 znaků')
        print(text)
        print('Cíl karty: ' + article_embed(item, target, day)['external']['uri'])
        return
    handle = os.environ.get('BLUESKY_HANDLE', 'zdenekbubak.bsky.social').strip()
    password = os.environ.get('BLUESKY_APP_PASSWORD', '').strip()
    if not password:
        raise RuntimeError('V GitHub Secrets chybí BLUESKY_APP_PASSWORD.')
    publish(item, day, handle, password, target)


if __name__ == '__main__':
    main()
