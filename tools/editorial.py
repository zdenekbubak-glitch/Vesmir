"""Optional editor's column. Standard library only; no changes to news data."""
import hashlib
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from html import escape
from urllib.parse import urlsplit
from assign_article_images import candidates_for, thumbnail, figure, image_url, image_schema

START = '<!-- EDITORIAL:START -->'
END = '<!-- EDITORIAL:END -->'

def inline(text):
    # Escape first: HTML in Markdown is displayed as text, never executed.
    text = escape(text, quote=True)
    def link(m):
        url = m[2]
        if not url.startswith(('https://', 'http://', '/')) or url.startswith('//'):
            return m[1]
        return '<a href="' + url + '">' + m[1] + '</a>'
    text = re.sub(r'\[([^\]]+)\]\(([^\s)]+)\)', link, text)
    return re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)

def markdown(body):
    blocks = []
    sources_level = 0
    for block in re.split(r'\n\s*\n', body.strip()):
        lines = block.splitlines()
        if not lines: continue
        heading = re.fullmatch(r'(#{2,3})\s+(.+)', block)
        if heading:
            level = len(heading[1])
            if sources_level and level <= sources_level:
                blocks.append('</section>')
                sources_level = 0
            if heading[2].strip().casefold().startswith('zdroje'):
                blocks.append('<section class="article-sources">')
                sources_level = level
            blocks.append(f'<h{level}>{inline(heading[2])}</h{level}>')
        elif all(line.startswith('- ') for line in lines):
            blocks.append('<ul>' + ''.join('<li>' + inline(line[2:]) + '</li>' for line in lines) + '</ul>')
        elif all(line.startswith('> ') for line in lines):
            blocks.append('<blockquote>' + inline(' '.join(line[2:] for line in lines)) + '</blockquote>')
        else:
            blocks.append('<p>' + inline(' '.join(lines)) + '</p>')
    if sources_level:
        blocks.append('</section>')
    return '\n'.join(blocks)

LINK = re.compile(r'\[([^\]]+)\]\(([^\s)]+)\)')
RELATED_HEADINGS = {
    'pro pochopení souvislostí', 'související z kosmopedie',
    'odkazy na kosmopedii', 'odkazy na novinky', 'související novinky',
    'související články z kosmonovinek',
}


def related_kind(url):
    """Only exact detail links on this site belong in the related-link footer."""
    parsed = urlsplit(url)
    if parsed.scheme:
        if parsed.scheme not in ('http', 'https') or parsed.hostname not in ('kosmonovinky.cz', 'www.kosmonovinky.cz'):
            return None
    elif not url.startswith('/') or url.startswith('//'):
        return None
    match = re.fullmatch(r'/(clanky|kosmopedie)/[a-z0-9-]+\.html', parsed.path)
    return match[1] if match else None


def related_section(links, heading, css):
    if not links:
        return ''
    items = ''.join('<li>' + inline('[' + title + '](' + url + ')') + '</li>' for title, url in links)
    return ('<section class="related ' + css + '"><h2>' + heading + '</h2><ul>' + items + '</ul></section>')


