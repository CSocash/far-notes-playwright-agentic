from datetime import datetime, timezone

import pytest
from playwright.sync_api import expect

# 12:00 in America/New_York (the conftest timezone_id), so "today" is 2026-06-01 there.
FIXED_NOW = datetime(2026, 6, 1, 16, 0, tzinfo=timezone.utc)


@pytest.mark.smoke
def test_tc_006_marking_a_subsection_covered_persists(signed_in_page, tracker_page):
    page = signed_in_page
    page.clock.set_fixed_time(FIXED_NOW)
    tracker_page.goto()
    preflight = tracker_page.section("91.103 — Preflight action")
    preflight.expand()
    item = tracker_page.item("91.103(a)")

    with page.expect_response(lambda r: "/api/subsections/" in r.url and r.request.method == "PATCH") as saved:
        item.covered_checkbox.check()
    assert saved.value.status == 200

    def assert_covered_today():
        expect(item.covered_checkbox).to_be_checked()
        expect(item.covered_label).to_have_text("Yes")
        expect(item.date).to_have_value("2026-06-01")
        expect(tracker_page.covered_count).to_have_text("1")
        expect(tracker_page.remaining_count).to_have_text("246")

    assert_covered_today()

    page.reload()
    expect(page.get_by_text("Connected to SQLite")).to_be_visible()
    preflight.expand()   # sections start collapsed again after a reload
    assert_covered_today()
