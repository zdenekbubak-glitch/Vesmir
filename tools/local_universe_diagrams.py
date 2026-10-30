"""Reproducible nearby-Universe illustrations; packaged data, no network access."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,math
from article_image_assets import font
from exoplanet_population_diagrams import txt
BG='#0b1424';W='#edf4ff';M='#bac8db';B='#7dcfff';G='#8de0b1';Y='#ffd287';GRID='#35465e'
def text(d,x,y,t,size=25,color=W,width=1010):return txt(d,x,y,t,size,color,width=width)
def project(v):
 x,y,z=v;a=math.radians(35);b=math.radians(25)
 return x*math.cos(a)-y*math.sin(a),(x*math.sin(a)+y*math.cos(a))*math.sin(b)-z*math.cos(b)
def diagram(entry):
 data=json.loads((Path(__file__).resolve().parents[1]/entry['data_file']).read_text(encoding='utf8'));kind=entry['diagram'];h={'localview-sun':2260,'localview-stars':1450,'localview-milkyway':1450,'localview-group':1500,'localview-wide':1370}[kind];im=Image.new('RGB',(1100,h),BG);d=ImageDraw.Draw(im)
 if kind=='localview-sun':
  text(d,45,35,'Jaká budoucnost čeká Slunce?',39)
  text(d,45,105,'Pořadí etap • orientační odhady dob a jejich trvání',25,B)
  text(d,45,155,'U začátku uvádíme dobu od dneška, u pozdějších etap jejich trvání.',23,M)
  text(d,45,194,'Stejně velká pole představují různě dlouhá období.',23,M)
  rows=[
   ('Dnes','Hvězda na hlavní posloupnosti','V jádře se vodík mění na helium. Slunce pomalu zvyšuje vyzařovaný výkon.'),
   ('Během dalších miliard let','Proměny podmínek na Zemi','Silnější záření ovlivní podnebí, vodu a kyslík v atmosféře. Odhady, kdy tyto změny nastanou, se liší podle použitého modelu.'),
   ('Začátek asi za 5–6 miliard let od dneška','Přechod k červenému obru','Vodík v jádře dochází. Reakce pokračují kolem jádra; vnější vrstvy se rozpínají.'),
   ('Trvání přibližně 100 milionů let','Přeměna helia na uhlík a kyslík','Slunce získává energii přeměnou helia v jádře. Oproti předchozímu vrcholu fáze červeného obra se dočasně zmenší.'),
   ('Trvání řádově miliony až desítky milionů let','Opětovné rozpínání do červeného obra','Po vyčerpání helia v jádře pokračují jaderné reakce v okolních vrstvách. Slunce se znovu zvětšuje a postupně odvrhuje vnější obal.'),
   ('Po odvržení vnějších vrstev','Horký pozůstatek a okolní plyn','Odvržený plyn může krátce zářit jako slabá planetární mlhovina.'),
   ('Během miliard a desítek miliard let','Bílý trpaslík postupně chladne','Hustý pozůstatek o velikosti přibližně Země vyzařuje nahromaděné teplo. Jeho nitro postupně tuhne a svit slábne.'),
   ('Po bilionech let a ještě déle','Vzdálená budoucnost: černý trpaslík','Podle výpočtů zůstane chladný, téměř nesvítící pozůstatek Slunce.')]
  for i,(when,title,body) in enumerate(rows):
   yy=265+i*235;d.rounded_rectangle((45,yy,1055,yy+213),radius=16,fill='#152339',outline=GRID,width=2)
   text(d,70,yy+14,when,24,Y,width=960);text(d,70,yy+57,title,29,W,width=960);text(d,70,yy+105,body,25,M,width=960)
   if i<len(rows)-1:d.line((550,yy+214,550,yy+233),fill=B,width=3)
  text(d,45,2180,'Podklad: ESA/Gaia a studie vývoje Slunce a Země uvedené u tématu.',22,M)
 elif kind=='localview-stars':
  text(d,45,35,'Které hvězdy jsou nejblíže Slunci?',37);text(d,45,105,'11 hvězd v 7 soustavách • vybrané okolí do 10 světelných let',24,B)
  x0,x1,top,bottom=400,1015,265,1145
  text(d,x0,185,'Vzdálenost od Slunce (světelné roky)',24,W,width=650)
  for t in [0,2,4,6,8,10]:
   x=x0+(x1-x0)*t/10;d.line((x,top-10,x,bottom),fill=GRID,width=2);text(d,x-8,top-47,str(t),22,M,width=65)
  cols={'M':'#ff9d87','G + K':Y,'A + bílý trpaslík':B,'M + M':'#ff9d87'}
  for i,a in enumerate(data['stars']):
   y=top+45+i*105;x=x0+(x1-x0)*a['distance_ly']/10;c=cols[a['kind']];text(d,45,y-17,a['name'],26,W,width=340);text(d,45,y+22,a['kind'],22,c,width=330);d.line((x0,y,x,y),fill=c,width=4);d.ellipse((x-8,y-8,x+8,y+8),fill=c)
   # Numeric label above marker, kept inside chart.
   text(d,min(x-23,980),y-40,str(a['distance_ly']).replace('.',','),22,c,width=80)
  text(d,45,1175,'Barvy: červená – třída M; žlutá – G/K; modrá – Sirius A/B.',24,M)
  text(d,45,1245,'Sirius: hvězda třídy A a bílý trpaslík. Body mají stejnou velikost.',24,M)
  text(d,45,1315,'Řádky ukazují vzdálenost, nikoli společný směr na obloze.',24,M)
  text(d,45,1380,'Alfa Centauri A/B a Proxima patří do jediné trojhvězdné soustavy.',23,Y)
 elif kind=='localview-milkyway':
  text(d,45,35,'Kde v Mléčné dráze leží Slunce?',38);text(d,45,105,'Pohled shora a z boku • názorná stavba disku',25,B)
  cx,cy,rad=545,605,355
  for rr in range(rad,0,-1):
   value=int(20+17*(1-rr/rad));d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),fill=(value//2,value,value+18))
  for k in range(4):
   pts=[]
   for j in range(220):
    t=j/219;r=55+t*290;a=k*math.pi/2+t*4.1;pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
   d.line(pts,fill='#527793',width=15)
  d.line((cx-80,cy+35,cx+80,cy-35),fill='#a9a6a0',width=30);d.ellipse((cx-17,cy-17,cx+17,cy+17),fill=Y)
  sx,sy=cx+rad*.535,cy;d.line([(sx-28,sy+35),(sx-10,sy+12),(sx,sy),(sx+10,sy-18),(sx+15,sy-40)],fill=Y,width=7);d.line((cx,cy,sx,sy),fill=Y,width=3);d.ellipse((sx-10,sy-10,sx+10,sy+10),fill=Y)
  text(d,55,175,'Shora: schematická spirální struktura',25,W);text(d,565,cy-80,'asi 27 tisíc světelných let',22,Y,width=440);text(d,sx+18,sy+15,'Slunce',29,Y,width=160);text(d,270,cy+42,'Střed Galaxie',24,Y,width=250)
  d.line((sx,sy+8,900,875),fill=Y,width=2);text(d,640,890,'Rameno Orionu / Místní rameno',24,W,width=415)
  d.line((190,1000,900,1000),fill=B,width=3)
  for x in [190,900]:d.line((x,988,x,1012),fill=B,width=3)
  text(d,235,1018,'Průměr jasné části disku: přibližně 100 tisíc sv. let',23,B,width=800)
  text(d,45,1100,'Z boku: Slunce leží blízko roviny disku',25,W)
  d.ellipse((190,1210,900,1230),fill='#527793');d.ellipse((495,1183,595,1257),fill='#8893a2');d.ellipse((sx-7,1213,sx+7,1227),fill=Y);text(d,sx+15,1245,'Slunce',24,Y,width=200)
  text(d,45,1320,'Oba pohledy: stejné délkové měřítko. Ramena jsou zjednodušená.',24,M)
  text(d,45,1380,'Halo se rozkládá daleko za vyznačenou jasnou část disku.',23,M)
 else:
  wide=kind=='localview-wide';limit=60 if wide else 3.5;ox,oy,scale=550,700,7.0 if wide else 100
  text(d,45,35,'Naše širší galaktické okolí' if wide else 'Místní skupina v prostoru',38);text(d,45,105,'Vybrané galaxie • prostorová projekce • počátek u Slunce',24,B)
  text(d,45,160,'Vzdálenosti na osách: miliony světelných let',25,W)
  def p(v):
   u,vv=project(v);return ox+scale*u,oy+scale*vv
  # Project orthogonal equal-scale axes, ticks remain attached to axes.
  for axis,label in [(0,'X'),(1,'Y'),(2,'Z')]:
   v=[0,0,0];v[axis]=limit;end=p(v);v[axis]=-limit;start=p(v);d.line((*start,*end),fill=GRID,width=2);text(d,end[0]+8,end[1]-10,label,25,B,width=70)
   ticks=[-40,-20,20,40] if wide else [-2,-1,1,2]
   for t in ticks:
    v[axis]=t;x,y=p(v);d.ellipse((x-3,y-3,x+3,y+3),fill=B);text(d,x+5,y+5,str(t),19,M,width=65)
  d.ellipse((ox-7,oy-7,ox+7,oy+7),fill=Y);text(d,ox-145,oy+15,'Mléčná dráha / my',23,Y,width=265)
  rows=data['galaxies'] if wide else data['galaxies'][:4]
  if wide:rows=[x for x in rows if x['kind'] in ['group','cluster']]
  offsets=({'M81':(-180,-48),'Centaurus':(15,12),'NGC':(-185,25),'Kupa':(-145,-65)} if wide else {'Velký':(-260,-100),'Malý':(40,50),'Andromeda':(-240,-90),'Galaxie':(25,15)})
  for a in rows:
   x,y=p(a['xyz_mly']);c=G if a['kind']=='satellite' else B;d.line((ox,oy,x,y),fill='#364b64',width=2);d.ellipse((x-7,y-7,x+7,y+7),fill=c)
   if not wide and a['kind']=='satellite':continue
   label=a['name'].replace(' – okolí skupiny M81','').replace(' – okolní skupina','').replace(' – oblast Sochaře','').replace('Galaxie v Trojúhelníku (M33)','M33')
   if wide:lx,ly=next(v for k,v in {'M81':(90,460),'Centaurus':(780,520),'NGC':(690,900),'Kupa':(660,280)}.items() if label.startswith(k))
   else:lx,ly=(60,780) if label.startswith('Andromeda') else (360,925)
   d.line((x,y,lx+20,ly+22),fill=GRID,width=2);text(d,lx,ly,label,25,c,width=390);text(d,lx,ly+65 if label.startswith('Kupa') else ly+38,str(a['distance_mly']).replace('.',',')+' mil. sv. let',22,M,width=300)
  if not wide:
   text(d,650,455,'Magellanova oblaka',24,G,width=380);text(d,650,490,'(detail níže)',23,M,width=380);d.line((700,530,ox+10,oy+10),fill=GRID,width=2)
   # Magnified satellite inset, separate scale; orthographic XY view would lose depth, reuse projection.
   box=(45,1020,1055,1335);d.rounded_rectangle(box,12,fill='#142239',outline=GRID,width=2);text(d,65,1038,'Detail u Mléčné dráhy: zvětšení 15× vůči horní mapě',24,W)
   cox,coy,ss=490,1160,1500
   for a in data['galaxies'][:2]:
    u,v=project(a['xyz_mly']);x,y=cox+ss*u,coy+ss*v;d.line((cox,coy,x,y),fill=GRID,width=2);d.ellipse((x-6,y-6,x+6,y+6),fill=G);dx,dy=(18,-40) if a['name'].startswith('Velký') else (15,-40);text(d,x+dx,y+dy,a['name'],22,G,width=285)
   d.ellipse((cox-7,coy-7,cox+7,coy+7),fill=Y);text(d,cox+15,coy-45,'My',23,Y,width=70);d.line((95,1280,245,1280),fill=B,width=3);text(d,85,1290,'0,1 mil. sv. let',21,B,width=290)
   text(d,45,1370,'X: k centru Galaxie • Y: podél roviny • Z: kolmo k rovině',23,M)
   text(d,45,1425,'Směry a vzdálenosti jsou převedeny do společných souřadnic.',22,M)
  else:
   text(d,45,1090,'X: k centru Galaxie • Y: podél roviny • Z: kolmo k rovině',23,M)
   text(d,45,1150,'Skupiny zastupuje uvedená galaxie, kupu v Panně směr M87.',24,M)
   text(d,45,1220,'Vzdálenosti jsou zaokrouhlené. Velikost značek je názorná.',24,M)
   text(d,45,1290,'Přesnější detail Místní skupiny ukazuje předchozí obrázek.',23,M)
 return im
