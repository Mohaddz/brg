"""Shared planning, evidence validation and dataset compatibility helpers."""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from _paths import ROOT, CONFIGS, REFERENCES


import hashlib
import json
import math
import random
import re
import statistics
from urllib.parse import unquote
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class OutputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FirstUser(OutputModel):
    text: str = Field(min_length=1)
    scenario: str = Field(min_length=1)


class UserTurn(OutputModel):
    action: Literal["message", "stop"]
    text: str
    scenario: str

    @model_validator(mode="after")
    def valid_decision(self):
        if (self.action == "message") != bool(self.text.strip()):
            raise ValueError("continuation needs a user message; stopping needs empty text")
        if self.action == "message" and not self.scenario.strip():
            raise ValueError("continuation needs a concrete scenario")
        return self


class Answer(OutputModel):
    text: str = Field(min_length=1)

    @model_validator(mode="after")
    def nonblank(self):
        if not self.text.strip():
            raise ValueError("blank answer")
        return self


class Review(OutputModel):
    natural_user: bool
    context_consistent: bool
    draft_acceptable: bool
    enhanced_acceptable: bool
    preferred: Literal["draft", "enhanced", "neither"]
    draft_completeness: int = Field(ge=1, le=5)
    enhanced_completeness: int = Field(ge=1, le=5)
    enhanced_adds_value: bool
    unnecessary_padding: bool
    unsupported_claims: list[str]
    issues: list[str]
    style_notes: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=1)


def screen_review(review):
    """Keep conflicting judgments as data, never select an unacceptable answer."""
    issues = list(review["issues"]) + list(review["unsupported_claims"])
    chosen = review["preferred"]
    if chosen != "neither" and not review[chosen + "_acceptable"]:
        issues.append(f"inconsistent review: preferred {chosen} marked unacceptable")
        chosen = "neither"
    if not review["natural_user"]:
        issues.append("unnatural user")
    if not review["context_consistent"]:
        issues.append("context inconsistency")
    if chosen == "neither":
        issues.append("no acceptable selected answer")
    return chosen, issues


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def atomic_json(path, value):
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def allocate(count, weighted):
    total = sum(weighted.values())
    if not total or any(weight < 0 for weight in weighted.values()):
        raise ValueError("nonnegative weights with positive total required")
    exact = {key: count * weight / total for key, weight in weighted.items()}
    result = {key: math.floor(value) for key, value in exact.items()}
    order = sorted(exact, key=lambda key: (-(exact[key] - result[key]), key))
    for key in order[:count - sum(result.values())]:
        result[key] += 1
    return result


def load_inputs(config_path):
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    references = read_json(config_path.parent / config["references"])
    sources = read_json(config_path.parent / config["sources"])
    if references.get("schema_version") != 1 or not references.get("references"):
        raise ValueError("empty/unknown reference library")
    if len({ref["id"] for ref in references["references"]}) != len(references["references"]):
        raise ValueError("duplicate reference ID")
    for ref in references["references"]:
        if ref["review_status"] != "agent_style_reviewed" or ref["role"] != "style_only_not_factual_evidence":
            raise ValueError("unreviewed reference or reference used as factual evidence")
    if len({source["source_id"] for source in sources}) != len(sources):
        raise ValueError("duplicate source ID")
    runtime = config["runtime"]
    if not 1 <= runtime["max_exchanges"] <= 5 or not 1 <= runtime["batch_size"] <= 32:
        raise ValueError("max_exchanges must be 1–5 and batch_size 1–32")
    if runtime["budget_usd"] <= 0 or runtime["reserve_per_request_usd"] <= 0:
        raise ValueError("positive budget and request reserve required")
    if not config["user_styles"] or not config["openings"]:
        raise ValueError("styles and openings required")
    return config, references, sources


