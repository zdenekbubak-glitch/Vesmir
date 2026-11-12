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
