# FAR Notes Test Scenarios

Generated with the `create-scenarios` skill from the `far-notes-domain` skill (`business-rules.md`, `user-flows.md`, `api-reference.md`, `data-models.md`) and checked against `server.js`, `app.js` and the auth page scripts. When the docs and the code disagreed, scenarios follow the code and the mismatch is listed under **Open questions**.

## Conventions

- **Fresh user**: a new account with a unique username and email (for example `pilot_<random>` / `pilot_<random>@test.com`) and a 15+ character password, created through `POST /api/auth/register`, then signed in through `POST /api/auth/login`. Its session is applied to the browser context. Each fresh user starts with untouched starter lists.
- **Starter list sizes for a fresh user**:
  - Part 91: 61 sections and **247** study items. `91.5`, `91.11`, `91.15` and `91.125` each have a single "Entire section" item.
  - Part 61: 30 sections and **208** study items.
- **Reference items**:
  - `91.103 — Preflight action` (locked) has `91.103(a)` and `91.103(b)`.
  - `91.5 — Pilot in command of aircraft requiring a type rating` (locked) has the single item `91.5` / "Entire section".
- **API calls** in Steps are made with the fresh user's session cookie and no `Origin` header unless the step says otherwise.
- **[Manual/Setup-heavy]** marks scenarios that need the server console (password reset links), a server restart (catalog backfill, clearing rate limits), direct database edits, or a long wait.
- **Rate-limit caution**: `register` allows only 5 attempts per IP per 15 minutes, counting successful ones. A suite that creates a fresh user per test needs a plan for this (see Open questions).
- **Priorities**:
  - **P0**: security or data isolation, or data loss
  - **P1**: core study flow
  - **P2**: important supporting behavior
  - **P3**: minor or cosmetic

---

## Happy Path (TC-001 – TC-099)

### TC-001: Create an account through the UI
**Category**: Happy Path
**Priority**: P0
**Preconditions**: Signed out. Username and email are not in use.
**Steps**:
1. Open `/login` and click "Create an account".
2. Fill in Username, Email address and Password (15+ characters).
3. Click "Create account".

**Expected Results**:
- The form is hidden.
- "Account created successfully. Return to the login page to sign in." is visible, and "Return to the login page" links to `/login`.
- `POST /api/auth/register` returns 201 `{ accountCreated: true }`.

**Business Rule**: user-flows.md › Flow #1; api-reference.md › register
**Suggested Layer**: E2E

### TC-002: Sign in with a username
**Category**: Happy Path
**Priority**: P0
**Preconditions**: A registered account. Signed out.
**Steps**:
1. Open `/login`.
2. Enter the username in "Username or email" and the password in "Password".
3. Click "Sign in".

**Expected Results**:
- The page redirects to `/`.
- `#current-user` shows the username.
- The brand shows "PART 91".
- The status shows "Connected to SQLite".

**Business Rule**: business-rules.md › Accounts: sign-in accepts username or email
**Suggested Layer**: E2E

### TC-003: Sign in with an email address
**Category**: Happy Path
**Priority**: P1
**Preconditions**: A registered account. Signed out.
**Steps**:
1. On `/login`, enter the account's **email** in "Username or email" and enter the password.
2. Click "Sign in".

**Expected Results**:
- The page redirects to `/`.
- `#current-user` shows the **username**, not the email.

**Business Rule**: business-rules.md › Accounts: sign-in accepts username or email
**Suggested Layer**: E2E

### TC-004: A fresh account sees the full Part 91 starter list at 0%
**Category**: Happy Path
**Priority**: P1
**Preconditions**: A fresh user, signed in.
**Steps**:
1. Open `/`.

**Expected Results**:
- `#total-count` = 247, `#covered-count` = 0, `#remaining-count` = 247, and `#progress-percent` = "0%".
- `#results-count` = "Showing 247 of 247 study items".
- The first section row is "91.1 — Applicability".
- There are 61 `.section-row` elements.

**Business Rule**: business-rules.md › Progress counted by study item; Accounts: each account has its own starter lists
**Suggested Layer**: E2E

### TC-005: Switch to Part 61 and see its starter list
**Category**: Happy Path
**Priority**: P1
**Preconditions**: A fresh user, signed in, on `/`.
**Steps**:
1. Select "Part 61" in `#part-select`.

**Expected Results**:
- `GET /api/regulations?part=61` returns 200.
- 30 section rows are shown, and the first is "61.3 — Requirement for certificates, ratings, and authorizations".
- `#total-count` = 208.

**Business Rule**: user-flows.md › Flow #3
**Suggested Layer**: E2E

### TC-006: Marking a subsection covered persists
**Category**: Happy Path
**Priority**: P1
**Preconditions**: A fresh user, signed in, on Part 91.
**Steps**:
1. Check "Mark 91.103(a) as covered".
2. Wait for `PATCH /api/subsections/:id?part=91` to return 200.
3. Reload the page.

**Expected Results**:
- Before the reload:
  - The label shows "Yes".
  - "Date covered for 91.103(a)" shows today's local date.
  - Covered = 1 and To go = 246.
- After the reload, the same values are shown.

**Business Rule**: business-rules.md › Checking Covered sets the date to today
**Suggested Layer**: E2E

### TC-007: Adding a note persists
**Category**: Happy Path
**Priority**: P1
**Preconditions**: A fresh user, signed in, on Part 91.
**Steps**:
1. Type "Check NOTAMs and weather" in "Notes for 91.103(a)".
2. Click outside the field.
3. Wait for the PATCH request to return 200, then reload.

**Expected Results**: After the reload, the note reads exactly "Check NOTAMs and weather".
**Business Rule**: business-rules.md › Notes autosave
**Suggested Layer**: E2E

### TC-008: Editing the covered date by hand persists
**Category**: Happy Path
**Priority**: P2
**Preconditions**: A fresh user. 91.103(a) is covered.
**Steps**:
1. Set "Date covered for 91.103(a)" to 2026-01-15.
2. Wait for the PATCH request, then reload.

**Expected Results**:
- The PATCH body contains `"date":"2026-01-15"`.
- After the reload, the date shows 2026-01-15 and the item is still covered.

**Business Rule**: business-rules.md › Date can also be edited by hand
**Suggested Layer**: E2E

### TC-009: Unchecking Covered clears the date
**Category**: Happy Path
**Priority**: P1
**Preconditions**: A fresh user. 91.103(a) is covered with a date.
**Steps**:
1. Uncheck "Mark 91.103(a) as covered".
2. Wait for the PATCH request, then reload.

**Expected Results**:
- The label shows "No" and the date is empty.
- Covered goes down by 1 and To go goes up by 1.
- These values persist after the reload.

**Business Rule**: business-rules.md › Unchecking clears the date
**Suggested Layer**: E2E

### TC-010: Add a custom section and save its heading
**Category**: Happy Path
**Priority**: P1
**Preconditions**: A fresh user, on Part 91.
**Steps**:
1. Click "+ Add section".
2. Click the new section's "Edit" button, type "91.999 — My custom topic" and press Enter.
3. Reload the page.

**Expected Results**:
- `POST /api/regulations?part=91` returns 201.
- The toast reads "New section added. Enter a regulation number to get started."
- The last section heading is "91.999 — My custom topic". It links to `https://www.ecfr.gov/current/title-14/part-91/section-91.999#section-91.999` and has an "Edit" button.
- The heading persists after the reload.
- Total = 248.

**Business Rule**: business-rules.md › Add section
**Suggested Layer**: E2E

### TC-011: Edit a custom heading with the Edit button
**Category**: Happy Path
**Priority**: P1
**Preconditions**: A fresh user with a custom section "91.999 — Old".
**Steps**:
1. Click "Edit section heading 91.999 — Old".
2. Replace the text with "91.998 — New" and press Enter.
3. Reload the page.

**Expected Results**:
- The heading link reads "91.998 — New" and points to `section-91.998`.
- It persists after the reload.

**Business Rule**: business-rules.md › Enter or blur saves the heading
**Suggested Layer**: E2E

### TC-012: Search by section number
**Category**: Happy Path
**Priority**: P1
**Preconditions**: A fresh user, on Part 91.
**Steps**:
1. Type "91.103" in "Search regulations or notes".

**Expected Results**:
- Only the "91.103 — Preflight action" section is shown, with items 91.103(a) and 91.103(b).
- `#results-count` = "Showing 2 of 247 study items".

**Business Rule**: business-rules.md › Search
**Suggested Layer**: E2E

### TC-013: The To study and Covered filters
**Category**: Happy Path
**Priority**: P1
**Preconditions**: A fresh user. 91.103(a) and 91.103(b) are covered.
**Steps**:
1. Click "Covered".
2. Click "To study".

**Expected Results**:
- With Covered: only 91.103(a) and 91.103(b) show under one section header, and the button count = 2.
- With To study: 245 items show, and neither 91.103 item is among them.

**Business Rule**: business-rules.md › Filters
**Suggested Layer**: E2E

### TC-014: Reset a forgotten password end to end [Manual/Setup-heavy]
**Category**: Happy Path
**Priority**: P1
**Preconditions**: A registered account. You can read the server console.
**Steps**:
1. On `/login`, click "Forgot password?".
2. Enter the email and click "Request reset link".
3. Copy the `/reset-password#token=…` link from the console and open it.
4. Enter a new 15+ character password in both fields and click "Set new password".
5. Sign in with the new password.

**Expected Results**:
- After step 2: "If an account matches that address, a reset link is available in the local server terminal."
- After step 4: "Password updated. You can now sign in with your new password."
- Step 5 succeeds.

**Business Rule**: user-flows.md › Flow #6
**Suggested Layer**: E2E

### TC-015: Log out
**Category**: Happy Path
**Priority**: P0
**Preconditions**: A fresh user, signed in, on `/`.
**Steps**:
1. Click "Log out".

**Expected Results**:
- `POST /api/auth/logout` returns 200 `{ loggedOut: true }`.
- The page redirects to `/login`.
- `GET /api/auth/me` returns `{ authenticated: false }`.

**Business Rule**: user-flows.md › Flow #7
**Suggested Layer**: E2E

### TC-016: The section heading opens the eCFR section in a new tab
**Category**: Happy Path
**Priority**: P2
**Preconditions**: A fresh user, on Part 91.
**Steps**:
1. Inspect the "Open 91.103 — Preflight action in the eCFR in a new tab" link.

**Expected Results**:
- `href` = `https://www.ecfr.gov/current/title-14/part-91/section-91.103#section-91.103`.
- `target="_blank"` and `rel="noopener noreferrer"`.

**Business Rule**: business-rules.md › eCFR links
**Suggested Layer**: E2E

### TC-017: The subsection reference links to the eCFR paragraph
**Category**: Happy Path
**Priority**: P2
**Preconditions**: A fresh user. Part 61 is selected.
**Steps**:
1. Inspect the link "Open 61.3(a) in the eCFR in a new tab".

**Expected Results**:
- `href` = `https://www.ecfr.gov/current/title-14/part-61/section-61.3#p-61.3(a)`.
- It opens in a new tab.

**Business Rule**: business-rules.md › eCFR links
**Suggested Layer**: E2E

### TC-018: The session survives a reload and a new tab
**Category**: Happy Path
**Priority**: P1
**Preconditions**: A fresh user, signed in.
**Steps**:
1. Reload `/`.
2. Open `/` in a second page of the same context.

**Expected Results**: Both pages load the tracker without redirecting to `/login`.
**Business Rule**: business-rules.md › Sessions last 7 days
**Suggested Layer**: E2E

