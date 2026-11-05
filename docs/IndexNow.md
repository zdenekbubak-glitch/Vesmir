# IndexNow pro Kosmonovinky

## Nasazení
Nahrajte všechny soubory z balíčku do původních cest, nejlépe v jednom commitu.
Není třeba vytvářet GitHub Secret ani nic měnit v Bing Webmaster Tools.
Ověřovací soubor .txt patří do kořene repozitáře. Jeho obsah ani název neměňte.
Po nahrání počkejte na úspěšné dokončení Deploy to GitHub Pages.

## Chování
- Zapojeno do pages.yml a daily-cosmo.yml, až po úspěšném nasazení.
- První běh ověří veřejný klíč a uloží výchozí stav. Starší stránky hromadně neposílá.
- Další běhy porovnávají kontrolní součty HTML stránek ze sitemap. Nové, změněné a odstraněné adresy odešlou na api.indexnow.org; samotná změna lastmod nestačí.
- Oznamují se také skutečné změny v přehledech a souvisejících odkazech. Neodesílá se RSS, obrázkové soubory ani budoucí nevydané příspěvky mimo sitemap.
- Před odesláním se ověří veřejný indexnow-deployment.json odpovídající aktuálnímu sestavení a obsah souboru klíče. Oznámení neodchází před dostupností nového nasazení.
- Historie se uchovává ve společné GitHub Actions cache obou workflow, nikoliv v repozitáři ani veřejném webu.
- Pokud odeslání selže, historie se neposune; další běh změny znovu zkusí. Kroky mají continue-on-error, takže nezastaví další sociální kroky ani nezneplatní nasazení.
- Pokud GitHub po dlouhé neaktivitě cache odstraní, další běh bezpečně založí nový výchozí stav bez hromadného odesílání historie.
- První běh ještě nevytvoří aktivitu odesílání v panelu IndexNow. Ta se objeví až při následné skutečné změně obsahu.
- Opravy překladů mají samostatná starší workflow. IndexNow zde není přidáno; jejich změny oznámí následující běžné nebo denní nasazení.

HTTP 200/202 potvrzuje přijetí oznámení, nikoliv zařazení do indexu. Požadavek podpory Bingu REQ00393753 zůstává důležitý.

## Kontrola
V Actions hledat Prepare IndexNow changes, Notify IndexNow after deployment a Save IndexNow history.
Testy: python3 -m unittest discover -s scripts -p test_indexnow.py -v
Skript používá pouze standardní knihovnu Pythonu. Nepřidává žádná AI volání ani platby.
Dokumentace: https://www.indexnow.org/documentation
