"""Manually placed teaching diagrams. No external assets or extra dependencies."""
import math
import random
from functools import lru_cache
from PIL import Image, ImageDraw

BG = '#0b1424'
WHITE = '#ecf4ff'
MUTED = '#afbed4'
BLUE = '#76c8ff'
GOLD = '#ffd287'
VIOLET = '#beadff'
GREEN = '#91d9b5'
GRID = '#304e70'


@lru_cache(maxsize=64)
def font(size):
    from assign_article_images import font as load
    return load(size)


class Canvas:
    def __init__(self, title):
        self.im = Image.new('RGB', (1200, 630), BG)
        self.d = ImageDraw.Draw(self.im)
        self.text(45, 24, title, WHITE, 32, maxwidth=1110)

    def text(self, x, y, value, color=MUTED, size=23, maxwidth=None):
        while maxwidth and self.d.textlength(value, font=font(size)) > maxwidth and size > 16:
            size -= 1
        self.d.text((x, y), value, fill=color, font=font(size))

    def paragraph(self, x, y, value, width, color=MUTED, size=23):
        words = value.split(); line = ''
        for word in words:
            nxt = (line + ' ' + word).strip()
            if line and self.d.textlength(nxt, font=font(size)) > width:
                self.text(x, y, line, color, size); y += size + 9; line = word
            else:
                line = nxt
        if line:
            self.text(x, y, line, color, size); y += size + 9
        return y

    def line(self, points, color=BLUE, width=3):
        self.d.line(points, fill=color, width=width)

    def arrow(self, x, y, xx, yy, color=BLUE, width=3):
        self.line([(x, y), (xx, yy)], color, width)
        a = math.atan2(yy-y, xx-x)
        self.d.polygon([(xx, yy), (xx-13*math.cos(a-.45), yy-13*math.sin(a-.45)),
                        (xx-13*math.cos(a+.45), yy-13*math.sin(a+.45))], fill=color)

    def circle(self, x, y, r, color=BLUE, fill=None, width=3):
        self.d.ellipse((x-r, y-r, x+r, y+r), outline=color, fill=fill, width=width)

    def box(self, x, y, xx, yy, color=GRID, fill='#152137'):
        self.d.rounded_rectangle((x, y, xx, yy), radius=12, outline=color, fill=fill, width=2)

    def finish(self):
        self.text(45, 585, 'VLASTNÍ SCHÉMA · Kosmologické novinky · CC BY 4.0', MUTED, 21)
        return self.im


