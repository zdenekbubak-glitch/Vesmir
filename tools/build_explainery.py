#!/usr/bin/env python3
# Generátor Kosmopedie – evergreen vysvětlovaček pro kosmonovinky.cz
# Čte data/explainery.json (a data/news.json pro prolinkování), vygeneruje:
#   - kosmopedie/<slug>.html      … jedna stránka každého explaineru
#   - kosmopedie/index.html       … přehled všech explainerů (seskupený podle rubriky)
#   - doplní URL do sitemap.xml
#
# Spouští se ZA build_static.py (ten už vygeneruje sitemap.xml, který tento
# script jen rozšíří). Využívá funkce z build_static.py — proto běží z kořene
# repozitáře a hledá build_static.py jak v rootu, tak v tools/:
#
#   python3 tools/build_explainery.py --site-dir . --out . --base https://kosmonovinky.cz
import argparse
import json
import re
import sys
from pathlib import Path
from assign_article_images import prepare as prepare_images, lookup as lookup_image, figure as image_figure, image_schema, image_url, thumbnail

_here = Path(__file__).resolve().parent
# Always prefer the shared template beside this generator (tools/build_static.py).
# A legacy copy in the repository root must not override the current template.
for _p in (_here.parent, _here):
    if str(_p) in sys.path:
        sys.path.remove(str(_p))
    sys.path.insert(0, str(_p))
from build_static import (FALLBACK_THEME, THEME_LABEL, esc, fmt_date, fmt_iso_date,
                          page_head, FOOT, slugify, classify, explainer_catalog, NEWSLETTER_CTA)

WHY_CSS = '''
    .why-box { background: #1a2438; border-left: 3px solid var(--accent); border-radius: 8px; padding: .9rem 1.1rem; margin: 1.3rem 0; }
    .why-box h2 { margin-top: 0; }
    .why-box p { margin: 0; }
    .explainer-perex { font-size: 1.06rem; color: #c9d6ec; }
'''


