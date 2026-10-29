---
name: playwright-best-practices
description: Python pytest + Playwright conventions for the FAR Notes test suite. Covers pytest config, file naming, locator priority, filtering and scoping, test structure, page objects, API mocking with page.route, mock data, wait strategies, debugging and anti-patterns. Use when writing, reviewing, fixing or refactoring Playwright tests (API, component or E2E) in this repo, or when a test is flaky.
---

# Playwright Best Practices (Python + pytest)

## Overview

These conventions apply to every Playwright test in this repo. Tests are written in **Python** with **pytest** and **pytest-playwright**, using the synchronous API (`playwright.sync_api`). They build on the other test skills:

- **`/create-scenarios`** writes `docs/test-scenarios.md` (what to test, with TC ids).
- **`/test-strategy`** writes `docs/test-strategy.md` (which layer tests each scenario).
- **`/generate-tests`** writes, runs and fixes the tests.
- **This skill** says how to write each test so it is readable, isolated and not flaky.

Core principles:

1. **Test what the user sees.** Find elements by role, label and visible text. Assert on what users perceive: text, state and accessible names.
2. **Every test stands alone.** Each test creates its own user and data through the API, never depends on another test, and can run in any order.
3. **Never wait for time; wait for state.** Use `expect(...)` assertions, which retry automatically, and wait for the specific network response. Never use `page.wait_for_timeout()` or `time.sleep()` inside a test.
4. **Use the lowest layer that proves the behavior.** Follow the layer chosen in `docs/test-strategy.md`, and don't drive the UI to check server validation.
5. **One test, one TC.** Each test function name starts with its scenario id (`test_tc_006_…`), so a failure points straight to the scenario.

Use the `far-notes-domain` skill for expected behavior, UI labels and API contracts. Don't guess them.

## Project Test Setup

**Current state** (2026-10-28): the Python test stack is installed. 59 test items pass, covering 32 scenarios, including 20 of the 20 P0 scenarios. `progress_reports/` has dated coverage reports.

- **Install once:**

  ```bash
  python3 -m venv .venv
  .venv/bin/pip install -r requirements-dev.txt     # pytest, pytest-playwright, playwright 1.64.1
  .venv/bin/playwright install chromium
  ```
- **The server reads two test-only environment variables.** Both default to normal behavior:
  - `FAR_NOTES_DB`: the database path. It defaults to `data/part91.sqlite`. Tests use `.test-data/far-notes-test.sqlite`, which is gitignored.
  - `FAR_NOTES_DISABLE_RATE_LIMIT=1`: turns off `consumeRateLimit`. The shared test server sets it. Rate-limit tests start their own server without it.
- **Built:**
  - the database fixture `test_db` (`tests/support/db.py`, which seeds reset tokens)
  - the tracker component setup (`serve_tracker_from_disk`, `mock_signed_in` and `mock_regulations` in `tests/mocks/routes.py`)
  - the mock data builders (`tests/mocks/data.py`)
  - the `signed_in_page` and `other_user` fixtures
- **Not built yet:**
  - expiring sessions through `test_db` (TC-225)
  - unit tests for the JavaScript helpers. They will use `node --test` and import `lib/validation.js` and `app-core.js`, both now importable. Never import `server.js`.

**Never run tests against the real `data/part91.sqlite` or the dev server on port 3000.**

### Config Reference

`pytest.ini`:

```ini
[pytest]
testpaths = tests
pythonpath = .                     # lets tests import tests.pages, tests.support, tests.mocks
base_url = http://127.0.0.1:3100   # the test server, never the dev server on :3000
addopts =
    --browser chromium
    --tracing retain-on-failure
    --screenshot only-on-failure
    --video retain-on-failure
    --output test-results
markers =
    smoke: runs on every change (all P0 scenarios plus core happy paths)
    api: real HTTP calls to the test server (auto-applied to tests/api)
    component: one page in a real browser with every request stubbed (auto-applied to tests/component)
    e2e: full user journey through browser, server and database (auto-applied to tests/e2e)
```

What `tests/conftest.py` provides:

