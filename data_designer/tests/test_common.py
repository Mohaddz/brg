"""Offline checks for parsing, evidence gates, preferences and dataset exports."""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from _paths import ROOT, CONFIGS, REFERENCES


import copy
import json
import tempfile
import unittest
import shutil
import subprocess
from pathlib import Path

from common import (Answer, Review, UserTurn, allocate, digest, finalize,
                    load_inputs, planned_rows, screen_review, style_issues, shape_feedback, select_answer,
                    validate_diversity, normalized_question, mark_repetition,
                    restore_answer_variant)
from research_topic import make_payload, citation_sources
from diversity_catalog import CATALOG, validate_catalog
from recipe import build_recipe
from prepare_hybrid_references import parse_messages
from export_hybrid_sft import annotation_fingerprint, select_rows, split_rows


class CommonTests(unittest.TestCase):
    def test_assigned_offer_accepts_natural_saudi_variants(self):
        row = {'quality_policy': {'closing_offer_turn': 1}}
        for question in ['تبغاني أعطيك مثالًا؟', 'تبغين نجرب مسألة؟', 'ودّك أشرحها؟']:
            self.assertEqual(style_issues(row, 'سؤال', '**الجواب**\n\n' + question, 1), [])
        self.assertIn('planned first-answer next-step offer is missing',
                      style_issues(row, 'سؤال', '**الجواب**\n\nإذا تحب، أشرحها.', 1))


    @classmethod
    def setUpClass(cls):
        cls.config, cls.library, cls.sources = load_inputs(ROOT / "tests/fixtures/planning.yaml")

    def test_reference_formats_and_ambiguous_prompt(self):
        messages, _ = parse_messages('[{"role":"user","content":"hi"}]')
        self.assertEqual(messages[0]["role"], "user")
        messages, _ = parse_messages("user: hi\n\nassistant: hello\n\nuser: explain")
        self.assertEqual([m["role"] for m in messages], ["user", "assistant", "user"])
        messages, _ = parse_messages("المستخدم: هلا\n\nالمساعد: أهلين")
        self.assertEqual(messages[1]["role"], "assistant")
        with self.assertRaises(ValueError):
            parse_messages('hi\n\nhello\n\nexplain')
        self.assertEqual(parse_messages("plain final", completion=True)[0][0]["role"], "assistant")

    def test_deterministic_pilot_and_nontrivial_short_users(self):
        rows = planned_rows(self.config, self.library, self.sources)
        self.assertEqual(rows, planned_rows(self.config, self.library, self.sources))
        self.assertEqual(len(rows), 50)
        self.assertEqual(sum(row["profile"] == "practical" for row in rows), 30)
        self.assertEqual(sum(row["profile"] == "deep" for row in rows), 20)
        self.assertEqual(len({row["family_id"] for row in rows}), 50)
        self.assertTrue(all(row["depth"] != "simple" for row in rows))
        self.assertTrue(all(row["max_exchanges"] >= 2 for row in rows if row["opening_mode"] != "direct"))
        self.assertEqual(sum(allocate(7, {"a": 3, "b": 2}).values()), 7)

    def test_missing_evidence_is_configuration_error(self):
        config = copy.deepcopy(self.config)
        config["domains"]["science"]["subdomains"]["astronomy"]["source_ids"] = []
        with self.assertRaisesRegex(ValueError, "checked source"):
            planned_rows(config, self.library, self.sources)

    def test_v2_keeps_literal_questions_short_unique_and_grounded(self):
        config, library, sources = load_inputs((CONFIGS / "hybrid_config_v2.yaml"))
        rows = planned_rows(config, library, sources)
        self.assertEqual(len(rows), 50)
        self.assertEqual(len({row["first_question"] for row in rows}), 50)
        self.assertEqual(rows, planned_rows(config, library, sources))
        self.assertTrue(all(1 <= row["max_exchanges"] <= 2 for row in rows))
        self.assertTrue(all(row["opening_mode"] == "direct" for row in rows))
        self.assertTrue(all(len(row["first_question"].split()) <= 18 for row in rows))
        self.assertTrue(all(row["first_question"] == row["cue"] for row in rows))
        self.assertTrue(all(row["fact_pack"] for row in rows if row["grounding_mode"] == "grounded"))
        self.assertEqual({row["domain"] for row in rows},
                         {"history", "saudi_sports", "public_figures", "homework", "teach_child", "science"})
        with self.assertRaisesRegex(ValueError, "distinct question seeds"):
            planned_rows(config, library, sources, 100)

    def test_style_screen_uses_task_and_turn_specific_limits(self):
        row = {"quality_policy": {"max_user_words": 4, "min_answer_words": 5,
                                  "min_followup_answer_words": 2, "max_answer_words": 10,
                                  "require_markdown": True}}
        self.assertEqual(style_issues(row, "short question", "**Answer** with four more words", 1), [])
        self.assertTrue(style_issues(row, "one two three four five", "**Enough** with four more words", 1))
        self.assertTrue(style_issues(row, "short question", "**Short** answer", 1))
        self.assertEqual(style_issues(row, "short question", "**Short** answer", 2), [])
        self.assertTrue(style_issues(row, "short question", "plain answer with five full words", 1))
        self.assertEqual(style_issues(row, "short question", "Answer with steps:\n1. First step", 1), [])
        self.assertTrue(style_issues(row, "short question", "**Long** " + "word " * 11, 1))
        feedback = json.loads(shape_feedback(row, "**Short** answer", 1))
        self.assertEqual(feedback["minimum_words"], 5)
        self.assertEqual(feedback["candidate_words"], 2)
        self.assertEqual(json.loads(shape_feedback(row, "**Short** answer", 2))["minimum_words"], 2)
        self.assertEqual(style_issues({}, "short question", "short answer", 2), [])

    def test_optional_closings_citations_and_scale_topic_limits(self):
        config, library, sources = load_inputs((CONFIGS / "hybrid_config_v2.yaml"))
        rows = planned_rows(config, library, sources)
        allowed = [row for row in rows if row["optional_closing_allowed"]]
        self.assertEqual(len(allowed), 8)
        self.assertTrue(all(row["depth"] != "compact" for row in allowed))
        self.assertEqual(len({row["answer_style"] for row in rows}), 5)
        self.assertTrue(all(row["quality_policy"]["require_citations"] == (row["grounding_mode"] == "grounded") for row in rows))
        scaled = copy.deepcopy(config)
        scaled["diversity"]["scale_gate_count"] = 2
        with self.assertRaisesRegex(ValueError, "explicit topic_id"):
            validate_diversity(scaled, rows)
        for index, row in enumerate(rows):
            row["topic_id"] = str(index)
        validate_diversity(scaled, rows)
        for row in rows:
            row["topic_id"] = "one-topic"
        with self.assertRaisesRegex(ValueError, "topic repetition"):
            validate_diversity(scaled, rows)
        self.assertEqual(normalized_question("أين الرياض؟"), normalized_question("اين الرياض!"))
        closing_row = {"quality_policy": {"closing_offer_turn": 1}}
        self.assertEqual(style_issues(closing_row, "question", "Complete answer.\n\nتبيني أوضحها بمثال ثاني؟", 1), [])
        self.assertTrue(style_issues(closing_row, "question", "Complete answer without offer.", 1))
        self.assertEqual(style_issues(closing_row, "question", "No repeated offer on follow-up.", 2), [])

    def test_citations_and_answer_clones_are_screened(self):
        row = dict(quality_policy={"require_citations": True}, sources='[{"url":"https://example.org/page"}]')
        self.assertEqual(style_issues(row, "question", "Answer. [Source](https://example.org/page)", 1), [])
        self.assertTrue(style_issues(row, "question", "Answer without citation", 1))
        self.assertTrue(style_issues(row, "question", "Answer. [Fake](https://other.org/page)", 1))
        text = " ".join(f"word{n}" for n in range(60))
        pairs = [(dict(repetition_policy={"answer_ngram_similarity": .72}, screening_passed=True,
                       conversation={"messages":[{"content":"different question"},{"content":text}]}),
                  dict(issues=[],machine_screen_passed=True)) for _ in range(2)]
        mark_repetition(pairs)
        self.assertTrue(pairs[0][0]["screening_passed"])
        self.assertFalse(pairs[1][0]["screening_passed"])

    def test_web_research_request_is_bounded_and_uses_actual_annotations(self):
        payload = make_payload("new history topic", ["example.org"])
        tool = payload["tools"][0]
        self.assertEqual(tool["type"], "openrouter:web_search")
        self.assertEqual(tool["parameters"]["max_total_results"], 3)
        message = {"annotations":[{"type":"url_citation", "url_citation":{"url":"https://example.org/a", "title":"Primary source"}},
                                  {"type":"url_citation", "url_citation":{"url":"https://example.org.evil.com/a"}}]}
        self.assertEqual(len(citation_sources(message, ["example.org"])), 1)
        self.assertEqual(citation_sources({"content":"https://example.org/invented"}, ["example.org"]), [])

    def test_diversity_recipe_has_200_questions_and_100_shared_families(self):
        validate_catalog()
        base, library, _ = load_inputs((CONFIGS / "hybrid_config_v2.yaml"))
        fixtures = [dict(topic_id=t["topic_id"], source_id="fixture-"+t["topic_id"],
            review_status="source_checked", url="https://example.org/"+t["topic_id"], publisher="offline fixture",
            checked_on="2026-10-01",facts=[dict(fact_id="fixture-"+t["topic_id"],text="Offline planning fixture, not training evidence.")])
            for t in CATALOG if t["allowed_domains"]]
        config = build_recipe(base, fixtures)
        rows = planned_rows(config, library, fixtures)
        self.assertEqual(len(rows), 200)
        self.assertEqual(len({r["topic_id"] for r in rows}), 100)
        self.assertEqual(len({r["family_id"] for r in rows}), 100)
        self.assertTrue(all(len(r["first_question"].split()) <= 24 for r in rows))
        self.assertEqual(sum(r["optional_closing_allowed"] for r in rows), 30)
        self.assertEqual(rows, planned_rows(config, library, fixtures))
        revised = build_recipe(base, fixtures, post_pilot=True)
        self.assertNotEqual(config['runtime']['output'], revised['runtime']['output'])
        self.assertNotEqual(config['sources'], revised['sources'])
        planned = planned_rows(revised, library, fixtures)
        self.assertEqual(len(planned), 200)
        narrow = [r for r in planned if r['depth'] == 'compact']
        self.assertTrue(narrow)
        self.assertTrue(all(r['quality_policy']['min_answer_words'] == 15 for r in narrow))
        self.assertTrue(all('source_limitations' in r for r in planned))
        with self.assertRaisesRegex(ValueError, "missing checked evidence"):
            build_recipe(base, fixtures[:-1])

    def test_stop_and_preference_validation(self):
        with self.assertRaises(ValueError):
            UserTurn(action="stop", text="continue", scenario="test")
        review = dict(natural_user=True, context_consistent=True, draft_acceptable=False,
                      enhanced_acceptable=True, preferred="draft", draft_completeness=2,
                      enhanced_completeness=5, enhanced_adds_value=True, unnecessary_padding=False,
                      unsupported_claims=[], issues=[], reason="draft fails")
        parsed = Review.model_validate(review).model_dump()
        chosen, issues = screen_review(parsed)
        self.assertEqual(chosen, "neither")
        self.assertTrue(any("inconsistent review" in issue for issue in issues))

    def test_shape_selection_never_chooses_model_rejected_alternative(self):
        row = {"quality_policy": {"min_answer_words": 5, "require_markdown": True}}
        review = dict(natural_user=True, context_consistent=True, draft_acceptable=True,
                      enhanced_acceptable=True, preferred="draft", unnecessary_padding=False,
                      unsupported_claims=[], issues=[])
        draft, enhanced = "**Short** answer", "**Full** answer explains the useful steps"
        self.assertEqual(select_answer(row, review, "question", draft, enhanced, 1, False)[0], "draft")
        selected, issues, note = select_answer(row, review, "question", draft, enhanced, 1, True)
        self.assertEqual(selected, "enhanced")
        self.assertEqual(issues, [])
        self.assertIn("model-acceptable", note)
        self.assertEqual(select_answer(row, dict(review, enhanced_acceptable=False), "question", draft, enhanced, 1, True)[0], "draft")
        self.assertTrue(select_answer(row, dict(review, unnecessary_padding=True), "question", draft, enhanced, 1, True)[1])


    def test_copied_reference_and_rejected_answer_stay_flagged(self):
        row = planned_rows(self.config, self.library, self.sources, 1)[0]
        row["conversation"]["messages"] = [{"role": "user", "content": "new request"},
                                             {"role": "assistant", "content": self.library["references"][0]["assistant"]}]
        row["turn_reviews"] = [{"turn": 1, "issues": ["both answers rejected"], "review": {}}]
        result, audit = finalize(row, self.library)
        self.assertFalse(result["screening_passed"])
        self.assertFalse(result["training_approved"])
        self.assertTrue(any("consecutive words" in issue for issue in audit["issues"]))


    def test_export_needs_matching_human_approval(self):
        row = dict(screening_passed=True, exact_duplicate=False, family_id="same-family", seed_index=1,
                   reference_library_sha256="refs", reference_ids=["ref"],
                   conversation={"messages": [{"role": "user", "content": "هلا"}, {"role": "assistant", "content": "أهلين"}]})
        self.assertEqual(select_rows([row], [], "pilot.jsonl")[0], [])
        annotation = dict(schema_version=1, dataset="pilot.jsonl", record_sha256=annotation_fingerprint(row),
                          target="conversation", verdict="good", issues=[])
        approved, _ = select_rows([row], [annotation], "pilot.jsonl")
        self.assertEqual(len(approved), 1)
        stale = dict(annotation, record_sha256="outdated")
        self.assertEqual(select_rows([row], [stale], "pilot.jsonl")[0], [])
        bad_message = dict(annotation, target=1, verdict="needs_work")
        self.assertEqual(select_rows([row], [annotation, bad_message], "pilot.jsonl")[0], [])
        rows = [dict(family_id="a"), dict(family_id="a"), dict(family_id="b"), dict(family_id="c")]
        train, validation = split_rows(rows, .3, 42)
        self.assertFalse({r["family_id"] for r in train} & {r["family_id"] for r in validation})

    @unittest.skipUnless(shutil.which("node"), "Node is needed to check viewer fingerprint compatibility")
    def test_annotation_hash_matches_viewer(self):
        row = dict(text="هلا\n«سؤال؟»", count=3, flags=[True, False], nested={"b": 2, "a": "اللهجة"})
        script = """const fs=require('fs'),crypto=require('crypto');
        function canonical(v){if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';
        if(v&&typeof v==='object')return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
        return JSON.stringify(v);}
        process.stdout.write(crypto.createHash('sha256').update(canonical(JSON.parse(fs.readFileSync(0,'utf8')))).digest('hex'));"""
        result = subprocess.run(["node", "-e", script], input=json.dumps(row, ensure_ascii=False),
                                text=True, encoding="utf-8", capture_output=True, check=True)
        self.assertEqual(result.stdout, annotation_fingerprint(row))


if __name__ == "__main__":
    unittest.main()
