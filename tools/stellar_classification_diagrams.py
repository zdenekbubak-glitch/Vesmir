"""Qualitative stellar classification diagrams; not observed stellar samples."""
from PIL import Image,ImageDraw
from article_image_assets import font
BG='#0b1424';WHITE='#edf4ff';MUTED='#b9c9dd';BLUE='#7dcfff';GOLD='#ffd287';GRID='#35465e'
CLASSES=[('O','40 000 K','#88aaff'),('B','20 000 K','#b3caff'),('A','9 000 K','#edf2ff'),('F','7 000 K','#fff3d6'),('G','5 800 K','#ffe5a0'),('K','4 500 K','#ffbc85'),('M','3 000 K','#ff8d76')]
def text(d,x,y,s,size=28,color=WHITE,width=990):
 f=font(size);line=''
 for w in s.split():
  trial=(line+' '+w).strip()
  if d.textbbox((0,0),trial,font=f)[2]>width and line:d.text((x,y),line,font=f,fill=color);y+=size+9;line=w
  else:line=trial
 if line:d.text((x,y),line,font=f,fill=color);y+=size+9
 return y

def diagram(entry):
 kind=entry['diagram'];im=Image.new('RGB',(1100,1150 if kind=='stellarclass-sequence' else 1050),BG);d=ImageDraw.Draw(im)
 if kind=='stellarclass-sequence':
  text(d,50,35,'Jak číst spektrální třídy hvězd',40);text(d,50,105,'O → B → A → F → G → K → M: povrchová teplota klesá',27,BLUE)
  for j,(name,temp,color) in enumerate(CLASSES):
   y=195+j*108;d.ellipse((120,y,180,y+60),fill=color);text(d,310,y+2,name,40);text(d,650,y+7,temp,32,color)
  text(d,50,990,'Uvedené teploty jsou orientační příklady pro jednotlivé třídy. Podtřídy 0–9 řadu dále zpřesňují.',25,MUTED)
  text(d,50,1068,'Barvy jsou schematické; velikost symbolů nevyjadřuje skutečné průměry hvězd.',23,MUTED)
 elif kind=='stellarclass-hr':
  text(d,50,35,'Hvězdy podle teploty a zářivého výkonu',37);text(d,50,100,'Názorné schéma Hertzsprungova–Russellova diagramu',26,MUTED)
  x0,x1,y0,y1=160,1010,220,825;d.line((x0,y0,x0,y1,x1,y1),fill=MUTED,width=3)
  for yy in [330,470,610,750]:d.line((x0,yy,x1,yy),fill=GRID,width=1)
  text(d,45,165,'větší výkon ↑',23,MUTED);text(d,45,850,'menší výkon',23,MUTED)
  text(d,185,855,'teplejší povrch',24,BLUE);text(d,760,855,'chladnější povrch',24,GOLD)
  d.line((365,886,740,886),fill=MUTED,width=3);d.polygon([(740,886),(725,879),(725,893)],fill=MUTED)
  d.line([(240,315),(350,405),(470,515),(610,610),(755,700),(910,775)],fill='#395b77',width=60)
  for j,(x,y) in enumerate([(245,320),(345,400),(460,505),(590,595),(715,675),(810,725),(905,772)]):d.ellipse((x-10,y-10,x+10,y+10),fill=CLASSES[j][2])
  text(d,435,665,'Hlavní posloupnost (V)',28,BLUE,width=470)
  d.ellipse((700,365,985,490),fill='#5a372b');text(d,765,405,'Obři (III)',29,GOLD,width=260)
  d.rounded_rectangle((255,235,990,287),radius=15,fill='#473b30');text(d,470,242,'Veleobři (I)',28,GOLD)
  d.ellipse((240,655,420,745),fill='#283b58');text(d,225,760,'Bílí trpaslíci',25,WHITE,width=260)
  text(d,50,935,'Oblasti ukazují různé skupiny hvězd. Polohy a počty značek jsou pouze ilustrační; osy nemají číselnou stupnici.',25,MUTED)
 else:raise ValueError(kind)
 d.text((50,im.height-33),'Vlastní výukové schéma • Kosmologické novinky',font=font(19),fill=MUTED)
 return im