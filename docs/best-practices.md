# Best Practices Review: FAR Notes Test Automation

Reviewed 2026-11-03 against `main` at `6a65056`. This document covers which practices the project uses (in test automation, quality assurance, security, test design, ISTQB, pytest and Python), where each one is applied, where the practice comes from, what's missing, and what needs improving.

**Numbers at the time of review**

| Measure | Value |
|---|---|
| Scenarios in `docs/test-scenarios.md` | 180 (P0 23, P1 57, P2 57, P3 43) |
| Scenarios automated | **57 (32%)**: P0 23/23, P1 19/57, P2 11/57, P3 4/43 |
| Automated tests (pytest items, counting parametrized cases) | 89: API 63, component 20, E2E 5, device 1 |
| Unit tests (`node --test`) | 0 of 24 planned |
| Smoke suite | 52 tests |
| Last full run | 88 passed in about 13 s; the device test passed separately (5 of 5 runs) |

**How to read the "Source" lines.** Each practice names where it is applied in this repository, and the outside reference it comes from. The outside references are well-known standards and guides, cited from general knowledge, so check the current edition before quoting them formally. They're listed in full under [References](#references).

---

## 1. Test automation practices

### 1.1 The test pyramid: one primary layer per scenario
Every scenario is given **one primary layer** by numbered decision rules: pure logic goes to unit tests, the server's contract to API tests, a UI's reaction to a response to component tests, and only real journeys to E2E. Anything else is a documented exception. The result is a pyramid: 63 API tests, 20 component tests, 5 E2E tests and 1 device test. E2E is 6.7% of automated scenarios, against a target of 15% or less.

- **In this project:** `docs/test-strategy.md` (summary, Layer Assignments, decision rules); the `test_strategy` skill (`.claude/skills/test_strategy/SKILL.md`), which also lists the anti-patterns it checks for (the "ice-cream cone", E2E used for validation, duplicate coverage).
- **Source:** Mike Cohn, *Succeeding with Agile* (2009), where the test pyramid comes from; Martin Fowler, "The Practical Test Pyramid" (Ham Vocke, 2018); Google Testing Blog, "Just Say No to More End-to-End Tests" (2015).

### 1.2 Test isolation: every test stands alone
- Each test registers its **own user** through the API (`fresh_user`), with its own HTTP client and cookie jar (`request_context`), or its own browser context.
- Each run starts from an **empty database** and deletes it afterwards. This was added after a database kept between runs grew to 611,000 rows and the server took more than 15 s to start.
- Tests never touch real data. The test server runs on **port 3100** with `.test-data/far-notes-test.sqlite`; the dev server on port 3000 and `data/part91.sqlite` are off-limits. This rule is written into `CLAUDE.md` and the `generate-tests` skill.
- The register rate limit is turned off **only** in the test server (`FAR_NOTES_DISABLE_RATE_LIMIT=1`). The rate-limit tests start their own server with the limit switched on.
- **In this project:** `tests/conftest.py` (`test_server`, `request_context`, `fresh_user`, `api`, `other_user`); `tests/support/server.py`.
- **Source:** Playwright docs, "Best Practices › Make tests as isolated as possible"; Martin Fowler, "Eradicating Non-Determinism in Tests" (2011); xUnit Test Patterns (Meszaros, 2007), "Fresh Fixture".

### 1.3 Deterministic tests: wait for state, never for time
- Assertions retry automatically until the expected state appears (`expect(locator).to_have_text(...)`).
- Tests wait for **specific network responses**, never fixed delays. The rules ban `wait_for_timeout`, `time.sleep` and `networkidle` in tests. The only sleeps are polling loops that check a condition (server start-up; the device test checking the API for a saved item).
- **Time is fixed**: the browser time zone is `America/New_York` and the locale is `en-US` (`browser_context_args`). Tests that depend on "today" use Playwright's clock (`page.clock`).
- New tests are **run 3 times** to catch flakiness before they count as done.
- **Known exception:** the device test compares the saved date with the Mac's own clock, because the Simulator's clock can't be fixed. It could fail around midnight.
- **In this project:** the `playwright-best-practices` skill (Wait Strategies, Anti-Patterns); `generate-tests` skill step 3; `tests/device/test_ios_app.py`.
- **Source:** Playwright docs, "Auto-waiting" and "Assertions"; Martin Fowler, "Eradicating Non-Determinism in Tests".