| Fixture | Scope | What it does |
|---------|-------|--------------|
| `test_server` | session, autouse | Starts `node server.js` on the `base_url` port with the test database and `FAR_NOTES_DISABLE_RATE_LIMIT=1`. If something already answers on that port, it's reused. |
| `browser_context_args` | function | pytest-playwright's context options, plus `timezone_id="America/New_York"` and `locale="en-US"`, so "today" is predictable |
| `request_context` | function | A fresh, signed-out Playwright `APIRequestContext` with its own cookie jar |
| `fresh_user` | function | Registers a unique user through the API and returns a dict with `username`, `email` and `password`. It does not sign in |
| `api` | function | `request_context` signed in as `fresh_user` |
| `other_user` | function | A second registered, signed-in user: a dict with `username`, `email`, `password` and `api` (its own request context). Used for isolation tests |
| `signed_in_page` | function | pytest-playwright's `page`, signed in as `fresh_user` through `page.request` (no UI login) |
| `test_db` | function | `ScratchDatabase` for the test database. `seed_reset_token(username)` returns a raw token. It refuses any path outside `.test-data/` |
| `login_page`, `create_account_page`, `tracker_page` | function | Page objects wrapping pytest-playwright's `page` |

pytest-playwright adds `playwright`, `browser`, `context`, `page` and `base_url`. `pytest_collection_modifyitems` in conftest adds the `api`, `component` or `e2e` marker based on the test's folder.

Commands:

```bash
.venv/bin/pytest                         # everything
.venv/bin/pytest -m api                  # one layer (api | component | e2e)
.venv/bin/pytest -m smoke                # Smoke suite
.venv/bin/pytest -k tc_002               # one TC
.venv/bin/pytest tests/api/test_auth.py  # one file
.venv/bin/pytest --collect-only -q       # list tests without running them
```

- Rate-limit tests (TC-217 to TC-219) use a **module-scoped** `isolated_server` fixture (`tests/support/server.py`). It runs on port 3200 with the limits **on** and its own database, which is deleted afterwards.
- **Parallel runs:** `pytest-xdist` isn't installed. If you add it, each worker needs its own port and database, because `test_server` and `isolated_server` use fixed ports.

### File Naming Convention

```
tests/
  conftest.py                       shared fixtures, layer markers, test server
  support/server.py                 ServerProcess: start/stop node server.js against a throwaway DB
  support/users.py                  register_user, sign_in, unique_id
  pages/<page>_page.py              Page Objects: login_page.py (LoginPage), tracker_page.py (TrackerPage)
  mocks/routes.py                   page.route helpers for component tests
  mocks/data.py                     mock data builders: subsection, section, preflight, entire_section, custom_section, many_items
  api/test_<area>.py                auth, access_control, rate_limits, origin, regulations, subsections, password_reset, robustness
  component/test_<page>_<area>.py   test_auth_pages.py, test_tracker_study_items.py, …
  e2e/test_<journey>.py             test_signup_signin.py, test_study_items.py, test_sections.py, test_password_reset.py
  unit/<module>.test.js             node:test, for the extracted JavaScript helpers only (planned)
```

- **Test names**: `test_tc_<nnn>_<scenario_title_in_snake_case>`. For example, TC-006 "Marking a subsection covered persists" becomes `test_tc_006_marking_a_subsection_covered_persists`.
- **Smoke tests** are marked `@pytest.mark.smoke`. Don't add layer markers by hand; they come from the folder.
- **Module basenames must be unique** across `tests/`, because there are no `__init__.py` files.
- **Names**: files use snake_case, and page object classes use PascalCase (`TrackerPage`).

## Locator Strategy (Priority Order)

Use the first option that works:

| # | Locator | Use for | FAR Notes example |
|---|---------|---------|-------------------|
| 1 | `get_by_role(role, name=...)` | Anything with a role: buttons, links, checkboxes, inputs, rows | `page.get_by_role("checkbox", name="Mark 91.103(a) as covered")` |
| 2 | `get_by_label(text)` | Form fields with a `<label>` or `aria-label` | `page.get_by_label("Username or email")`, `page.get_by_label("Notes for 91.103(a)")` |
| 3 | `get_by_placeholder(text)` | Inputs with no label (rare here) | `page.get_by_placeholder("Search regulations or notes...")` |
| 4 | `get_by_text(text)` | Non-interactive text: messages and headings | `page.get_by_text("No study items found")` |
| 5 | `get_by_test_id(id)` | Only if roles and text are ambiguous. This app has no `data-testid` attributes, so add them in app code only when needed | – |
| 6 | `locator("#id")` / CSS | Last resort, for elements with no role or name, such as summary numbers | `page.locator("#covered-count")`, `page.locator("#current-user")` |

