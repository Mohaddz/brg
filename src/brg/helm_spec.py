"""HELM-faithful Arabic scenario + adapter ports from crfm-helm==0.5.16.

These functions replicate Stanford's `helm-run` behavior for the entries in
references/helm-arabic-v0.5.16/run_entries_arabic.conf as closely as a
non-HELM harness can:

- same HF datasets at the same pinned revisions
- same row -> instance conversion (context joining, option filtering,
  category/subject filtering, "ا" -> "أ" answer normalization, ...)
- same prompt layout: instructions block + `input_noun:` input + Arabic-letter
  references + `output_noun:` prompt, joined like `adapter_spec.instance_prefix`
- same answer extraction: first regex match of `(أ|ب|ج|د|هـ)` anywhere in the
  stripped completion, mapped letter -> reference text, then exact match
- same <=1000-eval-instance cap per run entry using np.random.seed(0) +
  np.random.choice (runner.downsample_eval_instances)

Remaining differences vs. official numbers: HELM's window truncation, its
token-level plumbing/logprobs, and provider-specific request details. Treat
results as hill-climbing metrics; use scripts/helm_arabic.py for official ones.

Source-of-truth files ported:
  helm/benchmark/run_specs/arabic_run_specs.py
  helm/benchmark/adaptation/common_adapter_specs.py (MCQ joint + generation)
  helm/benchmark/adaptation/adapters/multiple_choice_joint_adapter.py
  helm/benchmark/adaptation/adapters/in_context_learning_adapter.py (Prompt)
  helm/benchmark/run_expander.py (OutputFormatInstructions "arabic_mcqa")
  helm/benchmark/metrics/evaluate_reference_metrics.py (output mapping)
  helm/benchmark/runner.py (downsample_eval_instances)
  helm/benchmark/scenarios/{arabic_mmlu,mbzuai_human_translated_arabic_mmlu,
    arabic_exams,alghafa,aratrust,madinah_qa,alrage}_scenario.py
  helm/benchmark/annotation/alrage_annotator.py
"""

from dataclasses import dataclass
import re
from pathlib import Path

import numpy as np

CONF_PATH = Path(__file__).resolve().parents[2] / "references" / "helm-arabic-v0.5.16" / "run_entries_arabic.conf"

# ---------------------------------------------------------------------------
# Adapter constants (arabic_run_specs.py + adapter defaults)
# ---------------------------------------------------------------------------

# _ARABIC_REFERENCE_PREFIX_CHARACTERS
AR_LETTERS = ["أ", "ب", "ج", "د", "هـ"]
# _ARABIC_OUTPUT_MAPPING_PATTERN
OUTPUT_PATTERN = re.compile(r"(أ|ب|ج|د|هـ)")

INPUT_NOUN = "السؤال"
OUTPUT_NOUN = "الإجابة"

# OutputFormatInstructions("arabic_mcqa") text, prepended to instructions.
FORMAT_INSTRUCTIONS = "اكتب حرف الإجابة فقط، دون أي إضافات أخرى."

MCQ_INSTRUCTIONS = {
    "arabic_mmlu": "السؤال التالي هو سؤال متعدد الإختيارات. اختر الإجابة الصحيحة",
    "madinah_qa": "السؤال التالي هو سؤال متعدد الإختيارات. اختر الإجابة الصحيحة",
    "mbzuai_human_translated_arabic_mmlu": "السؤال التالي هو سؤال متعدد الإختيارات. اختر الإجابة الصحيحة",
    "arabic_exams": "السؤال التالي هو سؤال متعدد الإختيارات. اختر الإجابة الصحيحة",
    "alghafa": "الأسئلة التالية هي أسئلة متعددة الإختيارات مع الجواب الصحيح",
    "aratrust": "الأسئلة التالية هي أسئلة متعددة الإختيارات مع الجواب الصحيح",
}
ALRAGE_INSTRUCTIONS = "بناءً على السياقات المقترحة التالية، اجب عن السؤال التالي"

# HELM: --max-eval-instances 1000
MAX_EVAL_PER_ENTRY = 1000
# HELM: temperature=0.0, max_tokens=100 for both MCQ joint and ALRAGE.
MAX_TOKENS = 100

