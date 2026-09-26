"""Inspect scorers for brg.

- `helm_mcq`: HELM's output_mapping + exact_match pipeline for arabic_mcqa.
- `balsam`: KSAA-style BLEU / ROUGE-L / fuzzy accuracy (ported from Barq-LLM
  balsam_eval.py, minus the Modal machinery).
- `alrage_judge`: HELM's ALRAGEAnnotator against any Inspect model spec.
"""

from collections import Counter
from difflib import SequenceMatcher
import math
import re

from inspect_ai.scorer import Score, Target, accuracy, mean, scorer
from inspect_ai.solver import TaskState

from brg import helm_spec


# ---------------------------------------------------------------------------
# HELM MCQ scorer
# ---------------------------------------------------------------------------

@scorer(metrics=[accuracy()])
def helm_mcq():
    """First (أ|ب|ج|د|هـ) match in the stripped completion -> mapped text -> EM."""

    async def score(state: TaskState, target: Target) -> Score:
        completion = state.output.completion or ""
        letter = helm_spec.extract_choice(completion)
        choices = state.metadata["choices"]
        gold_index = state.metadata["gold_index"]
        correct = helm_spec.is_correct(completion, gold_index, choices)
        mapped = None
        if letter in helm_spec.AR_LETTERS[: len(choices)]:
            mapped = choices[helm_spec.AR_LETTERS.index(letter)]
        return Score(
            value="C" if correct else "I",
            answer=letter or "",
            explanation=(
                f"gold letter: {helm_spec.AR_LETTERS[gold_index]}; "
                f"mapped: {mapped!r}; gold: {choices[gold_index]!r}"
            ),
            metadata={"letter": letter, "subset": state.metadata.get("subset")},
        )

    return score


# ---------------------------------------------------------------------------
# BALSAM metrics (ported: _normalize/_accuracy/_bleu/_rouge from balsam_eval.py)
# ---------------------------------------------------------------------------


def _normalize(text):
    return " ".join(re.sub(r"[^\w\s]", " ", text.casefold()).split())


def _accuracy(prediction, references):
    pred = _normalize(prediction)
    if not pred:
        return 0.0
    best = 0.0
    for ref in references:
        target = _normalize(ref)
        if not target:
            continue
        ratio = SequenceMatcher(None, target, pred).ratio()
        partial = max(
            (SequenceMatcher(None, target, pred[i : i + len(target)]).ratio()
             for i in range(max(1, len(pred) - len(target) + 1))),
            default=0,
        )
        best = max(best, ratio, partial)
    return float(best >= 0.85)


def _tokens(text):
    return text.split()


def _bleu(prediction, references):
    """Smoothed sentence BLEU with whitespace tokenization, matching KSAA's setup."""
    hyp = _tokens(prediction)
    refs = [_tokens(ref) for ref in references if ref]
    if not hyp or not refs:
        return 0.0
    closest = min(refs, key=lambda ref: (abs(len(ref) - len(hyp)), len(ref)))
    bp = min(1.0, math.exp(1 - len(closest) / len(hyp))) if len(hyp) else 0.0
    logs = []
    for n in range(1, 5):
        hyp_ngrams = Counter(tuple(hyp[i : i + n]) for i in range(max(0, len(hyp) - n + 1)))
        max_ref = Counter()
        for ref in refs:
            counts = Counter(tuple(ref[i : i + n]) for i in range(max(0, len(ref) - n + 1)))
            for gram, count in counts.items():
                max_ref[gram] = max(max_ref[gram], count)
        clipped = sum(min(count, max_ref[gram]) for gram, count in hyp_ngrams.items())
        total = sum(hyp_ngrams.values())
        logs.append(math.log((clipped + 1) / (total + 1)))
    return bp * math.exp(sum(logs) / 4)


