"""Dated exoplanet counts, received fluxes, and illustrative HZ model bands."""
from pathlib import Path
import json,math
from PIL import Image,ImageDraw
from article_image_assets import font
BG='#0b1424';WHITE='#edf4ff';MUTED='#bac8db';BLUE='#7dcfff';GOLD='#ffd287';GREEN='#8de0b1';GRID='#35465e'
def txt(d,x,y,s,size=27,col=WHITE,width=980):
 f=font(size);line=''
 for w in str(s).split():
  test=(line+' '+w).strip()
  if d.textbbox((0,0),test,font=f)[2]>width and line:d.text((x,y),line,font=f,fill=col);y+=size+9;line=w
  else:line=test
 if line:d.text((x,y),line,font=f,fill=col);y+=size+9
 return y
COEFF={'recent_venus':[1.776,2.136e-4,2.533e-8,-1.332e-11,-3.097e-15],'runaway':[1.107,1.332e-4,1.58e-8,-8.308e-12,-1.931e-15],'maximum':[.356,6.171e-5,1.698e-9,-3.198e-12,-5.575e-16],'early_mars':[.320,5.547e-5,1.526e-9,-2.874e-12,-5.011e-16]}
def hz_flux(teff,kind):
 if not 2600<=teff<=7200:raise ValueError('HZ fit temperature outside published range')
 t=teff-5780;return sum(c*t**n for n,c in enumerate(COEFF[kind]))
