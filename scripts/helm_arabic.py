"""Run Stanford's official HELM Arabic suite locally (crfm-helm==0.5.16).

This is the official-numbers path. The Inspect tasks in src/brg/tasks.py mirror
the same conf/schema but are not leaderboard-identical; use this when a real
HELM score is needed (e.g., for a published comparison).

Requires the optional dependency group:
    uv sync --group helm

Config check (no model calls):
    uv run --group helm python scripts/helm_arabic.py --check

Live run (model must be registered in HELM, e.g. openai/gpt-4o):
    OPENAI_API_KEY=... uv run --group helm python scripts/helm_arabic.py \
        --model openai/gpt-4o --run-id my-run --live

OPENAI_API_KEY is required even for non-OpenAI targets because ALRAGE's
annotator judges with openai/gpt-4o-2024-11-20. Outputs land in
runs/helm-arabic/<run-id>/.
"""

import argparse
import json
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "references" / "helm-arabic-v0.5.16"
OUTPUT_ROOT = REPO / "runs" / "helm-arabic"

FAMILIES = {
    "alrage", "arabic_exams", "mbzuai_human_translated_arabic_mmlu",
    "alghafa", "aratrust", "arabic_mmlu", "madinah_qa",
}


def _configuration():
    entries = CONFIG / "run_entries_arabic.conf"
    schema = CONFIG / "schema_arabic.yaml"
    if not entries.is_file() or not schema.is_file():
        raise FileNotFoundError("Missing pinned HELM conf/schema in references/")
    raw = entries.read_text(encoding="utf-8")
    descriptions = re.findall(r'\{description:\s*"([^"]+)"', raw)
    families = {d.split(":", 1)[0] for d in descriptions}
    if families != FAMILIES:
        raise ValueError(f"HELM Arabic family mismatch: {families ^ FAMILIES}")
    return {"helm_version": "0.5.16", "families": sorted(families),
            "run_entries": len(descriptions),
            "max_eval_instances_per_run": 1000}


def _credentials_dir():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required for the ALRAGE GPT-4o judge")
    d = tempfile.mkdtemp(prefix="brg-helm-creds-")
    creds = Path(d) / "credentials.conf"
    creds.write_text("openaiApiKey: " + json.dumps(key) + "\n", encoding="utf-8")
    creds.chmod(0o600)
    return d


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true",
                        help="verify config parses; no model calls")
    parser.add_argument("--live", action="store_true",
                        help="actually run (paid eval). Required for live runs.")
    parser.add_argument("--model", default="", help="HELM-registered model, e.g. openai/gpt-4o")
    parser.add_argument("--run-id", default="", help="unique run id (output dir name)")
    args = parser.parse_args()

    details = _configuration()

    if args.check:
        cmd = ["helm-run", "--conf-paths", str(CONFIG / "run_entries_arabic.conf"),
               "--num-train-trials", "1", "--max-eval-instances", "1000",
               "--priority", "2", "--suite", "brg-helm-check",
               "--models-to-run", "openai/gpt-4o", "--skip-instances",
               "--output-path", "/tmp/brg-helm-check"]
        subprocess.run(cmd, check=True)
        print(json.dumps({**details, "official_config_parsed": True}, indent=2))
        return 0

    if not args.live:
        parser.error("Refusing to run without --live (this is a paid evaluation)")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", args.run_id):
        parser.error("--run-id must be alphanumeric/._- (max 80 chars)")
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", args.model):
        parser.error("--model must be a HELM-registered model name")

    out = OUTPUT_ROOT / args.run_id
    if out.exists():
        raise FileExistsError(f"Run directory already exists: {out}")
    out.mkdir(parents=True)
    creds = _credentials_dir()

    cmd = ["helm-run", "--conf-paths", str(CONFIG / "run_entries_arabic.conf"),
           "--num-train-trials", "1", "--max-eval-instances", "1000",
           "--priority", "2", "--suite", args.run_id,
           "--models-to-run", args.model, "--output-path", str(out),
           "--local-path", creds]
    with (out / "helm-run.log").open("w", encoding="utf-8") as log:
        subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
    with (out / "helm-summarize.log").open("w", encoding="utf-8") as log:
        subprocess.run(["helm-summarize", "--schema", str(CONFIG / "schema_arabic.yaml"),
                        "--suite", args.run_id, "--output-path", str(out)],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    print(json.dumps({"status": "complete", "output": str(out), **details}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
