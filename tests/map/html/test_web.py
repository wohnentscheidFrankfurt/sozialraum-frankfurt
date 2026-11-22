"""Structure of the template web/map.html and of web/js. Their texts stand in pipeline/map/html/texts.de.yaml.
Behaviour stays with the browser tests (tests/browser/). tests/test_architecture.py checks title and header of web/."""
import re
from pathlib import Path

from pipeline import config
from pipeline.map.html.model import T, fill_text_markers
from tests.test_text_copies import js_literals

TEMPLATE = (config.WEB / "map.html").read_text(encoding="utf-8")
HTML = fill_text_markers(TEMPLATE, T["de"])  # the template with its German texts
JS_FILES = sorted((config.WEB / "js").glob("*.js"))


def test_template_starts_with_the_doctype():
    assert HTML.startswith("<!doctype html>\n")


def test_header_names_title_views_and_tabs():
    header = re.search(r'<header id="header">(.*?)</header>', HTML, re.S).group(1)
    assert "<h1>Sozialraum Frankfurt</h1>" in header
    assert re.findall(r'data-view="(\w+)"', header) == ["map", "history", "new_construction", "rent_burden"]
    tabs = re.findall(r'data-tab="(\w+)"', HTML)
    assert tabs == ["city", "area", "candidates", "help"]
    assert all(f'<section id="tab-{t}" class="tab' in HTML for t in tabs)
    labels = re.findall(r'data-(?:view|tab)="\w+"[^>]*>([^<]*)</button>', HTML)
    assert len(labels) == 8 and all(label.strip() for label in labels)
    # the template holds markers, the language file the words
    assert re.findall(r'data-(?:view|tab)="\w+"[^>]*>([^<]*)</button>', TEMPLATE) == [
        "{{views.map}}", "{{views.history}}", "{{views.new_construction}}", "{{views.rent_burden}}",
        "{{tabs.city}}", "{{tabs.area}}", "{{tabs.candidates}}", "{{tabs.help}}"]


def test_the_browser_app_genders_its_person_nouns():
    from tests.map.assembly.test_catalog import UNGENDERED
    files = [config.WEB / "map.html", *sorted((config.WEB / "js").glob("*.js"))]
    found = {f.name: UNGENDERED.findall(f.read_text(encoding="utf-8")) for f in files}
    assert {k: v for k, v in found.items() if v} == {}


# docs/design.md, Direct links: the fragments a link may carry. A published link never changes, so this list is fixed.
LINKS = ["karte", "trend", "trend/wem-gehoeren-die-wohnungen", "trend/wachstum-im-bestand", "trend/wer-waechst",
         "trend/grosse-haeuser", "neubau", "neubau/gefoerderte-wohnungen", "neubau/wohnungen-und-mieten", "miete",
         "miete/warmmiete-und-lohn", "miete/warmmiete-und-einkommen"]


