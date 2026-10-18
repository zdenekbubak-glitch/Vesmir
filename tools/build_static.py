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
import html
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

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
    ("vesmirne-teleskopy", "Vesmírné teleskopy", ["jwst", "james webb", "hubble", "euclid", "teleskop", "observatoř", "observatory", "kamera", "přístroj", "detektor"]),
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

CSS = """
    :root { --bg: #0b0f19; --card: #151b2d; --text: #e8eef7; --accent: #6ea8fe; --muted: #9aa8c7; }
    * { box-sizing: border-box; }
    body { font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; line-height: 1.55; }
    header { background: linear-gradient(135deg, #0f172a, #1e293b); padding: 1.8rem 1rem 1.5rem; text-align: center; border-bottom: 1px solid #1e293b; }
    a { color: var(--accent); text-decoration: none; }
    header a { color: inherit; text-decoration: none; }
    .logo-wrapper { display: flex; align-items: center; justify-content: center; gap: .9rem; margin-bottom: .5rem; }
    .logo-wrapper img { height: 80px; width: 80px; display: block; border-radius: 12px; }
    .logo-text h1 { margin: 0; font-size: 2rem; font-weight: 600; letter-spacing: -.02em; }
    .subtitle { color: var(--muted); margin: .35rem 0 1rem; font-size: .95rem; }
    nav { margin: .6rem 0 1.2rem; }
    nav a { color: var(--accent); margin: 0 .7rem; font-size: .95rem; }
    .signup-box { max-width: 720px; margin: 0 auto; background: rgba(21,27,45,.75); border: 1px solid #1e293b; border-radius: 10px; padding: .95rem 1.15rem; }
    .signup-box p { margin: 0 0 .65rem; font-size: .95rem; color: var(--muted); white-space: nowrap; }
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
    .lang-note { font-size: .85rem; color: #f0b429; }
    .source-link { display: inline-block; margin-top: .4rem; }
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
    .theme-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: .9rem; }
    .theme-card { background: var(--card); border: 1px solid #1e293b; border-radius: 10px; padding: 1rem 1.2rem; }
    .theme-card a { color: var(--accent); font-weight: 600; text-decoration: none; }
    .theme-card .count { color: var(--muted); font-size: .85rem; }
    .back { margin-top: 1.5rem; font-size: .9rem; }
    .post-nav { display: flex; justify-content: space-between; gap: 1rem; margin-top: 1.5rem; font-size: .95rem; }
    .post-nav .next { margin-left: auto; }
    .back a { color: var(--accent); }
    .search-box { width: 100%; padding: .35rem .85rem; margin: .6rem 0 1.2rem; border: 1px solid #1e293b; border-radius: 10px; background: var(--card); color: var(--text); font-size: .95rem; outline: none; }
    .search-box:focus { border-color: var(--accent); }
    .search-box::placeholder { color: #64748b; }
    @media (max-width: 520px) {
      .logo-wrapper { flex-direction: column; gap: 0.45rem; }
      .logo-wrapper img { height: 64px; width: 64px; }
      .logo-text h1 { font-size: 1.45rem; }
      .signup-box p { white-space: normal; }
    }
"""

COUNTER_JS = """
(function () {
  const body = JSON.stringify({ site: "vesmir", id: crypto.randomUUID() });
  async function odeslat() {
    try {
      const response = await fetch("https://ai-robotika-radar.zdenek-bubak.chatgpt.site/api/analytics/collect", {
        method: "POST", mode: "cors", credentials: "omit",
        headers: { "Content-Type": "application/json" }, body, keepalive: true
      });
      return response.ok;
    } catch { return false; }
  }
  odeslat().then(ok => { if (!ok) setTimeout(odeslat, 1500); });
})();
"""

SEARCH_JS = """
(function () {
  const box = document.getElementById('clanky-search');
  if (!box) return;
  box.addEventListener('input', function () {
    const q = this.value.toLowerCase();
    document.querySelectorAll('article.item').forEach(function (a) {
      a.style.display = a.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
    document.querySelectorAll('h2.section-title').forEach(function (h) {
      let el = h.nextElementSibling, any = false;
      while (el && el.tagName !== 'H2') {
        if (el.tagName === 'ARTICLE' && el.style.display !== 'none') any = true;
        el = el.nextElementSibling;
      }
      h.style.display = any ? '' : 'none';
    });
  });
})();
"""

