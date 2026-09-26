"""Load chat JSONL without Hugging Face's rigid nested-message schema inference."""

import json
from pathlib import Path

from datasets import Dataset, Features, Value, load_dataset
from huggingface_hub import hf_hub_download


def _jsonl_rows(file_path: str):
    with Path(file_path).open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            messages = row["messages"]
            if not isinstance(messages, list) or not messages:
                raise ValueError("each SFT row must contain a nonempty messages list")
            yield {"messages_json": json.dumps(messages, ensure_ascii=False)}


def load_chat_dataset(dataset: str, split: str, raw_jsonl: bool):
    if not raw_jsonl:
        return load_dataset(dataset, split=split)
    file_path = hf_hub_download(
        repo_id=dataset, filename=f"data/{split}.jsonl", repo_type="dataset"
    )
    return Dataset.from_generator(
        _jsonl_rows,
        gen_kwargs={"file_path": file_path},
        features=Features({"messages_json": Value("string")}),
    )
