# Test Strategy: Full analysis

Source: docs/test-scenarios.md (159 scenarios in scope) · Generated 2026-10-27 · TC-519 and TC-520 added 2026-10-28

## Summary

| Layer     | Scenarios | % | P0 | P1 | P2 | P3 |
|-----------|----------:|--:|---:|---:|---:|---:|
| Unit      | 24 | 14.1% | 0 | 4 | 12 | 8 |
| API       | 76 | 44.7% | 18 | 23 | 18 | 17 |
| Component | 57 | 33.5% | 2 | 14 | 24 | 17 |
| E2E       | 12 | 7.1% | 3 | 9 | 0 | 0 |
| Manual    | 1 | 0.6% | 0 | 0 | 0 | 1 |
| **Total** | **170** | **100%** | **23** | **50** | **54** | **43** |

The result is a proper pyramid: 100 unit and API tests form the base, 57 component tests sit in the middle, and 12 E2E journeys sit on top. E2E is 7.1% of the 169 automated scenarios, which **meets the ≤15% target**. The scenario file suggested E2E for 103 scenarios (65%); this strategy moves 91 of them down a layer.

Supporting checks add 2 Unit, 9 API, 2 Component. These are extra assertions inside existing tests at another layer, not separate scenarios.

## Layer Assignments