### TC-019: Full API round trip
**Category**: Happy Path
**Priority**: P1
**Preconditions**: The server is running.
**Steps**:
1. Register through the API.
2. Log in through the API.
3. `GET /api/regulations?part=91`.
4. `POST /api/regulations?part=91` with `{}`.
5. `PATCH` the new section with `{ "regulation": "91.999 — API topic" }`.
6. `PATCH` its subsection with `{ "covered": true, "date": "2026-10-01", "notes": "n" }`.

**Expected Results**:
- The calls return 201, 200 (with `Set-Cookie: study_session=…`), 200 with 61 sections, 201, 200 and 200 in that order.
- The final subsection is `{ code: "", title: "Entire section", covered: true, date: "2026-10-01", notes: "n" }`.

**Business Rule**: api-reference.md
**Suggested Layer**: API

### TC-020: The app signs in with a bearer token
**Category**: Happy Path
**Priority**: P1
**Preconditions**: A fresh user. A request context with no cookies.
**Steps**:
1. `POST /api/auth/login` with header `X-Far-Notes-Client: app`.
2. `GET /api/regulations?part=91` from a context with no cookies, with `Origin: capacitor://localhost` and `Authorization: Bearer <token>`.

**Expected Results**:
- Step 1 returns 200 with exactly the keys `username` and `token`, and `token` is 64 lowercase hex characters.
- Step 2 returns 200 with 61 sections and `Access-Control-Allow-Origin: capacitor://localhost`.

**Business Rule**: api-reference.md › Mobile app clients
**Suggested Layer**: API

### TC-021: In app mode the pages use the bearer token and bundled links
**Category**: Happy Path
**Priority**: P1
**Preconditions**: The login page with `window.FAR_NOTES_CONFIG` set (as `mobile/www/config.js` does). The API is stubbed.
**Steps**:
1. Open the login page.
2. Sign in.
3. Let the tracker load.

**Expected Results**:
- "Create an account" links to `create-account.html`, not `/create-account`.
- The login request carries `X-Far-Notes-Client: app`.
- After sign-in the app opens `index.html`, and its `/api/auth/me` request carries `Authorization: Bearer <the token from the login response>`.

**Business Rule**: SKILL.md › Architecture: api-client.js app mode
**Suggested Layer**: Component

---

## Business Rules (TC-100 – TC-199)

### TC-100: Progress counts study items, not sections
**Category**: Business Rule
**Priority**: P1
**Preconditions**: A fresh user, on Part 91.
**Steps**:
1. Cover 91.103(a) only.

**Expected Results**:
- Covered = 1 and To go = 246.
- `#progress-count` = "1 of 247 study items covered".
- `#filter-covered-count` = 1.
- The 91.103 section still has one uncovered item.

**Business Rule**: business-rules.md › Progress is counted by study item
**Suggested Layer**: E2E

### TC-101: Checking Covered replaces a hand-entered date with today
**Category**: Business Rule
**Priority**: P2
**Preconditions**: A fresh user. 91.103(a) is not covered and its date is set to 2026-01-01 (code allows this; see TC-415).
**Steps**:
1. Check "Mark 91.103(a) as covered".

**Expected Results**:
- The date changes to today's local date.
- The PATCH body has `covered: true` and today's date.

**Business Rule**: business-rules.md › Checking Covered sets the date to today (app.js change handler)
**Suggested Layer**: E2E

### TC-102: Locked starter headings have no Edit button
**Category**: Business Rule
**Priority**: P1
**Preconditions**: A fresh user.
**Steps**:
1. Look at the "91.103 — Preflight action" section row on Part 91.
2. Do the same for any Part 61 starter section.

**Expected Results**: The Edit button is hidden for every starter section.
**Business Rule**: business-rules.md › Locked headings
**Suggested Layer**: E2E

### TC-103: Patching a locked heading returns 403
**Category**: Business Rule
**Priority**: P0
**Preconditions**: A fresh user. Note the id of 91.103.
**Steps**:
1. `PATCH /api/regulations/<id>?part=91` with `{ "regulation": "hacked" }`.

**Expected Results**:
- 403 `{ error: "This regulation heading is protected and cannot be edited." }`.
- `GET` still shows "91.103 — Preflight action".

**Business Rule**: business-rules.md › Locked headings
**Suggested Layer**: API

### TC-104: Subsections of locked sections can still be edited
**Category**: Business Rule
**Priority**: P1
**Preconditions**: A fresh user.
**Steps**:
1. Cover 91.5 ("Entire section").
2. Add the note "type rating".
3. Reload the page.

**Expected Results**: Covered, the date and the note all persist for the 91.5 item.
**Business Rule**: business-rules.md › Locked headings: subsections stay editable
**Suggested Layer**: E2E

### TC-105: Sections and subsections can't be deleted
**Category**: Business Rule
**Priority**: P2
**Preconditions**: A fresh user.
**Steps**:
1. Look for any delete control in the UI.
2. `DELETE /api/regulations/<id>?part=91`.
3. `DELETE /api/subsections/<id>?part=91`.

**Expected Results**:
- The UI has no delete control.
- Both API calls return 404 `{ error: "API endpoint not found." }`, and the data is unchanged.

**Business Rule**: business-rules.md › No deletion
**Suggested Layer**: API

### TC-106: Add section resets the filter and search (heading input is not focused)
**Category**: Business Rule
**Priority**: P2
**Preconditions**: A fresh user. "Covered" filter is active and the search box contains "zzz".
**Steps**:
1. Click "+ Add section".

**Expected Results**:
- The "All" filter is active.
- The search box is empty.
- All 248 items are shown.
- The new section's heading input is **not** visible and does **not** have focus. `addRegulation` calls `focus()` on an input that still has the `hidden` attribute, so nothing happens. The user has to click "Edit" to type a heading. This contradicts business-rules.md and user-flows.md Flow #5; see Open questions.

