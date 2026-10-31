"""Regression checks for Czech topic matching; no network calls or publication."""
import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import build_static as site

ROOT = Path(__file__).resolve().parents[1]
CATALOG = site.explainer_catalog(ROOT)

def selected(text, *, summary='', limit=2):
    return {entry['id'] for entry in site.related_explainers({'title': text, 'summary': summary}, CATALOG, limit=limit)}

class ExplainerMatchingTests(unittest.TestCase):
    def test_all_topics_have_rules(self):
        self.assertEqual({e['id'] for e in CATALOG}, set(site.EXPLAINER_PATTERNS))

    def test_czech_black_hole_cases(self):
        for phrase in ['černá díra','černé díry','černé díře','černou díru','černá díro','černou dírou',
                       'černých děr','černým dírám','černých dírách','černými dírami','ČERNÝCH DĚR',
                       'cernych der','černých\n  děr','černých\u00a0děr','černá–díra','černých děr']:
            with self.subTest(phrase=phrase):
                self.assertIn('exp-005',selected(phrase))
                self.assertIn('exp-005',selected('Výsledky výzkumu',summary='Výpočty se týkají '+phrase+'.'))

    def test_real_missing_article(self):
        news=json.loads((ROOT/'data/news.json').read_text(encoding='utf8'))
        article=next(n for n in news if str(n['id'])=='2610.40514v1')
        self.assertIn('exp-005',{e['id'] for e in site.related_explainers(article,CATALOG)})

    def test_other_czech_cases(self):
        cases={'O temné hmotě':'exp-001','S gravitačními vlnami':'exp-002','O neutronových hvězdách':'exp-008',
               'U horizontu událostí':'exp-006','Bez temné energie':'exp-004','S rudými posuvy':'exp-038','Radioteleskopy':'exp-028','Mřížková teorie pole':'exp-045',
               'O spektrálních čarách':'exp-036','S Hubbleovou konstantou':'exp-025',
               'Splynutí galaxií':'exp-024','Sloučení galaxií':'exp-024','Srážkami galaxií':'exp-024',
               'O Maxi Planckovi':'exp-085','O Nielsi Bohrovi':'exp-086','O Werneru Heisenbergovi':'exp-088',
               'S Albertem Einsteinem':'exp-070','S Alexandrem Friedmannem':'exp-071'}
        for phrase,identity in cases.items():
            with self.subTest(phrase=phrase):self.assertIn(identity,selected(phrase))

    def test_newly_covered_topics(self):
        cases={'Výsledky družice Planck':'exp-060','Data z Euclidu':'exp-061','Přehlídka DESI':'exp-062',
               'Neutrinové detektory IceCube':'exp-063','Experiment LUX-ZEPLIN':'exp-064',
               'Spektrální třídy hvězd':'exp-095','Víceplanetové soustavy':'exp-096','Horkými Jupitery':'exp-097',
               'Budoucnost Slunce':'exp-098','Nejbližší hvězdy':'exp-099','Slunce v Mléčné dráze':'exp-100',
               'Velký Magellanův oblak':'exp-101','Magellanových oblaků':'exp-101'}
        for phrase,identity in cases.items():
            with self.subTest(phrase=phrase):self.assertIn(identity,selected(phrase))

    def test_requested_curvature_phrases(self):
        self.assertIn('exp-078',selected('Geometrie zakřiveného vesmíru'))
        self.assertIn('exp-078',selected('Zakřivení prostoročasu'))
        self.assertIn('exp-078',selected('Zakřivení časoprostoru'))
        self.assertNotIn('exp-078',selected('Zakřivené prostory'))

    def test_word_boundaries_and_ambiguous_names(self):
        for text in ['Černé direktivy firmy','Černých derivací','Ekonomická inflace roste','Nová budova laboratoře',
                     'Zakřivení plochy v materiálu']:
            with self.subTest(text=text):self.assertEqual(set(),selected(text))
        self.assertNotIn('exp-061',selected('Euclidean geometry and spheres'))
        self.assertNotIn('exp-032',selected('Modified gravity'))
        self.assertIn('exp-032',selected('Interferometr GRAVITY'))
        self.assertNotIn('exp-060',selected('Planckova konstanta'))
        self.assertIn('exp-085',selected('Planckova konstanta'))

    def test_ranking_still_prefers_headline(self):
        self.assertEqual('exp-005',site.related_explainers({'title':'Černých děr přibývá','summary':'Rozbor temné hmoty a Higgsova pole.'},CATALOG)[0]['id'])
        self.assertLessEqual(len(selected('Černé díry, temná hmota, gravitační vlny')),2)

    def test_future_missing_rule_is_reported(self):
        output=io.StringIO()
        with patch.object(site.json,'loads',return_value=[{'id':'exp-999','title':'Nové téma'}]),contextlib.redirect_stdout(output):
            site.explainer_catalog(ROOT)
        self.assertIn('exp-999',output.getvalue())

class ReverseLinkTests(unittest.TestCase):
    def test_topic_in_other_category(self):
        article = {'id':'a','title':'Vývoj supermasivních černých děr','_theme':'cerne-diry'}
        self.assertEqual([article],site.related_news_for_explainer({'id':'exp-018','theme':'temna-dira-v-centru'},[article]))

    def test_same_category_is_not_enough(self):
        self.assertEqual([],site.related_news_for_explainer({'id':'exp-018'},[{'id':'a','title':'Malé černé díry','_theme':'temna-dira-v-centru'}]))

    def test_reverse_is_not_limited_by_two_outgoing_links(self):
        article={'id':'a','title':'Temná hmota a gravitační vlny','summary':'Také supermasivní černé díry.'}
        self.assertNotIn('exp-018',selected(article['title'],summary=article['summary']))
        self.assertEqual([article],site.related_news_for_explainer({'id':'exp-018'},[article]))

    def test_editorial_choices_and_explicit_disable_are_preserved(self):
        news=[{'id':'a'},{'id':'b'}]
        self.assertEqual([news[1],news[0]],site.related_news_for_explainer({'id':'exp-018','related_news':['b','a']},news))
        self.assertEqual([],site.related_news_for_explainer({'id':'exp-018','disable_related_news':True},news))
        match={'id':'c','title':'Supermasivní černé díry'}
        self.assertEqual([match],site.related_news_for_explainer({'id':'exp-018','related_news':[]},[match]))
        with self.assertRaises(ValueError):site.related_news_for_explainer({'id':'exp-018','related_news':['missing']},news)

    def test_relevance_then_recency_and_limit(self):
        news=[{'id':'older','title':'Supermasivní černé díry','inserted_at':'2025-01-01'},
              {'id':'newer','title':'Supermasivní černé díry','inserted_at':'2026-01-01'},
              {'id':'body','title':'Výzkum','summary':'Supermasivní černé díry','inserted_at':'2026-02-01'}]
        self.assertEqual(['newer','older'],[n['id'] for n in site.related_news_for_explainer({'id':'exp-018'},news,limit=2)])

    def test_real_catalog_matches_and_explicit_selections(self):
        news=json.loads((ROOT/'data/news.json').read_text(encoding='utf8'))
        for entry in CATALOG:
            result=site.related_news_for_explainer(entry,news)
            if entry.get('related_news'):
                self.assertEqual([str(i) for i in entry['related_news']],[str(i['id']) for i in result])
            else:
                self.assertLessEqual(len(result),3)
                self.assertTrue(all(site.explainer_match_score(n,entry['id']) for n in result))
        self.assertTrue(site.related_news_for_explainer(next(e for e in CATALOG if e['id']=='exp-018'),news))

if __name__=='__main__':unittest.main()
