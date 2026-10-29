#!/usr/bin/env python3
"""Download an approved image catalog; persist stable topic assignments for news and Kosmopedie.
Only Python standard library + Pillow. Never changes source articles or their dates/IDs.
"""
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

VERSION = 2
RULES = [
 ('relictni-zareni', ['reliktn', 'mikrovln', 'cmb', 'cosmic microwave']),
 ('temna-hmota', ['temna hmot', 'temne hmot', 'dark matter', 'axion', 'wimp']),
 ('temna-energie', ['temna energi', 'temne energi', 'dark energy', 'hubble tension', 'hubbleovo napeti', 'hubblovo napeti', 'rozpinani', 'rozpinav']),
 ('gravitacni-vlny', ['gravitacni vln', 'gravitational wave', 'ligo', 'virgo', 'kilonov']),
 ('neutronove-hvezdy', ['neutronov', 'pulsar', 'pulzar', 'magnetar']),
 ('exoplanety', ['exoplan', 'planet', 'obyvateln', 'habitabil', 'proxima']),
 ('cerne-diry', ['cerna dir', 'cerne dir', 'cernych der', 'cernou dir', 'black hole', 'singularit', 'm87', 'sgr a']),
 ('kvazary', ['kvazar', 'kvasar', 'quasar', 'aktivni jadr', 'active galactic']),
 ('velky-tresk', ['velky tresk', 'velkeho tresku', 'big bang', 'inflac', 'rany vesmir', 'raneho vesmiru', 'prvotni', 'reioniz']),
 ('kvantova-gravitace', ['kvantov', 'quantum', 'strunov', 'string theor', 'entrop', 'holograf']),
 ('multivesmir', ['multivesmir', 'multiverse', 'paralelni vesmir', 'bubble univers']),
 ('gravimetrie-testy', ['gravitac', 'gravit', 'relativit', 'pata sila', 'moment hybnosti']),
 ('vesmirne-teleskopy', ['teleskop', 'dalekohled', 'observator', 'james webb', 'jwst', 'hubble', 'euclid']),
 ('galaxie', ['galaxi', 'galaxy', 'galaxies', 'mlecna draha', 'milky way']),
 ('hvezdy', ['hvezd', 'stellar', 'star ', 'supernov', 'mlhovin', 'nebula'])]
SCHEMATICS = ['relictni-zareni','temna-hmota','temna-energie','gravitacni-vlny',
              'velky-tresk','kvantova-gravitace','multivesmir','gravimetrie-testy','ostatni']

def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(s).lower()) if not unicodedata.combining(c))

def topic_for(item):
    if item.get('theme') in dict(RULES): return item['theme']
    title = norm(item.get('title','')+' '+item.get('original_title',''))
    for topic, words in RULES:
        if any(w in title for w in words): return topic
    body = norm(item.get('summary','')+' '+item.get('perex',''))
    for topic, words in RULES:
        if any(w in body for w in words): return topic
    return 'ostatni'

def key_for(item, collection):
    # Same identity even if titles/summaries change. Explainery have no permanent IDs.
    value = str(item.get('id') or item.get('url') or item.get('title') or '')
    return collection+':'+hashlib.sha256(value.encode()).hexdigest()[:24]

def read_json(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def font(size):
    from PIL import ImageFont
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','C:/Windows/Fonts/arial.ttf',
              '/System/Library/Fonts/Supplemental/Arial.ttf']:
        if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default(size=size)

def source_identity(entry):
    # Raw pixel hashes also catch files downloaded under different names/URLs.
    return entry.get('source_family') or entry.get('source_pixel_sha256') or entry.get('source_sha256') or entry.get('source_id') or entry.get('source') or entry['id']


SUBTOPICS = {
 'detectors': ['detektor','lux','zeplin',' lz','primou detek','primo hled','mineral'],
 'axions': ['axion','aksion','dali','temny foton','temnych foton'],
 'indirect': ['fermi','anihil','gama','gamma','integral'],
 'particles': ['detektor','lux','zeplin',' lz','wimp','axion','aksion','castic','foton','neutralin','rozptyl','mineral'],
 'lensing': ['cock','lensing'],
 'rotation': ['rotac','otacen','rotuj','rotation'],
 'clusters': ['kup','cluster'],
 'structure': ['halo','simul','map','struktur','sit','pavucin'],
 'expansion': ['rozpin','hubble','hubbl','napeti','sireny'],
 'supernova': ['supernov','refsdal'],
 'field': ['kvintes','fantom','pole','holograf','energii','energie'],
}


