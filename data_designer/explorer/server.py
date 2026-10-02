"""Read-only dataset API and production frontend. No third-party dependencies."""
from __future__ import annotations

import argparse
import json
import mimetypes
import statistics
import threading
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit


def messages(record):
    return (record.get("conversation") or {}).get("messages") or record.get("messages") or [
        {"role": "user", "content": record.get("question", "")},
        {"role": "assistant", "content": record.get("answer", "")},
    ]


class Datasets:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.cache = {}
        self.lock = threading.Lock()

    def files(self):
        candidates = sorted((p for p in self.root.glob("*.jsonl") if not any(
            token in p.stem.lower() for token in (".questions", ".answers", ".enhanced", ".reviews", ".quarantine", "annotation", "coverage")
        )), key=lambda p: p.stat().st_mtime, reverse=True)
        found = []
        for path in candidates:
            try:
                with path.open("rb") as source:
                    record = json.loads(source.readline(2 * 1024 * 1024))
                if isinstance(record, dict) and (isinstance(record.get("conversation", {}).get("messages"), list)
                    or isinstance(record.get("messages"), list)
                    or isinstance(record.get("question"), str) and isinstance(record.get("answer"), str)):
                    found.append(path)
            except (ValueError, AttributeError, OSError):
                continue
        return found

    def path(self, name):
        if name != Path(name).name or name not in {p.name for p in self.files()}:
            raise FileNotFoundError("Dataset not found")
        path = (self.root / name).resolve()
        if not path.is_relative_to(self.root):
            raise FileNotFoundError("Dataset not found")
        return path

    def index(self, name):
        path = self.path(name)
        cost_path = path.with_suffix(".cost.json")
        stamp = (path.stat().st_mtime_ns, path.stat().st_size,
                 cost_path.stat().st_mtime_ns if cost_path.exists() else None)
        with self.lock:
            if name in self.cache and self.cache[name][0] == stamp:
                return self.cache[name][1]
            rows, words, domains = [], [], Counter()
            screening_scope = None
            malformed = 0
            with path.open("rb") as source:
                while True:
                    offset = source.tell()
                    line = source.readline()
                    if not line:
                        break
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        screening_scope = record.get("screening_scope", screening_scope)
                        turns = messages(record)
                        request = next((m["content"] for m in turns if m["role"] == "user"), "")
                        domain = record.get("domain", record.get("subject", "general"))
                        domains[domain] += 1
                        lengths = [len(m["content"].split()) for m in turns if m["role"] == "assistant"]
                        words.extend(lengths)
                        rows.append({"id": len(rows), "offset": offset, "request": request,
                            "scenario": record.get("scenario", ""), "domain": domain,
                            "profile": record.get("profile", ""), "passed": record.get("screening_passed"),
                            "exchanges": len(lengths), "words": sum(lengths),
                            "max_reply_words": max(lengths, default=0),
                            "seed_index": record.get("seed_index")})
                    except (ValueError, TypeError, KeyError, AttributeError):
                        malformed += 1
            cost = {}
            try:
                raw_cost = json.loads(path.with_suffix(".cost.json").read_text())
                cost = {k: raw_cost[k] for k in ("reported_cost_usd", "unresolved_request_count", "unresolved_cost_upper_bound_usd", "observed_key_usage_delta_usd", "measurement_note", "completed_conversations") if k in raw_cost}
            except (OSError, ValueError, TypeError):
                pass
            info = {"name": name, "cost": cost, "screening_scope": screening_scope, "count": len(rows), "passed": sum(r["passed"] is True for r in rows),
                    "flagged": sum(r["passed"] is False for r in rows), "assistant_turns": len(words),
                    "median_words": statistics.median(words) if words else 0,
                    "domains": dict(domains), "malformed": malformed, "rows": rows}
            # Offsets and short request summaries only; full records stay on disk.
            if len(self.cache) >= 3:
                self.cache.pop(next(iter(self.cache)))
            self.cache[name] = (stamp, info)
            return info

    def record(self, name, index):
        info = self.index(name)
        if index < 0 or index >= len(info["rows"]):
            raise FileNotFoundError("Conversation not found")
        with self.path(name).open("rb") as source:
            source.seek(info["rows"][index]["offset"])
            return json.loads(source.readline())


def handler(datasets, dist):
    class Handler(BaseHTTPRequestHandler):
        def send(self, body, content_type="application/json; charset=utf-8", status=200):
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url = urlsplit(self.path)
            parts = unquote(url.path).strip("/").split("/")
            try:
                if url.path == "/explorer.html":
                    self.send_response(302)
                    self.send_header("Location", "/" + ("?" + url.query if url.query else ""))
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                if parts == ["api", "datasets"]:
                    return self.send([{"name": p.name, "bytes": p.stat().st_size} for p in datasets.files()])
                if len(parts) >= 3 and parts[:2] == ["api", "datasets"]:
                    name = parts[2]
                    if len(parts) == 5 and parts[3] == "records":
                        return self.send(datasets.record(name, int(parts[4])))
                    if len(parts) != 3:
                        raise FileNotFoundError()
                    info = datasets.index(name)
                    query = parse_qs(url.query)
                    search = query.get("search", [""])[0].casefold()
                    domain = query.get("domain", ["all"])[0]
                    status = query.get("status", ["all"])[0]
                    order = query.get("sort", ["dataset"])[0]
                    if order not in {"dataset", "reply_desc", "reply_asc"}:
                        raise ValueError("Invalid sort order")
                    rows = [r for r in info["rows"] if
                        (not search or search in (r["request"] + " " + r["scenario"] + " " + r["domain"]).casefold())
                        and (domain == "all" or r["domain"] == domain)
                        and (status == "all" or status == "pass" and r["passed"] is True
                             or status == "flagged" and r["passed"] is False)]
                    if order != "dataset":
                        rows.sort(key=lambda r: (
                            -r["max_reply_words"] if order == "reply_desc" else r["max_reply_words"],
                            r["id"]))
                    page = max(0, int(query.get("page", ["0"])[0]))
                    size = 100
                    return self.send({**{k: v for k, v in info.items() if k != "rows"}, "filtered": len(rows),
                        "page": page, "page_size": size,
                        "rows": [{k: v for k, v in row.items() if k != "offset"} for row in rows[page*size:(page+1)*size]]})
                if parts[0] == "api":
                    raise FileNotFoundError()
                asset = (dist / unquote(url.path).lstrip("/")).resolve()
                if not asset.is_relative_to(dist):
                    raise FileNotFoundError()
                if url.path == "/" or not asset.is_file() and "." not in asset.name:
                    asset = dist / "index.html"
                if not asset.is_file():
                    raise FileNotFoundError()
                return self.send(asset.read_bytes(), mimetypes.guess_type(asset.name)[0] or "application/octet-stream")
            except FileNotFoundError:
                self.send({"error": "Not found"}, status=404)
            except (ValueError, IndexError):
                self.send({"error": "Invalid request"}, status=400)
            except Exception:
                self.log_error("Dataset read failed")
                self.send({"error": "Could not read dataset"}, status=500)
    return Handler


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18766)
    parser.add_argument("--data", type=Path, default=Path(__file__).resolve().parent.parent / "output")
    args = parser.parse_args()
    dist = (Path(__file__).resolve().parent / "dist").resolve()
    print(f"Explorer at http://{args.host}:{args.port}; datasets: {args.data}", flush=True)
    ThreadingHTTPServer((args.host, args.port), handler(Datasets(args.data), dist)).serve_forever()
