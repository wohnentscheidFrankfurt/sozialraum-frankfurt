# Sozialraum Frankfurt – notes for Claude

Map of ownership, social situation, housing burden, land, protection and elections in Frankfurt am Main. Built for
the Wohnentscheid Frankfurt (2026). Other initiatives may use it (licence in `README.md`). Nothing is built in
advance for them.

## Rules

- **The repo lies on GitHub** at `wohnentscheidFrankfurt/sozialraum-frankfurt` and is public.
  Everything in it is public. Never commit secrets, personal data or internal matters of the initiative
  (strategy, demands, people); they stay in the folders of the initiative outside the repo.
- Commits use the noreply address of `wohnentscheidFrankfurt` (`includeIf` for `~/IdeaProjects/we/`), never a private
  or work address. Commits end with the Co-Authored-By line. Push only when the user asks.
  The history starts on 16.11.2026; the older one lies only in a local archive clone.
- Python always as `.venv/bin/python -I` from the repo root.
- Language: texts of the map (language files `texts.<lang>.yaml`, `web/`, built HTML) are German. Everything else in
  the repo (code, comments, `docs/`, file names) is English as far as possible, with terms from `docs/glossary.md`.
  German stays only for proper names and terms of the sources. Always short sentences, one statement per sentence.
- The map states facts and may draw the conclusion that its numbers carry ("Politik ist nie neutral."). Own
  conclusions follow the rule in `docs/data-rules.md` (well founded, traceable, simple). It demands nothing. Header:
  "Sozialraum Frankfurt". Tests check this.
- Numbers flow into political demands. Unchecked data costs credibility. Every number is checked against its source.
- Architecture (`docs/architecture.md`): `pipeline/` holds `build.py`, `config.py`, `update_sources.py`
  and four tiers: `engine/` (steps, store, datasets, downloads), `shared/` (`core`, `readers`, `zensus`, `geography`),
  `use_cases/` (one package per use case) and `map/` (`assembly`, `checks`, `html`). `model.py`, `catalog.py` and
  `checks.py` are pure, `sources.py` (and `shared/zensus/tables.py`) is the only place that knows source vocabulary,
  `step.py` does I/O through the store. `shared/` imports no use case; `use_cases/` import only `model` and `catalog` of
  another use case; `map/` only those of a use case. `tests/test_architecture.py` enforces this. German terms map to
  English names in `docs/glossary.md`.
- Every visible text of the map stands in a `texts.<lang>.yaml` next to its package, never in Python or `web/`.
  Source vocabulary stays in Python. See `docs/texts.md`, Where texts live.
- Text rules of the map are in `docs/texts.md`. UI rules are in `docs/design.md`. Domain rules for numbers are in
  `docs/data-rules.md`. Read the matching file before a change.

## Commands

```bash
.venv/bin/python -I -m pipeline.build                   # all steps, the map goes to output/
.venv/bin/python -I -m pipeline.build --step zensus     # one step
.venv/bin/python -I -m pipeline.update_sources          # download sources again and write the extracts into sources/
.venv/bin/python -I -m pytest -q -p no:warnings         # tests
(cd tests/browser && npx playwright test)               # browser tests of the built map, see below
.venv/bin/python -I tests/compare_build.py --help       # compare builds, see below
```

`--step checks` only collects the check files of the other steps. After a change in `reference/`, run the step that
writes the check first (or the full build).

Browser tests (`docs/architecture.md`, Browser tests): they need the build. Run them from `tests/browser`.
One file: `npx playwright test desktop/legend.spec.mjs`. One project: `--project=chrome-390`. Tests by name:
`--grep "…"`. `MAP_HTML` sets the map (default `output/sozialraum-frankfurt.html`). `CANDIDATES_CSV` sets the
candidates reference (default `interim/candidates_reference.csv`). `SCREENS` sets the folder of the screenshots
(default `output/screens`). Relative values resolve against the repo root. A failed test keeps its trace:
`npx playwright show-trace ../../output/playwright/results/<test>/trace.zip`. The HTML report opens with
`npx playwright show-report ../../output/playwright/report`. Each run empties `output/playwright/results`. Two runs at
the same time need their own `--output=<folder>` and `SCREENS` each, and they share and overwrite the HTML report.

Compare builds (only for a refactoring): `capture` the old build into a new folder, for example `golden/`
(`tests/compare_build.py capture --interim interim --output output --map sozialraum-frankfurt.html --dest golden`).
Then run `touch interim/.build-start`, build the new version and run `compare` with `--golden golden`. `compare`
prints changed values (exit code 1) and removed or added files, columns and keys (exit code 0). `ui` compares two dumps
of `tests/browser/tools/dump_text.mjs` (`node tests/browser/tools/dump_text.mjs <map.html> <out.json>`). Take the
golden dump with the current tool. Why: the tool waits until the map stands still; dumps of an older tool differ in the
tooltip and the grid keys.

New environment: `uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e '.[test]'` and
`(cd tests/browser && npm install && npx playwright install webkit)`.

## Layout

