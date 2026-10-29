---
name: create-scenarios
description: Create test scenarios for the FAR Notes study log from a feature, user flow, business rule, bug, or code change. Produces numbered positive, negative and edge-case scenarios with preconditions, steps and expected results, ready to turn into Playwright tests. Use when asked to write, plan, list or review test scenarios, test cases or acceptance criteria for this app.
---

# Create Scenarios

## Role
Assume the role of a senior functional test desginer who can think like  a real user and a malicious user.


## Before writing

1. Load the `far-notes-domain` skill. From its sub-files table, read only what the target needs:
   - `business-rules.md` for the expected behavior
   - `user-flows.md` for the happy path you're starting from
   - `api-reference.md` for status codes, request bodies and API-level setup
   - `data-models.md` when a scenario checks stored data
2. If the target is a code change, read the diff or the changed code too.
3. Base expected results on the documented rules and the actual code, never on guesses. If the docs and the code disagree, write the scenario to match the code and flag the mismatch under **Open questions**.

## Direction
Turn a feature, flow, rule, bug or code change into concrete test scenarios for FAR Notes.
Apply all 6 lenses (happy path, business rules, security, negative/error, edge cases, UI state) to each flow. Write scenarios in the output format below. Number them by category and keep them independent so they can run in any order.

## Coverage checklist

For every feature/flow in the domain skill, apply ALL 6 lenses:

| Lens | Question |
|------|----------|
| Happy Path | What is the expected successful journey? |
| Business Rules | What domain rules must be validated? |
| Security | Can unauthorized users access or manipulate this? |
| Negative/Error | What happens with invalid inputs or wrong state? |
| Edge Cases | What are the boundary values and limits? |
| UI State | Are there conditional displays, loading states, empty states? |

## Output Format
Write to **`docs/test-scenarios.md`** (consumed by `/test-strategy` skill). Use this template:

```
### TC-<NNN>: <Title>
**Category**: <Happy Path | Business Rule | Security | Negative | Edge Case | UI State>
**Priority**: <P0 | P1 | P2 | P3>
**Preconditions**: <what must be true>
**Steps**: <numbered actions>
**Expected Results**: <what to verify>
**Business Rule**: <rule from domain skill>
**Suggested Layer**: <E2E | API | Component | Unit>
```

Numbering: TC-001-099 Happy Path, TC-100-199 Business Rules, TC-200-299 Security, TC-300-399 Negative, TC-400-499 Edge Cases, TC-500-599 UI State.

## Rules
- Be exhaustive — cover every flow in the domain skill
- Every scenario must trace back to a documented rule or discovered code behavior
- Don't just test happy paths — edge cases and negative paths find the most bugs


<!-- For each target, consider each of these and include the ones that apply: -->

<!-- - **Happy path**: the main flow succeeds.
- **Validation**: invalid input, such as passwords shorter than 15 characters, bad dates, a bad `part`, or duplicate usernames or emails.
- **Boundaries**: the exact limits, such as 15-character passwords, 64-character usernames, 1024-byte passwords and 16 KB bodies.
- **Persistence**: the change survives a reload, after waiting for the save request.
- **Isolation**: data stays separate between Part 61 and Part 91, and between two users.
- **Access control**: signed-out users, locked headings (403), another user's IDs (404) and origin mismatches (403).
- **Rate limits**: 429 responses. Remember that register allows only 5 attempts per 15 minutes per IP.
- **UI state**: counts, progress %, filters, search, the empty state and toasts stay in sync.
- **Keyboard**: Enter, Escape and the `/` shortcut, where relevant. -->

## Output format

<!-- Group scenarios by area. Number them with a prefix for the area plus a counter:

| Area | Prefix |
| --- | --- |
| Auth | `AUTH-` |
| Study items | `STUDY-` |
| Sections | `SEC-` |
| Search and filters | `SRCH-` |
| Parts | `PART-` |
| API | `API-` | -->

Write each scenario like this:

```markdown
### STUDY-03: Covered date clears when an item is unchecked
- **Type**: Positive | Negative | Edge
- **Priority**: P1 (core flow or data loss) | P2 (important) | P3 (minor)
- **Layer**: UI | API | UI+API
- **Preconditions**: Signed in as a fresh user; Part 91; 91.103(a) is covered with today's date
- **Steps**:
  1. Uncheck "Mark 91.103(a) as covered"
  2. Wait for PATCH /api/subsections/:id
  3. Reload the page
- **Expected**:
  - Label shows "No" and the date field is empty
  - Covered count drops by 1 and To go rises by 1
  - After reload, the item is still uncovered with no date
```

After the scenarios, add:

- **Coverage summary**: a short table with one row per area and columns for Positive, Negative and Edge counts.
- **Open questions**: unclear or suspicious behavior that needs a decision, such as a docs-versus-code mismatch or a likely bug.

## Rules

- Each scenario checks one behavior and can run on its own. Prefer a fresh account per scenario, created through the API to save time.
- Steps use the real UI labels and accessible names from `far-notes-domain`, such as "Mark 91.103(a) as covered" and "+ Add section".
- Expected results are specific and checkable: exact text, counts, status codes or field values. Avoid vague results like "works correctly".
- Mark scenarios that need the server console (password reset links) or a server restart (catalog backfill, clearing rate limits) as **Manual/Setup-heavy**.
- Don't write Playwright code unless asked. This skill produces scenarios.
