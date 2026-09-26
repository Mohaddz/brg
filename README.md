# brg

Arabic LLM post-training on [Tinker](https://thinkingmachines.ai/tinker/):
fine-tune then RL `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16` on the
Barq Arabic SFT mix, hill-climbing a HELM-faithful Arabic eval suite plus a
saved BALSAM subset. Everything runs locally (WSL) — Tinker is a remote API.

See `plan.md` for the full roadmap and asset inventory.

## Setup

```bash
uv sync                 # core deps: inspect-ai, datasets, numpy, openai
uv sync --group helm    # + pinned crfm-helm==0.5.16 (official runner only)
```

`TINKER_API_KEY` in env for Tinker endpoints.

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
uv run python -m brg.eval_run --model <inspect-model-spec> [--tasks ...] [--limit N]
```

Any OpenAI-compatible endpoint works via Inspect's `openai-api` provider:
`openai-api/<service>/<model>` reads `<SERVICE>_API_KEY` and
`<SERVICE>_BASE_URL` from env.

```bash
# Tinker checkpoint (OpenAI-compatible)
export TINKER_BASE_URL=https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1
export TINKER_API_KEY=...
uv run python -m brg.eval_run \
    --model 'openai-api/tinker/tinker://<run>:train:0/sampler_weights/<step>'

# OpenRouter / DeepInfra / vLLM — same mechanism
export OPENROUTER_API_KEY=...
uv run python -m brg.eval_run --model openai-api/openrouter/qwen/qwen3-32b

# a subset of tasks, small limit for smoke checks
uv run python -m brg.eval_run --model ... --tasks arabic_mmlu,alghafa --limit 100
```

Raw `inspect eval` also works: `uv run inspect eval src/brg/tasks.py@arabic_mmlu --model ...`.
Filter subsets per family with `-T subsets=name1,name2` (conf spelling,
underscores).

### ALRAGE (LLM judge, off by default)

ALRAGE is passage-based QA scored by a judge model — HELM's annotator pins
`openai/gpt-4o-2024-11-20` (0–10 rubric, normalized to 0–1). It's gated behind
a flag so nothing calls a paid judge by accident:

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