def diagram(entry):
    if entry['diagram'].startswith('edu-b11-'):
        from cosmology_diagrams import diagram as cosmology_diagram
        return cosmology_diagram(entry)
    if entry['diagram'].startswith('edu-b7-'):
        from kosmopedie_batch7_diagrams import diagram as batch7_diagram
        return batch7_diagram(entry)
    if entry['diagram'].startswith('edu-b6-'):
        from kosmopedie_batch6_diagrams import diagram as batch6_diagram
        return batch6_diagram(entry)
    if entry['diagram'].startswith('edu-b5-'):
        from kosmopedie_batch5_diagrams import diagram as batch5_diagram
        return batch5_diagram(entry)
    c = Canvas(entry['title']); k = entry['diagram']
    if k == 'edu-gw-stretch':
        c.text(65, 90, 'Vlna střídavě prodlužuje vzdálenosti v jednom směru a zkracuje je v kolmém směru.', WHITE, 24)
        c.arrow(130,170,1045,170,BLUE)
        c.text(735,135,'směr šíření vlny',BLUE,22)
        def section(cx,rx,ry,u,v):
            return cx+rx*u,320+ry*v+0.30*rx*u
        points=[]
        for cx,rx,ry,label in ((220,92,92,'kruhový průřez'),(600,120,64,'jedna fáze'),(980,64,120,'opačná fáze')):
            for v in (-.60,-.30,0,.30,.60):
                u=math.sqrt(1-v*v)*.93
                c.line([section(cx,rx,ry,-u,v),section(cx,rx,ry,u,v)],GRID,2)
            for u in (-.60,-.30,0,.30,.60):
                v=math.sqrt(1-u*u)*.93
                c.line([section(cx,rx,ry,u,-v),section(cx,rx,ry,u,v)],GRID,2)
            ring=[section(cx,rx,ry,math.cos(math.tau*n/80),math.sin(math.tau*n/80)) for n in range(81)]
            points.append(ring)
            c.line(ring,BLUE,2)
            for x,y in ring[:-1:4]:
                c.circle(x,y,6,GOLD,GOLD,1)
            c.text(cx-100,490,label,MUTED,23)
        for index in (0,20,40,60):
            p=[ring[index] for ring in points]
            for a,b in zip(p,p[1:]):
                c.line([a,b],GRID,1)
        c.text(70,540,'Tři řezy v témže okamžiku. Změny vzdáleností jsou silně zvětšené.',MUTED,22)
    elif k == 'edu-lithium-7-relics':
        c.text(65,91,'Hypotéza pro první hodiny vesmíru',WHITE,25)
        for x,label,detail,col in (
            (65,'Nestabilní relikty','Rozpadající se částice nebo vypařující se útvary Q-balls',BLUE),
            (450,'Uvolněné částice','Antineutrina, elektrony a fotony mění průběh jaderných reakcí',VIOLET),
            (835,'Méně lithia-7','Podle výpočtu může vzniknout méně lithia-7',GOLD),
        ):
            c.box(x,181,x+300,447,col)
            c.text(x+20,215,label,col,26)
            c.paragraph(x+20,288,detail,260,WHITE,23)
        c.arrow(375,315,439,315,BLUE)
        c.arrow(760,315,825,315,BLUE)
        c.text(65,508,'Výsledky musí zároveň odpovídat měřením deuteria, helia-4 a reliktního záření.',MUTED,21)
    elif k == 'edu-dark-comparison':
        for x, label, color in ((60, 'Temná hmota', BLUE), (650, 'Temná energie', VIOLET)):
            c.box(x, 100, x+490, 505, color)
            c.text(x+25, 125, label, color, 30)
        for rr in (55, 85, 115): c.d.ellipse((305-rr*1.3, 300-rr, 305+rr*1.3, 300+rr), outline=GRID, width=3)
        c.d.ellipse((225, 285, 385, 315), fill=GOLD)
        c.paragraph(90, 420, 'Shlukuje se v halech a gravitačně ovlivňuje galaxie.', 430, WHITE, 23)
        for x, y in ((775, 270), (1005, 270), (775, 360), (1005, 360)):
            c.circle(x, y, 8, GOLD, GOLD, 1)
        c.arrow(800, 315, 970, 315, VIOLET)
        c.paragraph(680, 420, 'Souvisí se zrychleným rozpínáním vesmíru.', 430, WHITE, 23)
        c.text(70, 535, 'Dvě odlišné složky; druhá kresba ukazuje vývoj velkých vzdáleností.', MUTED, 21)
    elif k == 'edu-density-wave':
        c.text(65, 90, 'Analogie dopravní zácpy: oblast zhuštění nemusí putovat s auty.', WHITE, 24)
        for y, yellow, positions, label in ((245, 595, [240,360,475,535,595,655,715,860,1010], 'dříve'),
                                            (410, 825, [260,405,475,535,595,655,715,825,1040], 'později')):
            c.text(65, y-18, label, MUTED, 24)
            c.box(440, y-50, 780, y+50, VIOLET, '#302e4b')
            c.line([(220, y+55), (1120, y+55)], GRID, 3)
            for x in positions:
                c.d.rounded_rectangle((x-16, y-12, x+16, y+12), radius=5, fill=GOLD if x==yellow else BLUE)
            c.arrow(915, y-35, 1060, y-35, BLUE)
        c.arrow(595, 275, 825, 365, GOLD)
        c.text(450, 145, 'oblast zhuštění v obou časech', VIOLET, 24)
        c.text(65, 535, 'Žluté auto projede oblastí se zvýšenou hustotou. Podobně mohou hvězdy procházet ramenem.', MUTED, 21)
    elif k == 'edu-cluster-separation':
        c.text(65, 90, 'Po průletu dvou kup: horký plyn se zbrzdí, galaxie většinou projdou.', WHITE, 24)
        for cx in (255, 945):
            c.d.ellipse((cx-140, 210, cx+140, 430), fill='#183d60', outline=BLUE, width=3)
            for dx, dy in ((-50,-35),(35,25),(60,-25),(-20,45)):
                c.d.ellipse((cx+dx-9, 320+dy-4, cx+dx+9, 320+dy+4), fill=GOLD)
        for cx in (520, 680):
            c.d.ellipse((cx-125, 235, cx+125, 405), fill='#593c40', outline='#ffb39c', width=3)
        c.arrow(265, 190, 140, 190, BLUE); c.arrow(935, 190, 1060, 190, BLUE)
        c.text(190, 455, 'galaxie', GOLD, 24); c.text(890, 455, 'galaxie', GOLD, 24)
        c.text(460, 440, 'horký plyn', '#ffb39c', 25)
        c.paragraph(65, 505, 'Modře: hlavní koncentrace hmotnosti odvozené z čočkování. Ilustrace principu, nikoli mapa Bullet Clusteru.', 1060, MUTED, 21)
    elif k == 'edu-multimessenger':
        c.text(65, 90, 'GW170817 · pořadí zachycení a objevu · 17. srpna 2017', WHITE, 25)
        for x, num, title, body, color in ((65,'1','Gravitační vlny','Splynutí neutronových hvězd',BLUE),
                                          (450,'2','Gama záblesk','Přibližně o 1,7 s později',GOLD),
                                          (835,'3','Optický protějšek','Objeven asi 11 hodin po signálu',VIOLET)):
            c.box(x, 200, x+300, 450, color)
            c.circle(x+45, 245, 23, color); c.text(x+37, 227, num, color, 27)
            c.paragraph(x+20, 300, title, 260, color, 26)
            c.paragraph(x+20, 365, body, 260, WHITE, 23)
        c.arrow(380, 320, 430, 320); c.arrow(765, 320, 815, 320)
        c.text(65, 515, 'Časové rozestupy nejsou v měřítku. Pozorování pokračovala další dny a týdny.', MUTED, 21)
    elif k == 'edu-transit':
        c.text(65, 90, 'Planeta před hvězdou → malý opakovaný pokles jasnosti', WHITE, 25)
        for x, px, label in ((230,-100,'před přechodem'),(600,0,'během přechodu'),(970,100,'po přechodu')):
            c.circle(x, 235, 58, GOLD, '#6d5031', 2);c.circle(x+px, 235, 16, BLUE, BG, 2)
            c.text(x-110, 325, label, MUTED, 22)
        c.arrow(145, 490, 1090, 490, MUTED);c.arrow(145, 490, 145, 370, MUTED)
        points=[]
        for i in range(851):
            u=i/850
            drop=max(0,min(1,(u-.35)/.08,(.65-u)/.08))
            points.append((175+i,395+60*drop))
        c.line(points, BLUE, 4)
        c.text(60, 365, 'jas', MUTED, 22);c.text(1010, 500, 'čas', MUTED, 22)
        c.text(180, 535, 'Názorná křivka bez šumu; hloubka závisí také na poměru velikostí.', MUTED, 22)
    elif k == 'edu-stellar-orbit':
        c.text(65, 90, 'Opakovaně změříme polohu hvězdy a sledujeme její oběh.', WHITE, 25)
        c.d.ellipse((105, 175, 705, 485), outline=BLUE, width=3)
        focusx=405-math.sqrt(300**2-155**2);c.circle(focusx,330,16,GOLD,GOLD,1)
        for a in (.2,.8,1.5,2.1,2.7,3.3,4.1,4.9,5.5):
            c.circle(405+300*math.cos(a),330+155*math.sin(a),6,WHITE,WHITE,1)
        c.text(150, 365, 'centrální hmotnost', GOLD, 22)
        c.box(770, 190, 1140, 475, VIOLET)
        c.paragraph(795, 220, 'Velikost dráhy + doba oběhu', 310, WHITE, 27)
        c.arrow(950, 320, 950, 370, VIOLET)
        c.paragraph(795, 400, 'Odhad centrální hmotnosti', 310, VIOLET, 25)
        c.text(65, 530, 'Idealizovaná dráha, nikoli měření hvězdy S2; měřítko a projekce jsou zjednodušené.', MUTED, 21)
    elif k == 'edu-ligo-paths':
        c.text(65, 90, 'Fotodetektor měří interferenci světla z obou ramen.', WHITE, 25)
        c.line([(540,175),(540,420),(785,420)], GRID, 6)
        c.d.rectangle((514,162,566,175),fill=GOLD)
        c.d.rectangle((785,394,798,446),fill=GOLD)
        c.arrow(530,389,530,190,BLUE)
        c.arrow(550,190,550,389,BLUE)
        c.arrow(566,410,771,410,BLUE)
        c.arrow(771,430,566,430,BLUE)
        c.d.polygon([(524,420),(540,404),(556,420),(540,436)],fill=VIOLET)
        c.arrow(148,420,518,420,GOLD);c.text(148,452,'laser',GOLD,24)
        c.text(265,318,'dělič světla',VIOLET,24);c.arrow(398,345,525,408,VIOLET,2)
        c.text(586,150,'zrcadlo',GOLD,23)
        c.text(819,406,'zrcadlo',GOLD,23)
        c.arrow(540,444,540,506,GREEN);c.box(485,506,595,546,GREEN)
        c.text(622,511,'fotodetektor',GREEN,23)
        c.text(65,555,'Princip: optické dutiny a další zrcadla nejsou zakreslené.',MUTED,18)
    elif k == 'edu-neutron-capture':
        for x, color, title in ((65,BLUE,'Záchyt neutronu'),(655,VIOLET,'Přeměna beta minus')):
            c.box(x,125,x+485,495,color);c.text(x+25,150,title,color,27)
        c.text(110,240,'jádro + neutron',WHITE,26);c.arrow(300,290,300,345,BLUE)
        c.text(110,375,'stejný počet protonů',WHITE,24);c.text(110,415,'o jeden neutron více',BLUE,24)
        c.text(690,240,'neutron → proton',WHITE,27);c.arrow(900,290,900,345,VIOLET)
        c.text(690,375,'o jeden proton více',VIOLET,24);c.text(690,415,'vzniká jiný prvek',WHITE,24)
        c.text(65,525,'Při přeměně beta minus se uvolní také elektron a elektronové antineutrino.',MUTED,21)
        c.text(65,555,'Dva základní kroky; skutečný r-proces zahrnuje rozsáhlou síť reakcí.',MUTED,20)
    elif k == 'edu-galaxy-collision':
        c.text(65,90,'Při setkání galaxií se různé složky chovají odlišně.',WHITE,25)
        rng=random.Random(24)
        for x,label,color in ((65,'Hvězdy',BLUE),(655,'Plyn',GOLD)):
            c.box(x,150,x+485,495,color);c.text(x+25,175,label,color,29)
        for cx, color in ((230, BLUE), (378, VIOLET)):
            for _ in range(24):
                x = cx + max(-116, min(116, rng.gauss(0, 48)))
                y = 318 + max(-60, min(60, rng.gauss(0, 27)))
                c.circle(x,y,3,color,color,1)
        c.arrow(145,395,260,395,BLUE)
        c.arrow(463,243,348,243,VIOLET)
        c.paragraph(90,435,'Velké rozestupy: přímé srážky hvězd jsou vzácné.',435,WHITE,22)
        cloud = Image.new('RGBA', (410, 175))
        pixels = cloud.load()
        for y in range(175):
            for x in range(410):
                wobble = 0.85 + 0.10*math.sin(x/13+y/15) + 0.07*math.cos(x/9-y/12)
                left = math.exp(-((x-122)/66)**2-((y-92)/40)**2)*wobble
                right = math.exp(-((x-288)/66)**2-((y-84)/40)**2)*wobble
                hot = math.exp(-((x-205)/28)**2-((y-88)/48)**2)
                strength = min(1, 0.90*(left+right)+0.83*hot)
                if strength > .02:
                    mix = min(1, 1.6*hot)
                    pixels[x,y] = (255,int(145+86*mix),int(82+108*mix),int(255*strength))
        c.im.paste(cloud,(690,225),cloud)
        c.arrow(706,317,774,317,GOLD)
        c.arrow(1084,309,1020,309,GOLD)
        c.line([(895,286),(930,234),(944,234)],MUTED,2)
        c.text(951,220,'zahřátý plyn',GOLD,22)
        c.paragraph(680,435,'Při střetu se plyn může stlačit a zahřát.',435,WHITE,22)
        c.text(65,535,'Jde o princip, nikoli předpověď osudu konkrétní dvojice galaxií.',MUTED,22)
    elif k == 'edu-hubble-routes':
        c.text(65,90,'Obě cesty určují dnešní H₀, nikoli dvě různé epochy.',WHITE,25)
        rows=[(185,'Reliktní záření','kosmologický model','≈ 67–68',BLUE),
              (380,'Vzdálenosti + posuvy','kalibrace měřítek','≈ 73–74',GOLD)]
        for y,left,middle,value,color in rows:
            c.box(65,y,420,y+100,color);c.paragraph(85,y+28,left,315,color,24)
            c.arrow(435,y+50,490,y+50,color)
            c.box(505,y,835,y+100,color);c.paragraph(525,y+28,middle,290,WHITE,23)
            c.arrow(850,y+50,900,y+50,color);c.text(930,y+27,value,color,30)
        c.text(65,525,'Ilustrační skupiny výsledků v km/s/Mpc; nejsou to intervaly nejistoty.',MUTED,22)
        c.text(65,555,'Přesná čísla, data a předpoklady patří vždy ke konkrétní studii.',MUTED,20)
    elif k == 'edu-cosmic-budget':
        c.text(65,90,'Dnešní energetická bilance v modelu ΛCDM · zaokrouhlené hodnoty',WHITE,24)
        angle=-90
        for value,color in ((5,GOLD),(27,BLUE),(68,VIOLET)):
            c.d.pieslice((100,170,480,550),angle,angle+3.6*value,fill=color);angle+=3.6*value
        c.circle(290,360,108,BG,BG,1);c.text(223,342,'100 %',WHITE,32)
        for y,value,label,color in ((200,'5 %','běžná hmota',GOLD),(310,'27 %','temná hmota',BLUE),(420,'68 %','temná energie',VIOLET)):
            c.text(575,y,value,color,35);c.text(760,y+8,label,WHITE,28)
        c.text(545,525,'Podíly se v historii vesmíru měnily.',MUTED,22)
    elif k == 'edu-atmosphere-windows':
        c.text(65,90,'Co zpravidla propouští atmosféra až k povrchu?',WHITE,25)
        rows=[('Gama a rentgenové','prakticky ne',VIOLET),('Ultrafialové','většinu pohltí',VIOLET),
              ('Viditelné','široké okno',GREEN),('Infračervené','jen vybraná pásma',GOLD),('Rádiové','široká, ale ne všechna pásma',GREEN)]
        for i,(label,state,color) in enumerate(rows):
            y=160+i*65;c.text(95,y,label,WHITE,25);c.box(520,y-4,1100,y+45,color);c.text(545,y+3,state,color,23)
        c.text(65,520,'Propustnost závisí na vlnové délce, vodní páře, výšce a podmínkách.',MUTED,22)
        c.text(65,552,'Názorný přehled, nikoli přesná křivka propustnosti.',MUTED,20)
    elif k == 'edu-webb-l2':
        c.text(65,90,'Slunce, Země a okolí bodu L2 · silně zjednodušené měřítko',WHITE,24)
        c.circle(150,315,65,GOLD,'#725026',3);c.text(95,410,'Slunce',GOLD,27)
        c.circle(570,315,29,BLUE,'#244768',2);c.text(530,410,'Země',BLUE,27)
        c.line([(615,315),(1110,315)],GRID,2);c.circle(950,315,6,WHITE,WHITE,1)
        c.text(935,340,'L2',WHITE,25)
        c.d.ellipse((885,185,1015,445),outline=VIOLET,width=3)
        c.circle(995,220,12,VIOLET,VIOLET,1);c.text(1035,200,'Webb',VIOLET,25)
        c.arrow(620,165,950,165,MUTED,2);c.text(640,125,'≈ 1,5 milionu km',WHITE,24)
        c.arrow(240,260,480,260,GOLD);c.text(240,205,'světlo a teplo',GOLD,22)
        c.text(65,515,'Webb se pohybuje kolem Slunce na dráze v okolí L2, nikoli přímo v bodě.',MUTED,22)
        c.text(65,547,'Kresba není přesnou projekcí prostorové halo dráhy.',MUTED,20)
    elif k == 'edu-interferometry-baselines':
        c.text(65,90,'Při stejné vlnové délce pomáhají větší rozestupy rozlišit jemnější detail.',WHITE,24)
        for y,xs,label in ((245,(390,450,510,570),'kratší základny'),(430,(150,450,750,1050),'delší základny')):
            c.line([(xs[0],y+25),(xs[-1],y+25)],VIOLET,3)
            for x in xs:
                c.d.arc((x-25,y-35,x+25,y+5),0,180,fill=BLUE,width=4);c.line([(x,y-10),(x,y+25)],BLUE,3)
            c.text(65,y-90,label,GOLD,25)
        c.text(65,510,'Základna = vzdálenost mezi dvojicí teleskopů nebo antén.',WHITE,23)
        c.text(65,547,'Pro úplný obraz jsou důležité různé délky i směry; krátké základny mají také roli.',MUTED,20)
    elif k == 'edu-detector-layers':
        cx,cy=350,325
        for radius,color in ((180,VIOLET),(135,GOLD),(85,BLUE)):
            c.circle(cx,cy,radius,color,width=18)
        c.circle(cx,cy,8,WHITE,WHITE,1);c.text(300,520,'místo srážky',WHITE,22)
        c.arrow(cx+15,cy+5,560,410,GREEN,3);c.text(565,405,'mion',GREEN,23)
        for y,color,title,body in ((160,BLUE,'Dráhové detektory','Polohy a zakřivení drah nabitých částic'),
                                   (290,GOLD,'Kalorimetry','Uložená energie částic'),
                                   (420,VIOLET,'Mionové detektory','Stopy pronikavých mionů')):
            c.text(665,y,title,color,28);c.paragraph(665,y+42,body,460,WHITE,22)
        c.text(65,555,'Zjednodušený příčný řez obecným detektorem; vrstvy konkrétních experimentů se liší.',MUTED,18)
    elif k == 'edu-spectrum-reader':
        c.text(65,90,'Osa y ukazuje množství přijatého záření.',WHITE,25)
        x0,x1,y0=150,1080,455
        c.arrow(x0,y0,x1+20,y0,MUTED);c.arrow(x0,y0,x0,145,MUTED)
        points=[]
        for i in range(901):
            t=i/900;base=.50+.12*t
            f=base-.30*math.exp(-.5*((t-.29)/.022)**2)+.30*math.exp(-.5*((t-.72)/.022)**2)
            points.append((x0+t*(x1-x0),y0-f*330))
        c.line(points,BLUE,4)
        c.text(45,130,'záření',MUTED,22)
        c.text(750,490,'vlnová délka',MUTED,24)
        c.text(220,180,'absorpční pokles',GOLD,24);c.arrow(350,215,420,355,GOLD,2)
        c.text(760,115,'emisní vrchol',VIOLET,24);c.arrow(870,150,822,192,VIOLET,2)
        c.text(520,350,'kontinuum',WHITE,22)
        c.text(65,540,'Modelový příklad bez číselné stupnice; nejde o spektrum konkrétního objektu.',MUTED,21)
    elif k == 'edu-redshift-distance':
        c.text(65,90,'Stejné z, dva různé údaje: doba cesty a dnešní vzdálenost',WHITE,25)
        for x,y,value in ((95,150,'z'),(340,140,'Světlo cestovalo'),(750,140,'Dnešní vzdálenost')):
            c.text(x,y,value,MUTED,25)
        c.text(340,178,'miliardy let',BLUE,21);c.text(750,178,'miliardy světelných let',GOLD,21)
        for i,row in enumerate((('0,01','0,144','0,145'),('0,1','1,35','1,42'),('1','7,95','11,1'),('6','12,87','27,5'))):
            y=235+i*68
            if i==2:c.box(65,y-8,1125,y+48,GRID,'#1a2c43')
            for x,value,color in zip((95,370,800),row,(WHITE,BLUE,GOLD)):c.text(x,y,value,color,29)
        c.text(65,530,'Plochý ΛCDM: H₀ = 67,4 km/s/Mpc; Ωm = 0,315; záření zanedbáno.',MUTED,21)
        c.text(65,558,'Zaokrouhlené modelové výpočty, nikoli samostatná měření vzdáleností.',MUTED,20)
    elif k == 'edu-orbital-density':
        c.text(65,90,'Orbital 1s vodíku: řez hustotou pravděpodobnosti nálezu elektronu',WHITE,24)
        size=360;pic=Image.new('RGB',(size,size));px=pic.load()
        for y in range(size):
            for x in range(size):
                r=math.hypot((x-size/2)/(size/6),(y-size/2)/(size/6))
                density=math.exp(-2*r)
                v=math.sqrt(density)  # Monotonic display stretch to reveal the faint wings.
                px[x,y]=(int(11+225*v),int(20+224*v),int(36+219*v))
        c.im.paste(pic,(100,160));c.circle(280,340,3,GOLD,GOLD,1)
        c.arrow(530,340,285,340,GOLD,2);c.text(540,322,'jádro',GOLD,22)
        c.paragraph(650,185,'Světlejší oblast = větší hustota pravděpodobnosti.',460,WHITE,28)
        c.paragraph(650,315,'Elektron nemá zakreslenou oběžnou dráhu ani pevný okraj obalu.',460,BLUE,25)
        c.text(65,545,'Matematická ilustrace stavu 1s; jas je názorný a nejde o fotografii atomu.',MUTED,21)
    elif k == 'edu-tone-pulse':
        c.text(115,95,'Průběh v čase',WHITE,26);c.text(715,95,'Zastoupení frekvencí',WHITE,26)
        c.text(715,132,'Obě spektra mají vrchol přepočtený na 1.',MUTED,21)
        for baseline,sigma,fwidth,color,label in ((265,85,20,BLUE,'dlouhý tón'),(442,20,85,GOLD,'krátký zvuk')):
            c.text(55,baseline-86,label,color,24)
            c.arrow(110,baseline,558,baseline,MUTED,2)
            c.arrow(680,baseline,1128,baseline,MUTED,2)
            c.line([(900,baseline),(900,baseline-63)],GRID,2)
            c.text(651,baseline-12,'0',MUTED,21)
            c.line([(110+i,baseline-45*math.exp(-.5*((i-220)/sigma)**2)*math.cos((i-220)*.27)) for i in range(441)],color,3)
            c.line([(680+i,baseline-62*math.exp(-.5*((i-220)/fwidth)**2)) for i in range(441)],color,4)
        c.text(65,535,'Kratší zvuk má širší spektrum. Svislá značka ukazuje stejnou střední frekvenci.',MUTED,21)
    elif k == 'edu-entanglement-distance':
        c.paragraph(65,90,'Dva pozorovatelé vzdálení milion světelných let měří stejnou vlastnost, každý na své částici z provázané dvojice.',1070,WHITE,25)
        for x,label in ((100,'Pozorovatel A'),(805,'Pozorovatel B')):
            c.box(x,180,x+290,400,BLUE if x==100 else VIOLET)
            c.text(x+20,205,label,WHITE,25)
            c.text(x+25,270,'0 1 0 0 1 1',GOLD,30)
            c.text(x+20,345,'záznam šesti měření',MUTED,21)
        c.paragraph(425,205,'Pokus provedou šestkrát. Každá číslice je výsledek jednoho měření. Oba záznamy se v tomto příkladu shodují.',360,MUTED,23)
        c.arrow(165,460,1040,460,GREEN)
        c.text(150,490,'Záznamy porovnají až po doručení zprávy (nejméně milion let).',GREEN,24)
        c.text(65,540,'Uvedené řady jsou názorné; nejde o uskutečněný experiment na této vzdálenosti.',MUTED,21)
    else:
        raise ValueError('Unknown Kosmopedie diagram: '+k)
    return c.finish()
