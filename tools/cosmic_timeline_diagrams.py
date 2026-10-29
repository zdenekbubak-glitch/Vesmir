"""Reproducible Czech cosmic timelines. Times are approximate cosmic ages.

Sources and scope: catalog metadata and each article's bibliography. The first
three detail panels use log(time); the late panel uses linear cosmic age.
Intervals describe gradual transitions, not confidence intervals.
"""
import math,textwrap
from PIL import Image,ImageDraw
from article_image_assets import font
BG='#0b1424';CARD='#17243a';WHITE='#eef4ff';MUTED='#b9c9dd';BLUE='#79cfff';GOLD='#ffd287';GREEN='#91dfbd';GRID='#35455e'
PANELS={
'first':dict(title='První zlomky sekundy',subtitle='Od 10^-12 sekundy do přibližně 1 sekundy',unit='sekundy',lo=1e-12,hi=1,log=True,ticks=[(1e-12,'10^-12'),(1e-9,'10^-9'),(1e-6,'10^-6'),(1e-3,'10^-3'),(1,'1 s')],rows=[
('Horká částicová látka','10^-12 až přibližně 10^-5 s','Kvarky, gluony a další částice se často srážejí. Při rozpínání teplota klesá.',1e-12,1e-5),
('Vznik protonů a neutronů','řádově kolem 10^-5 s','Kvarky se vážou do složených částic. Protony a neutrony jsou stavebními částmi jader.',1e-5,1e-5),
('Neutrina se postupně oddělují','řádově kolem 1 s','Srážky neutrin s okolní látkou řídnou. Neutrina začínají putovat mnohem volněji.',.1,1)],note='10^-12 s = biliontina sekundy; 10^-6 s = miliontina. Rozsahy jsou orientační.',extra='Oddělování neutrin pokračuje i po první sekundě. Inflaci vysvětluje samostatné téma.'),
'minutes':dict(title='První minuty vesmíru',subtitle='Od 1 sekundy do přibližně 20 minut',unit='sekundy',lo=1,hi=1200,log=True,ticks=[(1,'1 s'),(10,'10 s'),(100,'100 s'),(1200,'20 min')],rows=[
('Ustaluje se poměr protonů a neutronů','kolem 1 s a dále','Vzájemné přeměny zpomalují. Část volných neutronů se před tvorbou jader rozpadne.',1,180),
('Ubývá elektronů a pozitronů','během prvních minut','Většina párů anihiluje a předává energii záření. Malý přebytek elektronů zůstává.',1,180),
('Deuterium otevírá cestu k heliu','přibližně 2 až 5 minut','Po ochlazení přežívají jádra deuteria. Navazující reakce rychle vytvářejí helium-4.',120,300),
('Jaderné reakce postupně utichají','přibližně 5 až 20 minut','Klesá teplota i hustota. Zůstává hlavně vodík a helium, se stopami dalších lehkých jader.',300,1200)],note='Fotony existují již v této horké látce. Vznik neutrálních atomů přijde mnohem později.',extra='Pásy ukazují přibližné doby hlavního průběhu; procesy se časově překrývají.'),
'light':dict(title='Od plazmatu k prvním galaxiím',subtitle='Od 20 minut do první miliardy let',unit='roky',lo=1200/31557600,hi=1e9,log=True,ticks=[(1200/31557600,'20 min'),(1,'1 rok'),(1e4,'10 tisíc let'),(1e9,'1 mld. let')],rows=[
('Dlouhá etapa horkého plazmatu','od prvních minut do asi 380 tisíc let','Jádra a volné elektrony tvoří plazma. Světlo se často rozptyluje na elektronech.',1200/31557600,380000),
('Hmota přebírá převahu nad zářením','přibližně 50 tisíc let','Hustoty energie hmoty a záření se vyrovnají. Poté převládá hmota; rostou zárodky struktur.',50000,50000),
('Vznik atomů a uvolnění reliktního světla','přibližně 380 tisíc let','Elektrony se vážou do atomů. Ubyde rozptylů a světlo může putovat mnohem volněji.',300000,500000),
('Temné věky, pak první hvězdy a galaxie','první hvězdy řádově po 100 až 200 milionech let','Gravitace zhušťuje plyn. Začíná hvězdná tvorba a rostou první galaxie; přesné začátky zkoumáme.',380000,300000000),
('Reionizace mezigalaktického vodíku','během prvních stovek milionů let až asi 1 miliardy','Záření prvních zdrojů postupně znovu odděluje elektrony od atomů v řídkém plynu.',150000000,1000000000)],note='První hvězdy nemají jediné přesně známé datum. Temné věky končí postupně v různých místech.',extra='Drobné časové úseky jsou zvýrazněny kroužkem; pás je vyznačen ve skutečném měřítku osy.'),
'late':dict(title='Od prvních galaxií k dnešku',subtitle='Od 1 do 13,8 miliardy let',unit='miliardy let',lo=1,hi=13.8,log=False,ticks=[(1,'1'),(4,'4'),(7,'7'),(10,'10'),(13.8,'13,8')],rows=[
('Galaxie a kosmická síť dále rostou','od první miliardy let až do dneška','Přitéká plyn, vznikají hvězdy a galaxie se slučují. Mění se jejich velikost, složení i okolí.',1,13.8),
('Vrchol kosmické hvězdné tvorby','zhruba 2 až 4 miliardy let','V průměru vznikají hvězdy nejrychleji. Později celková rychlost jejich tvorby klesá.',2,4),
('Rozpínání se začíná zrychlovat','asi 7,7 miliardy let v základním modelu ΛCDM','Vliv temné energie převáží nad gravitačním zpomalováním. Jde o vývoj velkých měřítek.',7.7,7.7),
('Vznik Slunce a Sluneční soustavy','asi 9,2 miliardy let; tedy před 4,6 miliardy let','Z místního oblaku plynu a prachu vzniká Slunce a planety včetně Země.',9.2,9.2),
('Dnešní vesmír','přibližně 13,8 miliardy let','Pozorujeme galaxie různého stáří a skládáme jejich světlo do příběhu kosmického vývoje.',13.8,13.8)],note='Čísla na ose znamenají stáří vesmíru. Dobu před dneškem získáme odečtením od 13,8.',extra='Začátek zrychlování je dřívější než převaha temné energie nad hmotou v energetické bilanci.')}

