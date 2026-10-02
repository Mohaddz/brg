"""Publish source-gated expanded recipe on the VM, without API calls."""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from _paths import ROOT, CONFIGS, REFERENCES

import argparse
import json
import os
from collections import Counter
from pathlib import Path

import yaml
from expanded_catalog_v3 import CATALOG, validate_catalog
from common import atomic_json, digest, load_inputs, planned_rows
from recipe import build_recipe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--additional-sources', type=Path, help='Reviewed source packs, not raw research candidates')
    parser.add_argument('--catalog', choices=['expanded-v3'], default='expanded-v3')
    args = parser.parse_args()
    if os.name == 'nt':
        parser.error('Artifacts and seed plans stay on the VM')
    validate_catalog()
    catalog = CATALOG
    revision = 'expanded_v3'
    root = ROOT
    directory = root / 'output' / revision
    recipe = CONFIGS / f'hybrid_config_{revision}.yaml'
    if recipe.exists():
        parser.error('Recipe already exists; preserve it and choose a new revision')
    sources = json.loads((root / 'output/diversity_v3/verified_sources_postpilot.json').read_text())
    if args.additional_sources:
        sources += json.loads(args.additional_sources.read_text())
    if any(s.get('review_status') != 'source_checked' or not s.get('facts') for s in sources):
        parser.error('Every included source pack must have checked nonempty notes')
    if len({s['source_id'] for s in sources}) != len(sources):
        parser.error('Duplicate source IDs')
    checked = {s['topic_id'] for s in sources}
    ready = [t for t in catalog if not t['allowed_domains'] or t['topic_id'] in checked]
    pending = [t for t in catalog if t not in ready]
    base = yaml.safe_load((CONFIGS / 'hybrid_config_v2.yaml').read_text())
    config = build_recipe(base, sources, post_pilot=True, catalog=ready)
    config.update(version='saudi-'+revision.replace('_','-'), count=sum(len(t['questions']) for t in ready),
        sources=f'../output/{revision}/verified_sources.json')
    config['runtime'].update(output=f'data_designer/output/saudi_{revision}.jsonl', max_parallel_requests=10)
    config['depths']['casual'] = 'Usually 5-60 words; warm natural conversation, without forced formatting or lecture structure.'
    config['quality_policy']['max_answer_words'] = 1000
    for domain in config['domains'].values():
        for sub in domain['subdomains'].values():
            if sub['request_type'] == 'casual_chat':
                sub['depth'] = 'casual'
                sub['quality_policy'].update(min_answer_words=5, require_markdown=False)
    directory.mkdir(parents=True, exist_ok=True)
    atomic_json(directory / 'catalog.json', [dict(t, generation_status='ready' if t in ready else 'needs_source_review') for t in catalog])
    atomic_json(directory / 'research_queue.json', pending)
    atomic_json(directory / 'verified_sources.json', sources)
    recipe.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding='utf-8')
    cfg, library, loaded_sources = load_inputs(recipe)
    seeds = planned_rows(cfg, library, loaded_sources)
    assert len(seeds) == len(ready) * 2
    assert {r['topic_id'] for r in seeds} == {t['topic_id'] for t in ready}
    atomic_json(directory / 'seed_plan.json', seeds)
    summary = dict(topics=len(catalog), questions=sum(len(t['questions']) for t in catalog),
        ready_topics=len(ready), pending_source_topics=len(pending),
        categories=dict(Counter(t['domain'] for t in catalog)), catalog_sha256=digest(catalog),
        generation_started=False, paid_requests=0)
    atomic_json(directory / 'summary.json', summary)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
