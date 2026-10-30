# Business Rules

Behavior rules for FAR Notes: the study tracker and user accounts, in both the UI and the API. Part of the `far-notes-domain` skill; see `SKILL.md` for vocabulary and architecture and `data-models.md` for the schema.

## Study tracker

- **Progress is counted by study item, not by section.** Total, Covered, To go, the filter counts, the progress percentage and "Showing X of Y study items" all count subsections across the active part.
- **Checking Covered sets the date to today** (the browser's local date, `YYYY-MM-DD`). Unchecking clears the date. The date can also be edited by hand. The server accepts only a valid ISO date or an empty string.
- **Notes autosave**: 350 ms after typing stops, and right away on blur. Covered and date changes save immediately. A failed save shows a toast that starts with "Could not save".
- **Locked headings**: starter sections show no Edit button, and `PATCH /api/regulations/:id` returns 403 "This regulation heading is protected and cannot be edited." Their subsections' covered, date and notes stay editable.
- **No deletion**: there is no way to delete a section or a subsection, in the UI or the API.
- **Add section** creates an empty-heading section in the active part with one "Entire section" item. It resets the filter to All, clears the search box and focuses the heading input. Enter or blur saves the heading. Escape reverts to the heading as it was when the input got focus, then saves that value. Either way the edit ends: the text box closes, the heading link shows the saved heading, and the Edit button's accessible name (`Edit section heading <heading>`) changes to match it.
- A user-added section gets lettered subsections from the catalog only when the **server restarts**. The startup backfill adds them next to the existing "Entire section" item; it doesn't happen when the heading is saved.
- **Search** (case-insensitive) matches the section heading, the subsection reference (e.g. `91.103(b)`), the subsection title and the notes. If the heading matches, all of that section's items show.
- **Collapsible sections**: every section starts collapsed when a part loads (including after a reload or a part switch). Each header has a toggle button named `Study items in <heading>` with `aria-expanded`, and a `covered/total` count for that section. The toolbar has **Expand all** and **Collapse all**. While a search is active, sections with matches open automatically; collapsing one during the search sticks until the search text changes, and clearing the search restores the previous collapse state. **Add section** opens the new section. Collapsing hides rows only: the counts and "Showing X of Y" are unchanged.
- **Filters**: All / To study (not covered) / Covered apply to subsections. A section header only shows if at least one of its items is visible. When nothing matches, the table hides and `#empty-state` shows.
- **eCFR links** open in a new tab:
  - section: `https://www.ecfr.gov/current/title-14/part-{part}/section-{n}#section-{n}`
  - subsection: `https://www.ecfr.gov/current/title-14/part-{part}/section-{n}#p-{n}({code})`
- **Subsection titles** come from `regulation-subsections.json` (an eCFR snapshot dated 2026-06-01, shaped as `parts[part][section] = [{code, title}]`). The server rewrites stored titles to match the catalog on every startup, so changing a title means changing the JSON.

## Accounts and isolation

- Each account has its own copy of both starter lists, with separate progress, dates and notes. Every query is scoped by `user_id`, so one user must never see or change another user's rows. Other users' IDs return 404.
- Username and email must be unique and are compared case-insensitively. Sign-in accepts either one.
- Passwords need at least 15 characters (counted as characters, not bytes) and at most 1024 bytes. No character-class rules apply.
- Sessions last 7 days in an HttpOnly, SameSite=Strict `study_session` cookie. Unauthenticated `/`, `/index.html`, `/app.js` and `/app-core.js` redirect to `/login`, and unauthenticated `/api/*` returns 401. A signed-in user who visits `/login` or `/create-account` is redirected to `/`.
- Forgot password never says whether the account exists. The one-time reset link is printed to the server console, not emailed, and expires after 30 minutes.
- Auth endpoints are rate-limited in memory per IP (login and forgot-password 8, register 5, per 15 minutes). Every attempt counts, successful or not, so a test suite that creates many accounts will hit the register limit until the server restarts.
- State-changing requests with an `Origin` header that doesn't match the host, and isn't an app origin, are rejected with 403.

## Mobile app clients

- The iOS and Android apps (`mobile/`) use the same API and the same `sessions` table as the website.
- App origins come from `FAR_NOTES_APP_ORIGINS` (default `capacitor://localhost,https://localhost`). Only they get CORS headers (no credentials). A preflight from any other origin gets 403.
- `POST /api/auth/login` returns the session token in the body only when the request sends `X-Far-Notes-Client: app`. A website login gets the token only in the HttpOnly cookie.
- Requests from an app origin authenticate by `Authorization: Bearer <token>` only. The cookie is ignored for them, so allowing those origins can't enable cross-site requests with the website cookie.
- Logging out with a bearer token deletes that session. The token otherwise lasts 7 days, like the cookie.
