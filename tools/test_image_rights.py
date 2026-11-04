"""Offline checks: python tools/test_image_rights.py"""
import ast
import copy
import json
from pathlib import Path
import unittest
from image_rights import source_metadata, image_rights, apply_rights
from assign_article_images import image_schema, gallery_image_schema

ROOT = Path(__file__).resolve().parents[1]
NASA = 'https://science.nasa.gov/image-article/apod-2026-november-4-example/'

def row(label, name):
    return '<table><tr><th>' + label + '</th><td>' + name + '</td></tr></table>'

class RightsTests(unittest.TestCase):
    def test_explicit_copyright_and_entities(self):
        fields = source_metadata(row('Credit &amp; Copyright:', '<a>Alice &amp; Bob</a>'), NASA)
        self.assertEqual('Alice & Bob', fields['credit'])
        self.assertEqual('Alice & Bob', fields['copyrightNotice'])
        self.assertEqual('Alice & Bob', fields['creator']['name'])

    def test_credit_is_not_ownership(self):
        fields = source_metadata(row('Credit:', 'NASA, ESA'), NASA)
        self.assertIn('creator', fields)
        self.assertNotIn('copyrightNotice', fields)

    def test_skip_editor_and_footer(self):
        page = row('Authors & editors:', 'Editor name') + '<footer>Copyright Publisher</footer>'
        self.assertEqual({}, source_metadata(page, NASA))

    def test_redirect_to_daily_homepage_is_not_historical_evidence(self):
        self.assertEqual({}, source_metadata(row('Credit & Copyright:', 'Todays author'), 'https://science.nasa.gov/apod/'))
        self.assertEqual({}, source_metadata(row('Credit & Copyright:', 'Unknown'), 'https://example.com/image'))

    def test_unknown_creator_is_not_invented(self):
        fields = source_metadata(row('Credit:', 'Unknown photographer'), NASA)
        self.assertNotIn('creator', fields)
        fields = source_metadata(row('Credit:', 'NASA / APOD'), NASA)
        self.assertNotIn('creator', fields)

    def test_verified_values_are_preserved(self):
        entry = {'creator': {'@type':'Person', 'name':'Verified author'}, 'copyrightNotice':'Verified owner'}
        original = copy.deepcopy(entry)
        apply_rights(entry, {'creator': {'name':'New name'}, 'copyrightNotice':'New owner'})
        self.assertEqual(original, entry)

    def test_own_diagram_fallback_and_gallery_agree(self):
        entry = {'id':'test','generated':True,'source_id':'own-diagram:test'}
        self.assertEqual('Kosmologické novinky', image_rights(entry)['copyrightNotice'])
        self.assertEqual(image_rights(entry), {k:v for k,v in gallery_image_schema(entry,'https://kosmonovinky.cz','/test.jpg').items() if k in ('creator','copyrightNotice')})

    def test_schemas_export_known_metadata_without_touching_licenses(self):
        cat = json.loads((ROOT/'data/article_image_catalog.json').read_text(encoding='utf8'))
        for entry in cat:
            data = image_schema(entry, 'https://kosmonovinky.cz')
            for field in ('creator','copyrightNotice'):
                if entry.get(field): self.assertEqual(entry[field],data[field])
            self.assertEqual(entry['license_url'], data['license'])
        for entry in json.loads((ROOT/'data/images.json').read_text(encoding='utf8')):
            data=gallery_image_schema(entry,'https://kosmonovinky.cz',entry.get('image'))
            for field in ('creator','copyrightNotice'):
                if entry.get(field): self.assertEqual(entry[field],data[field])

    def test_source_credit_does_not_get_truncated(self):
        name = 'A named contributor; ' * 25
        fields=source_metadata(row('Credit & Copyright:',name),NASA)
        self.assertGreater(len(fields['credit']),160)
        tree=ast.parse((ROOT/'scripts/fetch_images.py').read_text(encoding='utf8'))
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='enrich_source_metadata')
        class Response:
            text=row('Credit & Copyright:',name)
            url=NASA
            def raise_for_status(self): pass
        class Session:
            def get(self,*args,**kwargs): return Response()
        context={'SESSION':Session(),'source_metadata':source_metadata,'apply_rights':apply_rights}
        exec(compile(ast.Module(body=[function],type_ignores=[]),'<importer>','exec'),context)
        item=context['enrich_source_metadata']({'id':'sample','url':NASA,'credit':'Short'})
        self.assertEqual(name.strip(),item['credit'])
        self.assertEqual(name.strip(),item['copyrightNotice'])

if __name__=='__main__': unittest.main()
