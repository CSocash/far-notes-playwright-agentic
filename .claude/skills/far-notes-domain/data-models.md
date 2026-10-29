# Data Models

SQLite schema and data files behind FAR Notes. Part of the `far-notes-domain` skill; see `SKILL.md` for architecture and `api-reference.md` for the endpoints.

The SQLite schema is defined in `server.js`. Foreign keys are enabled, and every child table cascades on delete.

```
users 1 ──< regulations 1 ──< regulation_subsections
users 1 ──< sessions
users 1 ──< password_resets
```

**users**
| Column | Type | Notes |
| --- | --- | --- |
| id | INTEGER PK | |
| username | TEXT | UNIQUE, `COLLATE NOCASE` |
| email | TEXT | UNIQUE, `COLLATE NOCASE` |
| password_salt | TEXT | hex, 16 random bytes |
| password_hash | TEXT | hex scrypt output, 64 bytes |
| created_at | TEXT | `CURRENT_TIMESTAMP` |

**regulations** (one section in one part for one user)
| Column | Type | Notes |
| --- | --- | --- |
| id | INTEGER PK | |
| user_id | INTEGER FK → users | Added by migration, so the column is nullable. Legacy rows are assigned to the first user. |
| part | TEXT | `'91'` (default) or `'61'` |
| regulation | TEXT | Heading text, e.g. `91.103 — Preflight action`. Starts as `''` for a new section. |
| is_locked | INTEGER 0/1 | 1 = built-in starter heading that can't be edited |
| covered, date, notes | INTEGER / TEXT / TEXT | Legacy section-level progress, kept only so it can be copied into subsections. The app no longer reads or writes it. |
| created_at, updated_at | TEXT | timestamps |

**regulation_subsections** (one study item)
| Column | Type | Notes |
| --- | --- | --- |
| id | INTEGER PK | |
| regulation_id | INTEGER FK → regulations | |
| code | TEXT | Paragraph letter (`a`, `b`, …), or `''` for "Entire section". `UNIQUE (regulation_id, code)` |
| title | TEXT | From the catalog; overwritten from the catalog on startup |
| covered | INTEGER 0/1 | API returns a boolean |
| date | TEXT | `YYYY-MM-DD` or `''` |
| notes | TEXT | free text |
| created_at, updated_at | TEXT | timestamps |

**sessions** / **password_resets**
| Column | Type | Notes |
| --- | --- | --- |
| token_hash | TEXT PK | SHA-256 of the raw token. The raw token exists only in the cookie or the reset link. |
| user_id | INTEGER FK → users | |
| expires_at | INTEGER | epoch ms. Sessions last 7 days and resets last 30 minutes. Expired rows are deleted on startup and when they are found during use. |
| created_at | TEXT | timestamp |

**Subsection catalog** (`regulation-subsections.json`, read-only):
`{ source, sourceDate: "2026-06-01", parts: { "61": { "61.103": [{ code, title }] }, "91": { ... } } }`. The JSON keys are section numbers. A section with no entry gets the single "Entire section" item.