| TC | Title | Priority | Suggested → Primary | Supporting | Rule # | Rationale |
|----|-------|----------|---------------------|------------|--------|-----------|
| TC-001 | Create an account through the UI | P0 | E2E → E2E | API | 5 | The full sign-up journey across two pages. Validation errors are covered at the API layer (TC-124, TC-303) |
| TC-002 | Sign in with a username | P0 | E2E → E2E | – | 5 | Login → cookie → redirect → tracker render needs every part working together |
| TC-003 | Sign in with an email address | P1 | **E2E → API** | – | 2 | Email-as-identifier is server logic. The UI path is already proved by TC-002 |
| TC-004 | A fresh account sees the full Part 91 starter list at 0% | P1 | **E2E → API** | – | 3 | Seeded counts (61 sections and 247 items) can be read straight from GET. Count display is covered by TC-503 |
| TC-005 | Switch to Part 61 and see its starter list | P1 | **E2E → Component** | API | 4 | Part switch rendering with stubbed Part 61 data. API checks the 30/208 seed |
| TC-006 | Marking a subsection covered persists | P1 | E2E → E2E | – | 5 | Core study loop: UI change → PATCH → reload shows saved state |
| TC-007 | Adding a note persists | P1 | E2E → E2E | – | 5 | The debounced or blur autosave actually persisting is the integration risk |
| TC-008 | Editing the covered date by hand persists | P2 | **E2E → Component** | – | 4 | Assert the PATCH body from the date handler. Date persistence is proved by TC-019 |
| TC-009 | Unchecking Covered clears the date | P1 | **E2E → Component** | – | 4 | Assert the handler clears the date and sends covered:false. Persistence is proved by TC-019 |
| TC-010 | Add a custom section and save its heading | P1 | E2E → E2E | – | 5 | Add section → Edit → heading saved → reload covers POST and PATCH end to end |
| TC-011 | Edit a custom heading with the Edit button | P1 | **E2E → Component** | – | 4 | Enter-to-save sends the right PATCH. Persistence is proved by TC-010 |
| TC-012 | Search by section number | P1 | **E2E → Component** | Unit | 4 | Search display with stubbed data. Unit covers the matching logic |
| TC-013 | The To study and Covered filters | P1 | **E2E → Component** | – | 4 | Filter rendering and counts against a stubbed response |
| TC-014 | Reset a forgotten password end to end [Manual/Setup-heavy] | P1 | E2E → E2E | – | 6 | Hook: a DB fixture inserts a reset token with a known raw value, which replaces reading the server console |
| TC-015 | Log out | P0 | E2E → E2E | – | 5 | Logout → redirect → session gone needs the browser, cookie and server together |
| TC-016 | The section heading opens the eCFR section in a new tab | P2 | **E2E → Unit** | Component | 1 | ecfrUrl is pure. Component checks target=_blank and rel on the rendered link |
| TC-017 | The subsection reference links to the eCFR paragraph | P2 | **E2E → Unit** | – | 1 | Paragraph anchor built by the pure ecfrUrl |
| TC-018 | The session survives a reload and a new tab | P1 | E2E → E2E | – | 5 | Cookie reused across reload and a new page in the same context |
| TC-019 | Full API round trip | P1 | API → API | – | 2 | Already an API contract scenario |
| TC-020 | The app signs in with a bearer token | P1 | API → API | – | 2 | Login body and bearer auth are server contract; no app build needed |
| TC-021 | In app mode the pages use the bearer token and bundled links | P1 | Component → Component | – | 4 | `api-client.js` app mode, proved by injecting `FAR_NOTES_CONFIG` and stubbing the API. Native shells need device tests later |
| TC-100 | Progress counts study items, not sections | P1 | **E2E → Unit** | – | 1 | Counting by subsection is a pure summary calculation once extracted |
| TC-101 | Checking Covered replaces a hand-entered date with today | P2 | **E2E → Component** | – | 4 | Change handler overwrites the date. Needs a fixed clock |
| TC-102 | Locked starter headings have no Edit button | P1 | **E2E → Component** | – | 4 | Edit button hidden when isLocked:true in the stubbed data |
| TC-103 | Patching a locked heading returns 403 | P0 | API → API | – | 2 | Server-enforced 403 |
| TC-104 | Subsections of locked sections can still be edited | P1 | **E2E → API** | – | 2 | PATCH to a subsection under a locked section returns 200 and round-trips |
| TC-105 | Sections and subsections can't be deleted | P2 | API → API | – | 2 | DELETE returns 404. The UI has no control to test |
| TC-106 | Add section resets the filter and search (heading input is not focused) | P2 | **E2E → Component** | – | 4 | Filter and search reset, plus focus state (see the focus bug in Open Questions) |
| TC-107 | A new section has one "Entire section" item | P2 | **E2E → API** | – | 2 | POST response shape (one subsection with code "") |
| TC-108 | Escape reverts a heading edit and saves the original | P1 | E2E → E2E | – | 5 | Escape revert must survive a reload: regression test for the app.js fix |
| TC-109 | Escape on a brand-new section reverts it to empty | P2 | **E2E → Component** | – | 4 | Escape on an empty new heading sends PATCH with "". Persistence is covered by TC-108 |
| TC-110 | Blur saves the heading | P2 | **E2E → Component** | – | 4 | Blur triggers an immediate PATCH |
| TC-111 | The catalog fills in subsections on restart [Manual/Setup-heavy] | P3 | **E2E → Manual** | – | 6 | Needs a server restart mid-test. Low value (P3) |
| TC-112 | Sections without lettered paragraphs show one item | P2 | **E2E → Component** | – | 4 | Rendering of a code:"" item (reference = section number, title = Entire section) |
| TC-113 | A heading match shows every item in that section | P2 | **E2E → Unit** | – | 1 | matchingSubsections: a heading match returns every item |
| TC-114 | Search matches note text | P1 | **E2E → Unit** | – | 1 | matchingSubsections matches notes |
| TC-115 | Search matches a subsection title only | P2 | **E2E → Unit** | – | 1 | matchingSubsections matches titles only |
| TC-116 | Search is case-insensitive | P2 | **E2E → Unit** | – | 1 | Case-insensitive matching |
| TC-117 | A section header shows only when one of its items is visible | P2 | **E2E → Component** | – | 4 | Header visibility is render logic |
| TC-118 | Progress is tracked separately for each part | P0 | **E2E → API** | – | 3 | Isolation between parts is proved by GET counts per part |
| TC-119 | Switching parts resets the search and filter | P2 | **E2E → Component** | – | 4 | Part change resets UI state |
| TC-120 | Subsection titles come from the catalog | P3 | **E2E → API** | – | 2 | Compare GET titles with regulation-subsections.json |
| TC-121 | Notes autosave after a pause without leaving the field | P1 | **E2E → Component** | – | 4 | Use page.clock to prove one PATCH fires after 350 ms (no hard wait) |
| TC-122 | Covered and date changes save immediately | P2 | **E2E → Component** | – | 4 | PATCH is sent immediately on change |
| TC-123 | Registering does not sign the user in | P1 | **E2E → API** | – | 2 | No Set-Cookie on register, and GET / returns 302 |
| TC-124 | Username and email uniqueness ignores case | P1 | API → API | – | 2 | 409 from the server |
| TC-125 | Sign-in ignores the case of the username or email | P2 | API → API | – | 2 | NOCASE lookup |
| TC-126 | A password reset signs the user out everywhere [Manual/Setup-heavy] | P0 | **E2E → API** | – | 6 | Hook: DB-seeded reset token, then check two sessions both get 401. Promoted from manual because it's P0 |
| TC-127 | A new reset request cancels the previous link [Manual/Setup-heavy] | P1 | API → API | – | 6 | Hook: seed token T1, call forgot-password (which deletes earlier tokens), then T1 returns 400 |
| TC-128 | A reset link works only once [Manual/Setup-heavy] | P1 | API → API | – | 6 | Hook: DB-seeded token reused |
| TC-129 | The session cookie lasts 7 days | P2 | API → API | – | 2 | Set-Cookie attributes |
| TC-130 | Forgot password gives the same response for unknown emails | P1 | **E2E → API** | – | 2 | Identical response body for known and unknown emails |
| TC-131 | Every account gets its own copy of the starter lists | P0 | **E2E → API** | – | 3 | Isolation between users is proved through the API with two users |
| TC-132 | Spaces around the username are trimmed when registering | P3 | API → API | – | 2 | Server trims the username |
| TC-200 | A signed-out visit to the tracker redirects to login | P0 | API → API | – | 2 | 302 redirects without following them |
| TC-201 | Signed-out API calls are rejected | P0 | API → API | – | 2 | 401 gate |
| TC-202 | A signed-in user is sent away from the login and sign-up pages | P2 | **E2E → API** | – | 2 | 302 to / for a signed-in GET /login |
| TC-203 | Another user's subsection can't be changed | P0 | API → API | – | 2 | Cross-user subsection id returns 404 |
| TC-204 | Another user's section heading can't be changed | P0 | API → API | – | 2 | Cross-user regulation id returns 404 |
| TC-205 | Using the other part's id in a request returns 404 | P1 | API → API | – | 2 | Cross-part id returns 404 |
| TC-206 | Cross-origin writes are blocked | P0 | API → API | – | 2 | Origin header check on 8 endpoints, parameterized |
| TC-207 | Writes with no Origin header are accepted (current behavior) | P2 | API → API | – | 2 | Documents current behavior (Open Question) |
| TC-208 | Page scripts can't read the session cookie | P0 | **E2E → API** | – | 7 | Assert the HttpOnly and SameSite attributes; browser enforcement of HttpOnly is trusted |
| TC-209 | A session token stops working after logout | P0 | API → API | – | 2 | Replay of a logged-out token |
| TC-210 | A forged session cookie is rejected | P0 | API → API | – | 2 | Forged token |
| TC-211 | HTML in a heading is shown as text (stored XSS) | P0 | **E2E → Component** | API | 4+7 | Render a stubbed payload and assert it doesn't run. API proves it's stored verbatim |
| TC-212 | HTML in notes is shown as text (stored XSS) | P0 | **E2E → Component** | API | 4+7 | Same as TC-211, for notes and search results |
| TC-213 | SQL injection in the login identifier fails | P0 | API → API | – | 2 | Parameterized query |
| TC-214 | SQL-like text in a heading is stored as-is | P1 | API → API | – | 2 | Stored verbatim |
| TC-215 | Login errors don't reveal whether an account exists | P1 | API → API | – | 2 | Same message for unknown user and wrong password. Timing is checked loosely, as a non-blocking soft assertion |
| TC-216 | Registration reveals whether a username or email is taken (current behavior) | P3 | API → API | – | 2 | Documents current behavior |
| TC-217 | Login is rate-limited [Manual/Setup-heavy] | P1 | API → API | – | 6 | Hook: a dedicated server process (fresh in-memory limits, own DB and port) |
| TC-218 | Registration is rate-limited [Manual/Setup-heavy] | P1 | API → API | – | 6 | Hook: dedicated server process |
| TC-219 | Forgot password is rate-limited [Manual/Setup-heavy] | P2 | API → API | – | 6 | Hook: dedicated server process |
| TC-220 | Reset password is not rate-limited (current behavior) | P3 | API → API | – | 2 | Documents current behavior |
| TC-221 | Only allowlisted files are served | P0 | API → API | – | 2 | Allowlist plus path traversal, parameterized |
| TC-222 | Extra fields can't unlock or move a section | P0 | API → API | – | 2 | Extra fields ignored on regulations |
| TC-223 | Extra fields on a subsection are ignored | P1 | API → API | – | 2 | Extra fields ignored on subsections |
| TC-224 | /api/auth/me doesn't expose secrets | P1 | API → API | – | 2 | Response key set |
| TC-225 | An expired session counts as signed out [Manual/Setup-heavy] | P1 | **E2E → API** | – | 6 | Hook: DB fixture sets expires_at in the past, then GET / returns 302 |
| TC-226 | Non-GET requests to pages are rejected | P3 | API → API | – | 2 | 405 for non-GET page requests |
| TC-227 | A website login never returns the session token | P0 | API → API | – | 7 | Response body and Set-Cookie contract |
| TC-228 | Requests from an app origin ignore the session cookie | P0 | API → API | – | 7 | Guards the CSRF boundary that the app origins open |
| TC-229 | CORS is granted only to the app origins | P0 | API → API | – | 7 | Preflight and CORS headers are server contract |
| TC-230 | The app can write with a bearer token; other origins still can't | P1 | API → API | – | 7 | Origin check still applies with a bearer token |
| TC-231 | Logging out with a bearer token revokes it | P1 | API → API | – | 3 | Session row deleted, proved by a 401 |
| TC-232 | Malformed or unknown bearer tokens are rejected | P1 | API → API | – | 7 | Token parsing contract |
| TC-233 | api-client.js loads while signed out | P1 | API → API | – | 2 | Static allowlist and publicPaths |
| TC-300 | Login with a wrong password | P1 | **E2E → Component** | API | 4 | Stub a 401: error text plus password focus. API covers the message (TC-215) |
| TC-301 | Login with an unknown user | P2 | **E2E → API** | – | 2 | Same assertion as TC-215; fold it into the same parameterized test |
| TC-302 | Empty login fields block submission | P3 | **E2E → Component** | – | 4 | Required attribute blocks the request |
| TC-303 | Registering a duplicate username through the UI | P1 | **E2E → Component** | API | 4 | Stub a 409: error prefix shown and form stays visible. API covers the 409 (TC-124) |
| TC-304 | Registering a duplicate email through the UI | P1 | **E2E → API** | – | 2 | Duplicate email returns 409. The UI rendering is identical to TC-303 |
| TC-305 | Invalid username characters | P2 | **E2E → Unit** | – | 1 | Username regex, once extracted |
| TC-306 | An invalid email is rejected by the API | P2 | **API → Unit** | – | 1 | Email regex, once extracted |
| TC-307 | A 14-character password is rejected | P1 | **API → Unit** | API | 1 | Password minimum. API asserts one 400 message end to end |
| TC-308 | Mismatched passwords on the reset page | P2 | **E2E → Component** | – | 4 | Client-side check, no request sent |
| TC-309 | The reset page with no token | P2 | **E2E → Component** | – | 4 | Missing hash leads to the error message shown |
| TC-310 | A malformed or unknown reset token | P2 | API → API | – | 2 | Token format and unknown token |
| TC-311 | A short new password on reset | P2 | API → API | – | 2 | Validation order: token format, then password length |
| TC-312 | An invalid part value | P2 | API → API | – | 2 | 400 for a bad part |
| TC-313 | Covered must be a boolean | P2 | API → API | – | 2 | Type validation |
| TC-314 | Invalid date formats are rejected | P2 | **API → Unit** | API | 1 | isIsoDate table. API asserts one 400 message |
| TC-315 | Notes must be a string | P3 | API → API | – | 2 | Type validation |
| TC-316 | A subsection PATCH with no fields | P3 | API → API | – | 2 | Empty-update validation |
| TC-317 | Malformed JSON | P2 | API → API | – | 2 | readJson error path |
| TC-318 | A JSON `null` body (current behavior) | P3 | API → API | – | 2 | Documents current behavior (Open Question) |
| TC-319 | The heading must be text | P3 | API → API | – | 2 | Type validation |
| TC-320 | Ids that don't exist | P3 | API → API | – | 2 | 404 for unknown ids |
| TC-321 | An unknown API route | P3 | API → API | – | 2 | API fallthrough |
| TC-322 | A failed subsection save shows a toast | P1 | **E2E → Component** | – | 4 | Already uses a network stub, so it is a component test |
| TC-323 | A failed heading save shows a toast | P2 | **E2E → Component** | – | 4 | Network stub |
| TC-324 | A failed Add section shows a toast | P2 | **E2E → Component** | – | 4 | Network stub |
| TC-325 | Regulations fail to load | P1 | **E2E → Component** | – | 4 | Network stub |
| TC-326 | The session ends while the tracker is open | P1 | **E2E → Component** | API | 4 | Stub a PATCH 401 and check the redirect. API covers a dead token (TC-209) |
| TC-327 | Logout fails | P3 | **E2E → Component** | – | 4 | Network stub |
| TC-400 | A password of exactly 15 characters | P1 | **API → Unit** | – | 1 | Boundary for the password minimum |
| TC-401 | Password length counts characters, not code units | P2 | **E2E → Unit** | Component | 1 | Code-point counting. Component shows the browser's minlength lets 14 emoji through and the server error appears |
| TC-402 | The password byte limit | P2 | **API → Unit** | – | 1 | Byte limit |
| TC-403 | Username length limits | P2 | **API → Unit** | – | 1 | Username length |
| TC-404 | Allowed username punctuation | P3 | **API → Unit** | – | 1 | Username charset |
| TC-405 | Email length limit | P3 | **API → Unit** | – | 1 | Email length |
| TC-406 | Passwords are not trimmed | P2 | API → API | – | 2 | Exact-match login hashing |
| TC-407 | Request body size limit | P2 | API → API | – | 2 | 413 body limit |
| TC-408 | Unicode and multi-line notes keep their exact text | P2 | **E2E → API** | – | 3 | Unicode round trip |
| TC-409 | A section with an empty heading | P3 | **E2E → Component** | – | 4 | Render of an empty heading |
| TC-410 | A heading with no section number | P2 | **E2E → Component** | Unit | 4 | Render with no href. Unit covers section-number parsing |
| TC-411 | A Part 91 section number used in the Part 61 list | P3 | **E2E → Unit** | – | 1 | ecfrUrl with the active part (current behavior) |
| TC-412 | Leading spaces before the section number | P3 | **E2E → Unit** | – | 1 | Section-number regex |
| TC-413 | Leap-day dates | P3 | **API → Unit** | – | 1 | isIsoDate leap day |
| TC-414 | A future covered date is accepted (current behavior) | P3 | **E2E → API** | – | 2 | Server accepts future dates (current behavior) |
| TC-415 | A date on an uncovered item (current behavior) | P3 | **E2E → API** | – | 2 | Date stored without covered (current behavior) |
| TC-416 | Clearing a date with an empty string | P3 | API → API | – | 2 | Empty date accepted |
| TC-417 | The covered date follows the browser's time zone | P2 | **E2E → Unit** | – | 1 | localDate under TZ=Pacific/Kiritimati with a fixed Date |
| TC-418 | Progress percentage rounding | P3 | **E2E → Unit** | – | 1 | Rounding in the summary calculation |
| TC-419 | Rapid note edits save the last value | P1 | E2E → E2E | – | 5 | Serialized save queue against the real server |
| TC-420 | Rapid covered toggling ends in a consistent state | P1 | E2E → E2E | – | 5 | Final server state must match the UI after rapid toggles |
| TC-421 | Rapid part switching shows the last part chosen | P2 | **E2E → Component** | – | 4 | Delay one stub to prove loadSequence drops the late response |
| TC-422 | Two tabs editing the same note (last write wins) | P2 | **E2E → API** | – | 3 | Last write wins is a server property |
| TC-423 | Logging out of one browser keeps other sessions | P2 | **E2E → API** | – | 3 | Logout deletes only that session |
| TC-424 | Custom sections appear in the order they were created | P3 | **E2E → API** | – | 2 | ORDER BY id |
| TC-425 | A search of only spaces shows everything | P3 | **E2E → Unit** | – | 1 | Query trim |
| TC-426 | Special characters in search are matched literally | P3 | **E2E → Unit** | – | 1 | Literal includes, not regex |
| TC-427 | The login identifier is trimmed | P3 | **E2E → API** | – | 2 | Server trims the identifier |
| TC-428 | Escape after a debounced autosave still restores the original | P1 | E2E → E2E | – | 5 | Ordering of a debounced PATCH and the Escape PATCH against the real server |
| TC-429 | Duplicate section numbers are allowed | P3 | **E2E → API** | – | 2 | No uniqueness on headings |
| TC-430 | Unchecking an item while the Covered filter is on | P2 | **E2E → Component** | – | 4 | Re-render under the Covered filter |
| TC-500 | Connection status while loading | P3 | **E2E → Component** | – | 4 | Delay the stub to see the loading text |
| TC-501 | Header and title for Part 91 | P3 | **E2E → Component** | – | 4 | Header and title |
| TC-502 | Header, title and intro text change with the part | P3 | **E2E → Component** | – | 4 | Part text changes |
| TC-503 | Summary stats and filter counts stay in sync | P1 | **E2E → Component** | – | 4 | Counts in sync |
| TC-504 | The results count follows the search and filter | P2 | **E2E → Component** | – | 4 | Results count |
| TC-505 | The empty state when nothing matches | P2 | **E2E → Component** | – | 4 | Empty state |
| TC-506 | Escape clears the search box | P3 | **E2E → Component** | – | 4 | Keyboard |
| TC-507 | The `/` shortcut focuses search only outside text fields | P3 | **E2E → Component** | – | 4 | Keyboard |
| TC-508 | The active filter button is highlighted | P3 | **E2E → Component** | – | 4 | is-active class (an accepted exception) |
| TC-509 | Clicking Edit swaps the link for an input | P2 | **E2E → Component** | – | 4 | Edit toggle and focus |
| TC-510 | The toast hides itself | P3 | **E2E → Component** | – | 4 | Use page.clock for the 2.4 s auto-hide |
| TC-511 | Login page focus and the error state | P3 | **E2E → Component** | – | 4 | Focus and error state |
| TC-512 | Create-account success state | P2 | **E2E → Component** | – | 4 | Stub a 201 |
| TC-513 | Forgot-password success state | P3 | **E2E → Component** | – | 4 | Stub a 200 |
| TC-514 | Reset-password success state [Manual/Setup-heavy] | P3 | **E2E → Component** | – | 4 | Stub a 200, so no console or manual step is needed |
| TC-515 | Submit buttons are disabled while a request is in flight | P3 | **E2E → Component** | – | 4 | Delay the stub and check the disabled state |
| TC-516 | The progress bar width matches the percentage | P3 | **E2E → Component** | – | 4 | Stubbed 25-of-247 dataset |
| TC-517 | The progress caption before data loads | P3 | **E2E → Component** | – | 4 | Read the caption before the delayed stub resolves |
| TC-518 | Accessible names on controls and links | P2 | **E2E → Component** | – | 4 | Role and name queries on stubbed render |
| TC-519 | Saving or cancelling a heading edit hides the input | P2 | Component → Component | – | 4 | Pure UI reaction to Enter/Escape; stub the PATCH |
| TC-520 | The Edit button's accessible name follows the saved heading | P2 | Component → Component | – | 4 | Accessible-name check on stubbed render |
| TC-521 | Touch screens get 16px text fields, so iOS doesn't zoom | P2 | Component → Component | – | 4 | Computed font sizes under iPhone emulation; the zoom itself needs a real device |
| TC-522 | Desktop keeps the compact field sizes | P3 | Component → Component | – | 4 | Control for TC-521: the touch rule leaves desktop alone |

