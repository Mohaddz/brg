"""Offline checks for scale novelty and search-response accounting."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _paths

import io
import json
import os
import tempfile
import threading
import unittest
from decimal import Decimal
from unittest.mock import patch

from lightweight import Requests
from scale_release import NoveltyIndex, RESEARCH_SCHEMA, screen_context, accepted_rows, total_cost, release


class ScaleTests(unittest.TestCase):
    def test_release_replenishes_context_exclusions_before_packaging(self):
        with patch('scale_release.generate') as generate, patch('scale_release.accepted_rows',return_value=[]), patch(
                'scale_release.screen_context',side_effect=[[],[{},{}]]), patch('scale_release.package') as package:
            release(Path('unused'),2)
            self.assertEqual(generate.call_count,2)
            package.assert_called_once_with(Path('unused'),2)

    def test_context_screen_hides_notes_and_preserves_original_audit_rows(self):
        rows=[{'seed_index':i,'screening_passed':True,'remaining_issues':[],
            'first_question':'هل كان أول رائد فضاء سعودي؟',
            'fact_pack':'hidden notes','conversation':{'messages':[
                {'role':'user','content':'هل كان أول رائد فضاء سعودي؟'},
                {'role':'assistant','content':'من تقصد؟' if i else 'إيه، سلطان.'}]}} for i in range(2)]
        class FakeRequests:
            def __init__(inner,*args):pass
            def call(inner,name,system,data,*args):
                self.assertEqual(set(data), {'messages'})
                return {'acceptable':name.endswith('-1'),'reason':'missing person'}
            def report(inner,*args):pass
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp);(directory/'batches').mkdir()
            audit=directory/'batches/batch_001.jsonl'
            original=''.join(json.dumps(row)+'\n' for row in rows)
            audit.write_text(original)
            with patch('scale_release.Requests',FakeRequests):
                result=screen_context(directory,rows)
            self.assertEqual([r['seed_index'] for r in result],[1])
            self.assertEqual(audit.read_text(),original)
            loaded=accepted_rows(directory)
            self.assertFalse(loaded[0]['screening_passed'])
            self.assertTrue(loaded[1]['screening_passed'])
            (directory/'context.cost.json').write_text(json.dumps({'reported_cost_usd':'.005'}))
            self.assertEqual(total_cost(directory),Decimal('.005'))

    def test_paid_truncation_extension_is_bounded_and_both_calls_are_charged(self):
        def raw(finish, content, cost):
            return json.dumps({'choices':[{'finish_reason':finish,'message':{'content':content}}],
                'usage':{'cost':cost}}).encode()
        responses = [raw('length', '', .001), raw('stop', '{"facts":[]}', .002)]
        with tempfile.TemporaryDirectory() as directory:
            ledger = Requests.__new__(Requests)
            ledger.lock = threading.RLock()
            ledger.directory = Path(directory)
            ledger.cfg = {'model':'test','budget_usd':1}
            ledger.billing = {'pricing_usd_per_token':{'prompt':'0','completion':'0'}}
            def response(*args, **kwargs):
                value = io.BytesIO(responses.pop(0))
                value.headers = {}
                return value
            with patch.dict(os.environ, {'OPENROUTER_API_KEY':'offline'}), patch(
                    'lightweight.urllib.request.urlopen',side_effect=response) as network:
                value = ledger.call('novelty-one','system',{},RESEARCH_SCHEMA,100)
                self.assertEqual(value, {'facts':[]})
                self.assertEqual(network.call_count, 2)
            self.assertEqual(ledger.spent(), Decimal('.003'))
            self.assertEqual(len(list(Path(directory).glob('request-*.json'))), 2)

    def test_novelty_rejects_duplicates_and_keeps_different_tasks(self):
        index = NoveltyIndex()
        self.assertTrue(index.accept('اكتب رسالة شكر للمعلم'))
        self.assertFalse(index.accept('اكتب رسالة شكر للمعلم!'))
        self.assertFalse(index.accept('اكتب رسالة شكر للمعلم اليوم'))
        self.assertTrue(index.accept('اشرح الفرق بين الكتلة والوزن'))

    def test_search_prose_is_saved_and_charged_without_reissuing_search(self):
        body = json.dumps({'choices':[{'finish_reason':'stop','message':{
            'content':'Cited research prose rather than JSON.', 'annotations':[]}}],
            'usage':{'cost':.007}}).encode()
        with tempfile.TemporaryDirectory() as directory:
            ledger = Requests.__new__(Requests)
            ledger.lock = threading.RLock()
            ledger.directory = Path(directory)
            ledger.cfg = {'model':'test','budget_usd':1}
            ledger.billing = {'pricing_usd_per_token':{'prompt':'0','completion':'0'}}
            def response(*args, **kwargs):
                value = io.BytesIO(body)
                value.headers = {}
                return value
            with patch.dict(os.environ, {'OPENROUTER_API_KEY':'offline'}), patch(
                    'lightweight.urllib.request.urlopen',side_effect=response) as network:
                tools = [{'type':'openrouter:web_search'}]
                args = ('research-one','system',{},RESEARCH_SCHEMA,100)
                first = ledger.call(*args, extra_tools=tools)
                second = ledger.call(*args, extra_tools=tools)
                self.assertEqual(first, second)
                self.assertEqual(network.call_count, 1)
            self.assertEqual(ledger.spent(), Decimal('.007'))
            self.assertFalse(ledger.unresolved())


if __name__=='__main__':unittest.main()