Accessible names this app already provides:

```python
# Tracker
page.get_by_role("combobox", name="Select regulation part")
page.get_by_role("searchbox", name="Search regulations or notes")
page.get_by_role("button", name="Add section")                 # the "+" is aria-hidden
page.get_by_role("button", name="Log out")
page.get_by_role("button", name=re.compile(r"^Covered"))       # the name includes the count, e.g. "Covered 2"
page.get_by_role("button", name="Edit section heading 91.999 — My topic")
page.get_by_role("link", name="Open 91.103(a) in the eCFR in a new tab")
page.get_by_role("checkbox", name="Mark 91.103(a) as covered")
page.get_by_label("Date covered for 91.103(a)")
page.get_by_label("Notes for 91.103(a)")
page.get_by_role("status")                                     # the toast (role="status")

# Auth pages
page.get_by_label("Username or email"); page.get_by_label("Password")
page.get_by_role("button", name="Sign in")
page.get_by_role("alert")                                      # #login-error (role="alert")
page.get_by_role("link", name="Create an account")
page.get_by_label("New password"); page.get_by_label("Confirm new password")
```

Rules:

- Pass `exact=True`, or an anchored `re.compile(...)`, when one name is a prefix of another.
- Filter buttons include their count in their accessible name. Match them with `re.compile(r"^To study")`, or use `locator('.filter-button[data-filter="uncovered"]')`, which is fine because `data-filter` is a stable contract.
- Never use XPath, `nth-child` chains, or locators built from generated text such as dates or ids.

## Filtering and Scoping Patterns

Narrow down from a container instead of writing long selectors.

```python
# Find a row by what it contains, then work inside that row
row = page.get_by_role("row").filter(
    has=page.get_by_role("link", name="Open 91.103(a) in the eCFR in a new tab")
)
row.get_by_role("checkbox").check()
expect(row.get_by_text("Yes")).to_be_visible()

# Filter by text, or by the absence of something
page.get_by_role("row").filter(has_text="Entire section")
page.locator("tr.section-row").filter(has_not_text="Preflight")

# Scope to a region first
auth_card = page.locator("section.auth-card")
auth_card.get_by_label("Password").fill(password)

# Count and list checks
expect(page.locator("tr.section-row")).to_have_count(61)
expect(page.locator("#results-count")).to_have_text("Showing 2 of 247 study items")

# Combine conditions
page.get_by_role("button").and_(page.get_by_title("…"))
page.get_by_role("link", name=re.compile("eCFR")).or_(page.get_by_text("No link"))
```

App-specific notes:

- **Section headers and their items are sibling rows.** A section's heading `<tr class="section-row">` is followed by its subsection `<tr>`s, with no wrapper element. Scope to a **subsection row** with `filter(has=...)` as shown above. To get a section header row, use `page.locator("tr.section-row").filter(has_text="91.103 — Preflight action")`.
- Use `.first`, `.last` or `.nth(i)` only when the order is part of the requirement. For example, TC-424 checks that custom sections come last.

## Test Structure Patterns

```python
import pytest
from playwright.sync_api import expect


@pytest.mark.smoke
def test_tc_006_marking_a_subsection_covered_persists(page, fresh_user, tracker_page):
    # page.request shares the browser context's cookies, so this signs the page in without the UI
    page.request.post("/api/auth/login", data={"username": fresh_user["username"], "password": fresh_user["password"]})
    tracker_page.goto()
    item = tracker_page.item("91.103(a)")

    with page.expect_response(
        lambda r: "/api/subsections/" in r.url and r.request.method == "PATCH" and r.ok
    ):
        item.covered_checkbox.check()

    page.reload()
    expect(item.covered_checkbox).to_be_checked()
    expect(tracker_page.covered_count).to_have_text("1")
```

- **Arrange, Act, Assert.** Set data up through fixtures and the API, do one user action in the UI, then assert. For longer E2E journeys, split the phases into small, well-named helper functions.
- **Assertion styles:**
  - **Page and locator assertions**: always `expect(locator).to_have_text(...)`, `to_be_visible()`, `to_have_url(...)`, and so on. They retry until the timeout. Never write `assert locator.text_content() == ...`.
  - **API response assertions**: plain `assert res.status == 401` and `assert res.json() == {...}`. The response is already complete, so nothing needs retrying.
  - `expect(page).to_have_url()` needs a full URL (`f"{base_url}/"`) or a regex (`re.compile(r"/login$")`).
