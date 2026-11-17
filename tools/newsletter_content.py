"""Newsletter text shared by the example and sending script; no network calls."""

def czech_date(day):
    months = ('ledna', 'února', 'března', 'dubna', 'května', 'června',
              'července', 'srpna', 'září', 'října', 'listopadu', 'prosince')
    return f"{day.day}. {months[day.month - 1]}"


def build_email(items, start, end, *, total_count=None):
    subject = f"Kosmologické novinky: {czech_date(start)} – {czech_date(end)} {end.year}"
    count = len(items)
    noun = "příspěvek" if count == 1 else "příspěvky" if 2 <= count <= 4 else "příspěvků"
    intro = ("Týdenní výběr pěti příspěvků, které se za uplynulý týden objevily na kosmonovinky.cz."
             if count == 5 else f"Týdenní výběr: {count} {noun} z kosmonovinky.cz.")
    parts = [intro, '']
    for index, item in enumerate(items, start=1):
        url = item.get('_newsletter_url')
        if not url:
            path = item.get('_path')
            url = 'https://kosmonovinky.cz/' + path if path else 'https://kosmonovinky.cz/clanky/'
        parts.extend([f"## {index}. {item.get('title')}", '', item.get('summary') or '', '',
                      f"[Článek na Kosmonovinky.cz]({url})", ''])
    if total_count is not None and total_count > count:
        noun = "články" if 2 <= total_count <= 4 else "článků"
        parts.extend(['**Další čtení na Kosmonovinky.cz**', '',
                      f'Za stejné období přibylo na webu celkem {total_count} {noun}. '
                      'Newsletter přináší výběr; další kosmologická témata najdete v přehledu článků.', ''])
    else:
        parts.extend(['**Další čtení na Kosmonovinky.cz**', '',
                      'Další články o kosmologii a nové příspěvky najdete na našem webu.', ''])
    parts.extend(['**[Prohlédnout všechny články →](https://kosmonovinky.cz/clanky/)**', '',
                  '**Kosmopedie · pro pochopení souvislostí**', '',
                  'Srozumitelná vysvětlení pojmů z článků najdete v '
                  '[Kosmopedii](https://kosmonovinky.cz/kosmopedie/).', '',
                  '[Temná hmota](https://kosmonovinky.cz/kosmopedie/co-je-temna-hmota.html) · '
                  '[Černé díry](https://kosmonovinky.cz/kosmopedie/co-je-cerna-dira-a-jak-vznika.html) · '
                  '[Gravitační vlny](https://kosmonovinky.cz/kosmopedie/co-jsou-gravitacni-vlny.html)', '',
                  'Týdenní výběr připravují **Kosmonovinky.cz**.'])
    return subject, '\n'.join(parts)