def test_every_view_and_chart_has_a_fixed_link():
    from pipeline.use_cases.new_construction.catalog import RENTS_TEXTS, TEXTS
    from pipeline.use_cases.ownership_history.catalog import CHARTS
    from pipeline.use_cases.rent_burden.catalog import LOW_INCOME_TEXTS, WAGE_TEXTS
    views = dict(re.findall(r'data-view="(\w+)" data-link="([^"]+)"', HTML))
    assert views == {"map": "karte", "history": "trend", "new_construction": "neubau", "rent_burden": "miete"}
    charts = {"history": [c["link"] for c in CHARTS["de"].values()], "new_construction": [TEXTS["de"]["link"], RENTS_TEXTS["de"]["link"]],
              "rent_burden": [WAGE_TEXTS["de"]["link"], LOW_INCOME_TEXTS["de"]["link"]]}
    links = [f"{views[v]}/{c}" if c else views[v] for v in views for c in ["", *charts.get(v, [])]]
    assert links == LINKS
    assert all(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", part) for link in links for part in link.split("/"))


# docs/architecture.md, The map file. A link carries these ids and names, so they never change.
LAYER_IDS = ["OWN_PUBLIC", "OWN_COOP", "OWN_COMPANY", "OWN_PERSON", "OWN_STATE", "SOC_MIN_INCOME", "SOC_UNEMPLOYED",
             "SOC_INDEX", "LIF_ATTACHMENT", "HOU_RENTERS", "HOU_RENT", "LIF_RENT_BURDEN_RATIO", "SH_SHARE",
             "HOU_VACANT_MARKET", "HOU_VACANT_ALL", "HOU_PRE1919", "HOU_1949_1978", "LAND_VALUE", "ROOF_FLAT",
             "GAP_AREA", "ELEC_STRONGEST", "ELEC_TURNOUT"]
OVERLAY_NAMES = ["social_preservation", "social_preservation_pending", "townscape", "townscape_pending",
                 "pending_plans", "land_value", "flat_roofs", "building_gaps", "grid"]


def test_ids_of_map_links_never_change():
    from pipeline.map.assembly.catalog import CATALOG, map_overlays
    from tests.map.assembly.test_catalog import NUMBERS
    from pipeline.use_cases.election.catalog import T as ELECTION_TEXTS, election_indicators
    # the list shares of the election are built from data and stay out
    ids = [k.id for k in CATALOG["de"] + election_indicators([], ELECTION_TEXTS["de"]) if k.layer]
    assert ids == LAYER_IDS
    assert list(map_overlays(NUMBERS, "de")) == OVERLAY_NAMES


def test_help_explains_sharing():
    help_tab = re.search(r'<section id="tab-help".*?</section>', HTML, re.S).group(0)
    assert f"<strong>{T['de']['html.help.share.label']}</strong>" in help_tab


# A visible German word in a string literal of web/js. Its text belongs in the section `ui` of
# pipeline/map/html/texts.de.yaml and comes through APP.t. Comments are no literals (js_literals skips them).
GERMAN_WORD = re.compile(
    r"[äöüÄÖÜß„“]|k\. A\.|\b(und|oder|der|die|das|den|dem|des|ein|eine|eins|kein|keine|keins|nicht|nur|mit|von|bis|"
    r"unter|ab|alle|ja|nein|im|für|bei|je|es|gibt|sind|ist|gilt|gelten|hier|näher|ganz|Ganz|Rang|Stadt|Stadtteile?|"
    r"Bezirke?|Gebiet|Wohnungen|Häuser|Gebäude|Quelle|Quellen|Stand|Rechnung|Regel|Unsicherheit|Kriterien|"
    r"Kriterium|Erstellt|Einstellungen|Vorlage|Planung|Eigentum|Wahl|Wahlbeteiligung|Grenze|Anteil|Anteile|Ebene|"
    r"Liste|Treffer|Abfrage|Eigene|Verteilung|Vergleich|Milieuschutz|Ortsbildsatzung|Einwohner|Zensus|Umfragebezirk|"
    r"unbekannt|unsicher|heranzoomen|Gezählte|Baujahr|Gruppen|kandidaten|Wert|Werte|Profil)\b")
# literal -> reason; a literal with only these German words passes
JS_ALLOWED: dict[str, str] = {}


def german_literals(files) -> list[str]:
    return [f"{p.name}:{line}: {text}" for p in files for line, text in js_literals(p)
            if text not in JS_ALLOWED and GERMAN_WORD.search(text)]


def test_web_js_has_no_german_literal():
    assert german_literals(JS_FILES) == []


def test_the_guard_finds_german_literals(tmp_path):
    js = tmp_path / "a.js"
    js.write_text('// Stadt und Land in a comment\nAPP.a = "k. A.";\nAPP.b = `${n} von ${m}`;\nAPP.c = "Höhe";\n'
                  'APP.d = APP.t("legend.city", { value });\nAPP.e = "#tab-area .details-names";\n', encoding="utf-8")
    assert german_literals([js]) == ["a.js:2: k. A.", "a.js:3:  von ", "a.js:4: Höhe"]


UI_CALL = re.compile(r"APP\.t\(\s*\"([\w.]+)\"")


def ui_keys(tree: dict, prefix: str = "") -> set[str]:
    return {k for key, value in tree.items()
            for k in (ui_keys(value, f"{prefix}{key}.") if isinstance(value, dict) else {f"{prefix}{key}"})}


def test_every_ui_text_is_used_and_every_used_key_exists():
    js = "\n".join(p.read_text(encoding="utf-8") for p in JS_FILES)
    # a key is a literal, so this scan sees every key the browser asks for
    assert not re.findall(r"APP\.t\(\s*[^\s\"]", js)
    used, known = set(UI_CALL.findall(js)), ui_keys(T["de"].tree("ui"))
    assert used - known == set() and known - used == set()