### 1.4 Locators users can see, which double as an accessibility check
- Elements are found by **role and accessible name**, such as `get_by_role("checkbox", name="Mark 91.103(a) as covered")`, not by CSS classes or XPath.
- If a control loses its accessible name, the tests fail. That gives the project a basic accessibility check for free.
- The same names are used on iOS. Appium finds elements by the labels VoiceOver reads, and the single XPath used there is documented as the only exception.
- **In this project:** the `playwright-best-practices` skill (Locator Strategy table); `tests/pages/*.py`; `tests/pages/ios_app.py`.
- **Source:** Playwright docs, "Locators" (role locators come first); Testing Library's guiding principles ("The more your tests resemble the way your software is used…"); W3C WAI-ARIA.

### 1.5 Page objects, data builders and API-based setup
- **Page objects** hold locators and user actions; tests hold the assertions. There's one class per page, plus small objects for repeated parts such as `StudyItemRow` and `SectionRow`.
- **Mock data builders** (`preflight()`, `custom_section()`, `many_items(n)`) build data that matches the real API's shape, so each test states only what it cares about.
- **Preconditions are set up through the API**, such as marking an item covered. The UI is used only for the behavior under test.
- **In this project:** `tests/pages/`, `tests/mocks/data.py`, `tests/mocks/routes.py`, `tests/support/regulations.py` and `users.py`.
- **Source:** Martin Fowler, "PageObject" (2013); Meszaros, *xUnit Test Patterns* ("Test Data Builder", "Creation Method"); Playwright docs, "Page object models".

### 1.6 Stubbing the network at the right layer
- **Component tests** stub every request with `page.route()`, so they test the UI logic regardless of what's in the database. Errors (500), slow responses and responses arriving out of order are all simulated this way.
- **E2E tests never stub anything.** The strategy relabels any "E2E" test that stubs requests as a component test.
- **In this project:** `tests/component/*`, `tests/mocks/routes.py`; `docs/test-strategy.md` › Anti-Patterns ("Network stubs in E2E").
- **Source:** Playwright docs, "Mock APIs"; Google Testing Blog on hermetic tests.

### 1.7 Evidence when a test fails, and reporting
- When a test fails, Playwright **keeps a trace, a screenshot and a video** (`--tracing retain-on-failure`, `--screenshot only-on-failure`, `--video retain-on-failure` in `pytest.ini`). A trace can be replayed step by step.
- **Allure 3 report**, grouped into Web › layer › area and Mobile › iOS / Android / Both platforms › layer.
- **In this project:** `pytest.ini`, `allurerc.mjs`, `report_groups` in `tests/conftest.py`.
- **Source:** Playwright docs, "Trace viewer"; Allure Report documentation.

### 1.8 Mobile testing at two depths
- **Fast checks in Chromium.** Chromium emulates an iPhone (screen size, touch, the `(pointer: coarse)` media query), and a low-level browser command (CDP `Emulation.setSafeAreaInsetsOverride`) fakes the notch and home-indicator areas. These run in the normal suite.
- **One real-device test.** It runs the real iOS app on the iPhone 17 Simulator with Appium. It's separate from the normal run (`--run-device`), and the app is built against the test server and then put back to its normal settings.
- **API checks of the app's protocol:** bearer tokens, CORS and app origins.
- **In this project:** `tests/component/test_touch_layout.py`, `tests/device/`, `tests/support/ios_app.py`, `tests/api/test_mobile_clients.py`.
- **Source:** Playwright docs, "Emulation"; Appium XCUITest driver docs; Apple Human Interface Guidelines.

### 1.9 Tests that are proven to fail when they should
- Several tests start with a **control assertion** that checks the starting state, such as `# control: starts uncovered`, so they can't pass without the action actually doing something.
- New layout tests were run against the **old CSS** first, to confirm they would have caught the bug.
- **In this project:** `test_touch_layout.py` (TC-521 control), `tests/device/test_ios_app.py`, `test_mobile_clients.py` (TC-231 control).
- **Source:** "Test the test": the red-green step in test-driven development (Kent Beck, *Test-Driven Development by Example*, 2002); ISTQB CTFL v4.0, confirmation testing.

