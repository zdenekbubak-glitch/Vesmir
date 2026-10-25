"""Original teaching diagrams for quantum fields; illustrations, not measurements."""
import math
from kosmopedie_diagrams import Canvas, WHITE, MUTED, BLUE, GOLD, VIOLET, GREEN, GRID


def diagram(entry):
    c=Canvas(entry['title']);k=entry['diagram']
    if k=='edu-b5-qft':
        rows=[(105,BLUE,'Pole','Co tvoří fyzikální popis?','Elektronové, elektromagnetické a další pole.'),
              (255,GOLD,'Kvantová pravidla','Co můžeme předpovědět?','Možné stavy a pravděpodobnosti reakcí.'),
              (405,VIOLET,'Speciální relativita','Jak spolu souvisejí prostor a čas?','Pravidla platí i při vysokých rychlostech.')]
        for y,col,title,question,body in rows:
            c.box(65,y,1135,y+125,col)
            c.text(90,y+15,title,col,29)
            c.text(400,y+15,question,WHITE,25,maxwidth=700)
            c.paragraph(400,y+58,body,690,MUTED,23)
        c.text(65,550,'QFT spojuje tyto tři stavební kameny do společného výpočetního rámce.',MUTED,21)
    elif k=='edu-b5-annihilation':
        c.text(65,90,'Příklad s nulovou celkovou hybností před reakcí',WHITE,26)
        for x,col,label,symbol in ((210,BLUE,'elektron','e⁻'),(470,VIOLET,'pozitron','e⁺')):
            c.circle(x,260,48,col,'#152137');c.text(x-20,238,symbol,col,32)
            c.text(x-65,335,label,col,25)
        c.text(327,240,'+',WHITE,32);c.arrow(570,260,680,260,WHITE)
        for y,col in ((220,GOLD),(300,GOLD)):
            c.line([(720+i,y+13*math.sin(i*.13)) for i in range(301)],col,3)
        c.arrow(850,220,720,220,GOLD);c.arrow(890,300,1020,300,GOLD)
        c.text(760,350,'dva fotony',GOLD,27)
        c.paragraph(760,395,'Opačné směry, stejné energie.',350,WHITE,24)
        c.text(65,455,'Náboj: −e + e = 0 → 0',WHITE,27)
        c.text(65,505,'Celková energie a hybnost se zachovávají.',GREEN,26)
        c.text(65,550,'Schéma vstupu a výstupu reakce; nejde o záznam drah ani Feynmanův diagram.',MUTED,20)
    elif k=='edu-b5-fields':
        c.text(65,90,'Různá pole → různé druhy částic',WHITE,27)
        for y,col,name,result in ((155,BLUE,'Elektromagnetické pole','fotony'),(280,GOLD,'Elektronové pole','elektrony a pozitrony'),(405,VIOLET,'Higgsovo pole','Higgsovy bosony')):
            c.box(65,y,570,y+90,col);c.text(90,y+27,name,col,27,maxwidth=455)
            c.arrow(595,y+45,695,y+45,col)
            c.text(725,y+27,result,WHITE,27,maxwidth=400)
        c.text(65,540,'Částice jsou kvanta příslušných polí; řádky nejsou kresbou jejich tvaru.',MUTED,22)
    elif k=='edu-b5-vacuum':
        c.text(65,90,'Kvantový oscilátor v nejnižším energetickém stavu',WHITE,26)
        x0,x1,y0=110,660,455
        c.arrow(x0,y0,x1+15,y0,MUTED);c.arrow(x0,y0,x0,160,MUTED)
        c.line([(x0+i,y0-220*math.exp(-.5*((i-275)/80)**2)) for i in range(551)],BLUE,4)
        c.text(155,150,'hustota pravděpodobnosti',BLUE,23)
        c.text(195,490,'záporná poloha',MUTED,21);c.text(465,490,'kladná poloha',MUTED,21)
        c.text(377,460,'0',WHITE,21)
        c.paragraph(745,175,'Nejnižší energie neznamená přesně určenou polohu.',380,WHITE,29)
        c.paragraph(745,330,'Rozdělení má nenulovou šířku i bez dalšího buzení.',380,GOLD,25)
        c.text(65,545,'Názorný model bez číselné stupnice; křivka není průběhem pole v čase.',MUTED,21)
    elif k=='edu-b5-casimir':
        c.text(65,90,'Příklad dvou blízkých vodivých desek',WHITE,27)
        for x in (440,700):c.box(x,160,x+35,440,BLUE,'#304e70')
        c.arrow(325,300,425,300,GOLD,5);c.arrow(845,300,750,300,GOLD,5)
        c.text(135,345,'přitažlivá síla',GOLD,25);c.text(845,345,'přitažlivá síla',GOLD,25)
        c.line([(475,475),(700,475)],MUTED,2)
        c.line([(475,465),(475,485)],MUTED,2);c.line([(700,465),(700,485)],MUTED,2)
        c.text(500,490,'vzdálenost',WHITE,24)
        c.text(65,540,'Síla závisí i na materiálu, teplotě a geometrii. Rozměry a síly nejsou v měřítku.',MUTED,21)
    elif k=='edu-b5-higgs':
        for x,col,title in ((65,BLUE,'Higgsovo pole'),(650,GOLD,'Higgsův boson')):
            c.box(x,110,x+485,505,col);c.text(x+25,130,title,col,31)
        c.line([(95,300),(520,300)],BLUE,5)
        c.text(95,345,'Nenulová hodnota ve vakuu',WHITE,24,maxwidth=425)
        c.paragraph(95,400,'Přítomná i bez Higgsových bosonů.',425,MUTED,24)
        c.line([(680+i,300-100*math.exp(-.5*((i-210)/40)**2)) for i in range(426)],GOLD,4)
        c.text(680,345,'Kvantum pole',WHITE,25)
        c.paragraph(680,400,'Excitace: do pole byla dodána energie.',425,MUTED,24)
        c.text(65,545,'Čáry jsou názorné značky; nejde o skutečný tvar pole ani bosonu.',MUTED,22)
    elif k=='edu-b5-mass':
        for x,col,title in ((65,BLUE,'Elektron'),(650,GOLD,'Proton')):
            c.box(x,110,x+485,510,col);c.text(x+25,135,title,col,32)
        c.circle(305,265,35,BLUE,'#1d354f');c.text(285,243,'e⁻',WHITE,31)
        c.paragraph(95,350,'Klidová hmotnost souvisí s vazbou elektronového pole na Higgsovo pole.',425,WHITE,26)
        c.circle(890,265,85,GOLD,'#29303d')
        for x,y,t in ((855,235,'u'),(925,235,'u'),(890,295,'d')):
            c.circle(x,y,20,GOLD,'#3b3540');c.text(x-8,y-17,t,WHITE,23)
        c.paragraph(680,375,'Většina hmotnosti souvisí s energií kvarků a gluonového pole uvnitř.',425,WHITE,25)
        c.text(65,545,'Názorné srovnání, bez poměrů velikostí a bez procentního rozdělení energie.',MUTED,21)
    elif k=='edu-b5-gravity':
        for x,col,title,body in ((65,BLUE,'Obecná relativita','Hmota a energie ovlivňují geometrii prostoročasu.'),
                                 (650,GOLD,'Kvantová fyzika','Kvantové stavy, pravděpodobnosti a měření.')):
            c.box(x,110,x+485,300,col);c.text(x+25,132,title,col,29)
            c.paragraph(x+25,190,body,430,WHITE,26)
        c.arrow(310,315,505,385,BLUE);c.arrow(890,315,695,385,GOLD)
        c.box(210,400,990,525,VIOLET)
        c.text(255,415,'Společný popis: kvantová gravitace',VIOLET,31,maxwidth=690)
        c.text(255,470,'Kvantové chování i samotné geometrie',WHITE,26,maxwidth=690)
        c.text(65,550,'Úplnou, experimentálně potvrzenou teorii zatím hledáme.',MUTED,22)
    else:raise ValueError(k)
    return c.finish()
