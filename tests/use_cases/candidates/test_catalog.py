from pipeline.map.assembly.catalog import CATALOG
from pipeline.use_cases.candidates.catalog import CUSTOM_NOTE, TEMPLATES, UPPER_END_NOTE
from pipeline.use_cases.election.catalog import election_indicators


def test_every_template_has_a_lead():
    assert all(t["lead"] for t in TEMPLATES)
    social = {t["id"]: t for t in TEMPLATES}["social_preservation"]["criteria"]
    assert len(social) == 5 and social[-1]["indicator"] == "PROT_SOCIAL"  # „fallen heraus“


def test_criteria_on_the_upper_end_explain_it():
    """A criterion on the end of a range names its indicator in `city`. Only it carries the note."""
    crit = [k for t in TEMPLATES for k in t["criteria"]]
    assert [k.get("note") for k in crit if "city" in k] == [UPPER_END_NOTE] * 2
    assert all("label" in k for k in crit if "city" in k)
    assert all("note" not in k for k in crit if "city" not in k)


def test_the_custom_note_names_the_groups_without_district_values():
    """CUSTOM_NOTE names each criterion group without district values: its group, or its title where the rest of the
    group has district values."""
    lists = [{"name": "CDU", "key": "ELEC_CDU", "color": "#000"}]
    missing = [k for k in [*CATALOG, *election_indicators(lists)]
               if k.criterion and k.type in ("number", "yes_no") and "district" not in k.levels]
    assert {k.section for k in missing} == {"ownership", "stock", "election"}
    assert {k.id for k in missing if k.section == "stock"} == {"SH_SHARE"}
    names = {k.group for k in missing if k.section != "stock"} | {k.title for k in missing if k.section == "stock"}
    assert len(names) == 3 and all(n in CUSTOM_NOTE for n in names), names
