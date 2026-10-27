"""Reproducible explanatory diagrams for particle topics in Kosmopedie.

All figures are teaching models, not detector drawings or experimental data.
"""
import math
from PIL import Image, ImageDraw

BG = '#0b1424'
WHITE = '#edf4ff'
MUTED = '#b6c7dd'
BLUE = '#76c8ff'
GOLD = '#ffd287'
GREEN = '#91d9b5'
PURPLE = '#c4b0ff'


def diagram(entry):
    from assign_article_images import font
    im = Image.new('RGB', (1200, 630), BG)
    d = ImageDraw.Draw(im)

    def text(x, y, label, color=WHITE, size=25):
        d.text((x, y), label, font=font(size), fill=color)

    def line(points, color=BLUE, width=4):
        d.line(points, fill=color, width=width)

    def arrow(x, y, xx, yy, color=BLUE):
        line([(x, y), (xx, yy)], color)
        angle = math.atan2(yy-y, xx-x)
        d.polygon([(xx, yy), (xx-14*math.cos(angle-.5), yy-14*math.sin(angle-.5)),
                   (xx-14*math.cos(angle+.5), yy-14*math.sin(angle+.5))], fill=color)

    def circle(x, y, r=10, color=GOLD):
        d.ellipse((x-r, y-r, x+r, y+r), outline=color, width=3)

    text(45, 25, entry['title'], size=34)
    kind = entry['diagram']
    if kind == 'particle-accelerators':
        text(45, 82, 'Volba zařízení závisí na otázce, kterou chceme měřit.', MUTED, 25)
        for top, name, subtitle, color in (
            (135, 'Srážeč', 'Dva vstřícné svazky; měříme produkty srážky.', BLUE),
            (280, 'Pevný terč', 'Svazek zasáhne látku; vzniknou další částice.', GOLD),
            (425, 'Svazek neutrin', 'Neutrina z rozpadů míří ke vzdálenému detektoru.', GREEN),
        ):
            text(55, top, name, color, 29)
            text(55, top+40, subtitle, MUTED, 23)
            y = top+30
            if name == 'Srážeč':
                arrow(680, y, 850, y, color); arrow(1110, y, 940, y, color)
                circle(895, y, 14, color)
                for dx, dy in [(60, -40), (60, 40), (-45, 40)]:
                    arrow(895, y, 895+dx, y+dy, PURPLE)
            elif name == 'Pevný terč':
                arrow(690, y, 855, y, color)
                d.rectangle((865, y-35, 890, y+35), outline=color, width=4)
                for dy in [-35, 0, 35]: arrow(900, y, 1110, y+dy, PURPLE)
            else:
                arrow(670, y, 760, y, GOLD)
                d.rectangle((770, y-28, 790, y+28), outline=GOLD, width=3)
                arrow(800, y, 875, y, GOLD)
                text(800, y-36, 'piony', GOLD, 21)
                for x in range(890, 1030, 28): line([(x, y), (x+15, y)], GREEN, 4)
                d.rectangle((1050, y-38, 1125, y+38), outline=GREEN, width=3)
                text(910, y+40, 'neutrina', GREEN, 21)
    elif kind == 'particle-discovery':
        text(50, 83, 'Příklad hledání krátce žijící částice v produktech rozpadu', MUTED, 24)
        x0, x1, y0 = 130, 1090, 460
        arrow(x0, y0, x1+25, y0, MUTED); arrow(x0, y0, x0, 145, MUTED)
        text(62, 120, 'počet událostí', MUTED, 22)
        text(600, 480, 'hmotnost odvozená z produktů rozpadu', MUTED, 23)
        def background(t): return 65 + 125*math.exp(-1.5*t)
        def signal(t): return 145*math.exp(-.5*((t-.56)/.045)**2)
        line([(x0+i*9, y0-background(i/100)) for i in range(101)], BLUE, 4)
        line([(x0+i*9, y0-background(i/100)-signal(i/100)) for i in range(101)], GOLD, 5)
        line([(680, 155), (730, 155)], BLUE, 4); text(747, 139, 'známé procesy', BLUE, 23)
        line([(680, 194), (730, 194)], GOLD, 4); text(747, 178, 'navíc nový příspěvek', GOLD, 23)
        arrow(470, 195, 625, 239, PURPLE)
        text(160, 150, 'hledaný přebytek', PURPLE, 25)
        text(130, 535, 'Ilustrační křivky bez číselné stupnice; nejde o měření ani výpočet sigma.', MUTED, 22)
    elif kind == 'particle-antiatoms':
        text(55, 85, 'Co porovnáváme u vodíku a antivodíku', MUTED, 25)
        for cx, label, center, orbit, color in [(330, 'Vodík', 'proton (+)', 'elektron (−)', BLUE),
                                               (870, 'Antivodík', 'antiproton (−)', 'pozitron (+)', GOLD)]:
            text(cx-100, 135, label, color, 30)
            circle(cx, 315, 105, color)
            circle(cx, 315, 18, color)
            circle(cx+76, 242, 12, PURPLE)
            text(cx-115, 345, center, color, 24)
            text(cx-105, 175, orbit, PURPLE, 24)
        text(100, 470, 'Porovnání spektrálních čar', BLUE, 27)
        text(685, 470, 'Měření pohybu v gravitaci', GOLD, 27)
        text(75, 530, 'Symbolické složení atomů: kružnice není skutečná dráha elektronu či pozitronu.', MUTED, 22)
    elif kind == 'particle-neutrino-oscillations':
        text(55, 82, 'Zjednodušený model dvou druhů ve vakuu; energie je stejná.', MUTED, 24)
        x0, x1, top, bottom = 140, 1100, 170, 465
        arrow(x0, bottom, x1+20, bottom, MUTED)
        arrow(x0, bottom, x0, top-25, MUTED)
        text(42, 127, 'pravděpodobnost', MUTED, 22)
        text(65, top-15, '100 %', MUTED, 21); text(90, bottom-15, '0 %', MUTED, 21)
        for i in range(5):
            x=x0+i*(x1-x0)/4
            line([(x,bottom),(x,bottom+8)], MUTED, 2)
        for color, same in [(BLUE, True), (GOLD, False)]:
            points=[]
            for i in range(501):
                t=i/500
                change=.8*math.sin(2*math.pi*t)**2
                p=1-change if same else change
                points.append((x0+(x1-x0)*t,bottom-(bottom-top)*p))
            line(points, color, 4)
        text(205, 490, 'původní druh', BLUE, 25)
        text(540, 490, 'druhý druh', GOLD, 25)
        text(865, 490, 'vzdálenost →', MUTED, 23)
        text(70, 540, 'Dvě pravděpodobnosti se sčítají na 100 %. Skutečná neutrina mají tři druhy.', MUTED, 22)
    elif kind == 'particle-air-shower':
        text(55, 85, 'Primární částice z kosmu předá energii částicím v atmosféře.', MUTED, 24)
        arrow(600, 125, 600, 210, GOLD)
        text(650, 145, 'proton nebo atomové jádro', GOLD, 24)
        circle(600, 220, 12, GOLD)
        text(70, 200, 'srážka s jádrem vzduchu', MUTED, 24)
        line([(410,220),(570,220)], MUTED, 2)
        nodes = [(600,220)]
        for level, yy in enumerate([305, 385, 455]):
            new=[]
            spread=155/(level+1)
            for x,y in nodes:
                for shift in [-spread, spread]:
                    xx=x+shift
                    arrow(x,y+12,xx,yy-8,BLUE)
                    circle(xx,yy,5,BLUE)
                    new.append((xx,yy))
            nodes=new
        arrow(610,230,930,455,PURPLE)
        text(940,365,'mion',PURPLE,25)
        for i in range(14):
            t=i/14
            tt=min(t+.04,1)
            line([(610+500*t,230+120*t),(610+500*tt,230+120*tt)],GREEN,3)
        text(945,285,'neutrino',GREEN,23)
        line([(90,500),(1120,500)], MUTED, 4)
        for x in [220,480,740,1000]:
            d.rounded_rectangle((x-38,490,x+38,525),radius=7,outline=GOLD,width=3)
        text(350,535,'pozemní detektory zachytí část spršky',GOLD,24)
        text(70,575,'Schéma větvení: nesleduje jednotlivé reakce ani skutečné počty a energie částic.',MUTED,21)
    else:
        raise ValueError('Unknown particle diagram: '+kind)
    if kind != 'particle-air-shower':
        text(45, 592, 'VLASTNÍ SCHÉMA · vysvětlující model, nikoli naměřená data', MUTED, 20)
    return im
