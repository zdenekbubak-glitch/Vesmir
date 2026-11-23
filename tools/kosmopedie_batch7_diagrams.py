"""Original historical-method illustrations; no portraits or reproduced historical data."""
import math
from kosmopedie_diagrams import Canvas,font,WHITE,MUTED,BLUE,GOLD,VIOLET,GREEN,GRID

def diagram(entry):
 c=Canvas(entry['title']);k=entry['diagram']
 if k=='edu-b7-timeline':
  for i,(date,name,what,col) in enumerate([('1912','Leavittová','Cefeidy s delší periodou mají vyšší svítivost.',BLUE),('1927','Lemaître','Ze vzdáleností a rychlostí galaxií odhadl tempo rozpínání.',GOLD),('1929','Hubble','Vzdálenější galaxie se v průměru vzdalují rychleji.',VIOLET),('1970 a dále','Rubinová a Ford','Rychlý oběh hvězd na okrajích galaxií naznačuje temnou hmotu.',GREEN)]):
   y=100+110*i;c.box(60,y,1140,y+90,col);c.text(80,y+25,date,col,25);c.text(290,y+25,name,WHITE,26);c.paragraph(525,y+(26 if c.d.textlength(what,font=font(24))<=595 else 10),what,595,WHITE,24)
  c.text(60,550,'Vybrané milníky; navazují na práci dalších pozorovatelů, teoretiků a týmů.',MUTED,21,maxwidth=1080)
 elif k=='edu-b7-leavitt':
  for j,(x,period,label,col) in enumerate([(80,90,'kratší perioda',BLUE),(660,180,'delší perioda',GOLD)]):
   c.box(x,110,x+460,480,col)
   c.line([(x+25+i,270-55*math.sin(i*math.tau/period)) for i in range(410)],col,4)
   c.text(x+25,135,'Jasnost v čase',WHITE,25)
   c.text(x+25,350,label,col,29)
   c.text(x+25,410,'nižší svítivost' if j==0 else 'vyšší svítivost',WHITE,26)
  c.text(65,530,'Porovnání cefeid stejného typu. Křivky jsou názorné, ne původní měření.',MUTED,23,maxwidth=1070)
 elif k=='edu-b7-distance':
  for i,(title,body,col) in enumerate([('Změříme periodu','Jak dlouho trvá cyklus jasnosti?',BLUE),('Určíme svítivost','Delší perioda značí větší svítivost.',GOLD),('Odvodíme vzdálenost','Porovnáme svítivost s jasností na obloze.',VIOLET)]):
   x=55+385*i;c.box(x,160,x+320,450,col);c.paragraph(x+20,185,title,280,col,29);c.paragraph(x+20,290,body,280,WHITE,26)
   if i<2:c.arrow(x+325,305,x+375,305,MUTED)
  c.text(65,510,'Vztah kalibrujeme na cefeidách se známou vzdáleností.',WHITE,25)
  c.text(65,550,'Při praktickém měření se opravuje i vliv prachu a vlastností hvězdy.',MUTED,22,maxwidth=1070)
 elif k=='edu-b7-lemaitre':
  for y,spacing,label in [(220,122,'dříve'),(398,205,'později')]:
   c.text(70,y-15,label,WHITE,28)
   xs=[665+j*spacing for j in (-2,-1,0,1,2)]
   for j,x in enumerate(xs):
    c.circle(x,y,10,GOLD,GOLD,1)
    if j:
     c.line([(xs[j-1]+10,y+35),(x-10,y+35)],BLUE,3)
  c.text(300,105,'Tytéž značky, větší vzájemné vzdálenosti',WHITE,27)
  c.text(65,505,'Stejné zvětšení rozestupů uvidíme od kterékoliv značky.',MUTED,23)
  c.text(65,550,'Jednorozměrná analogie. Kresba zachycuje jen malý výsek prostoru.',MUTED,22)
 elif k=='edu-b7-hubble':
  c.arrow(140,470,1080,470,MUTED);c.arrow(140,470,140,130,MUTED)
  c.text(160,100,'rychlost vzdalování',WHITE,25);c.text(800,500,'vzdálenost',WHITE,25)
  c.line([(140,470),(1000,170)],BLUE,4)
  for x,y in [(250,432),(370,365),(505,358),(630,278),(780,270),(930,190)]:c.circle(x,y,7,GOLD,GOLD,1)
  c.text(670,160,'celkový trend',BLUE,25)
  c.text(65,550,'Smyšlené body ilustrují vztah a rozptyl; nejde o Hubbleova původní data.',MUTED,22,maxwidth=1080)
 elif k=='edu-b7-rubin':
  for x,col,title,body in [(65,BLUE,'Spektrum','Posuny čar v různých částech galaxie.'),(650,GOLD,'Rotační křivka','Oběžná rychlost podle vzdálenosti od středu.')]:
   c.box(x,120,x+485,455,col);c.text(x+25,145,title,col,31);c.paragraph(x+25,320,body,430,WHITE,26)
  for x in [160,200,250]:c.line([(x,220),(x,280)],BLUE,4)
  c.arrow(700,280,1050,280,MUTED);c.arrow(700,280,700,200,MUTED)
  c.line([(710+i,275-55*(1-math.exp(-i/45))) for i in range(300)],GOLD,4)
  c.arrow(565,265,635,265,WHITE)
  c.text(65,525,'Zohledníme sklon galaxie a rozdíly pohybu jejích částí.',MUTED,24,maxwidth=1080)
 elif k=='edu-b7-rotation':
  x0,y0=140,470;c.arrow(x0,y0,1080,y0,MUTED);c.arrow(x0,y0,x0,130,MUTED)
  c.text(160,100,'oběžná rychlost',WHITE,25);c.text(670,505,'vzdálenost od středu',WHITE,25)
  c.line([(140+i,470-240*(1-math.exp(-i/100))) for i in range(880)],GOLD,4)
  c.line([(140+i,470-240*(1-math.exp(-i/100))*(1 if i<200 else math.sqrt(200/i))) for i in range(880)],BLUE,4)
  c.text(570,190,'model s halem temné hmoty',GOLD,25)
  c.text(520,375,'model s hmotou soustředěnou u středu',BLUE,23,maxwidth=550)
  c.text(65,550,'Dva názorné modelové průběhy bez číselné stupnice; nejde o naměřené křivky.',MUTED,21,maxwidth=1080)
 elif k=='edu-b7-supernova-expansion':
  c.text(65,90,'Porovnání vzdálených supernov typu Ia při stejném rudém posuvu',WHITE,25)
  for x,label,body,col,strength in [
      (65,'Předpověď modelu','Bez zrychlování by supernovy v uvažovaném modelu byly jasnější.',BLUE,320),
      (630,'Pozorování','Supernovy byly slabší. To ukazovalo na větší vzdálenost.',GOLD,220)]:
   c.box(x,155,x+500,430,col)
   c.text(x+24,178,label,col,29)
   c.paragraph(x+24,235,body,450,WHITE,25)
   c.d.rounded_rectangle((x+24,357,x+24+strength,377),radius=9,fill=col)
  c.text(65,467,'Slabší jas po kalibraci odpovídal zrychlování rozpínání.',WHITE,24)
  c.text(65,530,'Délky pruhů znázorňují relativní jas. Hodnoty jsou pouze názorné.',MUTED,22)
 else:raise ValueError(k)
 return c.finish()