Rows in **bold** override the scenario's Suggested Layer.

## Suites

- **Smoke** (25, runs on every change): every P0, plus one E2E happy path per core flow (sign-in TC-002, study TC-006, sections TC-010, logout TC-015). The P0 E2E sign-up journey TC-001 is included automatically.
  TC-001, TC-002, TC-006, TC-010, TC-015, TC-103, TC-118, TC-126, TC-131, TC-200, TC-201, TC-203, TC-204, TC-206, TC-208, TC-209, TC-210, TC-211, TC-212, TC-213, TC-221, TC-222, TC-227, TC-228, TC-229
- **Regression** (95): all P1 and P2 scenarios not already in Smoke and not depending on a hook.
  TC-003, TC-004, TC-005, TC-007, TC-008, TC-009, TC-011, TC-012, TC-013, TC-016, TC-017, TC-018, TC-019, TC-020, TC-021, TC-100, TC-101, TC-102, TC-104, TC-105, TC-106, TC-107, TC-108, TC-109, TC-110, TC-112, TC-113, TC-114, TC-115, TC-116, TC-117, TC-119, TC-121, TC-122, TC-123, TC-124, TC-125, TC-129, TC-130, TC-202, TC-205, TC-207, TC-214, TC-215, TC-223, TC-224, TC-230, TC-231, TC-232, TC-233, TC-300, TC-301, TC-303, TC-304, TC-305, TC-306, TC-307, TC-308, TC-309, TC-310, TC-311, TC-312, TC-313, TC-314, TC-317, TC-322, TC-323, TC-324, TC-325, TC-326, TC-400, TC-401, TC-402, TC-403, TC-406, TC-407, TC-408, TC-410, TC-417, TC-419, TC-420, TC-421, TC-422, TC-423, TC-428, TC-430, TC-503, TC-504, TC-505, TC-509, TC-512, TC-518, TC-519, TC-520, TC-521
