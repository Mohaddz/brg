"""Run one YAML-configured SFT job using the pinned Tinker Cookbook."""

import argparse
import asyncio
from pathlib import Path

from brg.recipe import load_recipe


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args(argv)
    recipe = load_recipe(args.config)

    from tinker_cookbook import checkpoint_utils
    from tinker_cookbook.supervised import train
    from tinker_cookbook.supervised.types import ChatDatasetBuilderCommonConfig

    from brg.sft_data import HFDatasetBuilder

    renderer = checkpoint_utils.resolve_renderer_name_from_checkpoint_or_default(
        model_name=recipe.model,
        explicit_renderer_name=recipe.sft.renderer,
        load_checkpoint_path=recipe.sft.load_checkpoint_path,
    )
    common_config = ChatDatasetBuilderCommonConfig(
        model_name_for_tokenizer=recipe.model,
        renderer_name=renderer,
        max_length=recipe.sft.max_length,
        batch_size=recipe.sft.batch_size,
    )
    builder = HFDatasetBuilder(
        common_config=common_config,
        dataset=recipe.data.dataset,
        train_split=recipe.data.train_split,
        validation_split=(recipe.data.validation_split if recipe.sft.eval_every else None),
        train_limit=recipe.data.train_limit,
        validation_limit=recipe.data.validation_limit,
        shuffle_seed=recipe.data.shuffle_seed,
    )
    config = train.Config(
        log_path=str(recipe.sft.log_dir),
        model_name=recipe.model,
        recipe_name=recipe.name,
        renderer_name=renderer,
        load_checkpoint_path=recipe.sft.load_checkpoint_path,
        dataset_builder=builder,
        learning_rate=recipe.sft.learning_rate,
        lr_schedule=recipe.sft.lr_schedule,
        num_epochs=recipe.sft.num_epochs,
        lora_rank=recipe.sft.lora_rank,
        save_every=recipe.sft.save_every,
        async_periodic_saves=recipe.sft.async_periodic_saves,
        submit_ahead=recipe.sft.submit_ahead,
        eval_every=recipe.sft.eval_every,
        max_steps=recipe.sft.max_steps,
        wandb_project=recipe.wandb.project,
        wandb_name=recipe.name,
    )
    asyncio.run(train.main(config))


if __name__ == "__main__":
    main()