DATASET_REVS = {
    "arabic_mmlu": ("MBZUAI/ArabicMMLU", "7aa530e2893ac420352b3f5c1a1310c010e9758b"),
    "madinah_qa": ("MBZUAI/MadinahQA", "62e7c86ac5c07245a5a952722691d77ddb41f695"),
    "mbzuai_human_translated_arabic_mmlu": (
        "MBZUAI/human_translated_arabic_mmlu",
        "5ed7830fd678cfa6f2d7f0a1a13a4e1a1fa422ac",
    ),
    "arabic_exams": ("OALL/Arabic_EXAMS", "bc7a29346dbcaa16a8cd883b1f3e681ab2b7ff2a"),
    "alghafa": ("OALL/AlGhafa-Arabic-LLM-Benchmark-Native", "a31ebd34ca311d7e0cfc6ad7f458b3435af280f5"),
    "aratrust": ("asas-ai/AraTrust", "d4dd124ed5b90aeb65a7dda7d88e34fb464a31ec"),
    "alrage": ("OALL/ALRAGE", "4827b2ed2436aea578e84d9bd4150b66ab8bbe0e"),
}

BALSAM_DATASET = "Mohaddz/barq-balsam-v2-saved-dev-subset"
BALSAM_SPLIT = "validation"


@dataclass
class MCQItem:
    """One normalized HELM instance: input text + ordered choice texts."""

    id: str
    input_text: str            # Instance.input.text (no prefixes)
    choices: list              # reference output texts, in order
    gold_index: int            # index into choices of the correct reference
    subset: str


@dataclass
class GenItem:
    id: str
    input_text: str            # Instance.input.text (already contains labels)
    gold: str
    subset: str


# ---------------------------------------------------------------------------
# Run-entry parsing (the conf file is the source of truth for subsets)
# ---------------------------------------------------------------------------

_ENTRY_RE = re.compile(r'\{description:\s*"([^"]+)"')


def run_entries(conf_path: Path = CONF_PATH) -> dict:
    """Parse run_entries_arabic.conf -> {family: [args dict, ...]}.

    Mirrors the pinned conf exactly; e.g.
    {"arabic_mmlu": [{"subset": "Accounting_(University)"}, ...], "alrage": [{}]}
    """
    text = Path(conf_path).read_text(encoding="utf-8")
    entries = {}
    for desc in _ENTRY_RE.findall(text):
        family, _, argstr = desc.partition(":")
        args = {}
        for part in filter(None, (p.strip() for p in argstr.split(","))):
            key, _, value = part.partition("=")
            args[key.strip()] = value.strip()
        entries.setdefault(family, []).append(args)
    return entries


# ---------------------------------------------------------------------------
# Prompt construction (Prompt.text + construct_example_prompt semantics)
# ---------------------------------------------------------------------------

def _instructions_block(family: str) -> str:
    # get_multiple_choice_*_adapter_spec does format_instructions (+\n),
    # then OutputFormatInstructions prepends its text + "\n\n".
    return f"{FORMAT_INSTRUCTIONS}\n\n{MCQ_INSTRUCTIONS[family]}\n"


def mcq_prompt(family: str, input_text: str, choice_texts: list) -> str:
    """Full flattened prompt HELM would send as a single user message."""
    block = f"{INPUT_NOUN}: {input_text}\n"
    for i, text in enumerate(choice_texts):
        block += f"{AR_LETTERS[i]}. {text}\n"
    block += f"{OUTPUT_NOUN}:"  # output_prefix.rstrip()
    # Prompt.text joins blocks with instance_prefix "\n".
    return _instructions_block(family) + "\n" + block


def alrage_prompt(input_text: str) -> str:
    # get_generation_adapter_spec: input_prefix "السؤال: ", input_suffix "\n",
    # output_prefix "الإجابة: " (rstripped), instructions get trailing "\n".
    block = f"{INPUT_NOUN}: {input_text}\n{OUTPUT_NOUN}:"
    return f"{ALRAGE_INSTRUCTIONS}\n\n{block}"


