"""Phone layout: text field sizes on touch screens versus desktop, and the iPhone safe area.
iOS zooms into a focused field whose text is under 16px, which leaves the page cut off on the right,
and the app's pages are drawn under the status bar unless they pad for the safe area
(both seen in the iOS app on 2026-10-30)."""

import re

import pytest
from playwright.sync_api import expect

from tests.mocks.data import custom_section, many_items, preflight
from tests.pages.tracker_page import TrackerPage
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


def _open_tracker(page, expand=True):
    serve_tracker_from_disk(page)
    mock_signed_in(page)
    mock_regulations(page, {"91": [preflight(), custom_section()]})
    page.goto("/")
    page.get_by_text("Connected to SQLite").wait_for()
    if expand:
        TrackerPage(page).expand_all.click()   # sections start collapsed


def _font_size(page, selector):
    return page.locator(selector).first.evaluate("element => getComputedStyle(element).fontSize")


@pytest.mark.mobile("ios")
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


IPHONE_SAFE_AREA = {"top": 62, "bottom": 34}   # status bar and home indicator, iPhone 17 portrait


def _top(locator):
    return locator.bounding_box()["y"]


@pytest.mark.mobile("ios")
def test_tc_523_pages_stay_clear_of_the_iphone_status_bar(iphone_page, page):
    phone = iphone_page
    phone.context.new_cdp_session(phone).send("Emulation.setSafeAreaInsetsOverride", {"insets": IPHONE_SAFE_AREA})

    serve_auth_pages_from_disk(phone)
    mock_signed_out(phone)
    phone.goto("/login")
    padding = phone.evaluate("(({ paddingTop, paddingBottom }) => [paddingTop, paddingBottom])(getComputedStyle(document.body))")
    assert padding == ["62px", "34px"]
    assert _top(phone.get_by_role("link", name="FAA Regulations Study Log sign in")) >= IPHONE_SAFE_AREA["top"]

    _open_tracker(phone, expand=False)
    for control in [
        phone.get_by_role("link", name="Part 91 Study Log home"),
        phone.get_by_role("combobox", name="Select regulation part"),
        phone.get_by_role("button", name="Log out"),
    ]:
        assert _top(control) >= IPHONE_SAFE_AREA["top"]

    # Desktop has no safe area, so the padding is 0 and the layout is unchanged.
    serve_auth_pages_from_disk(page)
    mock_signed_out(page)
    page.goto("/login")
    assert page.evaluate("getComputedStyle(document.body).padding") == "0px"


def _box(locator):
    return locator.bounding_box()


@pytest.mark.mobile("ios")
def test_tc_524_on_a_phone_each_study_item_is_a_card_that_fits_the_screen(iphone_page, page):
    phone = iphone_page
    _open_tracker(phone)
    item = TrackerPage(phone).item("91.103(a)")
    reference = phone.get_by_role("link", name="Open 91.103(a) in the eCFR in a new tab")

    assert phone.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    expect(item.row).to_have_count(1)   # still a table row for screen readers and locators

    row, ref, covered, date, notes = (_box(x) for x in (item.row, reference, item.covered_label, item.date, item.notes))
    screen_width = phone.viewport_size["width"]
    for field in (covered, date, notes):
        assert field["x"] >= 0 and field["x"] + field["width"] <= screen_width
    assert ref["y"] < covered["y"] < notes["y"]                  # reference, then covered/date, then notes
    assert abs((covered["y"] + covered["height"] / 2) - (date["y"] + date["height"] / 2)) < 8   # covered and date share a line
    assert notes["width"] >= row["width"] * 0.8                  # notes span the card

    # Desktop keeps the table: covered, date and notes side by side on one line.
    _open_tracker(page)
    desktop = TrackerPage(page).item("91.103(a)")
    covered, date, notes = (_box(x) for x in (desktop.covered_label, desktop.date, desktop.notes))
    assert covered["x"] < date["x"] < notes["x"]
    assert abs(covered["y"] - notes["y"]) < 20


COVERED_BY = """([y]) => [40, 200, 360].map((x) => {
  const element = document.elementFromPoint(x, y);
  return element === document.body ? "body" : element.tagName.toLowerCase() + "." + element.className;
})"""


@pytest.mark.mobile("ios")
def test_tc_525_scrolled_content_never_shows_behind_the_status_bar_or_home_indicator(iphone_page, page):
    phone = iphone_page
    phone.context.new_cdp_session(phone).send("Emulation.setSafeAreaInsetsOverride", {"insets": IPHONE_SAFE_AREA})
    serve_tracker_from_disk(phone)
    mock_signed_in(phone)
    mock_regulations(phone, {"91": many_items(40)})
    # A failed save is the quickest way to show a toast.
    phone.route(re.compile(r"/api/subsections/\d+\?part="), lambda route: route.fulfill(status=500, json={"error": "Disk full"}))
    phone.goto("/")
    phone.get_by_text("Connected to SQLite").wait_for()
    TrackerPage(phone).expand_all.click()

    phone.locator("tr").nth(20).scroll_into_view_if_needed()   # the list now runs under both edges of the screen
    height = phone.viewport_size["height"]
    # Only the body's safe-area covers are hit near the edges; nothing from the page shows through.
    assert phone.evaluate(COVERED_BY, [30]) == ["body"] * 3
    assert phone.evaluate(COVERED_BY, [height - 15]) == ["body"] * 3

    phone.get_by_role("checkbox").nth(20).check(force=True)    # the input is visually hidden behind its checkmark
    toast = phone.get_by_role("status")
    expect(toast).to_have_text("Could not save study item: Disk full")
    expect(toast).to_have_css("opacity", "1")
    box = toast.bounding_box()
    assert box["y"] + box["height"] <= height - IPHONE_SAFE_AREA["bottom"]

    # Desktop: the covers have no height, so nothing is hidden.
    serve_auth_pages_from_disk(page)
    mock_signed_out(page)
    page.goto("/login")
    covers = page.evaluate("['::before', '::after'].map((pseudo) => getComputedStyle(document.body, pseudo).height)")
    assert covers == ["0px", "0px"]
