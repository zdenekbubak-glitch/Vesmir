"""Reproducible orbital-distance comparison, AU; circles use semimajor axes."""
from PIL import Image,ImageDraw
from article_image_assets import font
from exoplanet_population_diagrams import txt,hz_flux
import math
BG='#0b1424';WHITE='#edf4ff';MUTED='#bac8db';BLUE='#7dcfff';GREEN='#8de0b1';BAND='#245143';GRID='#35465e';GOLD='#ffd287'
TRAPPIST=[('b',.01154),('c',.01580),('d',.02227),('e',.02925),('f',.03849),('g',.04683),('h',.06189)]
SOLAR=[('Merkur',.3871,-145),('Venuše',.7233,-65),('Země',1.,30),('Mars',1.5237,145)]
TRAPPIST_HZ=(.024,.049) # Illustrative published interval: Gillon et al. 2016, Nature 533, 221.
SOLAR_HZ=(math.sqrt(1/hz_flux(5780,'runaway')),math.sqrt(1/hz_flux(5780,'maximum')))

def diagram(entry):
 im=Image.new('RGB',(1100,1450),BG);d=ImageDraw.Draw(im)
 txt(d,45,30,'TRAPPIST-1 a Sluneční soustava',39)
 txt(d,45,90,'Nahoře stejné měřítko vzdáleností • dole zvětšený detail',26,BLUE)
 txt(d,55,165,'Vnitřní Sluneční soustava',28)
 txt(d,650,165,'TRAPPIST-1',29)
 scale=120.;cy=440
 for cx,hz,solar in [(275,SOLAR_HZ,True),(825,TRAPPIST_HZ,False)]:
  ro,ri=hz[1]*scale,hz[0]*scale
  d.ellipse((cx-ro,cy-ro,cx+ro,cy+ro),fill=BAND)
  d.ellipse((cx-ri,cy-ri,cx+ri,cy+ri),fill=BG)
  if solar:
   for name,a,angle in SOLAR:
    rr=a*scale;d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),outline=MUTED,width=2)
    theta=math.radians(angle);x=cx+rr*math.cos(theta);y=cy+rr*math.sin(theta)
    d.ellipse((x-5,y-5,x+5,y+5),fill=BLUE)
    txt(d,x+9,y-13,name,21,width=150)
  else:
   for name,a in TRAPPIST:
    rr=a*scale;d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),outline=BLUE,width=1)
   d.line((cx+10,cy,cx+55,cy-40,cx+170,cy-40),fill=BLUE,width=2)
   txt(d,cx+35,cy-115,'Všech 7 planet',23,BLUE,width=200)
   txt(d,cx+35,cy-84,'v této oblasti',23,BLUE,width=200)
  d.ellipse((cx-4,cy-4,cx+4,cy+4),fill=GOLD)
  txt(d,cx-26,cy+15,'Slunce' if solar else 'hvězda',18,GOLD,width=120)
  y=700;d.line((cx-90,y,cx+30,y),fill=WHITE,width=3)
  for xx in [cx-90,cx+30]:d.line((xx,y-7,xx,y+7),fill=WHITE,width=2)
  txt(d,cx-60,y+14,'1 AU',24)
 txt(d,45,770,'I planeta h obíhá asi 6× blíže ke své hvězdě než Merkur ke Slunci.',27,WHITE)
 txt(d,45,825,'Detail TRAPPIST-1 • vzdálenosti zvětšené přibližně 107×',28,BLUE)
 x0,x1,y=100,1000,1070
 def xx(a):return x0+(x1-x0)*a/.07
 d.rectangle((xx(TRAPPIST_HZ[0]),940,xx(TRAPPIST_HZ[1]),1130),fill=BAND)
 txt(d,xx(.025),945,'Obyvatelné pásmo',23,GREEN,width=330)
 d.line((x0,y,x1,y),fill=MUTED,width=2)
 for v in [0,.01,.02,.03,.04,.05,.06,.07]:
  x=xx(v);d.line((x,y+64,x,y+74),fill=MUTED,width=2)
  label='0' if not v else f'{v:.2f}'.replace('.',',');txt(d,x-23,y+78,label,20,MUTED,width=85)
 d.ellipse((x0-7,y-7,x0+7,y+7),fill=GOLD)
 for name,a in TRAPPIST:
  x=xx(a);col=GREEN if name in 'efg' else BLUE
  d.ellipse((x-7,y-7,x+7,y+7),fill=col)
  txt(d,x-8,y-52,name,29,col,width=45)
  # Axis ticks carry distances; avoid crowded duplicate labels.
 txt(d,940,1180,'AU',20,MUTED)
 txt(d,45,1210,'1 AU je vzdálenost Země od Slunce (přibližně 150 milionů km).',24,MUTED)
 txt(d,45,1260,'Zelená označuje orientační oblast pro kapalnou vodu při vhodné atmosféře.',24,GREEN)
 txt(d,45,1310,'Kružnice znázorňují velikosti drah. Značky planet a hvězd jsou schematické; jejich polohy nejsou záznamem konkrétního okamžiku.',23,MUTED)
 txt(d,45,1405,'Vlastní schéma • dráhy: Agol a kol. / NASA • hranice pásma: viz zdroje v tématu',19,MUTED)
 return im