SIGNUP_FORM = """
    <div class="signup-box">
      <p>Týdenní výběr editora: pět nejzajímavějších článků v plném znění.</p>
      <form action="https://buttondown.com/api/emails/embed-subscribe/zdenek" method="post" class="embeddable-buttondown-form signup-form">
        <label for="bd-email">E-mail pro týdenní výběr</label>
        <input type="email" name="email" id="bd-email" placeholder="tvuj@email.cz" required />
        <input type="submit" value="Odebírat" />
      </form>
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


def id_digits(item_id):
    return re.sub(r"[^0-9]", "", str(item_id))[:12] or "0"


def classify(item):
    text = " ".join(str(item.get(k) or "") for k in ("title", "summary", "original_title")).lower()
    for slug, _label, keywords in THEMES:
        if any(kw in text for kw in keywords):
            return slug
    return FALLBACK_THEME[0]


def page_head(title, description, canonical, og_image=None, jsonld=None):
    og = ""
    if og_image:
        og = f'<meta property="og:image" content="{esc(og_image)}">\n  '
    ld = ""
    if jsonld:
        ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>\n  '
    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="alternate" type="application/atom+xml" title="Kosmologické novinky – Atom feed" href="/feed.xml">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Kosmologické novinky">
  {og}<style>{CSS}</style>
  <script>{COUNTER_JS}</script>
  {ld}</head>
<body>
  <header>
    <div class="logo-wrapper">
      <img src="/assets/logo-icon-square.png" alt="Kosmologické novinky" width="80" height="80">
      <div class="logo-text"><a href="/"><h1>Kosmologické novinky</h1></a></div>
    </div>
    <p class="subtitle">Česky o kosmologii: temná hmota, černé díry, galaxie, reliktní záření, gravitační vlny, neutronové hvězdy a další.</p>
    <nav>
      <a href="/index.html">Novinky</a>
      <a href="/clanky/">Přehled článků</a>
      <a href="/temata/">Rubriky</a>
      <a href="/kosmopedie/">Kosmopedie</a>
      <a href="/images.html">Obrázky</a>
      <a href="/contact.html">Kontakt</a>
      <a href="/feed.xml" style="color:#f0b429">RSS</a>
    </nav>
{SIGNUP_FORM}  </header>
  <main>
"""


