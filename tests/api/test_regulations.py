import pytest

from tests.support.regulations import (
    all_subsections,
    find_section,
    find_subsection,
    get_sections,
    patch_subsection,
)


@pytest.mark.smoke
def test_tc_103_patching_a_locked_heading_returns_403(api):
    locked = find_section(get_sections(api, "91"), "91.103")

    res = api.patch(f"/api/regulations/{locked['id']}?part=91", data={"regulation": "hacked"})

    assert res.status == 403
    assert res.json() == {"error": "This regulation heading is protected and cannot be edited."}
    assert find_section(get_sections(api, "91"), "91.103")["regulation"] == "91.103 — Preflight action"


@pytest.mark.smoke
def test_tc_118_progress_is_tracked_separately_for_each_part(api):
    item = find_subsection(get_sections(api, "61"), "61.3(a)")

    res = patch_subsection(api, "61", item["id"], covered=True)
    assert res.status == 200

    part_91 = all_subsections(get_sections(api, "91"))
    assert sum(subsection["covered"] for subsection in part_91) == 0

    part_61 = get_sections(api, "61")
    assert sum(subsection["covered"] for subsection in all_subsections(part_61)) == 1
    assert find_subsection(part_61, "61.3(a)")["covered"] is True


@pytest.mark.smoke
def test_tc_131_every_account_gets_its_own_copy_of_the_starter_lists(api, other_user):
    u1_item = find_subsection(get_sections(api, "91"), "91.103(a)")
    res = patch_subsection(api, "91", u1_item["id"], covered=True, notes="U1 private note")
    assert res.status == 200

    u2_sections = get_sections(other_user["api"], "91")
    u2_item = find_subsection(u2_sections, "91.103(a)")
    assert sum(subsection["covered"] for subsection in all_subsections(u2_sections)) == 0
    assert u2_item["covered"] is False
    assert u2_item["notes"] == ""

    u1_ids = {subsection["id"] for subsection in all_subsections(get_sections(api, "91"))}
    u2_ids = {subsection["id"] for subsection in all_subsections(u2_sections)}
    assert u1_ids.isdisjoint(u2_ids)