---

## 2. Quality assurance process

| Practice | Where | Source |
|---|---|---|
| **Scenarios before code.** Each flow is examined through 6 lenses: happy path, business rules, security, negative, edge cases and UI state. Each scenario has a TC id, category, priority, steps, expected results and the rule it traces to | `docs/test-scenarios.md`, `create-scenarios` skill | ISTQB CTFL v4.0, ch. 4 (test analysis and design); IEEE 829 / ISO/IEC/IEEE 29119-3 (test case specification) |
| **Risk-based priorities (P0–P3).** All 23 P0 scenarios are automated, and P0 plus one happy path per flow form the Smoke suite | `docs/test-strategy.md` › Suites | ISTQB CTFL v4.0, 5.2 (risk-based testing) |
| **Traceability.** Every test name starts with its TC id, every scenario names its business rule, and the strategy maps TC ids to files | test names, `docs/test-strategy.md` › Proposed Test Layout | ISTQB CTFL v4.0, 1.4.4 (traceability) |
| **A documented test oracle.** Expected behavior comes from the domain docs (`business-rules.md`, `api-reference.md`, `data-models.md`, `user-flows.md`), not from what the app currently does | `.claude/skills/far-notes-domain/` | ISTQB glossary, "test oracle"; Kaner, Bach and Pettichord, *Lessons Learned in Software Testing* |
| **Triage: test bug or application bug?** A decision table classifies each failure. Application bugs keep the correct assertion and are marked `xfail(strict=True)`; unclear requirements go to Open Questions; a test is never weakened to pass | `generate-tests` skill, step 5 | ISTQB CTFL v4.0, 5.5 (defect management); pytest docs, "xfail strict" |
| **Open questions recorded rather than guessed** | the "Open questions" sections of both docs | ISTQB CTFL v4.0, static testing of the test basis |
| **Coverage gap reports** | `progress_reports/2026-10-28_coverage-gap-report.md` | ISTQB CTFL v4.0, 5.3 (test monitoring and reporting) |
| **Change control.** A branch per change, pull requests, descriptive commits, the noreply email address and a co-author line | Git history, PRs #2–#4 | GitHub flow; Conventional review practice |
| **Results reported exactly as they were.** A failure is reported as a failure, and anything not run is said to be not run | `CLAUDE.md`, `generate-tests` skill › Rules | ISTQB Code of Ethics (CTFL) |

---

## 3. ISTQB concepts, mapped to this project

### 3.1 A note on terms
ISTQB's **"component testing"** means testing one unit of code in isolation. That's this project's **unit** layer. This project's **"component"** layer, one page with the network stubbed, is closer to ISTQB's **component integration testing**. The API layer is system-level testing of the backend through its interface. E2E and the device test are **system testing** of whole user journeys.

### 3.2 Test design techniques used
| Technique (ISTQB CTFL v4.0, ch. 4) | Examples in this project |
|---|---|
| **Equivalence partitioning** | `?part=61` / `91` / invalid; signed in versus signed out; same origin versus app origin versus another site (`test_origin.py`, `test_mobile_clients.py`) |
| **Boundary value analysis** | password exactly 15 characters, and 1024 bytes; username length limits; the 16 KB request-body limit (413 response) (`test_auth.py`, `test_robustness.py`) |
| **Decision tables** | how the server authenticates a request: which combination of origin, cookie and bearer token is accepted (TC-228, TC-230, TC-232); the triage table in `generate-tests` |
| **State transition testing** | session: signed out → signed in → logged out with the token revoked (TC-015, TC-231); password-reset token: issued → used → rejected again; section: collapsed ↔ expanded, and a search temporarily opening sections (TC-526 to TC-531) |
| **Error guessing** (experience-based) | the "malicious user" lens: injected script in notes (TC-211, TC-212), another user's ids (TC-203), oversized or malformed bodies |
| **Checklist-based testing** | the 6-lens coverage checklist in `create-scenarios`; the static review checklist in `generate-tests` |
| **Exploratory testing** | done informally: checking the app in the iOS Simulator found the zoom, status-bar, cut-off-card and tap-target problems. There are no charters or session notes, see §7 |

