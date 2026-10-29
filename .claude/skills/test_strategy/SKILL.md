---
name: test-strategy
description: Build the test strategy for FAR Notes. Assign each scenario in docs/test-scenarios.md to the lowest test layer that can prove it (unit, API, component or E2E), flag anti-patterns, and write docs/test-strategy.md. Use after /create-scenarios, or when asked which tests to automate, at which layer, or in what order.
argument-hint: "[feature-name or blank for full analysis]"
---

# Test Strategy

## Task

Turn the scenarios in `docs/test-scenarios.md` into a **strategy**: a decision, for each scenario, about which test layer will automate it, with the reason why.

- **Scope**: `$ARGUMENTS`
  - If it is blank, analyze every scenario.
  - If it names a feature (for example `auth`, `study-items`, `sections`, `search`, `parts`, `password-reset`), analyze only the scenarios for that feature. Match on title, steps and the **Business Rule** field, and list the TC ids you included.
- If `docs/test-scenarios.md` doesn't exist, stop and tell the user to run `/create-scenarios` first.
- Assign one **primary layer** per scenario. Add a **supporting layer** only when a second layer catches something the first can't.
- The scenario's **Suggested Layer** is a starting point. Override it when the decision rules below say so, and record the override.

### Layers in this project

The app is plain JavaScript with no framework, no build step and no npm dependencies. The **test suite is Python**: pytest with pytest-playwright (`requirements-dev.txt`, `pytest.ini`, `tests/conftest.py`). The only exception is the Unit layer, because its code under test is JavaScript. Each layer maps to these tools:

| Layer | What it runs | Tooling | Speed and cost |
|-------|--------------|---------|----------------|
| **Unit** | One pure function, with no DOM, network or database | `node:test` + `node:assert` (built into Node 22). These are the only non-Python tests, because the functions under test are JavaScript | Milliseconds |
| **API** | Real HTTP calls to the running `server.js` with a real SQLite database | pytest + Playwright Python `APIRequestContext` (`request_context` / `api` fixtures) | Tens of milliseconds |
| **Component** | One page or widget in a real browser, with the network stubbed by `page.route()` so the server's data doesn't matter | pytest-playwright `page` + `page.route()` (`tests/mocks/routes.py`) | Hundreds of milliseconds |
| **E2E** | A real user journey through the browser, server and database | pytest-playwright `page`, with no network stubs | Seconds |

**Testability note**: the pure helpers are importable for unit tests. Server checks are in `lib/validation.js`, and tracker logic is in `app-core.js` (see CLAUDE.md). Unit tests must import these modules, **never `server.js`**, because it opens the database and starts listening as soon as it's loaded. Logic that is still inside `app.js` or `server.js` needs another extraction first. List each one under **Prerequisites**, and never choose a higher layer just to avoid it without saying so.

## Decision Rules

Apply these in order. The first rule that matches decides the primary layer.

1. **Pure logic → Unit.** The result depends only on the inputs: date validation (`isIsoDate`), local-date formatting (`localDate`), eCFR URL building (`ecfrUrl`), section-number parsing, search matching (`matchingSubsections`), progress rounding, and password or username rules. Boundary values and many input variations belong here, as table-driven tests.
2. **Server contract → API.** Status codes, error messages, validation, auth gates (401 and 302), cross-origin 403, locked-heading 403, other users' ids (404), rate limits (429), body limits (413), extra fields in requests, the static file allowlist, and cookie attributes. If a scenario can be proved without rendering a page, it belongs at the API layer.
3. **Data isolation and persistence → API first.** Prove "user B can't see or change user A's data" and "a value round-trips" with API calls. Add one E2E check only when the UI could still show stale or wrong data even though the API is correct.
4. **UI reaction to a given response → Component.** Rendering, counts and progress in sync, filters and search display, empty states, toasts, error states (stub a 500), loading states (stub a delay), disabled buttons, focus, keyboard shortcuts, accessible names, and late responses arriving out of order (`loadSequence`). Stub the network so the test checks the UI logic, not the server.
5. **Several parts working together → E2E.** Use E2E only when the scenario's value is the integration: a happy-path journey, an autosave debounce that then persists after a reload, the session cookie being used across pages, redirects between pages, or the Escape revert surviving a reload. **Aim for no more than about 15% of automated scenarios at E2E.**
6. **Needs the console, a restart, a database edit or a long wait → Manual, or Automate with a hook.** This covers scenarios tagged **[Manual/Setup-heavy]**. Either keep them manual, or name the test hook that would make them automatable, such as capturing server stdout in a global setup, a test-only setting for the rate limits, or a fixture that edits the database. Put each hook under **Prerequisites**.
7. **Security scenarios get at least API coverage**, even if the risk shows up in the browser. Script-injection scenarios also need one Component or E2E check that the injected text never runs.
8. **Tiebreaker**: choose the lower layer. Escalate only when a lower layer can't observe the behavior.

### Priority and run order

- **Smoke** (runs on every change): all P0 scenarios, plus one E2E happy path for each core flow.
- **Regression**: everything P1 and P2.
- **Extended**: P3 scenarios, plus manual and hooked scenarios.

## Anti-Patterns to Flag

Report each of these that you find. Name the TC ids involved and say how to fix it.