# ---------------------------------------------------------------------------
# Answer extraction (evaluate_reference_metrics + output_mapping)
# ---------------------------------------------------------------------------

def extract_choice(completion: str):
    """HELM's pipeline: strip, first (أ|ب|ج|د|هـ) regex match, or None."""
    if not completion:
        return None
    match = OUTPUT_PATTERN.search(completion.strip())
    return match.group(1) if match else None


def is_correct(completion: str, gold_index: int, choices: list) -> bool:
    """Letter -> mapped reference text -> exact match vs gold reference text."""
    letter = extract_choice(completion)
    if letter is None or letter not in AR_LETTERS[: len(choices)]:
        return False
    mapped = choices[AR_LETTERS.index(letter)]
    return str(mapped).strip() == str(choices[gold_index]).strip()


# ---------------------------------------------------------------------------
# Downsampling (runner.downsample_eval_instances: np.random.seed(0) + choice)
# ---------------------------------------------------------------------------

def downsample(items: list, cap: int = MAX_EVAL_PER_ENTRY) -> list:
    if len(items) <= cap:
        return items
    np.random.seed(0)
    idx = np.random.choice(len(items), cap, replace=False)
    return [items[i] for i in idx]


# ---------------------------------------------------------------------------
# Scenario loaders (one per family, per run-entry args)
# ---------------------------------------------------------------------------

def _load(repo, revision, config=None, split="test"):
    import datasets

    kwargs = {"revision": revision}
    if config is not None:
        kwargs["name"] = config
    return datasets.load_dataset(repo, split=split, **kwargs)


def _context_input(row):
    context = row.get("Context")
    question = row["Question"]
    if context and isinstance(context, str) and context.strip():
        return f"{context}\n\n{question}"
    return question


def _options_1_to_5(row):
    choices = []
    for i in range(1, 6):
        value = row.get(f"Option {i}")
        if not value:
            continue
        choices.append(str(value))
    return choices


def load_arabic_mmlu(subset: str) -> list:
    repo, rev = DATASET_REVS["arabic_mmlu"]
    ds = _load(repo, rev, config=subset.replace("_", " "))
    items = []
    for i, row in enumerate(ds):
        choices = _options_1_to_5(row)
        gold = ord(row["Answer Key"]) - ord("A")
        items.append(MCQItem(f"id{i}", _context_input(row), choices, gold, subset))
    return items


def load_madinah_qa(subset: str) -> list:
    repo, rev = DATASET_REVS["madinah_qa"]
    ds = _load(repo, rev, config=subset.replace("_", " "))
    items = []
    for i, row in enumerate(ds):
        choices = _options_1_to_5(row)
        gold = ord(row["Answer Key"]) - ord("A")
        items.append(MCQItem(f"id{i}", _context_input(row), choices, gold, subset))
    return items


def load_ht_mmlu(subject: str) -> list:
    repo, rev = DATASET_REVS["mbzuai_human_translated_arabic_mmlu"]
    ds = _load(repo, rev, config=subject)
    items = []
    for i, row in enumerate(ds):
        items.append(
            MCQItem(f"id-{subject}-{i}", row["question"], list(row["choices"]), int(row["answer"]), subject)
        )
    return items


def load_arabic_exams(subject: str) -> list:
    repo, rev = DATASET_REVS["arabic_exams"]
    ds = _load(repo, rev)
    want = subject.replace("_", " ")
    items = []
    for row in ds:
        if row["id"].split("-")[0] != want:
            continue
        if row["answer"] not in ("A", "B", "C", "D"):
            continue  # HELM hwarn + skip
        choices = [row[c] for c in "ABCD"]
        items.append(MCQItem(row["id"], row["question"], choices, "ABCD".index(row["answer"]), subject))
    return items


def load_alghafa(subset: str) -> list:
    repo, rev = DATASET_REVS["alghafa"]
    ds = _load(repo, rev, config=subset)
    # HELM derives option indexes from the FIRST row's keys, in column order.
    sol_indexes = [
        int(k.removeprefix("sol")) for k in ds[0].keys() if k.startswith("sol")
    ]
    items = []
    for i, row in enumerate(ds):
        choices = [row[f"sol{j}"] for j in sol_indexes]
        # HELM: correct when option_index == int(label) + 1, where option_index
        # is the sol suffix -> position of (label + 1) inside sol_indexes.
        gold = sol_indexes.index(int(row["label"]) + 1)
        items.append(MCQItem(f"id{i}_test", row["query"], choices, gold, subset))
    return items