### 3.3 Test types covered
- **Functional:** most scenarios.
- **Security:** 23 of 34 scenarios automated.
- **Usability and portability:** the phone layout, safe areas and the 16px fields that stop iOS from zooming in.
- **Confirmation and regression:** bugs found get a test, and the Smoke suite runs on every change.
- **Not covered:** performance, load, reliability and formal accessibility audits (§7).

### 3.4 The seven testing principles in practice
1. **Testing shows the presence of defects, not their absence.** Testing found the empty-state bug, the TC-106 focus bug, the iOS zoom and the tap-target size.
2. **Exhaustive testing is impossible.** Hence the P0–P3 priorities and the one-layer-per-scenario rule.
3. **Early testing saves time and money.** Scenarios and strategy were written before the tests, and the domain docs before the scenarios.
4. **Defects cluster together.** Security and authentication got the deepest coverage: all P0 scenarios.
5. **Tests wear out (the pesticide paradox).** The skills regenerate scenarios when the domain docs change (`generate-tests` step 5).
6. **Testing is context dependent.** It's a local, single-user app, so there's no load testing, and the rate limits are per IP.
7. **Absence-of-defects fallacy.** All tests passing didn't mean the app was usable on a phone. Looking at it in the Simulator found problems the tests didn't.

### 3.5 Test process activities (ISTQB CTFL v4.0, 1.4)
| Activity | Here |
|---|---|
| Planning | `docs/test-strategy.md` |
| Monitoring and control | coverage gap report; Allure |
| Analysis and design | `docs/test-scenarios.md` |
| Implementation | `tests/` |
| Execution | pytest, Allure |
| Completion | **missing:** no completion report or retrospective (§7) |

---

## 4. Security practices

What the application does and how the tests check it. The categories follow the OWASP Top 10:2021; the controls follow the OWASP ASVS and Cheat Sheets.

| Risk (OWASP Top 10:2021) | Control in the app | Tested by |
|---|---|---|
| **A01 Broken access control** | Every query is scoped by `user_id`; another user's ids return 404, never 403, so they don't reveal anything; locked headings reject edits with 403; tracker files need a session | `test_access_control.py` (TC-200 to TC-204, TC-209, TC-210, TC-222) |
| **A02 Cryptographic failures** | Passwords use scrypt with a per-user salt; session and reset tokens are 32 random bytes and stored only as SHA-256 hashes; tokens are compared in constant time (`timingSafeEqual`) | `test_auth.py`, `test_password_reset.py` |
| **A03 Injection** | All 40 SQL statements are prepared statements; the frontend writes user text with `textContent` (the 3 `innerHTML` uses in `app.js` set fixed text only) | TC-211, TC-212 (script in notes never runs) |
| **A04 Insecure design** | Rate limits on login, register and reset; no delete endpoint by design; password reset expires in 30 minutes and works once | `test_rate_limits.py`, `test_password_reset.py` |
| **A05 Security misconfiguration** | Static files only from an allowlist; `Cache-Control: no-store` on protected pages; `X-Content-Type-Options: nosniff`; the server listens on 127.0.0.1 by default | `test_robustness.py`, TC-200 |
| **A07 Identification and authentication failures** | One login error message whether the user exists or not; a dummy scrypt run for unknown users so response times don't reveal valid names; HttpOnly, SameSite=Strict session cookie, 7-day expiry; password rules from NIST 800-63B (at least 15 characters, no forced character types, max 1024 bytes) | `test_auth.py` (TC-125, TC-129, TC-208, TC-215) |
| **Cross-site request forgery (CSRF)** | SameSite=Strict, plus an origin check on every request that changes data | `test_origin.py` (TC-206) |
| **CORS and the mobile app** | CORS only for the two app origins and without credentials; the app authenticates only with a bearer token, never the cookie; the login response includes the token only for the app | `test_mobile_clients.py` (TC-020, TC-227 to TC-233) |
| **Denial of service through large requests** | 16 KB request-body limit (413 response) | `test_robustness.py` |
| **Secrets and personal data** | The commit email is GitHub's noreply address; the database, `.test-data` and Allure output are gitignored; the initial password comes from an environment variable and is never stored in the source | `.gitignore`, Git history |

