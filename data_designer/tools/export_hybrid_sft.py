"""Export explicitly annotated hybrid chats, splitting related scenario families together."""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from _paths import ROOT, CONFIGS, REFERENCES


import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from common import digest


def annotation_fingerprint(row):
    # Matches AnnotationKit canonical JSON + SHA256 for these records.
    return digest(row)


def select_rows(rows, annotations, dataset):
    entries = {}
    for item in annotations:
        if item.get("dataset") != dataset:
            continue
        if item.get("schema_version") != 1 or item.get("verdict") not in {"good", "needs_work", "reject", "unrated"}:
            raise ValueError("invalid annotation schema/verdict")
        target = item.get("target")
        if target != "conversation" and (type(target) is not int or target < 0):
            raise ValueError("invalid annotation target")
        key = (item["record_sha256"], target)
        if key in entries:
            raise ValueError("duplicate annotation target; export one merged annotation backup")
        entries[key] = item
    kept, rejected = [], Counter()
    for row in rows:
        if row.get("exact_duplicate") or not row.get("screening_passed"):
            rejected["machine_flagged_or_duplicate"] += 1
            continue
        fingerprint = annotation_fingerprint(row)
        relevant = [value for (record_hash, _), value in entries.items() if record_hash == fingerprint]
        if any(value["verdict"] in {"reject", "needs_work"} or value.get("issues") for value in relevant):
            rejected["human_flagged"] += 1
            continue
        whole = entries.get((fingerprint, "conversation"), {})
        messages = row["conversation"]["messages"]
        all_messages_good = all(entries.get((fingerprint, index), {}).get("verdict") == "good" for index in range(len(messages)))
        if whole.get("verdict") != "good" and not all_messages_good:
            rejected["not_explicitly_approved"] += 1
            continue
        kept.append(dict(messages=messages, origin="hybrid_human_reviewed", family_id=row["family_id"],
                         seed_index=row["seed_index"], source_record_sha256=fingerprint,
                         reference_library_sha256=row["reference_library_sha256"],
                         reference_ids=row["reference_ids"], training_approved=True))
    return kept, dict(rejected)


def split_rows(rows, fraction, seed):
    families = sorted({row["family_id"] for row in rows}, key=lambda family: hashlib.sha256(f"{seed}:{family}".encode()).digest())
    if not 0 <= fraction < 1:
        raise ValueError("validation fraction must be >=0 and <1")
    validation_count = max(1, round(len(families) * fraction)) if fraction and len(families) > 1 else 0
    validation = set(families[:validation_count])
    return [row for row in rows if row["family_id"] not in validation], [row for row in rows if row["family_id"] in validation]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validation-fraction", type=float, default=.1)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("choose a new output directory")
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    annotations = [json.loads(line) for line in args.annotations.read_text(encoding="utf-8").splitlines() if line.strip()]
    approved, rejected = select_rows(rows, annotations, args.input.name)
    if not approved:
        parser.error("no conversations have explicit matching human approval; no export created")
    train, validation = split_rows(approved, args.validation_fraction, args.seed)
    args.output.joinpath("data").mkdir(parents=True)
    for name, split in [("train", train), ("validation", validation)]:
        args.output.joinpath("data", name + ".jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in split), encoding="utf-8")
    manifest = dict(input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
                    annotations_sha256=hashlib.sha256(args.annotations.read_bytes()).hexdigest(),
                    approved=len(approved), rejected=rejected, train=len(train), validation=len(validation),
                    split_seed=args.seed, split_by="family_id", reference_examples_exported=False,
                    note="All assistant turns supervised only after explicit review. Check tokenizer lengths before training. Reference-guided validation is not an independent style evaluation.")
    args.output.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
