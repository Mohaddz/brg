"""Launch YAML-configured Tinker SFT and independent checkpoint evaluators."""

import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from brg.recipe import load_recipe


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


def _run(recipe_path, recipe, train_only=False, eval_only=False):
    watchers = []
    trainer = None
    try:
        if not train_only:
            for job in recipe.evals:
                if job.enabled:
                    watchers.append(subprocess.Popen(_watch_command(recipe, job)))
                    print(f"Started {job.name} checkpoint evaluator", flush=True)
        if not eval_only:
            trainer = subprocess.Popen(
                [sys.executable, "-m", "brg.sft_run", "--config", str(recipe_path)]
            )
            print(f"Started SFT: {recipe.name}", flush=True)
            result = trainer.wait()
            if result:
                raise RuntimeError(f"SFT exited with status {result}")
        if watchers:
            print("Training finished; waiting for final checkpoint evaluations", flush=True)
            while watchers:
                for watcher in watchers[:]:
                    result = watcher.poll()
                    if result is not None:
                        watchers.remove(watcher)
                        if result:
                            raise RuntimeError(f"checkpoint evaluator exited with status {result}")
                if watchers:
                    time.sleep(2)
    finally:
        if trainer and trainer.poll() is None:
            trainer.send_signal(signal.SIGTERM)
            trainer.wait()
        for watcher in watchers:
            if watcher.poll() is None:
                watcher.send_signal(signal.SIGTERM)
        for watcher in watchers:
            watcher.wait()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="validate and print the plan only")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--train-only", action="store_true")
    mode.add_argument("--eval-only", action="store_true")
    args = parser.parse_args(argv)
    recipe_path = args.config.resolve()
    recipe = load_recipe(recipe_path)
    print(f"Recipe: {recipe.name}; model: {recipe.model}")
    print(f"SFT: {recipe.data.dataset} -> {recipe.sft.log_dir}; save every {recipe.sft.save_every} steps")
    for job in recipe.evals:
        print(f"Eval: {job.name} ({job.suite}, {','.join(job.tasks)}, "
              f"every {job.every_checkpoints} checkpoints, limit {job.limit}, "
              f"connections {job.max_connections}){' [disabled]' if not job.enabled else ''}")
    if args.check:
        return
    if not args.train_only and not any(job.enabled for job in recipe.evals):
        parser.error("no enabled evaluation jobs; use --train-only or enable one")
    if not args.train_only and not os.environ.get("TINKER_API_KEY"):
        parser.error("TINKER_API_KEY is required for checkpoint evaluation")
    _run(recipe_path, recipe, args.train_only, args.eval_only)


if __name__ == "__main__":
    main()
