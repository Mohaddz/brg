"""Evaluate Tinker Cookbook checkpoints in a process separate from training."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from brg.env import load_environment


def _checkpoints(path):
    if not path.is_file():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("sampler_path"):
            records.append(record)
    return records


def _checkpoint_id(record):
    digest = hashlib.sha256(record["sampler_path"].encode()).hexdigest()[:12]
    return f"{record.get('name', 'checkpoint')}-{digest}"


def _training_step(record, dataset_info):
    if isinstance(record.get("step"), int):
        return record["step"]
    if record.get("name", "").isdigit():
        return int(record["name"])
    if dataset_info.is_file() and isinstance(record.get("epoch"), int):
        info = json.loads(dataset_info.read_text(encoding="utf-8"))
        step = record["epoch"] * info["steps_per_epoch"] + (record.get("batch") or 0)
        if record.get("name") == "final" and info.get("max_steps") is not None:
            return min(step, info["max_steps"])
        return step
    return record.get("batch")


def _eval_command(args, record, output_dir):
    command = [
        sys.executable, "-m", "brg.eval_run",
        "--model", f"openai-api/tinker/{record['sampler_path']}",
        "--suite", args.suite,
        "--tasks", args.tasks,
        "--limit", str(args.limit),
        "--max-connections", str(args.max_connections),
        "--log-dir", str(output_dir / "inspect"),
        "--metrics-file", str(output_dir / "metrics.json"),
    ]
    if args.judge_model:
        command.extend(["--judge-model", args.judge_model])
    if args.alrage:
        command.append("--alrage")
    if args.wandb_project:
        command.extend(["--wandb-project", args.wandb_project])
        command.extend(["--wandb-group", args.wandb_group])
        step = _training_step(record, args.dataset_info)
        if isinstance(step, int) and step >= 0:
            command.extend(["--wandb-step", str(step)])
    if args.suite in ("najd", "all"):
        command.extend(["--najd-project", args.najd_project])
        for track in args.najd_track:
            command.extend(["--najd-track", track])
    return command


def _command_hash(command):
    return hashlib.sha256("\0".join(command).encode()).hexdigest()[:16]


def _start_evaluation(args, record):
    checkpoint_id = _checkpoint_id(record)
    output_dir = args.output_dir / checkpoint_id
    output_dir.mkdir(parents=True, exist_ok=True)
    command = _eval_command(args, record, output_dir)
    print(f"Evaluating {record['sampler_path']} -> {output_dir}", flush=True)
    log_file = (output_dir / "eval.log").open("w", encoding="utf-8")
    try:
        process = subprocess.Popen(
            command, stdout=log_file, stderr=subprocess.STDOUT,
            env={**os.environ, "INSPECT_DISPLAY": "plain"}, cwd=output_dir,
        )
    except Exception:
        log_file.close()
        raise
    return process, log_file, record, output_dir, _command_hash(command)


def _finish_evaluation(job, returncode, dataset_info):
    _, log_file, record, output_dir, command_hash = job
    log_file.close()
    result = {"sampler_path": record["sampler_path"],
              "step": _training_step(record, dataset_info),
              "returncode": returncode, "command_hash": command_hash}
    status_path = output_dir / "status.json"
    temporary_path = output_dir / "status.json.tmp"
    temporary_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary_path.replace(status_path)
    print(f"{'Completed' if returncode == 0 else 'Failed'} {_checkpoint_id(record)}: {output_dir / 'eval.log'}",
          flush=True)


def _watch(args):
    stopping = False
    final_seen = False
    failed = False

    def request_stop(signum, frame):
        nonlocal stopping
        stopping = True

    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, request_stop)
    seen = set()
    pending = []
    active = []
    selected_periodic = 0
    print(f"Watching {args.checkpoints}; results in {args.output_dir}", flush=True)
    while not stopping or active:
        if not stopping:
            records = _checkpoints(args.checkpoints)
            for index, record in enumerate(records, 1):
                checkpoint_id = _checkpoint_id(record)
                if checkpoint_id in seen:
                    continue
                seen.add(checkpoint_id)
                is_final = record.get("final") or record.get("name") == "final"
                if is_final:
                    final_seen = True
                if not is_final:
                    if index % args.every_checkpoints:
                        continue
                    if (args.max_periodic_evals is not None
                            and selected_periodic >= args.max_periodic_evals):
                        continue
                    selected_periodic += 1
                status_path = args.output_dir / checkpoint_id / "status.json"
                if status_path.is_file():
                    status = json.loads(status_path.read_text(encoding="utf-8"))
                    output_dir = args.output_dir / checkpoint_id
                    command_hash = _command_hash(_eval_command(args, record, output_dir))
                    if status.get("returncode") == 0 and status.get("command_hash") == command_hash:
                        continue
                pending.append(record)
            while pending and len(active) < args.max_evals:
                active.append(_start_evaluation(args, pending.pop(0)))
        finished = False
        for job in active[:]:
            returncode = job[0].poll()
            if returncode is not None:
                active.remove(job)
                _finish_evaluation(job, returncode, args.dataset_info)
                failed = failed or returncode != 0
                finished = True
        if finished and pending and not stopping:
            continue
        if args.stop_after_final and final_seen and not pending and not active:
            break
        if not stopping or active:
            time.sleep(args.poll_seconds)
    return 1 if failed else 0


def main(argv=None):
    load_environment()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoints", type=Path, required=True,
                        help="Tinker Cookbook log directory's checkpoints.jsonl")
    parser.add_argument("--dataset-info", type=Path, default=None,
                        help="trainer metadata for mapping final checkpoint to training step")
    parser.add_argument("--output-dir", type=Path, default=Path("runs/midtrain"))
    parser.add_argument("--suite", choices=("legacy", "helm", "balsam", "najd", "all"),
                        default="helm")
    parser.add_argument("--tasks", default=None)
    parser.add_argument("--najd-track", action="append", default=[])
    parser.add_argument("--najd-project", default="../najd-arena/tui")
    parser.add_argument("--alrage", action="store_true")
    parser.add_argument("--judge-model", default="")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--max-connections", type=int, default=128)
    parser.add_argument("--max-evals", type=int, default=1,
                        help="maximum checkpoint evaluations running at once")
    parser.add_argument("--every-checkpoints", type=int, default=1,
                        help="evaluate every Nth periodic checkpoint and the final checkpoint")
    parser.add_argument("--max-periodic-evals", type=int, default=None,
                        help="cap periodic evaluations; the final checkpoint is always evaluated")
    parser.add_argument("--stop-after-final", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    parser.add_argument("--wandb-project", default=os.environ.get("WANDB_PROJECT", ""))
    parser.add_argument("--wandb-group", default="midtrain")
    args = parser.parse_args(argv)
    if (args.limit < 1 or args.max_connections < 1 or args.max_evals < 1
            or args.every_checkpoints < 1 or args.poll_seconds <= 0
            or (args.max_periodic_evals is not None and args.max_periodic_evals < 0)):
        parser.error("limits, concurrency, and poll interval must be positive")
    if args.tasks is None:
        args.tasks = {"helm": "arabic_mmlu,aratrust", "balsam": "balsam_dev"}.get(
            args.suite, "all"
        )
    if args.suite == "najd" and args.tasks != "all":
        parser.error("use --najd-track to select Najd tracks")
    if args.suite in ("najd", "balsam") and args.alrage:
        parser.error("--alrage requires a HELM suite")
    if args.suite not in ("najd", "all") and args.najd_track:
        parser.error("--najd-track requires --suite najd or --suite all")
    args.checkpoints = args.checkpoints.resolve()
    args.dataset_info = (args.dataset_info or args.checkpoints.parent / "dataset_info.json").resolve()
    args.output_dir = args.output_dir.resolve()
    args.najd_project = Path(args.najd_project).resolve()
    return _watch(args)


if __name__ == "__main__":
    sys.exit(main())
