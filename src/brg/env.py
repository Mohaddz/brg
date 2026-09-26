"""Load local API credentials without overriding the process environment."""

from pathlib import Path

from dotenv import load_dotenv


def load_environment() -> None:
    repo_env = Path(__file__).resolve().parents[2] / ".env"
    local_env = Path.cwd() / ".env"
    if local_env.is_file():
        load_dotenv(local_env, override=False)
    elif repo_env.is_file():
        load_dotenv(repo_env, override=False)
