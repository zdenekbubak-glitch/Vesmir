#!/usr/bin/env python3
"""
Generátor statických SEO stránek pro kosmonovinky.cz
Čte data/news.json a data/images.json, vygeneruje:
  - clanky/<slug>.html        … jedna stránka každé novinky (indexovatelné pro Google)
  - clanky/index.html         … přehled všech novinek (s fulltextovým hledáním)
  - temata/<rubrika>.html     … tematické přehledy (černé díry, temná hmota, …)
  - obrazky/<slug>.html       … stránky obrázků galerie
  - sitemap.xml, robots.txt, feed.xml (Atom)
Použití: python3 tools/build_static.py --site-dir . --out _site --base https://kosmonovinky.cz
"""
import argparse
import editorial
from newsletter_content import build_email as newsletter_email
import html
from html.parser import HTMLParser
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlencode, quote
from assign_article_images import prepare as prepare_images, lookup as lookup_image, figure as image_figure, image_schema, gallery_image_schema, image_url, thumbnail

MESICE_GEN = ["ledna", "února", "března", "dubna", "května", "června", "července",
              "srpna", "září", "října", "listopadu", "prosince"]
MESICE_NOM = ["leden", "únor", "březen", "duben", "květen", "červen", "červenec",
              "srpen", "září", "říjen", "listopad", "prosinec"]

THEMES = [
    ("cerne-diry",       "Černé díry",        ["černá díra", "černé díry", "černé diře", "černou díru", "black hole", "singularity", "singularit"]),
    ("temna-hmota",      "Temná hmota",       ["temná hmota", "temné hmoty", "dark matter", "wimp", "axion", "axionů"]),
    ("gravitacni-vlny",  "Gravitační vlny",   ["gravitacní vln", "gravitational wave", "ligo", "virgo", "kilonov"]),
    ("exoplanety",       "Exoplanety",        ["exoplanet", "exoplaneta", "tranzitní", "habitabilní"]),
    ("galaxie",          "Galaxie",           ["galaxi", "galaxy", "mléčná dráha", "milky way", "andromed", "halo galaxi"]),
    ("vesmirne-teleskopy", "Teleskopy a observatoře", ["jwst", "james webb", "hubble", "euclid", "teleskop", "observatoř", "observatory", "kamera", "přístroj", "detektor"]),
    ("relictni-zareni",  "Reliktní záření",   ["reliktn", "cmb", "kosmické mikrovlnné"]),
    ("neutronove-hvezdy", "Neutronové hvězdy", ["neutronov", "magnetar", "pulsar", "pulzar"]),
    ("velky-tresk",      "Velký třesk",       ["velký třesk", "big bang", "rekombinac", "inflac", "reionizac", "prvotní vesmír", "raný vesmír", "raného vesmíru"]),
    ("temna-energie",    "Temná energie",     ["temná energie", "dark energy", "kosmologická konstanta"]),
    ("kvantova-gravitace", "Kvantová gravitace", ["kvantová gravitace", "quantum gravity", "smyčková gravitace", "string theory", "strunová teorie", "kvantová pěna"]),
    ("kvazary",          "Kvasary a aktivní jádra", ["kvazar", "quasar", "aktivní galaktické jádro", "agn"]),
    ("multivesmir",      "Multivesmír",       ["multivesmír", "paralelní vesmír", "parallel universe", "bubble univers", "vesmírů"]),
    ("temna-dira-v-centru", "Supermasivní černé díry", ["supermasiv", "sgr a*", "m87", "centra galaxi", "galaktického centra", "galaktické centrum"]),
    ("gravimetrie-testy", "Testy gravitace a fyziky", ["obecný princip ekvivalence", "oříškový", "sluneční soustavy", "merkur", "přesnost", "test gravitace", "lorentzov", "pauliho"]),
]
THEME_LABEL = {s: l for s, l, _ in THEMES}
FALLBACK_THEME = ("ostatni", "Další témata")