**Business Rule**: business-rules.md › Add section (doc says the heading input gets focus; code doesn't do this)
**Suggested Layer**: E2E

### TC-107: A new section has one "Entire section" item
**Category**: Business Rule
**Priority**: P2
**Preconditions**: A fresh user.
**Steps**:
1. Click "+ Add section" without typing anything.

**Expected Results**:
- There is exactly one subsection row, with title "Entire section", "No" covered, an empty date and an empty note.
- The API response has `isLocked: false` and `subsections.length` = 1 with `code: ""`.

**Business Rule**: business-rules.md › Add section; api-reference.md › POST /api/regulations
**Suggested Layer**: E2E

### TC-108: Escape reverts a heading edit and saves the original
**Category**: Business Rule
**Priority**: P1
**Preconditions**: A fresh user with a custom section "91.999 — Original".
**Steps**:
1. Click Edit and type " CHANGED".
2. Press Escape.
3. Wait for the PATCH request, then reload.

**Expected Results**:
- The heading shows "91.999 — Original" right away and after the reload.
- The last PATCH body is `{"regulation":"91.999 — Original"}`.

**Business Rule**: business-rules.md › Escape reverts to the heading as it was when the input got focus (bug fix in app.js)
**Suggested Layer**: E2E

### TC-109: Escape on a brand-new section reverts it to empty
**Category**: Business Rule
**Priority**: P2
**Preconditions**: A fresh user.
**Steps**:
1. Click "+ Add section".
2. Click the new section's "Edit" button, type "91.500 — Temp" and press Escape.
3. Reload the page.

**Expected Results**: The heading is still empty after the reload.
**Business Rule**: business-rules.md › Escape reverts
**Suggested Layer**: E2E

### TC-110: Blur saves the heading
**Category**: Business Rule
**Priority**: P2
**Preconditions**: A fresh user with a custom section.
**Steps**:
1. Click Edit and change the text to "91.997 — Blurred".
2. Click elsewhere on the page.
3. Reload the page.

**Expected Results**: The heading is "91.997 — Blurred" after the reload.
**Business Rule**: business-rules.md › Enter or blur saves the heading
**Suggested Layer**: E2E

### TC-111: The catalog fills in subsections on restart [Manual/Setup-heavy]
**Category**: Business Rule
**Priority**: P3
**Preconditions**: A fresh user with a custom Part 91 section titled "91.103 — Custom copy".
**Steps**:
1. Confirm the section has only "Entire section".
2. Restart the server.
3. Reload the page.

**Expected Results**: The custom section now has "Entire section" plus 91.103(a) and 91.103(b), and the custom heading is still editable.
**Business Rule**: business-rules.md › Catalog subsections arrive only on restart
**Suggested Layer**: E2E

### TC-112: Sections without lettered paragraphs show one item
**Category**: Business Rule
**Priority**: P2
**Preconditions**: A fresh user, on Part 91.
**Steps**:
1. Look at the 91.5 section.

**Expected Results**:
- There is one item. Its reference link text is "91.5", its title is "Entire section", and it links to `…/section-91.5#section-91.5`.
- The same holds for 91.11, 91.15 and 91.125.

**Business Rule**: SKILL.md › Vocabulary: Subsection; business-rules.md › eCFR links
**Suggested Layer**: E2E

### TC-113: A heading match shows every item in that section
**Category**: Business Rule
**Priority**: P2
**Preconditions**: A fresh user, on Part 91.
**Steps**:
1. Search for "preflight".

**Expected Results**: Both 91.103(a) and 91.103(b) are shown, even though only the heading contains "Preflight".
**Business Rule**: business-rules.md › Search: heading match shows all items
**Suggested Layer**: E2E

### TC-114: Search matches note text
**Category**: Business Rule
**Priority**: P1
**Preconditions**: A fresh user. 91.103(b) has the note "runway length mnemonic".
**Steps**:
1. Search for "mnemonic".

**Expected Results**:
- Only 91.103(b) is shown, under its section header.
- Results = "Showing 1 of 247 study items".

**Business Rule**: business-rules.md › Search matches notes
**Suggested Layer**: E2E

### TC-115: Search matches a subsection title only
**Category**: Business Rule
**Priority**: P2
**Preconditions**: A fresh user, on Part 91.
**Steps**:
1. Search for "takeoff and landing distance".

**Expected Results**:
- 91.103(b) is shown with the "91.103 — Preflight action" header.
- 91.103(a) is not shown.

**Business Rule**: business-rules.md › Search matches subsection title
**Suggested Layer**: E2E

### TC-116: Search is case-insensitive
**Category**: Business Rule
**Priority**: P2
**Preconditions**: A fresh user, on Part 91.
**Steps**:
1. Search for "PREFLIGHT ACTION".
2. Then search for "preflight action".

**Expected Results**: Both searches give the same 2 results.
**Business Rule**: business-rules.md › Search (case-insensitive)
**Suggested Layer**: E2E

### TC-117: A section header shows only when one of its items is visible
**Category**: Business Rule
**Priority**: P2
**Preconditions**: A fresh user. Only 91.103(a) is covered.
**Steps**:
1. Click "Covered".

**Expected Results**: Exactly one `.section-row` (91.103) and one item row are shown.
**Business Rule**: business-rules.md › Filters
**Suggested Layer**: E2E

### TC-118: Progress is tracked separately for each part
**Category**: Business Rule
**Priority**: P0
**Preconditions**: A fresh user.
**Steps**:
1. On Part 61, cover 61.3(a).
2. Switch to Part 91.
3. Switch back to Part 61.

**Expected Results**:
- Part 91 shows Covered = 0.
- Part 61 shows Covered = 1, and 61.3(a) is still covered.

**Business Rule**: user-flows.md › Flow #3; SKILL.md › Vocabulary: Part
**Suggested Layer**: E2E

### TC-119: Switching parts resets the search and filter
**Category**: Business Rule
**Priority**: P2
**Preconditions**: A fresh user. The search box contains "91.103" and the "Covered" filter is active.
**Steps**:
1. Select "Part 61".

**Expected Results**:
- The search box is empty.
- The "All" filter is active.
- All 208 Part 61 items are shown.

**Business Rule**: user-flows.md › Flow #3
**Suggested Layer**: E2E

### TC-120: Subsection titles come from the catalog
**Category**: Business Rule
**Priority**: P3
**Preconditions**: A fresh user.
**Steps**:
1. Read the title of 91.103(a).

**Expected Results**: It equals `regulation-subsections.json` › `parts["91"]["91.103"][0].title`, which starts "For a flight under IFR or a flight not in the vicinity of an airport".
**Business Rule**: business-rules.md › Subsection titles come from the catalog
**Suggested Layer**: E2E

### TC-121: Notes autosave after a pause without leaving the field
**Category**: Business Rule
**Priority**: P1
**Preconditions**: A fresh user.
**Steps**:
1. Type "abc" in "Notes for 91.103(a)" and leave focus in the field.
2. Wait about 1 second.

**Expected Results**:
- Exactly one `PATCH /api/subsections/:id` is sent, about 350 ms after the last keystroke, with `notes: "abc"`.
- No request is sent per keystroke.

**Business Rule**: business-rules.md › Notes autosave (350 ms debounce)
**Suggested Layer**: E2E

### TC-122: Covered and date changes save immediately
**Category**: Business Rule
**Priority**: P2
**Preconditions**: A fresh user.
**Steps**:
1. Check "Mark 91.103(a) as covered" and measure the time until the PATCH request is sent.

**Expected Results**: The PATCH is sent immediately, with no 350 ms delay.
**Business Rule**: business-rules.md › Covered and date changes save immediately
**Suggested Layer**: E2E

### TC-123: Registering does not sign the user in
**Category**: Business Rule
**Priority**: P1
**Preconditions**: Signed out.
**Steps**:
1. Register through the UI.
2. Go to `/`.

**Expected Results**:
- The register response has no `Set-Cookie`.
- `/` redirects to `/login`.

**Business Rule**: api-reference.md › register (does not sign in)
**Suggested Layer**: E2E

### TC-124: Username and email uniqueness ignores case
**Category**: Business Rule
**Priority**: P1
**Preconditions**: An account `Pilot_A` / `pilot_a@test.com` exists.
**Steps**:
1. Register `pilot_a` with a new email.
2. Register a new username with `PILOT_A@TEST.COM`.

**Expected Results**: Both return 409 `{ error: "That username or email is already in use." }`.
**Business Rule**: business-rules.md › Accounts: unique, compared case-insensitively
**Suggested Layer**: API

### TC-125: Sign-in ignores the case of the username or email
**Category**: Business Rule
**Priority**: P2
**Preconditions**: An account `Pilot_B` / `pilot_b@test.com`.
**Steps**:
1. Log in as `PILOT_B`.
2. Log in as `Pilot_B@Test.com`.

**Expected Results**: Both return 200, and the response `username` = "Pilot_B" (the stored case).
**Business Rule**: data-models.md › users: COLLATE NOCASE
**Suggested Layer**: API

### TC-126: A password reset signs the user out everywhere [Manual/Setup-heavy]
**Category**: Business Rule
**Priority**: P0
**Preconditions**: A user signed in on browser contexts A and B. A reset token from the console.
**Steps**:
1. Reset the password with the token.
2. In context A, reload `/`.
3. In context B, call `GET /api/regulations?part=91`.

**Expected Results**:
- A is redirected to `/login`.
- B gets 401 "Sign in required."

**Business Rule**: api-reference.md › reset-password revokes sessions
**Suggested Layer**: E2E

### TC-127: A new reset request cancels the previous link [Manual/Setup-heavy]
**Category**: Business Rule
**Priority**: P1
**Preconditions**: A registered account. You can read the console.
**Steps**:
1. Request a reset (token T1).
2. Request another reset (token T2).
3. Reset with T1.
4. Reset with T2.

**Expected Results**:
- T1 returns 400 "This reset link is invalid or has expired. Request a new one."
- T2 returns 200.

**Business Rule**: server.js › forgot-password deletes earlier resets for the user
**Suggested Layer**: API

### TC-128: A reset link works only once [Manual/Setup-heavy]
**Category**: Business Rule
**Priority**: P1
**Preconditions**: A reset token T.
**Steps**:
1. Reset with T.
2. Reset again with T and a different password.

**Expected Results**:
- The second call returns 400 "This reset link is invalid or has expired. Request a new one."
- The first new password still works.

**Business Rule**: business-rules.md › Accounts: one-time reset link
**Suggested Layer**: API

### TC-129: The session cookie lasts 7 days
**Category**: Business Rule
**Priority**: P2
**Preconditions**: A registered account.
**Steps**:
1. `POST /api/auth/login`.

**Expected Results**: `Set-Cookie` contains `study_session=<64 hex>; Path=/; HttpOnly; SameSite=Strict; Max-Age=604800`.
**Business Rule**: business-rules.md › Sessions last 7 days
**Suggested Layer**: API

### TC-130: Forgot password gives the same response for unknown emails
**Category**: Business Rule
**Priority**: P1
**Preconditions**: None.
**Steps**:
1. Submit "Request reset link" with `nobody_<random>@test.com`.

**Expected Results**:
- 200 with the same message as for a real account.
- The UI shows the same success text.
- Nothing is printed to the console.

**Business Rule**: business-rules.md › Forgot password never reveals whether the account exists
**Suggested Layer**: E2E

### TC-131: Every account gets its own copy of the starter lists
**Category**: Business Rule
**Priority**: P0
**Preconditions**: Two fresh users, U1 and U2.
**Steps**:
1. As U1, cover 91.103(a) and add a note.
2. Sign in as U2.

**Expected Results**:
- U2 sees Covered = 0 and an empty note on 91.103(a).
- U2's subsection ids differ from U1's.

**Business Rule**: business-rules.md › Accounts and isolation
**Suggested Layer**: E2E

### TC-132: Spaces around the username are trimmed when registering
**Category**: Business Rule
**Priority**: P3
**Preconditions**: None.
**Steps**:
1. Register `"  pilot_trim  "` through the API.
2. Log in as `pilot_trim`.

**Expected Results**: The register call returns 201 and the login returns 200 with `username: "pilot_trim"`.
**Business Rule**: server.js › register trims the username and email
**Suggested Layer**: API

---

## Security (TC-200 – TC-299)

### TC-200: A signed-out visit to the tracker redirects to login
**Category**: Security
**Priority**: P0
**Preconditions**: No session cookie.
**Steps**:
1. `GET /`, `/index.html`, `/app.js` and `/app-core.js` without following redirects.

**Expected Results**: Each returns 302 with `Location: /login` and `Cache-Control: no-store`.
**Business Rule**: business-rules.md › Accounts: unauthenticated redirects
**Suggested Layer**: API

### TC-201: Signed-out API calls are rejected
**Category**: Security
**Priority**: P0
**Preconditions**: No session cookie.
**Steps**:
1. Call `GET /api/regulations?part=91`.
2. Call `POST /api/regulations?part=91`.
3. Call `PATCH /api/subsections/1?part=91`.

**Expected Results**: Each returns 401 `{ error: "Sign in required." }`, and no data changes.
**Business Rule**: business-rules.md › Accounts: unauthenticated /api/* returns 401
**Suggested Layer**: API

### TC-202: A signed-in user is sent away from the login and sign-up pages
**Category**: Security
**Priority**: P2
**Preconditions**: A fresh user, signed in.
**Steps**:
1. Visit `/login`.
2. Visit `/create-account`.

**Expected Results**: Both redirect to `/`.
**Business Rule**: business-rules.md › Accounts: signed-in redirects
**Suggested Layer**: E2E

### TC-203: Another user's subsection can't be changed
**Category**: Security
**Priority**: P0
**Preconditions**: Fresh users U1 and U2. Note U1's 91.103(a) subsection id S.
**Steps**:
1. As U2, `PATCH /api/subsections/S?part=91` with `{ "covered": true, "notes": "pwned" }`.

**Expected Results**:
- 404 "Subsection not found."
- U1's item is unchanged.

**Business Rule**: business-rules.md › Accounts: other users' ids return 404
**Suggested Layer**: API

### TC-204: Another user's section heading can't be changed
**Category**: Security
**Priority**: P0
**Preconditions**: U1 has a custom section with id R.
**Steps**:
1. As U2, `PATCH /api/regulations/R?part=91` with `{ "regulation": "pwned" }`.

**Expected Results**:
- 404 "Regulation not found."
- U1's heading is unchanged.

**Business Rule**: business-rules.md › Accounts and isolation
**Suggested Layer**: API

### TC-205: Using the other part's id in a request returns 404
**Category**: Security
**Priority**: P1
**Preconditions**: A fresh user. Note the subsection id of 61.3(a).
**Steps**:
1. `PATCH /api/subsections/<id>?part=91` with `{ "covered": true }`.

**Expected Results**:
- 404 "Subsection not found."
- 61.3(a) stays uncovered.

**Business Rule**: api-reference.md › id from another part returns 404
**Suggested Layer**: API

### TC-206: Cross-origin writes are blocked
**Category**: Security
**Priority**: P0
**Preconditions**: A fresh user's session cookie.
**Steps**: Send each of these with the header `Origin: http://evil.example`:
1. `POST /api/auth/login`
2. `POST /api/auth/register`
3. `POST /api/auth/logout`
4. `POST /api/auth/forgot-password`
5. `POST /api/auth/reset-password`
6. `POST /api/regulations`
7. `PATCH /api/regulations/:id`
8. `PATCH /api/subsections/:id`

**Expected Results**:
- Each returns 403 `{ error: "Request origin is not allowed." }` and has no effect.
- The logout attempt leaves the session valid.

**Business Rule**: business-rules.md › Accounts: mismatched Origin returns 403
**Suggested Layer**: API

### TC-207: Writes with no Origin header are accepted (current behavior)
**Category**: Security
**Priority**: P2
**Preconditions**: A fresh user's session cookie.
**Steps**:
1. `PATCH /api/subsections/:id?part=91` with `{ "notes": "x" }` and no `Origin` header.

**Expected Results**: 200. This documents that `isSameOrigin` lets requests with no `Origin` through, and that SameSite=Strict is the remaining protection. See Open questions.
**Business Rule**: server.js › isSameOrigin
**Suggested Layer**: API

### TC-208: Page scripts can't read the session cookie
**Category**: Security
**Priority**: P0
**Preconditions**: A fresh user, signed in, on `/`.
**Steps**:
1. Evaluate `document.cookie` in the page.

**Expected Results**: It doesn't contain `study_session`.
**Business Rule**: business-rules.md › Accounts: HttpOnly cookie
**Suggested Layer**: E2E

### TC-209: A session token stops working after logout
**Category**: Security
**Priority**: P0
**Preconditions**: A fresh user, signed in. Note the `study_session` value.
**Steps**:
1. Log out.
2. Send `GET /api/regulations?part=91` with the old cookie added back by hand.

**Expected Results**: 401 "Sign in required."
**Business Rule**: server.js › logout deletes the session row
**Suggested Layer**: API

### TC-210: A forged session cookie is rejected
**Category**: Security
**Priority**: P0
**Preconditions**: None.
**Steps**:
1. Set `study_session` to 64 random hex characters.
2. Request `/` and `/api/regulations?part=91`.

**Expected Results**:
- `/` redirects 302 to `/login`.
- The API call returns 401.

**Business Rule**: business-rules.md › Accounts: sessions
**Suggested Layer**: API

### TC-211: HTML in a heading is shown as text (stored XSS)
**Category**: Security
**Priority**: P0
**Preconditions**: A fresh user.
**Steps**:
1. Add a section with the heading `<img src=x onerror="window.__xss=1">91.1 test`.
2. Reload the page.

**Expected Results**:
- The heading shows the literal text.
- No `img` element is created.
- `window.__xss` is undefined and no dialog appears.

**Business Rule**: app.js renders with textContent
**Suggested Layer**: E2E

### TC-212: HTML in notes is shown as text (stored XSS)
**Category**: Security
**Priority**: P0
**Preconditions**: A fresh user.
**Steps**:
1. Save the note `<script>window.__xss=1</script>` on 91.103(a).
2. Reload the page.
3. Search for "script".

**Expected Results**:
- The note shows as literal text, and no script runs.
- The search result row also renders it safely.

**Business Rule**: app.js renders notes with input.value
**Suggested Layer**: E2E

### TC-213: SQL injection in the login identifier fails
**Category**: Security
**Priority**: P0
**Preconditions**: At least one account exists.
**Steps**:
1. Log in with username `' OR '1'='1' --` and any password.

**Expected Results**: 401 "Username or password is incorrect.", with no session and no server error.
**Business Rule**: server.js › parameterized queries
**Suggested Layer**: API

### TC-214: SQL-like text in a heading is stored as-is
**Category**: Security
**Priority**: P1
**Preconditions**: A fresh user with a custom section.
**Steps**:
1. `PATCH` the heading to `x'); DROP TABLE users; --`.
2. `GET` the regulations.

**Expected Results**:
- The heading comes back exactly as sent.
- Users can still sign in.

**Business Rule**: server.js › parameterized queries
**Suggested Layer**: API

### TC-215: Login errors don't reveal whether an account exists
**Category**: Security
**Priority**: P1
**Preconditions**: An account `pilot_c` exists.
**Steps**:
1. Log in as `pilot_c` with a wrong password.
2. Log in as `nobody_<random>` with any password.

**Expected Results**: Both return 401 with exactly "Username or password is incorrect." and a similar response time, because both run scrypt.
**Business Rule**: server.js › login runs a dummy scrypt for unknown users
**Suggested Layer**: API

### TC-216: Registration reveals whether a username or email is taken (current behavior)
**Category**: Security
**Priority**: P3
**Preconditions**: An account `pilot_d` exists.
**Steps**:
1. Register `pilot_d` with a new email.

**Expected Results**: 409 "That username or email is already in use." This documents that registration exposes which accounts exist. See Open questions.
**Business Rule**: api-reference.md › register
**Suggested Layer**: API

### TC-217: Login is rate-limited [Manual/Setup-heavy]
**Category**: Security
**Priority**: P1
**Preconditions**: The server was just restarted, so the limits are clear. An account exists.
**Steps**:
1. Send 8 failed logins.
2. Send a 9th login with the **correct** password.

**Expected Results**: The 9th returns 429 "Too many sign-in attempts. Please wait 15 minutes and try again." and sets no cookie.
**Business Rule**: api-reference.md › rate limits (login 8 per 15 min)
**Suggested Layer**: API

### TC-218: Registration is rate-limited [Manual/Setup-heavy]
**Category**: Security
**Priority**: P1
**Preconditions**: The server was just restarted.
**Steps**:
1. Send 5 register requests, valid or not.
2. Send a 6th with valid, unused details.

**Expected Results**:
- The 6th returns 429 "Too many account creation attempts. Please wait 15 minutes and try again."
- No user is created.

**Business Rule**: api-reference.md › rate limits (register 5 per 15 min)
**Suggested Layer**: API

### TC-219: Forgot password is rate-limited [Manual/Setup-heavy]
**Category**: Security
**Priority**: P2
**Preconditions**: The server was just restarted.
**Steps**:
1. Send 9 forgot-password requests.

**Expected Results**: The 9th returns 429 "Too many reset requests. Please wait 15 minutes and try again."
**Business Rule**: api-reference.md › rate limits (forgot-password 8 per 15 min)
**Suggested Layer**: API

### TC-220: Reset password is not rate-limited (current behavior)
**Category**: Security
**Priority**: P3
**Preconditions**: None.
**Steps**:
1. Send 20 `POST /api/auth/reset-password` requests with random 64-hex tokens.

**Expected Results**: All 20 return 400 "This reset link is invalid or has expired. Request a new one." and none return 429. See Open questions.
**Business Rule**: server.js › reset-password has no consumeRateLimit
**Suggested Layer**: API

### TC-221: Only allowlisted files are served
**Category**: Security
**Priority**: P0
**Preconditions**: A fresh user, signed in. Repeat while signed out.
**Steps**: Request each of these:
1. `/server.js`
2. `/setup-user.js`
3. `/package.json`
4. `/regulation-subsections.json`
5. `/data/part91.sqlite`
6. `/../server.js`
7. `/%2e%2e/server.js`
8. `/.git/config`

**Expected Results**: Each returns 404 `{ error: "Not found." }` and never the file contents.
**Business Rule**: SKILL.md › Architecture: serveStatic allowlist
**Suggested Layer**: API

### TC-222: Extra fields can't unlock or move a section
**Category**: Security
**Priority**: P0
**Preconditions**: A fresh user with locked 91.103 (id L) and a custom section (id C).
**Steps**:
1. `PATCH /api/regulations/L?part=91` with `{ "regulation": "x", "is_locked": 0 }`.
2. `PATCH /api/regulations/C?part=91` with `{ "regulation": "y", "user_id": 1, "part": "61", "is_locked": 1 }`.

**Expected Results**:
- Step 1 returns 403, and 91.103 stays locked.
- Step 2 returns 200, but only the heading changes. The section keeps its owner, stays in Part 91 and stays unlocked.

**Business Rule**: server.js › PATCH reads only `regulation`
**Suggested Layer**: API

### TC-223: Extra fields on a subsection are ignored
**Category**: Security
**Priority**: P1
**Preconditions**: A fresh user.
**Steps**:
1. `PATCH /api/subsections/<91.103(a)>?part=91` with `{ "notes": "n", "title": "x", "code": "z", "regulation_id": 1 }`.

**Expected Results**: 200. Only the notes change, and the title, code and parent stay the same.
**Business Rule**: api-reference.md › PATCH subsections accepts covered, date and notes only
**Suggested Layer**: API

### TC-224: /api/auth/me doesn't expose secrets
**Category**: Security
**Priority**: P1
**Preconditions**: A fresh user, signed in.
**Steps**:
1. `GET /api/auth/me`.

**Expected Results**: The response has exactly the keys `authenticated`, `username` and `email`, with no id, salt, hash or token.
**Business Rule**: api-reference.md › me
**Suggested Layer**: API

### TC-225: An expired session counts as signed out [Manual/Setup-heavy]
**Category**: Security
**Priority**: P1
**Preconditions**: A fresh user, signed in. You can edit the database.
**Steps**:
1. Set this user's `sessions.expires_at` to a past time.
2. Reload `/`.

**Expected Results**:
- The page redirects to `/login`.
- The session row is deleted.

**Business Rule**: data-models.md › sessions: expired rows are removed when found
**Suggested Layer**: E2E

### TC-226: Non-GET requests to pages are rejected
**Category**: Security
**Priority**: P3
**Preconditions**: None.
**Steps**:
1. `POST /login`.
2. `PUT /styles.css`.

**Expected Results**: Both return 405 `{ error: "Method not allowed." }`.
**Business Rule**: server.js › handleRequest method check
**Suggested Layer**: API

### TC-227: A website login never returns the session token
**Category**: Security
**Priority**: P0
**Preconditions**: A fresh user.
**Steps**:
1. `POST /api/auth/login` without `X-Far-Notes-Client`.

**Expected Results**: 200 with exactly `{ username }` in the body, and the token only in the HttpOnly `Set-Cookie`.
**Business Rule**: business-rules.md › Mobile app clients: only the app gets the token in the body
**Suggested Layer**: API

### TC-228: Requests from an app origin ignore the session cookie
**Category**: Security
**Priority**: P0
**Preconditions**: A fresh user, signed in with the cookie.
**Steps**:
1. `GET /api/regulations?part=91` with `Origin: capacitor://localhost` and the cookie, but no bearer token.
2. `PATCH` 91.103(a) with `{ "notes": "x" }`, the same origin and the cookie only.

**Expected Results**:
- Both return 401 `{ error: "Sign in required." }`.
- 91.103(a)'s notes are unchanged.

**Business Rule**: business-rules.md › Mobile app clients: app origins authenticate by bearer token only
**Suggested Layer**: API

### TC-229: CORS is granted only to the app origins
**Category**: Security
**Priority**: P0
**Preconditions**: None.
**Steps**:
1. `OPTIONS /api/regulations?part=91` with `Origin: capacitor://localhost`.
2. The same with `Origin: https://localhost`.
3. The same with `Origin: http://evil.example`.
4. `GET /api/auth/me` with `Origin: http://evil.example`.

**Expected Results**:
- Steps 1 and 2 return 204 with `Access-Control-Allow-Origin` equal to the request's origin, `Access-Control-Allow-Methods: GET, POST, PATCH`, `Access-Control-Allow-Headers: Content-Type, Authorization, X-Far-Notes-Client`, and no `Access-Control-Allow-Credentials`.
- Step 3 returns 403 `{ error: "Request origin is not allowed." }` with no `Access-Control-Allow-Origin`.
- Step 4 has no `Access-Control-Allow-Origin`.

**Business Rule**: business-rules.md › Mobile app clients: CORS allowlist
**Suggested Layer**: API

### TC-230: The app can write with a bearer token; other origins still can't
**Category**: Security
**Priority**: P1
**Preconditions**: A fresh user, signed in as the app (bearer token).
**Steps**:
1. `PATCH` 91.103(a) with `{ "notes": "from the app" }`, `Origin: capacitor://localhost` and the bearer token.
2. `PATCH` it with `{ "notes": "evil" }`, `Origin: http://evil.example` and the same bearer token.

**Expected Results**:
- Step 1 returns 200 with `notes: "from the app"`.
- Step 2 returns 403 `{ error: "Request origin is not allowed." }`, and the notes stay "from the app".

**Business Rule**: business-rules.md › Mobile app clients; Security › origin check
**Suggested Layer**: API

### TC-231: Logging out with a bearer token revokes it
**Category**: Security
**Priority**: P1
**Preconditions**: A fresh user, signed in as the app.
**Steps**:
1. `POST /api/auth/logout` with the bearer token.
2. `GET /api/regulations?part=91` with the same token.

**Expected Results**: Step 1 returns 200 `{ loggedOut: true }`, and step 2 returns 401 `{ error: "Sign in required." }`.
**Business Rule**: server.js › logout deletes the session row
**Suggested Layer**: API

### TC-232: Malformed or unknown bearer tokens are rejected
**Category**: Security
**Priority**: P1
**Preconditions**: None.
**Steps**:
1. `GET /api/regulations?part=91` with `Authorization: Bearer abc`.
2. The same with a random 64-character hex token.
3. `GET /api/auth/me` with the random token.

**Expected Results**: Steps 1 and 2 return 401 `{ error: "Sign in required." }`, and step 3 returns `{ authenticated: false }`.
**Business Rule**: server.js › sessionToken
**Suggested Layer**: API

### TC-233: api-client.js loads while signed out
**Category**: Security
**Priority**: P1
**Preconditions**: No session.
**Steps**:
1. `GET /api-client.js`.

**Expected Results**: 200 with `Content-Type: text/javascript; charset=utf-8`, because the sign-in pages need it before any session exists.
**Business Rule**: SKILL.md › Architecture: serveStatic allowlist and publicPaths
**Suggested Layer**: API

---

## Negative (TC-300 – TC-399)

### TC-300: Login with a wrong password
**Category**: Negative
**Priority**: P1
**Preconditions**: A registered account.
**Steps**:
1. On `/login`, enter the right username and a wrong password, then submit.

**Expected Results**:
- `#login-error` shows "Username or password is incorrect."
- The Password field has focus.
- The URL stays `/login`.

**Business Rule**: user-flows.md › Flow #1 failures
**Suggested Layer**: E2E

### TC-301: Login with an unknown user
**Category**: Negative
**Priority**: P2
**Preconditions**: None.
**Steps**:
1. Sign in as `nobody_<random>`.

**Expected Results**: The same message as TC-300.
**Business Rule**: user-flows.md › Flow #1 failures
**Suggested Layer**: E2E

### TC-302: Empty login fields block submission
**Category**: Negative
**Priority**: P3
**Preconditions**: None.
**Steps**:
1. Click "Sign in" with both fields empty.

**Expected Results**: The browser's required-field check stops submission, and no `/api/auth/login` request is sent.
**Business Rule**: login.html › required attributes
**Suggested Layer**: E2E

### TC-303: Registering a duplicate username through the UI
**Category**: Negative
**Priority**: P1
**Preconditions**: An account `pilot_e` exists.
**Steps**:
1. On `/create-account`, register `pilot_e` with a new email.

**Expected Results**:
- The error reads "Account creation was not successful. That username or email is already in use."
- The form stays visible.

**Business Rule**: user-flows.md › Flow #1 failures
**Suggested Layer**: E2E

### TC-304: Registering a duplicate email through the UI
**Category**: Negative
**Priority**: P1
**Preconditions**: The email `pilot_e@test.com` is already registered.
**Steps**:
1. Register a new username with that email.

**Expected Results**: The same error as TC-303.
**Business Rule**: business-rules.md › Accounts: unique email
**Suggested Layer**: E2E

### TC-305: Invalid username characters
**Category**: Negative
**Priority**: P2
**Preconditions**: None.
**Steps**:
1. Register `pilot one`, `pilot@one` and `pilot/one` through the UI.

**Expected Results**: Each shows "Account creation was not successful. Username must be 1-64 characters and use only letters, numbers, periods, underscores, or hyphens."
**Business Rule**: api-reference.md › username rules
**Suggested Layer**: E2E

### TC-306: An invalid email is rejected by the API
**Category**: Negative
**Priority**: P2
**Preconditions**: None.
**Steps**:
1. Register through the API with the emails `a@b`, `no-at.com` and `a b@c.com`.

**Expected Results**: Each returns 400 "Enter a valid email address."
**Business Rule**: server.js › register email regex
**Suggested Layer**: API

### TC-307: A 14-character password is rejected
**Category**: Negative
**Priority**: P1
**Preconditions**: None.
**Steps**:
1. In the UI, type a 14-character password and submit.
2. Send the same password through the API.

**Expected Results**:
- The UI's minlength check blocks submission.
- The API returns 400 "Password must be at least 15 characters."

**Business Rule**: business-rules.md › Accounts: password of at least 15 characters
**Suggested Layer**: API

### TC-308: Mismatched passwords on the reset page
**Category**: Negative
**Priority**: P2
**Preconditions**: Open `/reset-password#token=<any>`.
**Steps**:
1. Enter different values in "New password" and "Confirm new password".
2. Submit.

**Expected Results**:
- "The passwords do not match." appears.
- No `/api/auth/reset-password` request is sent.

**Business Rule**: user-flows.md › Flow #6 failures
**Suggested Layer**: E2E

### TC-309: The reset page with no token
**Category**: Negative
**Priority**: P2
**Preconditions**: Open `/reset-password` with no hash.
**Steps**:
1. Enter matching 15+ character passwords and submit.

**Expected Results**: "This reset link is invalid or has expired. Request a new one." appears.
**Business Rule**: server.js › reset-password token format check
**Suggested Layer**: E2E

### TC-310: A malformed or unknown reset token
**Category**: Negative
**Priority**: P2
**Preconditions**: None.
**Steps**:
1. Reset with the token `abc`.
2. Reset with 64 random hex characters.

**Expected Results**: Both return 400 "This reset link is invalid or has expired. Request a new one."
**Business Rule**: api-reference.md › reset-password
**Suggested Layer**: API

### TC-311: A short new password on reset
**Category**: Negative
**Priority**: P2
**Preconditions**: A valid-format token.
**Steps**:
1. `POST /api/auth/reset-password` with a 10-character password.

**Expected Results**: 400 "Password must be at least 15 characters." The token's format is checked first, so a valid-format token is needed to reach this error.
**Business Rule**: server.js › reset-password checks
**Suggested Layer**: API

### TC-312: An invalid part value
**Category**: Negative
**Priority**: P2
**Preconditions**: A fresh user's session.
**Steps**:
1. `GET /api/regulations?part=60`.
2. `GET /api/regulations?part=abc`.
3. `POST /api/regulations?part=135`.

**Expected Results**: Each returns 400 "Part must be 61 or 91."
**Business Rule**: api-reference.md › part must be 61 or 91
**Suggested Layer**: API

### TC-313: Covered must be a boolean
**Category**: Negative
**Priority**: P2
**Preconditions**: A fresh user's session.
**Steps**:
1. PATCH a subsection with `{ "covered": "true" }`.
2. PATCH a subsection with `{ "covered": 1 }`.

**Expected Results**:
- Both return 400 "Covered must be true or false."
- The value is unchanged.

**Business Rule**: server.js › subsection PATCH validation
**Suggested Layer**: API

### TC-314: Invalid date formats are rejected
**Category**: Negative
**Priority**: P2
**Preconditions**: A fresh user's session.
**Steps**: PATCH a subsection's date to each of these:
1. `"2026-02-30"`
2. `"06/01/2026"`
3. `"2026-1-5"`
4. `null`

**Expected Results**: Each returns 400 "Date must be a valid YYYY-MM-DD date."
**Business Rule**: business-rules.md › server accepts only a valid ISO date or ""
**Suggested Layer**: API

### TC-315: Notes must be a string
**Category**: Negative
**Priority**: P3
**Preconditions**: A fresh user's session.
**Steps**:
1. PATCH a subsection with `{ "notes": 123 }`.

**Expected Results**: 400 "Notes must be text."
**Business Rule**: server.js › subsection PATCH validation
**Suggested Layer**: API

### TC-316: A subsection PATCH with no fields
**Category**: Negative
**Priority**: P3
**Preconditions**: A fresh user's session.
**Steps**:
1. PATCH a subsection with `{}`.
2. PATCH a subsection with `{ "foo": 1 }`.

**Expected Results**: Both return 400 "Provide at least one field to update."
**Business Rule**: api-reference.md › at least one field
**Suggested Layer**: API

### TC-317: Malformed JSON
**Category**: Negative
**Priority**: P2
**Preconditions**: A fresh user's session.
**Steps**: Send each of these bodies:
1. `{bad json` to `POST /api/regulations?part=91`
2. `{bad json` to `PATCH /api/subsections/:id?part=91`
3. `{bad json` to `POST /api/auth/login`
4. An empty body to `POST /api/regulations?part=91`

**Expected Results**: Each returns 400 "Request body must be valid JSON."
**Business Rule**: server.js › readJson
**Suggested Layer**: API

### TC-318: A JSON `null` body (current behavior)
**Category**: Negative
**Priority**: P3
**Preconditions**: A fresh user's session.
**Steps**: Send the body `null` to each of these:
1. `POST /api/regulations?part=91`
2. `PATCH /api/subsections/:id?part=91`
3. `POST /api/auth/login`

**Expected Results**:
- Each returns 400 with a raw JavaScript error message, such as "Cannot read properties of null (reading 'regulation')".
- The server keeps running.
- This documents that internal error text is shown to the client. See Open questions.

**Business Rule**: server.js › handlers return error.message
**Suggested Layer**: API

### TC-319: The heading must be text
**Category**: Negative
**Priority**: P3
**Preconditions**: A fresh user with a custom section.
**Steps**:
1. PATCH it with `{ "regulation": 5 }`.
2. PATCH it with `{}`.
3. POST a new section with `{ "regulation": [] }`.

**Expected Results**: Each returns 400 "Regulation must be text."
**Business Rule**: server.js › regulation validation
**Suggested Layer**: API

### TC-320: Ids that don't exist
**Category**: Negative
**Priority**: P3
**Preconditions**: A fresh user's session.
**Steps**:
1. `PATCH /api/regulations/999999?part=91`.
2. `PATCH /api/subsections/999999?part=91`.

**Expected Results**:
- The first returns 404 "Regulation not found."
- The second returns 404 "Subsection not found."

**Business Rule**: api-reference.md
**Suggested Layer**: API

### TC-321: An unknown API route
**Category**: Negative
**Priority**: P3
**Preconditions**: A fresh user's session.
**Steps**:
1. `GET /api/nope`.
2. `PUT /api/regulations/1?part=91`.

**Expected Results**: Both return 404 "API endpoint not found."
**Business Rule**: server.js › API fallthrough
**Suggested Layer**: API

### TC-322: A failed subsection save shows a toast
**Category**: Negative
**Priority**: P1
**Preconditions**: A fresh user. Intercept `PATCH /api/subsections/**` and answer 500 `{ "error": "Disk full" }`.
**Steps**:
1. Check "Mark 91.103(a) as covered".

**Expected Results**:
- The toast shows "Could not save study item: Disk full".
- The UI still shows the item as covered.
- After the intercept is removed and the page is reloaded, the item is uncovered.

**Business Rule**: business-rules.md › A failed save shows a toast starting "Could not save"
**Suggested Layer**: E2E

### TC-323: A failed heading save shows a toast
**Category**: Negative
**Priority**: P2
**Preconditions**: A fresh user with a custom section. Intercept `PATCH /api/regulations/**` and answer 500 `{ "error": "Boom" }`.
**Steps**:
1. Edit the heading and press Enter.

**Expected Results**: The toast shows "Could not save section: Boom".
**Business Rule**: business-rules.md › Failed save toast
**Suggested Layer**: E2E

### TC-324: A failed Add section shows a toast
**Category**: Negative
**Priority**: P2
**Preconditions**: A fresh user. Intercept `POST /api/regulations**` and answer 500 `{ "error": "Boom" }`.
**Steps**:
1. Click "+ Add section".

**Expected Results**:
- The toast shows "Could not add section: Boom".
- No new row appears and the total is unchanged.

**Business Rule**: app.js › addRegulation error path
**Suggested Layer**: E2E

### TC-325: Regulations fail to load
**Category**: Negative
**Priority**: P1
**Preconditions**: A fresh user. Intercept `GET /api/regulations**` and answer 500 `{ "error": "DB locked" }`.
**Steps**:
1. Open `/`.

**Expected Results**:
- The status shows "Database unavailable".
- The empty state shows "Database connection unavailable" and "Start the website with npm start, then reload this page."
- The table is hidden.
- The toast shows "Could not load regulations: DB locked".

**Business Rule**: app.js › loadPart error path
**Suggested Layer**: E2E

### TC-326: The session ends while the tracker is open
**Category**: Negative
**Priority**: P1
**Preconditions**: A fresh user with `/` open in tabs A and B.
**Steps**:
1. In tab B, click "Log out".
2. In tab A, check "Mark 91.103(a) as covered".

**Expected Results**:
- The PATCH returns 401.
- Tab A redirects to `/login`.
- The change is not saved.

**Business Rule**: SKILL.md › Architecture: apiRequest redirects on 401
**Suggested Layer**: E2E

### TC-327: Logout fails
**Category**: Negative
**Priority**: P3
**Preconditions**: A fresh user. Intercept `POST /api/auth/logout` and answer 500 `{ "error": "Boom" }`.
**Steps**:
1. Click "Log out".

**Expected Results**:
- The toast shows "Could not sign out: Boom".
- The page stays on `/`.

**Business Rule**: app.js › logout handler
**Suggested Layer**: E2E

---

## Edge Cases (TC-400 – TC-499)

### TC-400: A password of exactly 15 characters
**Category**: Edge Case
**Priority**: P1
**Preconditions**: None.
**Steps**:
1. Register with a password of exactly 15 ASCII characters.
2. Log in with it.

**Expected Results**: The register call returns 201 and the login returns 200.
**Business Rule**: business-rules.md › Accounts: at least 15 characters
**Suggested Layer**: API

### TC-401: Password length counts characters, not code units
**Category**: Edge Case
**Priority**: P2
**Preconditions**: None.
**Steps**:
1. In the UI, register with a password of 14 "😀" emoji. Each is 1 character (code point) but 2 UTF-16 units.
2. Register through the API with 15 "😀" emoji.

**Expected Results**:
- Step 1 passes the browser's minlength check (28 UTF-16 units) but the server rejects it: "Account creation was not successful. Password must be at least 15 characters."
- Step 2 returns 201.

**Business Rule**: business-rules.md › Accounts: counted as characters, not bytes
**Suggested Layer**: E2E

### TC-402: The password byte limit
**Category**: Edge Case
**Priority**: P2
**Preconditions**: None.
**Steps**:
1. Register with a 1024-byte ASCII password.
2. Register with a 1025-byte password.
3. Register with 342 three-byte characters (1026 bytes).

**Expected Results**:
- Step 1 returns 201.
- Steps 2 and 3 return 400 "Password must be 1024 bytes or fewer."

**Business Rule**: business-rules.md › Accounts: at most 1024 bytes
**Suggested Layer**: API

### TC-403: Username length limits
**Category**: Edge Case
**Priority**: P2
**Preconditions**: None.
**Steps**:
1. Register a 1-character username.
2. Register a 64-character username.
3. Register a 65-character username through the API.
4. Type 65 characters into the UI field.

**Expected Results**:
- 1 and 64 characters return 201.
- 65 characters returns 400 with the username rule message.
- The UI field stops at 64 characters (maxlength).

**Business Rule**: api-reference.md › usernames are 1–64 characters
**Suggested Layer**: API

### TC-404: Allowed username punctuation
**Category**: Edge Case
**Priority**: P3
**Preconditions**: None.
**Steps**:
1. Register `a.b_c-d`.

**Expected Results**: 201, and you can sign in with it.
**Business Rule**: api-reference.md › letters, numbers, `.`, `_` and `-`
**Suggested Layer**: API

### TC-405: Email length limit
**Category**: Edge Case
**Priority**: P3
**Preconditions**: None.
**Steps**:
1. Register a valid 254-character email.
2. Register a valid-format 255-character email through the API.

**Expected Results**:
- Step 1 returns 201.
- Step 2 returns 400 "Enter a valid email address."

**Business Rule**: server.js › email.length > 254
**Suggested Layer**: API

### TC-406: Passwords are not trimmed
**Category**: Edge Case
**Priority**: P2
**Preconditions**: None.
**Steps**:
1. Register with the password `"  correct horse battery  "`.
2. Log in with `"correct horse battery"`.
3. Log in with the exact original password.

**Expected Results**:
- Step 2 returns 401.
- Step 3 returns 200.

**Business Rule**: server.js › the password is used exactly as sent
**Suggested Layer**: API

### TC-407: Request body size limit
**Category**: Edge Case
**Priority**: P2
**Preconditions**: A fresh user.
**Steps**:
1. Save a 16,000-character note.
2. PATCH a note of more than 16,384 bytes.

**Expected Results**:
- Step 1 returns 200 and persists.
- Step 2 returns 413 "Request body is too large."
- In the UI, a note that is too large shows the toast "Could not save study item: Request body is too large."

**Business Rule**: SKILL.md › Tech Stack: 16 KB body limit
**Suggested Layer**: API

### TC-408: Unicode and multi-line notes keep their exact text
**Category**: Edge Case
**Priority**: P2
**Preconditions**: A fresh user.
**Steps**:
1. Save the note "Línea 1\nLine 2 ✈️ — 日本語" on 91.103(a).
2. Reload the page.

**Expected Results**: The note is identical after the reload, including the newline.
**Business Rule**: data-models.md › notes are free text
**Suggested Layer**: E2E

### TC-409: A section with an empty heading
**Category**: Edge Case
**Priority**: P3
**Preconditions**: A fresh user.
**Steps**:
1. Add a section and leave the heading empty.
2. Look at the rows.

**Expected Results**:
- The heading link has no `href`.
- The item's reference link has empty text and no `href`, and its title is "Entire section".
- See Open questions about the empty reference.

**Business Rule**: app.js › makeSubsectionRow uses the heading text when there is no section number
**Suggested Layer**: E2E

### TC-410: A heading with no section number
**Category**: Edge Case
**Priority**: P2
**Preconditions**: A fresh user.
**Steps**:
1. Add a section titled "Night currency notes".

**Expected Results**:
- Neither the heading nor the reference link has an `href`.
- The reference text is "Night currency notes".
- Searching "night" finds it.

**Business Rule**: SKILL.md › Vocabulary: a heading without a section number has no link
**Suggested Layer**: E2E

### TC-411: A Part 91 section number used in the Part 61 list
**Category**: Edge Case
**Priority**: P3
**Preconditions**: A fresh user, on Part 61.
**Steps**:
1. Add a section titled "91.103 — Wrong part".

**Expected Results**:
- The link goes to `…/part-61/section-91.103#section-91.103`, an eCFR URL that doesn't exist. This is the current behavior.
- See Open questions.

**Business Rule**: app.js › ecfrUrl uses the active part
**Suggested Layer**: E2E

### TC-412: Leading spaces before the section number
**Category**: Edge Case
**Priority**: P3
**Preconditions**: A fresh user with a custom section.
**Steps**:
1. Set the heading to "   91.155 — Spaces".

**Expected Results**: The section number is still found and the link points to `section-91.155`.
**Business Rule**: SKILL.md › Vocabulary: regex `/^\s*(\d+\.\d+)/`
**Suggested Layer**: E2E

### TC-413: Leap-day dates
**Category**: Edge Case
**Priority**: P3
**Preconditions**: A fresh user's session.
**Steps**:
1. PATCH a subsection's date to "2028-02-29".
2. PATCH it to "2026-02-29".

**Expected Results**:
- Step 1 returns 200.
- Step 2 returns 400 "Date must be a valid YYYY-MM-DD date."

**Business Rule**: server.js › isIsoDate round-trip check
**Suggested Layer**: API

### TC-414: A future covered date is accepted (current behavior)
**Category**: Edge Case
**Priority**: P3
**Preconditions**: A fresh user.
**Steps**:
1. Set the date of covered item 91.103(a) to "2030-12-31".

**Expected Results**: 200, and the date persists. No rule blocks future dates. See Open questions.
**Business Rule**: business-rules.md › the date can be edited by hand
**Suggested Layer**: E2E

### TC-415: A date on an uncovered item (current behavior)
**Category**: Edge Case
**Priority**: P3
**Preconditions**: A fresh user. 91.103(a) is uncovered.
**Steps**:
1. Set "Date covered for 91.103(a)" to "2026-05-01".
2. Reload the page.

**Expected Results**: The item stays uncovered ("No") and keeps the date 2026-05-01. See Open questions.
**Business Rule**: app.js › the date change handler doesn't check covered
**Suggested Layer**: E2E

### TC-416: Clearing a date with an empty string
**Category**: Edge Case
**Priority**: P3
**Preconditions**: A fresh user with a covered item.
**Steps**:
1. PATCH the subsection with `{ "date": "" }`.

**Expected Results**: 200 with `date: ""`, and covered stays true.
**Business Rule**: business-rules.md › the server accepts an empty string
**Suggested Layer**: API

### TC-417: The covered date follows the browser's time zone
**Category**: Edge Case
**Priority**: P2
**Preconditions**: A fresh user. Set the browser's `timezoneId` to "Pacific/Kiritimati" (UTC+14), and set the clock to 2026-06-01T12:00Z.
**Steps**:
1. Check "Mark 91.103(a) as covered".

**Expected Results**: The date is "2026-06-02", the local date there, not the UTC date "2026-06-01".
**Business Rule**: business-rules.md › the browser's local date
**Suggested Layer**: E2E

### TC-418: Progress percentage rounding
**Category**: Edge Case
**Priority**: P3
**Preconditions**: A fresh user, on Part 91 (247 items).
**Steps**:
1. Cover 1 item.
2. Cover a 2nd item.
3. Cover all items through the API and reload.

**Expected Results**:
- 1 item shows "0%" (0.4% rounded).
- 2 items show "1%".
- All items show "100%", the progress bar width is 100%, and To go = 0.

**Business Rule**: app.js › updateSummary uses Math.round
**Suggested Layer**: E2E

### TC-419: Rapid note edits save the last value
**Category**: Edge Case
**Priority**: P1
**Preconditions**: A fresh user.
**Steps**:
1. Type "one" in a note, leave the field, then quickly type "two" and leave the field.
2. Wait for all PATCH requests, then reload.

**Expected Results**: The note is "onetwo". The PATCH requests ran in order and the last one wins.
**Business Rule**: SKILL.md › Architecture: one serialized save queue per item
**Suggested Layer**: E2E

### TC-420: Rapid covered toggling ends in a consistent state
**Category**: Edge Case
**Priority**: P1
**Preconditions**: A fresh user.
**Steps**:
1. Click the covered checkbox for 91.103(a) 5 times quickly, ending checked.
2. Wait for all PATCH requests, then reload.

**Expected Results**: The item is covered with today's date. The server state matches the final UI state.
**Business Rule**: SKILL.md › Architecture: serialized saves
**Suggested Layer**: E2E

### TC-421: Rapid part switching shows the last part chosen
**Category**: Edge Case
**Priority**: P2
**Preconditions**: A fresh user. Delay `GET /api/regulations?part=61` by 1 second.
**Steps**:
1. Select Part 61, then right away select Part 91.

**Expected Results**:
- The Part 91 data is shown with Total = 247.
- The late Part 61 response is ignored.
- The brand shows "PART 91".

**Business Rule**: SKILL.md › Architecture: loadSequence drops superseded loads
**Suggested Layer**: E2E

### TC-422: Two tabs editing the same note (last write wins)
**Category**: Edge Case
**Priority**: P2
**Preconditions**: A fresh user with `/` open in tabs A and B.
**Steps**:
1. In A, set the note of 91.103(a) to "A".
2. In B, which still shows the old value, set it to "B".
3. Reload both tabs.

**Expected Results**: Both tabs show "B". Tab A gets no warning about the conflict. See Open questions.
**Business Rule**: server.js › PATCH overwrites with no version check
**Suggested Layer**: E2E

### TC-423: Logging out of one browser keeps other sessions
**Category**: Edge Case
**Priority**: P2
**Preconditions**: The same user signed in on contexts A and B.
**Steps**:
1. Log out in A.
2. Reload in B.

**Expected Results**: B stays signed in, because logout deletes only that session's token.
**Business Rule**: server.js › logout deletes one session
**Suggested Layer**: E2E

### TC-424: Custom sections appear in the order they were created
**Category**: Edge Case
**Priority**: P3
**Preconditions**: A fresh user.
**Steps**:
1. Add sections X, Y and Z, in that order.
2. Reload the page.

**Expected Results**: X, Y and Z appear after all starter sections, in that order.
**Business Rule**: server.js › listRegulations ORDER BY id
**Suggested Layer**: E2E

### TC-425: A search of only spaces shows everything
**Category**: Edge Case
**Priority**: P3
**Preconditions**: A fresh user.
**Steps**:
1. Type "   " in the search box.

**Expected Results**: All 247 items are shown, because the search text is trimmed.
**Business Rule**: app.js › render trims the query
**Suggested Layer**: E2E

### TC-426: Special characters in search are matched literally
**Category**: Edge Case
**Priority**: P3
**Preconditions**: A fresh user.
**Steps**:
1. Search for "91.103(b)".
2. Search for ".*".

**Expected Results**:
- "91.103(b)" shows only 91.103(b).
- ".*" matches nothing unless some text literally contains ".*", in which case the empty state shows.

**Business Rule**: business-rules.md › Search matches the subsection reference
**Suggested Layer**: E2E

### TC-427: The login identifier is trimmed
**Category**: Edge Case
**Priority**: P3
**Preconditions**: An account `pilot_f` exists.
**Steps**:
1. Sign in with "  pilot_f  " and the correct password.

**Expected Results**: Sign-in succeeds.
**Business Rule**: login.js and server.js trim the identifier
**Suggested Layer**: E2E

### TC-428: Escape after a debounced autosave still restores the original
**Category**: Edge Case
**Priority**: P1
**Preconditions**: A fresh user with a custom section "91.999 — Original".
**Steps**:
1. Click Edit and type " CHANGED".
2. Wait 1 second, until the debounced PATCH has saved "…CHANGED".
3. Press Escape, wait for the PATCH request, then reload.

**Expected Results**: After the reload, the heading is "91.999 — Original". The later PATCH sent by Escape overwrites the earlier one.
**Business Rule**: business-rules.md › Escape reverts and saves (regression test for the bug fix)
**Suggested Layer**: E2E

### TC-429: Duplicate section numbers are allowed
**Category**: Edge Case
**Priority**: P3
**Preconditions**: A fresh user.
**Steps**:
1. Add a custom section titled "91.103 — Duplicate".

**Expected Results**:
- 2 sections numbered 91.103 are shown.
- Searching "91.103" shows the 2 starter items plus the custom "Entire section" item.

**Business Rule**: data-models.md › no uniqueness on regulation text
**Suggested Layer**: E2E

### TC-430: Unchecking an item while the Covered filter is on
**Category**: Edge Case
**Priority**: P2
**Preconditions**: A fresh user. 91.103(a) and 91.103(b) are covered, and the "Covered" filter is active.
**Steps**:
1. Uncheck 91.103(a).

**Expected Results**:
- 91.103(a) disappears right away.
- The Covered filter count = 1 and the results text = "Showing 1 of 247 study items".

**Business Rule**: app.js › re-renders when the filter isn't All
**Suggested Layer**: E2E

---

## UI State (TC-500 – TC-599)

### TC-500: Connection status while loading
**Category**: UI State
**Priority**: P3
**Preconditions**: A fresh user. Delay `GET /api/regulations` by 1 second.
**Steps**:
1. Open `/`.

**Expected Results**: `#connection-status` shows "Loading regulations..." and then "Connected to SQLite".
**Business Rule**: app.js › loadPart
**Suggested Layer**: E2E

### TC-501: Header and title for Part 91
**Category**: UI State
**Priority**: P3
**Preconditions**: A fresh user, signed in.
**Steps**:
1. Open `/`.

**Expected Results**:
- `#brand-part` = "PART 91".
- `document.title` = "Part 91 Study Log".
- `#current-user` = the username.

**Business Rule**: app.js › loadPart
**Suggested Layer**: E2E

### TC-502: Header, title and intro text change with the part
**Category**: UI State
**Priority**: P3
**Preconditions**: A fresh user.
**Steps**:
1. Select Part 61.

**Expected Results**:
- The brand shows "PART 61".
- The title is "Part 61 Study Log".
- `#intro-copy` = "A simple place to track your progress through the FAA's Part 61 regulations. One section at a time."

**Business Rule**: user-flows.md › Flow #3
**Suggested Layer**: E2E

### TC-503: Summary stats and filter counts stay in sync
**Category**: UI State
**Priority**: P1
**Preconditions**: A fresh user.
**Steps**:
1. Cover 3 items.
2. Uncover 1 of them.

**Expected Results**:
- After each change, these all match without a reload: `#covered-count` = `#filter-covered-count`, `#remaining-count` = `#filter-uncovered-count`, and total = covered + remaining.
- The final state is 2 covered and 245 remaining.

**Business Rule**: business-rules.md › Progress counted by study item
**Suggested Layer**: E2E

### TC-504: The results count follows the search and filter
**Category**: UI State
**Priority**: P2
**Preconditions**: A fresh user.
**Steps**:
1. Search for "91.103".
2. Clear the search.
3. Click "To study".

**Expected Results**: The count reads "Showing 2 of 247 study items", then "Showing 247 of 247 study items", then "Showing 247 of 247 study items" (nothing is covered yet).
**Business Rule**: app.js › updateVisibleCount
**Suggested Layer**: E2E

### TC-505: The empty state when nothing matches
**Category**: UI State
**Priority**: P2
**Preconditions**: A fresh user.
**Steps**:
1. Search for "zzzz-no-match".

**Expected Results**:
- The table is hidden.
- `#empty-state` is visible with "No study items found" and "Try another search, or add a regulation section to your list."
- The results text is "Showing 0 of 247 study items".

**Business Rule**: user-flows.md › Flow #4
**Suggested Layer**: E2E

### TC-506: Escape clears the search box
**Category**: UI State
**Priority**: P3
**Preconditions**: A fresh user. The search box contains "91.103" and has focus.
**Steps**:
1. Press Escape.

**Expected Results**:
- The search box is empty and loses focus.
- All 247 items are shown.

**Business Rule**: user-flows.md › Flow #4
**Suggested Layer**: E2E

### TC-507: The `/` shortcut focuses search only outside text fields
**Category**: UI State
**Priority**: P3
**Preconditions**: A fresh user.
**Steps**:
1. Click the page background and press "/".
2. Focus "Notes for 91.103(a)" and type "/".

**Expected Results**:
- In step 1, the search box gets focus and no "/" is typed into it.
- In step 2, the note contains "/" and the focus stays in the note.

**Business Rule**: user-flows.md › Flow #4 (press `/` to focus)
**Suggested Layer**: E2E

### TC-508: The active filter button is highlighted
**Category**: UI State
**Priority**: P3
**Preconditions**: A fresh user.
**Steps**:
1. Click "To study", then "Covered", then "All".

**Expected Results**: Only the clicked button has the `is-active` class each time.
**Business Rule**: app.js › filter handlers
**Suggested Layer**: E2E

### TC-509: Clicking Edit swaps the link for an input
**Category**: UI State
**Priority**: P2
**Preconditions**: A fresh user with a custom section.
**Steps**:
1. Click "Edit section heading …".

**Expected Results**:
- The heading link is hidden.
- `.regulation-input` is visible, has focus, and its text is fully selected.
- After Enter, the link is visible again with the updated text and aria-label.

**Business Rule**: app.js › makeSectionRow
**Suggested Layer**: E2E

### TC-510: The toast hides itself
**Category**: UI State
**Priority**: P3
**Preconditions**: A fresh user.
**Steps**:
1. Click "+ Add section".
2. Watch `#toast`.

**Expected Results**: The toast gets the `is-visible` class right away and loses it after about 2.4 seconds.
**Business Rule**: app.js › showToast
**Suggested Layer**: E2E

### TC-511: Login page focus and the error state
**Category**: UI State
**Priority**: P3
**Preconditions**: Signed out.
**Steps**:
1. Open `/login`.
2. Submit wrong credentials.

**Expected Results**:
- On load, "Username or email" has focus.
- After the failure, `#login-error` is visible and Password has focus.
- The "Sign in" button is enabled again.

**Business Rule**: login.html and login.js
**Suggested Layer**: E2E

### TC-512: Create-account success state
**Category**: UI State
**Priority**: P2
**Preconditions**: Signed out.
**Steps**:
1. Register successfully.

**Expected Results**:
- `#create-account-form` is hidden and its fields are cleared.
- `#create-account-success` is visible with a link to `/login`.
- `#create-account-error` is hidden.

**Business Rule**: create-account.js
**Suggested Layer**: E2E

### TC-513: Forgot-password success state
**Category**: UI State
**Priority**: P3
**Preconditions**: None.
**Steps**:
1. Submit any well-formed email.

**Expected Results**: `#forgot-success` is visible, `#forgot-error` is hidden, and the button is enabled again.
**Business Rule**: forgot-password.js
**Suggested Layer**: E2E

### TC-514: Reset-password success state [Manual/Setup-heavy]
**Category**: UI State
**Priority**: P3
**Preconditions**: A valid reset link.
**Steps**:
1. Reset the password successfully.

**Expected Results**:
- `#reset-success` is visible.
- The form fields are cleared.
- The "Set new password" button **stays disabled**.

**Business Rule**: reset-password.js
**Suggested Layer**: E2E

### TC-515: Submit buttons are disabled while a request is in flight
**Category**: UI State
**Priority**: P3
**Preconditions**: Delay `/api/auth/login`, `/api/auth/register` and `/api/auth/forgot-password` by 1 second.
**Steps**:
1. Submit each form.

**Expected Results**: Each submit button is disabled during the request and enabled after it finishes. A double-click sends only one request.
**Business Rule**: login.js, create-account.js and forgot-password.js
**Suggested Layer**: E2E

### TC-516: The progress bar width matches the percentage
**Category**: UI State
**Priority**: P3
**Preconditions**: A fresh user with 25 of 247 Part 91 items covered.
**Steps**:
1. Open `/`.

**Expected Results**: `#progress-percent` = "10%", `#progress-bar` has `style.width` = "10%", and the caption = "25 of 247 study items covered".
**Business Rule**: app.js › updateSummary
**Suggested Layer**: E2E

### TC-517: The progress caption before data loads
**Category**: UI State
**Priority**: P3
**Preconditions**: Delay `GET /api/regulations` by 1 second.
**Steps**:
1. Open `/` and read `#progress-count` straight away.

**Expected Results**: It shows "0 of 0 study items covered", because `render()` runs before the fetch and replaces the static HTML text "0 of 0 sections covered". See Open questions.
**Business Rule**: app.js › loadPart calls render() before fetching
**Suggested Layer**: E2E

### TC-518: Accessible names on controls and links
**Category**: UI State
**Priority**: P2
**Preconditions**: A fresh user.
**Steps**:
1. Query by role and name: checkbox "Mark 91.103(a) as covered", textbox "Date covered for 91.103(a)", textbox "Notes for 91.103(a)", link "Open 91.103(a) in the eCFR in a new tab", combobox "Select regulation part" and searchbox "Search regulations or notes".

**Expected Results**: Each control resolves to exactly one element.
**Business Rule**: SKILL.md › Testing notes: accessible names
**Suggested Layer**: E2E

### TC-519: Saving or cancelling a heading edit hides the input
**Category**: UI State
**Priority**: P2
**Preconditions**: A fresh user with a custom section "91.999 — Original". (Added 2026-10-28 after a bug was found while automating TC-010.)
**Steps**:
1. Click "Edit section heading 91.999 — Original" and replace the text with "91.998 — Renamed".
2. Press **Enter**. (Repeat the scenario pressing **Escape** instead.)

**Expected Results**:
- The "Regulation section" text box is hidden, and only the heading link remains.
- With Enter, the link reads "91.998 — Renamed". With Escape, it reads "91.999 — Original".
- The heading text appears exactly once in the section row.

**Business Rule**: business-rules.md › Study tracker: Add section / editing headings (the input closes when the edit ends)
**Suggested Layer**: Component

### TC-520: The Edit button's accessible name follows the saved heading
**Category**: UI State
**Priority**: P2
**Preconditions**: A fresh user with a custom section "91.999 — Original". (Added 2026-10-28 after a bug was found while automating TC-010.)
**Steps**:
1. Click "Edit section heading 91.999 — Original", replace the text with "91.998 — Renamed" and press Enter.

**Expected Results**:
- A button named exactly "Edit section heading 91.998 — Renamed" exists.
- No button is still named "Edit section heading 91.999 — Original".
- The heading link is named "Open 91.998 — Renamed in the eCFR in a new tab".

**Business Rule**: business-rules.md › Study tracker: editing headings (accessible names match the visible heading); SKILL.md › Testing notes: accessible names
**Suggested Layer**: Component

### TC-521: Touch screens get 16px text fields, so iOS doesn't zoom
**Category**: UI State
**Priority**: P2
**Preconditions**: A touch device (iPhone emulation). The tracker's API is stubbed with one unlocked section.
**Steps**:
1. Open the login, create-account, forgot-password and reset-password pages.
2. Open the tracker.

**Expected Results**: Every text field has a computed `font-size` of `16px`: the auth inputs, the part menu, search, the section heading input, the date input and the notes box. iOS zooms into a focused field under 16px and leaves the page cut off on the right.
**Business Rule**: styles.css › `@media (pointer: coarse)`; found while running the iOS app on 2026-10-30
**Suggested Layer**: Component

### TC-522: Desktop keeps the compact field sizes
**Category**: UI State
**Priority**: P3
**Preconditions**: A desktop browser (mouse pointer).
**Steps**:
1. Open the login page and the tracker.

**Expected Results**: The fields keep their desktop sizes: auth inputs 12px, search and section heading 11px, date and notes 10px.
**Business Rule**: styles.css › the touch rule must not change the desktop layout
**Suggested Layer**: Component

### TC-523: Pages stay clear of the iPhone status bar
**Category**: UI State
**Priority**: P1
**Preconditions**: iPhone emulation with a safe area of 62px at the top and 34px at the bottom (status bar and home indicator), as in the iOS app. The tracker's API is stubbed.
**Steps**:
1. Open the login page.
2. Open the tracker.

**Expected Results**:
- The body's padding is 62px at the top and 34px at the bottom.
- The login page's logo, and the tracker's logo, part menu and Log out button, all start at least 62px from the top of the page.
- On a desktop (no safe area), the body padding is 0.

**Business Rule**: styles.css › safe-area padding with `viewport-fit=cover`; found while running the iOS app on 2026-10-30
**Suggested Layer**: Component

### TC-524: On a phone, each study item is a card that fits the screen
**Category**: UI State
**Priority**: P1
**Preconditions**: iPhone emulation (narrower than 700px). The tracker's API is stubbed with 91.103 and its subsections.
**Steps**:
1. Open the tracker.
2. Look at 91.103(a).

**Expected Results**:
- The page is no wider than the screen, so nothing needs sideways scrolling.
- 91.103(a)'s reference is on top, then its Covered checkbox and date on one line, then its notes box across the card's full width.
- The covered control, date and notes all sit inside the screen.
- The row is still exposed as a table row (role `row`), so screen readers and row-based locators keep working.
- On a desktop, the covered control, date and notes stay side by side in one table row.

**Business Rule**: styles.css › phone card layout below 700px; requested after the date and notes were cut off in the iOS app on 2026-10-30
**Suggested Layer**: Component

### TC-525: Scrolled content never shows behind the status bar or home indicator
**Category**: UI State
**Priority**: P1
**Preconditions**: iPhone emulation with a safe area of 62px at the top and 34px at the bottom. The tracker's API is stubbed with enough items to scroll.
**Steps**:
1. Open the tracker.
2. Scroll down so the study list passes under the top of the screen.
3. Mark an item covered while the save fails (stubbed 500), so a toast appears.

**Expected Results**:
- Across the screen's width, the top 62px and the bottom 34px are covered by the page background, not by any text or control.
- The toast appears above the bottom safe area, not under the home indicator.
- On a desktop, the covers are 0px tall.

**Business Rule**: styles.css › fixed safe-area covers (`body::before`, `body::after`); requested after scrolled text showed behind the iPhone status bar on 2026-10-30
**Suggested Layer**: Component

### TC-526: Sections start collapsed, with their progress showing
**Category**: UI State
**Priority**: P1
**Preconditions**: The tracker's API is stubbed with 91.103 (two items, (a) covered) and 91.5 (one item).
**Steps**:
1. Open the tracker.

**Expected Results**:
- Both section headers are visible, and each toggle ("Study items in …") has `aria-expanded="false"`.
- No study item rows are shown.
- 91.103's header shows "1/2" covered, and 91.5's shows "0/1".
- The counts are unchanged: "Showing 3 of 3 study items", Covered 1, To go 2.

**Business Rule**: app.js › sections start collapsed (requested 2026-10-30)
**Suggested Layer**: Component

### TC-527: A section's toggle expands and collapses only that section
**Category**: UI State
**Priority**: P1
**Preconditions**: As TC-526.
**Steps**:
1. Click "Study items in 91.103 — Preflight action".
2. Click it again.

**Expected Results**:
- After step 1, 91.103(a) and 91.103(b) are visible, the toggle has `aria-expanded="true"` and keeps focus, and 91.5 stays collapsed.
- After step 2, 91.103's items are hidden again and the toggle has `aria-expanded="false"`.

**Business Rule**: app.js › toggleSection
**Suggested Layer**: Component

### TC-528: Expand all and Collapse all
**Category**: UI State
**Priority**: P2
**Preconditions**: As TC-526.
**Steps**:
1. Click "Expand all".
2. Click "Collapse all".

**Expected Results**: After step 1 all 3 study items are visible and every toggle has `aria-expanded="true"`. After step 2 none are visible and every toggle has `aria-expanded="false"`.
**Business Rule**: app.js › setAllSections
**Suggested Layer**: Component

### TC-529: Searching opens the sections with matches, and clearing restores them
**Category**: UI State
**Priority**: P1
**Preconditions**: As TC-526. Every section is collapsed.
**Steps**:
1. Search "runway".
2. Collapse 91.103 with its toggle.
3. Clear the search.

**Expected Results**:
- After step 1, 91.103(b) is visible without clicking anything, and 91.5 is not shown (no matches).
- After step 2, 91.103's items are hidden, even though the search is still active.
- After step 3, every section is collapsed again, as before the search.

**Business Rule**: app.js › isExpanded (search opens matching sections)
**Suggested Layer**: Component

### TC-530: A section's progress updates when an item is marked covered
**Category**: UI State
**Priority**: P2
**Preconditions**: As TC-526, with PATCH answered like the server.
**Steps**:
1. Expand 91.103 and mark 91.103(b) covered.

**Expected Results**: 91.103's header changes from "1/2" to "2/2".
**Business Rule**: app.js › updateSectionProgress
**Suggested Layer**: Component

### TC-531: A newly added section opens expanded
**Category**: UI State
**Priority**: P2
**Preconditions**: As TC-526, with POST /api/regulations answered with a new unlocked section.
**Steps**:
1. Click "+ Add section".

**Expected Results**: The new section's toggle has `aria-expanded="true"` and its "Entire section" item is visible, while 91.103 and 91.5 stay collapsed.
**Business Rule**: app.js › addRegulation expands the new section
**Suggested Layer**: Component

---

## Coverage summary

| Category | P0 | P1 | P2 | P3 | Total |
|----------|---:|---:|---:|---:|------:|
| Happy Path (TC-001+) | 3 | 15 | 3 | 0 | 21 |
| Business Rule (TC-100+) | 4 | 11 | 15 | 3 | 33 |
| Security (TC-200+) | 16 | 12 | 3 | 3 | 34 |
| Negative (TC-300+) | 0 | 7 | 13 | 8 | 28 |
| Edge Case (TC-400+) | 0 | 4 | 12 | 15 | 31 |
| UI State (TC-500+) | 0 | 7 | 11 | 14 | 32 |
| **Total** | **23** | **56** | **57** | **43** | **179** |

10 scenarios are marked **[Manual/Setup-heavy]**.

## Open questions

1. **Register rate limit and per-test accounts.** Register allows 5 attempts per IP per 15 minutes, counting successful ones. A suite that creates a fresh user per test will start getting 429 after 5 tests. Options:
   - seed users in a global setup that runs `setup-user.js` or writes to the database directly
   - restart the server between test files
   - add a test-only setting to raise the limit
2. **Requests with no `Origin` header** pass `isSameOrigin` (TC-207). SameSite=Strict protects browsers, but non-browser clients can still send writes with a stolen cookie. Is this intended?
3. **Internal error messages reach the client.** A JSON `null` body returns raw JavaScript errors such as "Cannot read properties of null…" with status 400 (TC-318). Should these be replaced with a generic message?
4. **Registration reveals existing accounts** through the 409 response (TC-216), while login and forgot-password deliberately don't. Is this accepted for a local app?
5. **Reset-password has no rate limit** (TC-220). The 256-bit token makes guessing impractical, but this differs from the other auth endpoints.
6. **A date can be set on an uncovered item**, and future dates are accepted (TC-414, TC-415). Should the date require covered = true, or be limited to today or earlier?
7. **An empty heading gives an empty reference link** (TC-409). The subsection reference falls back to the heading text, which is empty, so the row has an invisible, unlabeled link.
8. **Wrong-part eCFR links** (TC-411). A `91.xxx` heading in the Part 61 list links to `part-61/section-91.xxx`. Should the link use the part from the section number, or should the heading be validated?
9. **Concurrent edits** (TC-422). The last write wins silently across tabs and devices, with no conflict detection.
10. **Progress caption wording** (TC-517). The static HTML says "0 of 0 sections covered", but the app always replaces it with "study items". The HTML text is never seen; it should probably be aligned.
11. **Add section doesn't focus the heading input** (TC-106). `business-rules.md` and `user-flows.md` Flow #5 say the new heading input gets focus so the user can type right away. In the code, the input still has the `hidden` attribute when `focus()` is called, so nothing is focused and the new section shows only an "Edit" button with an empty heading. Fix the code (unhide the input and hide the link before focusing), or update the docs.
12. **Skill template conflict.** `create-scenarios/SKILL.md` contains two output formats: the `TC-<NNN>` template and the older `STUDY-03` example with a Positive/Negative/Edge summary. This file uses the `TC-<NNN>` template, which names this output path, and adapts the coverage summary to its 6 categories. Remove the older block from the skill to avoid confusion.
13. **`/test-strategy` skill.** The skill says this file is used by `/test-strategy`, but no such skill exists in `.claude/skills/` yet.
