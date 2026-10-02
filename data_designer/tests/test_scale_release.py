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
from scale_release import NoveltyIndex, RESEARCH_SCHEMA


class ScaleTests(unittest.TestCase):
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
