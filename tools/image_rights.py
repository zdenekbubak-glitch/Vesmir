"""Verified image attribution, shared by importers and JSON-LD generators.

Credit and copyright are distinct. Never turn a publisher, editor, generic
NASA/APOD label, unknown photographer or web footer into an image owner.
"""
import html
import re
from urllib.parse import urlsplit

RIGHTS_FIELDS = ('creator', 'copyrightNotice', 'acquireLicensePage')

def clean_text(value):
    text = html.unescape(str(value or ''))
    return ' '.join(re.sub(r'<[^>]+>', ' ', text).split())


def creator_entity(name):
    name = clean_text(name)
    if not name or re.search(r'unknown|neznám|neuveden|unbekannt|o\.ang\.|^NASA\s*/\s*APOD$', name, re.I):
        return None
    # A joint credit may describe a collaboration, not one individual.
    group = re.search(r'NASA|ESA|ESO|NSF|NOIRLab|AURA|USGS|EHT|ETH|STScI|DLR|JPL|Observ|Collaboration|Consortium|Team|Survey|Foundation|Laborator|University|Institute|Service|White House|Lagrelius|[,&;/]| et al\.', name, re.I)
    return {'@type': 'Organization' if group else 'Person', 'name': name}


def apply_rights(entry, fields):
    """Fill gaps only; verified hand-edited records always win."""
    for key in RIGHTS_FIELDS:
        if fields.get(key) and not entry.get(key):
            entry[key] = fields[key]
    return entry


def image_rights(entry, base='https://kosmonovinky.cz'):
    result = {key: entry[key] for key in RIGHTS_FIELDS if entry.get(key)}
    if entry.get('generated') is True and str(entry.get('source_id', '')).startswith('own-diagram:'):
        result.setdefault('creator', {'@type': 'Organization', 'name': 'Kosmologické novinky', 'url': base.rstrip('/') + '/'})
        result.setdefault('copyrightNotice', 'Kosmologické novinky')
    return result


def source_metadata(page, url):
    """Read image-specific source fields, never general article author/footer.

    NASA's APOD landing page changes daily: do not use a redirected landing
    page as evidence for a historical image.
    """
    parsed = urlsplit(url)
    host = (parsed.hostname or '').lower()
    if host == 'science.nasa.gov' and '/image-article/apod-' in parsed.path:
        for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>', page, re.S | re.I):
            cells = re.findall(r'<t[hd]\b[^>]*>(.*?)</t[hd]>', row, re.S | re.I)
            if len(cells) != 2:
                continue
            label, value = map(clean_text, cells)
            if not re.search(r'credit', label, re.I) or not value:
                continue
            result = {'credit': value}
            creator = creator_entity(re.sub(r'^Image Credit:\s*', '', value, flags=re.I))
            if creator:
                result['creator'] = creator
            if 'copyright' in label.lower():
                result['copyrightNotice'] = value
            result['rights_metadata_source'] = url
            return result
    if host in ('www.eso.org', 'eso.org', 'esahubble.org', 'esawebb.org', 'noirlab.edu') and '/images/' in parsed.path:
        match = re.search(r'<div\b[^>]*class=["\'][^"\']*\bcredit\b[^"\']*["\'][^>]*>(.*?)</div>', page, re.S | re.I)
        if match:
            credit = clean_text(match[1])
            # Keep acknowledgements in the visible credit; they are not authors.
            byline = re.split(r'\bAcknowledg(?:e)?ments?:', credit, maxsplit=1, flags=re.I)[0].strip(' .;')
            result = {'credit': credit, 'rights_metadata_source': url}
            creator = creator_entity(byline)
            if creator:
                result['creator'] = creator
            return result
    return {}