def num(x,d=2):return f'{x:.{d}f}'.replace('.',',')
def diagram(entry):
 data=json.loads((Path(__file__).resolve().parents[1]/entry['data_file']).read_text(encoding='utf8'));kind=entry['diagram'];h=1290 if kind=='exopop-hosts' else 1510 if kind=='exopop-flux' else 950
 im=Image.new('RGB',(1100,h),BG);d=ImageDraw.Draw(im)
 if kind=='exopop-hosts':
  txt(d,50,35,'Kolem jakých hvězd obíhají známé exoplanety?',34);txt(d,50,100,'NASA Exoplanet Archive • údaje staženy 29. 10. 2026',25,MUTED)
  txt(d,50,145,f"{data['total_planets']:,} planet / {data['host_names']:,} hostitelů".replace(',',' '),30,BLUE)
  x0,x1=500,875;top=260;mx=4500
  for v in [0,1500,3000,4500]:
   x=x0+(x1-x0)*v/mx;d.line((x,top-25,x,top+8*100-25),fill=GRID,width=1);d.text((x-18,top-65),str(v),font=font(20),fill=MUTED)
  for i,g in enumerate(data['groups']):
   y=top+i*100;label=g['label'].replace(' — ','\n')
   for j,line in enumerate(label.split('\n')):txt(d,50,y+j*32,line,24,MUTED if j else WHITE,width=435)
   x=x0+(x1-x0)*g['count']/mx;d.rectangle((x0,y+10,max(x0+2,x),y+38),fill=GOLD if g['key']=='missing' else BLUE)
   txt(d,910,y,str(g['count']),27);txt(d,910,y+36,num(g['percent'],1)+' %',23,MUTED)
  y=1100;y=txt(d,50,y,'Každá planeta je v právě jedné skupině. Procenta mají společný základ 6 451 planet.',25,MUTED)
  txt(d,50,y+10,'U 4 034 planet chybí v archivu spektrální třída hvězdy. Jiné vlastnosti těchto hvězd mohou být známé.',25,MUTED)
 elif kind=='exopop-flux':
  txt(d,50,35,'Kolik energie dostávají vybrané planety?',36);txt(d,50,100,'Příjem hvězdné energie na jednotku plochy • Země = 1',25,MUTED)
  x0,x1=425,1015;top=245;rows=data['sample']+[{'pl_name':'Země — srovnání','hostname':'Slunce','pl_insol':1,'pl_insolerr1':None,'pl_insolerr2':None}]
  def xx(v):return x0+(x1-x0)*v/2
  for v in [0,.5,1,1.5,2]:
   x=xx(v);d.line((x,top-28,x,top+len(rows)*100-18),fill=BLUE if v==1 else GRID,width=2 if v==1 else 1);txt(d,x-15,top-70,num(v,1),22,MUTED,width=100)
  for i,e in enumerate(rows):
   y=top+i*100;v=e['pl_insol'];x=xx(v);band=data['host_habitable_bands'][e['hostname']]
   if band['wide_low'] is not None:d.rectangle((xx(band['wide_low']),y-4,xx(band['wide_high']),y+35),fill='#77613f')
   d.rectangle((xx(band['green_low']),y+2,xx(band['green_high']),y+29),fill='#347455')
   txt(d,50,y-12,e['pl_name'],27);txt(d,50,y+25,'Příjem energie: '+num(v,3).rstrip('0').rstrip(','),22,MUTED)
   lo=v+(e.get('pl_insolerr2') or 0);hi=v+(e.get('pl_insolerr1') or 0);a,b=xx(lo),xx(hi)
   d.line((a,y+14,b,y+14),fill=WHITE,width=4)
   for pos in [a,b]:d.line((pos,y+6,pos,y+22),fill=WHITE,width=3)
   d.ellipse((x-7,y+7,x+7,y+21),fill=WHITE,outline=BG,width=2)
  d.rectangle((50,1195,83,1216),fill='#347455');txt(d,95,1189,'Užší obyvatelná zóna',24,MUTED,width=450)
  d.rectangle((590,1195,623,1216),fill='#77613f');txt(d,635,1189,'Širší obyvatelná zóna',24,MUTED,width=430)
  y=1255;y=txt(d,50,y,'Bod: příjem energie planety. Úsečka: rozmezí odhadu podle měření. Pásmo v každém řádku odpovídá hostitelské hvězdě.',25,MUTED)
  txt(d,50,y+12,'TRAPPIST-1: publikované orientační pásmo. Ostatní hvězdy: model pro planetu o hmotnosti Země. Podrobnosti a zdroje v textu.',24,MUTED)
 elif kind=='exopop-hz':
  txt(d,50,35,'Jak se mění hranice obyvatelné zóny?',37);txt(d,50,100,'Ukázkový model pro planetu o hmotnosti Země',27,MUTED)
  x0,x1=400,1010
  for v in [0,.5,1,1.5,2]:
   x=x0+(x1-x0)*v/2;d.line((x,240,x,685),fill=GRID,width=1);txt(d,x-15,195,num(v,1),22,MUTED,width=100)
  for i,(label,t) in enumerate([('Slunce • 5 780 K',5780),('Hvězda K • 5 000 K',5000),('Hvězda M • 3 500 K',3500)]):
   y=275+i*140;txt(d,50,y,label,26,width=335)
   early=hz_flux(t,'early_mars');recent=hz_flux(t,'recent_venus');outer=hz_flux(t,'maximum');inner=hz_flux(t,'runaway')
   def xx(v):return x0+(x1-x0)*v/2
   d.rectangle((xx(early),y,xx(recent),y+38),fill='#77613f');d.rectangle((xx(outer),y+8,xx(inner),y+30),fill=GREEN)
   txt(d,x0,y+48,'Užší: '+num(outer)+' až '+num(inner)+' • širší: '+num(early)+' až '+num(recent),22,MUTED,width=650)
  txt(d,50,720,'Zelená: užší zóna. Hnědozlatá: širší zóna. Vodorovně příjem energie, Země = 1.',25,MUTED)
  txt(d,50,790,'Model Kopparapu a kol. (2014), pro hvězdy hlavní posloupnosti. Hranice závisejí na zvoleném klimatickém modelu; graf neposuzuje skutečné atmosféry planet.',25,MUTED)
 else:raise ValueError(kind)
 d.text((50,h-40),'Vlastní datový graf • Kosmologické novinky • zdroje a metodika v článku',font=font(20),fill=MUTED)
 return im