"""Builds both maps with the English map online into a folder, for the browser test of the language switch.
Call: .venv/bin/python -I tests/browser/tools/build_online_maps.py [FOLDER]  (default: output/online)
Runs the step map only, on the interim data of the last build. output/ and the local exports stay as they are."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

from pipeline import config
from pipeline.build import STEPS
from pipeline.engine.steps import Context, producers
from pipeline.engine.store import Store
from pipeline.map.html import step as map_step


def main(folder: Path) -> None:
    online = SimpleNamespace(**{k: v for k, v in vars(config).items() if k.isupper()})
    online.OUTPUT, online.EXPORTS, online.ENGLISH_ONLINE = folder, folder / "data", True
    map_step.run(Context(Store(config.INTERIM, producers(STEPS)), online))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else config.OUTPUT / "online")
