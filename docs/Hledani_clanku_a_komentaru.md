# Sjednocené hledání v Novinkách a Přehledu článků

Nahrajte všech 5 souborů z balíčku do původních cest. Generované HTML přehledu článků ani vyhledávací JSON se ručně nenahrávají: vzniknou při standardním sestavení webu.

- Vyhledávání je na obou stránkách nad příspěvky a zahrnuje celé texty všech vydaných komentářů Pohledem editora.
- Novinky nadále prohledávají novinky zobrazené na dané stránce (aktuální a předchozí měsíc), Přehled článků všechny články. Počty rozlišují zprávy a komentáře.
- Na Novinkách je bez dotazu vidět jen nejnovější komentář; při hledání se mohou objevit i starší. Komentáře bez shody se skryjí.
- Shoda v titulku nebo perexu se zvýrazní, shoda až uvnitř komentáře dostane krátký úryvek. Hledání ignoruje velikost písmen a diakritiku.
- Smazání dotazu, křížek nebo Escape obnoví původní přehled. Domovská stránka zachovává parametr q pro sdílení hledání.
- Nezveřejněné a budoucí komentáře se nevkládají ani do vyhledávacího indexu, ani do pomocných karet. Stávající datumové pravidlo zůstává zachováno.
- Při nedostupnosti fulltextového indexu zůstane hledání v titulcích a perexech a zobrazí se vysvětlení. Žádné nesouvisející připnuté komentáře se nevynucují.
- Obě stránky používají assets/article-search.js s verzovanou adresou kvůli mezipaměti.

Ověřeno v prohlížeči na 1280/390/320 px: starší komentář se shodou jen uvnitř textu, žádná shoda, hledání bez diakritiky, Escape, návrat nejnovějšího komentáře a vyloučení budoucího vydání.
