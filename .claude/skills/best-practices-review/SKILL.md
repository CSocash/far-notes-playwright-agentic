---
name: best-practices-review
description: Review how well FAR Notes follows best practices in test automation, quality assurance, ISTQB, security, pytest and Python, and track progress over time. Measures the project as it is now, checks each practice and known gap against the code, compares with the previous review, and writes a new dated report to docs/best-practices/. Use when asked for a best-practices review, an adherence check, a QA health check, or what has improved since the last review.
argument-hint: "[blank for a full review, or one area: automation | qa | istqb | security | pytest | python]"
---

# Best Practices Review

## Task

Write a **new, dated review** of the project's best practices, and show what changed since the previous one, so adherence can be tracked over time.

- **Scope:** `$ARGUMENTS`. Blank means every area. An area name limits sections 1 to 8 to that area; the measurements, the scorecard and the comparison are always included.
- **Output:** `docs/best-practices/<YYYY-MM-DD>_best-practices-review.md`, using today's date. If that file already exists, add a suffix (`_2`, `_3`) rather than overwriting it.
- **Earlier reviews are records.** Never edit or delete them. The newest earlier file in `docs/best-practices/` (by the date in its name) is the **baseline** to compare against.

## Step 1: Measure

Run these, and keep the exact output. Every number in the report must come from a command run during this review.

```bash
git log -1 --format='%h %ad' --date=short                     # the commit being reviewed
.venv/bin/pytest -q                                            # full suite: passed / failed / skipped / xfailed
.venv/bin/pytest --collect-only -q | tail -1                   # total collected (device tests are deselected)
for m in api component e2e smoke mobile; do echo "$m $(.venv/bin/pytest -m $m --collect-only -q | grep -c '::')"; done
.venv/bin/pytest --run-device -m device --collect-only -q | grep -c '::'   # device tests (collect only)
ls tests/unit 2>/dev/null; node --test tests/unit 2>&1 | tail -3          # unit tests, if any exist
grep -rn "xfail\|mark.skip\|pytest.skip" tests | grep -v __pycache__      # known bugs and skipped tests
```

Scenario coverage, by priority and by category:

```bash
python3 - <<'EOF'
import re, glob, collections
txt = open("docs/test-scenarios.md").read()
pri = dict(re.findall(r"### (TC-\d{3}):.*?\n\*\*Category\*\*:.*?\n\*\*Priority\*\*: (P\d)", txt))
cat = dict(re.findall(r"### (TC-\d{3}):.*?\n\*\*Category\*\*: (.+)", txt))
auto = set()
for f in glob.glob("tests/**/*.py", recursive=True):
    auto |= {"TC-" + n for n in re.findall(r"def test_tc_(\d{3})", open(f).read())}
print(f"scenarios {len(pri)}, automated {len(auto & pri.keys())}, tests without a scenario: {sorted(auto - pri.keys())}")
for group in (pri, cat):
    total, done = collections.Counter(group.values()), collections.Counter(group[t] for t in auto if t in group)
    for key in sorted(total): print(f"  {key}: {done[key]}/{total[key]}")
EOF
```

Run the device test only if the user asks, or if Appium and the iPhone 17 Simulator are available. Otherwise report it as **not run**.

**Never** run anything against `data/part91.sqlite`, the `VMC43` account, or the dev server on port 3000.

## Step 2: Check each practice against the code

