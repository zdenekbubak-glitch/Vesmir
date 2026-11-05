import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import submit_indexnow as m

BASE = 'https://kosmonovinky.cz'

class IndexNowTests(unittest.TestCase):
    def test_first_run_does_not_submit_old_pages(self):
        p = m.make_plan({BASE+'/':'a'}, None, BASE)
        self.assertTrue(p['baseline'])
        self.assertEqual(p['urls'], [])

    def test_only_new_changed_and_removed(self):
        old = {'version':1,'base':BASE,'pages':{BASE+'/a.html':'a',BASE+'/b.html':'b',BASE+'/gone.html':'x'}}
        p = m.make_plan({BASE+'/a.html':'a',BASE+'/b.html':'new',BASE+'/new.html':'c'},old,BASE)
        self.assertEqual(p['urls'],[BASE+'/b.html',BASE+'/gone.html',BASE+'/new.html'])

    def test_rebuild_without_changes(self):
        old = {'version':1,'base':BASE,'pages':{BASE+'/':'a'}}
        self.assertEqual(m.make_plan(old['pages'],old,BASE)['urls'],[])

    def test_corrupt_history_not_silently_reset(self):
        with self.assertRaises(ValueError):m.make_plan({}, {}, BASE)

    def test_snapshot_ignores_feed_and_lastmod(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'index.html').write_text('hello')
            (p/'sitemap.xml').write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+BASE+'/</loc><lastmod>2026-11-05</lastmod></url><url><loc>'+BASE+'/feed.xml</loc></url></urlset>')
            a=m.snapshot(p,BASE)
            (p/'sitemap.xml').write_text((p/'sitemap.xml').read_text().replace('2026-11-05','2026-11-06'))
            self.assertEqual(a,m.snapshot(p,BASE));self.assertEqual(len(a),1)

    def test_foreign_host_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'sitemap.xml').write_text('<urlset><url><loc>https://evil.example/</loc></url></urlset>')
            with self.assertRaises(ValueError):m.snapshot(p,BASE)

    def test_verify_retries_and_checks_key(self):
        expected={'version':1,'digest':'abc'}; calls=[]
        def getter(url):
            calls.append(url)
            if url.endswith('.txt'):return 200,b'correct-key'
            return 200,json.dumps(expected if len(calls)>2 else {'digest':'old'}).encode()
        m.wait_for_deployment(BASE,'correct-key',expected,getter,lambda _:None)
        self.assertEqual(len(calls),4)

    def test_no_notification_before_verified_deployment(self):
        with self.assertRaises(RuntimeError):m.wait_for_deployment(BASE,'key',{'digest':'abc'},lambda u:(200,b'bad'),lambda _:None)

    def test_payload_and_accepted_statuses(self):
        p={'urls':[BASE+'/a.html']};calls=[]
        def send(url,payload):calls.append(json.loads(payload));return 202,b''
        m.submit_plan(p,BASE,'test-key',send)
        self.assertEqual(calls[0]['urlList'],p['urls']);self.assertEqual(calls[0]['host'],'kosmonovinky.cz')

    def test_failure_does_not_advance_history(self):
        with tempfile.TemporaryDirectory() as d:
            site=Path(d);key='test-key-123';(site/'data').mkdir()
            m.write_json(site/'data/indexnow.json',{'base':BASE,'key':key});(site/(key+'.txt')).write_text(key)
            state=site/'state.json';m.write_json(state,{'old':'state'});before=state.read_bytes()
            plan=site/'plan.json';m.write_json(plan,{'base':BASE,'version':1,'pages':{},'urls':[BASE+'/a.html'],'baseline':False})
            with patch('sys.argv',['script','submit','--site-dir',d,'--state',str(state),'--plan',str(plan)]),patch.object(m,'wait_for_deployment'),patch.object(m,'submit_plan',side_effect=RuntimeError('HTTP 429')):
                with self.assertRaises(RuntimeError):m.main()
            self.assertEqual(state.read_bytes(),before)

if __name__=='__main__':unittest.main()

