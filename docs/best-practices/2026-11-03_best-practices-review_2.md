# Best Practices Review: 2026-11-03 (second review)

Reviewed 2026-11-03 against `main` at `cfe085d`. Baseline: `2026-11-03_best-practices-review.md` (same day, at `6a65056`).

## Summary

Nothing in the tests or application has changed since the baseline. The 4 commits since then (`3a51ab2`, `4d40f3a`, `ee5a441`, `cfe085d`) only added and dated the review and created the `best-practices-review` skill. So every measurement is unchanged: 57 of 180 scenarios automated, all 23 P0 scenarios included, and 88 tests passing plus the iOS device test.

- **The biggest improvement is in process.** Reviews are now dated records made by a repeatable skill, and the last two merges went through pull requests (#5, #6).
- **The biggest remaining risk** is unchanged: there's no CI, and no tracking of known bugs. Any change can still reach `main` without the tests running, and the known bugs (the empty state that's always visible, the TC-106 focus bug, the small iOS tap target) exist only in notes.
- **This review corrects one baseline claim.** The baseline said the `playwright-best-practices` skill still described a JavaScript setup. It doesn't: it has been Python since `59f9d34`. Its "Current state" paragraph and its copy of `pytest.ini` are out of date, though (§8.6).

## Measurements

