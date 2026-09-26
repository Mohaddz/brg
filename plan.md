# brg — Arabic LLM post-training on Tinker

Fine-tune then RL `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16` (30B MoE /
3B active, 64K ctx) on the curated Barq Arabic SFT mix, and hill-climb HELM
Arabic + a saved BALSAM subset. Everything runs locally (WSL) — Tinker is a
remote API, no Modal or GPU needed.

## Assets that already exist

| Asset | Where | Notes |
| --- | --- | --- |
| SFT data | `Mohaddz/barq-arabic-sft-candidate` (HF, public) | 78,497 train / 30,149 val rows. `messages` chat format + provenance/`token_count`/`metadata.rendering` fields. 1,178 held rows not published. |
| HELM Arabic spec | `Barq-LLM/references/helm-arabic-v0.5.16/` | `run_entries_arabic.conf` + `schema_arabic.yaml`, pinned to `crfm-helm==0.5.16`. 7 families, ~121 entries, zero-shot, `arabic_mcqa` format, ≤1000 instances each. |
| BALSAM subset | `Mohaddz/barq-balsam-v2-saved-dev-subset` (HF) | 653 rows, `validation` split: `prompt`, `references`, `choices`, `metric` ∈ {bleu, rouge, accuracy}. |
| Scorers to port | `Barq-LLM/src/barq/baseline_eval.py` (`extract_answer`, MCQ prompt builder) and `balsam_eval.py` (`_bleu`, `_rouge`, `_accuracy`) | ~150 lines total. Drop the Modal/provenance machinery. |
| Eval harness | `Barq-LLM/src/barq/inspect_eval.py` | Same pattern, simplified: load straight from HF instead of a frozen Modal bundle. |

## Repo layout (target: small, readable)

```
brg/
  plan.md
  pyproject.toml          # uv project; deps: inspect-ai, datasets, numpy, openai
                          #   (tinker, tinker-cookbook to be added with training)
                          #   dep group `helm`: crfm-helm==0.5.16 for official runs
  references/
    helm-arabic-v0.5.16/  # pinned run_entries_arabic.conf + schema_arabic.yaml
  scripts/
    helm_arabic.py        # local official runner: --check / --live (helm group)
  src/brg/
    helm_spec.py          # faithful port: conf parsing, per-family loaders at
                          #   pinned revisions, HELM prompt builders, extraction
    scorers.py            # helm_mcq, balsam (bleu/rouge/fuzzy-acc), alrage_judge
    tasks.py              # Inspect tasks: HELM Arabic families + balsam subset
    eval_run.py           # thin CLI: run the Inspect suite against any model endpoint
    tinker_eval.py        # bridge: run inspect tasks on the loop's SamplingClient
    data.py               # HF SFT candidate -> normalized conversations + train/val builders (TODO)
    sft.py                # tinker_cookbook supervised train config + entrypoint (TODO)
    rl.py                 # RLDataset + ProblemEnv with verifiable MCQ/format rewards (TODO)
  runs/                   # local logs, checkpoints manifest, eval outputs (gitignored)
```

## Evaluation design

One Inspect suite, three ways to point it at a model:

1. **Tinker checkpoints** — Tinker exposes an OpenAI-compatible endpoint:
   `https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1` with
   model name = `tinker://<run>:train:0/sampler_weights/<step>`. Run through
   Inspect's `openai-api` provider (`<SERVICE>_BASE_URL` + `<SERVICE>_API_KEY`,
   or `OPENAI_BASE_URL`/`OPENAI_API_KEY`). Verify exact model-string quoting
   during implementation.
2. **Any external OpenAI-compatible endpoint** (OpenRouter, DeepInfra, vLLM…)
   — same provider mechanism, per-endpoint env vars.
3. **Mid-training** — Tinker writes periodic sampler checkpoints; a separate
   `brg.eval_watch` process picks them up and runs the selected Inspect/Najd
   benchmarks while SFT continues. The in-loop `tinker_evaluator` bridge
   remains available for focused diagnostics.

