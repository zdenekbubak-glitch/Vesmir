"""Offline regression checks: python tools/test_article_images.py"""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from assign_article_images import prepare, key_for, source_identity, candidates_for


class AssignmentTests(unittest.TestCase):
    def fixture(self, catalog, news, assignments=None):
        temp=tempfile.TemporaryDirectory(prefix='image-test-',dir=Path.cwd());self.addCleanup(temp.cleanup)
        site=Path(temp.name);(site/'data').mkdir();folder=site/'assets/article-images';folder.mkdir(parents=True)
        for name,data in [('article_image_catalog',catalog),('news',news),('explainery',[]),('article_image_assignments',assignments or {})]:
            (site/'data'/(name+'.json')).write_text(json.dumps(data),encoding='utf-8')
        for e in catalog: (folder/(e['id']+'.jpg')).touch()
        return site

    def catalog(self,topic='temna-hmota',count=8):
        return [dict(id=topic+str(i),topic=topic,source_id=topic+str(i)) for i in range(count)]

    def news(self,count=24,title='Temná hmota'):
        return [dict(id=str(i),title=title,inserted_at=f'2026-01-{i+1:02d}T12:00:00Z') for i in range(count)]

    def test_recent_five_per_topic_and_lru(self):
        catalog=self.catalog()+self.catalog('cerne-diry')
        news=self.news()+[dict(id='bh'+str(i),title='Černé díry',inserted_at=f'2026-01-{i+1:02d}T11:00:00Z') for i in range(24)]
        site=self.fixture(catalog,news);cache,by_id=prepare(site,False)
        for title in ('Temná hmota','Černé díry'):
            history=[];last={}
            for item in sorted((e for e in news if e['title']==title),key=lambda e:e['inserted_at']):
                chosen=by_id[cache[key_for(item,'news')]];identity=source_identity(chosen)
                pool=candidates_for(item,catalog)
                self.assertNotIn(identity,history[-5:])
                fresh=[e for e in pool if source_identity(e) not in history[-5:]]
                self.assertEqual(last.get(identity,-1),min(last.get(source_identity(e),-1) for e in fresh))
                last[identity]=len(history);history.append(identity)

    def test_stability_with_new_and_backdated_articles_and_title_edit(self):
        site=self.fixture(self.catalog(),self.news(10));before,_=prepare(site,False)
        news=self.news(10);news[0]['title']='Upravený titulek článku'
        news += [dict(id='new',title='Temná hmota',inserted_at='2026-12-01'),dict(id='backdated',title='Temná hmota',inserted_at='2025-01-01')]
        (site/'data/news.json').write_text(json.dumps(news),encoding='utf-8')
        after,_=prepare(site,False)
        self.assertTrue(all(after[k]==v for k,v in before.items()))
        self.assertEqual(after,prepare(site,False)[0])

    def test_duplicate_pixels_are_one_source(self):
        catalog=self.catalog();catalog[1]['source_pixel_sha256']='same';catalog[0]['source_pixel_sha256']='same'
        site=self.fixture(catalog,self.news(20));cache,by_id=prepare(site,False)
        sequence=[source_identity(by_id[cache[key_for(e,'news')]]) for e in self.news(20)]
        for i,identity in enumerate(sequence): self.assertNotIn(identity,sequence[max(0,i-5):i])

    def test_subtopic_beats_variety_and_small_pool_is_allowed(self):
        catalog=self.catalog();catalog[0]['subtopics']=['particles','detectors'];catalog[1]['subtopics']=['particles','detectors']
        for e in catalog[2:]: e['subtopics']=['general','clusters']
        news=self.news(12,'Temná hmota v detektoru LUX-ZEPLIN')
        site=self.fixture(catalog,news);cache,_=prepare(site,False)
        self.assertEqual(set(cache.values()),{catalog[0]['id'],catalog[1]['id']})

    def test_missing_cached_asset_fails_without_reassignment(self):
        site=self.fixture(self.catalog(),self.news(3));before,_=prepare(site,False)
        (site/'assets/article-images'/(next(iter(before.values()))+'.jpg')).unlink()
        with self.assertRaises(RuntimeError): prepare(site,False)
        self.assertEqual(before,json.loads((site/'data/article_image_assignments.json').read_text()))


if __name__=='__main__': unittest.main()
