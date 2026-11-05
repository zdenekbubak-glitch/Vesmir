"""Notify IndexNow only after the matching Pages deployment is publicly available.

Standard library only. The cache contains the last fully accepted snapshot.
First run establishes a baseline without submitting old URLs.
"""
import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ENDPOINT = 'https://api.indexnow.org/indexnow'
MARKER = 'indexnow-deployment.json'


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')


def config(site):
    cfg = read_json(site / 'data/indexnow.json')
    base = cfg['base'].rstrip('/')
    parsed = urllib.parse.urlsplit(base)
    if parsed.scheme != 'https' or parsed.path or parsed.query or parsed.fragment or not parsed.netloc:
        raise ValueError('Invalid IndexNow base URL')
    key = cfg['key']
    if not re.fullmatch(r'[A-Za-z0-9-]{8,128}', key):
        raise ValueError('Invalid IndexNow key')
    if (site / (key + '.txt')).read_text(encoding='utf-8').strip() != key:
        raise ValueError('Key file does not match configuration')
    return base, key


def snapshot(site, base):
    result = {}
    root = site.resolve()
    for element in ET.parse(site / 'sitemap.xml').getroot():
        loc = element.find('{*}loc')
        if loc is None or not loc.text:
            continue
        url = loc.text.strip()
        part = urllib.parse.urlsplit(url)
        if part.scheme != 'https' or part.netloc != urllib.parse.urlsplit(base).netloc or part.query or part.fragment:
            raise ValueError('Unexpected URL in sitemap: ' + url)
        # IndexNow is for public web pages, not the RSS feed or image assets.
        if not (part.path.endswith('/') or part.path.endswith('.html') or not part.path):
            continue
        rel = urllib.parse.unquote(part.path).lstrip('/')
        if not rel or rel.endswith('/'):
            rel += 'index.html'
        file = (site / rel).resolve()
        if not file.is_relative_to(root) or not file.is_file():
            raise ValueError('Missing/unsafe sitemap page: ' + url)
        result[url] = hashlib.sha256(file.read_bytes()).hexdigest()
    if not result:
        raise ValueError('No HTML pages found in sitemap')
    return result


def make_plan(current, previous, base):
    if previous is None:
        return {'version': 1, 'base': base, 'baseline': True, 'pages': current, 'urls': []}
    if previous.get('version') != 1 or previous.get('base') != base or not isinstance(previous.get('pages'), dict):
        raise ValueError('Invalid cached IndexNow history; refusing to reset it silently')
    old = previous['pages']
    changed = [url for url, digest in current.items() if old.get(url) != digest]
    removed = set(old) - set(current)
    # Validate cached URLs before allowing removal notifications.
    for url in removed:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != 'https' or parsed.netloc != urllib.parse.urlsplit(base).netloc or parsed.query or parsed.fragment:
            raise ValueError('Unexpected URL in history')
    return {'version': 1, 'base': base, 'baseline': False, 'pages': current, 'urls': sorted(set(changed) | removed)}


def marker(plan):
    data = json.dumps(plan['pages'], sort_keys=True).encode()
    return {'version': 1, 'digest': hashlib.sha256(data).hexdigest()}


def fetch(url, payload=None):
    headers = {'User-Agent': 'Kosmonovinky-IndexNow/1.0', 'Cache-Control': 'no-cache'}
    if payload is not None:
        headers['Content-Type'] = 'application/json; charset=utf-8'
    request = urllib.request.Request(url, data=payload, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.status, response.read()


def wait_for_deployment(base, key, expected, getter=fetch, sleeper=time.sleep):
    for attempt in range(4):
        try:
            query = '?indexnow=' + expected['digest'] + '-' + str(attempt)
            _, body = getter(base + '/' + MARKER + query)
            _, key_body = getter(base + '/' + key + '.txt')
            if json.loads(body) == expected and key_body.decode('utf-8').strip() == key:
                return
        except (OSError, ValueError, UnicodeError):
            pass
        if attempt < 3:
            sleeper(8)
    raise RuntimeError('Deployed site/key not yet verified. No URLs submitted; history unchanged.')


def submit_plan(plan, base, key, sender=fetch):
    urls = plan['urls']
    for start in range(0, len(urls), 10000):
        batch = urls[start:start + 10000]
        payload = json.dumps({'host': urllib.parse.urlsplit(base).netloc,
                              'key': key, 'keyLocation': base + '/' + key + '.txt',
                              'urlList': batch}).encode('utf-8')
        status, _ = sender(ENDPOINT, payload)
        if status not in (200, 202):
            raise RuntimeError('IndexNow returned HTTP ' + str(status))
        print(f'IndexNow: {len(batch)} URL accepted (HTTP {status}). This is not confirmation of indexing.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'submit'])
    parser.add_argument('--site-dir', default='.')
    parser.add_argument('--state', required=True)
    parser.add_argument('--plan', required=True)
    args = parser.parse_args()
    site = Path(args.site_dir)
    base, key = config(site)
    if args.command == 'prepare':
        previous = read_json(args.state) if Path(args.state).exists() else None
        plan = make_plan(snapshot(site, base), previous, base)
        write_json(args.plan, plan)
        write_json(site / MARKER, marker(plan))
        print(f'IndexNow: {len(plan["pages"])} pages; {len(plan["urls"])} changes; baseline={plan["baseline"]}')
        return
    plan = read_json(args.plan)
    if plan['base'] != base or plan['version'] != 1:
        raise ValueError('Plan does not match configuration')
    wait_for_deployment(base, key, marker(plan))
    submit_plan(plan, base, key)
    # Only advance history after all batches were accepted (or baseline verified).
    write_json(args.state, {'version': 1, 'base': base, 'pages': plan['pages']})
    if plan['baseline']:
        print('IndexNow: baseline saved. Old URLs were not submitted. Future changes will be notified.')
    elif not plan['urls']:
        print('IndexNow: no changes; nothing submitted.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('::warning::IndexNow: ' + str(error).replace('\n', ' '), file=sys.stderr)
        sys.exit(1)
