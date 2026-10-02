# Salfah scale workflow

Code is edited and tested locally, committed/pushed, then pulled on the VM.
Datasets, request caches, research and release artifacts stay on the VM under
`data_designer/output/salfah15k_v1/`. The VM uses `.venv-hybrid`.

## Commands

```sh
.venv-hybrid/bin/python data_designer/run.py scale_release prepare
.venv-hybrid/bin/python data_designer/run.py scale_release screen
.venv-hybrid/bin/python data_designer/run.py scale_release pilot
.venv-hybrid/bin/python data_designer/run.py scale_release release --target 15000
```

Preparation authors 30 additional topic areas in each of 19 broad categories,
then 24 distinct task/situation candidates per topic. Existing checked factual
notes are reused; older Saudi technology and named poetry topics receive one
bounded OpenRouter search per topic when existing notes are unavailable.
Retrieved excerpts undergo extraction and model evidence screening. Failed
research topics are omitted, not mislabeled as checked. Ordinary stable knowledge
and original tasks can use general mode without fabricated citations.

All candidate starters have short wording, explicit task intent and a scenario
description. Exact and high-overlap lexical filtering removes obvious duplicate
requests. This is not proof of semantic uniqueness; sample review still matters.

The pilot stops after one 500-chat batch. The scale command resumes from completed
batches, uses cached paid responses after interruptions, and generates extra to
reach 15,000 passing chats. Generation and repairs use 100 workers. Every batch
checks all rows and model-reviews a reproducible 20% sample plus brief answers,
flagged/repaired chats. Cross-batch clone detection excludes new duplicates.
There are no manual content correction stages.
The `release` command also runs final context screening and packaging, generating
replacements if needed. `generate` and `package` remain available as separate steps.

Useful formatting is assessed contextually in model reviews. Plain prose and
drafts are allowed; Markdown absence alone never triggers a paid repair.
Packaging also reviews a small shortlist of potentially dangling starter
references without supplying hidden topic notes. Guessing missing subjects is
excluded; asking for clarification is allowed. This is a targeted check, not
a guarantee that every context problem is detected. Its calls and costs are saved.

Preparation has an $8 provider-spend ceiling. The overall preparation/generation
ceiling is $45, with at most $7 reserved per batch. In-flight calls reserve token
cost and searches reserve additional fees. Unknown charges remain unresolved;
they are not silently retried. These are operational stops, not a provider-side
hard cap. Costs sum actual per-response `usage.cost`; key usage is diagnostic.

## Artifacts and release

The completed run selected 15,000 chats / 46,384 assistant replies from 15,500
attempts. It covers 1,018 topic families and 28 categories. Median answer length
is 46 words, maximum 302; 13,485 chats have multiple exchanges. Actual provider
cost is $15.79876829 including preparation, intent screening, generation, repairs,
reviews, excluded/extra examples and final context checks. There are no unresolved
charges and no manual content corrections. Generation took 1h 27m 42s after the
pilots; preparation and pilot time are additional.

The final targeted context check reviewed 30 chats and excluded 13. There were
15,272 passing chats available after this check; the release selects 15,000.
Splits contain 13,493 train, 746 validation and 761 test chats, with no overlapping
topic families. These are model-screened data, not comprehensive human approval.
Published rows are shuffled independently within each split with seed 20261002;
conversation contents and split membership are unchanged.

The upload bundle is `output/salfah15k_v1/release/` on the VM. The full reader
copy is `output/saudi_salfah_15k.passing.jsonl`, with its aggregate cost report.

- `topic_inventory.json`, `research_notes.json`, `seed_pool.json`
- `preparation.work/`: cached responses and billing reservations
- `batches/`: recipes, all rows, passing rows, summaries, costs and raw calls
- `progress.json`: target, passing count, actual cost and last batch timing
- `salfah_reviewed.jsonl`: selected screened conversations
- `release/`: `data/{train,validation,test}.jsonl`, dataset card and report

Topic families stay together across approximately 90/5/5 train/validation/test
splits. The public schema uses alternating `messages` plus topic/category,
exchange count, grounding mode, synthetic status and model-review status.
Model screening is correlated with generation and is not comprehensive human
or independent factual review. Source excerpts retain their own rights; original
poetry is requested instead of full copyrighted poems or named-writer imitation.
