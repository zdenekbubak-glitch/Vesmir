"""Dated comparison plots, reconstructed solely from the packaged JSON snapshot."""
from pathlib import Path
from PIL import Image,ImageDraw
import math,json
from article_image_assets import font
from exoplanet_population_diagrams import txt
BG='#0b1424';WHITE='#edf4ff';MUTED='#bac8db';BLUE='#7dcfff';GREEN='#8de0b1';GOLD='#ffd287';GRID='#35465e'
def num(v,n=2):return f'{v:.{n}f}'.replace('.',',')

TYPE_COLORS={'rock':'#ffb36b','gas':'#7dcfff','envelope':'#b5a1ff','uncertain':'#b6bfcc'}
def planet_mark(d,x,y,planet,radius=6):
 color=TYPE_COLORS[planet.get('visual_type','uncertain')]
 if planet.get('hz_flag'):d.ellipse((x-radius-4,y-radius-4,x+radius+4,y+radius+4),outline=GREEN,width=3)
 d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=color)
 return color

def type_legend(d,y,show_band=True):
 for x,yy,key,label in [(65,y,'rock','Kamenná (u exoplanet odhad)'),(610,y,'gas','Plynný obr'),(65,y+55,'envelope','Planeta neptunového typu / menší planeta s obalem'),(610,y+55,'uncertain','Složení upřesňujeme')]:
  planet_mark(d,x,yy+14,{'visual_type':key},7)
  if key=='envelope':
   txt(d,x+22,yy,'Planeta neptunového typu /',22,MUTED,width=490);txt(d,x+22,yy+31,'menší planeta s obalem',22,MUTED,width=490)
  else:txt(d,x+22,yy,label,22,MUTED,width=490)
 d.ellipse((54,y+147,76,y+169),outline=GREEN,width=3);txt(d,87,y+145,'Zelený kroužek: planeta v obyvatelné zóně',23,GREEN,width=940)
 txt(d,45,y+195,'Zelený pás: odhad obyvatelné zóny pro danou hvězdu. Podrobnosti v textu.' if show_band else 'Typ planety vychází z měření a fyzikálních modelů.',22,MUTED)
 txt(d,45,y+240,'Zóna označuje možné podmínky pro kapalnou vodu při vhodné atmosféře.',22,MUTED)

