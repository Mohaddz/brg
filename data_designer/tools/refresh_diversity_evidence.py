"""Refresh a topic from explicitly selected primary pages, preserving prior research."""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from _paths import ROOT, CONFIGS, REFERENCES


import argparse
import gzip
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from common import atomic_json
from prepare_diversity_sources import TextParser


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topic', required=True)
    parser.add_argument('--urls', nargs='+', required=True)
    args = parser.parse_args()
    if os.name == 'nt':
        parser.error('Research artifacts stay on the VM')
    root = Path('data_designer/output/diversity_v3').resolve()
    catalog = json.loads((root / 'catalog.json').read_text())
    if args.topic not in {t['topic_id'] for t in catalog}:
        parser.error('Unknown catalog topic')
    evidence = []
    for url in args.urls:
        request = urllib.request.Request(url, headers={'User-Agent': 'BRG-Source-Review/1.0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(750000)
            if response.headers.get('Content-Encoding') == 'gzip' or raw.startswith(b'\x1f\x8b'):
                raw = gzip.decompress(raw)
            body = raw[:3000000].decode('utf-8', errors='replace')
        text = TextParser()
        text.feed(body)
        page = ' '.join(' '.join(text.parts).split())[:28000]
        if len(page) < 100:
            raise ValueError('Insufficient page text: ' + url)
        evidence.append(dict(url=url, title=url, content='', page_text=page,
                             retrieved_at=datetime.now(timezone.utc).isoformat(),
                             retrieval_method='direct_primary_page_fetch'))
    archive = root / 'prior_research' / (args.topic + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    archive.mkdir(parents=True)
    for suffix in ['candidate', 'research', 'evidence', 'notes-response']:
        path = root / (args.topic + '.' + suffix + '.json')
        if path.exists():
            path.rename(archive / path.name)
    atomic_json(root / (args.topic + '.evidence.json'), evidence)
    atomic_json(root / (args.topic + '.research.json'), dict(
        choices=[dict(message=dict(content='', annotations=[]))],
        retrieval_method='explicit_primary_pages_selected_by_agent',
        urls=args.urls, previous_research=str(archive)))
    print(json.dumps(dict(topic=args.topic, pages=len(evidence), archived=str(archive))))


if __name__ == '__main__':
    main()
