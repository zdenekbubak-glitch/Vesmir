"""Newsletter text shared by the example and sending script; no network calls."""

def czech_date(day):
    months = ('ledna', 'února', 'března', 'dubna', 'května', 'června',
              'července', 'srpna', 'září', 'října', 'listopadu', 'prosince')
    return f"{day.day}. {months[day.month - 1]}"


def build_email(items, start, end):
    subject = f"Kosmologické novinky: {czech_date(start)} – {czech_date(end)} {end.year}"
    count = len(items)
    noun = "příspěvek" if count == 1 else "příspěvky" if 2 <= count <= 4 else "příspěvků"
    intro = ("Týdenní výběr pěti příspěvků, které se za uplynulý týden objevily na kosmonovinky.cz."
             if count == 5 else f"Týdenní výběr: {count} {noun} z kosmonovinky.cz.")
    parts = [intro, '']
    for index, item in enumerate(items, start=1):
        url = item.get('url') or 'https://kosmonovinky.cz/'
        parts.extend([f"## {index}. {item.get('title')}", '', item.get('summary') or '', '',
                      f"[Původní zdroj]({url})", ''])
    parts.extend(['## Pro pochopení souvislostí', '',
                  'Narazili jste na neznámý pojem? V Kosmopedii najdete srozumitelná česká vysvětlení.', '',
                  '[Otevřít Kosmopedii](https://kosmonovinky.cz/kosmopedie/)', '',
                  '[Temná hmota](https://kosmonovinky.cz/kosmopedie/co-je-temna-hmota.html) · '
                  '[Černé díry](https://kosmonovinky.cz/kosmopedie/co-je-cerna-dira-a-jak-vznika.html) · '
                  '[Gravitační vlny](https://kosmonovinky.cz/kosmopedie/co-jsou-gravitacni-vlny.html)', '',
                  'Další příspěvky: [kosmonovinky.cz](https://kosmonovinky.cz/)'])
    return subject, '\n'.join(parts)
