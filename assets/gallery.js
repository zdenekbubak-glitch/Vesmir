/* Two separate curated galleries; no filename-based image-type inference. */
(() => {
  'use strict';
  const gallery = document.getElementById('gallery');
  if (!gallery) return;
  const input = document.getElementById('img-filter');
  const clear = document.getElementById('img-filter-clear');
  const type = document.getElementById('gallery-type');
  const use = document.getElementById('gallery-use');
  const status = document.getElementById('img-filter-meta');
  const descriptions = {
    snimky: 'Pravidelný výběr vesmírných obrázků z NASA APOD, Hubblea, Webba a dalších veřejných zdrojů.',
    temata: 'Vybrané obrázky a názorná schémata k výkladům. Typ a použití můžete zúžit filtry; odkazy vedou k souvisejícím tématům a článkům.'
  };
  const labels = {snimek: 'Snímek', ilustrace: 'Ilustrace', schema: 'Schéma nebo graf'};
  const cache = new Map();
  let context = {}, contextReady = false, branch = 'snimky', records = [], version = 0;
  function fold(s) { return String(s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, ''); }
  function node(tag, text, cls) {
    const el = document.createElement(tag); if (text) el.textContent = text; if (cls) el.className = cls; return el;
  }
  function safeUrl(value) {
    if (!value) return '';
    try { const u = new URL(value, location.href); return ['https:', 'http:'].includes(u.protocol) ? u.href : ''; } catch { return ''; }
  }
  function anchor(text, url, external = false) {
    const a = node('a', text); a.href = url;
    if (external) { a.target = '_blank'; a.rel = 'noopener noreferrer'; } return a;
  }
  async function fetchJson(url) {
    const response = await fetch(url, {cache: 'no-cache'});
    if (!response.ok) throw Error('Soubor galerie se nepodařilo načíst.');
    return response.json();
  }
  async function itemsFor(key) {
    if (!cache.has(key)) {
      const path = key === 'temata' ? '/data/kosmopedie_images.json' : '/data/images.json';
      const data = await fetchJson(path); if (!Array.isArray(data)) throw Error('Neplatný formát galerie.');
      const unique = new Map();
      data.forEach(item => { if (item && item.id) unique.set(key === 'temata' ? (item.catalog_image_id || item.id) : item.id, item); });
      cache.set(key, [...unique.values()].sort((a, b) => String(b.published || '').localeCompare(String(a.published || ''))));
    }
    return cache.get(key);
  }
  function locationState() {
    const u = new URL(location.href);
    return {branch: u.searchParams.get('galerie') === 'temata' ? 'temata' : 'snimky',
      q: (u.searchParams.get('q') || '').slice(0, 200),
      type: ['snimek', 'ilustrace', 'schema'].includes(u.searchParams.get('typ')) ? u.searchParams.get('typ') : '',
      use: ['kosmopedie', 'clanky'].includes(u.searchParams.get('pouziti')) ? u.searchParams.get('pouziti') : ''};
  }
  function writeState(push = false) {
    const u = new URL(location.href);
    for (const [key, value] of [['galerie', branch === 'temata' ? 'temata' : ''], ['q', input.value.trim()],
      ['typ', branch === 'temata' ? type.value : ''], ['pouziti', branch === 'temata' ? use.value : '']]) {
      if (value) u.searchParams.set(key, value); else u.searchParams.delete(key);
    }
    try { history[push ? 'pushState' : 'replaceState'](null, '', u.pathname + u.search + u.hash); } catch {}
  }
  function relatedLinks(figure, refs) {
    if (!refs.length) return;
    const area = node('div', '', 'gallery-related'); area.append(node('span', 'Související výklad:'));
    const list = node('ul');
    for (const ref of refs.slice(0, 3)) {
      const li = node('li'); li.append(anchor(ref.title, safeUrl(ref.href))); list.append(li);
    }
    area.append(list);
    if (refs.length > 3) {
      const details = node('details'); details.append(node('summary', `Další související texty (${refs.length - 3})`));
      const more = node('ul');
      refs.slice(3).forEach(ref => { const li = node('li'); li.append(anchor(ref.title, safeUrl(ref.href))); more.append(li); });
      details.append(more); area.append(details);
    }
    figure.append(area);
  }
  function render(items) {
    gallery.replaceChildren(); records = [];
    if (branch === 'temata' && !contextReady) gallery.append(node('p', 'Odkazy k použití obrázků se nepodařilo načíst. Obrázky a filtr typu zůstávají dostupné.', 'gallery-notice'));
    for (const item of items) {
      const meta = context[item.id] || {}, kind = item.gallery_type || meta.type || '';
      const refs = (Array.isArray(meta.related) ? meta.related : []).filter(r => r && safeUrl(r.href));
      if (!refs.length && branch === 'temata' && item.url && new URL(safeUrl(item.url) || location.href).pathname.startsWith('/kosmopedie/')) {
        refs.push({kind: 'kosmopedie', title: 'Otevřít související téma Kosmopedie', href: item.url});
      }
      const figure = node('figure', '', 'figure'); figure.id = 'img-' + item.id;
      const src = safeUrl(item.image || item.thumb || ('/assets/gallery/' + encodeURIComponent(item.id) + '.jpg'));
      const image = node('img'); image.src = src; image.alt = item.alt || item.title || item.original_title || 'Obrázek vesmíru';
      image.loading = 'lazy'; image.decoding = 'async';
      image.addEventListener('error', () => { image.hidden = true; figure.prepend(node('p', 'Náhled se nepodařilo načíst. Použijte odkaz na detail nebo zdroj.', 'gallery-notice')); }, {once: true});
      const detail = safeUrl(meta.detail);
      if (detail) { const a = anchor('', detail); a.append(image); figure.append(a); } else figure.append(image);
      const h = node('h2'); if (detail) h.append(anchor(item.title || '', detail)); else h.textContent = item.title || ''; figure.append(h);
      if (branch === 'temata') figure.append(node('span', item.gallery_type_label || labels[kind] || 'Typ dosud nezařazen', 'image-type'));
      figure.append(node('div', [item.source, item.published, item.credit].filter(Boolean).join(' · '), 'meta'));
      figure.append(node('p', item.caption || '', 'caption'));
      if (item.license_url && safeUrl(item.license_url)) {
        const p = node('p', 'Licence: ', 'meta'); p.append(anchor(item.license || 'Podmínky použití', safeUrl(item.license_url), true));
        if (item.modifications) p.append(document.createTextNode(' · ' + item.modifications)); figure.append(p);
      }
      if (branch === 'temata') relatedLinks(figure, refs);
      const source = safeUrl(branch === 'snimky' ? item.url : (meta.source_url || item.url));
      if (source && source !== new URL('/', location.href).href) {
        figure.append(anchor(branch === 'temata' && new URL(source).pathname.startsWith('/kosmopedie/') ? 'Výklad v Kosmopedii →' : 'Původní zdroj →', source, true));
      }
      gallery.append(figure);
      records.push({figure, kind, refs, text: fold([item.title, item.original_title, item.caption, item.credit, item.source, ...(item.gallery_keywords || []), ...refs.map(r => r.title)].join(' '))});
    }
    const empty = node('p', 'Žádný obrázek neodpovídá zvoleným filtrům.', 'empty'); empty.id = 'gallery-empty'; empty.hidden = true; gallery.append(empty);
  }
  function filter(update = true) {
    const q = fold(input.value.trim()); let count = 0;
    for (const r of records) {
      r.figure.hidden = !(r.text.includes(q) && (branch !== 'temata' || ((!type.value || r.kind === type.value) && (!use.value || r.refs.some(x => x.kind === use.value)))));
      if (!r.figure.hidden) count++;
    }
    const empty = document.getElementById('gallery-empty'); if (empty) empty.hidden = count !== 0;
    status.textContent = `${count} z ${records.length} obrázků`;
    clear.style.display = input.value ? 'inline-flex' : 'none'; if (update) writeState();
  }
  async function load(state = locationState(), findHash = true) {
    const token = ++version; branch = state.branch;
    document.querySelectorAll('[data-gallery]').forEach(a => { if (a.dataset.gallery === branch) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
    document.getElementById('gallery-topic-filters').hidden = branch !== 'temata';
    document.getElementById('gallery-description').textContent = descriptions[branch];
    input.value = state.q; type.value = state.type; use.value = state.use;
    gallery.replaceChildren(node('p', 'Načítám galerii…', 'empty')); status.textContent = '';
    try {
      const [items] = await Promise.all([itemsFor(branch), contextReady ? Promise.resolve() : fetchJson('/data/gallery-context.json').then(data => {
        if (!data || Array.isArray(data) || typeof data !== 'object') throw Error(); context = data; contextReady = true;
      }).catch(() => {})]);
      if (token !== version) return;
      // Existing image anchors can point into either collection.
      let id = ''; try { id = decodeURIComponent(location.hash.slice(1)); } catch {}
      if (findHash && id.startsWith('img-') && !items.some(i => 'img-' + i.id === id)) {
        const other = branch === 'temata' ? 'snimky' : 'temata';
        try {
          const alternatives = await itemsFor(other); if (token !== version) return;
          if (alternatives.some(i => 'img-' + i.id === id)) { await load({branch: other, q: '', type: '', use: ''}, false); return; }
        } catch {}
      }
      render(items);
      use.disabled = !contextReady;
      if (!contextReady) use.value = '';
      document.getElementById('img-filter-bar').style.display = 'block';
      if (id.startsWith('img-') && items.some(i => 'img-' + i.id === id)) { input.value = ''; type.value = ''; use.value = ''; }
      filter();
      const target = id && document.getElementById(id); if (target && !target.hidden) target.scrollIntoView({block: 'start'});
    } catch {
      if (token === version) { records = []; gallery.replaceChildren(node('p', 'Tuto galerii se nepodařilo načíst. Zkuste obnovit stránku nebo přejít do druhé galerie.', 'empty')); }
    }
  }
  document.querySelectorAll('[data-gallery]').forEach(a => a.addEventListener('click', event => {
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) return;
    event.preventDefault(); branch = a.dataset.gallery;
    input.value = ''; type.value = ''; use.value = '';
    const u = new URL(location.href); u.hash = ''; history.replaceState(null, '', u.pathname + u.search);
    writeState(true); load();
  }));
  input.addEventListener('input', () => filter());
  clear.addEventListener('click', () => { input.value = ''; filter(); input.focus(); });
  type.addEventListener('change', () => filter()); use.addEventListener('change', () => filter());
  window.addEventListener('popstate', () => load()); window.addEventListener('hashchange', () => load());
  load();
})();
