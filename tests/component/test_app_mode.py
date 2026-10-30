"""The real pages in app mode: window.FAR_NOTES_CONFIG is set, as mobile/www/config.js does in the
Capacitor app. The API is stubbed under a /backend prefix, which proves requests use apiBase."""

import re

import pytest
from playwright.sync_api import expect

from tests.mocks.data import preflight
from tests.mocks.routes import serve_auth_pages_from_disk, serve_tracker_from_disk

pytestmark = pytest.mark.mobile()   # the same bundled pages run in both apps

TOKEN = "ab" * 32


def test_tc_021_in_app_mode_the_pages_use_the_bearer_token_and_bundled_links(page, login_page, tracker_page):
    page.add_init_script("window.FAR_NOTES_CONFIG = { apiBase: location.origin + '/backend' };")
    serve_auth_pages_from_disk(page)
    serve_tracker_from_disk(page)

    login_requests = []
    me_auth_headers = []

    def login(route):
        login_requests.append(route.request)
        route.fulfill(json={"username": "pilot_app", "token": TOKEN})

    def me(route):
        auth = route.request.headers.get("authorization")
        me_auth_headers.append(auth)
        signed_in = auth == f"Bearer {TOKEN}"
        route.fulfill(json={"authenticated": True, "username": "pilot_app", "email": "pilot_app@test.com"}
                      if signed_in else {"authenticated": False})

    page.route("**/backend/api/auth/login", login)
    page.route("**/backend/api/auth/me", me)
    page.route(re.compile(r"/backend/api/regulations\?part="), lambda route: route.fulfill(json=[preflight()]))

    login_page.goto()
    expect(login_page.create_account_link).to_have_attribute("href", "create-account.html")

    login_page.sign_in("pilot_app", "correct horse battery staple")

    expect(page).to_have_url(re.compile(r"/index\.html$"))
    expect(page.get_by_text("Connected to SQLite")).to_be_visible()
    assert len(login_requests) == 1
    assert login_requests[0].headers["x-far-notes-client"] == "app"
    # The login page's own check ran before sign-in (no token yet); the tracker's ran after it.
    assert me_auth_headers[0] is None
    assert me_auth_headers[-1] == f"Bearer {TOKEN}"
