# Current conversation pipeline

Run `data_designer/run.py lightweight --config data_designer/configs/lightweight.json`
on the VM. Add `--dry-run` for offline planning without paid requests. The example
recipe selects 100 distinct topics including 40 poetry-writing/grammar tasks,
295 answers and a fresh output filename. Inspect/change it before a new run;
code/input fingerprints prevent accidentally resuming a completed run.

## Generation and screening

1. Select topics, starter questions, turn counts and reference notes.
2. Luna generates a whole conversation per call, up to 100 concurrent chats.
3. Code checks roles, turn count, starter preservation, length, Markdown,
   allowed citation URLs, closing offers and repetition.
4. Luna reviews a reproducible sample. Flagged chats receive full-conversation
   repair calls, in parallel across chats, followed by code and Luna rechecks.
5. Stop after two repair attempts. Run final cross-chat repetition checks.
6. Save all rows for audit; export passing chats separately as `.passing.jsonl`.

Code protects the original starter and all unflagged user turns. Only explicitly
flagged generated follow-ups may change. Raw calls, rejected repairs, accepted
changes, costs and timings are retained under the matching VM `.work/` directory.
A shared budget ledger reserves costs for in-flight calls and refuses spending
above the configured budget. Unknown charges retain conservative reservations.

## Limits and quality

The maximum is 1,000 whitespace-separated words per answer, with repair/exclusion
rather than truncation. Usual answer-length guidance stays concise. Output token
headroom is 5,000 per exchange plus 1,200 per chat; review calls allow 2,400 tokens.
Reasoning effort is unspecified. Chitchat permits brief plain answers; other
answers use meaningful Markdown. Generic closing offers are assigned selectively.

Same-model screening and code checks do not establish factual accuracy or human
training approval. The current closing-offer detector can flag conditional wording,
and the 15-word minimum can reject complete short answers. Those gates still need
improvement before scaling. The 1,000-word cap has not had a paid pilot.

## Topics and evidence

The additive catalog modules jointly define 460 topics, 920 starter questions and
28 categories. All modules are current dependencies, not alternative generators.
There are 292 source-ready topics/584 starters and 168 pending factual topics.
Poetry additions include 10 classical and 10 modern factual topics, 20 original
writing/interpretation tasks, and 20 grammar exercise topics. Factual poet/verse
attribution and historical claims use checked notes. Writing tasks produce
original text and avoid invented attribution or unverified metre claims.

The active base recipe is `configs/hybrid_config_expanded_v3.yaml`. Its 123 checked
reference packs stay on the VM at `output/expanded_v3/verified_sources.json`.
Source notes are reused; the conversation writer does not browse links during
generation. The source queue and seed plan are in the same output folder.
Research tools propose candidates that need review before entering checked notes.

## Measured 100-worker benchmark

The last completed automated batch generated 100 chats/295 answers in 14.61
seconds; generation plus reviews and repairs took 93.81 seconds. It recorded no
HTTP/rate-limit failures or unresolved requests. 29 chats received 45 repair calls,
with 45 rechecks and 14 initial reviews. No manual corrections were applied.
88 chats/247 answers passed; 12 were excluded. Median answer length was 50 words.

Provider cost was $0.115781495: generation $0.055144625, initial reviews
$0.007694075, repairs $0.029405960, rechecks $0.023536835. This benchmark used the
previous 450-word ceiling. At the same policy/mix and 88% yield, linear estimates
are $11.58 for 10k generated chats or $13.16 for 10k passing chats. New research,
VM and Codex/session costs are additional. This is not a measured scale-out
invoice, and one successful burst does not establish sustained provider capacity.

Completed benchmark artifacts remain on the VM under
`output/saudi_lightweight_parallel_100*`; they are not recipes to rerun. The reader
can display them through `data_designer/explorer/connect.ps1`.
