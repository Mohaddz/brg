"""Cache a bounded OpenRouter web-search research candidate on the VM for source review."""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from _paths import ROOT, CONFIGS, REFERENCES


import argparse
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from common import atomic_json, digest


def make_payload(query, domains, model="openai/gpt-6-luna"):
    return dict(model=model, temperature=0, max_tokens=1800,
        messages=[dict(role="user", content="Search the web once for this topic using the allowed primary-source domains. Summarize only supported facts with links to the actual supporting pages. Do not answer from memory without searching. Research topic: " + query)],
        tools=[dict(type="openrouter:web_search", parameters=dict(engine="exa", mode="fast",
            allowed_domains=sorted(set(domains)), max_results=3, max_total_results=3,
            max_uses=1, max_characters=1500))])


def citation_sources(message, domains):
    sources, seen = [], set()
    for annotation in message.get("annotations", []) or []:
        if annotation.get("type") != "url_citation":
            continue
        citation = annotation.get("url_citation", annotation)
        url = citation.get("url", "")
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in {"http", "https"} or not any(host == domain or host.endswith("." + domain) for domain in domains):
            continue
        if url not in seen:
            sources.append({key: citation[key] for key in ["url", "title", "content"] if key in citation})
            seen.add(url)
    return sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--allowed-domains", nargs="+", required=True)
    parser.add_argument("--cache-dir", type=Path, default=Path("data_designer/output/research"))
    parser.add_argument("--model", default="openai/gpt-6-luna")
    parser.add_argument("--check", action="store_true", help="show the bounded request offline")
    args = parser.parse_args()
    domains = sorted({domain.lower().strip().removeprefix("www.") for domain in args.allowed_domains})
    if any(not domain or "/" in domain or ":" in domain for domain in domains):
        parser.error("allowed domains must be hostnames, not URLs")
    payload = make_payload(args.query, domains, args.model)
    if args.check:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if os.name == "nt":
        parser.error("Run research on root@135.181.63.163; --check is local/offline")
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    key = digest(payload)
    path = args.cache_dir / (key + ".json")
    import fcntl
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if path.exists():
            print(json.dumps(dict(cache=str(path), cached=True, additional_api_requests=0)))
            return
        from brg.env import load_environment
        load_environment()
        request = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(payload).encode(), headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = json.load(response)
        message = raw["choices"][0]["message"]
        sources = citation_sources(message, domains)
        atomic_json(path, dict(schema_version=1, query=args.query, request_sha256=key,
            requested_at=datetime.now(timezone.utc).isoformat(), model=args.model,
            allowed_domains=domains, research_text=message.get("content"), citations=sources,
            review_status="pending_source_review" if sources else "no_verified_search_citations",
            usage=raw.get("usage"), response_id=raw.get("id"), raw_response=raw,
            note="Research candidate only. Verify facts against the linked pages before adding paraphrased notes to source_checked packs. Search snippets and generated summaries are not automatic approval."))
        print(json.dumps(dict(cache=str(path), cached=False, citations=len(sources),
            usage=raw.get("usage"), review_status="pending_source_review" if sources else "no_verified_search_citations")))


if __name__ == "__main__":
    main()
