"""Text field sizes on touch screens versus desktop. iOS zooms into a focused field whose text is
under 16px, which leaves the page cut off on the right (seen in the iOS app on 2026-10-30)."""

import pytest
from playwright.sync_api import expect

from tests.mocks.data import custom_section, preflight
from tests.mocks.routes import mock_regulations, mock_signed_in, mock_signed_out, serve_auth_pages_from_disk, serve_tracker_from_disk

AUTH_PAGES = ["/login", "/create-account", "/forgot-password", "/reset-password"]
TRACKER_FIELDS = {
    "search": "#search",
    "part menu": "#part-select",
    "section heading": ".section-row .regulation-input",
    "date": ".date-input",
    "notes": ".notes-input",
}


@pytest.fixture
def iphone_page(browser, playwright, base_url):
    """A page emulating an iPhone: touch input, so (pointer: coarse) matches."""
    device = {key: value for key, value in playwright.devices["iPhone 17"].items() if key != "default_browser_type"}
    context = browser.new_context(**device, base_url=base_url)
    page = context.new_page()
    yield page
    context.close()


def _open_tracker(page):
    serve_tracker_from_disk(page)
    mock_signed_in(page)
    mock_regulations(page, {"91": [preflight(), custom_section()]})
    page.goto("/")
    page.get_by_text("Connected to SQLite").wait_for()


def _font_size(page, selector):
    return page.locator(selector).first.evaluate("element => getComputedStyle(element).fontSize")


def test_tc_521_touch_screens_get_16px_text_fields(iphone_page):
    page = iphone_page
    assert page.evaluate("matchMedia('(pointer: coarse)').matches") is True   # control: the rule's condition holds

    serve_auth_pages_from_disk(page)
    mock_signed_out(page)
    for path in AUTH_PAGES:
        page.goto(path)
        inputs = page.locator(".auth-input")
        expect(inputs.first).to_be_visible()
        sizes = inputs.evaluate_all("elements => elements.map((element) => getComputedStyle(element).fontSize)")
        assert sizes and set(sizes) == {"16px"}, f"{path}: {sizes}"

    _open_tracker(page)
    sizes = {name: _font_size(page, selector) for name, selector in TRACKER_FIELDS.items()}
    assert sizes == {name: "16px" for name in TRACKER_FIELDS}


def test_tc_522_desktop_keeps_the_compact_field_sizes(page):
    assert page.evaluate("matchMedia('(pointer: coarse)').matches") is False

    serve_auth_pages_from_disk(page)
    mock_signed_out(page)
    page.goto("/login")
    assert _font_size(page, ".auth-input") == "12px"

    _open_tracker(page)
    assert {name: _font_size(page, selector) for name, selector in TRACKER_FIELDS.items()} == {
        "search": "11px",
        "part menu": "11px",
        "section heading": "11px",
        "date": "10px",
        "notes": "10px",
    }
