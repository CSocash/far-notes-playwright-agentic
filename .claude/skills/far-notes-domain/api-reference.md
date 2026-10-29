# API Reference

HTTP endpoints served by `server.js` at `http://127.0.0.1:3000`. Part of the `far-notes-domain` skill; see `SKILL.md` for architecture and `data-models.md` for the tables behind these responses.

All bodies and responses are JSON. Errors are always `{ error }` with a 4xx status. Every POST or PATCH with a mismatched `Origin` header gets 403.

## Authentication (No Auth Required)
| Method | Endpoint                   | Body                          | Response                                      |
|--------|----------------------------|-------------------------------|-----------------------------------------------|
| GET    | /api/auth/me               | -                             | { authenticated, username?, email? }          |
| POST   | /api/auth/register         | { username, email, password } | 201 { accountCreated: true } (no sign-in)     |
| POST   | /api/auth/login            | { username, password }        | { username } + `study_session` cookie (+ `token` for the app) |
| POST   | /api/auth/logout           | -                             | { loggedOut: true } + cookie cleared          |
| POST   | /api/auth/forgot-password  | { email }                     | { message } (same for unknown emails)         |
| POST   | /api/auth/reset-password   | { token, password }           | { passwordUpdated: true } (revokes sessions)  |

- `login` accepts a username *or* an email in the `username` field.
- Usernames must be 1–64 characters long and may contain only letters, numbers, `.`, `_` and `-`.
- Passwords need at least 15 characters and at most 1024 bytes.
- Per-IP rate limits, in memory, reset when the server restarts. Over the limit, the endpoint returns 429.
  - `login`: 8 attempts per 15 minutes
  - `forgot-password`: 8 attempts per 15 minutes
  - `register`: 5 attempts per 15 minutes

## Mobile app clients

- Send `X-Far-Notes-Client: app` to `login` to get `{ username, token }`. Send `Authorization: Bearer <token>` on every later call, including `logout`.
- `OPTIONS` from an app origin returns 204 with `Access-Control-Allow-Methods: GET, POST, PATCH` and `Access-Control-Allow-Headers: Content-Type, Authorization, X-Far-Notes-Client`. Any other origin gets 403.
- From an app origin, the cookie is ignored: without a bearer token, the call returns 401.

## Regulations (Session Cookie or Bearer Token Required)
| Method | Endpoint                 | Query/Body                              | Response                    |
|--------|--------------------------|-----------------------------------------|-----------------------------|
| GET    | /api/regulations         | ?part=61\|91                            | Section[]                   |
| POST   | /api/regulations         | ?part=61\|91, { regulation? }           | 201 Section                 |
| PATCH  | /api/regulations/:id     | ?part=61\|91, { regulation }            | Section (403 if locked)     |
| PATCH  | /api/subsections/:id     | ?part=61\|91, { covered?, date?, notes? } | Subsection                |

- Without a valid session, every endpoint here returns 401.
- `part` defaults to `91`; any other value returns 400.
- An `id` that belongs to another user, or to the other part, returns 404.
- A new section created by POST gets a single "Entire section" subsection.
- PATCH to a subsection needs at least one field. `date` must be `YYYY-MM-DD` or `""`.
- There are no DELETE endpoints.

**Types**
- `Section` = `{ id, regulation, isLocked, subsections: Subsection[] }`
- `Subsection` = `{ id, code, title, covered: boolean, date, notes }`
