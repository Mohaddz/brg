"""Load local API credentials without overriding the process environment."""

import os
from pathlib import Path

from dotenv import load_dotenv


def load_environment() -> None:
    repo_env = Path(__file__).resolve().parents[2] / ".env"
    local_env = Path.cwd() / ".env"
    if local_env.is_file():
        load_dotenv(local_env, override=False)
    elif repo_env.is_file():
        load_dotenv(repo_env, override=False)

    service_url = os.environ.get("TINKER_BASE_URL", "").rstrip("/")
    inference_suffix = "/oai/api/v1"
    if service_url.endswith(inference_suffix):
        if not os.environ.get("TINKER_OAI_BASE_URL"):
            os.environ["TINKER_OAI_BASE_URL"] = service_url
        service_url = service_url.removesuffix(inference_suffix)
        os.environ["TINKER_BASE_URL"] = service_url
    if service_url and not os.environ.get("TINKER_OAI_BASE_URL"):
        os.environ["TINKER_OAI_BASE_URL"] = service_url + inference_suffix
