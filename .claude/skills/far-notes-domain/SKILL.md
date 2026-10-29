---
name: far-notes-domain
description: Domain rules for the FAR Notes study log (FAA Part 61/91 regulations, sections vs. lettered subsections, coverage tracking, locked starter headings, eCFR links, per-user data). Use when writing or reviewing features, Playwright tests, test data, or bug reports for this app, or when deciding what behavior is expected.
user-invocable: false   # loaded automatically by the Claude agent when relevant, not called directly by the user; hidden from the slash-command menu
---

# FAR Notes Domain Knowledge

## Overview

FAR Notes is a personal study tracker for FAA regulations in Title 14 CFR. Every user signs in and gets a private study log for **Part 91** (General Operating and Flight Rules) and **Part 61** (Certification: Pilots, Flight Instructors, and Ground Instructors). The lists are study aids, not authoritative copies of the regulations.

## Tech Stack

- **Frontend**: Vanilla HTML/CSS/JavaScript (no framework, no build step), `<template>` rows, `fetch`, Google Fonts (DM Sans, Manrope)
- **Backend**: Node.js 22.13+ with zero npm dependencies: `node:http`, `node:sqlite` (`DatabaseSync`), SQLite in WAL mode at `data/part91.sqlite`
- **Auth**: Cookie sessions on the website (`study_session`, HttpOnly, SameSite=Strict, 7-day expiry) and the same session token as `Authorization: Bearer` in the mobile app; scrypt password hashing with per-user salt, per-IP rate limiting
- **Mobile**: iOS and Android apps in `mobile/`, built with Capacitor 8.6 from the website's own pages (the only part of the repo with npm dependencies)
- **Testing**: Python pytest + pytest-playwright (Playwright 1.64, Chromium) for API, component and E2E tests (`tests/`, `pytest.ini`, `requirements-dev.txt`). Planned unit tests for the JS helpers use `node --test`
- **API**: Hand-routed JSON REST at `http://127.0.0.1:3000/api/*`; no Swagger/OpenAPI docs (endpoints are listed in `api-reference.md`)

## Architecture

### Frontend

```
login.html ──── login.js ─────────┐
create-account.html ─ create-account.js ├─ POST /api/auth/*  (then redirect)
forgot-password.html ─ forgot-password.js │
reset-password.html ─ reset-password.js ┘  (token read from URL #token=…)

index.html ──── app.js
  1. GET /api/auth/me → not authenticated? → /login
  2. loadPart(activePart) → GET /api/regulations?part=91|61
  3. render(): section row + subsection rows (from #row-template),
     filtered by search text and All / To study / Covered
  4. edits → queueSave → persistItem → PATCH (debounced, one queue per item)
```

- `api-client.js` is loaded before every page script and exposes `window.FarNotesApi` (`fetch`, `goTo`, `pageUrl`). On the website it is a pass-through. When `window.FAR_NOTES_CONFIG` is set (only in the app, by `mobile/www/config.js`), it prefixes requests with the configured server, sends `X-Far-Notes-Client: app` and the bearer token (kept in `localStorage`), and rewrites `/login`-style links to the bundled `.html` files.
- `app-core.js` (loaded first) holds the pure logic as `window.FarNotesCore`: section-number parsing, eCFR URLs, references, search and filter matching, the progress summary and the local date. `app.js` uses it.
- `app.js` keeps all state in module-level variables (`regulations`, `activePart`, `activeFilter`) and re-renders the whole table body when the search, filter or part changes.
- Changing the part dropdown calls `loadPart`. A `loadSequence` counter drops responses from earlier, superseded loads.
- `apiRequest` adds the JSON header, redirects to `/login` on any 401 outside `/api/auth/`, and throws the server's `error` message so it can be shown in a toast.

### Backend

```
http.createServer → handleRequest(request, response)
  ├─ handleAuthRequest   /api/auth/me | login | register | logout | forgot-password | reset-password
  ├─ applyCors / OPTIONS CORS headers and preflight for APP_ORIGINS only
  ├─ authenticatedUser   bearer token, else study_session cookie (never the cookie from an app origin) → sessions → users
  ├─ auth gates          /api/* → 401 · / /index.html /app.js → 302 /login · /login when signed in → 302 /
  ├─ regulation API      GET/POST /api/regulations · PATCH /api/regulations/:id · PATCH /api/subsections/:id
  └─ serveStatic         explicit allowlist of HTML/CSS/JS/PNG files, everything else 404
```

