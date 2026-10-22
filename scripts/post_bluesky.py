#!/usr/bin/env python3
"""Daily Bluesky post, using the existing local card. No Buffer or extra state commit.

One deterministic AT Protocol TID per UTC day prevents duplicates on reruns,
including concurrent runs or a lost createRecord response. --dry-run uses no API.
"""
import argparse
from datetime import datetime, timezone
from io import BytesIO
import json
import os
from pathlib import Path
import re
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

SITE_URL = 'https://kosmonovinky.cz'
COLLECTION = 'app.bsky.feed.post'
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


def compose(item):
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
        'features': [{'$type': 'app.bsky.richtext.facet#link', 'uri': SITE_URL}],
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


def prepare_image(path):
    from PIL import Image, ImageOps
    data = path.read_bytes()
    with Image.open(BytesIO(data)) as original:
        original.load()
        image = ImageOps.exif_transpose(original).convert('RGB')
        width, height = image.size
        if original.format == 'JPEG' and len(data) <= MAX_IMAGE_BYTES:
            return data, width, height
        # Recompress only the uploaded copy; never modify assets/cards/daily.jpg.
        for quality in (92, 85, 75, 65):
            buf = BytesIO()
            image.save(buf, format='JPEG', quality=quality, optimize=True)
            data = buf.getvalue()
            if len(data) <= MAX_IMAGE_BYTES:
                return data, width, height
    raise RuntimeError('Karta je i po kompresi příliš velká pro Bluesky.')


class ApiError(RuntimeError):
    def __init__(self, method, status, code):
        self.status, self.code = status, code
        super().__init__(f'Bluesky {method}: HTTP {status}, {code}')


def api(base, method, *, token=None, payload=None, data=None, params=None):
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
        with urlopen(request, timeout=45) as response:
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


def publish(item, card, day, handle, password):
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
    if get_existing(pds, token, did, key):
        print(f'Bluesky: denní příspěvek {day} už existuje, znovu jej neposílám.')
        return
    data, width, height = prepare_image(card)
    uploaded = api(pds, 'com.atproto.repo.uploadBlob', token=token, data=data)
    blob = uploaded.get('blob')
    if not blob or blob.get('mimeType') != 'image/jpeg':
        raise RuntimeError('Bluesky nepotvrdilo nahrání JPEG karty.')
    text, facets = compose(item)
    record = {
        '$type': COLLECTION, 'text': text, 'facets': facets, 'langs': ['cs'],
        'createdAt': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'embed': {'$type': 'app.bsky.embed.images', 'images': [{
            'alt': shorten('Kosmologické novinky – ' + clean(item.get('title')), 900),
            'image': blob, 'aspectRatio': {'width': width, 'height': height},
        }]},
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
    print(f'Bluesky: https://bsky.app/profile/{did}/post/{key}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--site-dir', type=Path, default=Path('.'))
    args = parser.parse_args()
    root = args.site_dir
    day = datetime.now(timezone.utc).date().isoformat()
    items = json.loads((root / 'data/news.json').read_text(encoding='utf-8'))
    today = [i for i in items if (i.get('inserted_at') or '')[:10] == day]
    if not today:
        print('Bluesky: dnes žádná nová položka – kartu neposílám.')
        return
    # Same ordering and Czech preference as scripts/generate_x_card.py:pick_item.
    item = next((i for i in today if i.get('lang') != 'en'
                 and not i.get('needs_translation')), today[0])
    card = root / 'assets/cards/daily.jpg'
    if not card.is_file():
        raise RuntimeError('Chybí assets/cards/daily.jpg – nic neodesláno.')
    text, _ = compose(item)
    if args.dry_run:
        data, width, height = prepare_image(card)
        print(f'NÁHLED – nic se neodesílá. Klíč dne: {daily_key(day)}')
        print(f'Karta: {width}×{height}, {len(data)} bajtů; text: {len(text)}/300 znaků')
        print(text)
        return
    handle = os.environ.get('BLUESKY_HANDLE', 'zdenekbubak.bsky.social').strip()
    password = os.environ.get('BLUESKY_APP_PASSWORD', '').strip()
    if not password:
        raise RuntimeError('V GitHub Secrets chybí BLUESKY_APP_PASSWORD.')
    publish(item, card, day, handle, password)


if __name__ == '__main__':
    main()
