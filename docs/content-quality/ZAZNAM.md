# Fáze 0 — výchozí stav a zkušební běh

Podklad: větev main, commit c79053d82f67e04f880b3e2ea9c54df57545e579. Měření je v reports/baseline.md. Nové ruční workflow má pouze právo čtení, používá stávající závislosti a ukládá výsledek jako artefakt. DRY_RUN=1 přesměruje pouze zápis historie. Čtení historie, výběr i překlad fungují stejně jako dnes. Zkušební výstup obsahuje celou simulovanou historii, takže je v artefaktu jasně označený cestou tmp/content-dryrun/news.json a nepatří do data/.

## Vazby zjištěné v main

| Součást | Vztah k článkům |
| --- | --- |
| daily-cosmo.yml | Pouze workflow_dispatch. Spouštěč mimo repozitář nelze ze zdrojů určit. Volá fetch_and_update, generuje kartu, ukládá změny, sestavuje a nasazuje Pages a odesílá sociální příspěvky. |
| generate_x_card, Buffer pro X a Facebook, Bluesky | Karta a Buffer používají generate_x_card.pick_item. Bluesky má vlastní výběr. Výběr karty může sáhnout do historie, pokud chybí dnešní položky. Před vynucením kontroly textu je nutné otestovat i den bez vhodného článku. |
| post_daily_to_x.py | Samostatný skript bez nalezeného odkazu z workflow. Aktivní cesta na X v daily-cosmo.yml vede přes Buffer. |
| bluesky-daily.yml | Samostatné ruční spuštění s možností náhledu. Pro zkoušku používat jen --dry-run. |
| repair-translations.yml / repair_untranslated.py | Druhý zapisovatel news.json. Importuje summarize_czech a DailyQuotaExhausted. U záložní položky přepisuje summary i title. Změna titulku mění URL, pokud už byla položka zveřejněna. |
| repair-image-translations.yml a fetch_images.py | Pracují s galerií, ne se souhrny článků. Pro metadata obrázků se používá image_rights. |
| quote-x.yml / quote_x_posts.py | Čte články kvůli tematickému párování, stav zapisuje samostatně. |
| weekly-linkedin.yml / send_weekly_linkedin.py | Čte news.json pro týdenní příspěvek. |
| weekly-newsletter.yml / send_weekly_newsletter.py | Čte news.json. Používá tools/newsletter_content.build_email, stejně jako ukázka newsletteru v generátoru webu. |
| test-gemini.yml | Ruční zkouška Gemini, žádný zápis článků. |
| build_static.py / build_explainery.py | První vytváří i Atom feed a sitemapu. Druhý čte články kvůli souvisejícím odkazům. Odkaz pro připomínky vede na redakce@kosmonovinky.cz. |
| assign_article_images.py | Čte články a témata Kosmopedie, řeší přiřazení náhledů a používá image_rights.image_rights a article_image_assets.make_asset. |
| social_tracking.py | Pro sociální kroky a evidenci dodává article_url, tracked_url, post_key, receipt a SPOOL. Přímé odkazy jsou závislé na stejném výpočtu adresy jako web. |
| submit_indexnow.py | Pracuje s výslednou sitemapou po nasazení. Články ani překlady nepřepisuje. |
| log_list.sig | V prohlédnutých skriptech a workflow se nepoužívá. Původ souboru se z kódu nepodařilo doložit. |

V main není sledovaný soubor pod clanky/. Po vypadnutí z historie 500 záznamů generátor článek znovu nevytvoří. Na čerstvě sestaveném webu tudíž jeho stránka chybí. To je stávající vlastnost.

## Odchylky a rozhodnutí pro další fáze

- Široký výběr má smysl. Úzce odborná slova mají být vodítkem pro hodnocení, protože tvrdý filtr by mohl vyřadit i důležitý objev.
- Rozlišit výpadek ověřovatele od zamítnutí konkrétního textu. Při výpadku pokračovat s dříve ověřenými kandidáty nebo s menším výběrem podle dohodnutého režimu. Zamítnutý text se nesmí vrátit záložní cestou.
- arXiv je úložiště a samotná přítomnost na arXivu nedokládá stav recenze. Číselnou signifikanci posuzovat podle kontextu práce, systematik a toho, co autoři skutečně tvrdí.
- Kontrola čísel potřebuje rozlišit ekvivalentní zápisy, jednotky a vazbu hodnoty na tvrzení. Prostá shoda číslic může přijmout nesprávný údaj a zamítnout správný převod.
- Referenční příklady sestavit před porovnáním nového promptu ve fázi 3. V další fázi začít kontrolami v režimu hlášení, protože v českém archivu už jedna položka postrádá přesně jednu závěrečnou značku.
- Rozsah změny v této fázi: pouze zkušební zápis, ruční workflow a měření. Zvrácení: odebrat nové soubory a vrátit funkci save_history podle diffu. Produkční workflow ani formát dat se nemění.