def planned_rows(config, library, sources, count=None):
    count = config["count"] if count is None else count
    if count < 1:
        raise ValueError("positive count required")
    rng = random.Random(config["seed"])
    source_map = {source["source_id"]: source for source in sources}
    quotas = allocate(count, {name: domain["weight"] for name, domain in config["domains"].items()})
    openings = [name for name, number in allocate(count, config["openings"]).items() for _ in range(number)]
    rng.shuffle(openings)
    rows = []
    for domain_name, quota in quotas.items():
        if not quota:
            continue
        domain = config["domains"][domain_name]
        if domain["profile"] not in {"practical", "deep"} or domain["grounding_mode"] not in {"task", "grounded"}:
            raise ValueError("unknown profile/grounding mode")
        choices = [(name, sub, cue) for name, sub in domain["subdomains"].items() for cue in sub["cues"]]
        if not choices:
            raise ValueError(f"{domain_name} needs concrete cues before enabling")
        rng.shuffle(choices)
        if config.get("seed_user_mode") == "literal_question" and quota > len(choices):
            raise ValueError(f"{domain_name} needs more distinct question seeds for this count")
        for ordinal in range(quota):
            sub_name, sub, seed_cue = choices[ordinal % len(choices)]
            cue = seed_cue["question"] if isinstance(seed_cue, dict) else seed_cue
            topic_id = seed_cue.get("topic_id", "") if isinstance(seed_cue, dict) else ""
            packs = [source_map[sid] for sid in sub.get("source_ids", [])]
            if domain["grounding_mode"] == "grounded" and (not packs or any(pack["review_status"] != "source_checked" or not pack["facts"] for pack in packs)):
                raise ValueError(f"{domain_name}/{sub_name} needs checked source notes")
            facts = [dict(fact, source_id=pack["source_id"]) for pack in packs for fact in pack["facts"]]
            if len({fact["fact_id"] for fact in facts}) != len(facts):
                raise ValueError("duplicate fact ID in selected sources")
            refs = library["references"]
            user_refs = [rng.choice([ref for ref in refs if ref["origin"] == origin])
                         for origin in library.get("mix_origins", ["local", "saas"])]
            matching = [ref for ref in refs if ref["request_type"] == sub["request_type"] or ref["domain"] == domain_name]
            answer_refs = rng.sample(matching or refs, min(2, len(matching or refs)))
            depth = sub.get("depth", "substantial" if sub["request_type"] in {"drafting", "coding", "planning"} else "developed")
            opening = openings[len(rows)]
            distribution = config.get("exchange_distribution", {1: 10, 2: 55, 3: 35})
            limit = min(config["runtime"]["max_exchanges"], rng.choices(list(distribution), weights=list(distribution.values()))[0])
            if opening != "direct" and config["runtime"]["max_exchanges"] > 1:
                limit = max(2, limit)
            if limit == 1:
                opening = "direct"
            row = dict(seed_index=len(rows), seed=config["seed"], recipe_version=config["version"],
                       subject=domain_name, domain=domain_name, subdomain=sub_name, profile=domain["profile"],
                       request_type=sub["request_type"], cue=cue, user_style=config["user_styles"][len(rows) % len(config["user_styles"])],
                       opening_mode=opening, depth=depth, depth_guidance=config["depths"][depth],
                       max_exchanges=limit, grounding_mode=domain["grounding_mode"],
                       topic_id=topic_id,
                       repetition_policy=config.get("diversity", {}),
                       fact_pack=json.dumps(facts, ensure_ascii=False),
                       source_limitations=json.dumps([limit for pack in packs for limit in pack.get('limitations', [])], ensure_ascii=False),
                       sources=json.dumps([{key: pack[key] for key in ["source_id", "url", "publisher", "checked_on"]} for pack in packs]),
                       first_question=cue if config.get("seed_user_mode") == "literal_question" else "",
                       question_guidance=config.get("question_guidance", "Natural user wording; include only necessary context."),
                       response_guidance=config.get("response_guidance", "Develop the answer as much as the user's actual need requires."),
                       quality_policy=dict(config.get("quality_policy", {}), **sub.get("quality_policy", {})),
                       reference_ids=sorted({ref["id"] for ref in user_refs + answer_refs}),
                       user_references=json.dumps([{"user": ref["user"], "earlier_users": ref["earlier_user_messages"], "demonstrates": ref["demonstrates"]} for ref in user_refs], ensure_ascii=False),
                       answer_references=json.dumps([{"user": ref["user"], "assistant": ref["assistant"], "demonstrates": ref["demonstrates"]} for ref in answer_refs], ensure_ascii=False),
                       family_id=digest([domain_name, topic_id]) if topic_id else digest([domain_name, sub_name, cue]), scenario="", history="[]", turn_number=1,
                       conversation={"messages": []}, answer_variants=[], turn_reviews=[], training_approved=False)
            rows.append(row)
    rng.shuffle(rows)
    for index, row in enumerate(rows):
        row["seed_index"] = index
    apply_variation(config, rows)
    validate_diversity(config, rows)
    return rows


