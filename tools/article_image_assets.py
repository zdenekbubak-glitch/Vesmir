"""Credit-free source masters and small previews; all diagrams are qualitative."""
import hashlib
import io
import math
import textwrap
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps


def font(size):
    from assign_article_images import font as load
    return load(size)


def diagram(entry):
    """Different physical concepts, not random seeds/crops of one illustration."""
    im=Image.new('RGB',(1200,630),'#0b1424');d=ImageDraw.Draw(im)
    blue='#76c8ff';gold='#ffd287';violet='#beadff';muted='#afbed4';white='#ecf4ff'
    kind=entry['diagram'];title=entry['title']
    d.text((45,26),title,font=font(32),fill=white)
    def text(x,y,s,c=muted,size=23): d.text((x,y),s,font=font(size),fill=c)
    def line(points,c=blue,w=4): d.line(points,fill=c,width=w)
    def circle(x,y,r,c=blue,w=3): d.ellipse((x-r,y-r,x+r,y+r),outline=c,width=w)
    def arrow(x,y,xx,yy,c=blue):
        line([(x,y),(xx,yy)],c);a=math.atan2(yy-y,xx-x)
        d.polygon([(xx,yy),(xx-15*math.cos(a-.5),yy-15*math.sin(a-.5)),(xx-15*math.cos(a+.5),yy-15*math.sin(a+.5))],fill=c)
    def axes(x=150,y=450,w=880,h=300,xlabel='čas',ylabel='velikost'):
        arrow(x,y,x+w,y,muted);arrow(x,y,x,y-h,muted)
        text(x+w-100,y+15,xlabel);text(x+18,y-h+25,ylabel,size=20)
    def curve(fn,c=blue): line([(150+i*8,450-fn(i/100)*275) for i in range(101)],c)
    def node(x,y,label,c=blue):
        d.rounded_rectangle((x-110,y-40,x+110,y+40),radius=15,outline=c,width=3)
        text(x-100,y-14,label,c,21)
    if kind=='standard-model':
        def card(x,y,symbol,name,color,width=170):
            d.rounded_rectangle((x,y,x+width,y+75),radius=10,fill='#152137',outline=color,width=3)
            if symbol.startswith('ν'):
                text(x+14,y+5,'ν',color,28);text(x+32,y+22,symbol[1:],color,17)
            else:
                text(x+14,y+5,symbol,color,28)
            text(x+14,y+44,name,white,20)
        for i,label in enumerate(('I. generace','II. generace','III. generace')):
            x=145+i*190;text(x,100,label,muted,20)
        text(145,72,'Částice hmoty: fermiony',white,22)
        text(775,90,'Bosony a jejich role',white,22)
        text(40,172,'Kvarky',violet,20);text(40,390,'Leptony',blue,20)
        text(40,468,'neutrina',muted,17)
        rows=[(145,[('u','up'),('c','charm'),('t','top')],violet),
              (235,[('d','down'),('s','strange'),('b','bottom')],violet),
              (345,[('e','elektron'),('μ','mion'),('τ','tauon')],blue),
              (435,[('νe','elektronové'),('νμ','mionové'),('ντ','tauonové')],blue)]
        for y,particles,color in rows:
            for i,(symbol,name) in enumerate(particles):card(145+i*190,y,symbol,name,color)
        card(775,145,'γ — foton','elektromagnetická interakce',gold,380)
        card(775,235,'g — gluon','silná interakce',gold,380)
        card(775,345,'W⁺, W⁻, Z','slabá interakce',gold,380)
        card(775,435,'H — Higgsův boson','Higgsovo pole a hmotnost','#91d9b5',380)
        text(145,533,'Gravitace není součástí standardního modelu.',white,23)
    elif kind=='collider':
        d.ellipse((270,130,930,500),outline=blue,width=5)
        d.ellipse((290,150,910,480),outline=gold,width=5)
        arrow(470,137,640,137,blue);arrow(560,475,730,475,gold)
        circle(930,315,20,violet)
        arrow(950,300,1045,230,violet);arrow(950,330,1045,400,violet)
        text(355,270,'Dva protiběžné svazky',white,26)
        text(365,320,'protonů nebo těžkých iontů',muted,22)
        text(75,85,'magnety: vedení a zaostření svazků',blue,22)
        text(850,170,'srážka',violet,22);text(930,440,'produkty srážky',violet,22)
        text(75,525,'Princip urychlovače; rozměry, dráhy a počet míst srážek nejsou v měřítku.',size=21)
    elif kind=='rotation':
        axes(xlabel='poloměr',ylabel='oběžná rychlost')
        curve(lambda x:.75*(1-math.exp(-10*x)))
        curve(lambda x:.7*(1-math.exp(-18*x))/math.sqrt(1+5*x),gold)
        text(650,170,'s halem temné hmoty',blue);text(650,325,'pouze viditelná hmota',gold)
    elif kind=='detector':
        d.rounded_rectangle((460,145,760,430),radius=30,outline=blue,width=5)
        for y in (170,405):
            for x in range(490,750,45): circle(x,y,13,gold)
        arrow(130,310,550,310,violet);circle(565,310,16,gold)
        arrow(580,300,670,210,gold);arrow(580,320,680,375,blue)
        text(100,235,'částice?');text(475,460,'terč: kapalný xenon');text(810,190,'světlo + náboj')
        text(810,235,'princip detekce');text(95,495,'Není výkres přístroje LZ ani záznam události.',size=21)
    elif kind=='axion':
        d.rounded_rectangle((390,190,800,390),radius=25,outline=blue,width=4)
        for x in range(435,800,65): arrow(x,365,x,215,violet)
        arrow(100,290,370,290,gold)
        line([(810+i*3,290+25*math.sin(i/4)) for i in range(90)],gold)
        text(110,220,'axion?');text(425,430,'magnetické pole B');text(850,220,'foton')
    elif kind=='recoil':
        circle(620,310,65,gold);circle(260,310,18,violet)
        arrow(300,310,520,310,violet);arrow(665,340,880,440,gold);arrow(635,240,830,150,violet)
        text(120,180,'dopadající částice?');text(490,440,'jaderný terč');text(840,475,'zpětný ráz',gold)
        text(225,505,'Přenos energie při pružném rozptylu – princip, nikoli událost.')
    elif kind=='electron-recoil':
        circle(600,300,105,blue);circle(600,300,25,gold);circle(705,300,14,blue)
        arrow(200,220,680,290,violet);arrow(730,300,1020,400,blue)
        text(155,155,'hypotetická interakce');text(735,460,'vyražený elektron',blue)
        text(250,505,'Elektronové excitace jako kanál hledání temné hmoty')
    elif kind=='dual-signal':
        axes(xlabel='čas',ylabel='odezva xenonového detektoru')
        curve(lambda x:.75*math.exp(-((x-.2)/.018)**2)+.5*math.exp(-((x-.7)/.07)**2),gold)
        text(265,200,'S1: okamžité světlo',gold);text(640,265,'S2: ionizační signál',blue)
        text(200,510,'Ilustrační pulzy; žádný skutečný signál přístroje LZ.')
    elif kind=='annihilation':
        circle(245,240,45,blue);circle(245,390,45,violet)
        arrow(300,245,570,315);arrow(300,385,570,315,violet)
        circle(600,315,30,gold);arrow(640,300,940,180,gold);arrow(640,330,940,450,gold)
        text(120,140,'hypotetické částice');text(820,300,'záření / částice');text(420,470,'nepřímé hledání temné hmoty')
    elif kind=='halo':
        for r in (70,130,190): d.ellipse((600-r*1.6,300-r,600+r*1.6,300+r),outline=blue,width=3)
        d.ellipse((450,270,750,330),fill=gold)
        text(90,145,'rozsáhlé halo',blue);text(780,410,'viditelný disk',gold)
    elif kind=='lensing':
        circle(580,295,80,violet);circle(1000,295,25,gold);circle(180,295,15,blue)
        for sign in (-1,1): line([(200,295),(500,295+sign*125),(670,295+sign*125),(975,295)],gold)
        text(90,440,'pozorovatel');text(475,440,'hmotná čočka');text(950,440,'zdroj')
    elif kind=='expansion':
        for cx,r in ((270,65),(600,110),(950,160)):
            circle(cx,300,r)
            for angle in (0,1.8,3.6,4.8):
                x=cx+r*.6*math.cos(angle);y=300+r*.6*math.sin(angle);circle(x,y,7,gold)
        arrow(365,300,440,300);arrow(735,300,770,300)
        text(160,490,'dříve');text(880,490,'později');text(370,110,'Rostou vzdálenosti, ne velikosti galaxií.')
    elif kind=='hubble':
        axes(xlabel='vzdálenost',ylabel='rychlost vzdalování');curve(lambda x:.8*x)
        for i in range(1,10): circle(150+i*80,450-i*22,7,gold)
        text(240,150,'Hubbleův vztah: v ≈ H₀ d',size=29);text(620,340,'schematické body, nikoli data')
    elif kind=='ladder':
        for i,label in enumerate(('paralaxy','cefeidy','supernovy Ia')):
            x=160+i*320;y=410-i*100
            d.rectangle((x,y,x+255,465),outline=blue,width=3);text(x+10,y-45,label,white)
            if i<2: arrow(x+260,y-10,x+310,y-75,gold)
        text(125,510,'Kalibrace vzdáleností na stále větších škálách')
    elif kind=='candle':
        for x,r in ((280,48),(600,32),(950,20)):
            circle(x,270,r,gold)
            for a in range(8):
                angle=a*math.tau/8;line([(x+math.cos(angle)*(r+10),270+math.sin(angle)*(r+10)),(x+math.cos(angle)*(r+35),270+math.sin(angle)*(r+35))],gold)
        text(170,390,'bližší → jasnější');text(790,390,'vzdálenější → slabší');text(180,145,'Standardizované svíčky: supernovy typu Ia',white,28)
    elif kind=='bao':
        for x,y in ((320,290),(800,300)):
            for r in (50,100,150): circle(x,y,r,blue if r==150 else '#304e70')
            circle(x,y,9,gold)
        arrow(320,470,470,470,gold);text(510,450,'charakteristická škála');text(235,110,'Akustické vlny zanechaly stopu v rozložení hmoty.')
    elif kind=='equation-state':
        axes(xlabel='rudý posuv',ylabel='w = tlak / hustota energie')
        line([(150,290),(950,290)],gold);text(710,305,'w = −1 (Λ)',gold)
        curve(lambda x:.55+.12*math.sin(x*5),blue);text(480,150,'možný proměnný model',blue)
    elif kind=='density':
        axes(xlabel='rozměr vesmíru',ylabel='relativní hustota')
        curve(lambda x:.85*math.exp(-7*x),gold);curve(lambda x:.7*math.exp(-3*x),blue)
        curve(lambda x:.24,violet);text(560,175,'záření: a⁻⁴',gold);text(560,220,'hmota: a⁻³',blue);text(560,265,'konstanta Λ',violet)
    elif kind=='fate':
        axes(xlabel='čas',ylabel='rozměr vesmíru')
        curve(lambda x:.1+.15*x+.65*x*x,blue);curve(lambda x:.1+.65*x,gold)
        curve(lambda x:.1+2*x*(1-x),violet)
        text(190,100,'Možné scénáře vývoje – nikoli předpověď',white,26)
    elif kind=='potential':
        axes(xlabel='hodnota pole',ylabel='potenciální energie')
        curve(lambda x:.15+.7*math.exp(-4*x));circle(400,330,17,gold);arrow(420,337,575,375,gold)
        text(550,170,'pomalu se vyvíjející skalární pole');text(580,220,'model kvintesence')
    elif kind=='interferometer':
        line([(300,415),(300,160),(920,415)],'#0b1424')
        line([(300,170),(300,415),(940,415)],blue,10)
        d.rectangle((275,145,325,165),fill=gold);d.rectangle((940,390,960,440),fill=gold)
        arrow(105,415,275,415,gold);circle(300,415,18,violet)
        text(90,465,'laser');text(350,150,'dvě kolmá ramena');text(575,455,'změna optických drah')
    elif kind=='chirp':
        axes(xlabel='čas',ylabel='deformace')
        line([(150+i*2,310+(.06+i/500)**2*90*math.sin(i/20+i*i/1200)) for i in range(400)],blue)
        text(320,125,'Před splynutím roste frekvence i amplituda.');text(200,490,'Ilustrační průběh; není záznam detektoru.')
    elif kind=='gw-background':
        axes(xlabel='frekvence',ylabel='hustota energie pozadí')
        curve(lambda x:.15+.45*x,blue);curve(lambda x:.55*math.exp(-((x-.5)/.2)**2),gold)
        text(240,110,'Možné příspěvky stochastického gravitačního pozadí')
        text(220,490,'Kvalitativní modely; nikoli měření ani tepelné spektrum.')
    elif kind=='binary':
        for cx,cy in ((400,270),(800,340)):
            circle(cx,cy,45,gold)
            for r in (75,120,165): d.arc((cx-r,cy-r,cx+r,cy+r),20,300,fill=blue,width=3)
        text(235,110,'Dvojice kompaktních objektů vyzařuje energii.');arrow(470,310,690,310,violet)
    elif kind=='polarization':
        for cx,cy,s in ((350,300,1),(850,300,-1)):
            circle(cx,cy,130)
            for a in range(12):
                angle=a*math.tau/12;x=cx+110*math.cos(angle);y=cy+110*math.sin(angle)
                d.ellipse((x-7,y-7,x+7,y+7),fill=gold)
            arrow(cx-80,cy,cx+80,cy);arrow(cx,cy-80,cx,cy+80,violet)
        text(250,470,'polarizace +');text(735,470,'polarizace ×');text(210,115,'Dva nezávislé módy příčné gravitační vlny')
        # Rotate second ring's arrows to distinguish cross polarization.
        d.rectangle((765,215,935,385),fill='#0b1424')
        arrow(790,240,910,360);arrow(790,360,910,240,violet)
    elif kind=='pulsar-timing':
        circle(600,320,24,gold)
        for x,y in ((230,160),(950,160),(230,460),(950,460)):
            circle(x,y,18,blue);line([(x,y),(600,320)],'#3c688b');text(x-55,y-60,'pulzar',blue)
        text(430,110,'Síť přesných kosmických hodin');text(470,450,'změny časů příchodu')
    elif kind=='siren':
        node(280,220,'gravitační vlna');node(280,405,'rudý posuv',gold)
        arrow(400,220,680,300);arrow(400,405,680,330,gold);node(850,315,'vzdálenost / H₀',violet)
        text(130,110,'Standardní sirény spojují dva druhy měření.')
    elif kind=='spectrograph':
        d.polygon([(520,180),(400,430),(700,430)],outline=blue,fill='#1c304b')
        arrow(140,270,470,270,white)
        for i,c in enumerate(('#ba9dff','#76c8ff','#8bd9b0','#ffd287','#f3978a')):
            line([(590,300),(1030,175+i*60)],c,5)
        text(120,465,'vstupní světlo');text(750,490,'rozklad podle vlnové délky')
    elif kind=='spectrum':
        axes(xlabel='frekvence',ylabel='relativní intenzita')
        curve(lambda x:7*x*x*math.exp(-4*x),gold)
        text(420,150,'Tepelné spektrum reliktního záření');text(580,365,'schematický průběh')
    elif kind=='cmb-map':
        for x in range(180,1030,16):
            for y in range(150,440,16):
                if ((x-600)/430)**2+((y-295)/145)**2<1:
                    v=math.sin(x/75)*math.cos(y/45)+math.sin((x+y)/50)
                    d.rectangle((x,y,x+15,y+15),fill=('#4d8bbe' if v<0 else '#dd9d75'))
        text(240,475,'Kvalitativní ukázka teplotních odchylek; bez dat.')
    elif kind=='e-mode':
        for x in range(250,1000,80):
            for y in range(160,450,60):
                a=math.atan2(y-300,x-600);line([(x-17*math.cos(a),y-17*math.sin(a)),(x+17*math.cos(a),y+17*math.sin(a))],blue)
        text(190,490,'Radiální / tangenciální uspořádání polarizace (E).')
    elif kind=='b-mode':
        for x in range(250,1000,80):
            for y in range(160,450,60):
                a=math.atan2(y-300,x-600)+math.pi/4;line([(x-17*math.cos(a),y-17*math.sin(a)),(x+17*math.cos(a),y+17*math.sin(a))],violet)
        text(180,490,'Polarizační vzor s odlišnou paritou (B); bez dat.')
    elif kind=='foreground':
        for x,label,c in ((230,'prach',gold),(600,'CMB',blue),(970,'synchrotron',violet)):
            for y in range(190,400,28): line([(x-100,y),(x+100,y+30*math.sin(y/50))],c)
            text(x-100,450,label,c)
        text(220,110,'Pozorovaný signál obsahuje více složek.')
    elif kind=='recombination':
        for x,y in ((230,240),(230,390),(650,315)): circle(x,y,35,gold)
        circle(650,315,95,blue);circle(745,315,13,blue)
        arrow(330,310,500,310);line([(780+i*3,300+20*math.sin(i/4)) for i in range(100)],violet)
        text(115,140,'ionizovaný plyn');text(520,460,'vznik neutrálních atomů');text(820,220,'volné fotony')
    elif kind=='acoustic':
        axes(xlabel='úhlová škála',ylabel='výkon fluktuací')
        curve(lambda x:.1+.65*math.exp(-((x-.18)/.07)**2)+.45*math.exp(-((x-.47)/.07)**2)+.3*math.exp(-((x-.75)/.07)**2))
        text(350,110,'Akustické vrcholy – pouze kvalitativní schéma')
    elif kind=='reionization':
        for x,y,r in ((280,260,90),(520,340,120),(800,270,150)):
            d.ellipse((x-r,y-r,x+r,y+r),fill='#23476d',outline=blue,width=3);circle(x,y,9,gold)
        text(220,465,'Ionizované oblasti kolem prvních zdrojů světla')
    elif kind=='inflation':
        axes(xlabel='čas',ylabel='rozměr vesmíru');curve(lambda x:.05+.85*(math.exp(4*x)-1)/(math.exp(4)-1))
        text(240,125,'Velmi rychlý růst v modelu kosmické inflace')
    elif kind=='nucleosynthesis':
        for x,y in ((210,230),(210,390)): circle(x,y,26,blue)
        arrow(280,310,500,310,gold)
        for x,y,c in ((650,280,blue),(700,280,gold),(650,330,gold),(700,330,blue)): circle(x,y,28,c)
        text(120,145,'protony a neutrony');text(580,430,'lehká atomová jádra');text(220,495,'Prvotní nukleosyntéza; zjednodušené schéma.')
    elif kind=='timeline':
        line([(120,320),(1080,320)],blue,5)
        for x,label in ((170,'horký počátek'),(450,'atomy'),(710,'první hvězdy'),(1000,'galaxie')):
            circle(x,320,12,gold);text(x-85,200 if x<600 else 390,label,white,22)
        text(260,490,'Události nejsou zakresleny v lineárním časovém měřítku.')
    elif kind=='phase':
        for x,y,r in ((300,300,110),(570,330,95),(820,270,140)):
            circle(x,y,r,violet);arrow(x,y,x+r*.6,y,blue)
        text(240,130,'Růst a setkávání bublin nové fáze');text(260,490,'Hypotetický fázový přechod raného vesmíru.')
    elif kind=='21cm':
        circle(340,300,110,blue);circle(340,300,25,gold);circle(450,300,14,blue)
        arrow(520,300,710,300,gold);line([(730+i*3,300+25*math.sin(i/5)) for i in range(100)],violet)
        text(170,145,'hyperjemný přechod vodíku');text(770,420,'rádiový foton 21 cm')
    elif kind=='asymmetry':
        for i in range(6): circle(240+i*110,235,25,blue)
        for i in range(5): circle(240+i*110,385,25,gold)
        text(880,220,'hmota',blue);text(880,370,'antihmota',gold)
        text(200,485,'Ilustrace malé převahy; počty nejsou ve skutečném poměru.')
    elif kind=='web':
        nodes=[(220,230),(450,160),(750,210),(980,350),(700,440),(400,380)]
        for a,b in ((0,1),(1,2),(2,3),(3,4),(4,5),(5,0),(1,5),(2,4),(2,5)):
            line([nodes[a],nodes[b]],'#436a91',5)
        for x,y in nodes: circle(x,y,27,gold)
        text(210,490,'Zárodky struktur → vlákna a uzly kosmické sítě')
    elif kind=='curvature':
        for row in range(7):
            line([(100+i*10,180+row*40+90*math.exp(-((i-50)/15)**2)) for i in range(101)],blue,2)
        for col in range(15):
            x=130+col*65;line([(x,170),(x,460)],'#365574',2)
        circle(600,340,28,gold);text(170,110,'Zakřivení časoprostoru – prostorová analogie')
    elif kind=='orbit':
        circle(600,300,24,gold)
        for a in range(6):
            pts=[]
            for n in range(181):
                t=n*math.tau/180;x=220*math.cos(t);y=90*math.sin(t);angle=a*.18
                pts.append((600+x*math.cos(angle)-y*math.sin(angle),300+x*math.sin(angle)+y*math.cos(angle)))
            line(pts,blue,2)
        text(280,480,'Stáčení orientace dráhy při relativistické precesi')
    elif kind=='equivalence':
        for x,r,c in ((370,30,blue),(800,55,gold)):
            circle(x,200,r,c);arrow(x,280,x,420,c)
        line([(200,460),(980,460)],muted)
        text(210,110,'Volný pád nezávisí na složení testovacího tělesa.')
    elif kind=='redshift':
        for offset,scale,c in ((210,10,blue),(380,23,gold)):
            line([(150+i*2,offset+30*math.sin(i/scale)) for i in range(450)],c)
        text(140,130,'kratší vlnová délka',blue);text(700,440,'delší vlnová délka',gold)
        arrow(1060,230,1060,380,violet)
    elif kind=='shapiro':
        circle(600,340,55,gold)
        line([(160,250),(1040,250)],'#3c536f',2)
        line([(160,250),(450,220),(600,205),(750,220),(1040,250)],blue)
        text(210,115,'Signál prochází gravitačním polem.');text(210,460,'Dodatečné zpoždění; tvar dráhy je zvýrazněn.')
    elif kind=='screening':
        for x,label,c in ((320,'řídké prostředí',blue),(850,'husté prostředí',gold)):
            circle(x,300,65,c)
            for a in range(8):
                t=a*math.tau/8;arrow(x+80*math.cos(t),300+80*math.sin(t),x+145*math.cos(t),300+145*math.sin(t),c if x<500 else '#34465c')
            text(x-130,490,label,c)
        text(200,110,'Hypotetické stínění dodatečné síly v hustém prostředí')
    elif kind=='entanglement':
        circle(300,300,65,blue);circle(900,300,65,violet)
        for y in (250,300,350): line([(375,y),(825,600-y)],gold,2)
        text(190,450,'kvantový systém A');text(780,450,'kvantový systém B');text(310,125,'Korelace společného kvantového stavu')
    elif kind=='holography':
        circle(600,305,180,blue)
        for a in range(24):
            t=a*math.tau/24;circle(600+180*math.cos(t),305+180*math.sin(t),5,gold)
        for x,y in ((540,250),(670,330),(560,385)): circle(x,y,18,violet);arrow(x,y,600+(x-600)*2,305+(y-305)*2,gold)
        text(135,160,'objem');text(890,430,'hranice');text(170,510,'Holografická korespondence – teoretický princip')
    elif kind=='spin-network':
        pts=[(250,250),(450,160),(700,210),(950,330),(750,440),(430,390)]
        for i in range(6):
            line([pts[i],pts[(i+1)%6]],blue);line([pts[i],pts[(i+2)%6]],'#52658f',2)
        for i,(x,y) in enumerate(pts): circle(x,y,15,gold);text(x+20,y,'j',white)
        text(250,500,'Spinová síť – abstraktní popis kvantové geometrie')
    elif kind=='foam':
        for x,y,r in ((200,270,65),(370,200,90),(520,340,110),(760,220,80),(950,350,120)):
            d.arc((x-r,y-r,x+r,y+r),25,325,fill=blue,width=4)
            circle(x+20,y+15,15,violet)
        text(180,490,'Kvantová pěna je hypotetický obraz; ne mikrofotografie.')
    elif kind=='bounce':
        axes(xlabel='čas',ylabel='rozměr vesmíru');curve(lambda x:.12+2.6*(x-.5)**2)
        arrow(300,210,470,345,gold);arrow(690,345,870,210,gold)
        text(260,110,'Hypotetický odraz místo singularity')
    elif kind=='wormhole':
        for y in range(180,430,30):
            line([(150+i*9,y+(300-y)*.8*math.exp(-((i-50)/15)**2)) for i in range(101)],blue,2)
        d.ellipse((540,240,660,360),outline=gold,width=4)
        text(220,110,'Teoretická geometrie průchodu časoprostorem');text(250,490,'Červí díra je hypotéza, nikoli pozorovaný objekt.')
    elif kind=='feynman':
        line([(240,180),(600,300),(950,180)],blue);line([(240,430),(600,300),(950,430)],gold)
        circle(600,300,12,violet);text(200,110,'Interakční vrchol v poruchovém popisu pole')
        text(220,490,'Symbolický diagram; není trajektorie částic v prostoru.')
    elif kind=='discrete-time':
        for i in range(8):
            x=180+i*120;line([(x,245),(x,365)],blue,4);circle(x,305,10,gold)
            if i<7: arrow(x+20,305,x+95,305,violet)
        text(240,140,'Hypotetická diskrétní struktura času');text(240,470,'Jednotlivé kroky nejsou naměřené časové intervaly.')
    elif kind=='telescope':
        line([(220,180),(450,300),(220,420)],blue,7)
        for y in (190,270,350): arrow(1030,y,520,y,gold);line([(520,y),(450,300),(720,300)],gold)
        text(180,480,'optická soustava – princip sběru světla')
    elif kind=='pulsar':
        circle(600,310,60,gold)
        d.polygon([(580,260),(350,110),(520,280)],fill='#376d9b')
        d.polygon([(620,360),(850,510),(680,340)],fill='#376d9b')
        d.arc((470,180,730,440),200,510,fill=violet,width=4)
        text(160,460,'rotující neutronová hvězda a směrové svazky')
    elif kind=='jet':
        d.ellipse((390,270,810,370),outline=gold,width=12);circle(600,320,45,violet)
        d.polygon([(580,270),(540,110),(660,110),(620,270)],fill='#376d9b')
        d.polygon([(580,370),(540,500),(660,500),(620,370)],fill='#376d9b')
        text(85,180,'výtrysk');text(850,395,'akreční disk')
    elif kind=='horizon':
        d.ellipse((450,150,750,450),fill='#02050b',outline=gold,width=5)
        for y in (180,260,340,420):
            arrow(230,y,390,y,blue);arrow(485,y,570,300,violet)
        text(790,240,'horizont událostí',gold);text(170,490,'Hranice, ze které světlo nemůže uniknout ven.')
    elif kind=='collapse':
        for x,r,label in ((240,110,'hmotná hvězda'),(610,65,'kolaps jádra'),(960,38,'černá díra')):
            circle(x,300,r,gold if x<900 else violet);text(x-100,470,label)
        arrow(370,300,515,300);arrow(700,300,890,300)
        text(210,120,'Zjednodušená cesta ke vzniku hvězdné černé díry')
    elif kind=='multiverse':
        for x,y,r in ((240,250,90),(550,330,140),(910,240,110)): circle(x,y,r,blue);circle(x-20,y+20,20,gold)
        text(170,510,'Oddělené oblasti v hypotetickém scénáři multivesmíru')
    elif kind=='selection':
        node(240,300,'model',blue);node(600,300,'pozorování',gold);node(960,300,'porovnání',violet)
        arrow(360,300,470,300);arrow(720,300,830,300)
        text(200,470,'Vědecká interpretace vyžaduje testování předpovědí.')
    else: raise ValueError('Unknown diagram '+kind)
    d.text((45,578),'VLASTNÍ SCHÉMA · kvalitativní ilustrace, nikoli snímek ani naměřená data',font=font(22),fill=muted)
    return im


