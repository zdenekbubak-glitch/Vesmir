"""Standard-library attribution and publication receipts. Does not publish posts."""
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import json
import re

SPOOL = Path('.social-receipts.jsonl')

def post_key(source, kind, identity):
    import hashlib
    return source + '_' + kind + '_' + hashlib.sha256(str(identity).encode()).hexdigest()[:20]

def tracked_url(url, source, kind, key):
    p = urlsplit(url)
    if p.scheme != 'https' or p.hostname != 'kosmonovinky.cz':
        raise ValueError('Only kosmonovinky.cz links may be tagged')
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not k.startswith('utm_')]
    query += [('utm_source', source), ('utm_medium', 'social'), ('utm_campaign', 'kosmonovinky'), ('utm_content', key), ('utm_term', kind)]
    return urlunsplit((p.scheme, p.netloc, p.path or '/', urlencode(query), p.fragment))

def article_url(item, items):
    """Resolve exactly the article path used by tools/build_static.py, including collisions."""
    import unicodedata
    def slug(title):
        text = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii').lower()
        return '-'.join(re.sub(r'[^a-z0-9]+', ' ', text).split()[:10]) or 'clanek'
    used = set()
    for row in sorted(items, key=lambda x: x.get('inserted_at') or '', reverse=True):
        base = slug(row.get('title', 'clanek')) + '-' + (re.sub(r'[^0-9]', '', str(row.get('id')))[:12] or '0')
        name, number = base, 2
        while name in used:
            name = base + '-' + str(number)
            number += 1
        used.add(name)
        if row is item:
            return 'https://kosmonovinky.cz/clanky/' + name + '.html'
    raise ValueError('Selected daily article is not in news.json')


def receipt(source, kind, key, title, platform_id, status, target='https://kosmonovinky.cz/'):
    recheck_pending()
    # Buffer acceptance is not proof of publication. Keep its returned status.
    record = dict(source=source, kind=kind, key=key, title=str(title)[:300], platform_id=str(platform_id), status=str(status or 'submitted').lower(), target=target,
                  recorded_at=datetime.now(timezone.utc).isoformat())
    with SPOOL.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')

# Reconcile earlier receipts during the existing posting workflow.
# These requests only read status and never create, resend or edit a post.
_rechecked = False

def recheck_pending():
    global _rechecked
    if _rechecked:
        return
    _rechecked = True
    import os
    from urllib.request import Request, urlopen
    now = datetime.now(timezone.utc)
    path = Path('data/social_posts.json')
    if not path.exists():
        return
    try:
        records = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return
    if not isinstance(records, list):
        return
    token = os.environ.get('BUFFER_API_KEY')
    terminal = {'published', 'sent', 'posted', 'draft', 'failed', 'error', 'deleted'}
    pending = [row for row in records if isinstance(row, dict) and str(row.get('status', '')).lower() not in terminal]
    for old in pending[:20]:
        row = dict(old)
        checked = row.get('last_check_attempt_at')
        if checked:
            try:
                if (now - datetime.fromisoformat(checked.replace('Z', '+00:00'))).total_seconds() < 3600:
                    continue
            except (ValueError, TypeError):
                pass
        post_id = str(row.get('platform_id', ''))
        source = row.get('source')
        if source in ('x', 'facebook', 'linkedin') and token and post_id:
            payload = json.dumps({'query': 'query CheckPost($input: PostInput!) { post(input: $input) { id status } }',
                                  'variables': {'input': {'id': post_id}}}).encode()
            request = Request('https://api.buffer.com', data=payload,
                              headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
            provider = 'buffer'
        elif source == 'bluesky' and post_id.startswith('at://'):
            from urllib.parse import urlencode
            request = Request('https://public.api.bsky.app/xrpc/app.bsky.feed.getPosts?' + urlencode({'uris': post_id}))
            provider = 'bluesky'
        else:
            continue
        row['last_check_attempt_at'] = now.isoformat()
        try:
            with urlopen(request, timeout=10) as response:
                result = json.load(response)
            if provider == 'buffer':
                post = (result.get('data') or {}).get('post')
                if result.get('errors') or not post or str(post.get('id')) != post_id or not post.get('status'):
                    raise ValueError('No verified status')
                row['status'] = str(post['status']).lower()
            else:
                if not any(p.get('uri') == post_id for p in result.get('posts', [])):
                    raise ValueError('Not visible in AppView')
                row['status'] = 'published'
            row['publication_checked_at'] = now.isoformat()
            row['publication_check_source'] = provider
            row['publication_check_result'] = 'verified'
        except Exception:
            # Do not turn an API outage, missing post or rate limit into publication.
            row['publication_check_result'] = 'unavailable'
        # Keep recorded_at: it identifies the original publication cohort.
        with SPOOL.open('a', encoding='utf-8') as spool:
            spool.write(json.dumps(row, ensure_ascii=False) + '\n')

