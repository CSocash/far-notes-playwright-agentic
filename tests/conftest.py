from pathlib import Path
from urllib.parse import urlparse

import allure
import pytest

from tests.pages.create_account_page import CreateAccountPage
from tests.pages.login_page import LoginPage
from tests.pages.tracker_page import TrackerPage
from tests.support.db import ScratchDatabase
from tests.support.network import block_outside_requests
from tests.support.server import TEST_DATA, ServerProcess, is_up
from tests.support.users import register_user, sign_in

LAYER_MARKERS = ("api", "component", "e2e", "device")
LAYER_NAMES = {"api": "API", "component": "Component", "e2e": "E2E", "device": "Device"}
PLATFORM_NAMES = {"ios": "iOS", "android": "Android", None: "Both platforms"}
TEST_DB_PATH = TEST_DATA / "far-notes-test.sqlite"
DEV_SERVER_PORT = 3000   # npm start: the real data/part91.sqlite
LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1")


def pytest_addoption(parser):
    parser.addoption("--run-device", action="store_true",
                     help="also run tests/device: the iOS app in the Simulator through Appium (needs Xcode and Appium)")
    parser.addoption("--allow-dev-server", action="store_true",
                     help=f"allow --base-url on port {DEV_SERVER_PORT}, the dev server with your real data/part91.sqlite")


def pytest_sessionstart(session):
    """Refuses to run against the dev server on port 3000 unless --allow-dev-server is given.
    Tests create accounts and change data, and the dev server holds the real data/part91.sqlite."""
    config = session.config
    base_url = config.getoption("--base-url") or config.getini("base_url")
    if base_url and urlparse(base_url).port == DEV_SERVER_PORT and not config.getoption("--allow-dev-server"):
        raise pytest.UsageError(
            f"--base-url {base_url} is the dev server, which uses your real data/part91.sqlite. Tests would "
            f"create accounts and change data there. Run without --base-url to use the test server on port "
            f"3100, or add --allow-dev-server if you really mean it."
        )


def pytest_collection_modifyitems(config, items):
    """Marks each test with its layer from its folder, so `pytest -m api` works.
    Device tests are left out unless --run-device is given, so a plain run needs no Simulator."""
    deselected = []
    for item in items:
        parts = Path(item.fspath).parts
        for layer in LAYER_MARKERS:
            if layer in parts:
                item.add_marker(layer)
        if "device" in parts and not config.getoption("--run-device"):
            deselected.append(item)
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = [item for item in items if item not in deselected]


@pytest.fixture(autouse=True)
def report_groups(request):
    """Groups the Allure report as Web › layer › area, or Mobile › iOS / Android / Both platforms › layer.
    A test is mobile when it has the mobile marker; no effect when pytest runs without --alluredir."""
    node = request.node
    layer = next((LAYER_NAMES[m] for m in LAYER_NAMES if node.get_closest_marker(m)), "Other")
    mobile = node.get_closest_marker("mobile")
    if mobile:
        platform = mobile.args[0] if mobile.args else None
        allure.dynamic.parent_suite("Mobile")
        allure.dynamic.suite(PLATFORM_NAMES[platform])
        allure.dynamic.sub_suite(layer)
    else:
        allure.dynamic.parent_suite("Web")
        allure.dynamic.suite(layer)
        allure.dynamic.sub_suite(node.module.__name__.rsplit(".", 1)[-1].removeprefix("test_").replace("_", " ").capitalize())


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
    url = urlparse(base_url)
    if url.hostname not in LOCAL_HOSTS or url.port is None:
        pytest.exit(f"Nothing answers at {base_url}. A test server is started only for a local address with a "
                    f"port, such as http://127.0.0.1:3100; a remote server has to be running already.", returncode=4)
    port = url.port
    server = ServerProcess(port, TEST_DB_PATH, rate_limit_disabled=True, fresh_db=True)
    yield base_url
    server.stop(remove_db=True)


@pytest.fixture
def browser_context_args(browser_context_args):
    return {**browser_context_args, "timezone_id": "America/New_York", "locale": "en-US"}


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    # Playwright starts Chromium with --no-sandbox unless told otherwise; keep the sandbox on.
    return {**browser_type_launch_args, "chromium_sandbox": True}


@pytest.fixture
def context(context, base_url):
    """Every test's browser talks only to the test server, so tests stay offline and never load
    outside content into the browser. Contexts a test creates itself need block_outside_requests too."""
    block_outside_requests(context, base_url)
    return context


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
