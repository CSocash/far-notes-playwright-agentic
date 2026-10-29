"""Mock data builders matching the real API contract (far-notes-domain/api-reference.md):
Section = {id, regulation, isLocked, subsections}; Subsection = {id, code, title, covered, date, notes}.
Keys stay camelCase because they mirror the API."""

import itertools

_ids = itertools.count(1)


def subsection(**over):
    return {"id": next(_ids), "code": "a", "title": "Title", "covered": False, "date": "", "notes": "", **over}


def section(heading, subsections, **over):
    return {"id": next(_ids), "regulation": heading, "isLocked": True, "subsections": subsections, **over}


def preflight(**subsection_overrides):
    """91.103 with its real catalog titles. subsection_overrides apply to (a), e.g. notes="…"."""
    return section("91.103 — Preflight action", [
        subsection(code="a", title="For a flight under IFR or a flight not in the vicinity of an airport, weather "
                                   "reports and forecasts, fuel requirements, alternatives available if…",
                   **subsection_overrides),
        subsection(code="b", title="For any flight, runway lengths at airports of intended use, and the following "
                                   "takeoff and landing distance information:"),
    ])


def entire_section():
    return section("91.5 — Pilot in command of aircraft requiring a type rating",
                   [subsection(code="", title="Entire section")])


def custom_section(heading="91.999 — My custom topic"):
    return section(heading, [subsection(code="", title="Entire section")], isLocked=False)


def many_items(total, covered_count=0):
    """One section with `total` items, for count and rounding tests (e.g. 247)."""
    return [section("91.900 — Bulk", [subsection(code=str(i), covered=i < covered_count) for i in range(total)])]