def render_body(text):
    # Jednoduchý konvertor: odstavce oddělené prázdným řádkem,
    # řádky začínající '- ' nebo 'N. ' (1. 2. 3.) se sloučí do <ul>.
    out, ul = [], []

    def md(text):
        return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', esc(text))

    def flush():
        if ul:
            out.append('<ul>' + ''.join(ul) + '</ul>')
            ul.clear()

    for raw in str(text).strip().split('\n'):
        line = raw.rstrip()
        m = re.match(r'^(-|\d+\.)\s+(.*)$', line)
        if m:
            ul.append(f'<li>{md(m.group(2))}</li>')
            continue
        if not line.strip():
            flush()
            continue
        flush()
        out.append(f'<p>{md(line.strip())}</p>')
    flush()
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site-dir', default='.')
    ap.add_argument('--out', default='_site')
    ap.add_argument('--base', default='https://kosmonovinky.cz')
    args = ap.parse_args()
    base = args.base.rstrip('/')
    site = Path(args.site_dir)
    out = Path(args.out)

    expl_path = site / 'data' / 'explainery.json'
    if not expl_path.exists():
        print('explainery.json nenalezen - přeskakuji.')
        return
    explainery = explainer_catalog(site)
    image_library = prepare_images(site, download=False)

    # novinky pro sekci Související novinky (stejná logika rubrik jako build_static)
    news = json.loads((site / 'data' / 'news.json').read_text(encoding='utf-8'))
    news.sort(key=lambda x: x.get('inserted_at') or '', reverse=True)
    for item in news:
        item['_theme'] = classify(item)
    by_theme = {}
    for item in news:
        by_theme.setdefault(item['_theme'], []).append(item)

    slugs = {ex['_slug'] for ex in explainery}
    (out / 'kosmopedie').mkdir(parents=True, exist_ok=True)
    urls = []

    for ex in explainery:
        theme = ex.get('theme') or FALLBACK_THEME[0]
        theme_label = THEME_LABEL.get(theme, FALLBACK_THEME[1])
        url = f"{base}/kosmopedie/{ex['_slug']}.html"
        description = ex.get('description') or ex.get('perex', '')[:158]

        sec_html = ''
        for sec in ex.get('sections', []):
            sec_html += f"      <h2>{esc(sec.get('heading'))}</h2>\n{render_body(sec.get('body'))}\n"

        why_html = ''
        if ex.get('why_box'):
            why_html = ('      <div class="why-box">\n'
                        '        <h2>Proč je to zajímavé právě pro vás?</h2>\n'
                        + render_body(ex['why_box']) +
                        '\n      </div>\n')

        related_news = by_theme.get(theme, [])[:3]
        rel_html = ''
        if related_news:
            rows = []
            for r in related_news:
                rslug = slugify(r.get('title', 'clanek')) + '-' + (re.sub(r'[^0-9]', '', str(r.get('id')))[:12] or '0')
                rows.append(f'          <li><a href="/clanky/{rslug}.html">{esc(r.get("title"))}</a> '
                            f'<span class="meta">({fmt_date(r.get("published"))})</span></li>')
            rel_html = ('    <section class="related">\n'
                        '      <h2>Související novinky</h2>\n'
                        '      <ul>\n' + '\n'.join(rows) +
                        '\n      </ul>\n    </section>\n')

        rel_ex = [r for r in ex.get('related_explainery', []) if r in slugs]
        rel_ex_html = ''
        if rel_ex:
            items = []
            for r in rel_ex:
                title = next(e['title'] for e in explainery if e['_slug'] == r)
                items.append(f'          <li><a href="/kosmopedie/{r}.html">{esc(title)}</a></li>')
            rel_ex_html = ('    <section class="related">\n'
                           '      <h2>Související z Kosmopedie</h2>\n'
                           '      <ul>\n' + '\n'.join(items) +
                           '\n      </ul>\n    </section>\n')

        article_image = lookup_image(ex, "explainery", image_library)
        article_image_url = image_url(article_image, base)
        jsonld = {
            '@context': 'https://schema.org',
            '@type': 'Article',
            'headline': ex['title'],
            'description': description,
            'datePublished': ex.get('published'),
            'dateModified': ex.get('updated') or ex.get('published'),
            'inLanguage': 'cs',
            'author': {'@type': 'Organization', 'name': 'Kosmologické novinky'},
            'publisher': {'@type': 'Organization', 'name': 'Kosmologické novinky'},
            'mainEntityOfPage': url,
            'image': image_schema(article_image, base),
        }
        page = page_head(f"{ex['title']} - Kosmopedie - Kosmologické novinky", description, url,
                         og_image=article_image_url, jsonld=jsonld)
        page = page.replace('</style>', WHY_CSS + '</style>')
        page += (f"    <p class=\"breadcrumbs\"><a href=\"/\">Hlavní stránka</a> › <a href=\"/kosmopedie/\">Kosmopedie</a> › {esc(ex['title'])}</p>\n"
                 f"    <article class=\"post\">\n"
                 f"      <div class=\"theme-badge\"><a href=\"/temata/{theme}.html\">{esc(theme_label)}</a></div>\n"
                 f"      <h1>{esc(ex['title'])}</h1>\n"
                 f"      <p class=\"meta\">Kosmopedie · Aktualizováno: {fmt_date(ex.get('updated') or ex.get('published'))}</p>\n"
                 f"      <p class=\"explainer-perex\">{esc(ex.get('perex'))}</p>\n"
                 + image_figure(article_image) + sec_html + why_html + rel_html + rel_ex_html + NEWSLETTER_CTA +
                 '    </article>\n'
                 '    <p class=\"back\"><a href=\"/kosmopedie/\">← Celá Kosmopedie</a> · <a href=\"/temata/\">Rubriky</a></p>\n')
        page += FOOT
        (out / 'kosmopedie' / f"{ex['_slug']}.html").write_text(page, encoding='utf-8')
        urls.append((url, fmt_iso_date(ex.get('updated') or ex.get('published'))))
        print(f"  kosmopedie/{ex['_slug']}.html")

    # přehled všech explainerů
    groups = {}
    for ex in explainery:
        groups.setdefault(ex.get('theme') or FALLBACK_THEME[0], []).append(ex)
    list_html = ''
    for theme in sorted(groups, key=lambda t: THEME_LABEL.get(t, FALLBACK_THEME[1])):
        label = THEME_LABEL.get(theme, FALLBACK_THEME[1])
        list_html += f'    <h2 class=\"section-title\">{esc(label)}</h2>\n'
        for ex in groups[theme]:
            list_html += (f"    <article class=\"item\"><h2><a href=\"/kosmopedie/{ex['_slug']}.html\">{esc(ex['title'])}</a></h2>"
                          f"<p class=\"meta\">Aktualizováno: {fmt_date(ex.get('updated') or ex.get('published'))} · "
                          f"<a href=\"/temata/{theme}.html\">{esc(label)}</a></p>"
                          f"<div class=\"article-teaser\">"
                          + thumbnail(lookup_image(ex,'explainery',image_library),'/kosmopedie/'+ex['_slug']+'.html')
                          + f"<p class=\"summary\">{esc(ex.get('perex'))}</p></div></article>\n")
    idx = page_head('Kosmopedie - slovník pojmů kosmologie - Kosmologické novinky',
                    'Kosmopedie: vysvětlení pojmů kosmologie v češtině. Temná hmota, černé díry, gravitační vlny, reliktní záření, neutronové hvězdy a další - jednoduše a trvale.',
                    f'{base}/kosmopedie/')
    idx += (f"    <p class=\"breadcrumbs\"><a href=\"/\">Hlavní stránka</a> › Kosmopedie</p>\n"
            f"    <h1 class=\"section-title\" style=\"font-size:1.4rem;color:var(--text)\">Kosmopedie <span class=\"meta\">({len(explainery)} významů)</span></h1>\n"
            '    <p class=\"summary\">Vysvětlení základních pojmů kosmologie. Každý význam doplňuje rubriku novinek na stejné téma. Kliknutím na název hesla nebo obrázek otevřete celé vysvětlení.</p>\n'
            + list_html)
    idx += FOOT
    (out / 'kosmopedie' / 'index.html').write_text(idx, encoding='utf-8')
    latest = max(ex.get('updated') or ex.get('published') or '2026-01-01' for ex in explainery)
    urls.append((f'{base}/kosmopedie/', fmt_iso_date(latest)))

    # doplnění sitemap.xml
    sm_path = out / 'sitemap.xml'
    if sm_path.exists():
        sm = sm_path.read_text(encoding='utf-8')
        add = ''.join(f'  <url><loc>{esc(loc)}</loc><lastmod>{lm}</lastmod></url>\n' for loc, lm in urls)
        sm = sm.replace('</urlset>', add + '</urlset>')
        sm_path.write_text(sm, encoding='utf-8')

    print(f'OK: {len(explainery)} explainerů, {len(urls)} URL přidáno do sitemap')


if __name__ == '__main__':
    main()







