import re

from pipeline import config
from pipeline.shared.core.indicator import year_of
from pipeline.use_cases.ownership_history import catalog
from pipeline.use_cases.ownership_history.catalog import BAR_ORDER, EXAMPLES
from pipeline.use_cases.ownership_history.model import HISTORY_GROUPS
from pipeline.use_cases.ownership_shares.catalog import EXAMPLES as COMPANY_EXAMPLES
from pipeline.shared.zensus.model import SIZES

# the German texts of the view; the tests take each text from its constant
CHARTS, GROUP_TEXTS, HISTORY_SOURCE, SECTORS, SIZE_LABELS = (
    getattr(catalog, name)["de"] for name in ("CHARTS", "GROUP_TEXTS", "HISTORY_SOURCE", "SECTORS", "SIZE_LABELS"))
TEXTS = catalog.T["de"]

# greys for „Privat“, reds for „Gemeinschaft“ (RLS city profile)
PALETTE = {"housing_company": "#262626", "other_company": "#575757", "condo": "#8c8c8c", "person": "#bfbfbf",
           "public": "#d40000", "coop": "#8c0000", "nonprofit": "#f07067"}


def test_every_group_has_title_and_colour():
    assert list(GROUP_TEXTS) == list(HISTORY_GROUPS) and sorted(BAR_ORDER) == sorted(HISTORY_GROUPS)
    assert BAR_ORDER[:2] == ["housing_company", "other_company"]
    # pipeline/use_cases/ownership_history/README.md: white text on #d40000 reaches 5.5:1, on #fe0000 nothing reaches 4.5:1
    assert {k: t["color"] for k, t in GROUP_TEXTS.items()} == PALETTE
    assert all(t["title"] for t in GROUP_TEXTS.values())
    # long titles break into two lines in the chart „arrows“
    assert all(" ".join(t.get("lines", [t["title"]])) == t["title"] for t in GROUP_TEXTS.values())


def test_sectors_split_the_groups_into_two_blocks():
    """Sectors as in the city profile of the Rosa-Luxemburg-Stiftung: plain sums of Zensus classes."""
    assert {k: s["groups"] for k, s in SECTORS.items()} == {
        "private": ["housing_company", "other_company", "condo", "person"],
        "community": ["public", "coop", "nonprofit"]}
    # each sector is drawn in the main colour of its first group (docs/design.md, Sector boundary)
    assert all(t["color"] == GROUP_TEXTS[t["groups"][0]]["color"] for t in SECTORS.values())
    # the bars show each sector as one block
    assert BAR_ORDER == [g for s in SECTORS.values() for g in s["groups"]]


# Nouns of the example texts that name no owner
PLAIN_NOUNS = {"Kirchen", "Familienunternehmen", "Frankfurt", "Offenbach"}


def unsourced_words(examples: list[str], names: set[str]) -> list[str]:
    """The capitalised words of the example texts once the sourced names are gone. A name starts with a capital letter,
    so a name without an entry in EXAMPLES is left over. Lower-case words may change freely."""
    rest = " ".join(e.removeprefix("Z. B. ") for e in examples)
    for name in sorted(names, key=len, reverse=True):
        rest = rest.replace(name, " ")
    return [w for w in re.findall(r"\w[\w-]*", rest) if w[0].isupper() and w not in PLAIN_NOUNS]


def test_every_named_example_has_a_source():
    """Each example of EXAMPLES stands in an „example“ text of a group and has a source the build reads
    (docs/texts.md, Trend). Each name in an „example“ text has an entry of EXAMPLES here or in ownership_shares.
    „Z. B. …“ opens each example sentence."""
    names = {e["name"] for e in EXAMPLES + COMPANY_EXAMPLES}
    examples = [t["example"] for t in GROUP_TEXTS.values() if t["example"]]
    texts = " ".join(examples)
    assert {e["name"] for e in EXAMPLES} <= {n for n in names if n in texts}
    assert all(e.startswith("Z. B. ") for e in examples)
    assert unsourced_words(examples, names) == []
    assert all(hasattr(config, e["source"]) for e in EXAMPLES)


