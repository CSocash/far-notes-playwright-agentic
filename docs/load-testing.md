# Load Testing Notes

Notes from setting up the first load test for FAR Notes with [Locust](https://locust.io), a Python load testing tool. The script is `tests/load/locustfile.py`.

The app server is Node (`server.js`), but load testing only sends HTTP requests, so the server's language doesn't matter. Locust fits because the rest of the test suite is Python.

## 1. What load testing measures

A load test runs many simulated users against the server at the same time and watches three numbers:

| Metric | Meaning | Example goal |
|---|---|---|
| **RPS** (requests per second) | Throughput: how much work the server handles | — |
| **p95 latency** | 95% of requests finished faster than this | under 200 ms |
| **Error rate** | Share of requests that failed | 0% |

Common kinds, all using the same script with different settings:

- **Load test:** expected traffic. "Does it handle 20 users?"
- **Stress test:** keep adding users until it breaks. "Where's the limit?"
- **Spike test:** a sudden jump in users.
- **Soak test:** steady traffic for an hour or more. "Does it slow down over time?"

## 2. Setup

Locust is kept out of `requirements-dev.txt`, because CI doesn't need it:

```bash
.venv/bin/pip install -r requirements-load.txt
```

## 3. Running it

**Run every command from the project folder.** Keep the quotes, because the path has a space in it:

```bash
cd "/Users/conniesocash/Documents/Programming/Playwright Projects/far-notes-playwright-agentic"
```

**Terminal 1: start a throwaway server.** Never load test port 3000, which writes to the real `data/part91.sqlite`.

```bash
FAR_NOTES_DB=.test-data/load.sqlite FAR_NOTES_DISABLE_RATE_LIMIT=1 PORT=3200 npm start
```

- `FAR_NOTES_DB` points the server at a separate database. `.test-data/` is gitignored.
- `FAR_NOTES_DISABLE_RATE_LIMIT=1` is required. Otherwise login returns 429 after 8 attempts in 15 minutes and the results mean nothing.
- `PORT=3200` keeps it away from the dev server (3000) and the pytest server (3100).

**Terminal 2: start Locust.**

```bash
.venv/bin/locust -f tests/load/locustfile.py --host http://127.0.0.1:3200
```

Open http://localhost:8089, set **10 users** with a **ramp up of 2 per second**, and let it run for at least a minute.

Without the browser UI (prints a summary at the end):

```bash
.venv/bin/locust -f tests/load/locustfile.py --host http://127.0.0.1:3200 --headless -u 10 -r 2 -t 30s --only-summary
```

Each run adds `load_...` accounts to `.test-data/load.sqlite`. Delete that file whenever you want a fresh start.

### Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `npm error enoent Could not read package.json: ... /Users/conniesocash/package.json` | The command ran from the home folder, not the project | `cd` into the project first (see above) |
| `register` / `login` show 429s | Rate limiting is on | Restart the server with `FAR_NOTES_DISABLE_RATE_LIMIT=1` |

## 4. The script, line by line

### Imports and constant

```python
import random                                   # pick a random subsection to save
import uuid                                     # make unique usernames
from locust import HttpUser, between, task      # Locust's building blocks

PASSWORD = "load-test-password-123"  # 15+ characters, like the app requires
```

- `HttpUser`: the blueprint for one simulated person who sends HTTP requests.
- `between`: a helper for "wait a random amount of time."
- `task`: a **decorator** (the `@` thing) that marks a method as an action the user repeats.
- `PASSWORD`: one shared password for all fake users. The ALL CAPS name means it never changes. It must be at least 15 characters, or register returns 400.

### The user class

```python
class StudyUser(HttpUser):
    wait_time = between(1, 3)
```

- `StudyUser(HttpUser)` **inherits** from `HttpUser`, so it gets `self.client`, an HTTP client like `requests`.
- Starting 10 users creates 10 separate `StudyUser` objects, each with its own client and cookies.
- `wait_time = between(1, 3)` is **think time**: after each task the user pauses for a random 1 to 3 seconds, like a real person.
- Sanity check: 10 users at about 2 seconds each ≈ **5 requests per second**.

### Setup for each user: `on_start`

```python
def on_start(self):
    name = f"load_{uuid.uuid4().hex[:12]}"
    self.client.post("/api/auth/register",
                     json={"username": name, "email": f"{name}@example.test", "password": PASSWORD})
    self.client.post("/api/auth/login", json={"username": name, "password": PASSWORD})

    sections = self.client.get("/api/regulations?part=91").json()
    self.subsection_ids = [sub["id"] for section in sections for sub in section["subsections"]]
```

- `on_start` runs **once** per simulated user, like a pytest fixture.
- `name` builds a unique username such as `load_3f2a9c1e7b04`. `uuid4()` is a random ID, `.hex` drops the dashes, `[:12]` keeps it short, and the `f"..."` **f-string** inserts it.
- Paths have no host. Locust adds the `--host` from the command line.
- `json=` turns the dict into a JSON body and sets `Content-Type: application/json`.
- `example.test` is reserved for testing, so it can never be a real address.
- After login, `self.client` stores the `study_session` cookie and sends it on every later request, the same way a browser does. That's how the regulation calls get past the 401 check.
- No `Origin` header is sent. That's allowed: `isAllowedOrigin` in `server.js` only blocks a **foreign** origin.
- The last two lines fetch this user's Part 91 list and collect every subsection id into one flat list. Written as a normal loop:

  ```python
  ids = []
  for section in sections:
      for sub in section["subsections"]:
          ids.append(sub["id"])
  self.subsection_ids = ids
  ```

  Each user keeps only **its own** ids. Patching another user's id returns 404.

### Tasks and weights

```python
@task(5)
def view_part_91(self):
    self.client.get("/api/regulations?part=91")

@task(2)
def view_part_61(self):
    self.client.get("/api/regulations?part=61")

@task(3)
def mark_subsection_covered(self):
    sub_id = random.choice(self.subsection_ids)
    self.client.patch(f"/api/subsections/{sub_id}?part=91",
                      json={"covered": True},
                      name="/api/subsections/[id]")
```

- `@task(n)` marks an action the user repeats. `n` is its **weight**.
- The weights add up to 10, so each pick is **50%** view Part 91, **20%** view Part 61 and **30%** save.
- `random.choice` spreads writes across different rows instead of hitting the same one.
- The PATCH is the same request `app.js` sends when someone ticks a checkbox. `?part=91` must match the part the id came from, or the server returns 404.

### What one simulated user does

1. Register a new account
2. Log in and keep the cookie
3. Fetch Part 91 and save its subsection ids
4. Loop until Stop: pick a task by weight → run it → wait 1 to 3 seconds → repeat

## 5. What `name=` does

Locust's report has **one row per URL**, grouped by the exact URL text.

The GET tasks always hit the same URL, so each gets one row. The PATCH has the id **inside the URL**, so every save is a different URL:

- `/api/subsections/412?part=91`
- `/api/subsections/87?part=91`
- `/api/subsections/1530?part=91`

**Without `name=`**, each id gets its own row with one or two requests, which is too few to mean anything:

| Name | # Requests | Median (ms) |
|---|---|---|
| /api/subsections/412?part=91 | 1 | 5 |
| /api/subsections/87?part=91 | 2 | 6 |
| *...hundreds more rows...* | 1 | ... |

**With `name="/api/subsections/[id]"`**, they all go in one row:

| Name | # Requests | Median (ms) |
|---|---|---|
| /api/subsections/[id] | 180 | 5 |

- `[id]` is just text, not special syntax. `name="save subsection"` would work the same.
- It only changes the report. The server still gets the real URL.
- **Rule of thumb:** add `name=` whenever part of the URL changes from one request to the next.

## 6. Reading the results

### Columns in the Statistics tab

| Column | Meaning |
|---|---|
| # Requests / # Fails | How many were sent / how many failed |
| Median | Half were faster than this |
| 95%ile | 95% were faster than this. **The column people usually set goals on.** |
| 99%ile | 99% were faster than this. Shows the worst cases. |
| Min / Max | Fastest and slowest |
| Average size | Bytes returned per response |
| Current RPS | Requests per second right now |

**Percentiles need volume.** With only 1 to 6 requests, the median, 95th percentile and max are close to the same number. You need dozens or hundreds of requests before percentiles tell you anything.

### First baseline (2026-11-06, 10 users, ramp up 2/s, 30 s, headless)

| Request | Count | Median | 95th percentile |
|---|---|---|---|
| POST /api/auth/register | 10 | 36 ms | 42 ms |
| POST /api/auth/login | 10 | 25 ms | 26 ms |
| GET /api/regulations?part=91 | 85 | 5 ms | 7 ms |
| GET /api/regulations?part=61 | 24 | 5 ms | 6 ms |
| PATCH /api/subsections/[id] | 42 | 4 ms | 5 ms |
| **Total** | **171** | **5 ms** | **26 ms** |

0 failures, about **5.75 requests per second**.

### What we learned

- **The task mix came close to the weights:** about 56/16/28 against a target of 50/20/30. It's random, so short runs drift a little.
- **RPS matched the estimate** (10 users with about 2 seconds of think time ≈ 5 per second).
- **register and login are 5 to 10 times slower than everything else.** That's intended. `server.js` hashes passwords with scrypt, which is deliberately slow so stolen hashes are hard to crack. Node runs async scrypt on a small pool of worker threads (4 by default), so logins queue up when many users arrive at once. This is the first thing expected to slow down as users increase.
- **Response size matters too.** The Part 91 list is about **45 KB** and Part 61 about **33 KB**, because every GET returns the whole list with all subsections. That's fine on a laptop, but on a slow phone connection size can matter more than server speed. Load testing isn't only about time.
- **A run with 1 user** only shows one register and one login, and might not include a PATCH at all, since saving is only picked 30% of the time.

## 7. Known gap: no response checks

The script never checks a response. Locust counts a request as failed only on a 4xx/5xx status or a broken connection. If `register` returned a 400, Locust would log one failure, but `on_start` would carry on. Then `.json()` would crash on the 401 error body that comes back instead of a list.

## 8. Next steps

1. **Add response checks** (`catch_response=True`) so a bad response counts as a failure with a clear message instead of crashing the script.
2. **Stress run:** add users until the register and login times climb, to find the scrypt limit.
3. **Headless run with a CSV report** (`--csv`), so results can be compared between runs.
4. **Pass/fail thresholds** (for example p95 under 200 ms and 0% errors), so the load test can pass or fail like a real test.
