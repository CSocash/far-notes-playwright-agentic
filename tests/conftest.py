from pathlib import Path

import pytest

from tests.pages.create_account_page import CreateAccountPage
from tests.pages.login_page import LoginPage
from tests.pages.tracker_page import TrackerPage
from tests.support.db import ScratchDatabase
from tests.support.server import TEST_DATA, ServerProcess, is_up
from tests.support.users import register_user, sign_in

LAYER_MARKERS = ("api", "component", "e2e")
TEST_DB_PATH = TEST_DATA / "far-notes-test.sqlite"


def pytest_collection_modifyitems(items):
    """Marks each test with its layer from its folder, so `pytest -m api` works."""
    for item in items:
        parts = Path(item.fspath).parts
        for layer in LAYER_MARKERS:
            if layer in parts:
                item.add_marker(layer)


@pytest.fixture(scope="session", autouse=True)
def test_server(base_url):
    """The shared test server: its own database and the rate limits switched off.

    Never the dev server on port 3000 or data/part91.sqlite. If something already answers on
    base_url (for example a test server you started yourself), it is reused.
    Each run starts from an empty database and deletes it afterwards: every test makes its own users,
    and a database kept across runs grew until the server's start-up checks took longer than 15s.
    """
    if is_up(base_url):
        yield base_url
        return
    port = int(base_url.rsplit(":", 1)[1])
    server = ServerProcess(port, TEST_DB_PATH, rate_limit_disabled=True, fresh_db=True)
    yield base_url
    server.stop(remove_db=True)


@pytest.fixture
def browser_context_args(browser_context_args):
    return {**browser_context_args, "timezone_id": "America/New_York", "locale": "en-US"}


@pytest.fixture
def request_context(playwright, base_url):
    """A fresh APIRequestContext per test, with its own cookie jar."""
    context = playwright.request.new_context(base_url=base_url)
    yield context
    context.dispose()


@pytest.fixture
def fresh_user(request_context):
    return register_user(request_context)


@pytest.fixture
def api(request_context, fresh_user):
    """A request context signed in as fresh_user."""
    sign_in(request_context, fresh_user["username"], fresh_user["password"])
    return request_context


@pytest.fixture
def other_user(playwright, base_url):
    """A second registered user, for isolation tests. Uses its own request context."""
    context = playwright.request.new_context(base_url=base_url)
    user = register_user(context)
    sign_in(context, user["username"], user["password"])
    yield {**user, "api": context}
    context.dispose()


@pytest.fixture
def test_db():
    """Direct access to the test server's database, for setup the API can't do (reset tokens).
    Assumes the server on base_url uses TEST_DB_PATH, which is true when test_server started it."""
    return ScratchDatabase(TEST_DB_PATH)


@pytest.fixture
def signed_in_page(page, fresh_user):
    """A browser page signed in as fresh_user through the API (page.request shares the context's cookies)."""
    res = page.request.post("/api/auth/login", data={"username": fresh_user["username"], "password": fresh_user["password"]})
    assert res.status == 200, f"login {fresh_user['username']}: {res.status} {res.text()}"
    return page


@pytest.fixture
def create_account_page(page):
    return CreateAccountPage(page)


@pytest.fixture
def login_page(page):
    return LoginPage(page)


@pytest.fixture
def tracker_page(page):
    return TrackerPage(page)