def test_a_name_without_a_source_is_left_over():
    names = {e["name"] for e in EXAMPLES + COMPANY_EXAMPLES}
    examples = [t["example"] for t in GROUP_TEXTS.values() if t["example"]]
    assert unsourced_words([*examples, "Z. B. Vonovia und Adler Group."], names) == ["Adler", "Group"]


def test_the_public_group_says_why_the_view_joins_kommune_bund_and_land():
    """docs/texts.md, Texts per view: the Zensus 4000W-1011 counts the Nassauische Heimstätte as Land in 2011 and as
    Kommune in 2022, and the tooltip of the group says so."""
    about = GROUP_TEXTS["public"]["about"]
    assert "Nassauische Heimstätte" in about and year_of(TEXTS["core.z11_as_of"]) in about
    assert year_of(TEXTS["core.z22_as_of"]) in about
    assert all(w in about for w in ("Kommune", "Bund", "Land"))


def test_chart_texts():
    # pipeline/use_cases/ownership_history/README.md
    assert list(CHARTS) == ["houses", "decades", "arrows", "sizes"]
    # every heading names the companies as private: ABG is a company too (docs/data-rules.md, Groups)
    assert all("rivat" in c["title"] for c in CHARTS.values())
    assert all(len(c["title"]) <= 61 for c in CHARTS.values())


def test_every_chart_has_its_link():
    """docs/design.md, Direct links: a link names the question of the chart and never changes once published."""
    assert [c["link"] for c in CHARTS.values()] == ["wem-gehoeren-die-wohnungen", "wachstum-im-bestand",
                                                    "wer-waechst", "grosse-haeuser"]


def test_size_labels():
    assert list(SIZE_LABELS) == SIZES


def test_housing_company_examples_name_sahle_wohnen_with_two_sources():
    """The third example. The Magistrat names the owner, the company page says family-run."""
    assert "Sahle Wohnen" in GROUP_TEXTS["housing_company"]["example"]
    sahle = {e["source"]: e["phrases"] for e in EXAMPLES if e["name"] == "Sahle Wohnen"}
    assert set(sahle) == {"SAHLE_SUBSIDISED_PDF", "SAHLE_PAGE_HTML"}
    assert "Sahle Wohnen 915" in sahle["SAHLE_SUBSIDISED_PDF"]
    assert any("familiengeführt" in p for p in sahle["SAHLE_PAGE_HTML"])
    # the ⓘ of „Private Unternehmen“ keeps its examples
    from pipeline.use_cases.ownership_shares.catalog import INDICATORS
    info = next(i for i in INDICATORS["de"] if i.id == "OWN_COMPANY").calc
    assert "Sahle" not in info and "Sahle" not in str(COMPANY_EXAMPLES)


def test_one_source_line_with_the_licence_below_the_charts():
    assert "dl-de/by-2-0" in HISTORY_SOURCE and all("source" not in c for c in CHARTS.values())


def test_texts_of_person_and_condo_name_owners_as_persons():
    # docs/texts.md, Owners are „Personen“
    assert all("Personen" in GROUP_TEXTS[g]["about"] for g in ("person", "condo"))
    assert not any("Menschen" in str(t) for t in GROUP_TEXTS.values())


def test_every_decade_of_the_source_has_its_label():
    """The rows of the chart „decades“ are texts (decade_labels.<key>). In German they read as the source writes them,
    so the German view stays as it was."""
    from pipeline.shared.zensus.tables import read_buildings_by_decade
    decades, _ = read_buildings_by_decade(config.ZENSUS_3000G_2001.read_text(encoding="utf-8"))
    assert [TEXTS[f"decade_labels.{d['key']}"] for d in decades] == [d["label"] for d in decades]
    assert set(TEXTS.tree("decade_labels")) == {d["key"] for d in decades}
