"""Inspect tasks mirroring the pinned HELM Arabic suite (crfm-helm==0.5.16).

Every MCQ task unions the subsets from run_entries_arabic.conf, caps each
entry at 1000 eval instances (HELM's --max-eval-instances, same np.random
seed-0 sampling), sends the flattened HELM prompt as a single user message,
and decodes deterministically (temperature=0, max_tokens=100).

ALRAGE needs an LLM judge and is opt-in: `inspect eval brg/tasks.py@alrage
-T judge=openai/gpt-4o-2024-11-20` or env BRG_ALRAGE_JUDGE=<model spec>.
"""

import os

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import ChatMessageSystem, ChatMessageUser, GenerateConfig
from inspect_ai.solver import generate

from brg import helm_spec
from brg.scorers import alrage_judge, balsam, helm_mcq

MCQ_CONFIG = GenerateConfig(temperature=0.0, max_tokens=helm_spec.MAX_TOKENS)
BALSAM_CONFIG = GenerateConfig(temperature=0.0, max_tokens=512)


def _mcq_task(family: str, subsets: str = ""):
    want = {s.strip() for s in subsets.split(",") if s.strip()}
    items = helm_spec.family_items(family)
    if want:
        items = [it for it in items if it.subset in want]
    if not items:
        raise ValueError(f"No HELM rows matched family={family} subsets={want or 'all'}")
    samples = [
        Sample(
            id=f"{it.subset}:{it.id}",
            input=helm_spec.mcq_prompt(family, it.input_text, it.choices),
            target=helm_spec.AR_LETTERS[it.gold_index],
            metadata={
                "family": family,
                "subset": it.subset,
                "input_text": it.input_text,
                "choices": [str(c) for c in it.choices],
                "gold_index": it.gold_index,
            },
        )
        for it in items
    ]
    return Task(
        dataset=MemoryDataset(samples, name=f"helm_{family}"),
        solver=generate(),
        scorer=helm_mcq(),
        config=MCQ_CONFIG,
        name=f"helm_{family}",
        version="helm-arabic-0.5.16-port",
    )


@task
def arabic_mmlu(subsets: str = ""):
    return _mcq_task("arabic_mmlu", subsets)


@task
def madinah_qa(subsets: str = ""):
    return _mcq_task("madinah_qa", subsets)


@task
def ht_arabic_mmlu(subsets: str = ""):
    return _mcq_task("mbzuai_human_translated_arabic_mmlu", subsets)


@task
def arabic_exams(subsets: str = ""):
    return _mcq_task("arabic_exams", subsets)


@task
def alghafa(subsets: str = ""):
    return _mcq_task("alghafa", subsets)


@task
def aratrust(subsets: str = ""):
    return _mcq_task("aratrust", subsets)


@task
def alrage(judge: str = ""):
    """Passage-based QA scored by an LLM judge. OFF by default.

    judge: Inspect model spec for the judge. Official HELM uses
    openai/gpt-4o-2024-11-20. Any OpenAI-compatible endpoint works via
    openai-api/<service>/<model> + <SERVICE>_API_KEY/<SERVICE>_BASE_URL,
    or set env BRG_ALRAGE_JUDGE instead of -T judge=...
    """
    judge = judge or os.environ.get("BRG_ALRAGE_JUDGE", "")
    if not judge:
        raise ValueError(
            "ALRAGE is flag-gated: pass -T judge=<inspect-model-spec> "
            "(official HELM judge: openai/gpt-4o-2024-11-20) or set "
            "BRG_ALRAGE_JUDGE. Without it this task refuses to run."
        )
    items = helm_spec.family_items("alrage")
    samples = [
        Sample(
            id=it.id,
            input=helm_spec.alrage_prompt(it.input_text),
            target=it.gold,
            # The judge sees the raw instance input (question + candidates),
            # not the flattened prompt — same as HELM's annotator.
            metadata={"question": it.input_text, "subset": it.subset},
        )
        for it in items
    ]
    return Task(
        dataset=MemoryDataset(samples, name="helm_alrage"),
        solver=generate(),
        scorer=alrage_judge(judge),
        config=MCQ_CONFIG,
        name="helm_alrage",
        version="helm-arabic-0.5.16-port",
    )


_BALSAM_MCQ_SYS = "اختر الخيار الأنسب، وأخرج نص الخيار الصحيح فقط."
_BALSAM_FREE_SYS = "اتبع تعليمات المهمة وأجب مباشرة باللغة المطلوبة."


@task
def balsam_dev(metric: str = ""):
    """Saved BALSAM v2 dev subset (653 rows) from HF, scored per-row metric."""
    import datasets

    ds = datasets.load_dataset(helm_spec.BALSAM_DATASET, split=helm_spec.BALSAM_SPLIT)
    samples = []
    for row in ds:
        if metric and row["metric"] != metric:
            continue
        # Barq protocol: system message depends on whether the row is MCQ-style.
        sys = _BALSAM_MCQ_SYS if row["choices"] else _BALSAM_FREE_SYS
        samples.append(
            Sample(
                id=row["id"],
                input=[ChatMessageSystem(content=sys), ChatMessageUser(content=row["prompt"])],
                target=row["references"][0] if row["references"] else "",
                metadata={
                    "task": row["task"],
                    "task_name": row["task_name"],
                    "metric": row["metric"],
                    "references": list(row["references"]),
                    "choices": list(row["choices"]),
                },
            )
        )
    if not samples:
        raise ValueError(f"No BALSAM rows for metric={metric or 'all'}")
    return Task(
        dataset=MemoryDataset(samples, name=f"balsam_saved_{metric or 'all'}"),
        solver=generate(),
        scorer=balsam(),
        config=BALSAM_CONFIG,
        name=f"balsam_{metric or 'all'}",
        version="barq-balsam-saved-v1",
    )


ALL_TASKS = ["arabic_mmlu", "madinah_qa", "ht_arabic_mmlu", "arabic_exams",
             "alghafa", "aratrust", "balsam_dev"]
