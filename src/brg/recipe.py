"""Validated YAML recipes for supervised training and checkpoint evaluation."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator
import yaml


class RecipeSection(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DataConfig(RecipeSection):
    dataset: str
    raw_jsonl: bool = False
    train_split: str = "train"
    validation_split: str | None = "validation"
    train_limit: int | None = Field(default=None, gt=0)
    validation_limit: int | None = Field(default=512, gt=0)
    shuffle_seed: int = 0


class SFTConfig(RecipeSection):
    log_dir: Path
    renderer: str | None = None
    batch_size: int = Field(default=128, gt=0)
    max_length: int = Field(default=4096, gt=0)
    learning_rate: float = Field(default=0.0001, gt=0)
    lr_schedule: str = "linear"
    lora_rank: int = Field(default=32, gt=0)
    num_epochs: int = Field(default=1, gt=0)
    max_steps: int | None = Field(default=None, gt=0)
    save_every: int = Field(default=39, gt=0)
    async_periodic_saves: bool = True
    submit_ahead: int = Field(default=1, ge=0)
    eval_every: int = Field(default=0, ge=0)
    load_checkpoint_path: str | None = None


class WandbConfig(RecipeSection):
    project: str | None = None
    group: str | None = None


class EvalJob(RecipeSection):
    name: str
    enabled: bool = True
    evaluate_base: bool = False
    suite: str = "helm"
    tasks: list[str] = Field(default_factory=lambda: ["all"])
    tracks: list[str] = Field(default_factory=list)
    limit: int | None = Field(default=500, gt=0)
    max_tokens: int = Field(default=57344, gt=0)
    disable_thinking: bool = False
    every_checkpoints: int = Field(default=1, gt=0)
    max_periodic_evals: int | None = Field(default=None, ge=0)
    max_connections: int = Field(default=128, gt=0)
    max_evals: int = Field(default=1, gt=0)
    judge_model: str | None = None
    alrage: bool = False
    najd_project: str = "../najd-arena/tui"

    @model_validator(mode="after")
    def validate_selection(self):
        if self.suite not in ("legacy", "helm", "balsam", "najd", "all"):
            raise ValueError(f"unsupported evaluation suite: {self.suite}")
        if self.suite == "najd" and self.tasks != ["all"]:
            raise ValueError("Najd jobs require tasks: [all]; use tracks to filter")
        if self.suite in ("najd", "balsam") and self.alrage:
            raise ValueError("ALRAGE requires a HELM suite")
        if self.suite not in ("najd", "all") and self.tracks:
            raise ValueError("Najd tracks require suite: najd or all")
        return self


class Recipe(RecipeSection):
    name: str
    model: str
    data: DataConfig
    sft: SFTConfig
    wandb: WandbConfig = Field(default_factory=WandbConfig)
    evals: list[EvalJob] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_jobs(self):
        if not self.name or Path(self.name).name != self.name or self.name in (".", ".."):
            raise ValueError("recipe name must be a directory name")
        names = [job.name for job in self.evals]
        if len(names) != len(set(names)):
            raise ValueError("evaluation job names must be unique")
        for name in names:
            if not name or Path(name).name != name or name in (".", ".."):
                raise ValueError(f"evaluation job name must be a directory name: {name!r}")
        return self


def load_recipe(path: Path) -> Recipe:
    contents = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(contents, dict):
        raise ValueError("recipe must contain a YAML mapping")
    return Recipe.model_validate(contents)
