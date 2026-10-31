# Přiřazování odkazů z novinek do Kosmopedie

Odkazy sestavuje `tools/build_static.py` při generování webu pro všechny uložené novinky. Pravidla `EXPLAINER_PATTERNS` propojují ID tématu s českými a anglickými výrazy. Nejde o úplný jazykový analyzátor; významové varianty doplňujeme výslovně.

Text se převádí na malá písmena bez diakritiky, sjednocují se mezery a spojovníky. Pravidla respektují hranice slov. České koncovky zachycují regulární výrazy; nepravidelné tvary (například díra/děr) mají vlastní varianty. Společné pravidlo `BLACK_HOLE_PATTERN` se používá pro témata o černých dírách.

Nadpis má při výběru vyšší váhu než souhrn článku. Zůstává limit dvou odkazů. Pokud vhodné téma nenajdeme, blok se nevytvoří. Obecná slova jako čas, energie nebo prostor sama o sobě nejsou důvodem pro přiřazení tématu. Obecné „zakřivené prostory“ se nepřiřazují tématu o tvaru vesmíru.

Při přidání nového tématu:

1. Přidejte jeho ID a konkrétní výrazy do `EXPLAINER_PATTERNS`, včetně českého skloňování a vhodných anglických názvů.
2. Doplňte pozitivní a případně negativní příklady do `tools/test_explainer_links.py`.
3. Spusťte `python tools/test_explainer_links.py` a generování webu. Zkontrolujte vybrané odkazy v kontextu skutečných článků.

Generátor upozorní na téma bez pravidla. Test navíc vyžaduje pokrytí všech témat. To pomáhá odhalit chybějící pravidla při příštím rozšíření katalogu.
