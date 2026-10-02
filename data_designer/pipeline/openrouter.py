"""Read OpenRouter metadata for pricing and billing attribution."""
import json
import os
import urllib.request


def api(route: str) -> dict:
    request = urllib.request.Request("https://openrouter.ai/api/v1/" + route,
        headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)