- Everything lives in `server.js` except the input checks, which are in `lib/validation.js`. Startup does the following, in order:
  1. Creates the tables.
  2. Adds any missing columns.
  3. Assigns legacy rows to the first user.
  4. Seeds the starter lists.
  5. Re-locks starter rows.
  6. Back-fills subsections from `regulation-subsections.json`.
- `setup-user.js` is a separate CLI that writes the first user directly into the same SQLite file.

## Detailed Knowledge (Sub-Files)

Topic-specific knowledge lives in separate Markdown files in this folder (`.claude/skills/far-notes-domain/`). Don't load them all. Read only the ones that match the current task, using the table below. If none match, this file is enough.

| File | Read when the task involves |
| --- | --- |
| [`business-rules.md`](business-rules.md) | expected app behavior: progress counting, covered dates, autosave, locked headings, adding/editing sections, search, filters, eCFR links, subsection titles, plus account rules: per-user isolation, username/email uniqueness, password rules, sessions and redirects, password reset, rate limits, origin checks. Read before writing tests, assertions or bug reports, or changing `app.js`, auth or regulation API behavior. |
| [`user-flows.md`](user-flows.md) | end-to-end user journeys with steps and expected results: sign-up and sign-in, studying a subsection, switching parts, search and filters, adding and editing sections, password reset, logout and access control. Read when writing or planning Playwright E2E tests, manual test cases, or reproducing a bug. |
| [`data-models.md`](data-models.md) | SQLite schema: tables, columns, keys, relationships, token storage, and the `regulation-subsections.json` catalog format. Read when touching `server.js` schema or migrations, querying `data/part91.sqlite`, seeding or inspecting test data, or checking what a field stores. |
| [`api-reference.md`](api-reference.md) | HTTP endpoints: methods, paths, query params, request bodies, responses, status codes (401/403/404/429), rate limits, and the `Section`/`Subsection` response types. Read when calling or testing the API directly (e.g. Playwright `request` fixtures, API-level setup), mocking network calls, or changing routes in `server.js`. |

## Vocabulary

| Term | Meaning in this app |
| --- | --- |
| Part | `"91"` or `"61"`. Chosen with the `#part-select` dropdown. Every regulation API call carries `?part=`. Part 91 is the default. |
| Section / regulation | A heading row such as `91.103 — Preflight action`. Stored in `regulations.regulation` as free text. |
| Section number | The `NN.NNN` at the start of the heading, parsed with `/^\s*(\d+\.\d+)/`. It drives eCFR links and subsection lookup. A heading without one has no link. |
| Subsection / study item | One lettered paragraph of a section, e.g. `91.103(a)`. This is the unit that gets studied. A section with no lettered paragraphs in the catalog gets a single item with `code: ""` titled "Entire section". |
| Covered | Whether a study item has been studied. Stored only on subsections. |
| Starter / locked section | A built-in heading seeded for every user (`is_locked = 1`). Its heading cannot be edited. |
| User-added section | Created with **Add section**. Its heading can be edited. |

## Testing notes

- Start the app with `npm start` (http://127.0.0.1:3000). Data lives in `data/part91.sqlite`. Prefer creating a fresh account per test through `/create-account` over relying on the shared `VMC43` account.
- Stable selectors: `#part-select`, `#search`, `.filter-button[data-filter="all|uncovered|covered"]`, `#add-regulation`, `#regulation-rows`, `.section-row`, `.section-heading-link`, `.edit-button`, `.regulation-input`, `.subsection-reference`, `.subsection-title`, `.covered-input`, `.covered-label`, `.date-input`, `.notes-input`, `#total-count`, `#covered-count`, `#remaining-count`, `#progress-percent`, `#results-count`, `#empty-state`, `#toast`, `#logout`.
- Subsection controls have accessible names such as `Mark 91.103(a) as covered`, `Date covered for 91.103(a)` and `Notes for 91.103(a)`. Links are named `Open 91.103(a) in the eCFR in a new tab`.
- Because saves are debounced, wait for the `PATCH /api/subsections/:id` response (or blur the field) before reloading to check that a change persisted.
