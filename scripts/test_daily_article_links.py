import ast,json,tempfile,unittest,unicodedata,re
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit,parse_qs
import social_tracking as st
import generate_x_card as card
import post_bluesky as bs

class DailyArticleTests(unittest.TestCase):
 def test_all_news_match_generator(self):
  tree=ast.parse(Path('tools/build_static.py').read_text(encoding='utf8'))
  funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['slugify','id_digits']]
  main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
  unique=next(n for n in ast.walk(main) if isinstance(n,ast.FunctionDef) and n.name=='unique_slug')
  ns={'unicodedata':unicodedata,'re':re,'used_slugs':set()};exec(compile(ast.Module(body=funcs+[unique],type_ignores=[]),'generator','exec'),ns)
  news=json.loads(Path('data/news.json').read_text(encoding='utf8'))
  for item in sorted(news,key=lambda x:x.get('inserted_at') or '',reverse=True):
   expected='https://kosmonovinky.cz/clanky/'+ns['unique_slug'](item.get('title','clanek'),item.get('id'))+'.html'
   self.assertEqual(st.article_url(item,news),expected)
 def test_duplicate_slugs(self):
  a={'id':'123456789012-a','title':'Černá díra','inserted_at':'2026-11-09'};b=dict(a,id='123456789012-b',inserted_at='2026-11-08')
  self.assertTrue(st.article_url(b,[b,a]).endswith('cerna-dira-123456789012-2.html'))
 def test_same_item_as_card(self):
  day=card.datetime.now().date().isoformat()
  a={'id':'1','inserted_at':day,'lang':'en'};b={'id':'2','inserted_at':day,'lang':'cs','needs_translation':True};c={'id':'3','inserted_at':day,'lang':'cs'}
  self.assertIs(card.pick_item([a,b,c]),c)
 def test_tracking_unchanged(self):
  target='https://kosmonovinky.cz/clanky/cerna-dira-123.html'
  for source in ['x','facebook','bluesky']:
   key=st.post_key(source,'daily','2026-11-09');url=st.tracked_url(target,source,'daily',key);q=parse_qs(urlsplit(url).query)
   self.assertEqual(urlsplit(url).path,'/clanky/cerna-dira-123.html')
   self.assertEqual(q,{'utm_source':[source],'utm_medium':['social'],'utm_campaign':['kosmonovinky'],'utm_content':[key],'utm_term':['daily']})
 def test_bluesky_facet_and_length(self):
  item={'title':'Černé díry a hvězdy '*30,'summary':'Žhavý vesmír '*80};target='https://kosmonovinky.cz/clanky/test-123.html'
  text,facets=bs.compose(item,target,'2026-11-09');self.assertLessEqual(len(text),300)
  f=facets[0];self.assertEqual(text.encode()[f['index']['byteStart']:f['index']['byteEnd']].decode(),bs.SITE_URL)
  self.assertTrue(f['features'][0]['uri'].startswith(target+'?'));self.assertIn(st.post_key('bluesky','daily','2026-11-09'),f['features'][0]['uri'])
 def test_receipt_target(self):
  with tempfile.TemporaryDirectory() as d,patch.object(st,'SPOOL',Path(d)/'spool'),patch.object(st,'recheck_pending'):
   st.receipt('x','daily','key','title','id','published',target='https://kosmonovinky.cz/clanky/a.html')
   self.assertEqual(json.loads(st.SPOOL.read_text(encoding='utf8'))['target'],'https://kosmonovinky.cz/clanky/a.html')
 def test_existing_bluesky_no_duplicate(self):
  old={'value':{'facets':[{'features':[{'uri':'https://kosmonovinky.cz/?utm_source=bluesky'}]}]}}
  with patch.object(bs,'api',return_value={'did':'did:test','accessJwt':'token','didDoc':{'service':[{'id':'#atproto_pds','serviceEndpoint':'https://pds.example'}]}}),patch.object(bs,'get_existing',return_value=old),patch.object(bs,'confirm_publication') as confirm,patch.object(bs,'prepare_image') as upload:
   bs.publish({'title':'t'},Path('none'),'2026-11-09','handle','password','https://kosmonovinky.cz/clanky/new.html')
   upload.assert_not_called();self.assertEqual(confirm.call_args.args[-1],'https://kosmonovinky.cz/')

if __name__=='__main__':unittest.main()
