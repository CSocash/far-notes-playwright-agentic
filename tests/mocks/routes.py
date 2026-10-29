"""Route helpers for component tests: serve real pages from disk and stub every API call."""

import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]

SHARED_ASSETS = {
    "/styles.css": "styles.css",
    "/aircraft-front-view.png": "aircraft-front-view.png",
    "/api-client.js": "api-client.js",
}

AUTH_PAGES = {
    "/login": "login.html",
    "/login.js": "login.js",
    "/create-account": "create-account.html",
    "/create-account.js": "create-account.js",
    "/forgot-password": "forgot-password.html",
    "/forgot-password.js": "forgot-password.js",
    "/reset-password": "reset-password.html",
    "/reset-password.js": "reset-password.js",
    **SHARED_ASSETS,
}

TRACKER_PAGES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/app-core.js": "app-core.js",
    "/app.js": "app.js",
    **SHARED_ASSETS,
}


def stub_external_fonts(page):
    """Keeps component tests offline and deterministic: Google Fonts get an empty response."""
    page.route(re.compile(r"fonts\.(googleapis|gstatic)\.com"), lambda route: route.fulfill(status=200, body=""))


def _serve_from_disk(page, files):
    stub_external_fonts(page)
    page.route(
        lambda url: urlparse(url).path in files,
        lambda route: route.fulfill(path=ROOT / files[urlparse(route.request.url).path]),
    )


def serve_auth_pages_from_disk(page):
    """Serves the real auth pages from disk, so component tests never reach the server."""
    _serve_from_disk(page, AUTH_PAGES)


def serve_tracker_from_disk(page):
    """Serves the real tracker page from disk. The "/" document is included, so the server's
    sign-in redirect never applies. Pair it with mock_signed_in and mock_regulations."""
    _serve_from_disk(page, TRACKER_PAGES)


def mock_signed_out(page):
    page.route("**/api/auth/me", lambda route: route.fulfill(json={"authenticated": False}))


def mock_signed_in(page, username="pilot_test"):
    page.route(
        "**/api/auth/me",
        lambda route: route.fulfill(json={"authenticated": True, "username": username, "email": f"{username}@test.com"}),
    )


def mock_regulations(page, by_part):
    """Answers GET /api/regulations?part=… with by_part[part] (a list of mock Section dicts)."""

    def handle(route):
        part = dict(p.split("=", 1) for p in urlparse(route.request.url).query.split("&") if "=" in p).get("part")
        route.fulfill(json=by_part.get(part, []))

    page.route(re.compile(r"/api/regulations\?part="), handle)


def mock_login_rejected(page, on_request=None):
    def handle(route):
        if on_request:
            on_request(route.request)
        route.fulfill(status=401, json={"error": "Username or password is incorrect."})

    page.route("**/api/auth/login", handle)


def mock_heading_saves(page, sections):
    """Answers PATCH /api/regulations/:id like the server: merges the new heading into the matching
    mock section and echoes it back. Returns the list of request bodies received, in order."""
    by_id = {section["id"]: section for section in sections}
    received = []

    def handle(route):
        body = route.request.post_data_json
        received.append(body)
        section_id = int(re.search(r"/api/regulations/(\d+)", route.request.url).group(1))
        by_id[section_id]["regulation"] = body["regulation"]
        route.fulfill(json=by_id[section_id])

    page.route(re.compile(r"/api/regulations/\d+\?part="), handle)
    return received