**Sources:** OWASP Top 10:2021; OWASP Application Security Verification Standard (ASVS); OWASP Cheat Sheets (Password Storage, Session Management, Authentication, CSRF Prevention, Cross-Site Scripting Prevention); NIST SP 800-63B (Digital Identity Guidelines: authentication); MDN, "SameSite cookies" and "CORS".

---

## 5. pytest practices

| Practice | Where | Source |
|---|---|---|
| **Fixtures instead of setup and teardown methods.** Setup before `yield` and cleanup after it; fixtures build on each other (`request_context` → `fresh_user` → `api`) | `tests/conftest.py` | pytest docs, "How to use fixtures" |
| **Fixture scopes chosen on purpose.** `test_server` and `base_url` once per session; a new client and user per test | `tests/conftest.py` | pytest docs, "Fixture scopes" |
| **Shared fixtures in `conftest.py` files** at the root and in `tests/device/` | `tests/conftest.py`, `tests/device/conftest.py` | pytest docs, "conftest.py: sharing fixtures" |
| **Markers registered in `pytest.ini`** (`smoke`, `api`, `component`, `e2e`, `device`, `mobile(platform)`), with the layer markers applied automatically from each test's folder by a hook | `pytest.ini`, `pytest_collection_modifyitems` | pytest docs, "Working with custom markers" |
| **`@pytest.mark.parametrize`** with readable `ids`, and `pytest.param(..., marks=...)` to tag cases one by one | TC-200, TC-229, TC-232 | pytest docs, "Parametrizing tests" |
| **Custom command-line options** (`--run-device`) through `pytest_addoption`, and deselecting rather than skipping, so normal runs stay clean | `tests/conftest.py` | pytest docs, "Writing hook functions" |
| **Reusing plugin options** (`--slowmo`, `--headed`, `--base-url`) instead of inventing new ones | `tests/device/conftest.py` | pytest-playwright docs |
| **Selecting tests** with `-m` (markers) and `-k` (name expressions) | `CLAUDE.md` › Commands | pytest docs, "Selecting tests" |
| **`xfail(strict=True)` for known application bugs** (policy; not used yet, see §7) | `generate-tests` skill | pytest docs, "Skip and xfail" |

## 6. Python practices

| Practice | Where | Source |
|---|---|---|
| A virtual environment (`.venv`) with **exactly pinned** dependencies | `requirements-dev.txt` | Python Packaging User Guide, "Installing packages using pip and virtual environments" |
| PEP 8 naming and layout; constants in `UPPER_CASE`; short, focused modules | `tests/` | PEP 8 |
| Docstrings that explain **why**, not just what (for example why the database is cleared each run) | `tests/conftest.py`, `tests/support/*` | PEP 257 |
| `pathlib` for file paths; `subprocess` with a list of arguments (no shell string, so nothing in an argument can run as a command) | `tests/support/server.py`, `ios_app.py` | Python docs, `subprocess` › "Security Considerations" |
| Cleanup with `try` / `finally` (the normal iOS bundle is always put back) and `yield` fixtures | `tests/support/ios_app.py` | Python docs, "The try statement" |
| `pythonpath = .` so tests import `tests.support…` without any packaging workarounds | `pytest.ini` | pytest docs, "pythonpath" |

---

## 7. Best practices not yet addressed

