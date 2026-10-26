#!/usr/bin/env python3
# Generátor Kosmopedie – evergreen vysvětlovaček pro kosmonovinky.cz
# Čte data/explainery.json (a data/news.json pro prolinkování), vygeneruje:
#   - kosmopedie/<slug>.html      … jedna stránka každého explaineru
#   - kosmopedie/index.html       … přehled všech explainerů (seskupený podle rubriky)
#   - data/kosmopedie-search.json … vlastní výklad, bez kreditů a bibliografie
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
from html.parser import HTMLParser
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
                          page_head, FOOT, slugify, classify, explainer_catalog, NEWSLETTER_CTA, collection_switch)

# Kosmopedie may introduce a subject before it has its own news category.
KOSMOPEDIE_THEMES = {
    'kvantovy-svet': 'Kvantový svět',
    'svetlo-a-mereni-vesmiru': 'Světlo a měření vesmíru',
    'rozpinani-a-modely-vesmiru': 'Rozpínání a modely vesmíru',
    'castice-a-zakladni-sily': 'Částice a základní síly',
}
THEME_LABEL = {**THEME_LABEL, **KOSMOPEDIE_THEMES}

GROUP_DESCRIPTIONS = {
    'cerne-diry': 'Vznik černých děr, horizont událostí a jejich neobvyklé vlastnosti.',
    'temna-dira-v-centru': 'Obří černé díry v srdcích galaxií a jejich okolí.',
    'temna-hmota': 'Důkazy neviditelné hmoty a hledání jejího složení.',
    'temna-energie': 'Co stojí za zrychleným rozpínáním vesmíru?',
    'gravitacni-vlny': 'Vlnění prostoročasu, jeho měření a objevy.',
    'exoplanety': 'Planety u jiných hvězd a způsoby jejich hledání.',
    'galaxie': 'Jak galaxie vznikají, vyvíjejí se a vzájemně ovlivňují.',
    'vesmirne-teleskopy': 'Dalekohledy na Zemi i v kosmu a jejich možnosti.',
    'relictni-zareni': 'Nejstarší pozorovatelné světlo a jeho zpráva o vesmíru.',
    'neutronove-hvezdy': 'Husté pozůstatky hvězd, pulsary a magnetary.',
    'velky-tresk': 'Horký počátek vesmíru a jeho další vývoj.',
    'kvantovy-svet': 'Kvantová pravidla, částice, pole a měření.',
    'svetlo-a-mereni-vesmiru': 'Spektra, chemické složení a rudý posuv.',
    'rozpinani-a-modely-vesmiru': 'Rozpínání, model ΛCDM a jeho alternativy.',
    'castice-a-zakladni-sily': 'Stavební prvky hmoty, interakce a urychlovače.',
}


def topic_count(n):
    return f'{n} téma' if n == 1 else f'{n} témata' if n < 5 else f'{n} témat'



def theme_href(theme):
    if theme in KOSMOPEDIE_THEMES:
        return '/kosmopedie/#' + theme
    return '/temata/' + theme + '.html'

WHY_CSS = '''
    .why-box { background: #1a2438; border-left: 3px solid var(--accent); border-radius: 8px; padding: .9rem 1.1rem; margin: 1.3rem 0; }
    .why-box h2 { margin-top: 0; }
    .why-box p { margin: 0; }
    .explainer-perex { font-size: 1.06rem; color: #c9d6ec; }
    .section-image-link { display: block; cursor: zoom-in; }
    .explainer-group[hidden] { display: none; }
    .post mark { background: #f6d365; color: #141a26; border-radius: 2px; padding: 0 .06em; }
    .topic-paging { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; border-top: 1px solid #1e293b; padding-top: 1rem; margin-top: 1.2rem; }
    .topic-paging a { min-width: 0; text-decoration: none; overflow-wrap: anywhere; }
    .topic-paging a:hover, .topic-paging a:focus-visible { text-decoration: underline; }
    .topic-paging .meta { display: block; font-size: .85rem; margin-bottom: .2rem; }
    .topic-next { grid-column: 2; text-align: right; }
    @media (max-width: 640px) {
      .topic-paging { grid-template-columns: minmax(0, 1fr); gap: .85rem; }
      .topic-next { grid-column: auto; text-align: left; }
    }
'''


def render_body(text):
    # Jednoduchý konvertor: odstavce oddělené prázdným řádkem,
    # řádky začínající '- ' nebo 'N. ' (1. 2. 3.) se sloučí do <ul>.
    out, ul = [], []

    def md(text):
        text = esc(text)
        text = re.sub(r'\[([^\[\]]+)\]\((https://[^\s<>]+)\)',
                      r'<a href="\2">\1</a>', text)
        return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

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


