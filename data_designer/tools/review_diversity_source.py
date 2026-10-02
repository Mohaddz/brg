"""Record an explicit agent review after inspecting candidate facts and primary evidence."""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from _paths import ROOT, CONFIGS, REFERENCES


import argparse,json,os
from datetime import datetime,timezone
from pathlib import Path
from common import atomic_json,digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topics',nargs='+',required=True)
    parser.add_argument('--drop',default='{}',help='JSON mapping topic IDs to one-based fact numbers to omit')
    parser.add_argument('--note',required=True)
    args=parser.parse_args()
    if os.name=='nt':parser.error('Source research and review artifacts stay on the VM')
    root=Path('data_designer/output/diversity_v3')
    path=root/'source_reviews.json'
    reviews=json.loads(path.read_text()) if path.exists() else {}
    drops=json.loads(args.drop)
    for topic in args.topics:
        candidate=json.loads((root/(topic+'.candidate.json')).read_text())
        if candidate['status']!='pending_agent_review':parser.error('candidate not ready: '+topic)
        facts=[f for i,f in enumerate(candidate['facts'],1) if f['excerpt_found'] and i not in drops.get(topic,[])]
        if not facts:parser.error('no supported facts selected: '+topic)
        reviews[topic]=dict(verdict='checked',reviewed_by='codex_agent_source_review',
            reviewed_at=datetime.now(timezone.utc).isoformat(),candidate_sha256=digest(candidate),
            facts=facts,note=args.note,limitations=candidate.get('limitations',[]),
            omitted_fact_numbers=[i for i,f in enumerate(candidate['facts'],1) if not f['excerpt_found'] or i in drops.get(topic,[])])
    atomic_json(path,reviews)
    print(json.dumps(dict(reviewed_topics=len(reviews),updated=args.topics)))


if __name__=='__main__':main()
