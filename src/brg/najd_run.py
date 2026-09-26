"""Run the Najd engine with an explicit model output-token budget."""

import argparse
import asyncio
from pathlib import Path

from najd_arena.engine import run_benchmark
from najd_arena.models import JudgeConfig, ModelConfig, RunConfig


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-base")
    parser.add_argument("--api-key-env")
    parser.add_argument("--max-tokens", type=int, required=True)
    parser.add_argument("--disable-thinking", action="store_true")
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--sample", type=int)
    parser.add_argument("--track", action="append", default=[])
    parser.add_argument("--judge-model")
    parser.add_argument("--judge-api-key-env")
    parser.add_argument("--judge-api-base")
    args = parser.parse_args(argv)
    if args.max_tokens < 1 or args.concurrency < 1:
        parser.error("max tokens and concurrency must be positive")
    if args.judge_model and not args.judge_api_key_env:
        parser.error("--judge-api-key-env is required with --judge-model")

    if args.disable_thinking or args.judge_model:
        from najd_arena import providers

        completion = providers.acompletion

        async def configured_completion(**kwargs):
            if args.disable_thinking and kwargs.get("model") == args.model:
                kwargs["extra_body"] = {
                    **(kwargs.get("extra_body") or {}),
                    "reasoning_effort": False,
                }
            elif args.judge_model and kwargs.get("model") == args.judge_model:
                kwargs["temperature"] = 1.0
            return await completion(**kwargs)

        providers.acompletion = configured_completion

    judge = (
        JudgeConfig(args.judge_model, args.judge_api_key_env, args.judge_api_base)
        if args.judge_model else None
    )
    config = RunConfig(
        model=ModelConfig(
            name=args.model,
            model=args.model,
            api_base=args.api_base,
            api_key_env=args.api_key_env,
            max_tokens=args.max_tokens,
        ),
        judge=judge,
        tracks=tuple(args.track),
        sample=args.sample,
        concurrency=args.concurrency,
    )

    def progress(done, total, case_id):
        print(f"\r{done}/{total} {case_id:60}", end="", flush=True)

    run_id = asyncio.run(run_benchmark(Path.cwd(), config, progress=progress))
    print(f"\n{run_id}")


if __name__ == "__main__":
    main()
