# Autor a autorská práva u obrázků

`tools/image_rights.py` sjednocuje ověřené údaje pro články, Kosmopedii, Pohledem editora a galerii. Generátory předávají `creator`, `copyrightNotice` a `acquireLicensePage`, pokud jsou vyplněné. U našich vlastních schémat zůstává bezpečné doplnění Kosmologických novinek. Metadata třetích stran se neodvozují automaticky z názvu vydavatele.

## Nové denní obrázky

`scripts/fetch_images.py` před uložením nového snímku zkusí přečíst jeho konkrétní oficiální stránku. Řádek NASA „Credit & Copyright“ dovoluje doplnit obě pole. Řádek „Credit“ dokládá autorství, ale sám nedokládá držitele práv. Import odděluje fotografy od autorů a editorů doprovodného textu a od obecné patičky webu. Kredit se již nezkracuje na160 znaků a dekódují se HTML entity.

Získání metadat je nezávislé na AI. Při nedostupnosti zdroje se zapíše upozornění a běh pokračuje. Starý odkaz APOD přesměrovaný na denně proměnlivou hlavní stránku se pro metadata historického obrázku nepoužije. Existující ručně zadaný autor a údaj o právech mají přednost.

## Další ručně přidávané obrázky

Do `data/article_image_catalog.json` doplňte přesně doložené hodnoty: `creator` jako objekt Person/Organization nebo seznam takových objektů, `copyrightNotice` jako původní údaj o právech. Přidejte `rights_metadata_source` a datum `rights_verified_on`. Používejte konkrétní stránku obrázku, nikoli obecné autory článku. Pokud je fotograf neznámý nebo zdroj neuvádí vlastníka práv, příslušné pole zůstává prázdné. Nepřipisujte všechna díla NASA ani Kosmologickým novinkám a nepřevádějte je automaticky na CC BY.

Samostatné oznámení o public domain vychází z licenčního záznamu zdroje a neoznačuje nového vlastníka. Odkaz na zdroj zachovává podrobné podmínky.

## Ověření

Spusťte `python tools/test_image_rights.py` a `python tools/test_article_images.py`, poté běžné generování webu. Devět testů metadat ověřuje především falešné přiřazení copyrightu z pouhého kreditu, záměnu za textového editora, přesměrování historického APOD, zachování ověřených hodnot a nezkrácený kredit.

K 4. 11. 2026 obsahuje katalog 242 obrázků: autor je doložen u 235 a údaj o právech u 181. Denní galerie 61 snímků: autor u41, údaj o právech u23. Ne všechna nepovinná upozornění Googlu lze odstranit pravdivými údaji; neznámé hodnoty se nevymýšlejí.
