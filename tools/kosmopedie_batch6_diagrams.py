"""Original explanatory diagrams for cosmological models. No observational data."""
import math
from kosmopedie_diagrams import Canvas,WHITE,MUTED,BLUE,GOLD,VIOLET,GREEN,GRID

def diagram(entry):
 c=Canvas(entry['title']);k=entry['diagram']
 if k=='edu-b6-extensions':
  rows=[('Složení','Temná energie, temná hmota, neutrina',BLUE),('Geometrie','Prostorové zakřivení a rozpínání',GOLD),('Pravidla','Gravitace a vývoj nerovnoměrností',VIOLET)]
  for i,(a,b,col) in enumerate(rows):
   y=110+145*i;c.box(65,y,1135,y+110,col);c.text(90,y+28,a,col,29);c.paragraph(365,y+25,b,730,WHITE,26)
  c.text(65,550,'Rozšíření musí vysvětlit nová data a zachovat dosavadní úspěchy.',MUTED,23,maxwidth=1080)
 elif k=='edu-b6-energy':
  for x,col,title,body in [(65,BLUE,'Kosmologická konstanta','Hustota energie zůstává stejná.'),(650,GOLD,'Proměnlivá složka','Hustota energie se může vyvíjet.')]:
   c.box(x,115,x+485,460,col);c.text(x+25,135,title,col,29,maxwidth=435)
   c.paragraph(x+25,325,body,430,WHITE,28)
  c.line([(100,270),(510,270)],BLUE,5)
  c.line([(685+i,235+70*(i/410)**.7) for i in range(411)],GOLD,5)
  c.text(90,485,'dříve → později',BLUE,25);c.text(675,485,'dříve → později',GOLD,25)
  c.text(65,545,'Ilustrace dvou možností; směr změny proměnlivé složky není předem daný.',MUTED,22,maxwidth=1080)
 elif k=='edu-b6-density':
  x0,y0=135,470;w,h=920,300
  c.arrow(x0,y0,x0+w+20,y0,MUTED);c.arrow(x0,y0,x0,130,MUTED)
  c.text(155,100,'hustota / výchozí hustota',WHITE,25)
  for val in (.6,.8,1):
   y=y0-h*val;c.line([(x0,y),(x0+w,y)],GRID,1);c.text(70,y-15,str(val).replace('.',','),MUTED,21)
  c.line([(x0+i,y0-h) for i in range(w+1)],BLUE,5)
  c.line([(x0+i,y0-h*(1+i/w)**(-.6)) for i in range(w+1)],GOLD,5)
  for x,t in [(x0,'1'),(x0+w//2,'1,5'),(x0+w,'2')]:c.text(x-10,480,t,MUTED,22)
  c.text(730,510,'měřítko / výchozí měřítko',WHITE,22)
  c.text(550,132,'Λ: w = −1 → 100 %',BLUE,26)
  c.text(610,325,'w = −0,8 → asi 66 %',GOLD,26)
  c.text(65,550,'Výpočet ρ / ρ₀ = (a / a₀)⁻³⁽¹⁺ʷ⁾ pro samostatně se vyvíjející složku; příklady, ne data.',MUTED,20,maxwidth=1080)
 elif k=='edu-b6-gravity':
  c.box(365,100,835,205,BLUE);c.text(415,130,'Stejná kosmická struktura',WHITE,29,maxwidth=370)
  c.arrow(475,220,315,300,BLUE);c.arrow(725,220,885,300,GOLD)
  for x,col,t,b in [(65,BLUE,'Pohyb galaxií','Jak gravitace působí na hmotu?'),(650,GOLD,'Ohyb světla','Jak mění obrazy vzdálených galaxií?')]:
   c.box(x,310,x+485,475,col);c.text(x+25,330,t,col,30);c.paragraph(x+25,390,b,425,WHITE,25)
  c.text(65,520,'Společná předpověď pro oba jevy prověřuje gravitační pravidla.',WHITE,24,maxwidth=1080)
  c.text(65,555,'Pojmové schéma: změna gravitace může změnit vztah mezi oběma měřeními.',MUTED,21,maxwidth=1080)
 elif k=='edu-b6-mond':
  for x,col,t in [(65,BLUE,'Přidat temnou hmotu'),(650,GOLD,'Změnit gravitační vztah')]:
   c.box(x,110,x+485,500,col);c.text(x+25,130,t,col,28,maxwidth=430)
  for rr in [65,100,135]:c.d.ellipse((305-rr,310-rr*.65,305+rr,310+rr*.65),outline=BLUE,width=2)
  c.d.ellipse((245,300,365,320),fill=WHITE)
  c.paragraph(90,425,'Běžná hmota + neviditelné halo',425,WHITE,24)
  c.text(690,250,'Stejná běžná hmota',WHITE,28)
  c.arrow(885,300,885,350,GOLD)
  c.text(690,380,'Jiný výpočet zrychlení',GOLD,27)
  c.text(65,545,'Dvě strategie vysvětlení; obrázek neprokazuje správnost ani jedné.',MUTED,23,maxwidth=1080)
 elif k=='edu-b6-tests':
  rows=[('Galaxie','Rotační rychlosti a rozložení běžné hmoty',BLUE),('Kupy galaxií','Pohyby, horký plyn a gravitační čočkování',GOLD),('Celý vesmír','Reliktní záření a růst velkých struktur',VIOLET)]
  for i,(t,b,col) in enumerate(rows):
   y=110+i*140;c.box(65,y,1135,y+105,col);c.text(90,y+25,t,col,29,maxwidth=300);c.paragraph(425,y+27,b,670,WHITE,25)
  c.text(65,545,'Úspěch u jedné skupiny měření je nutné ověřit i u dalších.',MUTED,24,maxwidth=1080)
 elif k=='edu-b6-comparison':
  rows=[('Předpověď','Co model říká, že máme změřit?',BLUE),('Nejistoty','Jak přesně měříme a co může výsledek posunout?',GOLD),('Další zkouška','Obstojí stejné parametry i v jiných datech?',VIOLET)]
  for i,(a,b,col) in enumerate(rows):
   y=110+140*i;c.box(65,y,1135,y+105,col);c.text(90,y+25,a,col,28,maxwidth=300);c.paragraph(425,y+24,b,670,WHITE,25)
  c.text(65,545,'Hodnotíme také volnost modelu: počet a přípustné rozsahy parametrů.',MUTED,23,maxwidth=1080)
 elif k=='edu-b6-overfit':
  c.text(65,90,'Smyšlené body: nastavení modelu a další nezávislé měření',WHITE,25)
  x0,y0=130,460;c.arrow(x0,y0,1090,y0,MUTED);c.arrow(x0,y0,x0,155,MUTED)
  pts=[(210,405),(370,330),(530,335),(690,240)]
  c.line([(165,430),(1045,180)],BLUE,4)
  c.line([(165,440),*pts,(775,130),(850,420),(945,200),(1045,405)],GOLD,4)
  for x,y in pts:c.circle(x,y,7,WHITE,WHITE,1)
  c.circle(970,205,10,GREEN,None,4)
  c.text(740,150,'další měření',GREEN,24)
  c.text(180,490,'Jednoduchý trend',BLUE,24);c.text(570,490,'Volná křivka přes všechny body',GOLD,24)
  c.text(65,545,'Názorná ilustrace přeučení; nejde o kosmologická data ani statistický výsledek.',MUTED,22,maxwidth=1080)
 else:raise ValueError(k)
 return c.finish()
