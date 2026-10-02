"""Summarize a completed review batch without treating model ratings as approval."""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from _paths import ROOT, CONFIGS, REFERENCES


import argparse
import json
import statistics
from collections import Counter
from decimal import Decimal
from pathlib import Path


def median_words(rows):
    values = [len(m["content"].split()) for row in rows for m in row["conversation"]["messages"] if m["role"] == "assistant"]
    return statistics.median(values) if values else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, default=Path("data_designer/output/saudi_sft_pilot_v1/data/train.jsonl"))
    args = parser.parse_args()
    manifest = json.loads(args.input.with_suffix(".manifest.json").read_text(encoding="utf-8"))
    if not manifest.get("finished_at"):
        parser.error("generation is not complete yet")
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != manifest["completed_conversations"]:
        parser.error("dataset count doesn't match completed manifest")
    summary = json.loads(args.input.with_suffix(".summary.json").read_text(encoding="utf-8"))
    cost = json.loads(args.input.with_suffix(".cost.json").read_text(encoding="utf-8"))
    audit = json.loads(args.input.with_suffix(".audit.json").read_text(encoding="utf-8"))
    baseline = []
    if args.baseline.exists():
        baseline = [row for line in args.baseline.read_text(encoding="utf-8").splitlines() if line.strip()
                    for row in [json.loads(line)] if row.get("origin") == "synthetic"]
    previous_words = [len(m["content"].split()) for row in baseline for m in row["messages"] if m["role"] == "assistant"]
    total_cost = Decimal(str(cost["observed_key_usage_delta_usd"]))
    model = manifest["models"]
    lines = ["# Hybrid pilot review", "",
             f"{len(rows)} conversations, {summary['assistant_turns']} assistant turns, {len(summary['domains'])} active domains.", "",
             f"{summary['machine_screen_passed']} conversations passed model screening; {len(rows) - summary['machine_screen_passed']} were flagged. All require user review; none are training-approved.", "",
             "## Answer depth", "",
             f"Median whitespace words: draft {summary['draft_words']['median']}; enhanced {summary['enhanced_words']['median']}; displayed final {summary['selected_words']['median']}.", "",
             "Displayed finals include flagged candidates retained for inspection. Word counts are descriptive, not a quality score or training-effect measurement.", "",
             "| Conversation group | Chats | Median final answer words |", "| --- | ---: | ---: |"]
    for profile in ["practical", "deep"]:
        selected = [row for row in rows if row["profile"] == profile]
        lines.append(f"| {profile} | {len(selected)} | {median_words(selected)} |")
    passed = [row for row in rows if row["screening_passed"]]
    lines.append(f"| Machine-passing conversations | {len(passed)} | {median_words(passed)} |")
    if previous_words:
        lines.extend(["", f"Previous prepared synthetic training examples: median {statistics.median(previous_words)} words across {len(previous_words)} assistant turns. This is a different corpus, not a controlled ablation."])
    if "first_user_words" in summary:
        lines.extend(["", f"First user messages: median {summary['first_user_words']['median']} whitespace words. First answers: median {summary['first_answer_words']['median']} words. Markdown is present in {summary['markdown_answers']}/{summary['assistant_turns']} answers."])
    lines.extend(["", "## Coverage and screening", "", f"Domain counts: {json.dumps(summary['domains'], ensure_ascii=False)}.", "",
                  f"Raw model preference counts: {json.dumps(summary['preferred'])}. Actual display selections: {json.dumps(dict(Counter(variant['selected'] for row in rows for variant in row['answer_variants'])))}. Enhancement added value on {summary['enhancement_adds_value']} turns according to the model; enhanced padding flagged on {summary['enhanced_padding']} turns.", "",
                  f"First user messages containing 'يا هلا': {summary['first_user_ya_hala']}/{len(rows)}.", "",
                  f"Writer: {model['writer']}; enhancer: {model['enhancer']}; judge: {model['judge']}. Independent judge: {manifest['independent_judge']}. These ratings may share correlated mistakes.", "",
                  "## Flagged conversations", ""])
    for row, entry in zip(rows, audit, strict=True):
        if entry["issues"]:
            lines.append(f"- Sample {entry['row']} (seed {row['seed_index']}, {row['domain']}): " + "; ".join(entry["issues"]))
    lines.extend(["", "## Cost and storage", "",
                  f"Generation ledger's observed key-level usage change: ${cost['observed_key_usage_delta_usd']}.", "",
                  cost["measurement_note"], "",
                  f"Dataset: `{args.input}` on `{manifest['host']}`. Stage caches and logs remain on the VM.", "",
                  "## Next review", "",
                  "Open the batch in the viewer, compare draft/enhanced variants, and annotate complete conversations or individual messages. Resolve flagged records in a new version and re-review them. Export only matching explicit approvals; no training job has been launched.", ""])
    report = args.input.with_name(args.input.stem + "_report.md")
    report.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(dict(report=str(report), total_session_key_delta_usd=str(total_cost), summary=summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
