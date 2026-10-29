---
name: generate-tests
description: Generate, validate, run and fix Python pytest + Playwright tests for FAR Notes from docs/test-scenarios.md and docs/test-strategy.md. Follows a 5-step loop - write, validate (including live checks with the Playwright MCP browser), run, debug and fix, then classify each remaining failure as a test bug or an application bug against the far-notes-domain docs. Use when asked to write, generate, implement or automate tests for scenarios, a feature or a layer.
argument-hint: "[TC ids, feature-name, layer (unit|api|component|e2e), or blank for the Smoke suite]"
---

# Generate Tests

Turn scenarios into working **Python** tests: pytest with pytest-playwright for the API, component and E2E layers. Unit tests for the JavaScript helpers are the only exception and use `node:test`. A test is **done** only when it passes for the right reason, or fails because of a confirmed application bug that is clearly marked.

## Inputs

| Source | Use it for |
|--------|------------|
| `$ARGUMENTS` | Scope: TC ids (`TC-006 TC-108`), a feature (`auth`, `study-items`, `sections`, `search`, `parts`, `password-reset`), a layer (`api`, `component`, `e2e`, `unit`), or blank for the **Smoke** suite in `docs/test-strategy.md` |
| `docs/test-scenarios.md` | Steps, expected results and the Business Rule for each TC |
| `docs/test-strategy.md` | The layer, supporting layer, target file and prerequisites for each TC |
| `playwright-best-practices` skill | **Load it before writing any code.** It covers config, naming, locators, fixtures, POM, mocking, waits and anti-patterns |
| `far-notes-domain` skill | Expected behavior. In step 5, it is the reference for deciding test bug versus application bug |

If either `docs/` file is missing, stop and tell the user to run `/create-scenarios` and then `/test-strategy`.

## Before Step 1: Check prerequisites

Check that the test infrastructure exists (`docs/test-strategy.md` › Prerequisites):

- `.venv` exists with `requirements-dev.txt` installed, and `pytest.ini` and `tests/conftest.py` exist. If not, run `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt && .venv/bin/playwright install chromium`.
- The **test database is isolated**: `server.js` reads a configurable database path, and the `test_server` fixture in `tests/conftest.py` points it at `.test-data/far-notes-test.sqlite`.
- The **register rate-limit override** exists (or seeded users), unless the scope is only the rate-limit tests.
- For unit scope: the pure helpers are importable (`lib/validation.js`, `app-core.js`).
- The fixtures, page objects and mocks the target tests need exist under `tests/`.

If anything is missing, **don't write tests that rely on it**. List what's missing and ask the user before changing application code (`server.js`, `app.js`, `index.html`). Test-only files under `tests/`, plus `pytest.ini` and `requirements-dev.txt`, can be created without asking. **Never** run tests against `data/part91.sqlite` or against the dev server on port 3000.

## Process

### 1. Write the tests

1. Resolve the scope to a list of TC ids. Read each scenario and its row in the strategy's Layer Assignments.
2. Group the TCs by the target file from the strategy's **Proposed Test Layout**. Add to an existing file rather than creating a duplicate.
3. Write each test following `playwright-best-practices`:
   - The test function name starts with the TC id, as in `def test_tc_006_marking_a_subsection_covered_persists(...)`. Add `@pytest.mark.smoke` if the TC is in the Smoke suite. Layer markers are applied from the folder automatically.
   - Use the **primary layer** from the strategy. Put the supporting-layer assertion in the supporting layer's file, not in the same test.
   - Set preconditions through fixtures and the API, and use the UI only for the behavior under test.
   - Use role and label locators, and the accessible names from `far-notes-domain`.
   - Make the Expected Results the assertions, **word for word**: exact text, counts and status codes.
   - Wait for the specific response or state, never a fixed time. Control time with `page.clock` (`install`, `set_fixed_time`, `run_for`).
