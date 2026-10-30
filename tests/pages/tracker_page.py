import re

from playwright.sync_api import Page


class TrackerPage:
    def __init__(self, page: Page):
        self.page = page
        self.part_select = page.get_by_role("combobox", name="Select regulation part")
        self.search = page.get_by_role("searchbox", name="Search regulations or notes")
        self.add_section = page.get_by_role("button", name="Add section")
        self.expand_all = page.get_by_role("button", name="Expand all")
        self.collapse_all = page.get_by_role("button", name="Collapse all")
        self.log_out = page.get_by_role("button", name="Log out")
        self.toast = page.get_by_role("status")
        # These elements have no role or accessible name, so ids and classes are the only stable hooks.
        self.current_user = page.locator("#current-user")
        self.brand_part = page.locator("#brand-part")
        self.connection_status = page.locator("#connection-status")
        self.total_count = page.locator("#total-count")
        self.covered_count = page.locator("#covered-count")
        self.remaining_count = page.locator("#remaining-count")
        self.results_count = page.locator("#results-count")
        self.section_rows = page.locator("tr.section-row")

    def goto(self):
        self.page.goto("/")
        self.page.get_by_text("Connected to SQLite").wait_for()

    def item(self, ref):
        """A study item row by reference, e.g. "91.103(a)"."""
        return StudyItemRow(self.page, ref)

    def section(self, heading):
        """A section header row containing this heading text."""
        return SectionRow(self.section_rows.filter(has_text=heading))

    def last_section(self):
        """The bottom section row; new sections are appended there."""
        return SectionRow(self.section_rows.last)


class StudyItemRow:
    def __init__(self, page: Page, ref: str):
        self.row = page.get_by_role("row").filter(
            has=page.get_by_role("link", name=f"Open {ref} in the eCFR in a new tab")
        )
        self.covered_checkbox = page.get_by_role("checkbox", name=f"Mark {ref} as covered")
        self.covered_label = self.row.locator(".covered-label")   # "Yes"/"No", no accessible name of its own
        self.date = page.get_by_label(f"Date covered for {ref}")
        self.notes = page.get_by_label(f"Notes for {ref}")


class SectionRow:
    """Scoped to one section header row rather than to labels, so it keeps working while a heading
    is being renamed. (Until 2026-10-28 app.js left the Edit button's label stale after a save; TC-520.)"""

    def __init__(self, row):
        self.row = row
        self.heading_link = row.get_by_role("link")       # the only link in a header row; no role when it has no href
        self.edit_button = row.get_by_role("button", name=re.compile(r"^Edit section heading"))
        self.heading_input = row.get_by_role("textbox", name="Regulation section")
        self.toggle = row.get_by_role("button", name=re.compile(r"^Study items in"))   # aria-expanded holds its state

    def expand(self):
        """Opens the section (sections start collapsed); does nothing if it is already open."""
        if self.toggle.get_attribute("aria-expanded") != "true":
            self.toggle.click()

    def rename(self, heading):
        """Edit → type → Enter, the way a user saves a heading."""
        self.edit_button.click()
        self.heading_input.fill(heading)
        self.heading_input.press("Enter")
