import pytest

from tests.support.server import TEST_DATA, ServerProcess
from tests.support.users import register_user

ISOLATED_PORT = 3200


@pytest.fixture(scope="module")
def isolated_server():
    """Rate limits live in server memory, so these tests get their own server process
    (rate limits ON, own database) instead of the shared test server that disables them."""
    server = ServerProcess(ISOLATED_PORT, TEST_DATA / f"isolated-{ISOLATED_PORT}.sqlite", rate_limit_disabled=False)
    yield server
    server.stop(remove_db=True)


@pytest.fixture
def isolated_request(playwright, isolated_server):
    context = playwright.request.new_context(base_url=isolated_server.base_url)
    yield context
    context.dispose()


def test_tc_217_login_is_rate_limited(isolated_request):
    user = register_user(isolated_request)

    for attempt in range(1, 9):
        res = isolated_request.post(
            "/api/auth/login", data={"username": user["username"], "password": "definitely the wrong password"}
        )
        assert res.status == 401, f"failed attempt {attempt}"

    ninth = isolated_request.post("/api/auth/login", data={"username": user["username"], "password": user["password"]})
    assert ninth.status == 429
    assert ninth.json() == {"error": "Too many sign-in attempts. Please wait 15 minutes and try again."}
    assert "set-cookie" not in ninth.headers
