# Session Summary: 2026-10-27 to 2026-11-03

Claude Code session `agentic_development_UI_API_Mobile`. It took FAR Notes from an untested website to a tested website plus iOS and Android apps, with test reports and a repeatable best-practices review.

**Bottom line:** 57 of 180 scenarios are automated, including all 23 P0 scenarios. The suite has 88 tests across the API, component and E2E layers, all passing in about 13 s, plus 1 Appium test on the real iOS app that passes in about 30 s. Nothing runs automatically yet: there's no CI.

| | Start (2026-10-27) | End (2026-11-03) |
|---|---|---|
| Test scenarios | none | 180 (`docs/test-scenarios.md`) |
| Automated scenarios | 0 | 57, with all 23 P0 |
| Tests | none | 88 web + 1 device, all passing |
| Platforms | website | website, iOS app, Android app (Capacitor 8.6) |
| Test reports | none | Allure 3, grouped by Web/Mobile › platform › layer |
| Pull requests | 0 | 7 merged, plus 2 direct merges |

## Timeline

### 1. Claude Code setup and test planning (10-27)

- **`CLAUDE.md`** written with `/init`.
- **Skills** added under `.claude/skills/`:

  | Skill | What it does |
  |---|---|
  | `far-notes-domain` | Holds the app's rules. Split into `business-rules.md`, `user-flows.md`, `data-models.md` and `api-reference.md`. |
  | `create-scenarios` | Writes `docs/test-scenarios.md` using 6 lenses: happy path, business rules, security, negative, edge cases and UI state. |
  | `test_strategy` | Writes `docs/test-strategy.md`, choosing one layer for each scenario with the reason. |
  | `playwright-best-practices` | Sets the conventions for locators, fixtures, page objects, mocking and waits. |
  | `generate-tests` | Writes the tests, checks them, runs each 3 times, and debugs a failure up to 3 times before deciding whether it's a test bug or an application bug. |

- **Bug fixed:** pressing Escape while editing a heading kept the edited text instead of restoring the original.

### 2. Test suite (10-27 to 10-29) → PR #1

- **Switched to Python.** The tests were first planned in JavaScript Playwright and rewritten in **Python with pytest and pytest-playwright**. Unit tests for the JavaScript helpers stay on `node --test`; none are written yet.
- **Refactored the app so it can be tested:**
  - Pure helpers moved into `lib/validation.js` and `app-core.js`.
  - `FAR_NOTES_DB` and `FAR_NOTES_DISABLE_RATE_LIMIT` added, so tests use their own server on port 3100 with a separate database.
- **Coverage gap analysis:** `progress_reports/2026-10-28_coverage-gap-report.md` found 14 of 157 scenarios automated (9%). The P0 and Smoke scenarios were then automated.
- **Two `app.js` bugs fixed**, each with a new scenario:
  - The heading input stayed visible after saving (TC-519).
  - The Edit button's accessible name went stale after a rename (TC-520).
- **VMC43 login:** the account lived only in the `far-notes` project's database, which git excludes. That database was copied in, and the empty one was kept in `data/backups/`.

### 3. Mobile apps (10-29 to 10-30) → PRs #1 to #3

- **Capacitor chosen over a native Swift app.** It means one codebase for the website, iOS and Android, and the tests still cover most of the app.
- **`api-client.js` added** so the same pages work on the website and in the app. It supports bearer-token sessions and a CORS allowlist for the app origins.
- **iOS fixes**, found in the Simulator from the user's screenshots:

  | Fix | Scenarios | PR |
  |---|---|---|
  | No zooming into text fields on touch screens | TC-521, TC-522 | #2 |
  | Pages kept clear of the status bar and home indicator | TC-523 | #3 |
  | Study items shown as stacked cards on phones | TC-524 | #3 |
  | Solid bars over the safe areas when scrolling | TC-525 | #3 |
  | Sections collapsed by default, with Expand all and Collapse all | TC-526 to TC-531 | #3 |

- **Test speed:** the test server now starts each run with an empty database. The shared one had grown to 1,343 users and took more than 15 s to start.
- **Git setup:** commits use the GitHub noreply email, and a pull request is opened for each change.

### 4. Team reporting with Allure (10-30) → PR #4

- **Tool choice:** CI with GitHub Actions plus Allure was recommended over Xray, Zephyr and TestRail.
- **Allure setup:**
  - `allure-pytest` records the results, and Allure 3 builds the report: `npx allure@3.22.1`. Plain `npx allure` runs an old Allure 2 install.
  - `allurerc.mjs` and a `mobile("ios"|"android")` marker group the report as **Web / Mobile › iOS or Android › layer**.