- **Fixtures, not setup methods.** Put shared setup in `tests/conftest.py`. Put module-only setup in the test module as a fixture, with `autouse=True` if every test in the module needs it, as in `login_harness` in `test_auth_pages.py`.
- **Signed-in browser pages.** `page.request` shares cookies with the page's browser context. Signing in through `page.request.post("/api/auth/login", data=...)` therefore signs the page in without using the UI. Add a `signed_in_page` fixture for this when tracker tests need it, rather than overriding `page`, because sign-in tests need a signed-out page.
- **Set up data through the API** for preconditions such as "91.103(a) is covered" or "a custom section exists": `api.get("/api/regulations?part=91")`, find the id, then `api.patch(...)`.
- **API tests** use `request_context` (signed out) or `api` (signed in).
  - `data=dict` sends JSON. Pass `max_redirects=0` to see a 302.
  - Header names in `res.headers` are lowercase.
  - Playwright sends no `Origin` header by default, which this server accepts (TC-207). For cross-origin tests (TC-206), pass `headers={"Origin": "http://evil.example"}`.
- **Parameterize** repeated cases with `@pytest.mark.parametrize("value", [...])`. The test id shows each case, for example `test_tc_202_…[/login]`.
- **Known bugs**: if a test asserts the fixed behavior before the fix lands, use `@pytest.mark.xfail(strict=True, reason="TC-106: <rule>; app does <actual>")`. `strict=True` makes the test fail when the bug is fixed, as a reminder to remove the marker. A missing hook uses `@pytest.mark.skip(reason="FIXME: …")`. Never skip without a reason.
- **Soft checks**: Python Playwright has no `expect.soft`. Put related checks in one test in order of importance. For noisy, non-functional measurements (TC-215 timing), use `record_property` plus `warnings.warn` instead of a failing assert.

## Page Object Model (POM)

Page objects hold **locators and user actions**. Tests hold **assertions**. They live in `tests/pages/` and are supplied by fixtures in `tests/conftest.py`.

What exists today:

| File | Class | Locators | Actions | Used by |
|------|-------|----------|---------|---------|
| `tests/pages/login_page.py` | `LoginPage` | `username`, `password`, `sign_in_button`, `error` (role alert), `create_account_link` | `goto()`, `sign_in(identifier, password)` | TC-002, TC-300, TC-302, TC-511 |
| `tests/pages/create_account_page.py` | `CreateAccountPage` | `form`, `username`, `email`, `password`, `create_account_button`, `success` (role status), `return_to_login` | `goto()`, `create_account(username, email, password)` | TC-001 |
| `tests/pages/tracker_page.py` | `TrackerPage` | `part_select`, `search`, `add_section`, `log_out`, `toast`, `current_user`, `brand_part`, `connection_status`, `covered_count`, `remaining_count`, `results_count` | `goto()` (waits for "Connected to SQLite"), `item(ref)`, `section(heading)`, `last_section()` | TC-002, 006, 010, 015 |
| `tests/pages/tracker_page.py` | `StudyItemRow` | `row`, `covered_checkbox`, `covered_label`, `date`, `notes` | – | TC-006 |
| `tests/pages/tracker_page.py` | `SectionRow` (built from a row locator) | `row`, `heading_link`, `edit_button`, `heading_input` | `rename(heading)` | TC-010 |

Pattern (simplified; see `tests/pages/tracker_page.py` for the full version):

```python
# tests/pages/tracker_page.py
import re
from playwright.sync_api import Page


class TrackerPage:
    def __init__(self, page: Page):
        self.page = page
        self.part_select = page.get_by_role("combobox", name="Select regulation part")
        self.search = page.get_by_role("searchbox", name="Search regulations or notes")
        self.covered_count = page.locator("#covered-count")   # no role or name, so an id
        ...

    def goto(self):
        self.page.goto("/")
        self.page.get_by_text("Connected to SQLite").wait_for()   # readiness wait, not an assertion

    def filter(self, name):                 # "All" | "To study" | "Covered"
        return self.page.get_by_role("button", name=re.compile(rf"^{name}\b"))

    def item(self, ref):                    # e.g. "91.103(a)"
        return StudyItemRow(self.page, ref)

    def switch_part(self, part):            # "61" | "91"
        with self.page.expect_response(lambda r: f"/api/regulations?part={part}" in r.url):
            self.part_select.select_option(part)


class StudyItemRow:
    def __init__(self, page: Page, ref: str):
        self.row = page.get_by_role("row").filter(
            has=page.get_by_role("link", name=f"Open {ref} in the eCFR in a new tab")
        )
        self.covered_checkbox = page.get_by_role("checkbox", name=f"Mark {ref} as covered")
        self.date = page.get_by_label(f"Date covered for {ref}")
        self.notes = page.get_by_label(f"Notes for {ref}")
```