| Gap | Why it matters | Source |
|---|---|---|
| **No CI.** Nothing runs the tests automatically, and the last change was merged straight into `main` without a pull request or a test run on GitHub | A broken change can reach `main` unnoticed; there's no shared history of results | Martin Fowler, "Continuous Integration" (2006, rev. 2024); GitHub Actions docs |
| **No unit tests.** 0 of 24 planned (`node --test`), even though the pure helpers were already extracted to `lib/validation.js` and `app-core.js` for this | The base of the pyramid is missing; validation edge cases are tested more slowly, through the API | `docs/test-strategy.md`; test pyramid |
| **No code coverage measurement** | No one knows which server or frontend code no test runs | Node `--experimental-test-coverage` / c8; coverage.py |
| **No automated accessibility checks.** The tap target for "covered" is about 36×16 pt, and the empty date field is invisible on iOS; both were found by hand | Below Apple's 44×44 pt guideline, and likely below WCAG 2.2's 2.5.8 Target Size (Minimum, 24×24 CSS px, unless enough space surrounds the target) | WCAG 2.2; Apple HIG; axe-core / `axe-playwright-python` |
| **No dependency or code security scanning** (pip-audit, npm audit for `mobile/`, CodeQL, secret scanning, Dependabot) | Known vulnerable dependencies and leaked secrets would go unnoticed | OWASP Top 10 A06 (vulnerable and outdated components); GitHub security features |
| **No dynamic security scan** (for example OWASP ZAP) and no security headers beyond `nosniff` | See §8 | OWASP ZAP; OWASP Secure Headers Project |
| **No performance, load or reliability testing** | Acceptable for a local single-user app; needed before hosting it for others | ISTQB CTFL v4.0, non-functional testing |
| **No visual regression testing** | Layout regressions (like the cards on phones) are caught only by geometry assertions | Playwright `to_have_screenshot` |
| **One browser engine.** Chromium only; no WebKit, which is closer to iOS Safari, and no Firefox | iPhone tests run in Chromium imitating an iPhone, not Safari's engine | Playwright docs, "Browsers" |
| **Android is barely tested.** 1 test; no Android emulation or device test | Platform-specific bugs would be missed | — |
| **No exploratory testing charters or session notes** | Useful findings from the Simulator sessions live only in chat and memory | ISTQB CTFL v4.0, 4.4.2; James Bach, "Session-Based Test Management" |
| **No defect tracking.** Known bugs (the always-visible empty state, the TC-106 focus bug, the tap target) aren't in GitHub Issues, and there's no `xfail` test for them | Bugs can be forgotten, and a fix wouldn't be confirmed by a test | ISTQB CTFL v4.0, 5.5; pytest `xfail(strict=True)` |
| **No entry and exit criteria, and no test completion report** | "Done" isn't defined for a release | ISTQB CTFL v4.0, 5.1.3 and 5.3.2 |
| **No linting, formatting or type checking** for Python or JavaScript | Style drift and simple bugs aren't caught before review | Ruff, mypy or pyright; ESLint |
| **Only 32% of scenarios automated.** Negative: 3 of 28; edge cases: 2 of 31; P1: 19 of 57 | ISTQB's view is that negative and boundary cases find the most defects | `docs/test-scenarios.md` |

---

## 8. Practices that are in place but need improving

### Test automation
1. **Parallel runs.** The suite is isolated enough for `pytest-xdist`, but `test_server` would start one server per worker on the same port. It needs one shared server or a port per worker.
2. **Strict markers.** Add `--strict-markers` to `addopts`, so a misspelled marker (such as `@pytest.mark.smok`) is an error instead of silently running the test outside its suite.
3. **The deprecation warning.** Every run prints a warning about pytest-playwright's `base_url` fixture. Install `pytest-base-url`, or update pytest-playwright when a fix ships. Consider `-W error::pytest.PytestRemovedIn10Warning` in CI so new ones are noticed.
4. **The device test's date check** depends on the Mac's clock (§1.3). Allow either today's or yesterday's date around midnight, or read the date the app displays.
5. **Allure history and scenario coverage.** History isn't kept between runs, and coverage of the 180 scenarios isn't in the report. Publish both from CI.

### Quality assurance
6. **The docs have drifted from reality.**
   - `docs/test-strategy.md` › Open Questions still asks to approve `FAR_NOTES_DB` and the rate-limit override, which were done long ago.
   - The `playwright-best-practices` skill still shows a JavaScript `playwright.config.js` and `.spec.js` names, though the suite is Python.
   - `README.md` doesn't mention the tests or the mobile apps.

   Regenerate or edit them so the documents stay the test basis.
7. **Code review.** Pull requests were used for PRs #2–#4, but recent merges went straight to `main`. Turn on branch protection on `main`: require a pull request and passing CI.
8. **The progress report is out of date.** The coverage gap report is from 2026-10-28, when 14 scenarios were automated; 57 are now.

