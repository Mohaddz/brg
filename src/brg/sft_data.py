"""Hugging Face chat dataset adapter for the Tinker Cookbook trainer."""

import chz
import json
from pathlib import Path

from brg.chat_data import load_chat_dataset

from tinker_cookbook.renderers import TrainOnWhat
from tinker_cookbook.supervised.data import (
    SupervisedDatasetFromHFDataset,
    conversation_to_datum,
)
from tinker_cookbook.supervised.types import ChatDatasetBuilder


@chz.chz
class HFDatasetBuilder(ChatDatasetBuilder):
    dataset: str
    raw_jsonl: bool = False
    train_split: str = "train"
    validation_split: str | None = "validation"
    train_limit: int | None = None
    validation_limit: int | None = 512
    shuffle_seed: int = 0
    metadata_path: str | None = None
    max_steps: int | None = None

    def __call__(self):
        train_rows = load_chat_dataset(self.dataset, self.train_split, self.raw_jsonl)
        train_rows = train_rows.shuffle(seed=self.shuffle_seed)
        if self.train_limit is not None:
            train_rows = train_rows.select(range(min(self.train_limit, len(train_rows))))

        renderer = self.renderer
        max_length = self.common_config.max_length
        train_on_what = (
            self.common_config.train_on_what or TrainOnWhat.ALL_ASSISTANT_MESSAGES
        )

        def to_datum(row):
            messages = (
                json.loads(row["messages_json"])
                if self.raw_jsonl else row["messages"]
            )
            if not isinstance(messages, list) or not messages:
                raise ValueError("each SFT row must contain a nonempty messages list")
            messages = [
                {key: value for key, value in message.items()
                 if key != "reasoning_content" and value is not None}
                for message in messages
            ]
            return conversation_to_datum(messages, renderer, max_length, train_on_what)

        train_dataset = SupervisedDatasetFromHFDataset(
            train_rows, self.common_config.batch_size, map_fn=to_datum
        )
        if len(train_dataset) == 0:
            raise ValueError("train split has fewer rows than batch_size")
        if self.metadata_path is not None:
            path = Path(self.metadata_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"train_rows": len(train_rows),
                                        "steps_per_epoch": len(train_dataset),
                                        "max_steps": self.max_steps}) + "\n",
                            encoding="utf-8")

        validation_dataset = None
        if self.validation_split is not None:
            validation_rows = load_chat_dataset(
                self.dataset, self.validation_split, self.raw_jsonl
            )
            validation_rows = validation_rows.shuffle(seed=self.shuffle_seed)
            if self.validation_limit is not None:
                validation_rows = validation_rows.select(
                    range(min(self.validation_limit, len(validation_rows)))
                )
            validation_dataset = SupervisedDatasetFromHFDataset(
                validation_rows, self.common_config.batch_size, map_fn=to_datum
            )
            if len(validation_dataset) == 0:
                raise ValueError("validation split has fewer rows than batch_size")
        return train_dataset, validation_dataset