def draw_text(d,xy,text,size=30,color=WHITE,width=940):
 f=font(size);words=text.split();line='';y=xy[1]
 for w in words:
  trial=(line+' '+w).strip()
  if d.textbbox((0,0),trial,font=f)[2]>width and line:d.text((xy[0],y),line,font=f,fill=color);y+=size+10;line=w
  else:line=trial
 if line:d.text((xy[0],y),line,font=f,fill=color);y+=size+10
 return y

def diagram(entry):
 key=entry['diagram'].removeprefix('timeline-')
 if key=='overview':
  im=Image.new('RGB',(1100,1390),BG);d=ImageDraw.Draw(im);draw_text(d,(55,35),'Vývoj vesmíru: přehled čtyř etap',38,width=990)
  draw_text(d,(55,105),'Orientační posloupnost etap; vzdálenosti zde nevyjadřují délku času.',26,MUTED,width=990)
  cards=[('1','První sekunda','10^-12 s → přibližně 1 s','Horké částice, vznik protonů a neutronů, oddělování neutrin.'),('2','První minuty','1 s → přibližně 20 minut','Tvorba jader deuteria a helia; látka i záření dál chladnou.'),('3','Cesta k prvním galaxiím','20 minut → 1 miliarda let','Vznik atomů a uvolnění reliktního světla, první hvězdy a reionizace.'),('4','Pozdější vývoj','1 → 13,8 miliardy let','Růst galaxií, vrchol hvězdné tvorby, Sluneční soustava a dnešek.')]
  for j,(n,title,t,desc) in enumerate(cards):
   y=215+j*240;d.rounded_rectangle((50,y,1050,y+210),radius=18,fill=CARD);d.text((75,y+20),n,font=font(54),fill=GOLD);draw_text(d,(160,y+18),title,34,width=850);draw_text(d,(160,y+68),t,29,BLUE,width=850);draw_text(d,(160,y+112),desc,29,MUTED,width=820)
   if j<3:d.line((550,y+214,550,y+232),fill=BLUE,width=4)
  d.rounded_rectangle((50,1190,1050,1315),radius=12,outline=MUTED,width=2)
  for y in range(1200,1300,14):d.line((65,y+12,85,y),fill=GRID,width=2)
  draw_text(d,(105,1210),'Hypotetická dřívější inflace: podrobně ji vysvětluje samostatné téma.',27,MUTED,width=900)
 else:
  p=PANELS[key];h=540+len(p['rows'])*205;im=Image.new('RGB',(1100,h),BG);d=ImageDraw.Draw(im)
  draw_text(d,(55,30),p['title'],40,width=990);draw_text(d,(55,93),p['subtitle'],31,BLUE,width=990)
  rule='Logaritmická osa: stejný krok znamená stejný násobek času.' if p['log'] else 'Lineární osa: stejná vzdálenost znamená stejnou dobu.'
  draw_text(d,(55,148),rule,25,MUTED,width=990)
  def pos(t):
   a,b,c=(math.log10(t),math.log10(p['lo']),math.log10(p['hi'])) if p['log'] else (t,p['lo'],p['hi'])
   return 75+950*(a-b)/(c-b)
  for t,label in p['ticks']:
   x=pos(t);w=d.textbbox((0,0),label,font=font(24))[2];d.text((max(40,min(1060-w,x-w/2)),220),label,font=font(24),fill=MUTED)
  for j,(title,when,desc,start,end) in enumerate(p['rows']):
   y=270+j*205;d.rounded_rectangle((50,y,1050,y+188),radius=14,fill=CARD)
   draw_text(d,(72,y+12),title,30,width=950);draw_text(d,(72,y+56),when,25,GOLD,width=950)
   draw_text(d,(72,y+94),desc,25,MUTED,width=950)
   yy=y+173;d.line((75,yy,1025,yy),fill=GRID,width=3)
   for t,label in p['ticks']:d.line((pos(t),yy-6,pos(t),yy+6),fill=MUTED,width=2)
   a,b=pos(start),pos(end);d.line((a,yy,b,yy),fill=BLUE,width=9)
   if b-a<12:d.ellipse((a-7,yy-7,a+7,yy+7),fill=BG,outline=GOLD,width=3)
  yy=285+len(p['rows'])*205;yy=draw_text(d,(55,yy),p['note'],25,MUTED,width=990);draw_text(d,(55,yy+12),p['extra'],24,MUTED,width=990)
 d.text((55,im.height-40),'Čas od počátku horkého vývoje • přibližné údaje • Kosmologické novinky',font=font(20),fill=MUTED)
 return im