# Kosmopedie – 9. várka po autorské kontrole

Finální balíček 27. 10. 2026 se všemi schválenými připomínkami. Předloha: aktuální větev `main`: https://github.com/zdenekbubak-glitch/Vesmir . Před zabalením znovu načteno všech sedm upravovaných původních souborů; od stažení předlohy se nezměnily. Balíček není z této relace nahrán na GitHub.

## Obsah a návaznost

Pět nových témat exp-065 až exp-069 ve stávajícím okruhu **Částice a základní síly**. Po nasazení bude mít tento okruh sedm témat a celá Kosmopedie 69 témat. Původních 64 témat, jejich data, zdroje a obrázková přiřazení zůstaly zachované.

| Nové téma | Co doplňuje | Co neopakuje |
| --- | --- | --- |
| Proč používáme různé druhy urychlovačů částic? | Přesnost a četnost reakcí, SuperKEKB/Belle II, J-PARC/T2K, pevné terče a NA62. | Základní výklad fungování LHC z exp-034. |
| Jak ze signálů detektoru poznáme částici a objev? | Rekonstrukce, kombinace vrstev, invariantní hmotnost, pozadí a statistická významnost. | Stručný přehled LHC ani nové opakované téma o Higgsově bosonu. |
| Jak zkoumáme antiatomy a převahu hmoty nad antihmotou? | Výroba a uvěznění antivodíku, spektroskopie, gravitace, oddělení těchto testů od kosmologické asymetrie. | Již vysvětlenou anihilaci a soupis částic standardního modelu. |
| Proč neutrina mění svůj druh? | Druh a hmotnostní stav, kvantový vývoj, úbytek/výskyt druhu, rozdíl oscilací a přímé hmotnostní metody KATRIN. | Popis konstrukce IceCube a Super-Kamiokande z exp-063. |
| Co je kosmické záření a jak vznikají částicové spršky? | Primární částice, větvení spršky, pozemní rekonstrukce, fluorescence a vliv magnetických polí. | Neutrinové observatoře ani obecný částicový katalog. |

Porovnány také všechny současné nadpisy a výklady kvantového světa exp-040 až exp-049 a nové experimenty exp-060 až exp-064. Opakující se základy jsou řešeny odkazy na stávající témata. Každý nový text má perex, členěný výklad, dvě vybrané související zprávy, primární zdroje, pět souvisejících témat a závěrečný rámeček.

## Soubory v balíčku

Cesty v ZIPu jsou vůči kořeni repozitáře. Názvy souborů se nemění; nic se nemusí ručně přejmenovávat. Obsah složek ZIPu vložte do odpovídajících složek projektu.

- `data/explainery.json`: celý souhrnný soubor se 69 tématy.
- `data/article_image_catalog.json`: původní katalog a pět nových schémat.
- `data/article_image_assignments.json`: přidáno pět pevných přiřazení novým tématům.
- `data/kosmopedie_images.json`: doplněná tematická galerie a hledací označení.
- `tools/particle_diagrams.py`: nový skutečný projektový modul vykreslující pět schémat. Je potřebný pro jejich opětovné vytvoření.
- `tools/article_image_assets.py`: doplněno pouze volání tohoto modulu pro nová schémata.
- `tools/build_static.py`: přidáno pouze pět pravidel pro související odkazy z článků do nových témat.
- `assets/article-images/`: pět nových obrázků, zdrojových zmenšenin, náhledů a renderovacích otisků.
- `docs/Kosmopedie_plan_varek_6-9.md`: osmá várka označena jako nasazená, devátá jako připravená ke kontrole.
- tento předávací dokument.

Pracovní skripty přípravy, soubory pojmenované `varka9_*.py`, logy a prohlížečové kontroly nejsou součástí ZIPu. Tři soubory ve složce `tools/` výše naopak součástí projektu jsou a patří do stejnojmenné složky na GitHubu. `tools/build_explainery.py`, workflow a závislosti se neměnily; oprava českého řazení zůstává zachovaná. Vygenerované HTML se vytvoří stávajícím sestavením.

## Obrázky

Pět nových vysvětlujících schémat: tři uspořádání urychlovačových pokusů; model přebytku nad pozadím; vodík a antivodík; dvoudruhový model neutrinových oscilací; atmosférická částicová sprška. Katalog je označuje jako vlastní schémata pod CC BY 4.0, autor Kosmologické novinky. Výpočty a modely jsou výslovně odlišeny od měření. Neutrinový graf je dvoudruhový model ve vakuu, nikoli graf konkrétního experimentu. Obrázky mají 1200 × 630 px, náhledy 288 × 288 px; zdrojový kód je přiložen v projektu.

Téma o identifikaci částic má také druhý obrázek uvnitř textu: stávající pevně zvolené schéma vrstev detektoru `schema-detektor-vrstvy`. Tento již existující obrázek se do ZIPu znovu nepřibaluje. Všech šest použitých obrazů je zahrnuto v tematické galerii.

## Ověření

- Oba stávající generátory úspěšně sestavily web: 402 zpráv a 69 témat Kosmopedie.
- Ověřeny všechny interní odkazy pěti nových stránek, související témata, obrázky, jejich metadata, vyhledávací záznamy a zařazení do galerie.
- Chrome, šířky 1280 a 390 px: všech pět detailů, načtení všech obrázků a zvětšovací odkaz obrázku uvnitř textu; bez chyb skriptů, chybějících lokálních zdrojů a vodorovného přetékání.
- Ověřeno nové automatické prolinkování z článků, včetně vyloučení záměny částicového urychlovače s metaforou „kosmologický urychlovač“.
- Datové porovnání potvrdilo zachování všech původních 64 témat, celého původního katalogu a všech existujících přiřazení obrázků. V původních dvou upravovaných skriptech jsou pouze výše popsané doplňky.
- Odborné zdroje jsou uvedeny přímo u textů: CERN, CMS, ATLAS, Belle II/KEK, J-PARC/T2K, Fermilab, KATRIN/KIT, NASA, NOAA a Pierre Auger Observatory. Nejsou zaměňovány předpovědi budoucích strojů s existujícími výsledky ani statistická významnost s pravděpodobností pravdivosti teorie.

Zapracované připomínky: definice kaonu; odstranění nadbytečného „však“; vysvětlení rozpoznávání částice a nového objevu; kalorimetr; účinnost a záměny částic; konečné schválené vysvětlení pěti sigma; CP symetrie; leptogeneze; sjednocení výkladu neutrinových stavů a superpozice; srozumitelné vysvětlení rozdílů druhých mocnin hmotností.

Lokální náhled byl obnoven v C:/Projekty/Vesmir. V datech a webových odkazech nejsou cesty OneDrivu. Obrázky se na webu načítají z /assets/article-images/; ZIP zachovává tyto projektové cesty.
