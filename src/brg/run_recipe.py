"""Launch YAML-configured Tinker SFT and independent checkpoint evaluators."""

import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace
import yaml

from brg.eval_watch import _command_hash, _eval_command
from brg.env import load_environment
from brg.recipe import load_recipe


def _run_directory(base: Path, eval_only: bool, check: bool) -> Path:
    if eval_only:
        candidates = [(1, base)]
        for path in base.parent.glob(f"{base.name}-v*"):
            suffix = path.name.removeprefix(f"{base.name}-v")
            if suffix.isdigit():
                candidates.append((int(suffix), path))
        existing = [item for item in candidates if (item[1] / "checkpoints.jsonl").is_file()]
        if not existing:
            raise ValueError(f"no existing training run found for {base}")
        return max(existing)[1]

    version = 1
    while True:
        candidate = base if version == 1 else base.with_name(f"{base.name}-v{version}")
        if check:
            if not candidate.exists():
                return candidate
        else:
            try:
                candidate.mkdir(parents=True, exist_ok=False)
                return candidate
            except FileExistsError:
                pass
        version += 1


def _watch_command(recipe, job):
    command = [
        sys.executable, "-m", "brg.eval_watch",
        "--checkpoints", str((recipe.sft.log_dir / "checkpoints.jsonl").resolve()),
        "--output-dir", str((recipe.sft.log_dir / "evals" / job.name).resolve()),
        "--suite", job.suite,
        "--tasks", ",".join(job.tasks),
        "--limit", str(job.limit),
        "--every-checkpoints", str(job.every_checkpoints),
        "--max-connections", str(job.max_connections),
        "--max-evals", str(job.max_evals),
        "--stop-after-final",
        "--wandb-project", recipe.wandb.project or "",
        "--wandb-group", recipe.wandb.group or recipe.name,
    ]
    if job.max_periodic_evals is not None:
        command.extend(["--max-periodic-evals", str(job.max_periodic_evals)])
    if job.alrage:
        command.append("--alrage")
    if job.judge_model:
        command.extend(["--judge-model", job.judge_model])
    if job.suite in ("najd", "all"):
        command.extend(["--najd-project", str(Path(job.najd_project).resolve())])
        for track in job.tracks:
            command.extend(["--najd-track", track])
    return command


def _eval_args(recipe, job):
    return SimpleNamespace(
        suite=job.suite, tasks=",".join(job.tasks), limit=job.limit,
        max_connections=job.max_connections, judge_model=job.judge_model,
        alrage=job.alrage, wandb_project=recipe.wandb.project,
        wandb_group=recipe.wandb.group or recipe.name,
        najd_project=str(Path(job.najd_project).resolve()), najd_track=job.tracks,
        dataset_info=recipe.sft.log_dir / "dataset_info.json",
    )


def _start_base_evaluation(recipe, job):
    output_dir = (recipe.sft.log_dir / "evals" / job.name / "base").resolve()
    command = _eval_command(
        _eval_args(recipe, job), {"sampler_path": recipe.model, "step": 0}, output_dir
    )
    command_hash = _command_hash(command)
    status_path = output_dir / "status.json"
    if status_path.is_file() and (output_dir / "metrics.json").is_file():
        status = json.loads(status_path.read_text(encoding="utf-8"))
        if status.get("returncode") == 0 and status.get("command_hash") == command_hash:
            print(f"Base evaluation already complete: {job.name}", flush=True)
            return None
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = (output_dir / "eval.log").open("w", encoding="utf-8")
    try:
        process = subprocess.Popen(
            command, stdout=log_file, stderr=subprocess.STDOUT,
            env={**os.environ, "INSPECT_DISPLAY": "plain"}, cwd=output_dir,
        )
    except Exception:
        log_file.close()
        raise
    print(f"Started base evaluation: {job.name}", flush=True)
    return process, log_file, output_dir, command_hash


