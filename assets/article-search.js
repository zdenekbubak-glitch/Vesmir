/* Full text of published articles only; fetched on first search. */
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
  // Pure helpers are also used by regression checks; nothing is attached globally.
  const box = document.getElementById('clanky-search'); if (!box) return;
  const status = document.getElementById('clanky-search-status');
  const cards = Array.from(document.querySelectorAll('article.item')).map(card => {
    const link = card.querySelector('h2 a');
    // Search article content only; image credits, licenses and navigation are not content.
    const lead = ['h2', '.summary'].map(selector => {
      const el = card.querySelector(selector); return el ? el.textContent : '';
    });
    return {card, href: link ? new URL(link.href, location.href).pathname : '', original: card.innerHTML, visible: lead.map(value => normalized(value).text)};
  });
  let index = null, pending = null, generation = 0, timer;
  function reset() { cards.forEach(r => {r.card.innerHTML = r.original; r.card.hidden = false;}); }
  function headings() {
    document.querySelectorAll('h2.section-title').forEach(h => {
      let el = h.nextElementSibling, any = false;
      while (el && el.tagName !== 'H2') { if (el.matches('article.item') && !el.hidden) any = true; el = el.nextElementSibling; }
      h.hidden = !any;
    });
  }
  function load() {
    if (!pending) pending = fetch('/data/article-search.json', {cache: 'no-cache'}).then(async r => {
      if (!r.ok) throw Error('Search index unavailable');
      const data = await r.json(); if (!Array.isArray(data)) throw Error('Invalid search index');
      index = new Map(data.filter(r => typeof r.href === 'string' && typeof r.text === 'string').map(r => [r.href, r.text]));
    }).catch(e => {pending = null; throw e;});
    return pending;
  }
  async function apply() {
    const version = ++generation, q = box.value.trim(), needle = normalized(q).text;
    reset();
    if (!needle) {headings(); status.textContent = ''; return;}
    status.textContent = 'Načítám hledání v celých textech…';
    try {if (!index) await load();} catch {
      if (version !== generation) return;
      status.textContent = 'Celé texty se nepodařilo načíst. Zobrazeny jsou shody v titulcích a perexech; zkuste hledání znovu.';
      filter(needle, false); return;
    }
    if (version !== generation) return;
    const count = filter(needle, true);
    status.textContent = count ? count + ' z ' + cards.length + ' článků' : 'Žádný článek neodpovídá hledanému textu.';
  }
  function filter(needle, full) {
    let count = 0;
    cards.forEach(r => {
      const text = full ? index.get(r.href) || '' : '', inCard = r.visible.some(value => value.includes(needle));
      const match = inCard || normalized(text).text.includes(needle);
      r.card.hidden = !match; if (!match) return; count++;
      const title = r.card.querySelector('h2'), perex = r.card.querySelector('.summary');
      const inLead = [title, perex].some(el => el && normalized(el.textContent).text.includes(needle));
      [title, perex].filter(Boolean).forEach(el => highlight(el, needle));
      if (full && !inLead && normalized(text).text.includes(needle)) {
        const p = document.createElement('p'); p.className = 'search-excerpt'; p.textContent = excerpt(text, needle); highlight(p, needle);
        const teaser = r.card.querySelector('.article-teaser'); (teaser || perex || title).after(p);
      }
    });
    headings(); return count;
  }
  box.addEventListener('input', () => {generation++; clearTimeout(timer); timer = setTimeout(apply, 150);});
  box.addEventListener('keydown', e => {if (e.key === 'Escape') {box.value = ''; clearTimeout(timer); apply();}});
  if (box.value.trim()) apply();
})();

