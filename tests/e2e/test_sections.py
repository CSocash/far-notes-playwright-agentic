import pytest
from playwright.sync_api import expect

HEADING = "91.999 — My custom topic"
ECFR_URL = "https://www.ecfr.gov/current/title-14/part-91/section-91.999#section-91.999"


@pytest.mark.smoke
def test_tc_010_add_a_custom_section_and_save_its_heading(signed_in_page, tracker_page):
    page = signed_in_page
    tracker_page.goto()

    with page.expect_response(
        lambda r: "/api/regulations?part=91" in r.url and r.request.method == "POST"
    ) as created:
        tracker_page.add_section.click()
    assert created.value.status == 201
    expect(tracker_page.toast).to_have_text("New section added. Enter a regulation number to get started.")

    # Typing also queues a debounced save with the same body; whichever PATCH lands first proves the save.
    with page.expect_response(
        lambda r: "/api/regulations/" in r.url
        and r.request.method == "PATCH"
        and r.request.post_data_json == {"regulation": HEADING}
    ) as saved:
        tracker_page.last_section().rename(HEADING)
    assert saved.value.status == 200

    def assert_heading_saved():
        section = tracker_page.section(HEADING)
        expect(tracker_page.section_rows.last).to_contain_text(HEADING)
        expect(section.heading_link).to_have_attribute("href", ECFR_URL)
        expect(section.edit_button).to_be_visible()
        expect(tracker_page.total_count).to_have_text("248")

    assert_heading_saved()

    page.reload()
    expect(page.get_by_text("Connected to SQLite")).to_be_visible()
    assert_heading_saved()