def normalized_question(text):
    text = re.sub(r"[\u064b-\u065f\u0670\u0640]", "", text.casefold())
    text = text.translate(str.maketrans("أإآى٠١٢٣٤٥٦٧٨٩", "اااي0123456789"))
    return " ".join(re.findall(r"\w+", text))


def validate_diversity(config, rows):
    if config.get("seed_user_mode") == "literal_question":
        questions = [normalized_question(row["first_question"]) for row in rows]
        if len(set(questions)) != len(questions):
            raise ValueError("duplicate normalized question seeds")
    policy = config.get("diversity", {})
    if policy and len(rows) >= policy.get("scale_gate_count", 200):
        if any(not row.get("topic_id") for row in rows):
            raise ValueError("scale generation requires explicit topic_id on every question seed")
        topics = Counter(row["topic_id"] for row in rows)
        if max(topics.values()) > policy.get("max_questions_per_topic", 3):
            raise ValueError("scale topic repetition exceeds max_questions_per_topic")
        if len(topics) / len(rows) < policy.get("min_unique_topic_fraction", .4):
            raise ValueError("scale seed inventory has too few distinct topics")


def apply_variation(config, rows):
    rng = random.Random(config["seed"] + 73)
    styles = config.get("answer_styles", ["Use the natural structure that best fits the request."])
    if not styles:
        raise ValueError("answer_styles cannot be empty")
    order = [styles[index % len(styles)] for index in range(len(rows))]
    rng.shuffle(order)
    eligible = [row for row in rows if row["depth"] != "compact"]
    rate = config.get("optional_closing_rate", 0)
    if not 0 <= rate <= 1:
        raise ValueError("optional_closing_rate must be between zero and one")
    allowed = {row["seed_index"] for row in rng.sample(eligible, min(len(eligible), round(len(rows) * rate)))}
    for row, style in zip(rows, order):
        row["answer_style"] = style
        row["optional_closing_allowed"] = row["seed_index"] in allowed
        row["closing_guidance"] = ("On the first answer, finish with ONE brief, relevant next-step offer phrased as an ordinary Saudi question ending in ؟. Offer a worked example, another exercise or an unused detail already supported by the checked notes. Never promise an unsupported timeline or achievement list. Vary the wording. Complete the answer and citations first, then put this offer in its own final paragraph. Do not withhold any answer. Later answers should end naturally without another offer."
            if row["optional_closing_allowed"] else "End naturally. Do not append a next-step offer or a generic 'want more detail?' question. Questions inside a teaching activity are fine.")
        row["quality_policy"]["closing_offer_turn"] = 1 if row["optional_closing_allowed"] else 0
        cite = config.get("cite_grounded_answers", False) and row["grounding_mode"] == "grounded"
        row["quality_policy"]["require_citations"] = cite
        row["citation_guidance"] = ("Add one or two concise Markdown links to relevant supporting sources supplied in the source metadata. Cite the actual supporting page near its claim; do not invent URLs or cite irrelevant pages."
            if cite else "Do not invent citations. Arithmetic, worked exercises and hypothetical teaching activities do not need decorative web links.")


def style_issues(row, question, answer, turn):
    """Visible mechanical screening; word ranges never establish correctness."""
    policy = row.get("quality_policy", {})
    found = []
    if policy.get("max_user_words") and len(question.split()) > policy["max_user_words"]:
        found.append("user request exceeds short-question limit")
    minimum = policy.get("min_answer_words", 0)
    if turn > 1:
        minimum = policy.get("min_followup_answer_words", minimum)
    if len(answer.split()) < minimum:
        found.append("selected answer below response-length floor")
    if policy.get("max_answer_words") and len(answer.split()) > policy["max_answer_words"]:
        found.append("selected answer exceeds response-length ceiling")
    if policy.get("require_markdown") and not re.search(r"\*\*[^*]+\*\*|(?m:^#{1,3} |^[-*] |^\d+[.)] )", answer):
        found.append("selected answer lacks useful Markdown structure")
    if policy.get("require_citations"):
        links = re.findall(r"\[[^\]]+\]\((https?://[^\s]+?)\)", answer)
        known = {unquote(source["url"]).rstrip("/") for source in json.loads(row.get("sources", "[]"))}
        if not links:
            found.append("grounded answer lacks a supporting source link")
        if any(unquote(link).rstrip("/") not in known for link in links):
            found.append("citation URL is outside the checked source pack")
        if len(links) > 2:
            found.append("grounded answer has too many source links")
    if policy.get("closing_offer_turn") == turn:
        tail = answer.strip().split("\n\n")[-1]
        if not re.search(r"(?:تبي(?:ني|ن)?|تبغى|تبغاني|تبغين|ودّ?ك|تحب|تحتاج)[^\n؟?]{0,180}[؟?]", tail):
            found.append("planned first-answer next-step offer is missing")
    return found