### 5. Appium device test (11-02) → direct merges

- **`tests/device/`** runs TC-022 on the real iOS app in the iPhone 17 Simulator, and runs only with `--run-device`. The test:
  - signs in
  - marks 91.103(a) covered and checks the save through the API
  - relaunches the app and checks that the sign-in and the item survived
- **Build:** each run builds the app against the test server, then restores the normal bundle.
- **`--slowmo`** is supported for watching a run. The user found it too slow, so normal runs leave it off.
- **`Package.resolved`** committed. It pins Capacitor's Swift package so every build is the same.

### 6. Best-practices reviews (11-03) → PRs #5 to #7

- **`docs/best-practices/2026-11-03_best-practices-review.md`** covers automation, QA, ISTQB, security, pytest and Python, with sources, gaps and improvements.
- **Dated reviews.** Reviews are now dated, and the new **`best-practices-review`** skill writes a fresh dated review that compares against the previous one.
- **Second review:** `2026-11-03_best-practices-review_2.md`.
  - Scorecard: 21 in place, 12 partial and 14 missing, out of 47 practices.
  - It corrects one wrong claim from the first review.

### 7. Explanations given along the way

These topics were explained during the session:
- pytest: `parametrize`, `-k`, `--headed`, the `request_context` fixture, and where `base_url` comes from
- Git and tooling: `Package.resolved`, and why the `mobile/` folder looked untracked in VS Code (stale status, fixed by reloading the window)
- Design patterns in the project
- AI-assisted testing compared with agentic testing

## Problems hit and how they were solved

| Problem | Cause | Fix |
|---|---|---|
| Test database wiped | It lived in `test-results/`, which Playwright clears | Moved to `.test-data/` |
| TC-010 locator broke | It relied on the Edit button's stale label, which was bug TC-520 | `SectionRow` locates by its row element |
| TC-015 response unreadable | The page navigates away before the response can be read | A `route.fetch` observer, which doesn't stub the response |
| Allure ignored the groups | Allure 3 groups by file path by default | `allurerc.mjs` with `groupBy` |
| `--device` option clash | pytest-playwright already uses `--device` | Renamed to `--run-device` |
| Appium tap on "covered" did nothing | The checkbox is a 1×2px hidden input | Tap its parent element |

## Defects found and not fixed (deferred by the user)

- **The "No study items found" message is always visible**, on the website too, because `.empty-state { display: flex }` overrides `hidden`.
- **eCFR links leave the app** and open in Safari. The proposed fix is an in-app browser.
- **On iOS, an empty date field is invisible**, and the "covered" tap target is about 36×16pt. Apple recommends 44×44.
- **There's no way to delete an account.**

## What's next (deferred backlog, in recommended order)

1. GitHub Actions CI on every pull request, publishing the Allure report with its history.
2. WebKit and Android coverage. Android has only 1 test (TC-229).
3. A script that checks scenario coverage.
4. Parallel runs with pytest-xdist.
5. More Appium tests, run nightly, including Android. Android Studio isn't installed yet.
6. The quick wins from review 2:
   - `--strict-markers`
   - update the stale docs: the strategy's Open Questions, the skill's "Current state" and `README.md`
   - a comment at `server.js:850`
7. Bug tracking: GitHub Issues, plus `xfail(strict=True)` tests for known bugs.

## Ground rules followed throughout

- Tests never touch `data/part91.sqlite`, the `VMC43` account or the dev server on port 3000.
- Application code changes only after the user approves them.
- Test results are reported exactly as they came out.
- Commits and merges happen only when the user asks.

## Pull requests

| # | Change |
|---|---|
| 1 | Test suite, Claude Code skills, and the iOS and Android apps |
| 2 | Stop iOS from zooming into text fields |
| 3 | Safe areas, phone cards and collapsible sections |
| 4 | Allure reports grouped by platform |
| – | Appium iOS test (TC-022) and `Package.resolved` (direct merges) |
| 5 | First best-practices review |
| 6 | Dated reviews and the `best-practices-review` skill |
| 7 | Second best-practices review |

The full transcript is in `~/.claude/projects/-Users-conniesocash-Documents-Programming-Playwright-Projects-far-notes-playwright-agentic/64d184f2-4e5e-43b6-a05c-daa3243caf7c.jsonl`. Resume the session with `claude --resume` and pick `agentic_development_UI_API_Mobile`.