4. Reuse or extend shared code (`tests/conftest.py`, `tests/support`, `tests/pages`, `tests/mocks`) instead of copying it into tests.
5. Each **[Manual/Setup-heavy]** TC uses the hook named in the strategy, such as the DB reset-token fixture or a dedicated server process. If the hook doesn't exist, mark the test `@pytest.mark.skip(reason="FIXME: <missing hook>")`, and report it.
6. Don't add assertions the scenario doesn't call for, and don't weaken the ones it does.

### 2. Validate the tests (static review plus a live check with Playwright MCP)

Before running anything, confirm that each test is correct in principle.

**Static review**: go through this checklist for every new or changed test.

- [ ] It traces to exactly one TC, and every Expected Result is asserted.
- [ ] It is at the layer the strategy assigned. There are no network stubs in E2E and no real-server dependency in component tests.
- [ ] It has no `wait_for_timeout`, `time.sleep`, `networkidle`, focused runs left in (`-k` in `pytest.ini`), CSS or XPath chains (unless the best-practices table allows them), `expect` inside page objects, or UI-based setup.
- [ ] It creates its own user and data, and doesn't depend on test order.
- [ ] Time and time zone are fixed wherever "today" or timers are involved.
- [ ] `.venv/bin/pytest --collect-only -q` shows the test, which confirms it imports and is found.

**Live check with Playwright MCP**: for component and E2E tests, check the test's assumptions against the real page before trusting them.

- Use the Playwright MCP browser tools, such as `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_network_requests` and `browser_console_messages`. Tool names can vary by version, so check which tools are available.
- If the Playwright MCP server isn't connected, tell the user it can be added with `claude mcp add playwright -- npx @playwright/mcp@latest` (it is not configured in this project yet). Continue with the static review, and note in the report that the live check was skipped.
- Point the browser at the **test server**, `base_url` in `pytest.ini` (port 3100), which uses the test database. Sign in as a freshly registered test user.
- For each test:
  - Walk through its steps in the browser.
  - Use `browser_snapshot` (the accessibility tree) to confirm that every locator's role and accessible name exists and is unique. The filter buttons, for example, include their count in their name.
  - Confirm the expected text, counts and request bodies with `browser_network_requests`.
- Fix any locator or expectation that doesn't match **before** running the test. If the page contradicts the scenario, record it for step 5 rather than quietly changing the test.

### 3. Run the tests

Run the narrowest command that covers the scope, then widen it:

```bash
node --test tests/unit                               # unit (JavaScript helpers)
.venv/bin/pytest -m api                              # API
.venv/bin/pytest -m component                        # component
.venv/bin/pytest -m e2e                              # E2E
.venv/bin/pytest -k "tc_006 or tc_108"               # specific TCs
.venv/bin/pytest -m smoke                            # Smoke suite
.venv/bin/pytest tests/api/test_auth.py              # one file
```

- First run the new tests alone. When they pass, run the whole file, then the whole project, to catch interference between tests.
- Run each new test **3 times** (`for i in 1 2 3; do .venv/bin/pytest -k <tests> -q; done`, or `--count=3` if `pytest-repeat` is added) to catch flakiness before calling it done.
- Keep the actual output: pass and fail counts, error messages and trace paths. Never summarize a run you didn't see.

### 4. If a test fails, debug and fix

Find the cause before changing anything:

1. Read the error and the assertion diff. Rerun with `--tracing on` if needed, then open the trace with `.venv/bin/playwright show-trace test-results/<test>/trace.zip` and look at the DOM snapshot, the network (PATCH bodies, status codes) and the console.
2. Reproduce the failure with the Playwright MCP browser if the trace doesn't explain it. Check the test server's stdout for server errors.
3. Go through the **flaky test checklist** in `playwright-best-practices` › Debugging Tips:
   - a missing wait for the response
   - unfixed time or time zone
   - shared data
   - a 429 from the register limit
   - a locator that matches more than one element
4. Decide which kind of failure it is:
   - **Test defect**: a wrong locator, missing wait, bad setup, a stub that doesn't match the API, or a typo. Fix the test and go back to step 2 for that test.
   - **Environment problem**: the server didn't start, the port is in use, or a database or rate-limit leftover remains. Fix the setup, not the test.
   - **The test and the app disagree about behavior.** Go to step 5. Don't edit the assertion yet.