Rules:

- **One class per page.** Still to come: `ForgotPasswordPage` and `ResetPasswordPage`. Create each when the first test needs it.
- **Scope component objects to their row**, not to labels that change during the test. A rename changes both the heading text and the Edit button's name (TC-520), so `SectionRow` finds the button with `row.get_by_role("button", name=re.compile("^Edit section heading"))`. After a rename, look the row up again by its new heading.
- **Expose locators as attributes and actions as methods.** Methods are named after user intent, such as `sign_in(identifier, password)` or `switch_part("61")`, not `click_button()`.
- **No `expect` or `assert` inside page objects.** A readiness wait inside navigation, like `goto()` above, is the only exception.
- **Supply page objects through fixtures** (`def tracker_page(page): return TrackerPage(page)`), so tests don't construct them.
- Page objects are for component and E2E tests only. API tests use the helpers in `tests/support/`.

## API Mocking

Component tests stub the network with `page.route()`. E2E tests **never** stub. A stubbed E2E test is really a component test (see Anti-Patterns). Helpers live in `tests/mocks/routes.py`.

```python
# tests/mocks/routes.py (existing helpers)
def serve_auth_pages_from_disk(page):        # login/create-account/forgot/reset pages, their JS and CSS
    stub_external_fonts(page)                # Google Fonts get an empty 200, so tests stay offline
    page.route(
        lambda url: urlparse(url).path in AUTH_PAGES,
        lambda route: route.fulfill(path=ROOT / AUTH_PAGES[urlparse(route.request.url).path]),
    )

def mock_signed_out(page):
    page.route("**/api/auth/me", lambda route: route.fulfill(json={"authenticated": False}))

def mock_login_rejected(page, on_request=None):   # 401 + the real error text; optionally records requests
    ...
```

The tracker setup works the same way:

```python
serve_tracker_from_disk(page)                 # "/", index.html, app-core.js, app.js, styles.css, image
mock_signed_in(page)                          # /api/auth/me → authenticated
mock_regulations(page, {"91": [preflight(notes="…")], "61": []})
page.goto("/")
expect(page.get_by_text("Connected to SQLite")).to_be_visible()
```

Used by `tests/component/test_tracker_security.py` (TC-211, TC-212).

Patterns:

- **Errors**: `route.fulfill(status=500, json={"error": "Disk full"})`. The app shows `error` in its toasts (TC-322 to TC-325, TC-327).
- **Slow or out-of-order responses**: in the sync API, **never `time.sleep()` in a route handler**, because it blocks the whole test. Hold the route instead, assert the in-between state, then release it:

  ```python
  held = []
  page.route("**/api/regulations?part=61", held.append)      # don't fulfill yet
  tracker_page.part_select.select_option("61")
  expect(tracker_page.connection_status).to_have_text("Loading regulations...")
  held[0].fulfill(json=[...])                                  # now let it finish
  ```
- **Checking what was sent**:

  ```python
  with page.expect_request(lambda r: r.method == "PATCH") as req_info:
      ...  # the action
  assert req_info.value.post_data_json == {"covered": True, "date": "2026-06-01", "notes": ""}
  ```
- **Recording or counting calls**: pass a callback, as in `mock_login_rejected(page, on_request=calls.append)`, then `assert calls == []`.
- **Responding to PATCH** like the real server: echo back the merged subsection, so the UI stays consistent.
- **Add routes before `page.goto()`.** The last route registered for a URL wins, so a test can override a default stub.
- **Reading a response the page navigates away from.** `response.json()` fails once the page has navigated, which happens with logout and its redirect to `/login`. In E2E, record the response on its way through instead of stubbing it:

  ```python
  seen = []
  def record(route):
      response = route.fetch()                       # the real server answers
      seen.append((response.status, response.json()))
      route.fulfill(response=response)               # passed on unchanged
  page.route("**/api/auth/logout", record)
  ```

  This is an observer, not a stub, so it's allowed in E2E (TC-015). `route.fetch` must never change the response.