Go through the **Practice checklist** below. For each item, decide on one status, and give the evidence (a file and line, a command's output, or a config value):

- ✅ **In place**: done, and the evidence shows it working.
- ⚠️ **Partial / needs improvement**: present but incomplete, inconsistent, or out of date.
- ❌ **Missing**: not done.
- ➖ **Not applicable** at this stage. Say why, for example "local single-user app".

Check the baseline's "not addressed" and "needs improving" items one by one too: each is now fixed, partly fixed or still open. Look for **new** gaps as well, not only the ones already listed.

### Practice checklist

**Test automation**
- One primary layer per scenario; E2E at or below 15% of automated scenarios (`docs/test-strategy.md`).
- Isolation: a fresh user and client per test, a fresh database per run, test server on port 3100, rate limit off only in the test server (`tests/conftest.py`).
- No fixed waits in tests: `grep -rn "wait_for_timeout\|time.sleep\|networkidle" tests`. Every hit must be a documented polling loop.
- Time and time zone fixed wherever "today" matters.
- Role and label locators; every CSS selector or XPath has a stated reason (`tests/pages/`).
- Page objects contain no `expect`; setup goes through the API.
- Component tests stub the network; E2E tests never do: `grep -rn "page.route" tests/e2e`.
- Trace, screenshot and video kept on failure (`pytest.ini`).
- Reporting: Allure configured; whether history is kept.
- Mobile: emulation tests, API tests of the app protocol, device tests; whether Android is covered.
- New tests repeated 3 times; control assertions present.

**Quality assurance and ISTQB**
- Scenarios with TC id, category, priority, steps, expected results and business rule; all P0 scenarios automated.
- Traceability: every `test_tc_*` id exists in `docs/test-scenarios.md`, and the strategy's test layout matches the real files.
- Known bugs tracked (GitHub Issues and `xfail(strict=True)` tests).
- The docs match reality: compare `docs/test-strategy.md` (Open Questions, Prerequisites), `CLAUDE.md`, `README.md`, the `playwright-best-practices` skill and the latest `progress_reports/` file against the code.
- CI runs the tests on pull requests (`.github/workflows/`); `main` is protected; recent merges went through pull requests (`git log --merges --oneline -10`).
- Test techniques visible in the scenarios: equivalence partitioning, boundary values, decision tables, state transitions, error guessing.
- Entry and exit criteria, completion reports, exploratory testing charters.

**Security** (OWASP Top 10, ASVS, NIST SP 800-63B)
- Access control scoped by `user_id`; another user's ids return 404; locked headings return 403.
- scrypt with a per-user salt; tokens hashed with SHA-256; `timingSafeEqual`; a dummy scrypt for unknown users.
- Prepared statements only: no SQL built from strings in `server.js`. User text written with `textContent`; every `innerHTML` uses fixed text only.
- Rate limits; body limit; origin check; CORS allowlist without credentials; bearer token only from app origins.
- Cookie flags: HttpOnly, SameSite=Strict, and `Secure` when hosted.
- Response headers: `grep -n "Content-Security-Policy\|X-Frame-Options\|frame-ancestors\|Referrer-Policy\|Strict-Transport-Security\|X-Content-Type-Options" server.js`.
- Where the mobile app stores its token (`api-client.js`).
- Dependency and code scanning (pip-audit, npm audit in `mobile/`, CodeQL, Dependabot).
- No secrets or personal data committed: the commit email is the noreply address (`git log -20 --format=%ae | sort -u`).

**pytest and Python**
- Fixtures with `yield` cleanup and deliberate scopes; shared fixtures in `conftest.py` files.
- Markers registered; `--strict-markers` in `addopts`.
- `parametrize` with readable ids; custom options deselect rather than skip.
- Warnings in the last run, and where they come from.
- Pinned dependencies in `requirements-dev.txt`; a virtual environment.
- Linting, formatting and type checking (Ruff, mypy or pyright; a `pyproject.toml`).
- `subprocess` with a list of arguments, never `shell=True`: `grep -rn "shell=True" tests`.

## Step 3: Write the report

Use this structure. Keep the baseline's section numbers and headings, so two reviews can be compared side by side.

```markdown
# Best Practices Review: <YYYY-MM-DD>

Reviewed <date> against `main` at `<commit>`. Baseline: `<previous file name>` (or "none, first review").

## Summary
Three to five sentences: overall health, the biggest improvement since the baseline, and the biggest remaining risk.

## Measurements
| Measure | Baseline | Now | Change |
(scenarios, automated scenarios by priority, tests per layer, unit tests, smoke, warnings, last run result, run time)

## Scorecard
| Area | Practice | Baseline | Now | Evidence |
(one row per checklist item; statuses ✅ ⚠️ ❌ ➖; "new" in the Baseline column for items not checked before)

Counts: ✅ n · ⚠️ n · ❌ n · ➖ n, with the baseline's counts next to them.

## Changes since the baseline
- **Improved:** each item, with its commit or file
- **Got worse:** each item, with evidence
- **Still open:** each item, and how long it has been open (since which review)
- **New gaps found:** each item

## 1. Test automation practices … ## 6. Python practices
The practices in use, with where each is applied and its source.

## 7. Best practices not yet addressed
## 8. Practices in place that need improving
## 9. Suggested order of work
## References
```

If the baseline has no scorecard (the first review, `2026-11-03`, doesn't), work out its statuses from its sections 7 and 8: items listed there are ❌ or ⚠️, and practices described in sections 1 to 6 are ✅. Say in the report that the baseline statuses were derived this way.

## Rules

- **Read-only.** Don't change application code, tests, configuration or other docs during a review. List what needs changing; the user decides.
- **Report results exactly as they were.** Give the real counts and any failures. If something wasn't run, say so.
- **Every claim needs evidence** from this review: a command's output, or a file and line. Don't carry a status forward from the baseline without checking it again.
- **Check every TC id and file path you cite** against the code before writing it: `grep -rn "def test_tc_<id>" tests`.
- Cite outside sources by name and edition (ISTQB CTFL syllabus, OWASP Top 10 / ASVS / Cheat Sheets, NIST SP 800-63B, WCAG, Playwright, pytest and Python docs). Say they're cited from general knowledge unless you fetched them in this review.
- Write in plain, direct language. Explain any term a tester new to the project might not know.
- Don't commit the report. Tell the user its path and offer to commit it on a branch.