5. Allow at most **3 fix attempts** per test. If it still fails, stop and report it with the evidence, rather than looping or weakening the test.

Never do any of these to get a pass:
- loosen an assertion
- add `wait_for_timeout` or `time.sleep`
- raise timeouts
- add retries
- add `pytest.mark.skip` or `pytest.skip()` (except the documented FIXME case)
- switch to a CSS selector without a reason

### 5. Validate against the domain docs: test bug or application bug?

When the app's behavior differs from what the test expects, decide **which one is wrong**. The domain docs may have changed since the scenarios were written.

1. **Re-read the source of truth** for this rule:
   - `far-notes-domain` (`business-rules.md`, `api-reference.md`, `data-models.md`, `user-flows.md`)
   - the scenario's **Business Rule** field
   - the relevant code (`server.js`, `app.js`, the page scripts)
2. **Check whether anything changed recently.** Run `git log -p --since=<scenario file date> -- .claude/skills/far-notes-domain docs/test-scenarios.md server.js app.js` to see whether the rule, the scenario or the code changed after the test was written.
3. **Classify the failure:**

| Domain docs say | App does | Test expects | Verdict | Action |
|-----------------|----------|--------------|---------|--------|
| X | X | Y | **Test bug** (the test or scenario is out of date) | Fix the test. If the scenario text is wrong too, update `docs/test-scenarios.md` and say so |
| X | Y | X | **Application bug** | Keep the assertion. Mark it `@pytest.mark.xfail(strict=True, reason=...)` naming the TC, the rule and the observed behavior. Report it. Don't change app code without the user's approval |
| X (recently changed) | Y (old behavior) | X | **Application bug**: the requirement changed and the code hasn't caught up | As above, and point to the doc change |
| Silent or ambiguous | Y | X | **Unclear requirement** | Don't guess. Add it to Open Questions and ask the user whether Y is intended. Keep the test as `@pytest.mark.skip(reason="FIXME: awaiting decision")` until it's decided |
| X | Y | Y | **Test asserts the wrong behavior** (it locked in a bug) | Flag it. The test should assert X and be marked `xfail(strict=True)` |

4. Scenarios that are documented as asserting **current behavior** pass on today's behavior until the user decides otherwise. These are listed in the strategy's Open Questions, for example TC-207, TC-216, TC-220, TC-318, TC-411, TC-414, TC-415 and the TC-106 focus bug.
5. A doc change that affects **other** scenarios gets reported, so `/create-scenarios` and `/test-strategy` can be rerun.

## Output

At the end, report the following (and keep it short):

```markdown
## Test Generation Report: <scope>

**Files**: created or changed, each with the TC ids it covers
**Run**: <command> → <passed>/<failed>/<skipped>, repeated 3× (state if not)
**Live validation (Playwright MCP)**: done or skipped (with the reason)

| TC | Layer | Status | Notes |
|----|-------|--------|-------|
| TC-006 | E2E | ✅ Pass | |
| TC-106 | Component | ⚠️ xfail (app bug) | Heading input not focused after Add section; business-rules.md › Add section |
| TC-126 | API | ⏸ skip (FIXME) | DB reset-token fixture not built yet |

**Application bugs found**: each with the TC, the rule, expected versus actual, and the evidence (trace or response)
**Test bugs fixed**: what was wrong
**Doc or scenario updates**: what changed, and why
**Open questions**: decisions needed from the user
**Prerequisites still missing**: if any
```

## Rules

- Load `playwright-best-practices` before writing code, and follow it. If you deviate from it, say so in the report.
- One TC per test, with the TC id in the title. Never test a TC that isn't in `docs/test-scenarios.md`. Propose a new scenario instead.
- Never make a test pass by weakening it. Each failure is a test bug, an environment problem or an application bug, and the report says which.
- Never change application code, domain docs or scenario expectations without telling the user. Ask before changing application code.
- Never run tests against `data/part91.sqlite`, the `VMC43` account, or the dev server on port 3000.
- Report test results exactly as they were. If something wasn't run, say so.
