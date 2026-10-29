# Coverage Gap Report: 2026-10-28

**Bottom line:** 14 of 157 planned scenarios are automated (9%), and all 15 test runs pass. All 14 cover signing in. The tracker itself (studying items, sections, search, parts) has no automated tests beyond TC-002 confirming it loads after sign-in. Only 2 of 18 P0 security and isolation scenarios are covered.

Sources:
- `docs/test-scenarios.md` (157 scenarios)
- `docs/test-strategy.md` (layer assignments, test layout, suites)
- all files in `tests/`
- a fresh test run

## Test run

`.venv/bin/pytest -v --tb=line` is the pytest equivalent of `npx playwright test --reporter=line`. The suite has been Python since 2026-10-27, so `npx playwright test` no longer applies.

**15 passed, 0 failed, 0 skipped**, in 3.3 s. That's 14 scenarios, with TC-202 run once for each of its two pages. There are no `xfail` or skipped tests.

| File | Scenarios | Result |
|---|---|---|
| `api/test_auth.py` | TC-003, 125, 129, 213, 215, 301, 406, 427 | 8 ✅ |
| `api/test_access_control.py` | TC-202 (×2) | 2 ✅ |
| `api/test_rate_limits.py` | TC-217 | 1 ✅ |
| `component/test_auth_pages.py` | TC-300, 302, 511 | 3 ✅ |
| `e2e/test_signup_signin.py` | TC-002 | 1 ✅ |

## Planned vs implemented

| Layer | Done / planned | P0 | P1 | P2 | P3 |
|---|---:|---:|---:|---:|---:|
| Unit (`node --test`) | **0 / 24** | – | 0/4 | 0/12 | 0/8 |
| API | 10 / 68 | 1/15 | 3/18 | 5/18 | 1/17 |
| Component | 3 / 52 | 0/2 | 1/13 | 0/21 | 2/16 |
| E2E | 1 / 12 | 1/3 | 0/9 | – | – |
| Manual | 0 / 1 | – | – | – | 0/1 |
| **Total** | **14 / 157 (9%)** | **2/20** | **4/44** | **5/51** | **3/42** |

By category: Security 4/27, Negative 3/28, Business Rule 2/33, Edge Case 2/31, Happy Path 2/19, UI State 1/19.

Smoke suite: 2 of 22 (TC-002, TC-213). The 20 missing Smoke tests are all P0 or core happy paths:

TC-001, 006, 010, 015, 103, 118, 126, 131, 200, 201, 203, 204, 206, 208, 209, 210, 211, 212, 221, 222.

### By planned file

| Planned file | Done | Missing P0/P1 |
|---|---:|---|
| `tests/api/test_access_control.py` | 1/12 | TC-200, 201, 203, 204, 205, 209, 210, 222, 223, 225 |
| `tests/api/test_auth.py` | 7/15 | TC-123, 124, 130, 208, 224, 304 |
| `tests/api/test_origin.py` | 0/2 | TC-206 |
| `tests/api/test_password_reset.py` | 0/6 | TC-126, 127, 128 |
| `tests/api/test_rate_limits.py` | 1/3 | TC-218 |
| `tests/api/test_regulations.py` | 0/14 | TC-004, 019, 103, 104, 118, 131 |
| `tests/api/test_robustness.py` | 1/8 | TC-214, 221 |
| `tests/api/test_subsections.py` | 0/8 | – |
| `tests/component/test_auth_pages.py` | 3/10 | TC-303 |
| `tests/component/test_tracker_errors.py` | 0/6 | TC-322, 325, 326 |
| `tests/component/test_tracker_parts.py` | 0/4 | TC-005 |
| `tests/component/test_tracker_search_filter.py` | 0/9 | TC-012, 013 |
| `tests/component/test_tracker_sections.py` | 0/9 | TC-011, 102 |
| `tests/component/test_tracker_security.py` | 0/2 | TC-211, 212 |
| `tests/component/test_tracker_state.py` | 0/7 | TC-503 |
| `tests/component/test_tracker_study_items.py` | 0/5 | TC-009, 121 |
| `tests/e2e/test_password_reset.py` | 0/1 | TC-014 |
| `tests/e2e/test_sections.py` | 0/3 | TC-010, 108, 428 |
| `tests/e2e/test_signup_signin.py` | 1/4 | TC-001, 015, 018 |
| `tests/e2e/test_study_items.py` | 0/4 | TC-006, 007, 419, 420 |
| `tests/unit/app-core.test.js` | 0/13 | TC-100, 114 |
| `tests/unit/validation.test.js` | 0/11 | TC-307, 400 |
| `docs/manual-checklist.md` | 0/1 | – |