- **Extended / Manual** (50): P3 scenarios, plus scenarios that need a hook. The hooked P0 TC-126 also runs in Smoke once its hook exists.
  TC-014, TC-111, TC-120, TC-127, TC-128, TC-132, TC-216, TC-217, TC-218, TC-219, TC-220, TC-225, TC-226, TC-302, TC-315, TC-316, TC-318, TC-319, TC-320, TC-321, TC-327, TC-404, TC-405, TC-409, TC-411, TC-412, TC-413, TC-414, TC-415, TC-416, TC-418, TC-424, TC-425, TC-426, TC-427, TC-429, TC-500, TC-501, TC-502, TC-506, TC-507, TC-508, TC-510, TC-511, TC-513, TC-514, TC-515, TC-516, TC-517, TC-522
  - Hooks:
    - **DB reset-token fixture**: TC-014, TC-126, TC-127, TC-128.
    - **DB session-expiry fixture**: TC-225.
    - **Dedicated server process**: TC-217, TC-218, TC-219.
    - **Manual only**: TC-111 needs a server restart in the middle of the test. It could be automated with the dedicated-server hook if it becomes important.

## Prerequisites

Do these in order. The first three blocked **all** automated tests and are now **done** (2026-10-27). The test suite is **Python**: pytest with pytest-playwright.