def diagram(entry):
 data=json.loads((Path(__file__).resolve().parents[1]/entry['data_file']).read_text(encoding='utf8'));kind=entry['diagram'];h={'exofamily-orbits':1300,'exofamily-inner':1230,'exofamily-years':1230,'exofamily-sizes':1120}[kind]
 if kind in ['exofamily-orbits','exofamily-inner']:h+=60
 legend_y=h+5;h+=380
 im=Image.new('RGB',(1100,h),BG);d=ImageDraw.Draw(im)
 if kind in ['exofamily-orbits','exofamily-inner']:
  log=kind=='exofamily-orbits';txt(d,45,32,'Jak jsou planetární soustavy uspořádané?',35)
  txt(d,45,95,'Společná osa vzdáleností • všechny řádky mají stejné měřítko',25,BLUE)
  txt(d,45,145,'Logaritmická osa: stejné rozestupy znamenají stejný násobek.' if log else 'Detail do 1 AU: stejné rozestupy znamenají stejné vzdálenosti.',24,MUTED)
  txt(d,280,200,'Vzdálenost od hvězdy (AU)',25,WHITE,width=740)
  x0,x1=280,1020;top=345
  def xx(v):return x0+(x1-x0)*(math.log10(v/.01)/math.log10(40/.01) if log else v)
  ticks=[.01,.03,.1,.3,1,3,10,30] if log else [0,.2,.4,.6,.8,1]
  for v in ticks:
   x=xx(v);d.line((x,top-35,x,top+5*135+55),fill=BLUE if v==1 else GRID,width=2 if v==1 else 1);txt(d,x-19,top-85,str(v).replace('.',','),21,MUTED,width=70)
  for i,g in enumerate(data['systems']):
   y=top+i*135;col=GOLD if not i else BLUE
   txt(d,45,y-12,g['label'],25,col,width=225);txt(d,45,y+28,str(len(g['planets']))+' planet',21,MUTED,width=210)
   band=g.get('habitable_band_AU')
   if band:
    lo,hi=max(.01 if log else 0,band[0]),min(40 if log else 1,band[1])
    if lo<hi:d.rectangle((xx(lo),y-6,xx(hi),y+31),fill='#234c3c')
   d.line((x0,y+12,x1,y+12),fill=GRID,width=1)
   for j,p in enumerate(g['planets']):
    v=p['pl_orbsmax']
    if not log and v>1:continue
    x=xx(v);point_col=TYPE_COLORS[p['visual_type']]
    if not log and i==1:d.ellipse((x-2,y+10,x+2,y+14),fill=point_col)
    else:planet_mark(d,x,y+12,p,5)
    label=(['Me','Ve','Ze','Ma','Ju','Sa','Ur','Ne'][j] if not i else p['pl_name'].split()[-1])
    yy=y-30 if j%2==0 else y+28
    if not log and i==1:continue
    d.line((x,y+12,x,yy+17 if j%2==0 else yy),fill=point_col,width=1);txt(d,x-7,yy,label,18,point_col,width=50)
   if not log and i==1:txt(d,350,y-37,'b až h; v zóně e, f, g',21,BLUE,width=320)
   if not log:
    extra=[p for p in g['planets'] if p['pl_orbsmax']>1]
    if extra:txt(d,670,y+65,'Za okrajem: '+(', '.join(p['pl_name'].split()[-1] for p in extra) if i else 'Mars až Neptun'),18,MUTED,width=370)
  txt(d,45,1140 if log else 1120,'1 AU = vzdálenost Země od Slunce. Značky neukazují velikosti planet.',24,MUTED)
  txt(d,45,1200 if log else 1180,'Kepler-90 a TOI-178: vzdálenosti dopočtené z dob oběhu a hmotností hvězd. Údaje a postup jsou uvedeny v tématu.',23,MUTED)
 elif kind=='exofamily-years':
  txt(d,45,32,'Jak dlouho trvá rok na vybraných planetách?',34);txt(d,45,98,'Jeden oběh kolem hvězdy či dvojhvězdy • délka v pozemských dnech',24,BLUE)
  x0,x1=400,1020;top=255
  def xx(v):return x0+(x1-x0)*math.log10(v/.5)/math.log10(400/.5)
  for v in [1,3,10,30,100,365.256]:
   x=xx(v);d.line((x,top-28,x,top+6*105+40),fill=GOLD if v>365 else GRID,width=2 if v>365 else 1);txt(d,x-17,top-75,'365' if v>365 else str(v),21,MUTED,width=80)
  rows=data['unusual_planets']+[{'pl_name':'Země','pl_orbper':365.256,'visual_type':'rock','hz_flag':True}]
  for i,p in enumerate(rows):
   y=top+i*105;v=p['pl_orbper'];x=xx(v);col=TYPE_COLORS[p['visual_type']]
   txt(d,45,y-12,p['pl_name'],25,col,width=335);txt(d,45,y+25,num(v,3).rstrip('0').rstrip(',')+' dne',23,MUTED,width=335)
   d.line((x0,y+12,x,y+12),fill=col,width=5);planet_mark(d,x,y+12,p,6)
  txt(d,45,1080,'Logaritmická osa: stejný rozestup vyjadřuje stejný násobek délky roku.',24,MUTED)
 elif kind=='exofamily-sizes':
  txt(d,45,32,'Velikost a hmotnost vybraných planet',36);txt(d,45,98,'Poloměr a hmotnost vůči Zemi • obě osy jsou logaritmické',25,BLUE)
  x0,x1,y0,y1=170,1010,240,820
  def xx(m):return x0+(x1-x0)*math.log10(m)/math.log10(2000)
  def yy(rad):return y1-(y1-y0)*math.log10(rad/.7)/math.log10(20/.7)
  for m in [1,10,100,1000]:
   x=xx(m);d.line((x,y0,x,y1),fill=GRID);txt(d,x-12,y1+22,str(m),21,MUTED,width=100)
  for rad in [1,2,5,10,20]:
   y=yy(rad);d.line((x0,y,x1,y),fill=GRID);txt(d,90,y-15,str(rad),22,MUTED,width=70)
  txt(d,45,178,'Poloměr (Země = 1)',23,MUTED);txt(d,430,888,'Hmotnost (Země = 1)',24,MUTED)
  rows=[p for p in data['unusual_planets'] if p.get('pl_rade') is not None]+[{'pl_name':'Země','pl_rade':1,'pl_bmasse':1,'visual_type':'rock','hz_flag':True},{'pl_name':'Jupiter','pl_rade':11.21,'pl_bmasse':317.83,'visual_type':'gas','hz_flag':False}]
  for p in rows:
   x,y=xx(p['pl_bmasse']),yy(p['pl_rade']);col=planet_mark(d,x,y,p,6)
   for key,axis in [('pl_bmasse',xx),('pl_rade',yy)]:
    if p.get(key+'err1') is not None:
     lo=axis(p[key]+(p.get(key+'err2') or 0));hi=axis(p[key]+p[key+'err1'])
     d.line((lo,y,hi,y) if key=='pl_bmasse' else (x,lo,x,hi),fill=col,width=2)
   dx,dy={'HD 80606 b':(-130,50),'Jupiter':(-40,-48),'Kepler-16 b':(-85,20),'WASP-107 b':(-145,-35),'55 Cnc e':(12,5),'Země':(15,-30)}[p['pl_name']]
   txt(d,x+dx,y+dy,p['pl_name'],22,col,width=190)
  txt(d,45,960,'Úsečky znázorňují rozmezí odhadu podle měření; někde jsou menší než bod.',23,MUTED)
  txt(d,45,1010,'51 Peg b a planeta pulsaru nemají v použité studii změřený poloměr. Jejich hmotnosti najdete v tabulce.',23,MUTED)
 else:raise ValueError(kind)
 type_legend(d,legend_y,kind in ['exofamily-orbits','exofamily-inner'])
 d.text((45,h-34),'Vlastní datové schéma • NASA Exoplanet Archive, výběr 30. 10. 2026 • zdroje v tématu',font=font(18),fill=MUTED)
 return im