def shape_feedback(row, answer, turn):
    policy = row.get("quality_policy", {})
    minimum = policy.get("min_followup_answer_words", policy.get("min_answer_words", 0)) if turn > 1 else policy.get("min_answer_words", 0)
    issues = style_issues(row, "", answer, turn)
    return json.dumps(dict(candidate_words=len(answer.split()), minimum_words=minimum,
                           maximum_words=policy.get("max_answer_words"), issues=issues,
                           instruction="Meet this answer shape through useful explanation, not filler; preserve the user's requested brevity and acknowledge insufficient evidence."), ensure_ascii=False)


def select_answer(row, review, question, draft, enhanced, turn, prefer_shape=False):
    chosen, issues = screen_review(review)
    note = "model preference"
    candidates = {"draft": draft, "enhanced": enhanced}
    if prefer_shape and chosen != "neither":
        other = "enhanced" if chosen == "draft" else "draft"
        if (style_issues(row, question, candidates[chosen], turn)
                and review[other + "_acceptable"]
                and not style_issues(row, question, candidates[other], turn)):
            note = f"{chosen} misses requested answer shape; {other} is model-acceptable and meets it"
            chosen = other
        if chosen == "enhanced" and review["unnecessary_padding"]:
            issues.append("model flags padding in displayed enhanced answer")
    answer = candidates["draft" if chosen == "draft" else "enhanced"]
    issues.extend(style_issues(row, question, answer, turn))
    return chosen, issues, note


def restore_answer_variant(value):
    """Recover the documented legacy Arrow key/value representation without guessing."""
    if isinstance(value, dict):
        return value
    required = {'turn', 'user', 'draft', 'enhanced', 'selected', 'selection_reason'}
    allowed = required | {'enhanced_before_style_repair'}
    if not isinstance(value, list) or not all(isinstance(item, list) and len(item) == 2 and isinstance(item[0], str) for item in value):
        raise ValueError('unknown answer variant serialization')
    restored = dict(value)
    if len(restored) != len(value) or not required <= set(restored) <= allowed:
        raise ValueError('invalid legacy answer variant fields')
    restored['turn'] = int(restored['turn'])
    if restored['turn'] not in {1, 2} or any(not isinstance(v, str) for k, v in restored.items() if k != 'turn'):
        raise ValueError('invalid legacy answer variant values')
    return restored


def ngrams(text, size=12):
    words = re.findall(r"\w+", text.casefold())
    return {tuple(words[i:i + size]) for i in range(len(words) - size + 1)}


def finalize(row, library):
    row = json.loads(json.dumps(row))
    repaired_turns = [index + 1 for index, value in enumerate(row['answer_variants']) if not isinstance(value, dict)]
    row['answer_variants'] = [restore_answer_variant(value) for value in row['answer_variants']]
    if repaired_turns:
        row['serialization_repairs'] = dict(answer_variant_turns=repaired_turns,
            reason='Recovered legacy Arrow key/value arrays; conversation content unchanged')
    issues = [f"Turn {item['turn']}: {issue}" for item in row["turn_reviews"] for issue in item["issues"]]
    messages = row["conversation"]["messages"]
    if not messages or len(messages) % 2 or any(m["role"] != ("user" if i % 2 == 0 else "assistant") or not m["content"].strip() for i, m in enumerate(messages)):
        issues.append("invalid alternating conversation")
    for i, message in enumerate(messages):
        phrases = ngrams(message["content"])
        for ref in library["references"]:
            if phrases & ngrams(ref["user"] if message["role"] == "user" else ref["assistant"]):
                issues.append(f"Message {i + 1}: shares 12 consecutive words with reference {ref['id']}")
    row["screening_passed"] = not issues
    row["content_sha256"] = digest(messages)
    row["exchange_count"] = len(messages) // 2
    row["reference_library_sha256"] = digest(library)
    row["writer_model"] = row.pop("_writer_model", "")
    row["judge_model"] = row.pop("_judge_model", "")
    row["training_approved"] = False
    for key in ["history", "turn_number", "user_references", "answer_references", "current_user", "current_draft", "current_enhanced", "current_review", "enhancement_feedback", "repair_feedback", "enhanced_before_style_repair"]:
        row.pop(key, None)
    audit = dict(issues=issues, machine_screen_passed=not issues, turns_checked=len(row["turn_reviews"]),
                 human_review="pending", training_approved=False)
    return row, audit