- **Abort** (`route.abort()`) only to simulate a network failure.
- **Never stub** `/api/*` in E2E or API tests. Partial stubbing of the real server is the main source of false passes.

## Mock Data

Keep mock data small, matched to the API's shapes, and built by functions, so every test states only what it cares about. They live in `tests/mocks/data.py`.

```python
import itertools

_ids = itertools.count(1)


def subsection(**over):
    return {"id": next(_ids), "code": "a", "title": "Title", "covered": False, "date": "", "notes": "", **over}


def section(heading, subsections, **over):
    return {"id": next(_ids), "regulation": heading, "isLocked": True, "subsections": subsections, **over}


def preflight():
    return section("91.103 — Preflight action", [
        subsection(code="a", title="For a flight under IFR or a flight not in the vicinity of an airport, …"),
        subsection(code="b", title="For any flight, runway lengths at airports of intended use, …"),
    ])


def entire_section():
    return section("91.5 — Pilot in command of aircraft requiring a type rating",
                   [subsection(code="", title="Entire section")])


def custom_section(heading="91.999 — My custom topic"):
    return section(heading, [subsection(code="", title="Entire section")], isLocked=False)


def many_items(total, covered_count=0):          # e.g. 247 items for count and rounding tests
    return [section("91.900 — Bulk", [subsection(code=str(i), covered=i < covered_count) for i in range(total)])]
```

Rules:

- Mock data **matches the real API contract** in `far-notes-domain/api-reference.md`: `Section = {id, regulation, isLocked, subsections}` and `Subsection = {id, code, title, covered, date, notes}`. The JSON keys stay camelCase (`isLocked`), because they mirror the API.
- Use **real catalog values** (from `regulation-subsections.json`) when the test asserts titles. Otherwise use short placeholders.
- **Random and unique** data for real-server tests (usernames, emails, headings) comes from `tests.support.users.unique_id()`. **Fixed** data in component tests keeps them deterministic.
- **Dates**: never compute "today" in a test. Call `page.clock.set_fixed_time(datetime(2026, 6, 1, 12, 0))` before `goto`, together with the conftest `timezone_id`, and assert the literal `"2026-06-01"`.
- Mock data contains no secrets and never copies records from `data/part91.sqlite`.

## Wait Strategies

Playwright waits automatically before actions (the element must be visible, enabled and stable) and inside `expect(...)` assertions. Add waits only for things it can't infer:

| Situation | Do this |
|-----------|---------|
| An element appears or changes | `expect(locator).to_be_visible()`, `.to_have_text()`, `.to_have_count()` |
| A save must finish before a reload (autosave) | Wrap the action in `with page.expect_response(predicate):` |
| Debounced notes autosave (350 ms) | `page.clock.install()` before `goto`, type, then `page.clock.run_for(350)` inside `with page.expect_response(...)` |
| The toast hides after 2.4 s (TC-510) | `page.clock.run_for(2400)`, then `expect(toast).to_be_hidden()` |
| Navigation or redirect | `expect(page).to_have_url(f"{base_url}/")` or `expect(page).to_have_url(re.compile(r"/login$"))` |
| Data loaded on the tracker | `expect(page.get_by_text("Connected to SQLite")).to_be_visible()` |
| A loading or in-between state | Hold the route (see API Mocking), assert, then fulfill |
| An API value after a UI action | Wait for that action's response first, then read the API once and `assert` |

```python
# The context manager starts listening before the action, so a fast response is never missed
with page.expect_response(lambda r: "/api/subsections/" in r.url and r.request.method == "PATCH"):
    item.notes.fill("Check NOTAMs")
    item.notes.blur()
```

- **Never use** `page.wait_for_timeout()`, `time.sleep()` or `wait_for_load_state("networkidle")` in tests. The app makes no further requests after load, so "networkidle" says nothing about saves. `ServerProcess` polls while the server starts up, but that's outside any test.
- Don't raise timeouts to fix flakiness. Find the missing condition.

## Debugging Tips

- **Run one test with output:** `.venv/bin/pytest -k tc_006 -vv -s`. Add `-x` to stop at the first failure, `--lf` to rerun only the last failures, or `--pdb` to drop into the debugger.
- **Headed and step-by-step:**
  - `--headed --slowmo 500` shows the browser.
  - `PWDEBUG=1 .venv/bin/pytest -k tc_002 -s` opens the Playwright Inspector.
  - `page.pause()` stops at a chosen point.