def make_asset(entry,folder):
    folder=Path(folder);sources=folder/'sources';thumbs=folder/'thumbs'
    sources.mkdir(exist_ok=True);thumbs.mkdir(exist_ok=True)
    source=sources/(entry['id']+'.jpg');target=folder/(entry['id']+'.jpg')
    thumb=thumbs/(entry['id']+'.webp')
    stamp=folder/'sources'/(entry['id']+'.render.json')
    import json
    fingerprint=hashlib.sha256(json.dumps(entry,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    if target.exists() and thumb.exists() and stamp.exists() and stamp.read_text()==fingerprint: return
    if source.exists():
        with Image.open(source) as opened: original=opened.convert('RGB')
    elif entry.get('diagram'):
        original=diagram(entry);original.save(source,quality=95,optimize=True)
    else:
        req=urllib.request.Request(entry['download'],headers={'User-Agent':'Kosmonovinky-image-library/2.0'})
        with urllib.request.urlopen(req,timeout=60) as response: data=response.read(25*1024*1024+1)
        if len(data)>25*1024*1024: raise ValueError('Image larger than 25 MB')
        with Image.open(io.BytesIO(data)) as opened: original=ImageOps.exif_transpose(opened).convert('RGB')
        original.thumbnail((1800,1800),Image.Resampling.LANCZOS)
        original.save(source,quality=95,optimize=True)
    # No credit overlays are ever used as the input to a thumbnail.
    if entry.get('thumbnail_fit')=='cover':
        small=ImageOps.fit(original,(288,288),Image.Resampling.LANCZOS,centering=tuple(entry.get('centering',[.5,.5])))
    else:
        pic=ImageOps.contain(original,(288,288),Image.Resampling.LANCZOS)
        small=Image.new('RGB',(288,288),'#0b1424');small.paste(pic,((288-pic.width)//2,(288-pic.height)//2))
    small.save(thumb,'WEBP',quality=82,method=6)
    if entry.get('diagram'): im=original.copy()
    else:
        im=Image.new('RGB',(1200,630),'#080e1b')
        if entry.get('layout')=='landscape': pic=ImageOps.fit(original,(1200,510),Image.Resampling.LANCZOS,centering=tuple(entry.get('centering',[.5,.5])))
        else: pic=ImageOps.contain(original,(1200,510),Image.Resampling.LANCZOS)
        im.paste(pic,((1200-pic.width)//2,(510-pic.height)//2))
        d=ImageDraw.Draw(im);label='TEMATICKÝ OBRÁZEK · '+entry['kind']
        box=d.textbbox((0,0),label,font=font(19));d.rectangle((15,12,40+box[2],46),fill='#080e1b');d.text((24,18),label,font=font(19),fill='#edf4ff')
    d=ImageDraw.Draw(im)
    if not entry.get('diagram'):
        d.rectangle((0,510,1200,630),fill='#080e1b')
        for i,s in enumerate(textwrap.wrap(entry['credit'],width=105)):
            if i>2: raise ValueError('Credit too long: '+entry['id'])
            d.text((20,518+i*24),s,font=font(19),fill='#edf4ff')
        d.text((20,600),entry.get('source_id',entry['id'])+' · '+entry['license']+' · '+entry['modifications'],font=font(16),fill='#afbed4')
    im.save(target,'JPEG',quality=88,optimize=True)
    stamp.write_text(fingerprint)