- `pipeline/`: the Python build; it computes the data and packs the map. `build.py` (CLI, order of `STEPS`), `config.py`
  (all paths and URLs), `update_sources.py` (by hand, never a step) lie at the top. `engine/`:
  `datasets.py` (all interim data), `store.py`, `steps.py`, `download.py`.
  `shared/`: `core`, `readers`, `zensus`, `geography`. `use_cases/`: `ownership_cells`, `public_housing`, `coops`,
  `ownership_shares`, `ownership_history`, `new_construction`, `monitoring`, `survey`, `rent_burden`, `social_housing`,
  `housing`, `construction_year`, `land`, `flat_roofs`, `building_gaps`, `protection`, `election`, `candidates`.
  `map/`: `assembly`, `checks`, `html`.
  Each use case has a README: what, formula, why, inputs, output, checks, limits. Each use case has its own
  `catalog.py` (title and the result protocol of the ⓘ: source, as-of date, calculation, rule, uncertainty) and its
  `texts.de.yaml` (every visible text of the use case; the same in `shared/core`, `map/assembly`, `map/html`);
  `map/assembly/catalog.py` holds the order of the layers.
- `web/`: the browser app of the map (HTML template, CSS, JS, Leaflet, fonts). `pipeline/map/html` packs it into one
  file.
- `tests/` (pytest, mirrors `pipeline/`: one folder per package, inside the folder of its tier) and `tests/browser/`
  (Playwright Test: `desktop/` in the system Chrome, `mobile/` in WebKit and in Chrome with touch; only `file:`, `data:`
  and `blob:` load). `tests/browser/tools/dump_text.mjs` stores the visible text of fixed states.
  `tests/browser/tools/readme_images.mjs` draws the images of `README.md`. `tests/compare_build.py` compares two builds
  during a refactoring.
- `docs/`: the living docs. They describe the project as it is now; Git keeps the past. `docs/architecture.md`
  (code structure, data flow of each source into the HTML, checks, publishing), `docs/texts.md` (map texts and the ⓘ
  protocol), `docs/design.md` (UI of `web/`), `docs/data-rules.md` (rules for numbers, thresholds of the checks),
  `docs/glossary.md` (German terms and their English names). Spec and plan of a branch are not in the repo (see Way of
  working).
- `sources/`: all originals and our extracts, each exactly once, under Git, in folders by origin (`zensus`,
  `frankfurt/statistics`, `frankfurt/parlis`, `frankfurt/geodata`, `frankfurt/offices`, `hessen/statistics`,
  `hessen/boris`, `hessen/lod2`, `hessen/alkis`, `regionalstatistik`, `arbeitsagentur`, `companies`, `other`).
  Provenance in `sources/README.md`. The pipeline reads from there (`SOURCES` and `CITY` in `config.py`).
- `reference/`: reference values for the checks, party colors.
- `research/`: findings by date as Markdown, only in the repo; scripts in `research/scripts/`, results in
  `research/results/`, see `research/README.md`. The German findings are not translated. New results go here at the end
  of a working session, but only when a file outside `research/` names them or they record a data situation. A
  finding that nothing outside `research/` names goes (rules in `research/README.md`).
- `cache/` (raw downloads of `update_sources`), `interim/` (interim data), `output/` (result): not in Git.
  `golden/` (a captured build) exists only while a refactoring runs and is not in Git.

## Publishing

The repo with `sources/` and `research/` lies on GitHub (`wohnentscheidFrankfurt/sozialraum-frankfurt`). The map is
online at https://wohnentscheid-frankfurt.de/sozialraum-frankfurt/ (public). The Astro integration of the website
(`integrations/map.mjs`) copies the built file during the website build. The website's Caddy proxies the tiles. The map
build copies nothing outside the repo.
- **The repo is the single source.** The page shows only the map, `sozialraum-frankfurt.html`. Reason: the team are
  volunteers; too much reading does not help.
- **Third-party files:** `sources/` holds what the build reads or an ⓘ or a finding names. After a complaint the file
  goes and `sources/README.md` points to archive.org.
- **Goal of the build:** the file works on its own. `output/data/` and `interim/check_report.md` stay local.
- **Findings:** new research results go to `research/` as Markdown at the end of a working session (rules above).
- **Downloads of the user:** a local inbox folder (path in the project memory). Sort into `sources/` by origin, then
  empty.

## Way of working (confirmed by the user)

1. First check the data for real: fetch, look at columns, add up sums. Name domain traps early, for example the
   ecological fallacy, counting rules, as-of dates and neutrality.
2. Then the spec and the plan as temporary files outside the repo, in the IntelliJ scratches folder of the user
   (path in the project memory), and the implementation with TDD on a
   branch. At the end a final review by a fresh reviewer. Before the merge, what stays valid moves into the matching
   topic file in `docs/` or a README. Then merge to `main`. After the merge, docs and code speak for themselves.
3. Short status messages during long runs, otherwise no questions. Ask real decisions one at a time, with a
   recommendation.
4. If the spec changes, add an addendum and tell the user.
5. A decision made in chat updates the matching topic file in `docs/` (or a README) in the same commit. There are
   no dated protocol files.

## Access to sources

- **PARLIS (city council):**
  - Search: `https://www.frankfurt-gestalten.de/api/search?q=<term>` (JSON)
  - Document: `https://www.stvv.frankfurt.de/download/<ID>.pdf`
  - Attachments: on `https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='<ID>'` the links `/parlisobj/…pdf`
  - Answers to local councils (ST) often hold numbers per quarter.
- **frankfurt.de:** answers with 403, also to headless Chrome. The user downloads such files by hand.
- **Annual report "Kommunale Wohnraumversorgung":** steps for a new report in
  `pipeline/use_cases/social_housing/README.md`, section "New annual report".

## Memory

The project memory of Claude Code lies outside the repo.
`sozialraum-frankfurt-karte.md` describes the state of the map and the open points.
