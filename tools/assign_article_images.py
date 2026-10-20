#!/usr/bin/env python3
"""Download an approved image catalog; persist stable topic assignments for news and Kosmopedie.
Only Python standard library + Pillow. Never changes source articles or their dates/IDs.
"""
import argparse
import hashlib
import io
import json
import re
import textwrap
import unicodedata
import urllib.request
from pathlib import Path

VERSION = 1
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

def make_asset(entry, folder):
    from PIL import Image, ImageOps, ImageDraw
    path = folder / (entry['id']+'.jpg')
    if path.exists():
        with Image.open(path) as check: check.verify()
        return
    if entry.get('generated'):
        im = draw_schematic(entry)
    else:
        req=urllib.request.Request(entry['download'],headers={'User-Agent':'Kosmonovinky-image-library/1.0'})
        with urllib.request.urlopen(req,timeout=45) as response:
            data=response.read(25*1024*1024+1)
        if len(data)>25*1024*1024: raise ValueError('Image larger than 25 MB')
        with Image.open(io.BytesIO(data)) as original:
            original=ImageOps.exif_transpose(original).convert('RGB')
            # Preserve whole scientific image; fit on a dark canvas instead of cutting data.
            if entry.get('layout') == 'landscape':
                pic=ImageOps.fit(original,(1200,530),Image.Resampling.LANCZOS,centering=tuple(entry.get('centering',[0.5,0.5])))
                im=Image.new('RGB',(1200,630),'#080e1b');im.paste(pic,(0,0))
            else:
                pic=ImageOps.contain(original,(1200,530),Image.Resampling.LANCZOS)
                im=Image.new('RGB',(1200,630),'#080e1b');im.paste(pic,((1200-pic.width)//2,(530-pic.height)//2))
    d=ImageDraw.Draw(im)
    d.rectangle((0,530,1200,630),fill='#080e1b')
    if not entry.get('generated'):
        label='TEMATICKÝ OBRÁZEK · '+entry['kind']
        box=d.textbbox((0,0),label,font=font(18))
        d.rectangle((15,12,40+box[2],46),fill='#080e1b')
        d.text((24,18),label,font=font(18),fill='#e3e9f3')
    # All derived previews retain the full credit, source ID, license and alteration notice.
    lines=textwrap.wrap(entry['credit'],width=100)
    if len(lines)>2: raise ValueError('Credit too long for readable overlay: '+entry['id'])
    for n,line in enumerate(lines): d.text((22,539+n*23),line,font=font(19),fill='#e3e9f3')
    label=(entry.get('source_id',entry['id'])+' | ' if not entry.get('generated') else '')+entry['license']+' | '+entry.get('modifications','Zmenšeno, doplněn rámeček a kredit')
    d.text((22,601),label,font=font(16),fill='#aebed4')
    tmp=path.with_suffix('.tmp')
    im.save(tmp,'JPEG',quality=90,optimize=True);tmp.replace(path)

def draw_schematic(entry):
    """Own mathematical diagrams, explicitly labelled; never pretend to be observation data."""
    from PIL import Image,ImageDraw
    import math,random
    im=Image.new('RGB',(1200,630),'#0a1120');d=ImageDraw.Draw(im)
    rng=random.Random(entry['id']); t=entry['topic'];v=entry.get('variant',0)
    colors=['#67b8f7','#ca99f9','#62dccc']
    if t=='relictni-zareni':
        # Qualitative anisotropy mosaic, no real CMB data or fabricated scale.
        for x in range(170,1030,12):
            for y in range(110,450,12):
                if ((x-600)/430)**2+((y-280)/170)**2<1:
                    c=rng.choice(['#265e98','#5799c0','#d4ba85','#b67151','#783b45'])
                    d.rectangle((x,y,x+12,y+12),fill=c)
    elif t in ('gravitacni-vlny','gravimetrie-testy'):
        for row in range(5):
            pts=[(x,145+row*60+math.sin(x/75+row+v)*24) for x in range(90,1110,3)]
            d.line(pts,fill=colors[row%3],width=3)
    elif t in ('temna-energie','velky-tresk'):
        for row in range(7):
            pts=[(x,280+(row-3)*(12+((x-100)/1000)**(1.5+v*.4)*62)) for x in range(100,1100,5)]
            d.line(pts,fill=colors[row%3],width=3)
        for x in range(200,1100,180):
            r=5+(x-100)//80;d.ellipse((x-r,280-r,x+r,280+r),outline='#e8ce97',width=3)
    elif t=='temna-hmota':
        d.ellipse((330,100,870,460),outline='#527eb5',width=3)
        for n in range(180):
            a=rng.random()*math.tau;r=rng.random()**0.5*240
            x=600+math.cos(a)*r;y=280+math.sin(a)*r*.6
            d.ellipse((x-2,y-2,x+2,y+2),fill='#8acdf6')
        d.ellipse((530,235,670,325),outline='#e8ce97',width=4)
    elif t=='multivesmir':
        for n in range(16):
            x=rng.randint(130,1070);y=rng.randint(125,430);r=rng.randint(20,65)
            d.ellipse((x-r,y-r,x+r,y+r),outline=colors[n%3],width=3)
    else:
        for x in range(120,1120,65):d.line((x,130,x,445),fill='#2d4b6c',width=2)
        for y in range(130,446,45):d.line((120,y,1095,y),fill='#2d4b6c',width=2)
        for n in range(40):
            x=rng.randrange(120,1095,65);y=rng.randrange(130,446,45)
            d.ellipse((x-5,y-5,x+5,y+5),fill=colors[n%3])
    d.text((30,25),'Kosmologické novinky · '+entry['title'],font=font(25),fill='#e7eef8')
    d.text((30,487),'TEMATICKÉ SCHÉMA · nikoli snímek ani naměřená data',font=font(20),fill='#aebed4')
    return im

def prepare(site, download=True):
    site=Path(site);catalog=read_json(site/'data/article_image_catalog.json',[])
    if not catalog: raise ValueError('Chybí data/article_image_catalog.json')
    folder=site/'assets/article-images';folder.mkdir(parents=True,exist_ok=True)
    available=[]
    def prepare_entry(e):
        try:
            if download: make_asset(e,folder)
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
    by_id={e['id']:e for e in available};counts={i:0 for i in by_id}
    known_ids={e['id'] for e in catalog}
    full_catalog={e['id']:e for e in catalog}
    for image_id in cache.values():
        if image_id in counts: counts[image_id]+=1
    for collection,file in [('news','news.json'),('explainery','explainery.json')]:
        items=read_json(site/'data'/file,[])
        # Oldest first so adding fresh news cannot reshuffle previous assignments.
        items.sort(key=lambda e:(e.get('inserted_at') or e.get('published') or '',key_for(e,collection)))
        previous=[]
        for item in items:
            key=key_for(item,collection)
            old=full_catalog.get(cache.get(key),{})
            words=old.get('match_keywords',[])
            allowed=not words or any(w in norm(item.get('title','')+' '+item.get('original_title','')) for w in words)
            if cache.get(key) in known_ids and allowed:
                previous.append(cache[key]);continue
            topic=topic_for(item)
            title=norm(item.get('title','')+' '+item.get('original_title',''))
            exact=[e for e in available if e.get('match_keywords') and any(w in title for w in e['match_keywords'])]
            choices=exact or [e for e in available if e['topic']==topic and not e.get('match_keywords')]
            if not choices: choices=[e for e in available if e['topic']=='ostatni']
            if not choices: continue
            def rank(e):
                tie=hashlib.sha256((key+e['id']).encode()).hexdigest()
                return (e['id'] in previous[-3:],counts[e['id']],tie)
            e=min(choices,key=rank);cache[key]=e['id'];counts[e['id']]+=1;previous.append(e['id'])
    target=site/'data/article_image_assignments.json'
    content=json.dumps(cache,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    if not target.exists() or target.read_text(encoding='utf-8')!=content:
        tmp=target.with_suffix('.tmp');tmp.write_text(content,encoding='utf-8');tmp.replace(target)
    return cache,by_id

def lookup(item,collection,library):
    assignments,catalog=library
    return catalog.get(assignments.get(key_for(item,collection)))

def image_url(entry,base=''):
    if not entry:return None
    return base+'/assets/article-images/'+entry['id']+'.jpg'+('?v='+str(entry['revision']) if entry.get('revision') else '')

def figure(entry):
    from html import escape as esc
    if not entry:return ''
    links=' '.join('<a href="'+esc(a['url'],quote=True)+'" rel="noopener">'+esc(a['text'])+'</a>'
                   for a in entry.get('credit_links',[]) if a.get('url','').startswith(('https://','http://')))
    return ('<figure class="article-image"><img src="'+esc(image_url(entry),quote=True)+'" '
            'alt="'+esc(entry['alt'],quote=True)+'" width="1200" height="630" style="width:100%;height:auto;border-radius:10px">'
            '<figcaption style="font-size:.85rem;color:var(--muted)">'+esc(entry['caption'])+'<br>© / kredit: '+esc(entry['credit'])+
            ' · <a href="'+esc(entry['source'],quote=True)+'">Zdroj</a> · '+links+
            ' · <a href="'+esc(entry['license_url'],quote=True)+'">'+esc(entry['license'])+'</a>'
            ' · Úpravy: '+esc(entry.get('modifications','zmenšení, rámeček a kredit'))+'.</figcaption></figure>\n')

def image_schema(entry,base):
    if not entry:return None
    return {'@type':'ImageObject','url':image_url(entry,base),
            'contentUrl':image_url(entry,base),
            'caption':entry['caption'],'creditText':entry['credit'],'license':entry['license_url'],
            'acquireLicensePage':entry['source'],'width':1200,'height':630}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--site-dir',default='.')
    ap.add_argument('--offline',action='store_true',help='Pouze již stažené obrázky; žádná síť')
    args=ap.parse_args();cache,lib=prepare(args.site_dir,not args.offline)
    print(f'OK: {len(lib)} obrázků, {len(cache)} trvalých přiřazení. Zpracován archiv i nové články.')

if __name__=='__main__':main()

