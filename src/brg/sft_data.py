"""Hugging Face chat dataset adapter for the Tinker Cookbook trainer."""

import chz
import json
from pathlib import Path
from datasets import load_dataset

from tinker_cookbook.renderers import TrainOnWhat
from tinker_cookbook.supervised.data import (
    SupervisedDatasetFromHFDataset,
    conversation_to_datum,
)
from tinker_cookbook.supervised.types import ChatDatasetBuilder


@chz.chz
class HFDatasetBuilder(ChatDatasetBuilder):
    dataset: str
    train_split: str = "train"
    validation_split: str | None = "validation"
    train_limit: int | None = None
    validation_limit: int | None = 512
    shuffle_seed: int = 0
    metadata_path: str | None = None
    max_steps: int | None = None

    def __call__(self):
        train_rows = load_dataset(self.dataset, split=self.train_split)
        train_rows = train_rows.shuffle(seed=self.shuffle_seed)
        if self.train_limit is not None:
            train_rows = train_rows.select(range(min(self.train_limit, len(train_rows))))

        renderer = self.renderer
        max_length = self.common_config.max_length
        train_on_what = (
            self.common_config.train_on_what or TrainOnWhat.ALL_ASSISTANT_MESSAGES
        )

        def to_datum(row):
            messages = row["messages"]
            if not isinstance(messages, list) or not messages:
                raise ValueError("each SFT row must contain a nonempty messages list")
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
            validation_rows = load_dataset(self.dataset, split=self.validation_split)
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