def summarize(records):
    def lengths(kind):
        return [len(variant[kind].split()) for row in records for variant in row["answer_variants"]]
    def describe(values):
        return dict(n=len(values), median=statistics.median(values), mean=round(statistics.mean(values), 1), min=min(values), max=max(values)) if values else {"n": 0}
    reviews = [item["review"] for row in records for item in row["turn_reviews"]]
    return dict(conversations=len(records), assistant_turns=len(reviews),
                machine_screen_passed=sum(row["screening_passed"] for row in records),
                domains=dict(Counter(row["domain"] for row in records)),
                profiles=dict(Counter(row["profile"] for row in records)),
                exchange_counts=dict(Counter(row["exchange_count"] for row in records)),
                draft_words=describe(lengths("draft")), enhanced_words=describe(lengths("enhanced")),
                selected_words=describe([len(m["content"].split()) for row in records for m in row["conversation"]["messages"] if m["role"] == "assistant"]),
                preferred=dict(Counter(review["preferred"] for review in reviews)),
                enhancement_adds_value=sum(review["enhanced_adds_value"] for review in reviews),
                enhanced_padding=sum(review["unnecessary_padding"] for review in reviews),
                first_user_ya_hala=sum("يا هلا" in row["conversation"]["messages"][0]["content"] for row in records),
                first_user_words=describe([len(row["conversation"]["messages"][0]["content"].split()) for row in records]),
                first_answer_words=describe([len(row["conversation"]["messages"][1]["content"].split()) for row in records]),
                markdown_answers=sum(bool(re.search(r"\*\*[^*]+\*\*|(?m:^#{1,3} |^[-*] |^\d+[.)] )", message["content"]))
                    for row in records for message in row["conversation"]["messages"] if message["role"] == "assistant"),
                training_approved=0,
                measurement_note="Whitespace word counts; model ratings are screening, not independent or human assessment.")


def save(records, output, library):
    pairs = [finalize(row, library) for row in sorted(records, key=lambda row: row["seed_index"])]
    seen = set()
    for row, audit in pairs:
        row["exact_duplicate"] = row["content_sha256"] in seen
        if row["exact_duplicate"]:
            audit["issues"].append("exact duplicate conversation")
            row["screening_passed"] = audit["machine_screen_passed"] = False
        seen.add(row["content_sha256"])
    mark_repetition(pairs)
    temp = output.with_name(output.name + ".tmp")
    temp.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row, _ in pairs), encoding="utf-8")
    temp.replace(output)
    atomic_json(output.with_suffix(".audit.json"), [dict(audit, row=index) for index, (_, audit) in enumerate(pairs, 1)])
    atomic_json(output.with_suffix(".summary.json"), summarize([row for row, _ in pairs]))


def mark_repetition(pairs):
    """Flag lexical answer clones; topic caps separately prevent same-subject saturation."""
    postings, previous = {}, []
    for index, (row, audit) in enumerate(pairs):
        policy = row.get("repetition_policy", {})
        if not policy:
            previous.append(set())
            continue
        answer = row["conversation"]["messages"][1]["content"]
        answer = re.sub(r"\[[^\]]+\]\(https?://[^\s]+?\)", "", answer)
        grams = ngrams(normalized_question(answer), 5) if len(answer.split()) >= 40 else set()
        candidates = Counter(other for gram in grams for other in postings.get(gram, []))
        for other, _ in candidates.most_common(50):
            union = grams | previous[other]
            similarity = len(grams & previous[other]) / len(union) if union else 0
            if similarity >= policy.get("answer_ngram_similarity", .72):
                audit["issues"].append(f"near-duplicate first answer of row {other + 1} (5-word overlap {similarity:.2f})")
                row["screening_passed"] = audit["machine_screen_passed"] = False
                break
        previous.append(grams)
        for gram in grams:
            bucket = postings.setdefault(gram, [])
            bucket.append(index)
            if len(bucket) > 50:
                del bucket[0]

