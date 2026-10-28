"""Original teaching diagrams for cosmology and exoplanets; qualitative models."""
import math
from kosmopedie_diagrams import Canvas, WHITE, MUTED, BLUE, GOLD, VIOLET, GREEN, GRID

def diagram(entry):
    c=Canvas(entry['title']);k=entry['diagram']
    if k=='edu-b11-geometry':
        c.text(60,88,'Dvourozměrné analogie prostorové křivosti',WHITE,25)
        for j,(label,col) in enumerate([('kladná',GOLD),('nulová',BLUE),('záporná',VIOLET)]):
            x=60+390*j;c.box(x,150,x+350,500);c.text(x+90,170,label,col,29)
            if j==0:
                c.circle(x+175,330,95,col)
                for ry in [25,55,80]:c.d.ellipse((x+80,330-ry,x+270,330+ry),outline=col,width=2)
                for rx in [25,55]:c.d.ellipse((x+175-rx,235,x+175+rx,425),outline=col,width=2)
                c.text(x+100,450,'povrch koule',MUTED,23)
            elif j==1:
                for t in range(6):
                    c.line([(x+65+t*42,245),(x+65+t*42,420)],col,2)
                    c.line([(x+65,245+t*35),(x+275,245+t*35)],col,2)
                c.text(x+140,450,'rovina',MUTED,23)
            else:
                for t in [-1,-.6,-.2,.2,.6,1]:
                    pts=[(x+175+u*110,335+t*75+(u*u-.5)*t*48) for u in [i/30 for i in range(-30,31)]];c.line(pts,col,2)
                    pts=[(x+175+t*110,335+u*75+(t*t-.5)*u*48) for u in [i/30 for i in range(-30,31)]];c.line(pts,col,2)
                c.text(x+140,450,'sedlo',MUTED,23)
        c.text(60,535,'Geometrie určuje vztahy délek a úhlů; topologie celkové propojení prostoru.',MUTED,22)
    elif k=='edu-b11-fate':
        c.text(60,86,'Tři podmíněné scénáře vzdálené budoucnosti',WHITE,25)
        for j,(label,col) in enumerate([('Big Freeze',BLUE),('Big Crunch',GOLD),('Big Rip',VIOLET)]):
            x=60+j*390;c.box(x,145,x+350,505);c.text(x+65,166,label,col,28)
            c.arrow(x+45,435,x+315,435,MUTED);c.arrow(x+45,435,x+45,225,MUTED)
            pts=[]
            for i in range(101):
                t=i/100
                if j==0:y=25+150*(math.exp(t)-1)/(math.e-1)
                elif j==1:y=40+165*math.sin(math.pi*(.1+.9*t))
                else:y=25+165*(.12/(1.12-t)-.12/1.12)
                pts.append((x+45+255*t,435-y))
            c.line(pts,col,4);c.text(x+190,447,'budoucnost',MUTED,18)
            c.text(x+60,480,['chladnutí a řídnutí','obrat ke smršťování','rozpad vázaných struktur'][j],MUTED,18)
        c.text(60,535,'Svisle: prostorové měřítko. Ilustrační křivky bez časové stupnice v letech.',MUTED,21)
    elif k=='edu-b11-acceleration':
        c.text(60,88,'Vzdálenost dvojice míst ve třech stejně dlouhých časových krocích',WHITE,23)
        for row,(label,ds,col) in enumerate([('stálý přírůstek',[40,90,140,190],BLUE),('rostoucí přírůstek',[40,65,120,205],GOLD)]):
            y=190+row*170;c.text(65,y,label,col,24)
            for j,dist in enumerate(ds):
                xx=320+j*210;c.circle(xx,y+45,6,col,col);c.circle(xx+dist*.7,y+45,6,col,col)
                c.line([(xx,y+45),(xx+dist*.7,y+45)],col,2);c.text(xx,y+80,'t'+str(j),MUTED,20)
        c.text(65,525,'Zrychlování sledujeme v historii vzdáleností; měříme ji pomocí světla.',MUTED,23)
    elif k=='edu-b11-inflation':
        c.text(60,88,'Inflační scénář propojuje raný růst měřítek s pozdějšími strukturami',WHITE,23)
        labels=[('Rychlé rozpínání','zvětšení prostorových měřítek'),('Horká fáze','částice a záření'),('Pozdější stopy','reliktní záření a galaxie')]
        for j,((a,b),col) in enumerate(zip(labels,[VIOLET,GOLD,BLUE])):
            x=55+j*390;c.box(x,170,x+330,470);c.text(x+22,190,a,col,27)
            if j==0:
                for rr in [24,47,75]:c.circle(x+160,325,rr,col)
                for ang in [0,math.pi/2,math.pi,3*math.pi/2]:c.arrow(x+160+35*math.cos(ang),325+35*math.sin(ang),x+160+105*math.cos(ang),325+105*math.sin(ang),col)
            elif j==1:
                for i in range(6):
                    for z in range(3):c.circle(x+55+i*44,280+z*40,6,col,col)
            else:
                for i in range(5):c.line([(x+45,285+i*21),(x+140,325),(x+280,275+i*25)],col,2)
                for xx,yy in [(140,325),(230,300),(70,315)]:c.circle(x+xx,yy,10,GOLD,GOLD)
            c.paragraph(x+20,425,b,290,MUTED,20)
            if j<2:c.arrow(x+340,320,x+380,320)
        c.text(60,530,'Pojmová posloupnost; jednotlivé fáze mají velmi rozdílné délky trvání.',MUTED,22)
    elif k=='edu-b11-bbn':
        c.text(60,88,'Od protonů a neutronů k lehkým jádrům',WHITE,26)
        for x,label in [(120,'proton'),(290,'neutron')]:
            c.circle(x,270,25,GOLD if x==120 else BLUE,GOLD if x==120 else BLUE);c.text(x-40,315,label,MUTED,22)
        c.arrow(355,270,470,270);c.circle(540,257,23,GOLD,GOLD);c.circle(560,285,23,BLUE,BLUE)
        c.text(470,345,'deuterium',WHITE,25);c.text(470,380,'1 proton + 1 neutron',MUTED,19)
        c.arrow(640,270,815,270);c.text(645,180,'další jaderné',MUTED,19);c.text(660,208,'reakce',MUTED,19)
        for dx,dy,col in [(-20,-20,GOLD),(20,20,GOLD),(-20,20,BLUE),(20,-20,BLUE)]:c.circle(945+dx,270+dy,23,col,col)
        c.text(855,345,'helium-4',WHITE,25);c.text(845,380,'2 protony + 2 neutrony',MUTED,19)
        c.paragraph(75,460,'V prvních minutách vznikají jádra. Neutrální atomy se utvářejí mnohem později.',1050,MUTED,24)
    elif k=='edu-b11-atmosphere':
        c.text(60,86,'Při přechodu planety zkoumáme světlo prošlé okrajem její atmosféry',WHITE,23)
        c.circle(165,280,80,GOLD,GOLD);c.circle(525,280,54,BLUE);c.circle(525,280,36,WHITE,'#111827')
        for y in [231,244,316,329]:
            c.arrow(260,y,485,y,GOLD,2);c.arrow(570,y,855,y,BLUE,2)
        c.text(105,395,'hvězda',MUTED,24);c.text(435,395,'planeta s atmosférou',MUTED,23)
        c.box(900,200,1125,355);c.text(920,235,'rozklad světla',BLUE,23);c.text(928,275,'na spektrum',BLUE,23)
        c.paragraph(65,465,'Molekuly pohlcují vybrané vlnové délky. Jejich společné spektrální stopy pomáhají určit složení atmosféry.',1060,MUTED,24)
    elif k=='edu-b11-habitable':
        c.text(60,86,'Oblast vhodného příjmu hvězdného záření závisí na vlastnostech hvězdy',WHITE,23)
        for y,label,rad,zone in [(225,'méně svítivá hvězda',28,(300,480)),(405,'svítivější hvězda',49,(650,960))]:
            c.circle(150,y,rad,GOLD,GOLD);c.line([(215,y),(1120,y)],GRID,3)
            c.d.rounded_rectangle((zone[0],y-30,zone[1],y+30),radius=12,fill='#21493d',outline=GREEN,width=2)
            c.text(zone[0]+15,y-12,'obyvatelná zóna',GREEN,20);c.text(60,y+65,label,MUTED,22)
        c.text(65,535,'Povrchové podmínky dále ovlivňují atmosféra, voda, oblaky a vývoj planety.',MUTED,22)
    elif k=='edu-b11-horizons':
        c.text(60,86,'Dvě otázky o světle z velmi vzdálených míst',WHITE,26)
        for x,title,col in [(65,'Co vidíme dnes?',BLUE),(650,'Co k nám dorazí později?',GOLD)]:
            c.box(x,155,x+500,490);c.text(x+25,185,title,col,26)
        c.paragraph(95,255,'Světlo už stihlo doputovat k nám. Vidíme zdroj v jeho minulosti.',430,WHITE,26)
        c.paragraph(95,385,'Hranici určuje dosavadní vývoj vesmíru a šíření světla.',430,MUTED,23)
        c.paragraph(680,255,'Ptáme se na signál vyslaný nyní ze vzdáleného místa.',430,WHITE,26)
        c.paragraph(680,385,'Rozhoduje také budoucí průběh rozpínání.',430,MUTED,23)
        c.text(65,535,'Částicový horizont a kosmologický horizont událostí odpovídají jiným otázkám.',MUTED,21)
    else:raise ValueError(k)
    return c.finish()