- **Traces:** traces are kept for failing tests (`--tracing retain-on-failure` in `pytest.ini`). Use `--tracing on` to always record one. Open it with `.venv/bin/playwright show-trace test-results/<test-name>/trace.zip`. It shows actions, DOM snapshots, the network (PATCH bodies) and the console.
- **Screenshots and video** of failures are saved in `test-results/<test-name>/`.
- **Finding locators:** `.venv/bin/playwright codegen --target python-pytest http://127.0.0.1:3100/login` records the best locators in pytest style. Then move them into a page object.
- **Console and errors from the page:** `page.on("console", lambda m: print(m.text))` and `page.on("pageerror", print)`. The app logs failed saves with `console.error("Unable to save …")`.
- **Server-side problems:**
  - Start the test server yourself with `FAR_NOTES_DB=.test-data/far-notes-test.sqlite FAR_NOTES_DISABLE_RATE_LIMIT=1 PORT=3100 node server.js`. The `test_server` fixture will reuse it, and you can watch its output.
  - If `ServerProcess` fails, its error includes the server's output.
- **Inspecting the test database:** `sqlite3 .test-data/far-notes-test.sqlite "select * from sessions"`, or Python's `sqlite3` module. Never point either at `data/part91.sqlite`.
- **Flaky test checklist:**
  1. Is the action that triggers the save wrapped in `expect_response`?
  2. Is the time or time zone fixed?
  3. Is data shared with another test?
  4. Is a 429 coming from a rate limit (the wrong server, or the override missing)?
  5. Does a locator match more than one element (strict-mode violation)?
  6. Is a route handler blocking with `time.sleep`?

## Anti-Patterns to Avoid

| Anti-pattern | Why it hurts | Do this instead |
|--------------|--------------|-----------------|
| `page.wait_for_timeout(1000)` / `time.sleep()` | Slow, and still flaky | `expect_response`, an `expect(...)` assertion, or `page.clock` |
| `assert locator.text_content() == ...` | No retry, so it races the render | `expect(locator).to_have_text(...)` |
| `time.sleep()` inside a `page.route` handler | Blocks the sync API, so the whole test stalls | Hold the route and fulfill it later |
| CSS or XPath chains (`table tr:nth-child(4) td input`) | Breaks on any layout change | `get_by_role`/`get_by_label` plus `filter(has=...)` |
| Logging in through the UI in every test | Slow, and repeats the sign-in test | API sign-in in a fixture. Only sign-in tests use the form |
| Creating preconditions by clicking | Slow, and fails for unrelated reasons | Set up through the API (`api.post`/`api.patch`) |
| Tests that depend on order or each other's data | One failure cascades, and order changes break them | `fresh_user` per test and unique headings |
| Using the `VMC43` account, `data/part91.sqlite` or port 3000 | Corrupts real study data and shares state | The test server (port 3100) and `fresh_user` |
| Stubbing the network in E2E | It's a component test pretending to be E2E | Real server in E2E, stubs only in `tests/component` |
| A component test that needs real database data | Slow, and coupled to the server | Stub every `/api/*` call with mock builders |
| Validating server messages through the browser | Slow and duplicated | API test for the message, plus at most one Component render |
| `expect`/`assert` inside page objects | Hidden assertions, so failures are hard to read | Page objects return locators, and tests assert |
| Checking CSS classes or internal JS variables | Couples tests to implementation | Assert visible text, state or accessible names. `is-active` on filters is the one accepted exception |
| Computing "today" in the test | Fails around midnight and across time zones | `page.clock.set_fixed_time` plus the conftest `timezone_id` |
| Running against a server without the rate-limit override | Fails with 429 after the 5th registration | Let `test_server` start the server, or set `FAR_NOTES_DISABLE_RATE_LIMIT=1` |
| `pytest.mark.skip` with no reason, or a plain `xfail` | Silently shrinks the suite, or hides a fix | `skip(reason="FIXME: …")`, `xfail(strict=True, reason=…)` |
| Long tests that check many unrelated things | One failure hides the rest, and they map poorly to TC ids | One TC per test, or `parametrize` for variations |
| Raising timeouts or adding retries to "fix" flakiness | Hides real races | Find and wait for the actual condition |