class SearchBlocks(HTMLParser):
    """Keep words in links/bold, but not their URLs or markup. One paragraph per unit."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag in ('p', 'li'):
            self.current = []

    def handle_data(self, value):
        if self.current is not None:
            self.current.append(value)

    def handle_endtag(self, tag):
        if tag in ('p', 'li') and self.current is not None:
            value = ' '.join(''.join(self.current).split())
            if value:
                self.blocks.append(value)
            self.current = None


def is_sources(section):
    return str(section.get('heading') or '').strip().casefold().startswith('zdroje')


def searchable_body(value):
    return re.sub(r'<(p|li)>', r'<\1 data-search-block>', render_body(value))


def search_record(entry):
    blocks = []
    for section in entry.get('sections', []):
        if is_sources(section):
            continue
        if section.get('heading'):
            blocks.append(section['heading'])
        parser = SearchBlocks()
        parser.feed(render_body(section.get('body')))
        blocks.extend(parser.blocks)
    parser = SearchBlocks()
    parser.feed(render_body(entry.get('why_box', '')))
    blocks.extend(parser.blocks)
    return {'href': '/kosmopedie/' + entry['_slug'] + '.html', 'blocks': blocks}


def paging(previous, following):
    links = []
    for entry, rel, label, css in ((previous, 'prev', '← Předchozí téma', 'topic-prev'),
                                  (following, 'next', 'Následující téma →', 'topic-next')):
        if entry:
            links.append(f'<a class="{css}" rel="{rel}" data-topic-neighbour '
                         f'href="/kosmopedie/{esc(entry["_slug"])}.html">'
                         f'<span class="meta">{label}</span><span>{esc(entry["title"])}</span></a>')
    return ('<nav class="topic-paging" aria-label="Procházení témat Kosmopedie">' +
            ''.join(links) + '</nav>\n') if links else ''


def section_image_figure(entry):
    """The original-size asset stays accessible when a teaching chart is small on mobile."""
    href = esc(image_url(entry))
    attrs = f'href="{href}" target="_blank" rel="noopener"'
    link = f'<a class="section-image-link" {attrs} aria-label="Zvětšit obrázek: {esc(entry["title"])}">'
    figure = image_figure(entry).replace('<img ', link + '<img loading="lazy" decoding="async" ', 1)
    figure = figure.replace('<figcaption', '</a><figcaption', 1)
    return re.sub(r'(<figcaption\b[^>]*>)',
                  lambda m: m.group(1) + f'<a {attrs}>Zvětšit obrázek</a><br>', figure, count=1)


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
    groups = {}
    for ex in explainery:
        groups.setdefault(ex.get('theme') or FALLBACK_THEME[0], []).append(ex)
    group_order = sorted(groups, key=lambda t: THEME_LABEL.get(t, FALLBACK_THEME[1]))
    ordered = [ex for theme in group_order for ex in groups[theme]]
    neighbours = {ex['_slug']: (ordered[i-1] if i else None,
                               ordered[i+1] if i+1 < len(ordered) else None)
                  for i, ex in enumerate(ordered)}
    (out / 'data').mkdir(parents=True, exist_ok=True)
    (out / 'data' / 'kosmopedie-search.json').write_text(
        json.dumps([search_record(ex) for ex in ordered], ensure_ascii=False, separators=(',', ':')),
        encoding='utf-8')

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
        section_images = []
        for sec in ex.get('sections', []):
            sources = is_sources(sec)
            attribute = '' if sources else ' data-search-block'
            section = f"      <h2{attribute}>{esc(sec.get('heading'))}</h2>\n"
            section += (render_body(sec.get('body')) if sources else searchable_body(sec.get('body'))) + '\n'
            # Editorial placement: an optional catalog ID belongs to this exact
            # section, independently of automatic selection of the lead image.
            if sec.get('image_id'):
                section_image = image_library[1].get(sec['image_id'])
                if section_image is None:
                    raise ValueError(f"{ex['id']}: nedostupný obrázek oddílu {sec['image_id']}")
                section += section_image_figure(section_image)
                section_images.append(section_image)
            if sources:
                section = '<section class="article-sources">\n' + section + '</section>\n'
            sec_html += section

        why_html = ''
        if ex.get('why_box'):
            why_html = ('      <div class="why-box">\n'
                        '        <h2>Proč je to zajímavé právě pro vás?</h2>\n'
                        + searchable_body(ex['why_box']) +
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
        article_images = [article_image] if article_image else []
        for section_image in section_images:
            if not any(image['id'] == section_image['id'] for image in article_images):
                article_images.append(section_image)
        image_metadata = [image_schema(image, base) for image in article_images]
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
            'image': image_metadata if section_images else image_schema(article_image, base),
        }
        page = page_head(f"{ex['title']} - Kosmopedie - Kosmologické novinky", description, url,
                         og_image=article_image_url, jsonld=jsonld)
        page = page.replace('</style>', WHY_CSS + '</style>')
        page += (f"    <p class=\"breadcrumbs\"><a href=\"/\">Hlavní stránka</a> › <a data-search-back href=\"/kosmopedie/\">Kosmopedie</a> › {esc(ex['title'])}</p>\n"
                 f"    <article class=\"post\">\n"
                 f"      <div class=\"theme-badge\"><a href=\"{theme_href(theme)}\">{esc(theme_label)}</a></div>\n"
                 f"      <h1 data-search-block>{esc(ex['title'])}</h1>\n"
                 f"      <p class=\"meta\">Kosmopedie · Aktualizováno: {fmt_date(ex.get('updated') or ex.get('published'))}</p>\n"
                 f"      <p class=\"explainer-perex\" data-search-block>{esc(ex.get('perex'))}</p>\n"
                 '      <p id="kosmopedie-detail-search-status" class="search-status" role="status" hidden></p>\n'
                 + image_figure(article_image) + sec_html + why_html + rel_html + rel_ex_html + NEWSLETTER_CTA +
                 paging(*neighbours[ex['_slug']]) +
                 '    </article>\n'
                 '    <p class=\"back\"><a data-search-back href=\"/kosmopedie/\">← Celá Kosmopedie</a> · <a href=\"/temata/\">Rubriky</a></p>\n'
                 '    <script defer src="/assets/kosmopedie-search.js?v=2"></script>\n')
        page += FOOT
        (out / 'kosmopedie' / f"{ex['_slug']}.html").write_text(page, encoding='utf-8')
        urls.append((url, fmt_iso_date(ex.get('updated') or ex.get('published'))))
        print(f"  kosmopedie/{ex['_slug']}.html")

    # přehled všech explainerů
    list_html = ''
    group_cards = ''
    for theme in group_order:
        label = THEME_LABEL.get(theme, FALLBACK_THEME[1])
        description = GROUP_DESCRIPTIONS.get(theme, 'Srozumitelná vysvětlení a souvislosti z této oblasti.')
        group_cards += (f'<a class="topic-card" href="#{esc(theme)}" data-topic-group="{esc(theme)}">'
                        f'<h3>{esc(label)}</h3><p class="summary">{esc(description)}</p>'
                        f'<p class="count">{topic_count(len(groups[theme]))}</p></a>\n')
        list_html += f'    <section class="explainer-group" data-topic-group-section="{esc(theme)}" aria-labelledby="{esc(theme)}">\n'
        list_html += f'    <h2 class=\"section-title\" id=\"{esc(theme)}\">{esc(label)}</h2>\n'
        for ex in groups[theme]:
            list_html += (f"    <article class=\"item\"><h2><a href=\"/kosmopedie/{ex['_slug']}.html\">{esc(ex['title'])}</a></h2>"
                          f"<p class=\"meta\">Aktualizováno: {fmt_date(ex.get('updated') or ex.get('published'))} · "
                          f"<a href=\"#{esc(theme)}\" data-topic-group=\"{esc(theme)}\">{esc(label)}</a></p>"
                          f"<div class=\"article-teaser\">"
                          + thumbnail(lookup_image(ex,'explainery',image_library),'/kosmopedie/'+ex['_slug']+'.html')
                          + f"<p class=\"summary\">{esc(ex.get('perex'))}</p></div></article>\n")
        list_html += '    </section>\n'
    idx = page_head('Kosmopedie - slovník pojmů kosmologie - Kosmologické novinky',
                    'Kosmopedie: vysvětlení pojmů kosmologie v češtině. Temná hmota, černé díry, gravitační vlny, reliktní záření, neutronové hvězdy a další - jednoduše a trvale.',
                    f'{base}/kosmopedie/')
    idx = idx.replace('</style>', WHY_CSS + '</style>')
    idx += (f"    <p class=\"breadcrumbs\"><a href=\"/\">Hlavní stránka</a> › Kosmopedie</p>\n"
            f"    <h1 class=\"section-title\" style=\"font-size:1.4rem;color:var(--text)\">Kosmopedie <span class=\"meta\">({len(explainery)} témat)</span></h1>\n"
            '    <p class=\"summary\">Vyberte si okruh nebo procházejte všechna témata. Hledání prochází názvy, perexy i celé texty napříč Kosmopedií.</p>\n'
            + collection_switch('kosmopedie', 'groups') +
            '    <input type="search" id="kosmopedie-search" class="search-box" placeholder="Hledat v Kosmopedii…" aria-label="Hledat v Kosmopedii" maxlength="200" aria-controls="kosmopedie-topics">\n'
            '    <p id="kosmopedie-search-status" class="search-status" role="status" aria-live="polite"></p>\n'
            '<section id="kosmopedie-groups" aria-labelledby="kosmopedie-groups-heading"><h2 class="collection-heading" id="kosmopedie-groups-heading">Okruhy Kosmopedie</h2><div class="theme-grid">' + group_cards + '</div></section>\n'
            '<p id="kosmopedie-group-back" hidden><a href="/kosmopedie/" data-show-groups>← Všechny okruhy Kosmopedie</a></p>\n'
            '    <div id="kosmopedie-topics">\n' + list_html + '    </div>\n'
            '    <script defer src="/assets/kosmopedie-search.js?v=2"></script>\n')
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
