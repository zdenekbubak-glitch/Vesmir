#!/usr/bin/env python3
"""Merge quote state onto current remote main, preserving all other remote files.
An isolated Git index builds a commit whose sole change is the state file.
Retry a concurrent push without ever rerunning publication or forcing a push.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

STATE = 'state/quote_x_used.json'


def normalize(value):
    if isinstance(value, list):
        return {'version': 2, 'used': value, 'reviewed': {}}
    if not isinstance(value, dict) or not isinstance(value.get('used'), list) or not isinstance(value.get('reviewed'), dict):
        raise ValueError('Invalid quote state; refusing to discard data')
    return value


def merge_states(remote, local):
    remote, local = normalize(remote), normalize(local)
    result = dict(remote)
    result.update(version=2, used=sorted(set(remote['used']) | set(local['used'])))
    reviewed = dict(remote['reviewed'])
    for key, record in local['reviewed'].items():
        previous = reviewed.get(key, {})
        # A confirmed Buffer ID must never be overwritten by a mere evaluation.
        if previous.get('buffer_id') and not record.get('buffer_id'):
            continue
        if record.get('buffer_id') and not previous.get('buffer_id'):
            reviewed[key] = record
        elif record.get('at', '') >= previous.get('at', ''):
            reviewed[key] = record
    result['reviewed'] = reviewed
    return result


def git(*args, data=None, env=None, check=True):
    return subprocess.run(['git', *args], input=data, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=env, check=check)


def main():
    path = Path(STATE)
    if not path.exists():
        print('No quote state to save.')
        return
    local = normalize(json.loads(path.read_text(encoding='utf-8')))
    git('config', 'user.name', 'github-actions[bot]')
    git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    for attempt in range(1, 6):
        git('fetch', '--no-tags', 'origin', '+refs/heads/main:refs/remotes/origin/main')
        head = git('rev-parse', 'refs/remotes/origin/main').stdout.strip()
        exists = git('cat-file', '-e', f'{head}:{STATE}', check=False)
        remote = json.loads(git('show', f'{head}:{STATE}').stdout) if exists.returncode == 0 else []
        merged = merge_states(remote, local)
        content = json.dumps(merged, ensure_ascii=False, indent=2) + '\n'
        blob = git('hash-object', '-w', '--stdin', data=content).stdout.strip()
        with tempfile.TemporaryDirectory(prefix='quote-state-') as temporary:
            env = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / 'index'))
            git('read-tree', head, env=env)
            git('update-index', '--add', '--cacheinfo', f'100644,{blob},{STATE}', env=env)
            tree = git('write-tree', env=env).stdout.strip()
        if tree == git('rev-parse', f'{head}^{{tree}}').stdout.strip():
            print('Quote state already saved.')
            return
        commit = git('commit-tree', tree, '-p', head,
                     data='Quote X: aktualizace stavu použitých příspěvků\n').stdout.strip()
        pushed = git('push', 'origin', f'{commit}:refs/heads/main', check=False)
        if pushed.returncode == 0:
            print(f'Quote state saved, attempt {attempt}, commit {commit[:12]}.')
            return
        # Retry only an actual branch race; authentication errors must be visible.
        latest = git('ls-remote', 'origin', 'refs/heads/main').stdout.split()
        if not latest or latest[0] == head:
            raise RuntimeError('Cannot push quote state: ' + pushed.stderr)
        print(f'Remote main changed during push; merging again ({attempt}/5).')
        time.sleep(1)
    raise RuntimeError('Cannot save state after 5 concurrent updates; do not rerun publication blindly.')


if __name__ == '__main__':
    main()
