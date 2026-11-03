"""The real iOS app in the Simulator (Appium), against the test server. Run with `pytest --run-device`;
add `--slowmo 1000` to pause a second after each step so you can watch it."""

import datetime
import time

import pytest

from tests.support.regulations import find_subsection, get_sections

PREFLIGHT = "91.103 — Preflight action"


def wait_for_saved(api, reference, timeout=10):
    """Polls the API until the item is covered; returns the last copy seen. The app autosaves after 350 ms."""
    deadline = time.monotonic() + timeout
    while True:
        item = find_subsection(get_sections(api, "91"), reference)
        if item["covered"] or time.monotonic() > deadline:
            return item
        time.sleep(0.25)   # polling the server's state, not waiting for time to pass


@pytest.mark.mobile("ios")
def test_tc_022_on_the_ios_app_a_covered_item_is_saved_and_the_sign_in_survives_a_relaunch(ios_app, api, fresh_user):
    ios_app.sign_in(fresh_user["username"], fresh_user["password"])
    ios_app.wait_for_tracker()
    ios_app.tap(ios_app.section_toggle(PREFLIGHT))
    covered = ios_app.covered_switch("91.103(a)")
    assert covered.get_attribute("value") == "0"   # control: starts uncovered

    ios_app.tap(ios_app.covered_control("91.103(a)"))

    assert ios_app.wait_for_value(covered, "1") == "1"
    saved = wait_for_saved(api, "91.103(a)")
    assert saved["covered"] is True
    # The Simulator uses the Mac's clock and time zone, which can't be fixed from here.
    assert saved["date"] == datetime.date.today().isoformat()

    ios_app.relaunch()

    ios_app.wait_for_tracker()   # still signed in: no sign-in screen after the relaunch
    ios_app.tap(ios_app.section_toggle(PREFLIGHT))
    assert ios_app.wait_for_value(ios_app.covered_switch("91.103(a)"), "1") == "1"
