# Kosmopedie – předání 8. várky

Finální balíček po kontrole autora, 27. 10. 2026. Všechny schválené připomínky zapracovány. Předloha: aktuální větev `main` repozitáře https://github.com/zdenekbubak-glitch/Vesmir . Před závěrečnými úpravami znovu ověřena shoda všech pěti upravovaných souborů s výchozí verzí na GitHubu.

Zapracováno: oba odstavce závěru Plancku; vysvětlení společných deformací obrazů u Euclidu; zkrácení popisku DESI; označování „téma“ místo „heslo“ v nových textech; vysvětlení rudého posuvu; přepracování BAO včetně nadpisu, popisu a výpočtu skutečné velikosti charakteristického rozestupu; vysvětlení Čerenkovova světla a rekonstrukce směru příletu neutrina; srozumitelná návaznost omezení částicových kandidátů temné hmoty.

## Obsah

- exp-060: Co změřila družice Planck?
- exp-061: Co zkoumá kosmický dalekohled Euclid?
- exp-062: Co je DESI a jak mapuje rozpínání vesmíru?
- exp-063: Jak fungují detektory neutrin a co nám odhalují?
- exp-064: Jak experimenty hledají částice temné hmoty?

Všech pět hesel je ve stávajícím okruhu **Teleskopy a observatoře**. Navazují na předchozí strukturu: titulek, popis, datum, perex, členěný výklad, zdroje, související zprávy a odkazy do Kosmopedie, závěrečný vysvětlující rámeček. U DESI a xenonového detektoru je druhý obrázek uvnitř výkladu.

## Co nahrát

ZIP má cesty vůči kořeni repozitáře. Nahrajte všechny jeho soubory při zachování složek.

- `data/explainery.json`: úplný souhrnný JSON, původních 59 hesel zachováno, přidáno pět nových.
- `data/article_image_catalog.json`: přidány pouze čtyři nové obrazové zdroje s kredity a právy použití.
- `data/article_image_assignments.json`: pět pevných přiřazení pro nová hesla; původní přiřazení zachována.
- `data/kosmopedie_images.json`: doplnění tematické galerie a hledacích označení.
- `assets/article-images/`: čtyři nové webové obrázky, zdrojové zmenšeniny, náhledy a jejich renderovací otisky. Stávající schémata nejsou v ZIPu znovu přibalena.
- `docs/Kosmopedie_plan_varek_6-9.md`: aktualizovaný stav osmé várky; devátá várka ponechána pro částicové principy.
- tento dokument.

Kód generátorů, workflow, skripty a requirements nebyly měněny. Oprava českého řazení z GitHubu zůstává zachována. Generované HTML se nenahrává; vytvoří je stávající sestavení webu.

## Nové obrazové zdroje

| Obraz | Zdroj | Podmínky |
| --- | --- | --- |
| Planck Legacy CMB 2018 | https://www.esa.int/ESA_Multimedia/Images/2018/07/Planck_s_view_of_the_cosmic_microwave_background2 | ESA Standard Licence, vzdělávací a informační použití; ESA/Planck Collaboration. |
| Euclid: kupa Perseus | https://www.esa.int/ESA_Multimedia/Images/2023/11/Euclid_s_view_of_the_Perseus_cluster_of_galaxies | CC BY-SA 3.0 IGO; zachován úplný kredit i licence odvozených zmenšenin. |
| Kopule Mayallova dalekohledu / DESI | https://noirlab.edu/public/images/noirlab2512g/ | CC BY 4.0 podle galerie NOIRLab; úplný kredit konkrétního snímku. |
| Povrchová laboratoř IceCube | https://www.usgs.gov/media/images/icecube-lab-southpolejpg | Public domain podle konkrétní stránky USGS. |

Ověřeny popisy, typy obrazů a konkrétní podmínky; součástí katalogu jsou zdrojové odkazy, alt texty, popisky, licence, úpravy a SHA-256. Obrázky nejsou ořezány. Mapa CMB, barevná kompozice Euclidu a skutečné fotografie jsou označeny podle svého typu. Obrázky s jinými či nejasnými podmínkami z galerií DESI, INFN a IceCube nebyly do balíčku převzaty.

## Ověření

- Úspěšně spuštěny oba stávající generátory; 402 zpráv a 64 hesel Kosmopedie.
- Datové porovnání s předlohou potvrdilo zachování všech 59 původních hesel, celého původního obrazového katalogu a všech původních přiřazení.
- Ověřeny všechny interní odkazy a obrázky na pěti nových stránkách, související hesla, záznamy hledání i začlenění použitých obrázků do galerie.
- Prohlížeč Chrome: všech pět detailů ve šířkách 1280 a 390 px; bez chyb skriptů, chybějících lokálních prostředků a vodorovného přetékání. Ověřeno načtení všech použitých obrazů a zvětšovací odkazy druhých obrázků.
- Odborný text vychází z primárních zdrojů odkazovaných u každého hesla. U aktuálních náznaků DESI a neobvyklé události LZ je rozlišena interpretace, nejistota a potvrzený objev. Neutrinové pozadí raného vesmíru není vydáváno za přímo změřené IceCube či Super-Kamiokande.

Jde o připravené soubory; z této relace nebyly odeslány na GitHub ani zveřejněny na webu.