Task list (all zero-shot, deterministic decoding, matching HELM's protocol):

| Task | Source | Rows | Metric |
| --- | --- | --- | --- |
| `arabic_mmlu` | `MBZUAI/ArabicMMLU` test | ≤1000/subset-sample | letter accuracy |
| `ht_mmlu` | `MBZUAI/human_translated_arabic_mmlu` | same | letter accuracy |
| `arabic_exams` | `OALL/Arabic_EXAMS` test | same | letter accuracy |
| `alghafa` | `OALL/AlGhafa-Arabic-LLM-Benchmark-Native` | same | letter accuracy |
| `aratrust` | AraTrust (pin repo per HELM run spec) | same | letter accuracy |
| `madinah_qa` | `MBZUAI/MadinahQA` | same | letter accuracy |
| `alrage` | `OALL/ALRAGE` | same | judged score; judge default = `openai/gpt-4o-2024-11-20` (HELM's pinned annotator model — confirmed in `alrage_annotator.py`, schema says "judged by GPT-4o"); flag-gated, any Inspect model spec / OpenAI-compatible endpoint |
| `balsam_*` | `Mohaddz/barq-balsam-v2-saved-dev-subset` | 653 | BLEU / ROUGE-L / fuzzy accuracy |

Caveats to keep honest: Inspect ports on the same datasets are *not* official
HELM leaderboard numbers, though `helm_spec.py` now replicates HELM's actual
adapters: same pinned dataset revisions, same prompt layout (Arabic letters
أ/ب/ج/د/هـ, `arabic_mcqa` format instruction), same first-match letter
extraction, same ≤1000/entry subsample (np.random seed 0). For official
numbers, `scripts/helm_arabic.py` runs the pinned `crfm-helm==0.5.16` conf
locally (`uv run --group helm ...`). ALRAGE is the only family needing an LLM
judge — implemented behind `--alrage`, judge configurable via any
OpenAI-compatible endpoint (`openai-api/<service>/<model>` + env vars).

## Training plan

### Step 0 — env + smoke checks
- `uv` project; `TINKER_API_KEY` in env. Pin `tinker-cookbook` (≥0.5.5; verify
  `InspectEvaluatorBuilder` still exists, else use the SamplingClient bridge).
- Confirm renderer via `tinker_cookbook.model_info.get_recommended_renderer_name`
  (Barq used `nemotron3_ultra`).
- `data.py`: stream the HF dataset, normalize `messages` (handle optional
  `reasoning_content`, `tools`, per-row `metadata.rendering.enable_thinking`),
  emit clean `{messages: [...]}` train/val JSONL for `FromConversationFileBuilder`
  or a small custom `ChatDatasetBuilder`.
- Dry-run eval suite end-to-end on the base model with tiny limits.

### Step 1 — SFT pilot (~10k rows)
- `sft.py` wrapping `tinker_cookbook.supervised.train.main(Config)`:
  - `dataset_builder` over the train JSONL; val = subsample of the 30,149-row
    validation split (~512–1024 rows is plenty for a loss curve).
  - `lora_rank` 32, `learning_rate` from `hyperparam_utils.get_lr`, batch_size
    ~128 conversations, `max_length` sized from `token_count` distribution.
  - `save_every` sized so a checkpoint lands roughly every ~5k examples
    (≈ every 39 steps at bs=128), with `async_periodic_saves=True`.
    Keep in-loop benchmark evaluators disabled; run a fixed small Inspect
    subset from `brg.eval_watch` (limit ~100–500/task).
- Purpose: validate pipeline, rendering, eval wiring, and the loss curve.

### Step 2 — full SFT (78,497 rows, 1 epoch to start)
- Same config, `train_limit=None`. Checkpoints every ~5k rows act as the
  "stop early" points — inspect val loss + benchmark deltas at each and kill
  when flat. Resume = start a new run from the last `tinker://` state
  checkpoint rather than re-running.
- Budget sanity: ~40–80M training tokens/epoch × ~$0.44/M ≈ $18–35/epoch
  (verify against current pricing).

### Step 3 — checkpoint selection
- Run the full Inspect suite against each candidate checkpoint via the
  OpenAI-compatible endpoint. Track in `runs/` (step → per-task scores).
- Pick best on val loss + HELM-family + BALSAM aggregate; that checkpoint is
  the RL starting point (and the SFT deliverable).

### Step 4 — RL
- `rl.py` using `tinker_cookbook.rl`: `ProblemEnv` per prompt, reward =
  `extract_answer` match for MCQ-style rows (start with verifiable rewards
  only; BALSAM BLEU reward is a later option, it's noisier).
- Prompts: train-split rows with short verifiable answers, eval-benchmark rows
  excluded (the same NFC/shingle overlap check exists in `balsam_eval.py` if
  needed).
- Groups of 8–16 samples/prompt, `importance_sampling` or `cispo` loss, KL to
  the SFT checkpoint, same periodic Inspect eval cadence.

### Step 5 — compare & iterate
- Base vs SFT vs RL vs external endpoints, all through the same suite.
- Hill-climb loop: adjust data mix/LR/RL rewards from per-family deltas.

## Open questions (decide while implementing)

1. ~~Include ALRAGE now?~~ Done — behind `--alrage`; judge defaults to
   `openai/gpt-4o-2024-11-20` (HELM's pinned judge), any Inspect model spec
   works via `-T judge=` / `BRG_ALRAGE_JUDGE`.
2. Eval batch limits for mid-training checks — fixed 100–200/task vs full?
3. `enable_thinking`: dataset is marked `false` — keep thinking off
   everywhere, or train a thinking variant later?
4. Second epoch / continue past 80k only if val loss still improving?
