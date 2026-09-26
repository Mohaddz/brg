# brg

Arabic LLM post-training on [Tinker](https://thinkingmachines.ai/tinker/):
fine-tune then RL `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16` on the
Barq Arabic SFT mix, hill-climbing a HELM-faithful Arabic eval suite plus a
saved BALSAM subset. Everything runs locally (WSL) — Tinker is a remote API.

See `plan.md` for the full roadmap and asset inventory.

## Setup

```bash
uv sync                 # core deps: inspect-ai, datasets, numpy, openai
uv sync --group train   # + pinned Tinker Cookbook for recipe-driven SFT
uv sync --group helm    # + pinned crfm-helm==0.5.16 (official runner only)
```

The `train` and `helm` groups are mutually exclusive because their
dependencies conflict; the normal Inspect evaluation suite is included in
`train`. Create a local secrets file and fill in the keys you use:

```bash
cp .env.example .env
```

`.env` is Git-ignored. The recipe, standalone evaluation, checkpoint watcher,
SFT worker, and official HELM script load it automatically. Existing shell
environment variables take precedence. The full recipe needs Tinker,
OpenRouter, and W&B credentials; `HF_TOKEN` is optional.
`TINKER_BASE_URL` is the SDK training service root; `TINKER_OAI_BASE_URL`
is the OpenAI-compatible inference URL used by evaluations. An old `.env`
with the inference URL in `TINKER_BASE_URL` is corrected automatically.

## Recipe-driven SFT

Edit `configs/sft_pilot.yaml` or `configs/sft_full.yaml` to set the model,
Hugging Face train/validation splits, limits, renderer, LoRA and optimizer
settings, checkpoint cadence, W&B project, and any number of benchmark jobs.
Each job selects a suite and datasets/tracks, samples per task (`limit`),
connections per evaluation, simultaneous checkpoint evaluations (`max_evals`),
and cadence (`every_checkpoints`). `max_periodic_evals` caps periodic checks;
the final checkpoint is always evaluated. `evaluate_base: true` starts the
same benchmark against the unfine-tuned base model at step 0. Set
`enabled: false` to park a job.

```bash
uv run --group train python -m brg.run_recipe --config configs/sft_pilot.yaml --check
uv run --group train python -m brg.run_recipe --config configs/sft_pilot.yaml
```

The launcher starts base-model and checkpoint evaluation workers alongside
training, so the baseline does not hold up SFT. As
soon as an asynchronous sampler checkpoint is saved, workers evaluate it
without blocking the training loop. After training, the launcher waits for
final-checkpoint evaluations. Use `--train-only` or `--eval-only` to run either
side separately. Results live under `sft.log_dir`: `checkpoints.jsonl`,
`evals/<job>/base/eval.log`, `evals/<job>/<checkpoint>/eval.log`, and each
evaluation's `metrics.json` and `inspect/` logs. A restarted worker skips
successful evaluations. W&B training and individual evaluation runs share
the configured project/group. A separate `<recipe>-eval-trends` run charts
the base and checkpoint scores against `train_step`: individual HELM tasks,
HELM's unweighted mean across selected tasks, BALSAM, Najd, and the three
suite headlines under `overview/`, including one combined live line chart.
The mean is a diagnostic, not an official
HELM leaderboard score. Najd's score is canonical only for a complete run.
`eval_every: 0` keeps in-loop validation NLL disabled and skips loading the
validation split; set it positive if you also want synchronous validation
loss, which can pause training at that step.
Periodic Tinker checkpoints expire after the Cookbook's default 7 days, so
do not defer their evaluations indefinitely.

## Eval suite (Inspect)

The Inspect tasks in `src/brg/tasks.py` replicate Stanford HELM Arabic
(`crfm-helm==0.5.16`) as closely as a non-HELM harness can: same datasets at
the same pinned revisions, same prompt layout (Arabic letters أ/ب/ج/د/هـ,
`arabic_mcqa` format instruction), same first-match letter extraction, same
≤1000-instance cap per run entry (np.random seed 0). Deterministic decoding:
temperature 0, max_tokens 100.

| Task | Source | Metric |
| --- | --- | --- |
| `arabic_mmlu` | `MBZUAI/ArabicMMLU` test, 40 subsets | letter accuracy |
| `ht_arabic_mmlu` | `MBZUAI/human_translated_arabic_mmlu` test, 57 subjects | letter accuracy |
| `arabic_exams` | `OALL/Arabic_EXAMS` test, 5 subjects | letter accuracy |
| `alghafa` | `OALL/AlGhafa-Arabic-LLM-Benchmark-Native` test, 9 subsets | letter accuracy |
| `aratrust` | `asas-ai/AraTrust` test, 7 categories | letter accuracy |
| `madinah_qa` | `MBZUAI/MadinahQA` test, 2 subsets | letter accuracy |
| `alrage` | `OALL/ALRAGE` train split (HELM treats it as test) | LLM judge score — **flag-gated** |
| `balsam_dev` | `Mohaddz/barq-balsam-v2-saved-dev-subset` (653 rows) | BLEU / ROUGE-L / fuzzy accuracy |

### Run it

```bash
uv run python -m brg.eval_run --model <inspect-model-spec> [--suite legacy|helm|balsam|najd|all] [--tasks ...] [--limit N]
```

Any OpenAI-compatible endpoint works via Inspect's `openai-api` provider:
`openai-api/<service>/<model>` reads `<SERVICE>_API_KEY` and
`<SERVICE>_BASE_URL` from env.

```bash
# Tinker checkpoint (OpenAI-compatible)
export TINKER_OAI_BASE_URL=https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1
export TINKER_API_KEY=...
uv run python -m brg.eval_run \
    --model 'openai-api/tinker/tinker://<run>:train:0/sampler_weights/<step>'

# OpenRouter / DeepInfra / vLLM — same mechanism
export OPENROUTER_API_KEY=...
uv run python -m brg.eval_run --model openai-api/openrouter/qwen/qwen3-32b

# a subset of tasks, small limit for smoke checks
uv run python -m brg.eval_run --model ... --tasks arabic_mmlu,alghafa --limit 100

# just HELM, just BALSAM, or one dataset
uv run python -m brg.eval_run --model ... --suite helm
uv run python -m brg.eval_run --model ... --suite balsam
uv run python -m brg.eval_run --model ... --suite helm --tasks arabic_mmlu
uv run python -m brg.eval_run --model ... --suite helm --tasks alrage --judge-model openai/gpt-4o-2024-11-20
```

The default `legacy` suite retains the previous HELM plus BALSAM behavior.
`--suite all` also runs Najd. `--limit` caps samples per Inspect task, and is
passed as Najd's sample count when Najd is selected. `--max-connections` sets
both Inspect model connections and concurrent samples, or Najd concurrency.

### Najd Benchmark

Najd uses the [official Najd Arena evaluator](https://github.com/najdresearch/najd-arena)
and its certified dataset, adapters, and scoring. Set it up beside this repo:

```bash
git clone https://github.com/najdresearch/najd-arena.git ../najd-arena
cd ../najd-arena/tui && uv sync
cd ../../brg
```

Then run the full benchmark, a sample, or one track:

```bash
uv run python -m brg.eval_run --model openai-api/openrouter/openai/gpt-6-luna \
    --suite najd --judge-model openai-api/openrouter/openai/gpt-4o-2024-11-20 \
    --max-connections 32
uv run python -m brg.eval_run --model openai-api/openrouter/openai/gpt-6-luna \
    --suite najd --najd-track <track-name> --limit 100
```

The wrapper maps the existing `<SERVICE>_API_KEY` and `<SERVICE>_BASE_URL`
variables to Najd's OpenAI-compatible LiteLLM provider. Najd writes
`.najd-arena-v1/runs/<run-id>/report.json`, plus case-level grades and model
outputs, under the current directory. Track-filtered and sampled runs are
diagnostic; a complete run with a judge is needed for Najd's canonical score.
Use `--najd-project <path>` if the Najd checkout is elsewhere. `--tasks`
selects individual HELM/BALSAM datasets; `--najd-track` selects Najd tracks.

### Tracking and live evaluation

Set `WANDB_PROJECT=brg` (and authenticate with `wandb login`) to log Inspect
scores and Najd's aggregate, coverage, and track scores to W&B. Related
checkpoints can use `--wandb-group <training-run>` and `--wandb-step <step>`.
Each CLI invocation creates one evaluation run. The Tinker cookbook supports
training loss and evaluation logging through `wandb_project` and `wandb_name`
when an SFT entrypoint is configured.

The in-training Inspect bridge in `src/brg/tinker_eval.py` accepts
`max_connections=128` by default. This controls concurrent Tinker sampling
requests during those evaluations; the standalone CLI's
`--max-connections` remains independently configurable.

### Evaluate while SFT continues

For nonblocking mid-training benchmarks, configure the Tinker Cookbook SFT
run with periodic sampler checkpoints (`save_every > 0` and
`async_periodic_saves=True`) and leave its in-loop benchmark evaluators off
(`eval_every=0`, `evaluator_builders=[]`). The cookbook writes each completed
checkpoint to `<sft-log-path>/checkpoints.jsonl`. Start this separate worker
from the `brg` checkout while training runs in another process:

```bash
export TINKER_API_KEY=...
export TINKER_OAI_BASE_URL=https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1
uv run python -m brg.eval_watch --checkpoints runs/sft/<run>/checkpoints.jsonl \
    --suite helm --tasks arabic_mmlu,aratrust --limit 500 \
    --max-connections 128
```

The worker uses each checkpoint's `sampler_path`, evaluates without holding up
the trainer, and keeps results in `runs/midtrain/<checkpoint>/`. Inspect logs
and terminal output are in each checkpoint's `inspect/` and `eval.log`. It
skips successful evaluations after a restart; failed ones retry on restart.
`--max-evals` controls how many checkpoints are evaluated simultaneously
(default 1). Use `--suite najd --tasks all --judge-model ...` for judged Najd
checks. If `WANDB_PROJECT` is set, each checkpoint's scores are logged as a
separate W&B run under the `midtrain` group with its training step.

Raw `inspect eval` also works: `uv run inspect eval src/brg/tasks.py@arabic_mmlu --model ...`.
Filter subsets per family with `-T subsets=name1,name2` (conf spelling,
underscores).

### ALRAGE (LLM judge, off by default)

ALRAGE is passage-based QA scored by a judge model — HELM's annotator pins
`openai/gpt-4o-2024-11-20` (0–10 rubric, normalized to 0–1). It's gated behind
a flag or explicit task selection so nothing calls a paid judge by accident:

```bash
uv run python -m brg.eval_run --model ... --alrage
# judge defaults to openai/gpt-4o-2024-11-20 (uses OPENAI_API_KEY)

# any OpenAI-compatible judge endpoint:
uv run python -m brg.eval_run --model ... --alrage \
    --judge-model 'openai-api/alrage/<judge-model>'
# with ALRAGE_API_KEY + ALRAGE_BASE_URL set

# or via inspect directly:
uv run inspect eval src/brg/tasks.py@alrage --model ... -T judge=openai/gpt-4o-2024-11-20
# env alternative: BRG_ALRAGE_JUDGE=<model-spec>
```

## Official HELM numbers

Inspect scores are for hill-climbing, not leaderboard claims. For official
numbers, `scripts/helm_arabic.py` runs the pinned `crfm-helm==0.5.16` runner
locally against `references/helm-arabic-v0.5.16/` (the model must be
registered in HELM, and `OPENAI_API_KEY` is required for the ALRAGE judge):

```bash
uv run --group helm python scripts/helm_arabic.py --check
OPENAI_API_KEY=... uv run --group helm python scripts/helm_arabic.py \
    --model openai/gpt-4o --run-id <unique-id> --live
```

Outputs land in `runs/helm-arabic/<run-id>/`.

## Layout

```
src/brg/
  helm_spec.py    # HELM port: conf parsing, pinned-revision loaders,
                  #   prompt builders, answer extraction, judge template
  scorers.py      # helm_mcq / balsam / alrage_judge Inspect scorers
  tasks.py        # Inspect task definitions
  eval_run.py     # CLI over the suite
  tinker_eval.py  # mid-training evaluator bridge (SamplingClient)
references/helm-arabic-v0.5.16/   # pinned run_entries conf + schema
scripts/helm_arabic.py            # official runner (helm dep group)
runs/                             # logs + eval outputs (gitignored)
```