def _finish_base_evaluation(job, returncode):
    _, log_file, output_dir, command_hash = job
    log_file.close()
    status_path = output_dir / "status.json"
    temporary_path = output_dir / "status.json.tmp"
    temporary_path.write_text(
        json.dumps({"step": 0, "returncode": returncode,
                    "command_hash": command_hash}) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(status_path)
    print(f"Base evaluation {'completed' if returncode == 0 else 'failed'}: "
          f"{output_dir / 'eval.log'}", flush=True)


def _collect_metrics(recipe, wandb_run, seen, chart_rows=None):
    enabled_jobs = {job.name: job for job in recipe.evals if job.enabled}
    chart_changed = False
    for status_path in (recipe.sft.log_dir / "evals").glob("*/*/status.json"):
        if status_path.parent.parent.name not in enabled_jobs:
            continue
        if status_path in seen:
            continue
        status = json.loads(status_path.read_text(encoding="utf-8"))
        job = enabled_jobs[status_path.parent.parent.name]
        sampler_path = recipe.model if status_path.parent.name == "base" else status.get("sampler_path")
        if not sampler_path:
            continue
        expected_command = _eval_command(
            _eval_args(recipe, job),
            {"sampler_path": sampler_path, "step": status.get("step")},
            status_path.parent.resolve(),
        )
        if status.get("command_hash") != _command_hash(expected_command):
            continue
        if status.get("returncode") != 0:
            seen.add(status_path)
            continue
        metrics_path = status_path.with_name("metrics.json")
        if not metrics_path.is_file():
            continue
        result = json.loads(metrics_path.read_text(encoding="utf-8"))
        if result.get("status") != 0:
            seen.add(status_path)
            continue
        scores = {
            key: value for key, value in result["metrics"].items()
            if key.startswith(("helm/", "balsam/", "najd/"))
            and isinstance(value, (int, float)) and math.isfinite(value)
        }
        for suite in ("helm", "balsam", "najd"):
            if f"{suite}/score" in scores:
                scores[f"overview/{suite}"] = scores[f"{suite}/score"]
        step = status.get("step")
        if scores and isinstance(step, int):
            for name in scores:
                wandb_run.define_metric(name, step_metric="train_step")
            wandb_run.log({"train_step": step, **scores})
            if chart_rows is not None:
                for suite in ("helm", "balsam", "najd"):
                    if f"overview/{suite}" in scores:
                        chart_rows.setdefault(suite, {})[step] = scores[f"overview/{suite}"]
                        chart_changed = True
            print(f"Logged evaluation trends at step {step}: {status_path.parent}", flush=True)
        seen.add(status_path)
    if chart_changed:
        import wandb

        series = [(suite, sorted(chart_rows[suite].items()))
                  for suite in ("helm", "balsam", "najd") if chart_rows.get(suite)]
        chart = wandb.plot.line_series(
            xs=[[step for step, _ in points] for _, points in series],
            ys=[[score for _, score in points] for _, points in series],
            keys=[suite.upper() for suite, _ in series],
            title="Evaluation scores vs training step",
            xname="Training step",
        )
        wandb_run.log({"overview/score_chart": chart})


def _run(recipe_path, recipe, train_only=False, eval_only=False):
    watchers = []
    base_evaluations = []
    trainer = None
    wandb_run = None
    try:
        if not train_only:
            for job in recipe.evals:
                if job.enabled:
                    watchers.append(subprocess.Popen(_watch_command(recipe, job)))
                    print(f"Started {job.name} checkpoint evaluator", flush=True)
                    if job.evaluate_base:
                        base = _start_base_evaluation(recipe, job)
                        if base is not None:
                            base_evaluations.append(base)
        if not eval_only:
            trainer = subprocess.Popen(
                [sys.executable, "-m", "brg.sft_run", "--config", str(recipe_path)],
                env={**os.environ, "WANDB_RUN_GROUP": recipe.wandb.group or recipe.name},
            )
            print(f"Started SFT: {recipe.name}", flush=True)
        if not train_only and recipe.wandb.project:
            import wandb

            wandb_run = wandb.init(
                project=recipe.wandb.project,
                group=recipe.wandb.group or recipe.name,
                name=f"{recipe.name}-eval-trends",
                job_type="evaluation-trends",
                config={"recipe": recipe.name, "model": recipe.model},
            )
            wandb_run.define_metric("train_step")
        seen = set()
        chart_rows = {}
        training_finished = eval_only
        errors = []
        while not training_finished or watchers or base_evaluations:
            if trainer and not training_finished:
                result = trainer.poll()
                if result is not None:
                    training_finished = True
                    if result:
                        raise RuntimeError(f"SFT exited with status {result}")
                    print("Training finished; waiting for final evaluations", flush=True)
            for base in base_evaluations[:]:
                result = base[0].poll()
                if result is not None:
                    base_evaluations.remove(base)
                    _finish_base_evaluation(base, result)
                    if result:
                        errors.append(f"base evaluation failed: {base[2]}")
            for watcher in watchers[:]:
                result = watcher.poll()
                if result is not None:
                    watchers.remove(watcher)
                    if result:
                        errors.append(f"checkpoint evaluator exited with status {result}")
            if wandb_run:
                _collect_metrics(recipe, wandb_run, seen, chart_rows)
            if not training_finished or watchers or base_evaluations:
                time.sleep(2)
        if wandb_run:
            _collect_metrics(recipe, wandb_run, seen, chart_rows)
        if errors:
            raise RuntimeError("; ".join(errors))
    finally:
        if trainer and trainer.poll() is None:
            trainer.send_signal(signal.SIGTERM)
            trainer.wait()
        for watcher in watchers:
            if watcher.poll() is None:
                watcher.send_signal(signal.SIGTERM)
        for watcher in watchers:
            watcher.wait()
        for base in base_evaluations:
            if base[0].poll() is None:
                base[0].send_signal(signal.SIGTERM)
            base[0].wait()
            base[1].close()
        if wandb_run:
            wandb_run.finish()


def main(argv=None):
    load_environment()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="validate and print the plan only")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--train-only", action="store_true")
    mode.add_argument("--eval-only", action="store_true")
    args = parser.parse_args(argv)
    recipe_path = args.config.resolve()
    recipe = load_recipe(recipe_path)
    if not args.check and not args.train_only and not any(job.enabled for job in recipe.evals):
        parser.error("no enabled evaluation jobs; use --train-only or enable one")
    if not args.check and not args.train_only:
        for variable in ("TINKER_API_KEY", "TINKER_OAI_BASE_URL"):
            if not os.environ.get(variable):
                parser.error(f"{variable} is required for checkpoint evaluation")
        for job in recipe.evals:
            if job.enabled and job.suite in ("najd", "all"):
                if not (Path(job.najd_project).resolve() / "pyproject.toml").is_file():
                    parser.error(f"Najd project not found: {job.najd_project}")
                if job.judge_model and job.judge_model.startswith("openai-api/"):
                    service = job.judge_model.split("/", 2)[1].upper().replace("-", "_")
                    for variable in (f"{service}_API_KEY", f"{service}_BASE_URL"):
                        if not os.environ.get(variable):
                            parser.error(f"{variable} is required for {job.name} judge")
    base_dir = recipe.sft.log_dir
    try:
        run_dir = _run_directory(base_dir, args.eval_only, args.check)
    except ValueError as error:
        parser.error(str(error))
    suffix = run_dir.name.removeprefix(base_dir.name)
    recipe = recipe.model_copy(update={
        "name": f"{recipe.name}{suffix}",
        "sft": recipe.sft.model_copy(update={"log_dir": run_dir}),
    })
    print(f"Recipe: {recipe.name}; model: {recipe.model}")
    print(f"SFT: {recipe.data.dataset} -> {run_dir}; save every {recipe.sft.save_every} steps")
    for job in recipe.evals:
        print(f"Eval: {job.name} ({job.suite}, {','.join(job.tasks)}, "
              f"every {job.every_checkpoints} checkpoints, limit {job.limit}, "
              f"connections {job.max_connections}, base {job.evaluate_base})"
              f"{' [disabled]' if not job.enabled else ''}")
    if args.check:
        return
    if not args.eval_only:
        recipe_path = run_dir / "recipe.yaml"
        recipe_path.write_text(yaml.safe_dump(recipe.model_dump(mode="json")), encoding="utf-8")
    _run(recipe_path, recipe, args.train_only, args.eval_only)


if __name__ == "__main__":
    main()
