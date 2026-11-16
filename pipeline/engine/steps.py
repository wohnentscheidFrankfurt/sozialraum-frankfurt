"""Step and Context. A step reads datasets from the store, computes and writes datasets."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from pipeline.shared.core.checks import Check, as_rows
from pipeline.engine.datasets import Dataset


@dataclass(frozen=True)
class Context:
    store: Any  # pipeline.engine.store.Store
    config: Any  # the module pipeline.config, or a namespace with the same names in tests
    log: Callable[[str], None] = print


@dataclass(frozen=True)
class Step:
    name: str
    run: Callable[[Context], None]
    needs: tuple[Dataset, ...] = ()
    makes: tuple[Dataset, ...] = ()


def check_order(steps: list[Step]) -> None:
    """Every needed dataset comes from an earlier step; no dataset and no step name appears twice."""
    made: dict[str, str] = {}
    names: set[str] = set()
    for step in steps:
        if step.name in names:
            raise ValueError(f"step `{step.name}` appears twice")
        names.add(step.name)
        for dataset in step.needs:
            if dataset.name not in made:
                raise ValueError(f"step `{step.name}` needs `{dataset.name}`, made by no earlier step")
        for dataset in step.makes:
            if dataset.name in made:
                raise ValueError(f"`{dataset.name}` is made by `{made[dataset.name]}` and `{step.name}`")
            made[dataset.name] = step.name


def producers(steps: list[Step]) -> dict[str, str]:
    return {dataset.name: step.name for step in steps for dataset in step.makes}


def write_checks(store, dataset: Dataset, checks: list[Check]) -> None:
    store.write(dataset, as_rows(checks))
