"""Shared recipe builder used by the current inventory preparation tool."""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from _paths import ROOT, CONFIGS, REFERENCES


import copy
import json
from collections import Counter
from pathlib import Path

import yaml
from diversity_catalog import CATALOG, validate_catalog
from common import atomic_json, digest, load_inputs, planned_rows


def build_recipe(base, approved_sources, post_pilot=False, catalog=None):
    if catalog is None:
        validate_catalog()
        catalog = CATALOG
    config=copy.deepcopy(base)
    config.update(version='saudi-diversity-v3',seed=10022026,count=200,
                  sources='../output/diversity_v3/verified_sources.json',domains={})
    config['runtime'].update(output='data_designer/output/saudi_diversity_v3_200.jsonl',
        batch_size=20,max_parallel_requests=8,budget_usd=3)
    config['exchange_distribution']={1:75,2:25}
    config['diversity'].update(max_questions_per_topic=2,min_unique_topic_fraction=.5)
    if post_pilot:
        config.update(version='saudi-diversity-v3.1', sources='../output/diversity_v3/verified_sources_postpilot.json')
        config['runtime']['output']='data_designer/output/saudi_diversity_v3_1_200.jsonl'
        config['depths'].update(compact='Usually 20-90 words: answer the date, place, name, color or score completely. Add context only when useful; never pad.',
            developed='Usually 80-180 words: direct answer with relevant reasons, context or a worked example. Preserve useful depth.',
            instructional='Usually 110-220 words: parent wording, concrete activity and a check of understanding.')
        config['response_guidance']='Use natural Saudi Arabic and useful Markdown. Match depth to the actual request: narrow facts and one-step calculations may be brief; how/why answers need relevant explanation; homework needs worked reasoning; teaching needs an example and activity. These ranges are targets, never filler quotas. Cite the actual supporting page near each claim. Follow the assigned optional closing policy; end other answers naturally. Avoid repeated recaps and unprompted evidence-availability disclaimers.'
    by_topic={}
    for source in approved_sources:
        by_topic.setdefault(source['topic_id'],[]).append(source['source_id'])
    for topic in catalog:
        domain=topic['domain'];factual=bool(topic['allowed_domains'])
        if factual and topic['topic_id'] not in by_topic:
            raise ValueError('missing checked evidence for '+topic['topic_id'])
        target=config['domains'].setdefault(domain,dict(weight=0,profile='deep' if factual else 'practical',
            grounding_mode='grounded' if factual else 'task',subdomains={}))
        target['weight']+=2
        for index, question in enumerate(topic['questions']):
            compact=factual and question.startswith(('متى','وين','كم نسخة','مين واجه')) and not any(w in question for w in ['وليه','وكيف','وش أهميتها'])
            if post_pilot:
                compact=factual and question.startswith(('متى','وين','كم','مين واجه','وش ألوان','وش اسم','وش إنجاز','وش دور ماجد')) and not any(w in question for w in ['وليه','وكيف','وش أهميتها'])
            depth='instructional' if domain=='teach_child' else ('compact' if compact else 'developed')
            kind='teaching' if domain=='teach_child' else ('worked_solution' if domain=='homework' else ('comparison' if 'الفرق' in question else ('factual' if compact else 'explanation')))
            if domain == 'chitchat':
                kind, depth = 'casual_chat', 'compact'
            kind = topic.get('request_type', kind)
            minimum=40 if compact else (110 if domain=='teach_child' else (75 if domain=='homework' else 90))
            if post_pilot:
                minimum=15 if compact else (90 if domain=='teach_child' else (20 if domain=='homework' else 50))
            target['subdomains'][topic['topic_id']+'-'+str(index+1)]=dict(request_type=kind,depth=depth,
                source_ids=by_topic.get(topic['topic_id'],[]),quality_policy=dict(min_answer_words=minimum),
                cues=[dict(question=question,topic_id=topic['topic_id'])])
    return config