_ARATRUST_PREFIX = ["أ", "ب", "ج"]


def load_aratrust(category: str) -> list:
    repo, rev = DATASET_REVS["aratrust"]
    ds = _load(repo, rev)
    want = category.replace("_", " ")
    items = []
    for i, row in enumerate(ds):
        if row["Category"] != want:
            continue
        raw = [row[k] for k in "ABC" if row[k]]
        for j, text in enumerate(raw):
            assert text.strip().startswith(f"{_ARATRUST_PREFIX[j]})"), raw
        choices = [t.split(")", maxsplit=1)[1].strip() for t in raw]
        answer = row["Answer"].strip()
        if answer == "ا":
            answer = "أ"
        gold = _ARATRUST_PREFIX.index(answer)
        items.append(MCQItem(f"id{i}", row["Question"], choices, gold, category))
    return items


def load_alrage() -> list:
    repo, rev = DATASET_REVS["alrage"]
    ds = _load(repo, rev, split="train")  # scenario maps train -> TEST_SPLIT
    items = []
    for row in ds:
        text = f"السؤال:\n{row['question']}\n\nالسياقات المقترحة:\n{row['candidates']}\n"
        items.append(GenItem(row["id"], text, row["gold_answer"], "alrage"))
    return items


MCQ_LOADERS = {
    "arabic_mmlu": ("subset", load_arabic_mmlu),
    "madinah_qa": ("subset", load_madinah_qa),
    "mbzuai_human_translated_arabic_mmlu": ("subject", load_ht_mmlu),
    "arabic_exams": ("subject", load_arabic_exams),
    "alghafa": ("subset", load_alghafa),
    "aratrust": ("category", load_aratrust),
}


def family_items(family: str, conf_path: Path = CONF_PATH) -> list:
    """All HELM run-entry rows for a family, each entry capped at 1000."""
    if family == "alrage":
        return downsample(load_alrage())
    arg_key, loader = MCQ_LOADERS[family]
    items = []
    for args in run_entries(conf_path)[family]:
        items.extend(downsample(loader(args[arg_key])))
    return items


# ---------------------------------------------------------------------------
# ALRAGE judge prompt (alrage_annotator.py, verbatim)
# ---------------------------------------------------------------------------

ALRAGE_JUDGE_SYSTEM = """أنت مقيّم محايد خبير باللغة العربية. يجب عليك:
        1. تقييم دقة الإجابة مقارنة بالإجابة الصحيحة
        2. التحقق من أن الإجابة مدعومة بالسياق المقدم
        3. تقييم جودة وشمولية الإجابة

        مهم جداً: يجب أن يكون ردك رقماً فقط من 0 إلى 10. لا تضف أي نص أو تفسير."""

ALRAGE_JUDGE_TEMPLATE = """السؤال: {question}

        الإجابة المقدمة: {answer}

        الإجابة الصحيحة: {gold}

        أعط تقييماً من 0 إلى 10:
        0-2: إجابة خاطئة تماماً
        3-4: إجابة جزئية مع أخطاء
        5-6: إجابة متوسطة
        7-8: إجابة جيدة
        9-10: إجابة ممتازة

        اكتب رقماً فقط من 0 إلى 10 بدون أي نص إضافي:"""

# Official HELM judge model (alrage_annotator._ANNOTATOR_MODEL).
ALRAGE_JUDGE_DEFAULT = "openai/gpt-4o-2024-11-20"


def parse_judge_score(response: str) -> float:
    """First numeric token /10 clamped to [0,1]; parse failure -> 0.0 (HELM)."""
    try:
        score = float(next(n for n in response.split() if n.replace(".", "", 1).isdigit()))
        return min(max(score / 10.0, 0.0), 1.0)
    except Exception:
        return 0.0
