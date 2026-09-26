"""Bridge: run the Inspect suite inside Tinker training eval callbacks.

Same pattern as Barq-LLM: tinker_cookbook's InspectEvaluatorBuilder feeds the
loop's SamplingClient into our task builders. ALRAGE is excluded here — judge
calls don't belong on the training hot path; run it post-hoc via eval_run.
"""


def tinker_evaluator(*, model_name, renderer_name, log_dir, max_tokens, limit=None,
                     tasks=None, max_connections=128):
    """Return a cookbook evaluator builder for SFT/RL eval callbacks."""
    from tinker_cookbook.eval.inspect_evaluators import InspectEvaluatorBuilder

    from brg import tasks as brg_tasks

    names = tasks or brg_tasks.ALL_TASKS
    builders = {
        "arabic_mmlu": brg_tasks.arabic_mmlu,
        "madinah_qa": brg_tasks.madinah_qa,
        "ht_arabic_mmlu": brg_tasks.ht_arabic_mmlu,
        "arabic_exams": brg_tasks.arabic_exams,
        "alghafa": brg_tasks.alghafa,
        "aratrust": brg_tasks.aratrust,
        "balsam_dev": brg_tasks.balsam_dev,
    }
    built = [builders[name]() for name in names]
    return InspectEvaluatorBuilder(
        tasks=built,
        model_name=model_name,
        renderer_name=renderer_name,
        log_dir=str(log_dir),
        limit=limit,
        temperature=0.0,
        max_tokens=max_tokens,
        max_connections=max_connections,
    )
