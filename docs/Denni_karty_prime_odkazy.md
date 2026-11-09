# Denní karty: odkaz přímo na představovaný článek

Nahrajte všech 5 souborů balíčku do původních cest, nejlépe jedním commitem. Workflow daily-cosmo.yml patří do .github/workflows/. Není třeba nastavovat další Secrets.

- X: druhý příspěvek denního vlákna odkazuje na konkrétní článek, ne na hlavní stránku.
- Facebook: odkaz pod textem denního příspěvku vede na stejný konkrétní článek.
- Bluesky: klikací odkaz zobrazený jako https://kosmonovinky.cz nyní vede přes svou odkazovou anotaci na daný článek. Krátký viditelný text je zachován kvůli limitu 300 znaků; úplná cílová adresa je ve facet URI. Režim --dry-run vypíše také cílový článek.
- Všechny sítě zachovávají utm_source, utm_medium=social, utm_campaign=kosmonovinky, původní utm_content identifikátor příspěvku a utm_term=daily.
- Evidence nových denních příspěvků ukládá jako target adresu konkrétního článku. Historická data se nepřepisují.
- X a Facebook nově vybírají položku stejnou funkcí pick_item jako generátor karty; tím se předchází odkazování na jiný článek při neúplných překladech. Bluesky používá tutéž funkci.
- Adresa článku respektuje české názvy, nejvýše 10 slov, číselný identifikátor i přípony při shodných názvech podle současného build_static.py.
- Denní klíče Bluesky i UTM identifikátory zůstávají stejné. Opakování běhu nevytváří kvůli této změně další příspěvek a již existující příspěvek se neupravuje.
- Pořadí nasazení, IndexNow, ověřování aktuálního obrázku z CDN a zpracování chyb zůstávají zachované. X má nadále svůj existující krok před nasazením webu; nově vytvořený článek bude dostupný po dokončení následujícího nasazení v témže běhu.
- Vzhled daily.jpg, týdenní výběry LinkedIn a ostatní ručně posuzované posty se nemění. Žádná další AI volání.

Kontrola: příští nový denní příspěvek na každé síti otevřít a ověřit, že odkaz vede přímo na článek shodný s kartou. Starší již vydané posty se touto změnou zpětně nemění.

Testy: python -m unittest discover -s scripts -p test_daily_article_links.py -v
Ověřeno také offline spuštěním obou skutečných Buffer kroků s náhradním API; během přípravy nebylo nic zveřejněno. Doporučené vyhodnocení výsledků 23. 11. 2026.