### Security in the application (before it's hosted anywhere)
9. **Missing response headers:** a Content Security Policy (it would block injected scripts even if a bug let one in), `frame-ancestors` or `X-Frame-Options` (stops the site being shown inside another site's frame), and `Referrer-Policy`. Once hosted on HTTPS, add `Strict-Transport-Security` and the `Secure` cookie flag.
10. **Rate limits are kept in memory** and keyed on the connecting IP. They reset when the server restarts, and behind a proxy every user shares the proxy's IP. They need the forwarded client IP (`X-Forwarded-For`, from a trusted proxy only), and shared storage if the server ever runs more than once.
11. **The mobile app stores its session token in `localStorage`.** Any script that runs in the web view can read it. Store it in the iOS Keychain or Android Keystore through a secure-storage plugin.
12. **Password reset prints the link to the server console.** That's fine locally; a hosted version needs an email service.
13. **No account deletion.** A hosted service would need it for privacy laws such as the GDPR's right to erasure. It's deferred, by your decision.

### Python
14. Add a `pyproject.toml` with Ruff (linting and formatting) and type hints on the shared helpers in `tests/support` and `tests/pages`. Consider pinning dependencies by hash (`pip-compile --generate-hashes`) so installs can't be tampered with.

---

## 9. Suggested order of work

1. **CI** on every pull request: the full suite, the Allure report with history, and scenario coverage. Turn on branch protection for `main`.
2. **Close the defect loop.** Put the known bugs in GitHub Issues and add `xfail(strict=True)` tests for them.
3. **Unit tests** for `lib/validation.js` and `app-core.js` (24 scenarios, fast and cheap).
4. **Accessibility:** axe checks in the component tests, and a fix for the tap-target size and the invisible date field.
5. **Breadth:** WebKit, Android emulation, and the remaining negative and edge-case scenarios.
6. **Security headers and dependency scanning,** before hosting.
7. **Linting and type checking; parallel runs** when the suite grows.

This order matches the backlog you deferred on 2026-11-02, with the defect-tracking and accessibility items added.

---

## References

Cited from general knowledge, not fetched for this review; check the current edition before quoting.

- **ISTQB:** Certified Tester Foundation Level (CTFL) Syllabus v4.0 (2023), with the ISTQB Glossary and Code of Ethics. istqb.org
- **ISO/IEC/IEEE 29119** Software Testing (parts 1–4), and IEEE 829 (test documentation; superseded by 29119-3).
- **OWASP:** Top 10:2021; Application Security Verification Standard (ASVS); Cheat Sheet Series (Password Storage, Session Management, Authentication, CSRF Prevention, XSS Prevention, HTTP Headers); Secure Headers Project; ZAP. owasp.org
- **NIST** SP 800-63B, Digital Identity Guidelines: Authentication and Lifecycle Management. pages.nist.gov/800-63-4
- **W3C:** WCAG 2.2 (Success Criterion 2.5.8, Target Size (Minimum)); WAI-ARIA. w3.org/WAI
- **Apple** Human Interface Guidelines, "Accessibility" (minimum 44×44 pt tap targets). developer.apple.com/design
- **Playwright** docs: Best Practices, Locators, Assertions, Auto-waiting, Mock APIs, Trace viewer, Emulation; pytest-playwright plugin. playwright.dev/python
- **pytest** docs: fixtures, markers, parametrize, skip and xfail, hooks, configuration. docs.pytest.org
- **Python:** PEP 8, PEP 257; Python Packaging User Guide; `subprocess` security notes. python.org
- **Appium** XCUITest driver documentation. appium.io
- **Allure Report** documentation. allurereport.org
- **Martin Fowler** (martinfowler.com): "TestPyramid" and "The Practical Test Pyramid" (Ham Vocke), "PageObject", "Eradicating Non-Determinism in Tests", "Continuous Integration".
- **Books:** Mike Cohn, *Succeeding with Agile* (2009); Gerard Meszaros, *xUnit Test Patterns* (2007); Kent Beck, *Test-Driven Development by Example* (2002); Kaner, Bach and Pettichord, *Lessons Learned in Software Testing* (2001).
- **Google Testing Blog:** "Just Say No to More End-to-End Tests" (2015). testing.googleblog.com
- **This project:** `CLAUDE.md`; `docs/test-scenarios.md`; `docs/test-strategy.md`; `progress_reports/`; and the skills in `.claude/skills/` (`create-scenarios`, `test_strategy`, `generate-tests`, `playwright-best-practices`, `far-notes-domain`).