def article_parts(body):
    """Preserve prose; render sources, news and Kosmopedie in one shared order."""
    links = {'clanky': [], 'kosmopedie': []}
    seen = {'clanky': set(), 'kosmopedie': set()}
    for match in LINK.finditer(body):
        kind = related_kind(match[2])
        if kind and urlsplit(match[2]).path not in seen[kind]:
            seen[kind].add(urlsplit(match[2]).path)
            links[kind].append((match[1], match[2]))

    pieces = re.split(r'(?m)^##[ \t]+([^\r\n]+)[ \t]*$', body)
    prose, sources = [pieces[0]], []
    for i in range(1, len(pieces), 2):
        heading, content = pieces[i].strip(), pieces[i + 1]
        lines = [line for line in content.splitlines() if line.strip()]
        is_link_list = bool(lines) and all(re.fullmatch(r'- \[[^\]]+\]\([^\s)]+\)', line.strip()) for line in lines)
        if heading.casefold().startswith('zdroje'):
            kept = []
            for line in content.splitlines():
                item = re.fullmatch(r'\s*- \[([^\]]+)\]\(([^\s)]+)\)\s*', line)
                # Local links move to the related footer; keep all external sources
                # and any explanatory prose in the bibliography.
                if item and related_kind(item[2]):
                    continue
                kept.append(line)
            if any(line.strip() for line in kept):
                sources.append('## ' + heading + '\n\n' + '\n'.join(kept).strip())
        elif heading.casefold() in RELATED_HEADINGS and is_link_list and all(related_kind(LINK.search(line)[2]) for line in lines):
            # A dedicated list is now represented once by the standard footer.
            continue
        else:
            prose.append('## ' + heading + '\n' + content)
    return {
        'body': markdown('\n\n'.join(prose)),
        'sources': '\n'.join(markdown(part) for part in sources),
        'related_news': related_section(links['clanky'], 'Související novinky', 'editorial-news'),
        'related_explainery': related_section(links['kosmopedie'], 'Související z Kosmopedie', 'kosmopedie-context'),
    }


def paging(previous, following):
    links = []
    for post, rel, label, css in ((previous, 'prev', '← Předchozí příspěvek', 'prev'),
                                  (following, 'next', 'Následující příspěvek →', 'next')):
        if post:
            links.append('<a class="' + css + '" rel="' + rel + '" href="' + escape(post['href'], quote=True) + '">'
                         '<span class="meta">' + label + '</span><span>' + escape(post['title']) + '</span></a>')
    return ('<nav class="post-nav editorial-paging" aria-label="Procházení příspěvků Pohledem editora">'
            + ''.join(links) + '</nav>') if links else ''


def load_posts(site, library):
    posts = []
    today = datetime.now(ZoneInfo('Europe/Prague')).date()
    for path in sorted((site / 'content/editorial').glob('*.md')):
        if path.name.startswith(('_', '.')): continue
        raw = path.read_text(encoding='utf-8-sig')
        match = re.fullmatch(r'---\s*\n(.*?)\n---\s*\n(.*)', raw, re.S)
        if not match: raise ValueError(f'{path}: chybí hlavička mezi ---')
        meta = {}
        for line in match[1].splitlines():
            if not line.strip() or line.lstrip().startswith('#'): continue
            key, sep, value = line.partition(':')
            if not sep: raise ValueError(f'{path}: neplatný řádek hlavičky')
            meta[key.strip()] = value.strip().strip('"').strip("'")
        if meta.get('published', 'false').lower() != 'true': continue
        for key in ('title', 'date', 'perex'):
            if not meta.get(key): raise ValueError(f'{path}: vyplňte {key}')
        published = date.fromisoformat(meta['date'])
        if published > today: continue
        slug = path.stem
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
            raise ValueError(f'{path}: název souboru smí obsahovat malá písmena bez diakritiky, číslice a spojovníky')
        if not match[2].strip(): raise ValueError(f'{path}: chybí text')
        meta.update(article_parts(match[2]))
        meta.update(slug=slug, author='Zdeněk Bubák',
                    href='/pohledem-editora/' + slug + '.html', published=meta['date'])
        catalog = library[1]
        requested = meta.get('image', 'auto')
        if requested and requested != 'auto':
            if requested not in catalog: raise ValueError(f'{path}: neznámý obrázek {requested}')
            entry = catalog[requested]
        else:
            candidates = sorted(candidates_for(meta, list(catalog.values())), key=lambda e:e['id'])
            entry = candidates[int(hashlib.sha256(slug.encode()).hexdigest(),16) % len(candidates)] if candidates else None
        meta['image_entry'] = entry
        posts.append(meta)
    return sorted(posts, key=lambda p:(p['date'],p['slug']), reverse=True)

