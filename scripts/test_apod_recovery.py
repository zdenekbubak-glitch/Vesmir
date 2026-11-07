import ast,unittest,types,urllib.parse
from pathlib import Path
class RecoveryTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  tree=ast.parse(Path('scripts/fetch_images.py').read_text(encoding='utf-8-sig'))
  funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('alt_urls','looks_like_image')]
  cls.ns={'re':__import__('re'),'requests':types.SimpleNamespace(utils=types.SimpleNamespace(quote=urllib.parse.quote))}
  exec(compile(ast.Module(body=funcs,type_ignores=[]),'fetch_images.py','exec'),cls.ns)
 def test_exact_archived_file(self):self.assertEqual(self.ns['alt_urls']('https://apod.nasa.gov/apod/image/2609/Cocoon_Czerski_3000.jpg')[1],'https://www.astro.cz/apod_data/2026/09/Cocoon_Czerski_3000.jpg')
 def test_html_not_image(self):self.assertFalse(self.ns['looks_like_image'](b'<!DOCTYPE html>'+b'x'*100))
 def test_other_hosts(self):self.assertFalse(any('astro.cz' in u for u in self.ns['alt_urls']('https://esahubble.org/image/test.jpg')))
 def test_landing_page(self):self.assertFalse(any('astro.cz' in u for u in self.ns['alt_urls']('https://apod.nasa.gov/apod/')))
 def test_fake_host(self):self.assertFalse(any('astro.cz' in u for u in self.ns['alt_urls']('https://evil.example/apod.nasa.gov/apod/image/2609/x.jpg')))
if __name__=='__main__':unittest.main()
