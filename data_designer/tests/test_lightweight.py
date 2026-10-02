"""Offline checks of quality gates and cost attribution; never call a model."""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from _paths import ROOT, CONFIGS, REFERENCES

import json
import io
import os
import concurrent.futures
import threading
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from lightweight import Requests, batch_checks, checks, conversation_schema, review_failed, replace_answers, generate_conversations, apply_conversation_repair, repairable_user_positions, screen_conversations, export


class LightweightTests(unittest.TestCase):
    def test_casual_style_exception_does_not_weaken_factual_checks(self):
        row = dict(self.row(), domain='chitchat', grounding_mode='task')
        messages = self.messages()
        messages[1]['content'] = 'A short natural reply with enough words.'
        messages[3]['content'] = 'Another friendly reply without forced formatting here.'
        self.assertEqual(checks(row, messages, {'references': []}), [])
        row['domain'] = 'science'
        self.assertIn('missing useful Markdown', ' '.join(checks(row, messages, {'references': []})))

    def row(self):
        return {"seed_index": 0, "first_question": "why?", "max_exchanges": 2,
                "sources": json.dumps([{"url": "https://source.test/fact"}]),
                "grounding_mode": "grounded"}

    def messages(self):
        return [{"role": "user", "content": "why?"},
                {"role": "assistant", "content": "**Explanation** " + "useful " * 20 + "[source](https://source.test/fact)"},
                {"role": "user", "content": "what happened next?"},
                {"role": "assistant", "content": "**Follow-up** " + "different " * 20 + "[source](https://source.test/fact)"}]

    def test_exact_depth_and_roles(self):
        row, messages = self.row(), self.messages()
        self.assertEqual(checks(row, messages, {"references": []}), [])
        messages[2]["role"] = "assistant"
        self.assertIn("invalid role", " ".join(checks(row, messages, {"references": []})))
        self.assertEqual(checks(row, messages[:2], {"references": []}), ["Incorrect exchange count"])
        self.assertEqual(conversation_schema(6)["properties"]["messages"]["minItems"], 12)

    def test_first_question_and_citation_gate(self):
        messages = self.messages()
        messages[0]["content"] = "rewritten"
        messages[1]["content"] = messages[1]["content"].replace("source.test", "invented.test")
        issues = checks(self.row(), messages, {"references": []})
        self.assertIn("First question changed", issues)
        self.assertIn("citation outside", " ".join(issues))

    def test_repeated_user_and_cross_topic_answers(self):
        messages = self.messages()
        messages[2]["content"] = messages[0]["content"]
        self.assertIn("duplicate user", " ".join(checks(self.row(), messages, {"references": []})))
        rows = [{"seed_index": n, "conversation": {"messages": self.messages()}} for n in range(2)]
        flags = batch_checks(rows)
        self.assertTrue(flags[0] and flags[1])

    def test_reviewer_conflicts_fail_closed(self):
        good = dict(acceptable=True, issues=[], accuracy=5, usefulness=4, naturalness=4,
                    continuity=4, baseline_comparison="similar")
        self.assertFalse(review_failed(good))
        self.assertTrue(review_failed(dict(good, issues=["unsupported date"])))
        self.assertTrue(review_failed(dict(good, accuracy=3)))
        self.assertTrue(review_failed(dict(good, baseline_comparison="worse")))

    def test_closing_offer_respects_assigned_turn(self):
        row, messages = self.row(), self.messages()
        messages[1]["content"] += " \u0625\u0630\u0627 \u062a\u0628\u064a \u0623\u0634\u0631\u062d \u0644\u0643."
        self.assertIn("unassigned closing offer", " ".join(checks(row, messages, {"references": []})))
        row["quality_policy"] = {"closing_offer_turn": 1}
        self.assertNotIn("unassigned closing offer", " ".join(checks(row, messages, {"references": []})))

    def test_costs_include_invalid_completion_and_repairs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, cost in [("generate-0", .003), ("repair-0-1", .002), ("recheck-0-1", .001)]:
                (root / f"request-{name}.json").write_text(json.dumps({"raw": {
                    "usage": {"cost": cost}, "choices": [{"finish_reason": "length"}]}}))
            ledger = Requests.__new__(Requests)
            ledger.lock = threading.RLock()
            ledger.directory = root
            self.assertEqual(ledger.spent(), Decimal("0.006"))
            (root / "request-review-1.json").write_text(json.dumps({"raw": {"usage": {}}}))
            with self.assertRaisesRegex(RuntimeError, "Missing provider cost"):
                ledger.spent()

    def test_unresolved_transport_cost_reserves_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Requests.__new__(Requests)
            ledger.lock = threading.RLock()
            ledger.directory = Path(directory)
            (ledger.directory / "request-recheck-0.unresolved").write_text(json.dumps({"reserve_usd": "0.0032845"}))
            self.assertEqual(ledger.spent(), Decimal("0.0032845"))

    def test_assistant_only_repairs_cannot_rewrite_users(self):
        messages = self.messages()
        corrected = replace_answers(messages, ["new answer", "new continuation"])
        self.assertEqual(corrected[::2], messages[::2])
        self.assertNotEqual(corrected[1], messages[1])
        self.assertIn("Explanation", messages[1]["content"])
        with self.assertRaises(ValueError):
            replace_answers(messages, ["incomplete"])

    def test_repair_can_fix_flagged_followup_but_locks_other_users(self):
        original = self.messages()
        original[2] = {"role": "assistant", "content": ""}
        allowed = repairable_user_positions(original, ["Message 3: invalid role or blank content"])
        self.assertEqual(allowed, [2])
        value = {"messages": self.messages()}
        corrected = apply_conversation_repair(self.row(), original, value, allowed)
        self.assertEqual(corrected[2]["role"], "user")
        self.assertEqual(original[2]["content"], "")
        value["messages"][0]["content"] = "rewritten starter"
        with self.assertRaisesRegex(ValueError, "starter"):
            apply_conversation_repair(self.row(), original, value, allowed)
        with self.assertRaisesRegex(ValueError, "protected user"):
            apply_conversation_repair(self.row(), original, {"messages": self.messages()}, [])
        self.assertEqual(repairable_user_positions(original, ["Repair changed protected user message 3"]), [])

    def test_parallel_repairs_recheck_and_keep_seed_order(self):
        barrier = threading.Barrier(3)
        original = self.messages()
        original[2] = {"role": "assistant", "content": ""}
        seeds = [dict(self.row(), seed_index=i, conversation={"messages": original}, baseline_answer="") for i in range(3)]
        calls = []
        lock = threading.Lock()
        class FakeRequests:
            def call(inner, name, system, data, schema, max_tokens, *args):
                with lock:
                    calls.append(name)
                if name.startswith("repair-"):
                    self.assertEqual(data["allowed_user_message_numbers"], [3])
                    barrier.wait(timeout=5)
                    return {"messages": self.messages()}
                return dict(acceptable=True, issues=[], accuracy=5, usefulness=5, naturalness=5,
                    continuity=5, baseline_comparison="similar", reason="ok")
        with patch("lightweight.context", return_value={}):
            results = screen_conversations(seeds, FakeRequests(), {"references": []}, set(),
                {i: [] for i in range(3)}, {"repair_concurrency": 3, "repair_attempts": 2, "model": "test"})
        self.assertEqual([r["seed_index"] for r in results], [0, 1, 2])
        self.assertTrue(all(r["screening_passed"] for r in results))
        self.assertTrue(all(r["repair_history"][0]["changed_user_message_numbers"] == [3] for r in results))
        self.assertEqual(len(calls), 6)
        self.assertEqual(seeds[0]["conversation"]["messages"][2]["content"], "")

    def test_failed_repairs_stop_at_cap_and_are_excluded(self):
        seed = dict(self.row(), conversation={"messages": self.messages()}, baseline_answer="")
        seed["conversation"]["messages"][2]["content"] = ""
        calls = []
        class FakeRequests:
            def call(inner, name, *args):
                calls.append(name)
                value = {"messages": self.messages()}
                value["messages"][0]["content"] = "forbidden rewrite"
                return value
            def report(inner, *args):
                return {}
        with patch("lightweight.context", return_value={}):
            results = screen_conversations([seed], FakeRequests(), {"references": []}, set(), {0: []},
                {"repair_concurrency": 1, "repair_attempts": 2, "model": "test"})
        self.assertEqual(len(calls), 2)
        self.assertFalse(results[0]["screening_passed"])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "pilot.jsonl"
            results[0]["domain"] = "science"
            export(results, output, FakeRequests())
            self.assertTrue(output.read_text())
            self.assertEqual(output.with_suffix(".passing.jsonl").read_text(), "")

    def test_1000_word_cap_and_historical_policy(self):
        row, messages = self.row(), self.messages()
        messages[1]["content"] = "**Explanation** " + "detail " * 999
        self.assertEqual(len(messages[1]["content"].split()), 1000)
        row["grounding_mode"] = "task"
        self.assertEqual(checks(row, messages, {"references": []}), [])
        messages[1]["content"] += "extra"
        self.assertIn("15-1000 word bounds (1001)", " ".join(checks(row, messages, {"references": []})))
        row["quality_policy"] = {"max_answer_words": 240}
        self.assertIn("15-240 word bounds", " ".join(checks(row, messages, {"references": []})))

    def test_ten_generation_workers_keep_seed_order(self):
        barrier = threading.Barrier(10)
        lock = threading.Lock()
        active = peak = started = 0

        class FakeRequests:
            def call(self, name, system, data, schema, max_tokens):
                nonlocal active, peak, started
                with lock:
                    active += 1
                    peak = max(peak, active)
                    rank = started
                    started += 1
                if rank < 10:
                    barrier.wait(timeout=5)
                with lock:
                    active -= 1
                return {"messages": [{"role": "user", "content": str(data["seed_index"])},
                    {"role": "assistant", "content": "answer"}]}

        seeds = [{"seed_index": i, "max_exchanges": 1} for i in range(20)]
        with patch("lightweight.context", side_effect=lambda row: {"seed_index": row["seed_index"]}):
            result = generate_conversations(seeds, FakeRequests(), 10)
        self.assertEqual((started, peak), (20, 10))
        self.assertEqual([r["seed_index"] for r in result], list(range(20)))
        self.assertEqual([r["conversation"]["messages"][0]["content"] for r in result], [str(i) for i in range(20)])
        self.assertNotIn("conversation", seeds[0])

    def test_inflight_reservation_blocks_concurrent_overspend_and_cache_reuses(self):
        entered, release = threading.Event(), threading.Event()
        body = json.dumps({"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps({"messages": []})}}], "usage": {"cost": .01}}).encode()

        def fake_urlopen(req, timeout):
            entered.set()
            if not release.wait(timeout=5):
                raise TimeoutError("Test release not received")
            response = io.BytesIO(body)
            response.headers = {}
            return response

        with tempfile.TemporaryDirectory() as directory:
            ledger = Requests.__new__(Requests)
            ledger.lock = threading.RLock()
            ledger.directory = Path(directory)
            ledger.cfg = {"model": "test-model", "budget_usd": .15}
            ledger.billing = {"pricing_usd_per_token": {"prompt": "0", "completion": ".01"}}
            args = ("system", {}, conversation_schema(1), 10)
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-test"}), patch(
                "lightweight.urllib.request.urlopen", side_effect=fake_urlopen) as network:
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    first = pool.submit(ledger.call, "generate-0", *args)
                    try:
                        self.assertTrue(entered.wait(timeout=5))
                        with self.assertRaisesRegex(RuntimeError, "budget would be exceeded"):
                            ledger.call("generate-1", *args)
                    finally:
                        release.set()
                    self.assertEqual(first.result(timeout=5), {"messages": []})
                self.assertEqual(ledger.spent(), Decimal("0.01"))
                self.assertEqual(ledger.call("generate-0", *args), {"messages": []})
                self.assertEqual(network.call_count, 1)


if __name__ == "__main__":
    unittest.main()
