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

def receipt(source, kind, key, title, platform_id, status, target='https://kosmonovinky.cz/'):
    # Buffer acceptance is not proof of publication. Keep its returned status.
    record = dict(source=source, kind=kind, key=key, title=str(title)[:300], platform_id=str(platform_id), status=str(status or 'submitted').lower(), target=target,
                  recorded_at=datetime.now(timezone.utc).isoformat())
    with SPOOL.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
