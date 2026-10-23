"""Merge only social publication receipts into latest main, retrying concurrent pushes."""
from pathlib import Path
import json
import subprocess
import tempfile
from social_tracking import SPOOL

def git(*args, cwd=None):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

def main():
    if not SPOOL.exists():
        print('Žádná nová potvrzení ze sítí.'); return
    incoming = [json.loads(line) for line in SPOOL.read_text().splitlines() if line.strip()]
    root = Path(git('rev-parse', '--show-toplevel'))
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / 'receipts'
        git('fetch', 'origin', 'main')
        git('worktree', 'add', '--detach', str(work), 'origin/main')
        try:
            for attempt in range(4):
                if attempt:
                    git('fetch', 'origin', 'main'); git('reset', '--hard', 'origin/main', cwd=work)
                path = work / 'data/social_posts.json'
                previous = json.loads(path.read_text()) if path.exists() else []
                merged = {r['key']: r for r in previous}
                for row in incoming:
                    old = merged.get(row['key'])
                    if not old or old['status'] not in ('published', 'sent', 'posted'):
                        merged[row['key']] = row
                path.parent.mkdir(exist_ok=True)
                path.write_text(json.dumps(sorted(merged.values(), key=lambda r:r['recorded_at']), ensure_ascii=False, indent=2)+'\n')
                git('add', 'data/social_posts.json', cwd=work)
                if not git('diff', '--cached', '--name-only', cwd=work): break
                git('-c', 'user.name=cosmo-agent', '-c', 'user.email=agent@users.noreply.github.com', 'commit', '-m', 'Záznam výsledků odeslání na sociální sítě', cwd=work)
                try: git('push', 'origin', 'HEAD:main', cwd=work); break
                except subprocess.CalledProcessError:
                    if attempt==3: raise RuntimeError('Potvrzení se nepodařilo uložit; zkontrolujte běh workflow.') from None
        finally: git('worktree', 'remove', '--force', str(work))
    print('Potvrzení ze sítí uložena; koncepty nejsou vydané příspěvky.')
if __name__ == '__main__': main()