1. ✅ **Isolate the test database.** `server.js` reads `FAR_NOTES_DB`, which defaults to `data/part91.sqlite`. The test server uses `.test-data/far-notes-test.sqlite`, which is gitignored. `PORT` was already configurable.
2. ✅ **Deal with the register rate limit.** Option (a) was chosen: `FAR_NOTES_DISABLE_RATE_LIMIT=1`. Almost every scenario needs a fresh user, and `register` allows only 5 per IP per 15 minutes. Choose one:
   - (a) A test-only setting, such as an environment variable that raises or turns off `consumeRateLimit` and is never set in normal use. **This is recommended.**
   - (b) A user-seeding fixture that inserts users straight into the test database using the same scrypt parameters (16-byte hex salt, 64-byte key) and runs `createStarterRegulationsForUser`. That function lives inside `server.js`, so this option also needs prerequisite 4.

   The rate-limit tests (TC-217 to TC-219) always use their own dedicated server process without the override.
3. ✅ **Install and configure the Python test stack.**
   - `.venv` plus `requirements-dev.txt`, which pins `pytest`, `pytest-playwright` and `playwright` 1.64.1. Install with `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt && .venv/bin/playwright install chromium`.
   - `pytest.ini` sets `base_url` to `http://127.0.0.1:3100`, Chromium, traces, screenshots and video on failure, and the `smoke`, `api`, `component` and `e2e` markers.
   - `tests/conftest.py` has a session fixture that starts `node server.js` with the test database and the rate-limit override (it reuses a server that's already running on that port). It also auto-marks each test with its layer from its folder.
   - Unit tests are the one exception: the code under test is JavaScript, so they stay on `node --test tests/unit` (decided; see Open Questions 6).
4. ✅ **Make server logic importable.** Done in `lib/validation.js`: `isIsoDate`, `checkUsername`, `checkEmail` and `checkPassword` (character minimum, byte maximum). Each check returns the exact client error message or `null`, and `server.js` calls them in the same order as before. The planned `require.main` guard was **not** added: `server.js` opens the database and runs migrations as soon as it's loaded, so unit tests must import `lib/validation.js`, never `server.js`.
5. ✅ **Make client logic importable.** Done in `app-core.js`: `sectionNumber`, `ecfrUrl`, `referenceFor`, `normalizeQuery`, `matchingSubsections(regulation, query, filter)` (the filter is now a parameter instead of the global `activeFilter`), `summarize` (totals and the rounded progress) and `localDate(now = new Date())`.
   - It's a classic script that sets `window.FarNotesCore`, or `module.exports` under Node.
   - `index.html` loads it before `app.js`.
   - `/app-core.js` is in `serveStatic` and in `TRACKER_PATHS`, so it needs sign-in like `app.js`.
   - Checked against the old code with 12,006 differential comparisons, the pytest suite and a browser check.
6. **Fixtures.**
   - ✅ `fresh_user`: registers through the API (`tests/support/users.py`).
   - ✅ `api`: a Playwright `APIRequestContext` signed in as `fresh_user`.
   - ✅ `request_context`: a fresh, signed-out `APIRequestContext` per test.
   - ✅ Dedicated server process for rate-limit tests (`tests/support/server.py`).
   - ✅ `test_db` (`tests/support/db.py`): seeds reset tokens with Python's `sqlite3`. The raw token is generated by the test and its SHA-256 is inserted. Expiring sessions (TC-225) is still to add.
   - ✅ `signed_in_page`: a browser page signed in through the API.
   - ✅ `other_user`: a second signed-in user for isolation tests.
7. ✅ **Component harness** (built 2026-10-28: `serve_tracker_from_disk`, `mock_signed_in`, `mock_regulations` and the `tests/mocks/data.py` builders). Serve the real `index.html`, `app.js`, `app-core.js` and `styles.css` from disk with `page.route()` (`tests/mocks/routes.py`; already done for the auth pages) (the `/` document included, so the server's auth redirect is bypassed), and stub `/api/auth/me` and `/api/regulations*` with small JSON fixtures:
   - 91.103 with (a) and (b)
   - 91.5 as an Entire section
   - one unlocked custom section
   - a 247-item generator for count tests

   Auth pages are served the same way, with their `/api/auth/*` calls stubbed.
8. **Time control.** Use `page.clock` and `timezone_id` (set in `browser_context_args` in conftest) for anything about today, the debounce or the toast (TC-006, TC-101, TC-121, TC-417, TC-420, TC-510). For unit tests, set `TZ` per test process and pass a fixed `Date` into `localDate`.
9. **Wait helpers.** Use `page.expect_response(...)` matching `PATCH /api/subsections/:id` or `/api/regulations/:id` before every reload, never `page.wait_for_timeout()` or `time.sleep()`.

## Anti-Patterns Found

- **Ice-cream cone in the suggested layers**: the scenario file suggests E2E for 103 of 157 scenarios (66%). This strategy keeps 12 at E2E (7.7% of automated scenarios). Fix: use the Layer Assignments above, not the Suggested Layer field.
- **Network stubs in E2E**: TC-322, TC-323, TC-324, TC-325, TC-327, TC-421, TC-500, TC-515 and TC-517 are labeled E2E but rely on `page.route()` stubs or delays. Fix: they are relabeled Component.
- **E2E for validation**: TC-300 to TC-305, TC-401, TC-130 and TC-202 check server messages or redirects through the browser. Fix: they move to API or Unit, and only the UI rendering of one representative error stays at Component (TC-300, TC-303).
- **Duplicate coverage**:
  - TC-301 and TC-215 assert the same login message. Fix: one parameterized API test.
  - TC-208 and TC-129 both assert Set-Cookie attributes. Fix: one test.
  - TC-303 and TC-304, and TC-124, all assert 409. Fix: one Component render plus one parameterized API test.
  - TC-307 and TC-400 cover the same password boundary. Fix: one table-driven unit test.
- **Testing through the UI to set up data**: preconditions such as "91.103(a) is covered" (TC-009, TC-013, TC-101, TC-114, TC-117, TC-430, TC-503) and "a custom section exists" (TC-011, TC-108, TC-110, TC-428) must be created through the API in the `freshUser` fixture, not by clicking. Only TC-001 and TC-010 create data through the UI, because that is what they test.
- **Shared mutable state**:
  - All tests currently share `data/part91.sqlite` and the in-memory rate-limit map with each other and with the real `VMC43` account. Fix: prerequisites 1 and 2.
  - TC-217 to TC-219 consume the per-IP budget for every other test. Fix: dedicated server process.
- **Rate-limit collisions**: the 116 scenarios whose preconditions need a fresh or registered user will hit 429 after the 5th registration. This is a blocker. Fix: prerequisite 2.
- **Hard waits**: TC-121 ("wait about 1 second"), TC-428 ("wait 1 second"), TC-510 (2.4 s) and TC-500, TC-421 and TC-515 (1 s delays). Fix: `page.clock` for timers, and `page.expect_request`/`page.expect_response` for saves. Delayed stubs are fine, but assertions must wait on state rather than time.
- **Testing implementation details**:
  - TC-516 asserts `style.width`. This is acceptable because the bar has no text, but prefer `aria-valuenow` if a progressbar role is added.
  - TC-510 asserts the `is-visible` class. Prefer checking toast visibility.
  - TC-508's `is-active` is an accepted exception.
- **Untestable unit candidates**: `isIsoDate` and the inline username, email and password checks in `server.js`, and `ecfrUrl`, `matchingSubsections` (it reads the global `activeFilter`), `updateSummary` (it mixes calculation and DOM writes) and `localDate` in `app.js`. Fix: prerequisites 4 and 5. The 24 unit-layer scenarios depend on this.
- **Flaky time dependence**: TC-006, TC-009, TC-101, TC-417 and TC-420 assert "today". Fix: a fixed clock and time zone.
- **Scenario gaps**: rules in `business-rules.md` and `data-models.md` with no scenario:
  - **Reset links expire after 30 minutes.** Add an API scenario that seeds a token with a past `expires_at` (DB fixture).
  - **Subsection titles are rewritten from the catalog on every startup.** TC-120 only checks equality. Add a dedicated-server scenario that edits a title in the database, restarts the server, and checks the title is restored.
  - **Legacy section-level progress is copied into subsections on migration.** Add a dedicated-server scenario starting from a pre-subsection database (P3).
  - **The 16 KB limit on auth endpoints.** TC-407 covers only subsections; add a parameterized row.
- **Untraceable scenarios**: none. Every scenario's Business Rule field points to a domain doc or to specific code.

## Proposed Test Layout

```
tests/unit/app-core.test.js                      TC-016, TC-017, TC-100, TC-113, TC-114, TC-115, TC-116, TC-411, TC-412, TC-417, TC-418, TC-425, TC-426
tests/unit/validation.test.js                    TC-305, TC-306, TC-307, TC-314, TC-400, TC-401, TC-402, TC-403, TC-404, TC-405, TC-413
tests/api/test_access_control.py                 TC-200, TC-201, TC-202, TC-203, TC-204, TC-205, TC-209, TC-210, TC-222, TC-223, TC-225, TC-423
tests/api/test_auth.py                           TC-003, TC-123, TC-124, TC-125, TC-129, TC-130, TC-132, TC-208, TC-215, TC-216, TC-224, TC-301, TC-304, TC-406, TC-427
tests/api/test_mobile_clients.py                 TC-020, TC-227, TC-228, TC-229, TC-230, TC-231, TC-232, TC-233
tests/api/test_origin.py                         TC-206, TC-207
tests/api/test_password_reset.py                 TC-126, TC-127, TC-128, TC-220, TC-310, TC-311
tests/api/test_rate_limits.py                    TC-217, TC-218, TC-219
tests/api/test_regulations.py                    TC-004, TC-019, TC-103, TC-104, TC-105, TC-107, TC-118, TC-120, TC-131, TC-312, TC-319, TC-320, TC-424, TC-429
tests/api/test_robustness.py                     TC-213, TC-214, TC-221, TC-226, TC-317, TC-318, TC-321, TC-407
tests/api/test_subsections.py                    TC-313, TC-315, TC-316, TC-408, TC-414, TC-415, TC-416, TC-422
tests/component/test_app_mode.py                 TC-021
tests/component/test_auth_pages.py               TC-300, TC-302, TC-303, TC-308, TC-309, TC-511, TC-512, TC-513, TC-514, TC-515
tests/component/test_tracker_errors.py           TC-322, TC-323, TC-324, TC-325, TC-326, TC-327
tests/component/test_tracker_parts.py            TC-005, TC-119, TC-421, TC-502
tests/component/test_tracker_search_filter.py    TC-012, TC-013, TC-117, TC-430, TC-504, TC-505, TC-506, TC-507, TC-508
tests/component/test_tracker_sections.py         TC-011, TC-102, TC-106, TC-109, TC-110, TC-112, TC-409, TC-410, TC-509, TC-519, TC-520
tests/component/test_tracker_security.py         TC-211, TC-212
tests/component/test_tracker_state.py            TC-500, TC-501, TC-503, TC-510, TC-516, TC-517, TC-518
tests/component/test_touch_layout.py             TC-521, TC-522
tests/component/test_tracker_study_items.py      TC-008, TC-009, TC-101, TC-121, TC-122
tests/e2e/test_password_reset.py                 TC-014
tests/e2e/test_sections.py                       TC-010, TC-108, TC-428
tests/e2e/test_signup_signin.py                  TC-001, TC-002, TC-015, TC-018
tests/e2e/test_study_items.py                    TC-006, TC-007, TC-419, TC-420
manual-checklist.md (docs/)                      TC-111
tests/conftest.py, tests/support/, tests/pages/, tests/mocks/   fixtures (fresh_user, api, request_context, db), server control, page objects, route stubs
```

Unit tests run with `node --test` and need no browser. API, component and E2E tests are pytest + pytest-playwright modules that share `tests/conftest.py`, and their layer marker is applied from the folder. Mark Smoke tests `@pytest.mark.smoke`.

## Open Questions

1. **Test database location.** Do you approve adding `FAR_NOTES_DB` (or a similar name) so tests never touch `data/part91.sqlite`? Nothing can be automated safely without it.
2. **Rate-limit override.** Should it be (a) a test-only environment variable in `server.js` (recommended) or (b) seeding users directly in the database? Option (a) changes production code but keeps the test setup simple.
3. **Refactoring for unit tests.** Prerequisites 4 and 5 change `server.js`, `app.js` and `index.html` (a new `app-core.js`). Should they be done, or should those 24 unit scenarios move up to API or Component? That would make the test suite slower and the failures harder to trace.
4. **Lock in current behavior or the desired behavior?** These scenarios assert today's behavior, which the scenario file flagged as questionable:
   - TC-207: requests with no Origin are accepted
   - TC-216: registration reveals existing accounts
   - TC-220: reset-password has no rate limit
   - TC-318: raw error text for a null body
   - TC-411: wrong-part eCFR link
   - TC-414: future dates accepted
   - TC-415: date on an uncovered item

   If any is a bug to fix, its test should assert the fixed behavior and be marked `@pytest.mark.xfail(strict=True, reason=...)` until the fix lands.
5. **Add-section focus bug** (carried from the scenario file). TC-106 asserts that the heading input does **not** get focus, which contradicts the domain docs. Fix the code first, so TC-106 asserts that it does get focus, or keep it as a documented known issue?
6. **Test language: decided (2026-10-27).** API, component and E2E tests are Python (pytest + pytest-playwright). Unit tests for the extracted JavaScript helpers stay on Node's built-in runner (`node --test tests/unit`). These are the only non-Python tests, and the 24 unit-layer scenarios keep their Unit assignment.
7. **Browsers.** Chromium only to start? WebKit and Firefox could be added later for the component and E2E projects.
