"""Collapsible sections: sections start collapsed, each header has a toggle and a covered/total count,
and the toolbar has Expand all / Collapse all. Searching opens the sections that have matches."""

import re

import pytest
from playwright.sync_api import expect

from tests.mocks.data import custom_section, entire_section, preflight
from tests.mocks.routes import mock_regulations, mock_signed_in, serve_tracker_from_disk

PREFLIGHT = "91.103 — Preflight action"
TYPE_RATING = "91.5 — Pilot in command of aircraft requiring a type rating"


@pytest.fixture
def sections():
    return [preflight(covered=True, date="2026-10-28"), entire_section()]


@pytest.fixture
def tracker(page, tracker_page, sections):
    serve_tracker_from_disk(page)
    mock_signed_in(page)
    mock_regulations(page, {"91": sections})
    tracker_page.goto()
    return tracker_page


def item_rows(page):
    """Study item rows (not section headers): the ones with a covered checkbox."""
    return page.locator("#regulation-rows tr").filter(has=page.get_by_role("checkbox"))


def test_tc_526_sections_start_collapsed_with_their_progress_showing(page, tracker):
    preflight_row, type_rating_row = tracker.section(PREFLIGHT), tracker.section(TYPE_RATING)

    expect(tracker.section_rows).to_have_count(2)
    expect(preflight_row.toggle).to_have_attribute("aria-expanded", "false")
    expect(type_rating_row.toggle).to_have_attribute("aria-expanded", "false")
    expect(item_rows(page)).to_have_count(0)
    expect(preflight_row.row.locator(".section-progress")).to_have_text("1/2 covered")
    expect(type_rating_row.row.locator(".section-progress")).to_have_text("0/1 covered")
    expect(tracker.results_count).to_have_text("Showing 3 of 3 study items")
    expect(tracker.covered_count).to_have_text("1")
    expect(tracker.remaining_count).to_have_text("2")


def test_tc_527_a_sections_toggle_expands_and_collapses_only_that_section(page, tracker):
    toggle = tracker.section(PREFLIGHT).toggle

    toggle.click()
    expect(tracker.item("91.103(a)").covered_checkbox).to_be_attached()
    expect(tracker.item("91.103(b)").notes).to_be_visible()
    expect(toggle).to_have_attribute("aria-expanded", "true")
    expect(toggle).to_be_focused()
    expect(tracker.section(TYPE_RATING).toggle).to_have_attribute("aria-expanded", "false")
    expect(item_rows(page)).to_have_count(2)

    toggle.click()
    expect(item_rows(page)).to_have_count(0)
    expect(toggle).to_have_attribute("aria-expanded", "false")


def test_tc_528_expand_all_and_collapse_all(page, tracker):
    toggles = page.get_by_role("button", name=re.compile(r"^Study items in"))

    tracker.expand_all.click()
    expect(item_rows(page)).to_have_count(3)
    for toggle in toggles.all():
        expect(toggle).to_have_attribute("aria-expanded", "true")

    tracker.collapse_all.click()
    expect(item_rows(page)).to_have_count(0)
    for toggle in toggles.all():
        expect(toggle).to_have_attribute("aria-expanded", "false")


def test_tc_529_searching_opens_the_sections_with_matches_and_clearing_restores_them(page, tracker):
    tracker.search.fill("runway")
    expect(tracker.item("91.103(b)").notes).to_be_visible()
    expect(tracker.section_rows).to_have_count(1)            # 91.5 has no match, so it isn't shown

    tracker.section(PREFLIGHT).toggle.click()
    expect(item_rows(page)).to_have_count(0)
    expect(tracker.search).to_have_value("runway")            # still searching

    tracker.search.fill("")
    expect(tracker.section_rows).to_have_count(2)
    expect(item_rows(page)).to_have_count(0)
    expect(tracker.section(PREFLIGHT).toggle).to_have_attribute("aria-expanded", "false")


def test_tc_530_a_sections_progress_updates_when_an_item_is_marked_covered(page, tracker, sections):
    def echo_patch(route):
        item_id = int(re.search(r"/api/subsections/(\d+)", route.request.url).group(1))
        item = next(sub for sec in sections for sub in sec["subsections"] if sub["id"] == item_id)
        route.fulfill(json={**item, **route.request.post_data_json})

    page.route(re.compile(r"/api/subsections/\d+\?part="), echo_patch)
    preflight_row = tracker.section(PREFLIGHT)
    preflight_row.expand()

    tracker.item("91.103(b)").covered_checkbox.check()

    expect(preflight_row.row.locator(".section-progress")).to_have_text("2/2 covered")


def test_tc_531_a_newly_added_section_opens_expanded(page, tracker):
    new_section = {**custom_section(""), "regulation": ""}
    page.route(
        re.compile(r"/api/regulations\?part=91$"),
        lambda route: route.fulfill(status=201, json=new_section) if route.request.method == "POST" else route.fallback(),
    )

    tracker.add_section.click()

    new_row = tracker.last_section()
    expect(new_row.toggle).to_have_attribute("aria-expanded", "true")
    expect(item_rows(page)).to_have_count(1)                  # only the new section's "Entire section"
    expect(page.locator("#regulation-rows tr").last).to_contain_text("Entire section")
    expect(tracker.section(PREFLIGHT).toggle).to_have_attribute("aria-expanded", "false")
    expect(tracker.section(TYPE_RATING).toggle).to_have_attribute("aria-expanded", "false")