## Missing test layers

- **Unit: none written.** `tests/unit/` doesn't exist yet. The 2026-10-27 refactor (`lib/validation.js`, `app-core.js`) is checked only by one-off comparisons outside the suite, so nothing guards it against regressions.
- **Component tests only cover the login page.** The 49 tracker scenarios need a setup that serves the tracker page with its API calls faked, plus mock data builders. Neither exists yet.
- **E2E: 1 of 12.** None of the 4 core journeys (sign-up, study an item, add a section, log out) and none of the save and Escape regression tests (TC-108, TC-428, TC-419, TC-420) are covered.
- **API coverage is mostly login.** Six planned files have no tests (see the table above).

### Missing setup that blocks tests

| Missing piece | Blocks |
|---|---|
| `signed_in_page` fixture, `StudyItemRow` and `SectionRow` page objects | the 11 remaining E2E tests |
| Tracker component setup (`mock_signed_in`, `mock_regulations`) and `tests/mocks/data.py` | 49 component tests, including P0 TC-211 and TC-212 |
| Database fixture (seed reset tokens, expire sessions) | TC-126 (P0), 127, 128, 225, 014 |
| Small regulations helper (look up section and subsection ids through the API) | most of `test_regulations.py`, `test_subsections.py` and `test_access_control.py` |

### Rules with no scenario at all

These come from `docs/test-strategy.md` › Anti-Patterns › Scenario gaps:

- reset links expire after 30 minutes
- subsection titles are restored from the catalog on startup
- legacy progress is copied into subsections
- the 16 KB body limit applies to auth endpoints

## What to write next, in priority order

1. **13 P0 API security and isolation tests.** These need only the regulations helper; everything else exists.
   - TC-103, 118, 131, 200, 201, 203, 204, 206, 208, 209, 210, 221, 222
   - Add the P1 tests in the same files at the same time: TC-123, 124, 205, 214, 223, 224 and 304.

   This is the biggest risk reduction for the effort, and it takes the Smoke suite from 2 to 15.
2. **24 unit tests on `node --test`.** No new setup is needed, they run in milliseconds, and they guard the refactor. Start with the P1 tests: TC-100, 114, 307 and 400.
3. **Core E2E journeys.** First add `signed_in_page`, `StudyItemRow`, `SectionRow` and a fixed clock.
   - The 4 Smoke journeys: TC-001, 006, 010 and 015.
   - Then the regression guards: TC-108 and TC-428 (the Escape fix), and TC-007, 018, 419 and 420.
4. **Tracker component setup**, then the P0 and P1 component tests.
   - P0: TC-211 and 212 (injected HTML shown as text).
   - P1: TC-322, 325 and 326 (error handling), TC-503 (counts), TC-012 and 013 (search and filters), TC-009, 121, 011, 102 and 005.
5. **Database fixture**, then TC-126 (P0), 127, 128, 225 and 014.
6. **New scenarios** for the 4 uncovered rules, through `/create-scenarios`.
7. **Everything else:** the remaining P2 and P3 tests, file by file.

Items 1 and 2 together would take coverage from 9% to about 30%, and P0 coverage from 2/20 to 15/20, without building any new test setup beyond a small helper.
