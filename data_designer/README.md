# Saudi conversation data designer

Generate and review Saudi Arabic conversations on the VM at
`root@135.181.63.163`, repository `/root/brg`. Use `.venv-hybrid`; keep generated
datasets and long jobs on the VM.

| Directory | Contents |
| --- | --- |
| `pipeline/` | Lightweight generator, shared planning/validation and API metadata helper |
| `catalogs/` | Topic catalogs; v3 has 460 topics and 920 starter questions |
| `configs/` | Current generation recipe and shared base configurations |
| `references/` | Small style libraries, selections and initial source notes |
| `tools/` | Research, recipe preparation, reports, evaluation and exports |
| `tests/` | Offline Python tests |
| `docs/` | Current pipeline details and measured benchmark |
| `explorer/` | Dataset reader app and read-only server |
| `output/` | VM datasets, checked sources, raw calls, costs and backups |
| `archive/` | Ignored historical dataset artifacts only |

The current generator produces full conversations in parallel, screens them,
repairs flagged chats and exports passing rows separately. It has a 1,000-word
answer ceiling and supports up to 100 workers. See [pipeline details](docs/LIGHTWEIGHT.md).
Completed pilots describe their original settings and remain historical.

For the 500-chat pilot and 15k target, see the [scale workflow](docs/SCALE.md).

From `/root/brg`, inspect a recipe without paid calls:

```sh
.venv-hybrid/bin/python data_designer/run.py lightweight --config data_designer/configs/lightweight.json --dry-run
```

For a new run, create a recipe in `configs/`, select the latest base recipe
`hybrid_config_expanded_v3.yaml`, and choose a fresh output name under
`../output/`. Recipe input/output paths are relative to that config file;
hybrid `runtime.output` paths are relative to the repository. Do not rerun
completed pilots with changed code or inputs: fingerprints intentionally reject it.

Other commands use the same launcher:

```sh
.venv-hybrid/bin/python data_designer/run.py prepare_diversity_sources --help
.venv-hybrid/bin/python data_designer/run.py export_hybrid_sft --help
.venv-hybrid/bin/python -m unittest discover -s data_designer/tests -p 'test_*.py'
```

Factual reference packs for the latest inventory stay at
`output/expanded_v3/verified_sources.json`; its research queue and seed plan are
in the same folder. The cleanup does not alter sources or generation policy.

Reconnect the existing reader from Windows:

```powershell
& data_designer/explorer/connect.ps1 -Dataset saudi_lightweight_parallel_100.passing.jsonl
```

Retired generators, pilot correction scripts, old reader assets and obsolete
pilot recipes have been removed. Existing dataset artifacts and backups remain
ignored locally; production datasets and logs stay on the VM. The VM should
receive repository changes through Git after they are committed and pushed.
