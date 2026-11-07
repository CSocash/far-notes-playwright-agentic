# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

FAA Regulations Study Log: a local, single-machine study tracker for Part 61 and Part 91 regulations. Plain Node.js (>= 22.13) with **zero npm dependencies** — it uses built-in `node:http`, `node:crypto`, and `node:sqlite` (`DatabaseSync`). The frontend is vanilla HTML/CSS/JS with no build step. The iOS and Android apps in `mobile/` wrap those same pages with Capacitor; that folder is the only place with npm dependencies.

## Commands

- `npm start` — runs `server.js` on http://127.0.0.1:3000 (bound to localhost by default; override with `PORT` and `HOST`, e.g. `HOST=0.0.0.0` to reach it from a phone on the LAN).
- `INITIAL_PASSWORD='at-least-15-chars' npm run setup-user` — creates the initial account (defaults `VMC43` / `VMC43@test.com`, override with `INITIAL_USERNAME` / `INITIAL_EMAIL`). Refuses to overwrite an existing account.
- Password reset has no email service: `POST /api/auth/forgot-password` prints a one-time reset link (30 min expiry) to the server terminal.
- The app must be loaded through the server, not by opening `index.html` directly.
- Mobile apps (`mobile/`, Capacitor 8.6, iOS and Android). Run `npm install` there once. `npm run build` copies the website's pages into `mobile/www`, and `npm run ios` / `npm run android` also run `cap sync` and open Xcode or Android Studio. Without `FAR_NOTES_API_URL`, the iOS Simulator calls `http://127.0.0.1:3000` and the Android emulator calls `http://10.0.2.2:3000`.
- Tests are Python: pytest + pytest-playwright (Playwright 1.64, Chromium).
  - One-time setup: `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt && .venv/bin/playwright install chromium`.
  - `.venv/bin/pytest` runs everything.
  - `.venv/bin/pytest -m api`, `-m component`, `-m e2e` or `-m smoke` runs one group. The layer markers come from the test's folder.
  - `.venv/bin/pytest -k tc_002` runs a single test.
  - `.venv/bin/pytest --run-device -m device` runs the Appium tests in `tests/device` (the real iOS app on the iPhone 17 Simulator; needs Xcode and Appium 3 with the XCUITest driver). They are left out of plain runs. Each session rebuilds the app against the test server on port 3100, then restores the normal `mobile/ios` bundle. Add `--slowmo 1000` to watch it step by step.
  - Allure report: `.venv/bin/pytest --alluredir=allure-results --clean-alluredir`, then `npx allure@3.22.1 generate allure-results` and `npx allure@3.22.1 open allure-report` (plain `npx allure` runs an old Allure 2 install).
  - Load tests use Locust (`tests/load/locustfile.py`, not collected by pytest). Install with `.venv/bin/pip install -r requirements-load.txt`. Start a throwaway server with `FAR_NOTES_DB=.test-data/load.sqlite FAR_NOTES_DISABLE_RATE_LIMIT=1 PORT=3300 npm start`, then run `.venv/bin/locust -f tests/load/locustfile.py --host http://127.0.0.1:3300` (web UI on http://localhost:8089, or add `--headless -u 10 -r 2 -t 30s`). Never point it at port 3000.
  - The one exception is unit tests for the JavaScript helpers. They use Node's built-in runner, `node --test tests/unit` (none written yet).
  - A session fixture in `tests/conftest.py` starts its own server on port 3100 with `FAR_NOTES_DB=.test-data/far-notes-test.sqlite` and `FAR_NOTES_DISABLE_RATE_LIMIT=1`, so tests never touch `data/part91.sqlite`.
  - `--base-url` points the tests at another server (reused if it answers; a remote one must already be running). Port 3000, the dev server with the real `data/part91.sqlite`, is refused unless you add `--allow-dev-server`.
  - Test browsers stay offline: Chromium runs with its sandbox on, and every request not to the server under test (Google Fonts, eCFR) is blocked. A context a test creates itself with `browser.new_context` needs `block_outside_requests` from `tests/support/network.py`.
  - Test conventions are in the `playwright-best-practices` skill.

## Architecture

**`server.js` is the whole backend** — schema, migrations, seeding, auth, routing, and static file serving in one file:

- **Startup migrations run on every boot.** `CREATE TABLE IF NOT EXISTS` plus `PRAGMA table_info` checks add columns (`part`, `is_locked`, `user_id`) to older databases. It then (re)seeds starter lists per user, re-locks starter rows, and back-fills `regulation_subsections` for every regulation from `regulation-subsections.json` (`INSERT OR IGNORE`, and subsection titles are overwritten from the catalog). Schema changes must stay idempotent and must preserve existing user data — legacy section-level `covered/date/notes` are copied down into subsections.
- **Data model:** `users` → `regulations` (per user, per `part` "61"/"91"; `is_locked=1` marks built-in starter headings) → `regulation_subsections` (one row per lettered paragraph `code`, or a single row with `code=''` / "Entire section" when the catalog has none). Coverage, date, and notes live on **subsections**, not regulations. Also `sessions` and `password_resets`, which store only SHA-256 hashes of tokens.
- **Starter lists** are hardcoded arrays (`starterRegulations` for Part 91, `part61StarterRegulations` for Part 61) of `[sectionNumber, heading]`. The section number is parsed from the heading text (`/^\s*(\d+\.\d+)/`) to look up subsections in `regulation-subsections.json` (eCFR snapshot dated 2026-06-01, `parts[part][section] = [{code, title}]`). New-user seeding goes through `createStarterRegulationsForUser`.
- **Routing** is a hand-written chain of `if (pathname === ... && method === ...)` in `handleAuthRequest` (`/api/auth/*`: me, login, register, logout, forgot-password, reset-password) and `handleRequest` (`GET/POST /api/regulations`, `PATCH /api/regulations/:id`, `PATCH /api/subsections/:id`). Every regulation API call needs `?part=61|91`. Static files come from an explicit allowlist in `serveStatic` plus `publicPaths` — **a new frontend file has to be registered in both, and in `FILES` in `mobile/scripts/build-www.js`**, and the tracker files in `TRACKER_PATHS` (`/`, `/index.html`, `/app.js`, `/app-core.js`) require auth (they redirect to `/login`).
- **Security conventions to keep:** state-changing requests check `isAllowedOrigin` (same origin or one of `APP_ORIGINS`); requests from an app origin authenticate only by `Authorization: Bearer` (`sessionToken`), never the cookie, and the login body includes the token only for `X-Far-Notes-Client: app`; auth endpoints use the in-memory `consumeRateLimit`; passwords use scrypt with a per-user salt (minimum 15 characters, max 1024 bytes); session cookie `study_session` is HttpOnly + SameSite=Strict, 7-day TTL; every query is scoped by `user_id`; locked headings reject PATCH with 403; there is no delete endpoint by design.

**Shared pure logic** (no DOM, network or globals, so `node --test` can unit-test it):
- `lib/validation.js`: `isIsoDate`, `checkUsername`, `checkEmail` and `checkPassword`. Each check returns the client error message or `null`. `server.js` uses them for register, reset-password and subsection dates.
- `app-core.js`: `sectionNumber`, `ecfrUrl`, `referenceFor`, `normalizeQuery`, `matchingSubsections(regulation, query, filter)`, `summarize` and `localDate(now)`. It's a classic script wrapped in a function. In the browser it sets `window.FarNotesCore`, which `app.js` reads (`index.html` loads it first), and under Node it exports the same object with `module.exports`.

**Frontend:** every page loads `api-client.js` first and makes requests and redirects through `FarNotesApi.fetch` / `FarNotesApi.goTo` (never bare `fetch` or `location.replace`), so the same scripts work on the website and in the Capacitor app. Each HTML page has its own script (`login.js`, `create-account.js`, `forgot-password.js`, `reset-password.js`). `app.js` drives the main tracker: it loads a part via `apiRequest` (which redirects to `/login` on 401), renders section rows and subsection rows from `<template>` elements in `index.html`, links citations to eCFR, and autosaves edits through `queueSave` → `persistItem` (350 ms debounce, with one serialized promise queue per item so PATCHes don't race).

`setup-user.js` opens the same `data/part91.sqlite` on its own and duplicates the `users` table DDL, so keep it in sync with `server.js` if the users schema changes. The database (`data/*.sqlite*`) is gitignored.