## Ověření a náklady

Místní zkouška se simulovanými odpověďmi ověřila deduplikaci, běžný český výsledek i zálohu při vyčerpání kvóty. Kontrolní součet data/news.json zůstal v obou případech shodný. Prošla kontrola syntaxe Pythonu a načtení YAML. Ruční běh v GitHub Actions s živými zdroji a Gemini bude ověřitelný po nahrání.

Přírůstek automatických denních nákladů: 0 Kč a 0 tokenů. Místní zkouška nevolala Gemini. Ruční běh s živými daty využije stejný model a rozsah jako dnešní denní překlad, maximálně sedm položek a dva pokusy na položku. Přesnou spotřebu zkoušky zatím nemáme změřenou.

Místní sestavení prošlo pro 500 článků a 101 témat Kosmopedie. Prošlo všech 51 existujících testů.

## Fáze 1

Místní sestavení obou verzí potvrdilo 61 změněných stránek HTML. Po sjednocení hranic odstavců a mezer bylo HTML shodné. Adresy článků i obsah sitemap.xml jsou shodné. Prošlo 51 existujících testů. Přidaná kontrola je samostatný příkaz a nezasahuje do překladu ani publikování. Odchylka od návrhu: kontroly zatím spouštíme v režimu hlášení. Nové překlady ani výběr nepřepisují. Slovníček obsahuje návrhy k posouzení. Náklady navíc: 0 tokenů, 0 Kč. Návrat: obnovit tools/build_static.py a odebrat kontrolní skript, slovníček a report. Dříve evidované případy dne bez vhodného článku a zachování adres při opravě anglické verze zůstávají podmínkami pozdějšího zapnutí.

## Fáze 2 – stínový výběr

Samostatné workflow **Stínový výběr článků** běží na main ručně a od 13. do 26. listopadu 2026 přibližně v 9:07 pražského času. GitHub může plánovaný běh zpozdit. V obou větvích porovnání se použije jedna verze historie a společný sběr RSS. ArXiv se dotazuje dvakrát, aby srovnávací větev zachovala skutečný limit 12 záznamů a původní zálohu RSS. Rozšířený dotaz má pojistku 100 záznamů a okno 60 hodin. Při výpadku arXiv API se zachová stávající postup opakování a využijí se dostupné RSS zdroje.

Délka abstraktu, hustota matematických zápisů a vybrané odborné výrazy snižují skóre. Důležité odborné práce tak stále mohou postoupit. Za populární kandidáty považujeme položky se srozumitelností alespoň 4 a technickou náročností nejvýše 2, kromě čistě matematických prací. Výběr upřednostňuje dosažení cílových počtů srozumitelných a pozorovacích či populárních položek. Následuje počet vybraných článků a součet jejich skóre. Limity na téma a matematické práce platí vždy. Při neúplném nebo chybném bodování se použije dosavadní výběr.

Každý běh uloží do artefaktu **selection-shadow** čitelný soubor comparison.md a úplný curation_log.json s kandidáty, skóre, rozdíly a údaji o spotřebě. Artefakty mají platnost 30 dní. Zápis do data/curation_log.json a produkční commit se řeší až při případném přepnutí. Karta má v této fázi pouze navrženého kandidáta. Kontrola českého textu před potvrzením karty patří do následného zapojení.

Předpoklad 20–40 kandidátů znamená zhruba 8–20 tisíc vstupních a 2–5 tisíc výstupních tokenů za den. Při sazbě Gemini 3.6 Flash 0,75 USD za milion vstupních a 3,75 USD za milion výstupních tokenů vychází odhad přibližně na 0,014–0,034 USD za běh, tedy asi 0,19–0,47 USD za 14 běhů před daní. Skutečná spotřeba závisí na počtu a délce podkladů. Zdroj sazeb je https://aistudio.google.com/docs/pricing#gemini-3.6-flash.

Místní simulace ověřila bodování, výpadek bodování, prázdný den a limity výběru. Živý výsledek ověří první běh v GitHub Actions. Zkoušku lze ukončit vypnutím samostatného workflow.