FOOT = """  </main>
</body>
</html>
"""


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
    images = []
    img_path = site / "data" / "images.json"
    if img_path.exists():
        images = json.loads(img_path.read_text(encoding="utf-8"))
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

    urls = []  # (loc, lastmod) pro sitemap

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
        lang_note = ""
        if item.get("lang") != "cs":
            lang_note = '<p class="lang-note">Anglický originál – český souhrn se nepodařilo vytvořit.</p>'
        nav_parts = []
        if i > 0:
            nav_parts.append(f'<a class="prev" href="/{news[i-1]["_path"]}">← Novější článek</a>')
        if i + 1 < len(news):
            nav_parts.append(f'<a class="next" href="/{news[i+1]["_path"]}">Starší článek →</a>')
        nav_html = '<nav class="post-nav">' + ''.join(nav_parts) + '</nav>' if nav_parts else ""
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
            "image": f"{base}/assets/logo-icon-square.png",
        }
        page = page_head(
            f'{item.get("title")} – Kosmologické novinky', description, url,
            og_image=f"{base}/assets/logo-icon-square.png", jsonld=jsonld,
        )
        title_txt = esc(item.get("title"))
        crumb_title = title_txt if len(title_txt) <= 45 else title_txt[:45].rstrip() + "…"
        page += f'''    <p class="breadcrumbs"><a href="/">Hlavní stránka</a> › <a href="/temata/">Rubriky</a> › <a href="/temata/{theme_slug}.html">{esc(theme_label)}</a> › {crumb_title}</p>
    <article class="post">
      <div class="theme-badge"><a href="/temata/{theme_slug}.html">{esc(theme_label)}</a></div>
      <h1>{esc(item.get("title"))}</h1>
      <p class="meta">Publikováno: {fmt_date(item.get("published"))} · Zdroj: {esc(item.get("source"))}</p>
      <p class="summary">{esc(summary)}</p>
{lang_note}      <a href="{esc(item.get("url"))}" target="_blank" rel="noopener">Původní zdroj →</a>
{nav_html}{rel_html}    </article>
        <p class="back"><a href="/clanky/">← Přehled článků</a> · <a href="/temata/">Rubriky</a></p>
'''
        page += FOOT
        (out / item["_path"]).write_text(page, encoding="utf-8")
        urls.append((url, fmt_iso_date(item.get("inserted_at") or item.get("published"))))

    # ---- přehled všech článků ----
    groups = {}
    for item in news:
        dt = parse_dt(item.get("inserted_at") or item.get("published"))
        key = f"{dt.year}-{dt.month:02d}" if dt else "0000-00"
        groups.setdefault(key, []).append(item)
    list_html = ""
    for key in sorted(groups, reverse=True):
        dt = parse_dt(groups[key][0].get("inserted_at"))
        label = f"{MESICE_NOM[dt.month - 1]} {dt.year}" if dt else key
        list_html += f'    <h2 class="section-title">{esc(label)}</h2>\n'
        for item in groups[key]:
            list_html += (f'    <article class="item"><h2><a href="/{item["_path"]}">{esc(item.get("title"))}</a></h2>'
                          f'<p class="meta">{fmt_date(item.get("published"))} · {esc(item.get("source"))} · '
                          f'<a href="/temata/{item["_theme"]}.html">{esc(THEME_LABEL.get(item["_theme"], FALLBACK_THEME[1]))}</a></p></article>\n')
    idx = page_head("Přehled článků – Kosmologické novinky",
                    "Kompletní přehled českých souhrnů kosmologických studií a novinek: temná hmota, černé díry, gravitační vlny, galaxie a další.",
                    f"{base}/clanky/")
    idx += f'''    <p class="breadcrumbs"><a href="/">Hlavní stránka</a> › Přehled článků</p>
    <h1 class="section-title" style="font-size:1.4rem;color:var(--text)">Přehled článků ({len(news)})</h1>
    <p class="summary">Všechny články přehledně po měsících, nejnovější nahoře. Kliknutím na titulek otevřete celý text — výběr zúží fulltextové hledání níže.</p>
    <input type="search" id="clanky-search" class="search-box" placeholder="Hledat v článcích…" aria-label="Hledat v článcích">
{list_html}    <script>{SEARCH_JS}</script>
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
                        f'<p class="meta">{fmt_date(it.get("published"))} · {esc(it.get("source"))}</p></article>\n' for it in items)
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
    tidx = page_head("Rubriky – Kosmologické novinky",
                     "Tematické rubriky kosmologických novinek: černé díry, temná hmota, gravitační vlny, exoplanety, galaxie a další.",
                     f"{base}/temata/")
    tidx += f'''    <p class="breadcrumbs"><a href="/">Hlavní stránka</a> › Rubriky</p>
    <h1 class="section-title" style="font-size:1.4rem;color:var(--text)">Rubriky</h1>
    <div class="theme-grid">
{theme_cards}    </div>
'''
    tidx += FOOT
    (out / "temata" / "index.html").write_text(tidx, encoding="utf-8")
    urls.append((f"{base}/temata/", fmt_iso_date(news[0].get("inserted_at") if news else None)))

    # ---- stránky obrázků ----
    if images:
        (out / "obrazky").mkdir(exist_ok=True)
        gallery_items = ""
        for img in images:
            url = f"{base}/{img['_path']}"
            caption = img.get("caption") or img.get("title")
            description = truncate(caption)
            img_url = f"{base}/{img.get('image') or img.get('thumb')}"
            jsonld = {
                "@context": "https://schema.org",
                "@type": "ImageObject",
                "name": img.get("title"),
                "description": description,
                "contentUrl": img_url,
                "datePublished": img.get("published"),
                "creditText": img.get("credit"),
            }
            page = page_head(f'{img.get("title")} – Obrázek – Kosmologické novinky', description, url,
                             og_image=img_url, jsonld=jsonld)
            page += f'''    <p class="breadcrumbs"><a href="/">Hlavní stránka</a> › <a href="/images.html">Galerie</a> › {esc(img.get("title"))}</p>
    <article class="post">
      <h1>{esc(img.get("title"))}</h1>
      <p class="meta">Zdroj: {esc(img.get("source"))} · {fmt_date(img.get("published"))}{" · Autor snímku: " + esc(img.get("credit")) if img.get("credit") else ""}</p>
      <figure>
        <img src="/{esc(img.get('image') or img.get('thumb'))}" alt="{esc(img.get('title'))}" loading="lazy">
        <figcaption>{esc(caption)}</figcaption>
      </figure>
      <p class="source-link"><a href="{esc(img.get("url"))}" target="_blank" rel="noopener">Původní zdroj snímku →</a></p>
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
        urls.append((f"{base}/{path}", lm))

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
