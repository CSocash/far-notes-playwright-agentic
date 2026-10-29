import pytest
from playwright.sync_api import expect

from tests.mocks.data import custom_section, preflight
from tests.mocks.routes import mock_regulations, mock_signed_in, serve_tracker_from_disk

HEADING_PAYLOAD = '<img src=x onerror="window.__xss=1">91.1 test'
NOTE_PAYLOAD = "<script>window.__xss=1</script>"


@pytest.fixture
def dialogs(page):
    """Records any alert/confirm/prompt; injected script would typically trigger one."""
    seen = []
    page.on("dialog", lambda dialog: (seen.append(dialog.message), dialog.dismiss()))
    return seen


def open_tracker(page, part_91_sections):
    serve_tracker_from_disk(page)
    mock_signed_in(page)
    mock_regulations(page, {"91": part_91_sections})
    page.goto("/")
    expect(page.get_by_text("Connected to SQLite")).to_be_visible()


def assert_no_script_ran(page, dialogs):
    expect(page.locator("#regulation-rows img")).to_have_count(0)
    expect(page.locator("#regulation-rows script")).to_have_count(0)
    assert page.evaluate("window.__xss") is None
    assert dialogs == []


@pytest.mark.smoke
def test_tc_211_html_in_a_heading_is_shown_as_text(page, dialogs):
    open_tracker(page, [custom_section(HEADING_PAYLOAD)])
    page.reload()
    expect(page.get_by_text("Connected to SQLite")).to_be_visible()

    # A heading without a section number renders as an <a> with no href, which has no link role,
    # so the class is the only stable hook for it.
    expect(page.locator(".section-heading-link")).to_have_text(HEADING_PAYLOAD)
    assert_no_script_ran(page, dialogs)


@pytest.mark.smoke
def test_tc_212_html_in_notes_is_shown_as_text(page, dialogs):
    open_tracker(page, [preflight(notes=NOTE_PAYLOAD)])
    page.reload()
    expect(page.get_by_text("Connected to SQLite")).to_be_visible()
    notes = page.get_by_label("Notes for 91.103(a)")

    expect(notes).to_have_value(NOTE_PAYLOAD)
    assert_no_script_ran(page, dialogs)

    page.get_by_role("searchbox", name="Search regulations or notes").fill("script")

    expect(page.locator("#results-count")).to_have_text("Showing 1 of 2 study items")
    expect(notes).to_have_value(NOTE_PAYLOAD)
    assert_no_script_ran(page, dialogs)
