import pytest
from playwright.sync_api import expect

from tests.mocks.data import custom_section
from tests.mocks.routes import mock_heading_saves, mock_regulations, mock_signed_in, serve_tracker_from_disk

ORIGINAL = "91.999 — Original"
RENAMED = "91.998 — Renamed"


@pytest.fixture
def custom_heading(page, tracker_page):
    """The tracker with one unlocked section; heading saves are answered like the real server."""
    section = custom_section(ORIGINAL)
    serve_tracker_from_disk(page)
    mock_signed_in(page)
    mock_regulations(page, {"91": [section]})
    saves = mock_heading_saves(page, [section])
    tracker_page.goto()
    return saves


@pytest.mark.parametrize(("key", "expected_heading"), [("Enter", RENAMED), ("Escape", ORIGINAL)])
def test_tc_519_saving_or_cancelling_a_heading_edit_hides_the_input(page, tracker_page, custom_heading, key, expected_heading):
    section = tracker_page.section(ORIGINAL)
    section.edit_button.click()
    section.heading_input.fill(RENAMED)

    with page.expect_request(lambda r: r.method == "PATCH" and r.post_data_json == {"regulation": expected_heading}):
        section.heading_input.press(key)

    expect(page.get_by_role("textbox", name="Regulation section")).to_be_hidden()
    # Look the row up again by the heading it should now show (it no longer contains ORIGINAL after Enter).
    expect(tracker_page.section(expected_heading).heading_link).to_have_text(expected_heading)
    # Exactly once: in the link, not also in a still-visible text box.
    expect(tracker_page.section_rows.get_by_text(expected_heading, exact=True)).to_have_count(1)
    expect(tracker_page.section_rows.get_by_role("textbox")).to_have_count(0)


def test_tc_520_the_edit_buttons_accessible_name_follows_the_saved_heading(page, tracker_page, custom_heading):
    tracker_page.section(ORIGINAL).rename(RENAMED)

    expect(page.get_by_role("button", name=f"Edit section heading {RENAMED}", exact=True)).to_be_visible()
    expect(page.get_by_role("button", name=f"Edit section heading {ORIGINAL}", exact=True)).to_have_count(0)
    expect(page.get_by_role("link", name=f"Open {RENAMED} in the eCFR in a new tab", exact=True)).to_be_visible()