def card(post, fmt_date, home=False):
    href = post['href']; title = escape(post['title']); perex = escape(post['perex'])
    label = '<a href="/pohledem-editora/">Pohledem editora</a>'
    return (f'<article class="item editorial-card"><p class="meta">{label} · Zdeněk Bubák · {fmt_date(post["date"])}</p>'
            f'<h2><a href="{href}">{title}</a></h2><div class="article-teaser">'
            + thumbnail(post['image_entry'],href) + f'<p class="summary">{perex}</p></div>'
            f'<a href="{href}">Přečíst komentář →</a></article>')

def build(site, out, base, library, page_head, foot, fmt_date, article_footer="", description_formatter=None, feedback_renderer=None):
    posts = load_posts(site, library)
    folder = out / 'pohledem-editora'; folder.mkdir(exist_ok=True)
    # This directory is owned by this generator; remove withdrawn comments too.
    for old in folder.glob('*.html'): old.unlink()
    urls = []
    for index, post in enumerate(posts):
        previous = posts[index + 1] if index + 1 < len(posts) else None
        following = posts[index - 1] if index > 0 else None
        url = base + post['href']; entry = post['image_entry']
        description = description_formatter(post['perex']) if description_formatter else post['perex']
        schema = {'@type':'Article','headline':post['title'],'description':description,
                  'datePublished':post['date'],'inLanguage':'cs','mainEntityOfPage':url,
                  'author':{'@type':'Person','name':'Zdeněk Bubák'},'image':image_schema(entry,base)}
        page = page_head(post['title']+' – Pohledem editora – Kosmologické novinky',description,url,image_url(entry,base),schema)
        page += ('<p class="breadcrumbs"><a href="/">Hlavní stránka</a> › <a href="/pohledem-editora/">Pohledem editora</a></p>'
                 '<article class="post"><p class="theme-badge">Pohledem editora</p>'
                 f'<h1>{escape(post["title"])}</h1><p class="meta">Zdeněk Bubák · {fmt_date(post["date"])}</p>'
                 f'<p class="summary"><strong>{escape(post["perex"])}</strong></p>'+figure(entry)+post['body']+
                 post['sources']+post['related_news']+post['related_explainery']+article_footer+
                 (feedback_renderer(post['title'], url) if feedback_renderer else '')+paging(previous, following)+
                 '</article><p class="back"><a href="/pohledem-editora/">← Všechny komentáře</a> · <a href="/clanky/">Přehled článků</a></p>'+foot)
        (folder/(post['slug']+'.html')).write_text(page,encoding='utf-8')
        urls.append((url,post['date']))
    page = page_head('Pohledem editora – Kosmologické novinky','Osobní komentáře Zdeňka Bubáka k novinkám z kosmologie.',base+'/pohledem-editora/')
    page += ('<p class="breadcrumbs"><a href="/">Hlavní stránka</a> › Pohledem editora</p><h1>Pohledem editora</h1>'
             '<p>Osobní ohlédnutí Zdeňka Bubáka za děním v kosmologii. Co mě zaujalo, nad čím přemýšlím a co stojí za pozornost.</p>')
    page += ''.join(card(p,fmt_date) for p in posts) if posts else '<p>První komentář se zde objeví po zveřejnění.</p>'
    (folder/'index.html').write_text(page+foot,encoding='utf-8')
    if posts: urls.append((base+'/pohledem-editora/',posts[0]['date']))
    source = site/'index.html'
    if source.exists():
        homepage = source.read_text(encoding='utf-8')
        if START not in homepage or END not in homepage:
            raise ValueError('index.html: chybí značky EDITORIAL pro upoutávku')
        teaser = card(posts[0],fmt_date,True) if posts else ''
        homepage = re.sub(re.escape(START)+'.*?'+re.escape(END),lambda m:START+'\n'+teaser+'\n'+END,homepage,flags=re.S)
        (out/'index.html').write_text(homepage,encoding='utf-8')
    return posts, urls
