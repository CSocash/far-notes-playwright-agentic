"""API helpers for finding and changing sections and subsections (test setup and verification)."""

import re

REFERENCE_PATTERN = re.compile(r"^(\d+\.\d+)(?:\(([a-z0-9]+)\))?$")


def get_sections(request_context, part):
    res = request_context.get(f"/api/regulations?part={part}")
    assert res.status == 200, f"GET part {part}: {res.status} {res.text()}"
    return res.json()


def find_section(sections, section_number):
    """The first section whose heading starts with the section number, e.g. "91.103"."""
    for section in sections:
        if re.match(rf"^\s*{re.escape(section_number)}\b", section["regulation"]):
            return section
    raise AssertionError(f"No section {section_number}")


def find_subsection(sections, reference):
    """A subsection by reference: "91.103(a)", or "91.5" for an Entire section item."""
    match = REFERENCE_PATTERN.match(reference)
    assert match, f"Bad reference {reference!r}"
    section_number, code = match.group(1), match.group(2) or ""
    for subsection in find_section(sections, section_number)["subsections"]:
        if subsection["code"] == code:
            return subsection
    raise AssertionError(f"No subsection {reference}")


def all_subsections(sections):
    return [subsection for section in sections for subsection in section["subsections"]]


def patch_subsection(request_context, part, subsection_id, **fields):
    return request_context.patch(f"/api/subsections/{subsection_id}?part={part}", data=fields)


def create_section(request_context, part, heading):
    """Adds a section, then sets its heading. Returns the section as the API reports it."""
    created = request_context.post(f"/api/regulations?part={part}", data={})
    assert created.status == 201, f"POST part {part}: {created.status} {created.text()}"
    res = request_context.patch(f"/api/regulations/{created.json()['id']}?part={part}", data={"regulation": heading})
    assert res.status == 200, f"PATCH heading: {res.status} {res.text()}"
    return res.json()