def subtopic_for(item):
    text = norm(item.get('title','')+' '+item.get('original_title',''))
    for tag, words in SUBTOPICS.items():
        if any(w in text for w in words): return tag
    return 'general'


def candidates_for(item, available):
    # Section diagrams are selected explicitly by the editor, never as a lead image.
    available=[e for e in available if not e.get('manual_only')]
    topic=topic_for(item); text=norm(item.get('title','')+' '+item.get('original_title',''))
    pool=[e for e in available if topic in e.get('topics',[e['topic']]) and not e.get('alias_of')]
    exact=[e for e in pool if e.get('match_keywords') and any(norm(w) in text for w in e['match_keywords'])]
    subtopic=subtopic_for(item)
    specific=[e for e in pool if subtopic != 'general' and subtopic in e.get('subtopics',[])]
    general=[e for e in pool if 'general' in e.get('subtopics',['general']) and not e.get('match_keywords')]
    return exact or specific or general or [e for e in available if e['topic']=='ostatni' and not e.get('alias_of')]


def prepare(site, download=True, reassign=False):
    site=Path(site);catalog=read_json(site/'data/article_image_catalog.json',[])
    if not catalog: raise ValueError('Chybí data/article_image_catalog.json')
    folder=site/'assets/article-images';folder.mkdir(parents=True,exist_ok=True)
    available=[]
    def prepare_entry(e):
        try:
            if download:
                from article_image_assets import make_asset as render_asset
                render_asset(e,folder)
            if (folder/(e['id']+'.jpg')).is_file(): return e
        except Exception as err: print('Obrázek přeskočen:',e['id'],err,flush=True)
    if download:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as executor:
            available=[e for e in executor.map(prepare_entry,catalog) if e]
    else:
        available=[e for e in catalog if (folder/(e['id']+'.jpg')).is_file()]
    if not available: raise RuntimeError('Žádný dostupný tematický obrázek')
    cache=read_json(site/'data/article_image_assignments.json',{})
    if reassign: cache={}
    by_id={e['id']:e for e in available}
    missing=set(cache.values())-set(by_id)
    if missing: raise RuntimeError('Uložené obrázky nejsou dostupné; přiřazení nebylo změněno: '+', '.join(sorted(missing)))
    records=[]
    for collection,file in [('news','news.json'),('explainery','explainery.json')]:
        records.extend((item,collection) for item in read_json(site/'data'/file,[]))
    records.sort(key=lambda r:(r[0].get('inserted_at') or r[0].get('published') or '',key_for(*r)))
    history={};last_used={}
    for step,(item,collection) in enumerate(records):
        key=key_for(item,collection);topic=topic_for(item)
        previous=history.setdefault(topic,[])
        if cache.get(key) in by_id:
            chosen=by_id[cache[key]]
        else:
            choices=candidates_for(item,available)
            if not choices: raise ValueError('Chybí vhodný obrázek: '+str(item.get('title')))
            recent=set(previous[-5:])
            fresh=[e for e in choices if source_identity(e) not in recent]
            choices=fresh or choices
            chosen=min(choices,key=lambda e:(last_used.get(source_identity(e),-1), hashlib.sha256((key+e['id']).encode()).hexdigest()))
            cache[key]=chosen['id']
        identity=source_identity(chosen)
        previous.append(identity);last_used[identity]=step
    target=site/'data/article_image_assignments.json'
    content=json.dumps(cache,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    if not target.exists() or target.read_text(encoding='utf-8')!=content:
        tmp=target.with_suffix('.tmp');tmp.write_text(content,encoding='utf-8');tmp.replace(target)
    export_previews(site,cache,by_id)
    return cache,by_id


def thumbnail(entry, href):
    from html import escape as esc
    if not entry or not entry.get('thumbnail'): return ''
    links=' '.join('<a href="'+esc(a['url'],quote=True)+'">'+esc(a['text'])+'</a>' for a in entry.get('credit_links',[]) if a.get('url','').startswith(('https://','http://')))
    return ('<figure class="article-preview"><a href="'+esc(href,quote=True)+'" aria-label="Otevřít článek: '+esc(entry['title'],quote=True)+'">'
            '<img src="/'+esc(entry['thumbnail'],quote=True)+'" alt="'+esc(entry['alt'],quote=True)+'" width="288" height="288" loading="lazy" decoding="async"></a>'
            '<figcaption>Tematický obrázek · '+esc(entry['kind'])+' · '+esc(entry['credit'])+' '+links+' · '
            '<a href="'+esc(entry['source'],quote=True)+'">Zdroj</a> · '
            '<a href="'+esc(entry['license_url'],quote=True)+'">'+esc(entry['license'])+'</a> · '+esc(entry.get('thumbnail_modifications','zmenšení'))+'</figcaption></figure>')


def export_previews(site, assignments, catalog):
    from build_static import slugify, id_digits
    items=read_json(site/'data/news.json',[])
    items.sort(key=lambda x:x.get('inserted_at') or '',reverse=True)
    used=set();manifest={}
    for item in items:
        stem=slugify(item.get('title','clanek'))+'-'+id_digits(item.get('id'));slug=stem;n=2
        while slug in used: slug=stem+'-'+str(n);n+=1
        used.add(slug)
        entry=catalog.get(assignments.get(key_for(item,'news')))
        identity=str(item.get('id') or item.get('url') or item.get('title') or '')
        href='/clanky/'+slug+'.html'
        manifest[identity]={'href':href,'html':thumbnail(entry,href)}
    target=site/'data/article_image_previews.json'
    target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def lookup(item,collection,library):
    assignments,catalog=library
    return catalog.get(assignments.get(key_for(item,collection)))

def image_url(entry,base=''):
    if not entry:return None
    return base+'/assets/article-images/'+entry['id']+'.jpg'+('?v='+str(entry['revision']) if entry.get('revision') else '')

def figure(entry, zoom=None):
    from html import escape as esc
    if not entry:return ''
    links=' '.join('<a href="'+esc(a['url'],quote=True)+'" rel="noopener">'+esc(a['text'])+'</a>'
                   for a in entry.get('credit_links',[]) if a.get('url','').startswith(('https://','http://')))
    result = ('<figure class="article-image"><img src="'+esc(image_url(entry),quote=True)+'" '
            'alt="'+esc(entry['alt'],quote=True)+'" width="'+str(entry.get('width',1200))+'" height="'+str(entry.get('height',630))+'" style="width:100%;height:auto;border-radius:10px">'
            '<figcaption style="font-size:.85rem;color:var(--muted)">'+esc(entry['caption'])+'<br>© / kredit: '+esc(entry['credit'])+
            ' · <a href="'+esc(entry['source'],quote=True)+'">Zdroj</a> · '+links+
            ' · <a href="'+esc(entry['license_url'],quote=True)+'">'+esc(entry['license'])+'</a>'
            ' · Úpravy: '+esc(entry.get('modifications','zmenšení, rámeček a kredit'))+'.</figcaption></figure>\n')

    if zoom is None:
        zoom = entry.get('zoomable', False)
    if zoom:
        link = ('<a href="' + esc(image_url(entry), quote=True) + '" target="_blank" rel="noopener" '
                'class="article-image-zoom" aria-label="Zvětšit graf: ' + esc(entry['title'], quote=True) + '">')
        result = result.replace('<img ', link + '<img ', 1).replace('<figcaption', '</a><figcaption', 1)
        caption = '<figcaption style="font-size:.85rem;color:var(--muted)">'
        result = result.replace(caption, caption + link + 'Zvětšit graf</a><br>', 1)
    return result


def image_schema(entry,base):
    if not entry:return None
    result = {'@type':'ImageObject','url':image_url(entry,base),
              'contentUrl':image_url(entry,base),
              'caption':entry['caption'],'creditText':entry['credit'],'license':entry['license_url'],
              'acquireLicensePage':entry['source'],'width':entry.get('width',1200),'height':entry.get('height',630)}
    # Use explicit rights metadata where known. A credit line alone does not
    # establish either authorship or ownership of a third-party image.
    creator = entry.get('creator')
    copyright_notice = entry.get('copyrightNotice')
    if entry.get('generated') is True and str(entry.get('source_id','')).startswith('own-diagram:'):
        creator = creator or {'@type':'Organization','name':'Kosmologické novinky',
                              'url':base.rstrip('/') + '/'}
        copyright_notice = copyright_notice or 'Kosmologické novinky'
    if creator:
        result['creator'] = creator
    if copyright_notice:
        result['copyrightNotice'] = copyright_notice
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--site-dir',default='.')
    ap.add_argument('--offline',action='store_true',help='Pouze již stažené obrázky; žádná síť')
    ap.add_argument('--reassign',action='store_true',help='Výslovné jednorázové přerozdělení celého archivu')
    args=ap.parse_args();cache,lib=prepare(args.site_dir,not args.offline,args.reassign)
    print(f'OK: {len(lib)} obrázků, {len(cache)} trvalých přiřazení. Zpracován archiv i nové články.')

if __name__=='__main__':main()


