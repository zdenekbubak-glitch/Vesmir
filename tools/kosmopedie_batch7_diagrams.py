"""Original historical-method illustrations; no portraits or reproduced historical data."""
import math
from kosmopedie_diagrams import Canvas,WHITE,MUTED,BLUE,GOLD,VIOLET,GREEN,GRID

def diagram(entry):
 c=Canvas(entry['title']);k=entry['diagram']
 if k=='edu-b7-timeline':
  for i,(date,name,what,col) in enumerate([('1912','Leavittová','Perioda cefeidy → svítivost',BLUE),('1927','Lemaître','Rozpínání: teorie + pozorování',GOLD),('1929','Hubble','Vzdálenosti + spektrální posuvy',VIOLET),('1970 a dále','Rubinová a Ford','Rotace galaxií → chybějící hmota',GREEN)]):
   y=100+110*i;c.box(60,y,1140,y+90,col);c.text(80,y+25,date,col,25);c.text(290,y+25,name,WHITE,26);c.text(610,y+26,what,WHITE,24,maxwidth=510)
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
  for i,(title,body,col) in enumerate([('Změříme periodu','Jak dlouho trvá cyklus jasnosti?',BLUE),('Určíme svítivost','Pomocí kalibrovaného vztahu.',GOLD),('Odvodíme vzdálenost','Porovnáme ji se zachyceným světlem.',VIOLET)]):
   x=55+385*i;c.box(x,160,x+320,450,col);c.paragraph(x+20,185,title,280,col,29);c.paragraph(x+20,290,body,280,WHITE,26)
   if i<2:c.arrow(x+325,305,x+375,305,MUTED)
  c.text(65,510,'Kalibrace navazuje na vzdálenosti známé jinou metodou.',WHITE,25)
  c.text(65,550,'Při praktickém měření se opravuje i vliv prachu a vlastností hvězdy.',MUTED,22,maxwidth=1070)
 elif k=='edu-b7-lemaitre':
  for y,width,title in [(220,200,'dříve'),(410,380,'později')]:
   c.text(70,y-15,title,WHITE,28)
   for j in range(3):c.circle(320+j*width,y,10,GOLD,GOLD,1)
   c.line([(320,y+35),(320+width,y+35)],BLUE,3)
  c.text(300,105,'Tytéž značky, větší vzájemné vzdálenosti',WHITE,27)
  c.text(65,505,'Příklad rovnoměrného zvětšení měřítka. Žádná značka není vyvoleným středem.',MUTED,23,maxwidth=1080)
  c.text(65,550,'Jednorozměrná analogie, nikoli kresba tvaru nebo okraje vesmíru.',MUTED,22,maxwidth=1080)
 elif k=='edu-b7-hubble':
  c.arrow(140,470,1080,470,MUTED);c.arrow(140,470,140,130,MUTED)
  c.text(160,100,'rychlost vzdalování',WHITE,25);c.text(800,500,'vzdálenost',WHITE,25)
  c.line([(170,450),(1000,170)],BLUE,4)
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
  c.text(570,190,'rozlehlé hmotné halo',GOLD,25)
  c.text(520,375,'hmotnost převážně v centrální oblasti',BLUE,23,maxwidth=550)
  c.text(65,550,'Dva názorné modelové průběhy bez číselné stupnice; nejde o naměřené křivky.',MUTED,21,maxwidth=1080)
 else:raise ValueError(k)
 return c.finish()
