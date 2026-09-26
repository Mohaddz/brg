"""Run the brg Inspect suite against any model endpoint.

Model is an Inspect model spec. For OpenAI-compatible endpoints use the
`openai-api` provider: `openai-api/<service>/<model>` with env vars
`<SERVICE>_API_KEY` and `<SERVICE>_BASE_URL` (uppercased service name).

Tinker checkpoints are OpenAI-compatible:
    TINKER_OAI_BASE_URL=https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1
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
import json
import math
import os
from pathlib import Path
from statistics import mean
import subprocess
import sys

from brg import tasks as brg_tasks
from brg.env import load_environment
from brg.helm_spec import ALRAGE_JUDGE_DEFAULT


HELM_TASKS = [name for name in brg_tasks.ALL_TASKS if name != "balsam_dev"]


def _build_tasks(names, alrage, judge_model, suite="legacy"):
    builders = {
        "arabic_mmlu": brg_tasks.arabic_mmlu,
        "madinah_qa": brg_tasks.madinah_qa,
        "ht_arabic_mmlu": brg_tasks.ht_arabic_mmlu,
        "arabic_exams": brg_tasks.arabic_exams,
        "alghafa": brg_tasks.alghafa,
        "aratrust": brg_tasks.aratrust,
        "balsam_dev": brg_tasks.balsam_dev,
    }
    available = {
        "legacy": brg_tasks.ALL_TASKS + ["alrage"],
        "helm": HELM_TASKS + ["alrage"],
        "balsam": ["balsam_dev"],
        "all": brg_tasks.ALL_TASKS + ["alrage"],
    }[suite]
    selected = [name for name in available if name != "alrage"] if names == ["all"] else names
    unknown = [n for n in selected if n not in available]
    if unknown:
        raise ValueError(f"Unknown tasks {unknown}; choose from {sorted(available)} or 'all'")
    built = [builders[name]() for name in selected if name != "alrage"]
    if "alrage" in selected or alrage:
        built.append(brg_tasks.alrage(judge=judge_model or ALRAGE_JUDGE_DEFAULT))
    return built


def _najd_model(spec: str):
    if spec.startswith("openai-api/"):
        _, service, model = spec.split("/", 2)
        prefix = service.upper().replace("-", "_")
        api_key_env = f"{prefix}_API_KEY"
        api_base = os.environ.get(f"{prefix}_BASE_URL")
        if not api_base or not os.environ.get(api_key_env):
            raise ValueError(f"Najd requires {api_key_env} and {prefix}_BASE_URL")
        return f"openai/{model}", api_key_env, api_base
    if spec.startswith("openai/"):
        return spec, "OPENAI_API_KEY", os.environ.get("OPENAI_BASE_URL")
    raise ValueError("Najd requires an openai-api/<service>/<model> or openai/<model> spec")


def _run_najd(args):
    project = Path(args.najd_project).resolve()
    if not (project / "pyproject.toml").is_file():
        raise ValueError(f"Najd Arena project not found at {project}; clone najdresearch/najd-arena beside brg")
    model, api_key_env, api_base = _najd_model(args.model)
    command = ["uv", "run", "--project", str(project), "python",
               str(Path(__file__).with_name("najd_run.py").resolve()),
               "--model", model, "--api-key-env", api_key_env,
               "--max-tokens", str(args.max_tokens),
               "--concurrency", str(args.max_connections)]
    if api_base:
        command.extend(["--api-base", api_base])
    if args.limit is not None:
        command.extend(["--sample", str(args.limit)])
    if args.disable_thinking:
        command.append("--disable-thinking")
    for track in args.najd_track:
        command.extend(["--track", track])
    if args.judge_model:
        judge, judge_key_env, judge_base = _najd_model(args.judge_model)
        command.extend(["--judge-model", judge, "--judge-api-key-env", judge_key_env])
        if judge_base:
            command.extend(["--judge-api-base", judge_base])
    else:
        print("Najd open-ended cases remain ungraded without --judge-model.", file=sys.stderr)
    print("Najd results: .najd-arena-v1/runs/", flush=True)
    return subprocess.run(command, check=False).returncode


def _najd_metrics(previous_runs):
    run_root = Path.cwd() / ".najd-arena-v1" / "runs"
    new_runs = set(run_root.iterdir()) - previous_runs if run_root.is_dir() else set()
    if len(new_runs) != 1:
        return {}, None
    run_dir = new_runs.pop()
    report_path = run_dir / "report.json"
    if not report_path.is_file():
        return {}, None
    report = json.loads(report_path.read_text(encoding="utf-8"))
    metrics = {
        f"najd/{name}": value
        for name in ("najd_score", "case_weighted_score", "coverage")
        if (value := report.get(name)) is not None
    }
    metrics.update({f"najd/track/{name}": value for name, value in report.get("tracks", {}).items()})
    return metrics, report_path


def main(argv=None):
    load_environment()
    if os.environ.get("TINKER_OAI_BASE_URL"):
        os.environ["TINKER_BASE_URL"] = os.environ["TINKER_OAI_BASE_URL"]
    parser = argparse.ArgumentParser(prog="brg-eval", description=__doc__,
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True,
                        help="Inspect model spec, e.g. openai/gpt-4o or "
                             "openai-api/<service>/<model>")
    parser.add_argument("--suite", choices=("legacy", "helm", "balsam", "najd", "all"),
                        default="legacy", help="benchmark suite (default: legacy HELM + BALSAM)")
    parser.add_argument("--tasks", default="all",
                        help="comma-separated HELM/BALSAM dataset names or 'all'")
    parser.add_argument("--najd-track", action="append", default=[],
                        help="Najd track to run; repeat for multiple tracks (default: all)")
    parser.add_argument("--najd-project", default="../najd-arena/tui",
                        help="path to the official najd-arena/tui project")
    parser.add_argument("--alrage", action="store_true",
                        help="include the ALRAGE judged task (costs judge API calls)")
    parser.add_argument("--judge-model", default="",
                        help=f"judge model spec for ALRAGE (default {ALRAGE_JUDGE_DEFAULT})")
    parser.add_argument("--limit", type=int, default=None,
                        help="max samples per task (Inspect --limit)")
    parser.add_argument("--max-tokens", type=int, default=57344,
                        help="output-token budget per sample (default: 57344)")
    parser.add_argument("--disable-thinking", action="store_true",
                        help="disable reasoning for Tinker chat models")
    parser.add_argument("--log-dir", default="runs/inspect")
    parser.add_argument("--metrics-file", type=Path, default=None,
                        help="write scalar scores as JSON for recipe trend logging")
    parser.add_argument("--max-connections", type=int, default=16)
    parser.add_argument("--wandb-project", default=os.environ.get("WANDB_PROJECT", ""),
                        help="log evaluation scores to this W&B project")
    parser.add_argument("--wandb-group", default=None,
                        help="group related checkpoints in W&B")
    parser.add_argument("--wandb-step", type=int, default=None,
                        help="training step associated with this checkpoint")
    args = parser.parse_args(argv)

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    if args.max_tokens < 1:
        parser.error("--max-tokens must be positive")
    if args.disable_thinking and not args.model.startswith("openai-api/tinker/"):
        parser.error("--disable-thinking requires an openai-api/tinker/ model")
    if args.max_connections < 1:
        parser.error("--max-connections must be positive")
    if args.suite == "najd" and args.tasks != "all":
        parser.error("use --najd-track to select Najd tracks")
    if args.suite in ("legacy", "helm", "balsam") and args.najd_track:
        parser.error("--najd-track requires --suite najd or --suite all")
    if args.suite in ("balsam", "najd") and args.alrage:
        parser.error("--alrage requires a HELM suite")

    wandb_run = None
    if args.wandb_project:
        import wandb

        wandb_run = wandb.init(
            project=args.wandb_project,
            group=args.wandb_group,
            job_type="evaluation",
            config={"model": args.model, "judge_model": args.judge_model,
                    "suite": args.suite, "tasks": args.tasks, "limit": args.limit,
                    "max_tokens": args.max_tokens,
                    "disable_thinking": args.disable_thinking,
                    "max_connections": args.max_connections,
                    "najd_tracks": args.najd_track},
        )
    try:
        status = 0
        metrics = {}
        helm_scores = []
        if args.suite != "najd":
            from inspect_ai import eval as inspect_eval

            names = [name.strip() for name in args.tasks.split(",") if name.strip()]
            built = _build_tasks(names, args.alrage, args.judge_model, args.suite)
            generation_args = (
                {"extra_body": {"reasoning_effort": False}}
                if args.disable_thinking else {}
            )
            results = inspect_eval(
                built,
                model=args.model,
                limit=args.limit,
                log_dir=args.log_dir,
                max_connections=args.max_connections,
                max_samples=args.max_connections,
                max_tokens=args.max_tokens,
                **generation_args,
            )
            for result in results:
                scores = {
                    metric.name: metric.value
                    for score in (result.results.scores if result.results else [])
                    for metric in score.metrics.values()
                }
                print(f"{result.eval.task}: {scores}")
                metrics.update({f"inspect/{result.eval.task}/{name}": value
                                for name, value in scores.items()})
                primary = scores.get("accuracy", scores.get("mean"))
                if isinstance(primary, (int, float)) and math.isfinite(primary):
                    if result.eval.task.startswith("helm_"):
                        metrics[f"helm/{result.eval.task.removeprefix('helm_')}"] = primary
                        helm_scores.append(primary)
                    elif result.eval.task.startswith("balsam_"):
                        metrics["balsam/score"] = primary
            status = 0 if all(result.status == "success" for result in results) else 1
            if helm_scores:
                metrics["helm/score"] = mean(helm_scores)
        if args.suite in ("najd", "all"):
            run_root = Path.cwd() / ".najd-arena-v1" / "runs"
            previous_runs = set(run_root.iterdir()) if run_root.is_dir() else set()
            status = max(status, _run_najd(args))
            najd_scores, report_path = _najd_metrics(previous_runs)
            metrics.update(najd_scores)
            if isinstance(najd_scores.get("najd/najd_score"), (int, float)):
                metrics["najd/score"] = najd_scores["najd/najd_score"]
            if report_path:
                print(f"Najd report: {report_path}")
                if wandb_run:
                    wandb_run.summary["najd_report"] = str(report_path)
        if wandb_run and metrics:
            wandb_run.log(metrics, step=args.wandb_step)
        if args.metrics_file is not None:
            args.metrics_file.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = args.metrics_file.with_suffix(args.metrics_file.suffix + ".tmp")
            temporary_path.write_text(
                json.dumps({"model": args.model, "suite": args.suite,
                            "status": status, "metrics": metrics}, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary_path.replace(args.metrics_file)
        return status
    finally:
        if wandb_run:
            wandb_run.finish()


if __name__ == "__main__":
    sys.exit(main())