def _rouge(prediction, references):
    """Max-reference ROUGE-1/2/L F1 using whitespace tokenization."""
    hyp = _tokens(prediction)
    if not hyp:
        return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}
    best = {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}
    for ref_text in references:
        ref = _tokens(ref_text)
        scores = {}
        for n, name in ((1, "rouge1"), (2, "rouge2")):
            a = Counter(tuple(hyp[i : i + n]) for i in range(max(0, len(hyp) - n + 1)))
            b = Counter(tuple(ref[i : i + n]) for i in range(max(0, len(ref) - n + 1)))
            overlap = sum((a & b).values())
            p = overlap / sum(a.values()) if a else 0.0
            r = overlap / sum(b.values()) if b else 0.0
            scores[name] = 2 * p * r / (p + r) if p + r else 0.0
        prev = [0] * (len(ref) + 1)
        for token in hyp:
            curr = [0]
            for j, other in enumerate(ref, 1):
                curr.append(prev[j - 1] + 1 if token == other else max(prev[j], curr[-1]))
            prev = curr
        lcs = prev[-1]
        p = lcs / len(hyp)
        r = lcs / len(ref) if ref else 0.0
        scores["rougeL"] = 2 * p * r / (p + r) if p + r else 0.0
        best = {key: max(best[key], scores[key]) for key in best}
    return best


def balsam_score(prediction, references, metric):
    metric = metric.lower()
    if metric == "accuracy":
        return {"accuracy": _accuracy(prediction, references)}
    if metric == "bleu":
        return {"bleu": _bleu(prediction, references)}
    if metric == "rouge":
        return _rouge(prediction, references)
    raise ValueError(f"Unsupported BALSAM metric: {metric}")


_PRIMARY = {"bleu": "bleu", "rouge": "rougeL", "accuracy": "accuracy"}


@scorer(metrics=[mean()])
def balsam():
    """Dispatch on each sample's `metric` metadata; primary value is that
    metric's score, all sub-scores go to metadata."""

    async def score(state: TaskState, target: Target) -> Score:
        metric = state.metadata["metric"]
        values = balsam_score(state.output.completion, state.metadata["references"], metric)
        return Score(
            value=values[_PRIMARY[metric]],
            answer=state.output.completion,
            metadata={**values, "metric": metric, "task": state.metadata.get("task")},
        )

    return score


# ---------------------------------------------------------------------------
# ALRAGE judge (alrage_annotator.py port; judge = any Inspect model spec)
# ---------------------------------------------------------------------------

@scorer(metrics=[mean()])
def alrage_judge(judge_model: str):
    """Score 0-1 from an LLM judge, HELM's exact template + parsing.

    `judge_model` is an Inspect model spec, e.g. "openai/gpt-4o-2024-11-20"
    (the official HELM judge) or "openai-api/alrage/<model>" with
    ALRAGE_API_KEY/ALRAGE_BASE_URL env vars for any OpenAI-compatible endpoint.
    """
    from inspect_ai.model import ChatMessageSystem, ChatMessageUser, GenerateConfig, get_model

    try:
        judge = get_model(judge_model, config=GenerateConfig(temperature=0.0, max_tokens=2000))
    except Exception as e:
        raise ValueError(
            f"ALRAGE judge {judge_model!r} failed to initialize ({e}). For "
            "OpenAI-compatible endpoints use judge='openai-api/<service>/<model>' "
            "with <SERVICE>_API_KEY and <SERVICE>_BASE_URL env vars set."
        ) from e

    async def score(state: TaskState, target: Target) -> Score:
        user = helm_spec.ALRAGE_JUDGE_TEMPLATE.format(
            question=state.metadata["question"],
            answer=state.output.completion,
            gold=target.text,
        )
        messages = [
            ChatMessageSystem(content=helm_spec.ALRAGE_JUDGE_SYSTEM),
            ChatMessageUser(content=user),
        ]
        output = await judge.generate(messages)
        response = output.completion
        return Score(
            value=helm_spec.parse_judge_score(response),
            answer=state.output.completion,
            explanation=response,
            metadata={"judge": judge_model, "judge_prompt": user},
        )

    return score
