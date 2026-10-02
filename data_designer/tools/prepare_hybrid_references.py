"""Extract explicitly selected style references, never a rewritten SFT dataset."""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from _paths import ROOT, CONFIGS, REFERENCES


import argparse
import hashlib
import json
import re
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def parse_messages(value, *, completion=False):
    if isinstance(value, list):
        return validate_messages(value), "json"
    if not isinstance(value, str) or not value.strip():
        raise ValueError("empty/non-text conversation")
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, list):
        return validate_messages(parsed), "json"
    matches = list(re.finditer(r"(?:^|\n)\s*(user|assistant|system|المستخدم|المساعد|النظام)\s*:", value, re.I))
    if matches:
        roles = {"المستخدم": "user", "المساعد": "assistant", "النظام": "system"}
        messages = [{"role": roles.get(match.group(1), match.group(1).lower()),
                     "content": value[match.end():matches[i + 1].start() if i + 1 < len(matches) else len(value)].strip()}
                    for i, match in enumerate(matches)]
        return validate_messages(messages), "transcript"
    if completion:
        return [{"role": "assistant", "content": value.strip()}], "plain_completion"
    # Unlabelled transcripts and broken JSON must be selected and normalized
    # explicitly in the selection file, rather than guessing role boundaries.
    raise ValueError("ambiguous unlabelled prompt or malformed JSON")


def validate_messages(messages):
    if not messages:
        raise ValueError("empty messages")
    for message in messages:
        if message.get("role") not in {"user", "assistant", "system"} or not isinstance(message.get("content"), str) or not message["content"].strip():
            raise ValueError("invalid role/content")
    return [{"role": m["role"], "content": m["content"].strip()} for m in messages]


def prepare(saas, local, selections):
    references = []
    for selection in selections:
        origin, index = selection["origin"], selection["index"]
        if selection["review_status"] != "agent_style_reviewed":
            raise ValueError("each selected reference needs an explicit style review")
        raw = (saas if origin == "saas" else local)[index]
        if origin == "saas":
            if "normalized_prompt" in selection:
                history = validate_messages(selection["normalized_prompt"])
            else:
                history, _ = parse_messages(raw["enhanced_prompt"])
            completion, _ = parse_messages(raw["enhanced_completion"], completion=True)
            if history[-1]["role"] != "user" or len(completion) != 1 or completion[0]["role"] != "assistant":
                raise ValueError("select a user-ending prompt with a standalone assistant completion")
            user = history[-1]["content"]
            answer = completion[0]["content"]
            earlier_users = [m["content"] for m in history[:-1] if m["role"] == "user"]
        elif origin == "local":
            messages = validate_messages(raw["conversation"]["messages"])
            turn = selection.get("turn", 1)
            user, answer = messages[2 * turn - 2]["content"], messages[2 * turn - 1]["content"]
            earlier_users = [m["content"] for m in messages[:2 * turn - 2] if m["role"] == "user"]
        else:
            raise ValueError("unknown reference origin")
        reference = {key: selection[key] for key in ["id", "origin", "index", "domain", "request_type", "demonstrates", "review_status", "review_note"]}
        reference.update(source_row_sha256=digest(raw), role="style_only_not_factual_evidence",
                         user=selection.get("edited_user", user),
                         assistant=selection.get("edited_assistant", answer),
                         earlier_user_messages=earlier_users,
                         edited=("edited_user" in selection or "edited_assistant" in selection),
                         training_approved=False)
        references.append(reference)
    if len({r["id"] for r in references}) != len(references):
        raise ValueError("duplicate reference ID")
    return {"schema_version": 1, "purpose": "Style guidance for NEW conversations; not SFT data or factual evidence",
            "saas_sha256": digest(saas), "local_sha256": digest(local),
            "selection_sha256": digest(selections), "references": references}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saas", type=Path, required=True)
    parser.add_argument("--local", type=Path, default=Path("data_designer/output/saudi_scale_1000.jsonl"))
    parser.add_argument("--selections", type=Path, default=(REFERENCES / "hybrid_reference_selections.json"))
    parser.add_argument("--output", type=Path, default=(REFERENCES / "hybrid_references.json"))
    args = parser.parse_args()
    if args.output.exists():
        parser.error("reference output already exists; choose a new file")
    saas = json.loads(args.saas.read_text(encoding="utf-8"))
    local = [json.loads(line) for line in args.local.read_text(encoding="utf-8").splitlines() if line.strip()]
    result = prepare(saas, local, json.loads(args.selections.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(result['references'])} reviewed style references; source datasets unchanged.")


if __name__ == "__main__":
    main()