- **Ice-cream cone**: more E2E than API and unit tests together, or E2E above about 15%.
- **E2E for validation**: testing error messages or limits through the browser when an API call proves the same thing.
- **Duplicate coverage**: the same rule asserted at several layers without a new risk at each one.
- **Testing through the UI to set up data**: creating accounts, sections or covered items by clicking when the API can do it. Setup should use API calls, and the UI should be used only for the behavior under test.
- **Shared mutable state**: scenarios that depend on another test's data, the `VMC43` account, or the order tests run in.
- **Rate-limit collisions**: per-test sign-ups that will hit the register limit (5 per IP per 15 minutes). Flag them and propose seeded users or a test-only setting.
- **Hard waits**: `page.wait_for_timeout()` or `time.sleep()` used instead of waiting for the specific `PATCH` or `GET` response. The 350 ms debounce invites this.
- **Network stubs in E2E**: an E2E test that stubs the API is really a component test, so label it that way.
- **Real servers in component tests**: a component test that depends on database state is really an E2E test.
- **Testing implementation details**: asserting CSS classes or internal variables when visible text, roles or accessible names would prove the same thing. The `is-active` filter class is an acceptable exception, because it's the only signal.
- **Untestable unit candidates**: pure logic stuck inside `app.js` or `server.js`. Propose extracting it instead of testing it at a higher layer.
- **Flaky time dependence**: "today" assertions without a fixed clock or time zone.
- **Scenario gaps**: a business rule in `business-rules.md` that no scenario covers, or a scenario whose **Business Rule** field doesn't trace back to a documented rule or to code.

## Output

Write the strategy to **`docs/test-strategy.md`**, replacing any earlier version. For a feature-scoped run, write `docs/test-strategy-<feature-name>.md` instead. Use this structure:

```markdown
# Test Strategy: <Full analysis | feature-name>

Source: docs/test-scenarios.md (<n> scenarios in scope) · Generated <YYYY-MM-DD>

## Summary
| Layer     | Scenarios | % | P0 | P1 | P2 | P3 |
|-----------|----------:|--:|---:|---:|---:|---:|
| Unit      | | | | | | |
| API       | | | | | | |
| Component | | | | | | |
| E2E       | | | | | | |
| Manual    | | | | | | |

The pyramid shape in one sentence, and whether it meets the ≤15% E2E target.

## Layer Assignments
| TC | Title | Priority | Suggested → Primary | Supporting | Rule # | Rationale |
|----|-------|----------|---------------------|------------|--------|-----------|
| TC-001 | Create an account through the UI | P0 | E2E → E2E | API | 5 | Signup journey integration; API covers validation |

## Suites
- **Smoke**: TC ids
- **Regression**: TC ids
- **Extended / Manual**: TC ids, each with the hook that would automate it

## Prerequisites
Refactors, fixtures and test hooks needed before the tests can be written, such as extracting pure helpers, a fresh-user fixture that creates users through the API, a seeded-user setup for the rate limit, stdout capture for reset links, and a fixed clock and time zone.

## Anti-Patterns Found
- **<anti-pattern>**: TC ids and the fix.

## Proposed Test Layout
tests/unit/<module>.test.js, tests/api/test_<area>.py, tests/component/test_<page>_<area>.py, tests/e2e/test_<journey>.py, mapping each file to the TC ids it covers.

## Open Questions
Decisions the user needs to make before implementing.
```

## Rules

- Every scenario in scope appears exactly once in **Layer Assignments**. None may be dropped silently. If a scenario shouldn't be automated, assign it to Manual and say why.
- Every assignment names the decision rule number that produced it. Any change from the **Suggested Layer** is shown as `Suggested → Primary`.
- Base decisions on what the code can actually observe at each layer. Read the relevant code when unsure, for example whether a function is pure, or whether the UI or only the server enforces a rule.
- Keep scenario ids, titles and priorities exactly as they appear in `docs/test-scenarios.md`. Don't renumber or rewrite scenarios. If a scenario is wrong, raise it under Open Questions.
- Count by unique scenario and make the percentages add up to 100%.
- Don't write test code. This skill produces the strategy, and implementing it is a separate step.
- Carry the Open questions from `docs/test-scenarios.md` forward when they affect a layer decision.

## Knowledge Sources

Read only what the task needs:

| Source | Use it for |
|--------|------------|
| `docs/test-scenarios.md` | **The required input.** Scenario ids, categories, priorities, suggested layers and Manual tags |
| `far-notes-domain` skill (`SKILL.md`) | Tech stack, architecture, and the frontend and backend structure |
| `far-notes-domain/business-rules.md` | Checking that scenarios trace to rules, and finding coverage gaps |
| `far-notes-domain/api-reference.md` | Deciding whether a scenario can be proved at the API layer |
| `far-notes-domain/data-models.md` | Persistence and isolation checks, and database fixtures |
| `far-notes-domain/user-flows.md` | Choosing the few journeys that deserve E2E |
| `create-scenarios` skill | The scenario template and TC numbering this skill uses |
| `server.js`, `app.js`, page scripts | Checking whether logic is pure or extractable, and where each rule is enforced |
| `package.json` | Current scripts and dependencies. No test runner is installed yet. |
