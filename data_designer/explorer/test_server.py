import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen
from server import Datasets, handler


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.data = root / "data"
        self.data.mkdir()
        self.dist = root / "dist"
        self.dist.mkdir()
        (self.dist / "index.html").write_text("<title>Explorer</title>")
        self.record = {"domain": "writing", "screening_passed": True, "conversation": {"messages": [
            {"role": "user", "content": "ابي رسالة"}, {"role": "assistant", "content": "هذه رسالة بسيطة"}]}}
        (self.data / "pilot.jsonl").write_text(json.dumps(self.record, ensure_ascii=False) + "\n" + json.dumps({**self.record, "screening_passed": False}) + "\nbroken\n", encoding="utf-8")
        (self.data / "pilot.questions1.jsonl").write_text("{}")
        self.datasets = Datasets(self.data)
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), handler(self.datasets, self.dist.resolve()))
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.http.server_port}"

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join()
        self.temp.cleanup()

    def get(self, path):
        with urlopen(self.base + path) as response:
            return json.load(response)

    def test_index_filter_and_record(self):
        self.assertEqual([d["name"] for d in self.get("/api/datasets")], ["pilot.jsonl"])
        result = self.get("/api/datasets/pilot.jsonl?status=flagged")
        self.assertEqual((result["count"], result["passed"], result["filtered"], result["malformed"]), (2, 1, 1, 1))
        self.assertNotIn("offset", result["rows"][0])
        self.assertEqual(self.get("/api/datasets/pilot.jsonl/records/0"), self.record)
        self.assertEqual(self.get("/api/datasets/pilot.jsonl?search=missing")["filtered"], 0)

    def test_path_traversal_and_bad_index_are_rejected(self):
        for path in ("/api/datasets/..%2F.env", "/api/datasets/pilot.jsonl/records/-1", "/%2e%2e/server.py", "/api/unknown"):
            with self.assertRaises(HTTPError) as result:
                self.get(path)
            self.assertEqual(result.exception.code, 404)
            result.exception.close()

    def test_index_refreshes_after_file_change(self):
        self.assertEqual(self.datasets.index("pilot.jsonl")["count"], 2)
        with (self.data / "pilot.jsonl").open("a", encoding="utf-8") as output:
            output.write(json.dumps(self.record) + "\n")
        self.assertEqual(self.datasets.index("pilot.jsonl")["count"], 3)

    def test_request_cost_is_exposed_and_refreshes(self):
        path = self.data / "pilot.cost.json"
        path.write_text(json.dumps({"reported_cost_usd": "0.02", "observed_key_usage_delta_usd": "0.08"}))
        self.assertEqual(self.datasets.index("pilot.jsonl")["cost"]["reported_cost_usd"], "0.02")
        path.write_text(json.dumps({"reported_cost_usd": "0.02345"}))
        self.assertEqual(self.datasets.index("pilot.jsonl")["cost"]["reported_cost_usd"], "0.02345")

    def test_legacy_bookmark_redirects_to_app(self):
        with urlopen(self.base + "/explorer.html?dataset=pilot.jsonl") as response:
            self.assertTrue(response.url.endswith("/?dataset=pilot.jsonl"))
            self.assertIn(b"Explorer", response.read())


if __name__ == "__main__":
    unittest.main()
