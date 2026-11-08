/* Shared search for published news and editorial comments; full text loads on demand. */
(() => {
  function normalized(value) {
    let text = '', starts = [], ends = [], offset = 0;
    for (const char of String(value || '')) {
      const part = char.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
      for (let i = 0; i < part.length; i++) { text += part[i]; starts.push(offset); ends.push(offset + char.length); }
      offset += char.length;
    }
    return {text, starts, ends};
  }
  function ranges(text, needle) {
    const n = normalized(text), result = [];
    if (!needle) return result;
    let i = 0;
    while ((i = n.text.indexOf(needle, i)) !== -1) {
      result.push([n.starts[i], n.ends[i + needle.length - 1]]); i += needle.length;
    }
    return result;
  }
  function highlightText(node, needle) {
    const text = node.textContent, hits = ranges(text, needle);
    if (!hits.length) return;
    const fragment = document.createDocumentFragment(); let at = 0;
    for (const [a, b] of hits) {
      fragment.append(document.createTextNode(text.slice(at, a)));
      const mark = document.createElement('mark'); mark.textContent = text.slice(a, b); fragment.append(mark); at = b;
    }
    fragment.append(document.createTextNode(text.slice(at))); node.replaceWith(fragment);
  }
  function highlight(root, needle) {
    const walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT); const nodes = [];
    while (walk.nextNode()) nodes.push(walk.currentNode);
    nodes.forEach(node => highlightText(node, needle));
  }
  function excerpt(text, needle) {
    const hit = ranges(text, needle)[0]; if (!hit) return '';
    let start = Math.max(0, hit[0] - 65), end = Math.min(text.length, Math.max(start + 180, hit[1] + 35));
    if (start) { const space = text.indexOf(' ', start); if (space >= start && space < hit[0]) start = space + 1; }
    if (end < text.length) { const space = text.lastIndexOf(' ', end); if (space >= hit[1]) end = space; }
    return (start ? '…' : '') + text.slice(start, end) + (end < text.length ? '…' : '');
  }
  const home = Boolean(document.getElementById('news-filter'));
  const box = document.getElementById(home ? 'news-filter' : 'clanky-search'); if (!box) return;
  const status = document.getElementById(home ? 'filter-meta' : 'clanky-search-status');
  const clearBtn = home ? document.getElementById('filter-clear') : null;
  const empty = home ? document.getElementById('news-no-match') : null;
  const nodes = home ? document.querySelectorAll('#feed article.post, main > article.editorial-card') : document.querySelectorAll('article.item');
  const cards = Array.from(nodes).map(card => {
    const link = card.querySelector('h2 a');
    // Search content only, excluding credits, navigation and unrelated links.
    const lead = [card.querySelector('h2'), ...card.querySelectorAll('.summary')].filter(Boolean);
    return {card, href: link ? new URL(link.href, location.href).pathname : '', original: card.innerHTML,
      searchOnly: home && card.hasAttribute('data-search-only'), editorial: card.classList.contains('editorial-card'),
      visible: lead.map(el => normalized(el.textContent).text)};
  });
  let index = null, pending = null, generation = 0, timer;
  function reset() { cards.forEach(r => {r.card.innerHTML = r.original; r.card.hidden = r.searchOnly;}); }
  function headings() {
    if (home) {
      document.querySelectorAll('#feed .news-month').forEach(group => {
        group.hidden = !Array.from(group.querySelectorAll('article.post')).some(card => !card.hidden);
      });
    } else {
      document.querySelectorAll('h2.section-title').forEach(h => {
        let el = h.nextElementSibling, any = false;
        while (el && el.tagName !== 'H2') { if (el.matches('article.item') && !el.hidden) any = true; el = el.nextElementSibling; }
        h.hidden = !any;
      });
    }
  }
  function load() {
    if (!pending) pending = fetch('/data/article-search.json', {cache: 'no-cache'}).then(async r => {
      if (!r.ok) throw Error('Search index unavailable');
      const data = await r.json(); if (!Array.isArray(data)) throw Error('Invalid search index');
      index = new Map(data.filter(r => typeof r.href === 'string' && typeof r.text === 'string').map(r => [r.href, r.text]));
    }).catch(e => {pending = null; throw e;});
    return pending;
  }
  function countText() {
    const comments = cards.filter(r => r.editorial && !r.card.hidden).length;
    const articles = cards.filter(r => !r.editorial && !r.card.hidden).length;
    return (home ? 'Novinky: ' : 'Články: ') + articles + ' · Komentáře: ' + comments;
  }
  function updateUrl(q) {
    if (!home) return;
    try { const url = new URL(location.href); if (q) url.searchParams.set('q', q); else url.searchParams.delete('q'); history.replaceState(null, '', url.pathname + url.search + url.hash); } catch {}
  }
  function filter(needle, full) {
    let count = 0;
    cards.forEach(r => {
      const text = full ? index.get(r.href) || '' : '';
      const match = r.visible.some(value => value.includes(needle)) || normalized(text).text.includes(needle);
      r.card.hidden = !match; if (!match) return; count++;
      const title = r.card.querySelector('h2'), summaries = Array.from(r.card.querySelectorAll('.summary'));
      const lead = [title, ...summaries].filter(Boolean);
      const inLead = lead.some(el => normalized(el.textContent).text.includes(needle));
      lead.forEach(el => highlight(el, needle));
      if (full && !inLead && normalized(text).text.includes(needle)) {
        const p = document.createElement('p'); p.className = 'search-excerpt'; p.textContent = excerpt(text, needle); highlight(p, needle);
        const teaser = r.card.querySelector('.article-teaser'); (teaser || summaries.at(-1) || title).after(p);
      }
    });
    headings(); if (empty) empty.hidden = count !== 0;
    return count;
  }
  async function apply() {
    const version = ++generation, q = box.value.trim(), needle = normalized(q).text;
    reset(); updateUrl(q);
    if (clearBtn) clearBtn.style.display = q ? 'inline-flex' : 'none';
    if (!needle) { headings(); if (empty) empty.hidden = true; status.textContent = home ? countText() : ''; return; }
    // Keep only matching leads visible while waiting for the full-text index.
    filter(needle, false);
    status.textContent = 'Načítám hledání v celých textech…';
    try {if (!index) await load();} catch {
      if (version !== generation) return;
      status.textContent = 'Celé texty se nepodařilo načíst. Zobrazeny jsou shody v titulcích a perexech; zkuste hledání znovu.';
      return;
    }
    if (version !== generation) return;
    reset(); const count = filter(needle, true);
    status.textContent = count ? countText() : (home ? 'Žádná novinka ani komentář neodpovídá hledanému textu.' : 'Žádný článek ani komentář neodpovídá hledanému textu.');
  }
  function clear() { box.value = ''; clearTimeout(timer); apply(); box.focus(); }
  box.addEventListener('input', () => {generation++; clearTimeout(timer); timer = setTimeout(apply, 150);});
  box.addEventListener('keydown', e => {if (e.key === 'Escape') {e.preventDefault(); clear();}});
  if (home) {
    const bar = document.getElementById('filter-bar'); bar.hidden = false; bar.style.display = 'block';
    if (clearBtn) clearBtn.addEventListener('click', clear);
    const clearEmpty = document.getElementById('clear-empty'); if (clearEmpty) clearEmpty.addEventListener('click', clear);
    box.value = new URLSearchParams(location.search).get('q') || '';
    window.addEventListener('popstate', () => {box.value = new URLSearchParams(location.search).get('q') || ''; apply();});
  }
  apply();
})();
