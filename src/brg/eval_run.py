"""Run the brg Inspect suite against any model endpoint.

Model is an Inspect model spec. For OpenAI-compatible endpoints use the
`openai-api` provider: `openai-api/<service>/<model>` with env vars
`<SERVICE>_API_KEY` and `<SERVICE>_BASE_URL` (uppercased service name).

Tinker checkpoints are OpenAI-compatible:
    TINKER_BASE_URL=https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1
    TINKER_API_KEY=...
    uv run python -m brg.eval_run \
        --model 'openai-api/tinker/tinker://<run>:train:0/sampler_weights/<step>'

Or use OPENAI_BASE_URL/OPENAI_API_KEY with `--model openai/<model-name>`.

ALRAGE is gated behind --alrage and needs a judge model (default:
openai/gpt-4o-2024-11-20, the official HELM judge). For a non-OpenAI judge:
    --alrage --judge-model 'openai-api/alrage/<judge-model>'
    with ALRAGE_API_KEY + ALRAGE_BASE_URL set.

Examples:
    uv run python -m brg.eval_run --model openai-api/deepinfra/Qwen/... --limit 100
    uv run python -m brg.eval_run --model openai/gpt-4o --tasks arabic_mmlu,alghafa
    uv run python -m brg.eval_run --model ... --alrage --judge-model openai/gpt-4o-2024-11-20
"""

import argparse
import sys

from brg import tasks as brg_tasks
from brg.helm_spec import ALRAGE_JUDGE_DEFAULT


def _build_tasks(names, alrage, judge_model):
    builders = {
        "arabic_mmlu": brg_tasks.arabic_mmlu,
        "madinah_qa": brg_tasks.madinah_qa,
        "ht_arabic_mmlu": brg_tasks.ht_arabic_mmlu,
        "arabic_exams": brg_tasks.arabic_exams,
        "alghafa": brg_tasks.alghafa,
        "aratrust": brg_tasks.aratrust,
        "balsam_dev": brg_tasks.balsam_dev,
    }
    selected = brg_tasks.ALL_TASKS if names == ["all"] else names
    unknown = [n for n in selected if n not in builders]
    if unknown:
        raise ValueError(f"Unknown tasks {unknown}; choose from {sorted(builders)} or 'all'")
    built = [builders[name]() for name in selected]
    if alrage:
        built.append(brg_tasks.alrage(judge=judge_model or ALRAGE_JUDGE_DEFAULT))
    return built


def main(argv=None):
    parser = argparse.ArgumentParser(prog="brg-eval", description=__doc__,
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True,
                        help="Inspect model spec, e.g. openai/gpt-4o or "
                             "openai-api/<service>/<model>")
    parser.add_argument("--tasks", default="all",
                        help="comma-separated task names or 'all' (ALRAGE excluded unless --alrage)")
    parser.add_argument("--alrage", action="store_true",
                        help="include the ALRAGE judged task (costs judge API calls)")
    parser.add_argument("--judge-model", default="",
                        help=f"judge model spec for ALRAGE (default {ALRAGE_JUDGE_DEFAULT})")
    parser.add_argument("--limit", type=int, default=None,
                        help="max samples per task (Inspect --limit)")
    parser.add_argument("--log-dir", default="runs/inspect")
    parser.add_argument("--max-connections", type=int, default=16)
    args = parser.parse_args(argv)

    from inspect_ai import eval as inspect_eval

    names = [n.strip() for n in args.tasks.split(",") if n.strip()]
    built = _build_tasks(names, args.alrage, args.judge_model)
    results = inspect_eval(
        built,
        model=args.model,
        limit=args.limit,
        log_dir=args.log_dir,
        max_connections=args.max_connections,
        max_samples=args.max_connections,
    )
    for result in results:
        scores = {
            metric.name: metric.value
            for score in (result.results.scores if result.results else [])
            for metric in score.metrics.values()
        }
        print(f"{result.eval.task}: {scores}")
    return 0 if all(r.status == "success" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