# Shared navigation between subject cards and the complete content list.
def collection_switch(kind, current):
    if kind == 'kosmopedie':
        links = [('groups', '/kosmopedie/', 'Okruhy'),
                 ('all', '/kosmopedie/?view=all', 'Všechna témata')]
    else:
        links = [('groups', '/temata/', 'Rubriky'),
                 ('all', '/clanky/', 'Všechny články')]
    icons = {
        'groups': '<svg viewBox="0 0 20 20" aria-hidden="true" focusable="false"><rect x="2" y="2" width="6" height="6" rx="1"/><rect x="12" y="2" width="6" height="6" rx="1"/><rect x="2" y="12" width="6" height="6" rx="1"/><rect x="12" y="12" width="6" height="6" rx="1"/></svg>',
        'all': '<svg viewBox="0 0 20 20" aria-hidden="true" focusable="false"><path d="M3 4h14M3 10h14M3 16h14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    }
    html = '<nav class="collection-switch" aria-label="Zobrazení přehledu">'
    for key, href, label in links:
        active = ' aria-current="page"' if key == current else ''
        html += f'<a data-collection-view="{key}" href="{href}"{active}>{icons[key]}<span>{label}</span></a>'
    return html + '</nav>\n'


CSS = """
    :root { --bg: #0b0f19; --card: #151b2d; --text: #e8eef7; --accent: #6ea8fe; --muted: #9aa8c7; }
    * { box-sizing: border-box; }
    body { font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; line-height: 1.55; }
    header { background: linear-gradient(135deg, #0f172a, #1e293b); padding: 1.8rem 1rem 1.5rem; text-align: center; border-bottom: 1px solid #1e293b; }
    a { color: var(--accent); text-decoration: none; }
    header a { color: inherit; text-decoration: none; }
    .logo-wrapper { display: flex; align-items: center; justify-content: center; gap: .9rem; margin-bottom: .5rem; }
    .logo-wrapper img { height: 80px; width: 80px; display: block; border-radius: 12px; }
    .logo-text .site-name { margin: 0; font-size: 2rem; font-weight: 600; letter-spacing: -.02em; }
    .subtitle { color: var(--muted); margin: .35rem 0 1rem; font-size: .95rem; }
    nav { margin: .6rem 0 1.2rem; }
    nav a { color: var(--accent); margin: 0 .7rem; font-size: .95rem; }
    .signup-box { max-width: 720px; margin: 0 auto; background: rgba(21,27,45,.75); border: 1px solid #1e293b; border-radius: 10px; padding: .95rem 1.15rem; }
    .signup-box p { margin: 0 0 .65rem; font-size: .95rem; color: var(--muted); white-space: normal; }
    .signup-form { display: flex; gap: .5rem; flex-wrap: wrap; justify-content: center; align-items: center; }
    .signup-form label { display: none; }
    .signup-form input[type=email] { flex: 1; min-width: 200px; padding: .55rem .85rem; border: 1px solid #334155; border-radius: 6px; background: #0b0f19; color: var(--text); font-size: .95rem; }
    .signup-form input[type=email]::placeholder { color: #64748b; }
    .signup-form input[type=submit] { padding: .55rem 1.15rem; background: var(--accent); color: #0b0f19; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: .95rem; }
    .signup-form input[type=submit]:hover { filter: brightness(1.12); }
    .signup-form p { width: 100%; margin: .5rem 0 0; font-size: .75rem; color: var(--muted); }
    .signup-form p a { color: var(--muted); text-decoration: underline; }
    main { max-width: 820px; margin: 0 auto; padding: 1.5rem 1rem 3rem; }
    .breadcrumbs { font-size: .85rem; color: var(--muted); margin-bottom: 1.2rem; }
    .breadcrumbs a { color: var(--accent); }
    .post { background: var(--card); border: 1px solid #1e293b; border-radius: 12px; padding: 1.4rem 1.5rem; margin-bottom: 1.2rem; }
    .meta { font-size: .82rem; color: var(--muted); margin-bottom: .8rem; }
    .meta a { color: var(--accent); }
    .post h1 { font-size: 1.45rem; line-height: 1.3; margin: 0 0 .9rem; }
    .post h2 { font-size: 1.15rem; margin: 1.2rem 0 .5rem; }
    .summary { margin: 0 0 1rem; }
    .newsletter-cta { margin: 1.4rem 0 0; padding-top: .8rem; border-top: 1px solid #1e293b; font-size: .88rem; color: var(--muted); }
    .lang-note { font-size: .85rem; color: #f0b429; }
    .post a.original-source { font-size: .82rem; line-height: 1.5; color: var(--accent); text-decoration: none; }
    .post a.original-source:hover, .post a.original-source:focus-visible { text-decoration: underline; }
    .source-link { display: inline-block; margin-top: .4rem; }
    .post .source-link { display: block; margin: .6rem 0 0; font-size: .82rem; line-height: 1.5; }
    .post .article-sources { margin: 1rem 0; font-size: .82rem; line-height: 1.5; color: var(--muted); }
    .post .article-sources h2, .post .article-sources h3 { margin: 0 0 .35rem; font-size: .9rem; line-height: 1.5; color: var(--muted); }
    .post .article-sources p { margin: .2rem 0; }
    .post .article-sources ul, .post .article-sources ol { margin: .2rem 0; padding-left: 1.2rem; }
    .post .article-sources li { margin: .15rem 0; }
    .post .article-sources a { overflow-wrap: anywhere; }
    .related { margin-top: 1.4rem; border-top: 1px solid #1e293b; padding-top: 1rem; }
    .related ul { margin: .5rem 0 0; padding-left: 1.2rem; }
    .related li { margin-bottom: .35rem; }
    .related a { color: var(--accent); }
    .theme-badge { display: inline-block; background: #1e293b; border-radius: 999px; padding: .15rem .8rem; font-size: .8rem; margin-bottom: .8rem; }
    .theme-badge a { color: var(--accent); text-decoration: none; }
    article.item { background: var(--card); border: 1px solid #1e293b; border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: .9rem; }
    article.item h2 { font-size: 1.1rem; margin: 0 0 .4rem; }
    article.item h2 a { color: var(--text); text-decoration: none; }
    article.item h2 a:hover { color: var(--accent); }
    article.item .meta { margin-bottom: .2rem; }
    .year-title, .section-title { color: var(--muted); }
    .section-title { font-size: 1.05rem; margin: 1.4rem 0 .6rem; }
    figure { margin: 0 0 1rem; }
    figure img { width: 100%; border-radius: 10px; }
    figcaption { font-size: .85rem; color: var(--muted); margin-top: .5rem; }
    [hidden] { display: none !important; }
    .collection-switch { display: flex; flex-wrap: wrap; gap: .45rem; margin: 1rem 0; }
    .collection-switch a { display: inline-flex; align-items: center; gap: .5rem; padding: .5rem .8rem; border: 1px solid #334155; border-radius: 9px; color: var(--muted); text-decoration: none; font-size: .92rem; }
    .collection-switch a[aria-current="page"] { color: var(--text); border-color: var(--accent); background: var(--card); }
    .collection-switch a:hover { color: var(--accent); border-color: var(--accent); }
    .collection-switch svg { width: 1.1rem; height: 1.1rem; flex: 0 0 auto; fill: currentColor; }
    .collection-switch a:focus-visible, .topic-card:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
    .topic-card { display: block; background: var(--card); border: 1px solid #1e293b; border-radius: 10px; padding: 1rem 1.2rem; color: var(--text); text-decoration: none; }
    .topic-card:hover { border-color: var(--accent); text-decoration: none; }
    .topic-card h3 { margin: 0 0 .55rem; color: var(--accent); font-size: 1.05rem; }
    .topic-card .summary { font-size: .92rem; margin: 0 0 .65rem; }
    .topic-card .count { color: var(--muted); font-size: .85rem; margin: 0; }
    .collection-heading { color: var(--muted); font-size: 1.05rem; margin: 1rem 0; }
    .feedback-link { margin: 1rem 0; font-size: .85rem; line-height: 1.6; color: var(--muted); }
    .feedback-link a { text-decoration: none; }
    .feedback-link a:hover, .feedback-link a:focus-visible { text-decoration: underline; }
    .feedback-email { overflow-wrap: anywhere; }
    .theme-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: .9rem; }
    .theme-card { background: var(--card); border: 1px solid #1e293b; border-radius: 10px; padding: 1rem 1.2rem; }
    .theme-card a { color: var(--accent); font-weight: 600; text-decoration: none; }
    .theme-card .count { color: var(--muted); font-size: .85rem; }
    .back { margin-top: 1.5rem; font-size: .9rem; }
    .post-nav { display: flex; justify-content: space-between; gap: 1rem; border-top: 1px solid #1e293b; padding-top: 1rem; margin-top: 1.5rem; font-size: .95rem; }
    .post-nav .next { margin-left: auto; }
    .image-paging { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }
    .image-paging a { min-width: 0; overflow-wrap: anywhere; text-decoration: none; }
    .image-paging a:hover, .image-paging a:focus-visible { text-decoration: underline; }
    .image-paging .next { grid-column: 2; margin-left: 0; text-align: right; }
    .image-paging span { display: block; }
    @media (max-width: 600px) {
      .image-paging { grid-template-columns: minmax(0, 1fr); }
      .image-paging .next { grid-column: auto; text-align: left; }
    }
    .back a { color: var(--accent); }
    .search-box { width: 100%; padding: .35rem .85rem; margin: .6rem 0 1.2rem; border: 1px solid #1e293b; border-radius: 10px; background: var(--card); color: var(--text); font-size: .95rem; outline: none; }
    article.item[hidden], h2.section-title[hidden] { display: none !important; }
    .search-excerpt { margin: .6rem 0; padding-left: .8rem; border-left: 2px solid var(--accent); font-size: .9rem; color: var(--muted); }
    .search-status { font-size: .85rem; color: var(--muted); margin: 0 0 1rem; }
    article.item mark { background: #f6d365; color: #141a26; border-radius: 2px; padding: 0 .06em; }
    .search-box:focus { border-color: var(--accent); }
    .search-box::placeholder { color: #64748b; }
    @media (max-width: 520px) {
      .logo-wrapper { flex-direction: column; gap: 0.45rem; }
      .logo-wrapper img { height: 64px; width: 64px; }
      .logo-text .site-name { font-size: 1.45rem; }
      .signup-box p { white-space: normal; }
    }
"""

COUNTER_JS = """
// Counter is loaded from the shared file; see page_head.
"""



def feedback_link(title, canonical_url):
    """Private editorial feedback; creating this link never sends a message."""
    title = ' '.join(str(title or '').split())
    body = (f'Příspěvek: {title}\r\nOdkaz: {canonical_url}\r\n\r\n'
            'Popište prosím chybu nebo nepřesnost:\r\n')
    params = urlencode({'subject': 'Připomínka k příspěvku: ' + title, 'body': body}, quote_via=quote)
    href = 'mailto:redakce@kosmonovinky.cz?' + params
    return ('<p class="feedback-link">Našli jste chybu nebo nepřesnost? '
            f'<a href="{esc(href)}" target="_blank" rel="noopener noreferrer">Napište redakci.</a> '
            '<span class="feedback-email">(redakce@kosmonovinky.cz)</span></p>')


NEWSLETTER_CTA = ('<p class="newsletter-cta">Zaujalo vás téma? '
                  '<a href="#bd-email" data-newsletter-focus>Přihlaste se k týdennímu výběru e-mailem ↑</a></p>')

NEWSLETTER_FOCUS_JS = """
document.addEventListener('click', function (event) {
  const link = event.target.closest && event.target.closest('[data-newsletter-focus]');
  if (!link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
  const field = document.getElementById('bd-email');
  if (!field) return;
  event.preventDefault();
  field.focus({ preventScroll: true });
  const box = field.closest('.signup-box') || field;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  box.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'center' });
});
"""

SIGNUP_FORM = """
    <div class="signup-box">
      <p>Každý týden 5 nejzajímavějších objevů a poznatků o vesmíru do e-mailu.</p>
      <p style="font-size:.82rem;margin:-.25rem 0 .65rem">Česky, srozumitelně a s odkazy do Kosmopedie.</p>
      <form action="https://buttondown.com/api/emails/embed-subscribe/zdenek" method="post" class="embeddable-buttondown-form signup-form">
        <label for="bd-email">E-mail pro týdenní výběr</label>
        <input type="email" name="email" id="bd-email" placeholder="tvuj@email.cz" required />
        <input type="submit" value="Odebírat" />
      </form>
    <p class="newsletter-preview-link" style="margin:.55rem 0 0;font-size:.82rem;white-space:normal"><a href="/newsletter/">Ukázka newsletteru →</a></p>
    </div>
"""


def esc(s):
    return html.escape(str(s or ""), quote=True)


def slugify(text, max_words=10):
    t = unicodedata.normalize("NFKD", text)
    t = t.encode("ascii", "ignore").decode("ascii").lower()
    t = re.sub(r"[^a-z0-9]+", " ", t).split()
    return "-".join(t[:max_words]) or "clanek"


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def fmt_date(value):
    dt = parse_dt(value)
    if not dt:
        return ""
    return f"{dt.day}. {MESICE_GEN[dt.month - 1]} {dt.year}"


def fmt_iso_date(value):
    dt = parse_dt(value)
    return dt.date().isoformat() if dt else "2026-01-01"


def truncate(text, limit=158):
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(" ,.;:") + "…"


class SearchTextParser(HTMLParser):
    """Visible editorial body only; do not index navigation or HTML attributes."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'): self.ignored += 1
        elif tag in ('p', 'li', 'h2', 'h3', 'blockquote', 'br'): self.parts.append(' ')
    def handle_endtag(self, tag):
        if tag in ('script', 'style'): self.ignored = max(0, self.ignored - 1)
        elif tag in ('p', 'li', 'h2', 'h3', 'blockquote'): self.parts.append(' ')
    def handle_data(self, data):
        if not self.ignored: self.parts.append(data)


def search_body(item):
    if 'body' in item:
        parser = SearchTextParser()
        parser.feed(item['body'])
        return ' '.join(''.join(parser.parts).split())
    return ' '.join(str(item.get('summary') or item.get('original_title') or item.get('title') or '').split())


def article_perex(item, limit=280):
    """Short teaser for listings only; never modifies the full detail text."""
    text = str(item.get('perex') or item.get('summary') or item.get('original_title') or item.get('title') or '')
    text = re.split(r'\s*Proč\s+je\s+to\s+zajímavé\s*:', text, maxsplit=1, flags=re.IGNORECASE)[0]
    text = re.sub(r'\s+', ' ', text).strip()
    parts = re.split(r'(?<=[.!?])\s+(?=[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ])', text)
    result = ''
    for sentence in parts[:2]:
        candidate = (result + ' ' + sentence).strip()
        if len(candidate) > limit:
            break
        result = candidate
    if result:
        return result
    if len(text) <= limit:
        return text
    clipped = text[:limit - 1]
    if ' ' in clipped:
        clipped = clipped.rsplit(' ', 1)[0]
    return clipped.rstrip(' ,;:–-') + '…'


def id_digits(item_id):
    return re.sub(r"[^0-9]", "", str(item_id))[:12] or "0"


def classify(item):
    text = " ".join(str(item.get(k) or "") for k in ("title", "summary", "original_title")).lower()
    for slug, _label, keywords in THEMES:
        if any(kw in text for kw in keywords):
            return slug
    return FALLBACK_THEME[0]


# Explicit topic patterns prevent arbitrary links based on shared generic words.
# Keys refer to stable IDs in data/explainery.json; unknown entries are omitted.
EXPLAINER_PATTERNS = {
    'exp-093': r'nasa exoplanet archive|katalog.*exoplanet',
    'exp-094': r'trappist.?1|proxima.* b|lhs.?1140|toi.?700|kepler.?62',
    'exp-085': r'max planck',
    'exp-086': r'niels bohr',
    'exp-087': r'louis de broglie',
    'exp-088': r'werner heisenberg',
    'exp-089': r'erwin schrodinger',
    'exp-090': r'max born',
    'exp-091': r'wolfgang pauli',
    'exp-092': r'paul dirac',

    'exp-001': r'temn\w* hmot\w*|dark matter|\baxion\w*|\bwimps?\b',
    'exp-002': r'gravitacn\w* vln\w*|gravitational wave',
    'exp-003': r'spad\w* do cern\w* dir\w*|pad\w* do cern\w* dir\w*|spagetifik\w*',
    'exp-004': r'temn\w* energi\w*|dark energy|kosmologick\w* konstant\w*',
    'exp-005': r'cern\w* dir\w*|black holes?',
    'exp-006': r'horizont\w* udalost\w*|event horizons?',
    'exp-007': r'reliktn\w* zaren\w*|\bcmb\b|cosmic microwave background',
    'exp-008': r'neutronov\w* hvezd\w*|neutron stars?',
    'exp-009': r'spiraln\w* ramen\w*|spiral arms?',
    'exp-010': r'rotacn\w* kriv\w*|rotation curves?|dukaz\w* temn\w* hmot\w*',
    'exp-011': r'hawking\w*|vypar\w* cern\w* dir\w*|black hole evaporation',
    'exp-012': r'\bgw\d{6}\b|detek\w* gravitacn\w* vln\w*|gravitational.wave event',
    'exp-013': r'anizotrop\w*|map\w* reliktn\w* zaren\w*|cmb anisotrop\w*',
    'exp-014': r'\bmagnetar\w*|\bpul[sz]ar\w*',
    'exp-015': r'\bexoplanet\w*',
    'exp-016': r'\baxion\w*|\bwimps?\b|kandidat\w* temn\w* hmot\w*|dark matter candidates?',
    'exp-017': r'velk\w* tresk\w*|big bang|kosmick\w* inflac\w*|cosmic inflation',
    'exp-018': r'supermasiv\w*|supermassive|\bsgr a|\bm87\b',
    'exp-019': r'bez temn\w* hmot\w*|without dark matter|dark.matter.free',
    'exp-020': r'\bligo\b|\bvirgo\b|\bkagra\b|\blisa\b|interferometr\w*',
    'exp-021': r'\bcobe\b|\bwmap\b|planck\w* (?:druzic\w*|satelit\w*|observator\w*)',
    'exp-022': r'kilonov\w*|r.proces\w*|nukleosyntez\w*|nucleosynthesis|tezk\w* prvk\w*',
    'exp-023': r'vznik\w* galaxi\w*|formov\w* galaxi\w*|galaxy formation|galaxi\w* rost\w*',
    'exp-024': r'sraz\w* galaxi\w*|splyv\w* galaxi\w*|sluc\w* galaxi\w*|galaxy (?:collisions?|mergers?)',
    'exp-025': r'hubble\w* konstant\w*|hubble constant|\bh0\b|\bh₀\b',
    'exp-026': r'hubble\w* napeti|hubble tension',
    'exp-027': r'\b(?:λ|lambda)[ -]?cdm\b|\blcdm\b|standard\w* kosmolog\w* model\w*',
    'exp-028': r'\bteleskop\w*|\bdalekohled\w*|\bobservator\w*|\bjwst\b|james webb|\balma\b|\bvlt\b',
    'exp-029': r'standard\w* model\w* castic\w*|standard model of particle|\bkvark\w*|\bquark\w*|\blepton\w*|higgs\w*',
    'exp-030': r'hubble\w* (?:vesmirn\w* )?(?:teleskop\w*|dalekohled\w*)|hubble space telescope|\bhst\b',
    'exp-031': r'webb\w*|\bjwst\b',
    'exp-032': r'\bvlt\b|\bvlti\b|\bparanal\w*|\bgravity\b',
    'exp-033': r'\balma\b|\bchajnantor\w*',
    'exp-034': r'\blhc\b|\bcern\b|\batlas\b|\bcms\b|\balice\b|urychlovac\w*|hadron collider',
    'exp-035': r'\bspektroskop\w*|\bspektrograf\w*|\bspectroscop\w*|\bspectrograph\w*',
    'exp-036': r'absorpc\w* car\w*|emisn\w* car\w*|spektral\w* car\w*|absorption lines?|emission lines?',
    'exp-037': r'chemick\w* slozen\w*|chemical composition|\bmetalic\w*|metallicity|molekul\w*.*atmosfer\w*',
    'exp-038': r'rud\w* posuv\w*|modr\w* posuv\w*|\bredshift\w*|\bblueshift\w*',
    'exp-039': r'jades.gs.z14.0|3c.?273|j1030.0524',
    'exp-040': r'kvantov\w* mechanik\w*|quantum mechanics',
    'exp-041': r'vlnov\w* funkc\w*|wave.?function\w*|pravdepodobnostn\w* amplitud\w*',
    'exp-042': r'\bsuperpozic\w*|\bsuperposition\w*|\bdekoherenc\w*|\bdecoherence\w*',
    'exp-043': r'\bheisenberg\w*|princip\w* neurcitost\w*|uncertainty principle',
    'exp-044': r'kvantov\w* provazan\w*|\bentangle\w*|bellov\w* nerovnost\w*',
    'exp-045': r'kvantov\w* teori\w* pol\w*|quantum field theor\w*|\bqft\b',
    'exp-046': r'kvantov\w* pol\w*|quantum fields?|elektronov\w* pol\w*',
    'exp-047': r'kvantov\w* vaku\w*|quantum vacuum|vakuov\w* fluktuac\w*|casimir\w*',
    'exp-048': r'higgs\w*|brout.englert',
    'exp-049': r'kvantov\w* gravitac\w*|quantum gravity|\bgraviton\w*|smyckov\w* gravitac\w*|string theor\w*',
    'exp-050': (r'rozsir\w* (?:standardn\w* |zakladn\w* )?(?:kosmologick\w* model\w*|(?:model\w* )?(?:lambda|λ|l)[ -]?cdm)'
        r'|extended cosmolog\w*|beyond [λl]?cdm|early dark energy|ran\w* temn\w* energi\w*'
        r'|\b(?:sidm|wdm)\b|self[ -]?interact\w* dark matter|warm dark matter'
        r'|(?:sebeinterag\w*|samointerag\w*|vzajemne interag\w*|tepl\w*) temn\w* hmot\w*'),
    'exp-051': r'promenliv\w* temn\w* energi\w*|dynamick\w* temn\w* energi\w*|evolving dark energy|dynamical dark energy|kvintesenc\w*|quintessence|w0wa',
    'exp-052': r'modifikovan\w* gravitac\w*|modified gravity|scalar.tensor|skalarne.tenzor\w*|f\(r\)',
    'exp-053': r'\bmond\b|modifikovan\w* newton\w*|modified newtonian|bez temn\w* hmot\w*',
    'exp-054': r'bayes\w*|porovnavan\w* (?:kosmologick\w* )?model\w*|model selection|systematick\w* (?:chyb\w*|nejistot\w*)',
    'exp-055': r'histori\w* kosmologi\w*|history of cosmology',
    'exp-056': r'leavitt\w*|cefeid\w*|cepheid\w*',
    'exp-057': r'lemaitre\w*|prvotni atom|primeval atom',
    'exp-058': r'edwin hubble|hubble.{0,12}1929|slipher\w*|humason\w*',
    'exp-059': r'vera rubin\w*|rubinov\w*|kent ford',
    'exp-070': r'albert einstein',
    'exp-071': r'friedmann\w*',
    'exp-072': r'perlmutter\w*',
    'exp-073': r'brian schmidt',
    'exp-074': r'adam riess|riessov\w*',
    'exp-075': r'penzias\w*|robert wilson',
    'exp-076': r'james peebles|jim peebles|peeblesov\w*',
    'exp-077': r'fritz zwicky|zwickyho',
    'exp-078': r'kosmick\w* topologi\w*|cosmic topology|prostorov\w* kriv\w*|spatial curvature|tvar\w* vesmir\w*',
    'exp-079': r'big rip|big crunch|big freeze|heat death|tepelna smrt|konec vesmir\w*|budoucnost\w* vesmir\w*',
    'exp-080': r'zrychl\w* rozpin\w*|accelerat\w* expansion|supernov\w* cosmolog\w*',
    'exp-081': r'kosmick\w* inflac\w*|kosmologick\w* inflac\w*|cosmic inflation|cosmological inflation|primordial gravitational waves',
    'exp-082': r'nukleosyntez\w*|nucleosynthesis|primordial deuterium|prvotn\w* deuteri\w*',
    'exp-083': r'exoplanet\w* atmospher\w*|atmospher\w* exoplanet\w*|atmosfer\w* exoplanet\w*|exoplanet\w* atmosfer\w*|transmission spectr\w*',
    'exp-084': r'obyvateln\w* zon\w*|habitable zone|circumstellar habitab\w*',
    'exp-065': r'superkekb|belle\s*ii|j[ -]?parc|(?:leptonov\w*|mionov\w*|casticov\w*) urychlovac\w*|urychlovac\w* castic\w*|collider\w*|fixed[ -]target',
    'exp-066': r'identifikac\w* castic\w*|particle identification|statistick\w* vyznam\w*|\bsigma\b|nov\w* castic\w*|new particle',
    'exp-067': r'antihmot\w*|antimatter|antiatom\w*|antivodik\w*|antihydrogen|leptogenez\w*|leptogenesis',
    'exp-068': r'neutrin\w* oscil\w*|neutrino oscillation\w*|oscil\w* neutrin\w*|hmotnost\w* neutrin\w*|neutrino mass\w*|\bmsw\b',
    'exp-069': r'kosmick\w* zaren\w*|cosmic rays?|casticov\w* sprsk\w*|air showers?|pierre auger',
}


def explainer_catalog(site):
    """Use the exact same slug allocation as the Kosmopedie generator."""
    path = Path(site) / 'data' / 'explainery.json'
    if not path.exists():
        return []
    entries = json.loads(path.read_text(encoding='utf-8'))
    used = set()
    for entry in entries:
        root = slugify(entry['title'])
        slug, number = root, 2
        while slug in used:
            slug = f'{root}-{number}'
            number += 1
        used.add(slug)
        entry['_slug'] = slug
    return entries


def topic_text(value):
    text = unicodedata.normalize('NFKD', str(value or '').lower())
    return ''.join(c for c in text if not unicodedata.combining(c))


def related_explainers(item, catalog, limit=2):
    title = topic_text(item.get('title'))
    body = topic_text(' '.join(str(item.get(k) or '') for k in ('summary', 'original_title')))
    ranked = []
    for entry in catalog:
        pattern = EXPLAINER_PATTERNS.get(entry.get('id'))
        if not pattern:
            continue
        title_hit = bool(re.search(pattern, title))
        body_hit = bool(re.search(pattern, body))
        if not (title_hit or body_hit):
            continue
        # Prefer a specific concept from the headline over incidental body mentions.
        basic = entry['id'] in ('exp-001', 'exp-002', 'exp-005', 'exp-007', 'exp-008')
        score = 10 * title_hit + 2 * body_hit + (0 if basic else 1)
        ranked.append((-score, entry['id'], entry))
    return [entry for _, _, entry in sorted(ranked, key=lambda r: (r[0], r[1]))[:limit]]


def explainer_links_html(item, catalog):
    entries = related_explainers(item, catalog)
    if not entries:
        return ''
    links = '\n'.join(
        f'        <li><a href="/kosmopedie/{esc(entry["_slug"])}.html">{esc(entry["title"])}</a></li>'
        for entry in entries)
    return ('    <section class="related kosmopedie-context">\n'
            '      <h2>Pro pochopení souvislostí</h2>\n'
            '      <p>Související pojmy srozumitelně vysvětluje Kosmopedie:</p>\n'
            '      <ul>\n' + links + '\n      </ul>\n    </section>\n')



def write_home_explainer_links(news, catalog, out):
    """Reuse detail-page selection for the lightweight homepage links."""
    labels = [
        'Temná hmota', 'Gravitační vlny', 'Pád do černé díry', 'Temná energie',
        'Černé díry', 'Horizont událostí', 'Reliktní záření', 'Neutronové hvězdy',
        'Spirální ramena', 'Důkazy temné hmoty', 'Hawkingovo záření',
        'Objevy gravitačních vln', 'Mapa reliktního záření', 'Magnetary a pulsary',
        'Exoplanety', 'Částice temné hmoty', 'Velký třesk', 'Supermasivní černé díry',
        'Vesmír bez temné hmoty', 'Měření gravitačních vln', 'Snímkování reliktního záření',
        'Vznik těžkých prvků', 'Vznik galaxií', 'Srážky galaxií',
    ]
    short = {f'exp-{i:03d}': label for i, label in enumerate(labels, 1)}
    links = {}
    for item in news:
        if not item.get('id'):
            continue
        entries = related_explainers(item, catalog)
        if entries:
            links[str(item['id'])] = [
                {'href': '/kosmopedie/' + entry['_slug'] + '.html',
                 'title': entry['title'], 'label': short.get(entry.get('id'), entry['title'])}
                for entry in entries]
    folder = Path(out) / 'data'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'kosmopedie_links.json').write_text(
        json.dumps(links, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return links



def complete_topic_gallery(curated, explainery, library, catalog):
    """Include every actual Kosmopedie image, preserving curated metadata and IDs."""
    result = [dict(item) for item in curated]
    known = {item.get('catalog_image_id') for item in result}
    used = set()
    for ex in explainery:
        entry = lookup_image(ex, 'explainery', library)
        if entry:
            used.add(entry['id'])
        used.update(sec['image_id'] for sec in ex.get('sections', []) if sec.get('image_id'))
    kinds = {'snímek': 'snimek', 'kompozitní snímek': 'snimek', 'mapa odvozená z pozorování': 'snimek',
             'výtvarná představa': 'ilustrace', 'umělecká představa': 'ilustrace', 'ilustrace': 'ilustrace', 'vlastní schéma': 'schema'}
    for image_id in sorted(used - known):
        e = catalog.get(image_id)
        if not e:
            raise ValueError('Obrázek Kosmopedie chybí v katalogu: ' + image_id)
        result.append({'id': 'kosmopedie-' + image_id, 'catalog_image_id': image_id,
                       'title': e['title'], 'caption': e.get('caption', ''),
                       'image': 'assets/article-images/' + image_id + '.jpg', 'thumb': e.get('thumbnail', ''),
                       'source': e.get('credit', ''), 'url': e.get('source', ''), 'credit': e.get('credit', ''),
                       'published': e.get('verified_on', ''), 'inserted_at': e.get('verified_on', ''),
                       'lang': 'cs', 'needs_translation': False, 'license': e.get('license', ''),
                       'license_url': e.get('license_url', ''), 'modifications': e.get('modifications', '')})
    for item in result:
        e = catalog.get(item.get('catalog_image_id'), {})
        item.setdefault('gallery_type', kinds.get(e.get('kind'), ''))
        if e.get('kind') in ('kompozitní snímek', 'mapa odvozená z pozorování'):
            item.setdefault('gallery_type_label', 'Kompozitní snímek' if e['kind'] == 'kompozitní snímek' else 'Mapa odvozená z pozorování')
        words = list(item.get('gallery_keywords', []))
        text = topic_text(' '.join([e.get('title', ''), e.get('topic', ''), *e.get('topics', [])]))
        if 'cern' in text and ('dir' in text or 'der' in text) or 'm87' in text or 'sagittarius' in text:
            words += ['černá díra', 'černé díry', 'black hole']
        item['gallery_keywords'] = list(dict.fromkeys(words))
    return result


def write_gallery_context(site, out, images, news, explainery, library, editor_posts):
    """Describe only curated gallery entries; never import the entire image catalogue."""
    catalog = {e['id']: e for e in json.loads((Path(site) / 'data/article_image_catalog.json').read_text(encoding='utf-8'))}
    by_catalog = {}
    context = {}
    kinds = {'snímek': 'snimek', 'výtvarná představa': 'ilustrace', 'ilustrace': 'ilustrace', 'vlastní schéma': 'schema'}
    for image in images:
        key = image.get('catalog_image_id')
        entry = catalog.get(key, {})
        item = {'detail': '/' + image['_path'], 'related': [],
                'type': image.get('gallery_type') or kinds.get(entry.get('kind'), ''),
                'source_url': entry.get('source', '') if key else image.get('url', '')}
        context[str(image['id'])] = item
        if key:
            by_catalog.setdefault(key, []).append(item)

    def attach(image_id, kind, title, href):
        for item in by_catalog.get(image_id, []):
            if not any(r['href'] == href for r in item['related']):
                item['related'].append({'kind': kind, 'title': title, 'href': href})

    for ex in explainery:
        entry = lookup_image(ex, 'explainery', library)
        ids = [entry['id']] if entry else []
        ids += [sec['image_id'] for sec in ex.get('sections', []) if sec.get('image_id')]
        for image_id in ids:
            attach(image_id, 'kosmopedie', ex['title'], '/kosmopedie/' + ex['_slug'] + '.html')
    for item in news:
        entry = lookup_image(item, 'news', library)
        if entry:
            attach(entry['id'], 'clanky', item['title'], '/' + item['_path'])
    for post in editor_posts:
        entry = post.get('image_entry')
        if entry:
            attach(entry['id'], 'clanky', post['title'], post['href'])
    folder = Path(out) / 'data'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'gallery-context.json').write_text(json.dumps(context, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')


def build_home_news(site, out, news, library, links, now=None):
    """Render identical news HTML for all visitors; JS only filters existing cards."""
    template = Path(out) / 'index.html'
    if not template.exists():
        template = Path(site) / 'index.html'
    if not template.exists():
        return
    page = template.read_text(encoding='utf-8')
    start, end = '<!-- NEWS:START -->', '<!-- NEWS:END -->'
    if page.count(start) != 1 or page.count(end) != 1:
        raise ValueError('index.html: chybí jednoznačné značky NEWS:START a NEWS:END')
    tz = ZoneInfo('Europe/Prague')
    now = (now or datetime.now(tz)).astimezone(tz)
    current = now.year * 12 + now.month
    groups = {}
    for item in news:
        dt = parse_dt(item.get('inserted_at') or item.get('published'))
        if not dt:
            continue
        dt = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        local = dt.astimezone(tz)
        if local.year * 12 + local.month not in (current, current - 1):
            continue
        groups.setdefault((local.year, local.month), []).append((item, local))
    blocks = []
    for (year, month), items in sorted(groups.items(), reverse=True):
        cards = []
        for item, inserted in items:
            href = '/' + item['_path']
            published = fmt_date(item.get('published'))
            meta = (f'Vloženo: {inserted.day}. {inserted.month}. {inserted.year} '
                    f'{inserted:%H:%M:%S} · Zdroj: {esc(item.get("source"))}')
            if published:
                meta += ' · Publikováno: ' + esc(published)
            note = ('<p class="lang-note">Anglický originál – český souhrn se nepodařilo vytvořit.</p>'
                    if item.get('lang') == 'en' or item.get('needs_translation') else '')
            terms = links.get(str(item.get('id')), [])
            context = ''
            if terms:
                anchors = ' · '.join(f'<a href="{esc(e["href"])}">{esc(e["label"])}</a>' for e in terms)
                context = f'<p class="kosmopedie-inline">Pojmy v Kosmopedii: {anchors}</p>'
            source = str(item.get('url') or '')
            source_link = (f'<a class="original-source" href="{esc(source)}" target="_blank" rel="noopener">Původní zdroj →</a>'
                           if urlsplit(source).scheme in ('http', 'https') else '')
            cards.append(
                '<article class="post">'
                f'<h2><a href="{esc(href)}">{esc(item.get("title"))}</a></h2>'
                f'<div class="meta">{meta}</div>' + note + '<div class="article-teaser">'
                + thumbnail(lookup_image(item, 'news', library), href)
                + f'<p class="summary">{esc(item.get("summary"))}</p></div>'
                + context + source_link + '</article>')
        blocks.append('<section class="news-month">'
                      f'<h2 class="section-title">{MESICE_NOM[month - 1]} {year}</h2>'
                      + '\n'.join(cards) + '</section>')
    if not blocks:
        blocks.append('<p class="empty">Žádné novinky za tento a minulý měsíc.</p>')
    blocks.append('<p class="empty" id="news-no-match" hidden>Nic se nenašlo. '
                  '<button type="button" id="clear-empty">Vymazat filtr</button></p>')
    blocks.append('<div class="archive-link"><a href="archive.html">Starší příspěvky v archivu →</a></div>')
    rendered = '\n'.join(blocks)
    page = re.sub(re.escape(start) + '.*?' + re.escape(end),
                  lambda _: start + '\n' + rendered + '\n' + end, page, flags=re.S)
    (Path(out) / 'index.html').write_text(page, encoding='utf-8')


def absolute_url(base, value):
    """Preserve remote HTTPS image URLs; resolve local paths once."""
    value = str(value or '').strip()
    result = urljoin(base.rstrip('/') + '/', value)
    return result if urlsplit(result).scheme in ('http', 'https') else ''


def image_alt(item):
    """Use editorial alt text when present; otherwise the existing image title."""
    return re.sub(r'\s+', ' ', str(item.get('alt') or item.get('title') or
                                   item.get('original_title') or 'Astronomický snímek')).strip()


def breadcrumb_data(canonical, title):
    parsed = urlsplit(canonical)
    base = f'{parsed.scheme}://{parsed.netloc}'
    parts = parsed.path.strip('/').split('/')
    labels = {'clanky': 'Přehled článků', 'temata': 'Rubriky',
              'obrazky': 'Obrázky', 'kosmopedie': 'Kosmopedie', 'pohledem-editora': 'Pohledem editora'}
    label = title.split(' – ')[0].split(' - Kosmopedie')[0]
    entries = [('Hlavní stránka', base + '/')]
    section = parts[0]
    if section in labels:
        entries.append((labels[section], base + '/' + section + '/'))
        if len(parts) > 1 and parts[-1] != 'index.html':
            entries.append((label, canonical))
    elif parsed.path not in ('/', '/index.html'):
        entries.append((label, canonical))
    if len(entries) < 2:
        return None
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i, 'name': name, 'item': url}
        for i, (name, url) in enumerate(entries, 1)]}


def navigation_html(canonical):
    """Derive the active section from this page's canonical path, not click history."""
    path = urlsplit(canonical).path
    active = None
    exact = False
    if path in ('/', '/index.html', '/archive.html'):
        active = '/index.html'
        exact = path != '/archive.html'
    elif path == '/images.html' or path.startswith('/obrazky/'):
        active = '/images.html'
        exact = path == '/images.html'
    elif path.startswith('/pohledem-editora/'):
        active, exact = '/clanky/', False
    elif path == '/contact.html':
        active, exact = '/contact.html', True
    else:
        for section in ('clanky', 'temata', 'kosmopedie'):
            prefix = '/' + section + '/'
            if path.rstrip('/') == '/' + section or path.startswith(prefix):
                active = prefix
                exact = path in (prefix, prefix + 'index.html', '/' + section)
                break
    links = [('/index.html', 'Novinky'), ('/clanky/', 'Přehled článků'),
             ('/temata/', 'Rubriky'), ('/kosmopedie/', 'Kosmopedie'),
             ('/images.html', 'Obrázky'), ('/contact.html', 'Kontakt'), ('/feed.xml', 'RSS')]
    rows = ['    <nav aria-label="Hlavní navigace">']
    for href, label in links:
        current = (' aria-current="' + ('page' if exact else 'location') + '"') if href == active else ''
        style = ' style="color:#f0b429"' if href == '/feed.xml' else ''
        rows.append(f'      <a href="{href}"{current}{style}>{label}</a>')
    rows.append('    </nav>')
    return '\n'.join(rows)


def search_title(title, limit=65):
    """Keep the HTML title concise; full headings and social titles stay intact."""
    text = " ".join(str(title or "").split())
    if len(text) <= limit:
        return text
    # Drop repeated branding before shortening the subject of the page.
    text = re.sub(r"\s+[–—-]\s+Kosmologické novinky$", "", text)
    if len(text) <= limit:
        return text
    cut = text[:limit - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:–—-") + "…"


def page_head(title, description, canonical, og_image=None, jsonld=None):
    base = canonical.split('/', 3)[:3]
    base = '/'.join(base)
    has_content_image = bool(og_image and not og_image.endswith('/assets/logo-icon-square.png'))
    share_image = absolute_url(base, og_image or '/assets/logo-icon-square.png')
    card = 'summary_large_image' if has_content_image else 'summary'
    article = bool(jsonld and jsonld.get('@type') in ('Article', 'NewsArticle'))
    og_type = 'article' if article else 'website'
    share_alt = ((jsonld.get('image') or {}).get('caption') if isinstance(jsonld.get('image'), dict) else None) or (jsonld.get('name') or title) if has_content_image and jsonld else 'Kosmologické novinky – logo webu'
    og = (f'<meta property="og:image" content="{esc(share_image)}">\n  '
          f'<meta property="og:image:alt" content="{esc(share_alt)}">\n  '
          '<meta property="og:locale" content="cs_CZ">\n  '
          f'<meta name="twitter:card" content="{card}">\n  '
          f'<meta name="twitter:title" content="{esc(title)}">\n  '
          f'<meta name="twitter:description" content="{esc(description)}">\n  '
          f'<meta name="twitter:image" content="{esc(share_image)}">\n  '
          f'<meta name="twitter:image:alt" content="{esc(share_alt)}">\n  ')
    nodes = []
    if jsonld:
        node = {k: v for k, v in jsonld.items() if k != '@context' and v not in (None, '')}
        if article:
            # A brand logo is not a picture of the subject of the article.
            if node.get('image') == base + '/assets/logo-icon-square.png':
                node.pop('image')
            node['url'] = canonical
            if (node.get('author') or {}).get('@type') != 'Person':
                node['author'] = {'@type': 'Organization', 'name': 'Kosmologické novinky', 'url': base + '/'}
            node['publisher'] = {'@type': 'Organization', 'name': 'Kosmologické novinky',
                                 'url': base + '/', 'logo': {'@type': 'ImageObject', 'url': base + '/assets/logo-icon-square.png'}}
            for key, tag in [('datePublished', 'article:published_time'), ('dateModified', 'article:modified_time')]:
                if node.get(key):
                    og += f'<meta property="{tag}" content="{esc(node[key])}">\n  '
        nodes.append(node)
    breadcrumb = breadcrumb_data(canonical, title)
    if breadcrumb:
        nodes.append(breadcrumb)
    ld = ''
    if nodes:
        graph = {'@context': 'https://schema.org', '@graph': nodes}
        # Prevent source text containing </script> from breaking out of JSON-LD.
        encoded = json.dumps(graph, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
        ld = f'<script type="application/ld+json">{encoded}</script>\n  '
    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(search_title(title))}</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="alternate" type="application/atom+xml" title="Kosmologické novinky – Atom feed" href="/feed.xml">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:type" content="{og_type}">
  <meta property="og:site_name" content="Kosmologické novinky">
  {og}<style>{CSS}</style>
  <link rel="stylesheet" href="/assets/article-previews.css">
  <link rel="stylesheet" href="/assets/navigation.css">
  <script defer src="/assets/analytics.js"></script>
  <script>{COUNTER_JS}</script>
  <script>{NEWSLETTER_FOCUS_JS}</script>
  {ld}</head>
<body>
  <header>
    <div class="logo-wrapper">
      <img src="/assets/logo-icon-square.png" alt="Kosmologické novinky" width="80" height="80">
      <div class="logo-text"><a href="/"><div class="site-name">Kosmologické novinky</div></a></div>
    </div>
    <p class="subtitle">Česky o kosmologii: temná hmota, černé díry, galaxie, reliktní záření, gravitační vlny, neutronové hvězdy a další.</p>
{navigation_html(canonical)}
{SIGNUP_FORM}  </header>
  <main>
"""


FOOT = """  </main>
</body>
</html>
"""



def build_newsletter_example(out, base, news):
    """Illustrative message, not an archive or proof of a sent newsletter."""
    pool = [item for item in news if item.get('lang') == 'cs' and item.get('title') and item.get('summary')]
    if not pool:
        pool = [item for item in news if item.get('title') and item.get('summary')
                and item.get('lang') != 'en' and not item.get('needs_translation')]
    # Pick different topics deterministically for a representative example.
    selected, themes = [], set()
    for item in pool:
        theme = classify(item)
        if theme in themes:
            continue
        selected.append(item); themes.add(theme)
        if len(selected) == 5:
            break
    for item in pool:
        if len(selected) == 5:
            break
        if item not in selected:
            selected.append(item)
    folder = Path(out) / 'newsletter'
    folder.mkdir(parents=True, exist_ok=True)
    url = base + '/newsletter/'
    page = page_head('Ukázka newsletteru – Kosmologické novinky',
                     'Podívejte se, jak může vypadat týdenní e-mail s českými souhrny novinek o vesmíru a odkazy do Kosmopedie.', url)
    page += ('<p class="breadcrumbs"><a href="/">Hlavní stránka</a> › Ukázka newsletteru</p>'
             '<article class="post"><h1>Takto může vypadat váš týdenní výběr</h1>'
             '<p class="summary">Ilustrační ukázka obsahu newsletteru. Nejde o archiv již odeslaného vydání; '
             'výběr se při aktualizaci webu může změnit. Vzhled e-mailu se může podle poštovní aplikace lišit.</p>')
    if selected:
        stamps = [parse_dt(item.get('inserted_at') or item.get('published')) for item in selected]
        dates = [stamp.date() for stamp in stamps if stamp]
        if dates:
            subject, body = newsletter_email(selected, min(dates), max(dates))
            page += '<p class="meta">Ukázkový předmět: ' + esc(subject) + '</p>'
            page += editorial.markdown(body)
        else:
            page += '<p>Ukázku připravujeme.</p>'
    else:
        page += '<p>Ukázku připravujeme.</p>'
    page += ('</article><p class="back"><a href="#bd-email">Chci dostávat týdenní výběr e-mailem ↑</a>'
             ' · <a href="/">Zpět na novinky</a></p>' + FOOT)
    (folder / 'index.html').write_text(page, encoding='utf-8')
    return (url, max(dates).isoformat() if selected and dates else datetime.now(timezone.utc).date().isoformat())


def gallery_neighbours(images, topic_ids):
    """Match gallery.js: separate collections, deduplicate and sort newest first."""
    neighbours = {}
    for thematic in (False, True):
        members = [img for img in images if (img['id'] in topic_ids) == thematic]
        def identity(img):
            return (img.get('catalog_image_id') or img['id']) if thematic else img['id']
        unique = {identity(img): img for img in members}
        ordered = sorted(unique.values(), key=lambda img: str(img.get('published') or ''), reverse=True)
        by_identity = {
            identity(img): (ordered[i - 1] if i else None,
                            ordered[i + 1] if i + 1 < len(ordered) else None)
            for i, img in enumerate(ordered)
        }
        for img in members:
            neighbours[img['_path']] = by_identity[identity(img)]
    return neighbours


def image_paging(previous, following):
    links = []
    for image, rel, label in ((previous, 'prev', '← Předchozí obrázek'),
                              (following, 'next', 'Následující obrázek →')):
        if image:
            links.append(f'<a class="{rel}" rel="{rel}" href="/{esc(image["_path"])}">'
                         f'<span class="meta">{label}</span><span>{esc(image.get("title"))}</span></a>')
    return ('<nav class="post-nav image-paging" aria-label="Procházení obrázků">' +
            ''.join(links) + '</nav>') if links else ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-dir", default=".")
    ap.add_argument("--out", default="_site")
    ap.add_argument("--base", default="https://kosmonovinky.cz")
    args = ap.parse_args()
    base = args.base.rstrip("/")
    site = Path(args.site_dir)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    news = json.loads((site / "data" / "news.json").read_text(encoding="utf-8"))
    kosmopedie = explainer_catalog(site)
    home_links = write_home_explainer_links(news, kosmopedie, out)
    image_library = prepare_images(site, download=False)
    images = []
    img_path = site / "data" / "images.json"
    if img_path.exists():
        images = json.loads(img_path.read_text(encoding="utf-8"))
    curated = []
    permanent_images = site / 'data' / 'kosmopedie_images.json'
    if permanent_images.exists():
        catalog = {e['id']: e for e in json.loads((site / 'data/article_image_catalog.json').read_text(encoding='utf-8'))}
        curated = json.loads(permanent_images.read_text(encoding='utf-8'))
        curated = complete_topic_gallery(curated, kosmopedie, image_library, catalog)
        (out / 'data').mkdir(parents=True, exist_ok=True)
        (out / 'data' / 'kosmopedie_images.json').write_text(json.dumps(curated, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        images = list({img['id']: img for img in images + curated}.values())
    news.sort(key=lambda x: x.get("inserted_at") or "", reverse=True)

    used_slugs = set()

    def unique_slug(text, item_id):
        base_slug = slugify(text)
        s = f"{base_slug}-{id_digits(item_id)}"
        n = 2
        while s in used_slugs:
            s = f"{base_slug}-{id_digits(item_id)}-{n}"
            n += 1
        used_slugs.add(s)
        return s

    # ---- přiřazení URL a rubrik ----
    for item in news:
        item["_slug"] = unique_slug(item.get("title", "clanek"), item.get("id"))
        item["_path"] = f"clanky/{item['_slug']}.html"
        item["_theme"] = classify(item)

    for img in images:
        img["_slug"] = unique_slug(img.get("title", "obrazek"), img.get("id"))
        img["_path"] = f"obrazky/{img['_slug']}.html"

    by_theme = {}
    for item in news:
        by_theme.setdefault(item["_theme"], []).append(item)

    editor_posts, urls = editorial.build(site, out, base, image_library, page_head, FOOT, fmt_date, article_footer=NEWSLETTER_CTA, description_formatter=truncate, feedback_renderer=feedback_link)

    write_gallery_context(site, out, images, news, kosmopedie, image_library, editor_posts)
    build_home_news(site, out, news, image_library, home_links)
    urls.append(build_newsletter_example(out, base, news))

    # ---- stránky novinek ----
    (out / "clanky").mkdir(exist_ok=True)
    for i, item in enumerate(news):
        theme_slug = item["_theme"]
        theme_label = THEME_LABEL.get(theme_slug, FALLBACK_THEME[1])
        url = f"{base}/{item['_path']}"
        summary = item.get("summary") or item.get("original_title") or item.get("title")
        description = truncate(summary)
        related = [r for r in by_theme.get(theme_slug, []) if r["_path"] != item["_path"]][:3]
        rel_html = ""
        if related:
            lis = "\n".join(f'          <li><a href="/{r["_path"]}">{esc(r.get("title"))}</a> <span class="meta">({fmt_date(r.get("published"))})</span></li>' for r in related)
            rel_html = f'''    <section class="related">
      <h2>Související novinky</h2>
      <ul>
{lis}
      </ul>
    </section>
'''
        context_html = explainer_links_html(item, kosmopedie)
        lang_note = ""
        if item.get("lang") == "en" or item.get("needs_translation"):
            lang_note = '<p class="lang-note">Anglický originál – český souhrn se nepodařilo vytvořit.</p>'
        nav_parts = []
        if i > 0:
            nav_parts.append(f'<a class="prev" href="/{news[i-1]["_path"]}">← Novější článek</a>')
        if i + 1 < len(news):
            nav_parts.append(f'<a class="next" href="/{news[i+1]["_path"]}">Starší článek →</a>')
        nav_html = '<nav class="post-nav">' + ''.join(nav_parts) + '</nav>' if nav_parts else ""
        article_image = lookup_image(item, "news", image_library)
        article_image_url = image_url(article_image, base)
        jsonld = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": item.get("title"),
            "description": description,
            "datePublished": item.get("published"),
            "dateModified": item.get("inserted_at") or item.get("published"),
            "inLanguage": "cs",
            "author": {"@type": "Organization", "name": item.get("source") or "Kosmologické novinky"},
            "publisher": {"@type": "Organization", "name": "Kosmologické novinky"},
            "mainEntityOfPage": url,
            "image": image_schema(article_image, base),
        }
        page = page_head(
            f'{item.get("title")} – Kosmologické novinky', description, url,
            og_image=article_image_url, jsonld=jsonld,
        )
        title_txt = esc(item.get("title"))
        crumb_title = title_txt if len(title_txt) <= 45 else title_txt[:45].rstrip() + "…"
        page += f'''    <p class="breadcrumbs"><a href="/">Hlavní stránka</a> › <a href="/temata/">Rubriky</a> › <a href="/temata/{theme_slug}.html">{esc(theme_label)}</a> › {crumb_title}</p>
    <article class="post">
      <div class="theme-badge"><a href="/temata/{theme_slug}.html">{esc(theme_label)}</a></div>
      <h1>{esc(item.get("title"))}</h1>
      <p class="meta">Publikováno: {fmt_date(item.get("published"))} · Zdroj: {esc(item.get("source"))}</p>
      {image_figure(article_image)}
      <p class="summary">{esc(summary)}</p>
{lang_note}      <a class="original-source" href="{esc(item.get("url"))}" target="_blank" rel="noopener">Původní zdroj →</a>
{context_html}{rel_html}{NEWSLETTER_CTA}{feedback_link(item.get('title'), url)}{nav_html}    </article>
        <p class="back"><a href="/clanky/">← Přehled článků</a> · <a href="/temata/">Rubriky</a></p>
'''
        page += FOOT
        (out / item["_path"]).write_text(page, encoding="utf-8")
        urls.append((url, fmt_iso_date(item.get("inserted_at") or item.get("published"))))

    # Index only published entries selected by the existing generators.
    search_entries = [dict(href=item['href'] if 'body' in item else '/' + item['_path'],
                           text=search_body(item)) for item in news + editor_posts]
    (out / 'data').mkdir(parents=True, exist_ok=True)
    (out / 'data' / 'article-search.json').write_text(
        json.dumps(search_entries, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    # ---- přehled všech článků ----
    groups = {}
    for item in sorted(news + editor_posts, key=lambda x: x.get("inserted_at") or x.get("published") or "", reverse=True):
        dt = parse_dt(item.get("inserted_at") or item.get("published"))
        key = f"{dt.year}-{dt.month:02d}" if dt else "0000-00"
        groups.setdefault(key, []).append(item)
    list_html = ""
    for key in sorted(groups, reverse=True):
        dt = parse_dt(groups[key][0].get("inserted_at") or groups[key][0].get("published"))
        label = f"{MESICE_NOM[dt.month - 1]} {dt.year}" if dt else key
        list_html += f'    <h2 class="section-title">{esc(label)}</h2>\n'
        for item in groups[key]:
            if "body" in item:
                list_html += editorial.card(item, fmt_date)
                continue
            list_html += (f'    <article class="item"><h2><a href="/{item["_path"]}">{esc(item.get("title"))}</a></h2>'
                          f'<p class="meta">{fmt_date(item.get("published"))} · {esc(item.get("source"))} · '
                          f'<a href="/temata/{item["_theme"]}.html">{esc(THEME_LABEL.get(item["_theme"], FALLBACK_THEME[1]))}</a></p>'
                          f'<div class="article-teaser">'
                          + thumbnail(lookup_image(item,"news",image_library),'/'+item['_path'])
                          + f'<p class="summary">{esc(article_perex(item))}</p></div><a href="/{item["_path"]}">Číst celý článek →</a></article>\n')
    idx = page_head("Přehled článků – Kosmologické novinky",
                    "Kompletní přehled českých souhrnů kosmologických studií a novinek: temná hmota, černé díry, gravitační vlny, galaxie a další.",
                    f"{base}/clanky/")
    editor_archive_link = '<p><a href="/pohledem-editora/">Pohledem editora — všechny komentáře Zdeňka Bubáka →</a></p>\n' if editor_posts else ""
    idx += f'''    <p class="breadcrumbs"><a href="/">Hlavní stránka</a> › Přehled článků</p>
    <h1 class="section-title" style="font-size:1.4rem;color:var(--text)">Přehled článků ({len(news) + len(editor_posts)})</h1>
    <p class="summary">Všechny články přehledně po měsících, nejnovější nahoře. Kliknutím na titulek otevřete celý text — výběr zúží fulltextové hledání níže.</p>
{collection_switch('articles', 'all')}{editor_archive_link}    <input type="search" id="clanky-search" class="search-box" placeholder="Hledat v článcích…" aria-label="Hledat v článcích">
    <p id="clanky-search-status" class="search-status" role="status" aria-live="polite"></p>
{list_html}    <script defer src="/assets/article-search.js"></script>
'''
    idx += FOOT
    (out / "clanky" / "index.html").write_text(idx, encoding="utf-8")
    urls.append((f"{base}/clanky/", fmt_iso_date(news[0].get("inserted_at") if news else None)))

    # ---- tematické rubriky ----
    (out / "temata").mkdir(exist_ok=True)
    theme_cards = ""
    all_themes = [(s, l) for s, l, _ in THEMES] + [FALLBACK_THEME]
    for slug, label in all_themes:
        items = by_theme.get(slug, [])
        if not items:
            continue
        url = f"{base}/temata/{slug}.html"
        cards = "".join(f'    <article class="item"><h2><a href="/{it["_path"]}">{esc(it.get("title"))}</a></h2>'
                        f'<p class="meta">{fmt_date(it.get("published"))} · {esc(it.get("source"))}</p>'
                        f'<div class="article-teaser">'
                        + thumbnail(lookup_image(it,"news",image_library),'/'+it['_path'])
                        + f'<p class="summary">{esc(article_perex(it))}</p></div><a href="/{it["_path"]}">Číst celý článek →</a></article>\n' for it in items)
        desc = f"Novinky a souhrny studií z oblasti: {label}. České vysvětlení nejnovějších poznatků kosmologie."
        page = page_head(f"{label} – rubrika – Kosmologické novinky", desc, url,
                         og_image=f"{base}/assets/logo-icon-square.png")
        page += f'''    <p class="breadcrumbs"><a href="/">Hlavní stránka</a> › <a href="/temata/">Rubriky</a> › {esc(label)}</p>
    <h1 class="section-title" style="font-size:1.4rem;color:var(--text)">{esc(label)} <span class="meta">({len(items)} článků)</span></h1>
{cards}'''
        page += FOOT
        (out / "temata" / f"{slug}.html").write_text(page, encoding="utf-8")
        urls.append((url, fmt_iso_date(items[0].get("inserted_at"))))
        theme_cards += (f'    <div class="theme-card"><a href="/temata/{slug}.html">{esc(label)}</a>'
                        f'<p class="count">{len(items)} článků</p></div>\n')
    tidx = page_head("Rubriky článků – Kosmologické novinky",
                     "Tematické rubriky kosmologických novinek: černé díry, temná hmota, gravitační vlny, exoplanety, galaxie a další.",
                     f"{base}/temata/")
    tidx += f'''    <p class="breadcrumbs"><a href="/">Hlavní stránka</a> › Rubriky článků</p>
    <h1 class="section-title" style="font-size:1.4rem;color:var(--text)">Rubriky článků</h1>
    <p class="summary">Vyberte si rubriku, nebo přejděte na přehled všech článků.</p>
    {collection_switch('articles', 'groups')}
    <div class="theme-grid">
{theme_cards}    </div>
'''
    tidx += FOOT
    (out / "temata" / "index.html").write_text(tidx, encoding="utf-8")
    urls.append((f"{base}/temata/", fmt_iso_date(news[0].get("inserted_at") if news else None)))

    # ---- stránky obrázků ----
    topic_image_ids = {img['id'] for img in curated}
    image_adjacent = gallery_neighbours(images, topic_image_ids)
    if images:
        (out / "obrazky").mkdir(exist_ok=True)
        gallery_items = ""
        for img in images:
            url = f"{base}/{img['_path']}"
            caption = img.get("caption") or img.get("title")
            description = truncate(caption)
            img_url = absolute_url(base, img.get("image") or img.get("thumb"))
            jsonld = {'@context': 'https://schema.org',
                      **gallery_image_schema(img, base, img_url),
                      'description': description}
            navigation = image_paging(*image_adjacent[img['_path']])
            gallery_back = '/images.html?galerie=temata' if img['id'] in topic_image_ids else '/images.html'
            gallery_back += '#img-' + quote(str(img['id']), safe='')
            catalog_image = image_library[1].get(img.get('catalog_image_id'))
            license_html = ''
            if catalog_image:
                jsonld.update(image_schema(catalog_image, base))
                license_html = (f'<p class="source-link">Licence: <a href="{esc(catalog_image["license_url"])}">'
                                f'{esc(catalog_image["license"])}</a> · {esc(catalog_image["modifications"])}</p>')
            else:
                rights_links = []
                if jsonld.get('license'):
                    rights_links.append(f'<a href="{esc(jsonld["license"])}">Podmínky použití obrázku</a>')
                if jsonld.get('acquireLicensePage'):
                    rights_links.append(f'<a href="{esc(jsonld["acquireLicensePage"])}">Informace k získání oprávnění</a>')
                if rights_links:
                    license_html = '<p class="source-link">' + ' · '.join(rights_links) + '</p>'
            page = page_head(f'{img.get("title")} – Obrázek – Kosmologické novinky', description, url,
                             og_image=img_url, jsonld=jsonld)
            page += f'''    <p class="breadcrumbs"><a href="/">Hlavní stránka</a> › <a href="/images.html">Galerie</a> › {esc(img.get("title"))}</p>
    <article class="post">
      <h1>{esc(img.get("title"))}</h1>
      <p class="meta">Zdroj: {esc(img.get("source"))} · {fmt_date(img.get("published"))}{" · Autor snímku: " + esc(img.get("credit")) if img.get("credit") else ""}</p>
      <figure>
        <img src="{esc(img_url)}" alt="{esc(image_alt(img))}" loading="lazy">
        <figcaption>{esc(caption)}</figcaption>
      </figure>
      <p class="source-link"><a class="original-source" href="{esc(img.get("url"))}" target="_blank" rel="noopener">Původní zdroj snímku →</a></p>
{license_html}
      {navigation}
      <p class="back"><a href="{esc(gallery_back)}">← Zpět do galerie</a></p>
    </article>
'''
            page += FOOT
            (out / img["_path"]).write_text(page, encoding="utf-8")
            urls.append((url, fmt_iso_date(img.get("inserted_at") or img.get("published"))))
            gallery_items += (f'    <article class="item"><h2><a href="/{img["_path"]}">{esc(img.get("title"))}</a></h2>'
                              f'<p class="meta">{fmt_date(img.get("published"))} · {esc(img.get("source"))}</p></article>\n')
        oidx = page_head("Všechny obrázky – Kosmologické novinky",
                         "Galerie astronomických snímků s českými popisky: NASA APOD a další zdroje.",
                         f"{base}/obrazky/")
        oidx += f'''    <p class="breadcrumbs"><a href="/">Hlavní stránka</a> › Obrázky</p>
    <h1 class="section-title" style="font-size:1.4rem;color:var(--text)">Všechny obrázky ({len(images)})</h1>
{gallery_items}'''
        oidx += FOOT
        (out / "obrazky" / "index.html").write_text(oidx, encoding="utf-8")
        urls.append((f"{base}/obrazky/", fmt_iso_date(images[0].get("inserted_at") if images else None)))

    # ---- statické stránky do sitemap ----
    for path in ("index.html", "archive.html", "images.html", "contact.html", "feed.xml"):
        p = out / path
        lm = fmt_iso_date(news[0].get("inserted_at") if news else None)
        if p.exists():
            import os
            lm = fmt_iso_date(datetime.fromtimestamp(os.path.getmtime(p), tz=timezone.utc).isoformat())
        urls.append((base + "/" if path == "index.html" else f"{base}/{path}", lm))

    # ---- robots.txt ----
    (out / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: " + base + "/sitemap.xml\n", encoding="utf-8")

    # ---- sitemap.xml ----
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lm in urls:
        sm.append(f"  <url><loc>{esc(loc)}</loc><lastmod>{lm}</lastmod></url>")
    sm.append("</urlset>")
    (out / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")

    # ---- Atom feed ----
    def atom_date(value):
        dt = parse_dt(value) or datetime(2026, 1, 1, tzinfo=timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    feed_items = news[:50]
    entries = []
    for item in feed_items:
        link = f"{base}/{item['_path']}"
        entries.append(f"""  <entry>
    <title>{esc(item.get('title'))}</title>
    <link href="{esc(link)}"/>
    <id>{esc(link)}</id>
    <updated>{atom_date(item.get('inserted_at') or item.get('published'))}</updated>
    <published>{atom_date(item.get('published'))}</published>
    <category term="{esc(THEME_LABEL.get(item['_theme'], FALLBACK_THEME[1]))}"/>
    <summary>{esc(truncate(item.get('summary') or '', 400))}</summary>
  </entry>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="cs">
  <title>Kosmologické novinky</title>
  <link href="{base}/" rel="alternate"/>
  <link href="{base}/feed.xml" rel="self"/>
  <id>{base}/</id>
  <updated>{atom_date(feed_items[0].get('inserted_at') if feed_items else None)}</updated>
  <subtitle>Česky o kosmologii: temná hmota, černé díry, galaxie, reliktní záření, gravitační vlny, neutronové hvězdy a další.</subtitle>
{chr(10).join(entries)}
</feed>
"""
    (out / "feed.xml").write_text(feed, encoding="utf-8")

    print(f"OK: {len(news)} článků, {len(images)} obrázků, {len(urls)} URL v sitemap")


if __name__ == "__main__":
    main()
