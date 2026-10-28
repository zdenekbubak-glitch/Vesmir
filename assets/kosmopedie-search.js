/* Kosmopedie: own article text only; no image credits, bibliography or navigation. */
(() => {
  'use strict';

  function normalized(value) {
    let text = '', starts = [], ends = [], offset = 0;
    for (const char of String(value || '')) {
      let part = char.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
      if (/\s/.test(char)) part = ' ';
      if (!part && starts.length && /[\u0300-\u036f]/.test(char)) ends[ends.length - 1] = offset + char.length;
      for (let i = 0; i < part.length; i++) {
        if (part[i] === ' ' && text.endsWith(' ')) { ends[ends.length - 1] = offset + char.length; continue; }
        text += part[i]; starts.push(offset); ends.push(offset + char.length);
      }
      offset += char.length;
    }
    return {text, starts, ends};
  }

  function ranges(value, needle) {
    if (!needle) return [];
    const folded = normalized(value), hits = [];
    let at = 0;
    while ((at = folded.text.indexOf(needle, at)) !== -1) {
      hits.push([folded.starts[at], folded.ends[at + needle.length - 1]]);
      at += needle.length;
    }
    return hits;
  }

  // Search a whole paragraph, including phrases spanning <strong> or <a> nodes.
  function highlight(root, needle) {
    const walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT), nodes = [];
    let value = '';
    while (walk.nextNode()) {
      const node = walk.currentNode;
      nodes.push({node, start: value.length}); value += node.textContent;
    }
    const hits = ranges(value, needle);
    if (!hits.length) return 0;
    for (const {node, start} of nodes) {
      const text = node.textContent, end = start + text.length;
      const overlaps = hits.filter(([a, b]) => a < end && b > start);
      if (!overlaps.length) continue;
      const fragment = document.createDocumentFragment(); let at = 0;
      for (const [a, b] of overlaps) {
        const left = Math.max(0, a - start), right = Math.min(text.length, b - start);
        fragment.append(document.createTextNode(text.slice(at, left)));
        const mark = document.createElement('mark'); mark.textContent = text.slice(left, right);
        fragment.append(mark); at = right;
      }
      fragment.append(document.createTextNode(text.slice(at))); node.replaceWith(fragment);
    }
    return hits.length;
  }

  function excerpt(text, needle) {
    const hit = ranges(text, needle)[0]; if (!hit) return '';
    let start = Math.max(0, hit[0] - 65), end = Math.min(text.length, Math.max(start + 180, hit[1] + 35));
    if (start) { const space = text.indexOf(' ', start); if (space >= start && space < hit[0]) start = space + 1; }
    if (end < text.length) { const space = text.lastIndexOf(' ', end); if (space >= hit[1]) end = space; }
    return (start ? '…' : '') + text.slice(start, end) + (end < text.length ? '…' : '');
  }

  function query() { return (new URL(location.href).searchParams.get('q') || '').slice(0, 200).trim(); }
  function setQuery(url, value) {
    if (value) url.searchParams.set('q', value); else url.searchParams.delete('q');
    return url.pathname + url.search + url.hash;
  }
  function linkQuery(link, value) {
    link.setAttribute('href', setQuery(new URL(link.getAttribute('href'), location.href), value));
  }

  const box = document.getElementById('kosmopedie-search');
  if (!box) {
    const detail = document.querySelector('article.post'), q = query(), needle = normalized(q).text;
    if (!detail || !needle || !document.getElementById('kosmopedie-detail-search-status')) return;
    let count = 0;
    detail.querySelectorAll('[data-search-block]').forEach(block => { count += highlight(block, needle); });
    const status = document.getElementById('kosmopedie-detail-search-status');
    status.hidden = false;
    const label = count === 1 ? 'shoda' : count >= 2 && count <= 4 ? 'shody' : 'shod';
    status.append(document.createTextNode(count ? `Hledaný výraz „${q}“: ${count} ${label} v tématu. ` : `Výraz „${q}“ v tomto tématu nenalezen. `));
    const clear = document.createElement('a'); clear.textContent = 'Zrušit zvýraznění';
    clear.href = setQuery(new URL(location.href), ''); status.append(clear);
    document.querySelectorAll('[data-topic-neighbour], [data-search-back]').forEach(link => linkQuery(link, q));
    const back = document.querySelector('.back [data-search-back]');
    if (back) back.textContent = '← Výsledky hledání v Kosmopedii';
    const first = detail.querySelector('mark');
    if (first && !location.hash) requestAnimationFrame(() => first.scrollIntoView({block: 'center'}));
    return;
  }

  const status = document.getElementById('kosmopedie-search-status');
  const cards = Array.from(document.querySelectorAll('#kosmopedie-topics article.item')).map(card => {
    const title = card.querySelector('h2'), perex = card.querySelector('.summary'), link = card.querySelector('h2 a');
    return {card, original: card.innerHTML, href: new URL(link.href, location.href).pathname,
      title: normalized(title.textContent).text, perex: normalized(perex ? perex.textContent : '').text};
  });
  let index = null, pending = null, generation = 0, timer;

  // Group navigation uses real anchor URLs; without JavaScript the full list remains readable.
  const groupGrid = document.getElementById('kosmopedie-groups');
  const topicList = document.getElementById('kosmopedie-topics');
  const groupBack = document.getElementById('kosmopedie-group-back');
  const sections = Array.from(document.querySelectorAll('.explainer-group'));
  function selectedGroup() {
    let hash;
    try { hash = decodeURIComponent(location.hash.slice(1)); } catch { return ''; }
    if (hash === 'temna-dira-v-centru') hash = 'cerne-diry';
    return sections.some(g => g.dataset.topicGroupSection === hash) ? hash : '';
  }
  function groups() {
    const searching = Boolean(box.value.trim()), selected = selectedGroup();
    const all = new URL(location.href).searchParams.get('view') === 'all';
    const showCards = !searching && !selected && !all;
    if (groupGrid) groupGrid.hidden = !showCards;
    if (topicList) topicList.hidden = showCards;
    if (groupBack) groupBack.hidden = !selected || searching;
    sections.forEach(group => {
      const matches = Array.from(group.querySelectorAll('article.item')).some(card => !card.hidden);
      group.hidden = !matches || (!searching && selected && group.dataset.topicGroupSection !== selected);
    });
    document.querySelectorAll('[data-collection-view]').forEach(link => {
      const current = link.dataset.collectionView === ((searching || (!selected && all)) ? 'all' : 'groups');
      if (current) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
    });
  }
  function navigate(event, mode, hash = '') {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    const url = new URL(location.href);
    url.searchParams.delete('q'); url.hash = hash;
    if (mode === 'all') url.searchParams.set('view', 'all'); else url.searchParams.delete('view');
    history.pushState(null, '', url.pathname + url.search + url.hash);
    box.value = ''; clearTimeout(timer); apply();
    if (hash) {
      const heading = document.getElementById(hash);
      if (heading) { heading.tabIndex = -1; heading.focus({preventScroll: true}); heading.scrollIntoView({block: 'start'}); }
    } else {
      // The clicked control may have disappeared together with its card grid.
      const heading = document.getElementById('kosmopedie-groups-heading');
      if (mode === 'groups' && heading) { heading.tabIndex = -1; heading.focus({preventScroll: true}); }
    }
  }
  document.querySelectorAll('[data-collection-view]').forEach(link => {
    link.addEventListener('click', event => navigate(event, link.dataset.collectionView));
  });
  document.querySelectorAll('#kosmopedie-groups a[data-topic-group]').forEach(link => {
    link.addEventListener('click', event => navigate(event, 'groups', link.dataset.topicGroup));
  });
  if (topicList) topicList.addEventListener('click', event => {
    const link = event.target.closest('a[data-topic-group]');
    if (link) navigate(event, 'groups', link.dataset.topicGroup);
  });
  document.querySelectorAll('[data-show-groups]').forEach(link => {
    link.addEventListener('click', event => navigate(event, 'groups'));
  });
  function reset() { cards.forEach(r => { r.card.innerHTML = r.original; r.card.hidden = false; }); }
  function load() {
    if (!pending) pending = fetch('/data/kosmopedie-search.json', {cache: 'no-cache'}).then(async response => {
      if (!response.ok) throw Error('Search index unavailable');
      const data = await response.json(); if (!Array.isArray(data)) throw Error('Invalid search index');
      index = new Map(data.filter(r => typeof r.href === 'string' && Array.isArray(r.blocks)).map(r => [r.href,
        r.blocks.filter(b => typeof b === 'string').map(text => ({text, folded: normalized(text).text}))]));
    }).catch(error => { pending = null; throw error; });
    return pending;
  }
  function filter(needle, q, full) {
    let count = 0;
    for (const r of cards) {
      const lead = r.title.includes(needle) || r.perex.includes(needle);
      const block = full ? (index.get(r.href) || []).find(b => b.folded.includes(needle)) : null;
      r.card.hidden = !(lead || block); if (r.card.hidden) continue; count++;
      const title = r.card.querySelector('h2'), perex = r.card.querySelector('.summary');
      [title, perex].filter(Boolean).forEach(element => highlight(element, needle));
      if (!lead && block) {
        const paragraph = document.createElement('p'); paragraph.className = 'search-excerpt';
        paragraph.textContent = excerpt(block.text, needle); highlight(paragraph, needle);
        (r.card.querySelector('.article-teaser') || perex || title).after(paragraph);
      }
      r.card.querySelectorAll('h2 a, .article-preview > a').forEach(link => linkQuery(link, q));
    }
    groups(); return count;
  }
  async function apply() {
    const version = ++generation, q = box.value.slice(0, 200).trim(), needle = normalized(q).text;
    reset(); history.replaceState(null, '', setQuery(new URL(location.href), q));
    if (!needle) { groups(); status.textContent = ''; return; }
    groups();
    status.textContent = 'Načítám hledání v celých textech…';
    try { if (!index) await load(); } catch {
      if (version !== generation) return;
      filter(needle, q, false);
      status.textContent = 'Celé texty se nepodařilo načíst. Zobrazeny jsou shody v názvech a perexech; zkuste hledání znovu.';
      return;
    }
    if (version !== generation) return;
    const count = filter(needle, q, true);
    status.textContent = count ? `Nalezeno ${count} z ${cards.length} témat.` : 'Žádné téma neodpovídá hledanému textu.';
  }
  box.addEventListener('input', () => { generation++; clearTimeout(timer); timer = setTimeout(apply, 150); });
  box.addEventListener('keydown', event => {
    if (event.key === 'Escape') { box.value = ''; clearTimeout(timer); apply(); }
    if (event.key === 'Enter') { event.preventDefault(); clearTimeout(timer); apply(); }
  });
  window.addEventListener('popstate', () => { box.value = query(); clearTimeout(timer); apply(); });
  box.value = query() || box.value.slice(0, 200);
  window.addEventListener('hashchange', () => { clearTimeout(timer); apply(); });
  apply();
})();