| Measure | Baseline | Now | Change |
|---|---|---|---|
| Commit reviewed | `6a65056` | `cfe085d` | +4 commits, docs and skill only |
| Scenarios in `docs/test-scenarios.md` | 180 | 180 | – |
| Scenarios automated | 57 (32%) | 57 (32%) | – |
| … P0 / P1 / P2 / P3 | 23/23 · 19/57 · 11/57 · 4/43 | 23/23 · 19/57 · 11/57 · 4/43 | – |
| … Negative / Edge case | 3/28 · 2/31 | 3/28 · 2/31 | – |
| Tests without a scenario | 0 | 0 | – |
| Tests collected (normal run) | 88 of 89 (1 device test deselected) | 88 of 89 | – |
| API / component / E2E / device | 63 / 20 / 5 / 1 | 63 / 20 / 5 / 1 | – |
| Smoke / mobile-tagged | 52 / 14 | 52 / 14 | – |
| Unit tests (`node --test tests/unit`) | 0 (folder missing) | 0 ("Could not find 'tests/unit'") | – |
| `xfail` / skipped tests | 0 / 0 | 0 / 0 | – |
| Full run | 88 passed, 1 warning, ~13 s | **88 passed, 1 warning, 13.03 s** | – |
| Device test (iOS Simulator, Appium) | passed (5 of 5 runs) | **1 passed, 30.25 s** | – |
| Warnings | 1 (`PytestRemovedIn10Warning`, pytest-playwright's `base_url`) | 1 (same) | – |

All "Now" values come from commands run during this review (`.venv/bin/pytest -q`, `--collect-only`, `-m <marker>`, `--run-device -m device`, the scenario-coverage script in the skill, and `git log`).

## Scorecard

The baseline had no scorecard. Its statuses below are **derived** as the skill describes: items in its sections 7 and 8 count as ❌ or ⚠️, and practices described in sections 1–6 count as ✅. Every "Now" status was checked again in this review.

| # | Area | Practice | Baseline | Now | Evidence (this review) |
|---|---|---|---|---|---|
| 1 | Automation | One primary layer per scenario; E2E ≤ 15% | ✅ | ✅ | `docs/test-strategy.md:12,17`: E2E 12 of 179 planned (6.7%); in practice 5 of 89 tests |
| 2 | Automation | Isolation: fresh user, client and database; port 3100; rate limit off only in tests | ✅ | ✅ | `tests/conftest.py` (`test_server`, `request_context`, `fresh_user`); `tests/support/server.py` |
| 3 | Automation | No fixed waits in tests | ✅ | ✅ | 4 `time.sleep` hits, all documented: 3 polling loops (`tests/support/server.py:49`, `tests/device/conftest.py:44`, `tests/device/test_ios_app.py:21`) and the opt-in slow mode (`tests/pages/ios_app.py:25`). No `wait_for_timeout` or `networkidle` |
| 4 | Automation | Time and time zone fixed where "today" matters | ⚠️ | ⚠️ | Fixed for the browser (`tests/conftest.py:78`, `tests/e2e/test_study_items.py:13`); the device test still uses the Mac's clock (`tests/device/test_ios_app.py:38`) |
| 5 | Automation | Role and label locators; reasons for CSS/XPath | ✅ | ✅ | The one XPath and 2 CSS locators carry a reason (`tests/pages/ios_app.py:73`, `create_account_page.py:7`, `tracker_page.py:49`). The 8 summary-number locators in `tracker_page.py:17–24` have no inline reason, but are allowed by the skill's locator table, row 6 |
| 6 | Automation | No `expect` in page objects; setup through the API | ✅ | ✅ | No `expect` calls in `tests/pages/*.py` |
| 7 | Automation | Component tests stub; E2E tests don't | ✅ | ✅ | The only `page.route` in `tests/e2e` (`test_signup_signin.py:51`) is a documented observer that passes the real response through |
| 8 | Automation | Trace, screenshot and video kept on failure | ✅ | ✅ | `pytest.ini` addopts |
| 9 | Automation | Reporting with history | ⚠️ | ⚠️ | Allure configured (`allurerc.mjs`), but no `history` setting, so no trends |
| 10 | Automation | Android coverage | ❌ | ❌ | 1 test tagged `mobile("android")` |
| 11 | Automation | New tests repeated 3×; control assertions | ✅ | ✅ | `generate-tests` skill step 3; controls in `test_touch_layout.py:52`, `test_ios_app.py:30`, `test_mobile_clients.py` (TC-231) |
| 12 | Automation | Parallel runs | ⚠️ | ⚠️ | No `pytest-xdist` in `requirements-dev.txt` |
| 13 | Automation | More than one browser engine | ❌ | ❌ | `--browser chromium` only (`pytest.ini`) |
| 14 | Automation | Unit tests | ❌ | ❌ | `tests/unit` doesn't exist |
| 15 | Automation | Code coverage measured | ❌ | ❌ | No coverage tool configured |
| 16 | Automation | Automated accessibility checks | ❌ | ❌ | No axe or similar in the requirements |
| 17 | Automation | Visual regression | ❌ | ❌ | No screenshot comparisons in `tests/` |
| 18 | Automation | Performance and load testing | ❌ | ❌ | None. Acceptable for a local single-user app until it's hosted |
| 19 | QA | Scenario structure; all P0 automated | ✅ | ✅ | P0 23/23 (coverage script) |
| 20 | QA | Traceability | ✅ | ✅ | Tests without a scenario: `[]`; every test name starts with a TC id |
| 21 | QA | Known bugs tracked | ❌ | ❌ | GitHub API: 0 issues (6 pull requests); `grep xfail` finds nothing |
| 22 | QA | Docs match reality | ⚠️ | ⚠️ | Strategy Open Questions 1–3 are stale; the skill's "Current state" paragraph is stale; `README.md` doesn't mention the tests or the apps; the latest progress report is from 2026-10-28 |
| 23 | QA | CI runs the tests | ❌ | ❌ | No `.github/` folder |
| 24 | QA | Merges through reviewed pull requests; `main` protected | ⚠️ | ⚠️ | Last 10 merges: 8 through pull requests, 2 direct (`6730fb0`, `6a65056`). The last 2 (#5, #6) went through pull requests. Branch protection not checked: the GitHub API needs a sign-in for that |
| 25 | QA / ISTQB | Test design techniques | ✅ | ✅ | Equivalence partitions, boundaries, decision tables and state transitions are visible in `test_origin.py`, `test_auth.py`, `test_robustness.py`, `test_mobile_clients.py`, `test_tracker_collapse.py` |
| 26 | QA / ISTQB | Entry and exit criteria; completion reports; exploratory charters | ❌ | ❌ | Not found in `docs/` or `progress_reports/` |
| 27 | QA | Scenario automation breadth | ❌ | ❌ | 57/180 (32%); Negative 3/28; Edge 2/31 |
| 28 | Security | Access control | ✅ | ✅ | `test_access_control.py` (TC-200 to TC-204, TC-209, TC-210, TC-222) |
| 29 | Security | Password and token cryptography | ✅ | ✅ | `server.js:457` (dummy scrypt for unknown users), `server.js:459` (`timingSafeEqual`) |
| 30 | Security | Injection: bound SQL values; safe DOM writes | ✅ | ✅ | `server.js:850` builds its column list only from fixed text, with values bound as `?`; the 3 `innerHTML` writes (`app.js:383,393,406`) use fixed text |
| 31 | Security | Rate limits, body limit, origin check, CORS, bearer token | ✅ | ✅ | `test_rate_limits.py`, `test_robustness.py`, `test_origin.py`, `test_mobile_clients.py` |
| 32 | Security | Rate limits ready for hosting | ⚠️ | ⚠️ | Kept in memory and keyed on the connecting IP |
| 33 | Security | Cookie flags | ⚠️ | ⚠️ | HttpOnly and SameSite=Strict; no `Secure` (`server.js:384`). Fine on localhost |
| 34 | Security | Security response headers | ❌ | ❌ | Only `X-Content-Type-Options` (`server.js:611,666`); no CSP, frame, referrer or HSTS headers |
| 35 | Security | Mobile token storage | ⚠️ | ⚠️ | `localStorage` (`api-client.js:25,33`) |
| 36 | Security | Dependency and code scanning | ❌ | ❌ | No Dependabot, no CodeQL; `pip-audit` not installed |
| 37 | Security | No secrets or personal email committed | ✅ | ✅ | `git log -20 --format=%ae`: only the noreply address |
| 38 | Security | Account deletion | ⚠️ | ⚠️ | No delete endpoint; deferred by the project owner |
| 39 | Security | Password reset delivery | ⚠️ | ⚠️ | The link is printed to the server console. Fine locally |
| 40 | pytest | Fixtures with `yield` cleanup and deliberate scopes | ✅ | ✅ | 11 `yield` fixtures; 4 session-scoped fixtures in `conftest.py` files |
| 41 | pytest | Markers registered and enforced | ⚠️ | ⚠️ | Registered in `pytest.ini`; no `--strict-markers` |
| 42 | pytest | `parametrize` ids; options deselect rather than skip | ✅ | ✅ | 4 uses of `ids=` / `pytest.param`; `--run-device` deselects (`tests/conftest.py`) |
| 43 | pytest | Warnings | ⚠️ | ⚠️ | 1 warning in every run (pytest-playwright's `base_url`) |
| 44 | Python | Pinned dependencies; virtual environment | ✅ | ✅ | `requirements-dev.txt`: 5 exact pins; `.venv` |
| 45 | Python | Linting, formatting and type checking | ❌ | ❌ | No `pyproject.toml`, Ruff or pre-commit config; 0 return-type hints in `tests/support` and `tests/pages` |
| 46 | Python | `subprocess` without a shell | ✅ | ✅ | `grep shell=True tests`: none |
| 47 | QA | Regular, recorded best-practice reviews | new | ✅ | `docs/best-practices/` and the `best-practices-review` skill (`ee5a441`) |

**Counts:** ✅ 21 · ⚠️ 12 · ❌ 14 · ➖ 0 (baseline, derived: ✅ 20 · ⚠️ 12 · ❌ 14 · ➖ 0, for 46 practices; row 47 is new).

## Changes since the baseline

- **Improved**
  - Reviews are now dated and repeatable: `docs/best-practices/2026-11-03_best-practices-review.md` and the `best-practices-review` skill (`ee5a441`, merged in #6).
  - The two merges since the baseline went through pull requests (#5, #6), after two direct merges before it (`6730fb0`, `6a65056`). The status stays ⚠️ until branch protection makes this a rule rather than a habit.
- **Got worse:** nothing.
- **Still open** (all first listed in the baseline, 2026-11-03):
  - No CI.
  - No bug tracking.
  - No unit tests.
  - No code coverage.
  - No accessibility checks.
  - Chromium only.
  - Android barely covered.
  - No security headers, and no dependency or code scanning.
  - No `--strict-markers`.
  - No linting or type checking.
  - The pytest-playwright warning.
  - Docs out of date.
  - Scenario breadth at 32%.
- **New gaps found**
  - The `playwright-best-practices` skill's "Current state (2026-10-28)" paragraph says "59 test items … 32 scenarios … 20 of the 20 P0". Its copy of `pytest.ini` lacks the `mobile` and `device` markers. Both are stale.
  - The baseline's own claim about that skill (JavaScript config) was wrong, so an earlier review needs checking too, not just the code. This review corrects it here and leaves the baseline unchanged, as a record.
  - The 8 summary-number locators in `tests/pages/tracker_page.py:17–24` carry no inline reason. They're allowed by the skill's locator rules, so this is a minor point.

## 1. Test automation practices

Re-checked and unchanged since the baseline. Sources are as in the baseline's §1.
- **1.1 Test pyramid:** one layer per scenario (63 API, 20 component, 5 E2E, 1 device).
- **1.2 Isolation:** a fresh user and client per test; a fresh database per run; port 3100.
- **1.3 Determinism:** no fixed waits, only documented polling; the browser clock and time zone fixed; the device test's date check is the exception.
- **1.4 Locators** by role and label, matching VoiceOver labels on iOS.
- **1.5 Page objects,** data builders and API setup.
- **1.6 Network stubbing** in component tests only; the one E2E route is an observer.
- **1.7 Evidence on failure** (trace, screenshot, video) and the Allure report.
- **1.8 Mobile testing** at two depths: Chromium emulation, plus Appium on the Simulator, re-run in this review and passing.
- **1.9 Control assertions,** and new tests proven to fail.

## 2. Quality assurance process

Unchanged, plus one addition. Scenarios come before code; priorities are risk-based (P0 23/23); traceability is complete (no tests without a scenario); the domain docs act as the oracle; failures are triaged as test or application bugs; open questions are recorded; coverage reports exist; and changes go through branches and pull requests. **New:** a repeatable, dated best-practices review with a scorecard.

## 3. ISTQB concepts, mapped to this project

Unchanged; see the baseline's §3: the note on terms, the techniques (equivalence partitioning, boundary values, decision tables, state transitions, error guessing, checklists), the test types, the seven principles and the test process. The process activity "completion" is still missing (row 26).

## 4. Security practices

Unchanged. Every control in the baseline's §4 table was re-checked against `server.js`, `api-client.js` and the tests (rows 28–39). One clarification: `server.js:850` builds part of an SQL statement with `${updates.join(", ")}`. It's safe, because the joined parts are fixed text and every user value is bound as a `?` parameter. A future change that put user input into `updates` would break this, so it's worth a short comment in the code.

## 5. pytest practices

Unchanged: `yield` fixtures with deliberate scopes, shared `conftest.py` files, registered markers applied from folders, `parametrize` with ids and per-case marks, `--run-device` deselecting rather than skipping, reused plugin options (`--slowmo`, `--headed`, `--base-url`), and the `xfail(strict=True)` policy, still unused.

## 6. Python practices

Unchanged: a virtual environment with exact pins, PEP 8 naming, docstrings that explain why, `pathlib`, `subprocess` with argument lists and no shell, and `try`/`finally` cleanup.

## 7. Best practices not yet addressed

Unchanged from the baseline (rows 10, 13–18, 21, 23, 26, 27, 34, 36, 45):
- CI
- unit tests
- code coverage
- automated accessibility checks
- dependency and code scanning, and security headers
- performance testing (acceptable until hosting)
- visual regression
- browser engines beyond Chromium
- Android
- exploratory charters
- bug tracking
- entry and exit criteria, and completion reports
- linting and type checking
- scenario breadth (Negative 3/28, Edge 2/31)

## 8. Practices in place that need improving

Items 1–5 and 7–14 are as in the baseline and still open (rows 4, 9, 12, 22, 24, 32, 33, 35, 38, 39, 41, 43). Item 6 is corrected:

6. **The docs have drifted from reality** (corrected list):
   - `docs/test-strategy.md` › Open Questions 1–3 ask to approve `FAR_NOTES_DB`, the rate-limit override and the unit-test refactors, which were all done long ago. Its Prerequisites section is up to date.
   - The `playwright-best-practices` skill is Python (the baseline was wrong here), but its "Current state (2026-10-28)" paragraph and its `pytest.ini` copy are out of date.
   - `README.md` doesn't mention the tests or the mobile apps.
   - The newest progress report, `progress_reports/2026-10-28_coverage-gap-report.md`, reports 14 scenarios automated; the real figure is 57.

## 9. Suggested order of work

Unchanged, since nothing on it has been started:
1. CI on pull requests, with the Allure report and history, plus branch protection.
2. Bugs into GitHub Issues, with `xfail(strict=True)` tests.
3. Unit tests.
4. Accessibility checks and fixes.
5. WebKit, Android and the negative and edge-case scenarios.
6. Security headers and dependency scanning.
7. Linting, type checking and parallel runs.

**Quick wins** that take minutes and would turn ⚠️ rows into ✅ in the next review:
- add `--strict-markers` (row 41)
- update the stale Open Questions, the skill's "Current state" paragraph and `README.md` (row 22)
- add a comment at `server.js:850` (§4)

## References

As in the baseline (ISTQB CTFL v4.0; ISO/IEC/IEEE 29119; OWASP Top 10:2021, ASVS and Cheat Sheets; NIST SP 800-63B; WCAG 2.2; Apple HIG; Playwright, pytest, Python, Appium and Allure documentation; Fowler, Cohn, Meszaros, Beck, and Kaner, Bach and Pettichord). Cited from general knowledge, not fetched in this review. The GitHub REST API was queried in this review for the issue count only.
