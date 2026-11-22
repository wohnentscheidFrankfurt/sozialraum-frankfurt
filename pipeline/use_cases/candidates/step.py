"""Step candidates: evaluation of every template on the shown values, the reference for the browser check."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.city_values import city_value_dict
from pipeline.use_cases.candidates.catalog import TEMPLATES
from pipeline.shared.core.texts import SOURCE_LANGUAGE
from pipeline.use_cases.candidates.model import evaluate
from pipeline.engine.datasets import CANDIDATES_REFERENCE, CITY_VALUES, INDICATORS_DISTRICTS, INDICATORS_QUARTERS, MAP_CATALOG
from pipeline.engine.steps import Context, Step


def run(ctx: Context) -> None:
    areas = {"district": ctx.store.read(INDICATORS_DISTRICTS), "quarter": ctx.store.read(INDICATORS_QUARTERS)}
    values = city_value_dict(ctx.store.read(CITY_VALUES))
    catalog = ctx.store.read(MAP_CATALOG)["catalog"]  # written finished by assembly: the decimals the map shows
    decimals = {i["id"]: i["decimals"] for i in catalog}
    ranked = {i["id"] for i in catalog if i["rank"] > 0}
    templates = TEMPLATES[SOURCE_LANGUAGE]  # ids, levels and criteria do not depend on the language; the file has no text
    reference = pd.concat([evaluate(areas[t["level"]], t["criteria"], values, decimals, ranked).assign(template=t["id"], level=t["level"])
                           for t in templates], ignore_index=True)[["template", "level", "area", "met", "full"]]
    ctx.store.write(CANDIDATES_REFERENCE, reference)
    for t in templates:
        rows = reference[reference["template"] == t["id"]]
        ctx.log(f"{t['title']}: {rows['full'].sum()} full matches, {(rows['met'] == len(t['criteria']) - 1).sum()} close")


STEP = Step("candidates", run, needs=(INDICATORS_DISTRICTS, INDICATORS_QUARTERS, CITY_VALUES, MAP_CATALOG), makes=(CANDIDATES_REFERENCE,))
