"""The API as the Capacitor app (mobile/) uses it: bearer tokens from app origins, plus CORS."""

import re
import secrets

import pytest

from tests.support.regulations import find_subsection, get_sections
from tests.support.users import sign_in

IOS_ORIGIN = "capacitor://localhost"
ANDROID_ORIGIN = "https://localhost"
EVIL_ORIGIN = "http://evil.example"
APP_CLIENT = {"X-Far-Notes-Client": "app"}
SIGN_IN_REQUIRED = {"error": "Sign in required."}
ORIGIN_REJECTED = {"error": "Request origin is not allowed."}


def app_headers(token, origin=IOS_ORIGIN):
    return {"Origin": origin, "Authorization": f"Bearer {token}"}


@pytest.fixture
def bare_context(playwright, base_url):
    """A request context that never holds a cookie, like the app's web view talking to the server."""
    context = playwright.request.new_context(base_url=base_url)
    yield context
    context.dispose()


@pytest.fixture
def app_token(playwright, base_url, fresh_user):
    """Signs fresh_user in the way the app does and returns the session token from the body."""
    context = playwright.request.new_context(base_url=base_url)
    res = context.post(
        "/api/auth/login",
        headers={**APP_CLIENT, "Origin": IOS_ORIGIN},
        data={"username": fresh_user["username"], "password": fresh_user["password"]},
    )
    assert res.status == 200, res.text()
    token = res.json()["token"]
    context.dispose()
    return token


def _subsection(context, headers, reference):
    res = context.get("/api/regulations?part=91", headers=headers)
    assert res.status == 200, res.text()
    return find_subsection(res.json(), reference)


@pytest.mark.mobile("ios")
def test_tc_020_the_app_signs_in_with_a_bearer_token(request_context, bare_context, fresh_user):
    res = request_context.post(
        "/api/auth/login",
        headers=APP_CLIENT,
        data={"username": fresh_user["username"], "password": fresh_user["password"]},
    )
    assert res.status == 200
    body = res.json()
    assert set(body) == {"username", "token"}
    assert re.fullmatch(r"[a-f0-9]{64}", body["token"])

    regs = bare_context.get("/api/regulations?part=91", headers=app_headers(body["token"]))
    assert regs.status == 200
    assert len(regs.json()) == 61
    assert regs.headers["access-control-allow-origin"] == IOS_ORIGIN


@pytest.mark.smoke
def test_tc_227_a_website_login_never_returns_the_session_token(request_context, fresh_user):
    res = sign_in(request_context, fresh_user["username"], fresh_user["password"])
    assert res.json() == {"username": fresh_user["username"]}
    assert re.match(r"study_session=[a-f0-9]{64}; .*HttpOnly", res.headers["set-cookie"])


@pytest.mark.smoke
@pytest.mark.mobile("ios")
def test_tc_228_requests_from_an_app_origin_ignore_the_session_cookie(api):
    before = find_subsection(get_sections(api, "91"), "91.103(a)")
    app_origin_cookie_only = {"Origin": IOS_ORIGIN}

    read = api.get("/api/regulations?part=91", headers=app_origin_cookie_only)
    assert read.status == 401
    assert read.json() == SIGN_IN_REQUIRED

    write = api.patch(f"/api/subsections/{before['id']}?part=91", headers=app_origin_cookie_only, data={"notes": "x"})
    assert write.status == 401
    assert write.json() == SIGN_IN_REQUIRED

    assert find_subsection(get_sections(api, "91"), "91.103(a)")["notes"] == before["notes"]


@pytest.mark.smoke
@pytest.mark.parametrize("origin", [
    pytest.param(IOS_ORIGIN, marks=pytest.mark.mobile("ios")),
    pytest.param(ANDROID_ORIGIN, marks=pytest.mark.mobile("android")),
])
def test_tc_229_cors_preflight_is_granted_to_app_origins(bare_context, origin):
    res = bare_context.fetch("/api/regulations?part=91", method="OPTIONS", headers={"Origin": origin})
    assert res.status == 204
    assert res.headers["access-control-allow-origin"] == origin
    assert res.headers["access-control-allow-methods"] == "GET, POST, PATCH"
    assert res.headers["access-control-allow-headers"] == "Content-Type, Authorization, X-Far-Notes-Client"
    assert "access-control-allow-credentials" not in res.headers


@pytest.mark.smoke
@pytest.mark.mobile()
def test_tc_229_cors_is_not_granted_to_other_origins(bare_context):
    preflight = bare_context.fetch("/api/regulations?part=91", method="OPTIONS", headers={"Origin": EVIL_ORIGIN})
    assert preflight.status == 403
    assert preflight.json() == ORIGIN_REJECTED
    assert "access-control-allow-origin" not in preflight.headers

    me = bare_context.get("/api/auth/me", headers={"Origin": EVIL_ORIGIN})
    assert "access-control-allow-origin" not in me.headers


@pytest.mark.mobile("ios")
def test_tc_230_the_app_can_write_with_a_bearer_token_but_other_origins_cannot(bare_context, app_token):
    item = _subsection(bare_context, app_headers(app_token), "91.103(a)")
    url = f"/api/subsections/{item['id']}?part=91"

    saved = bare_context.patch(url, headers=app_headers(app_token), data={"notes": "from the app"})
    assert saved.status == 200
    assert saved.json()["notes"] == "from the app"

    rejected = bare_context.patch(url, headers=app_headers(app_token, EVIL_ORIGIN), data={"notes": "evil"})
    assert rejected.status == 403
    assert rejected.json() == ORIGIN_REJECTED

    assert _subsection(bare_context, app_headers(app_token), "91.103(a)")["notes"] == "from the app"


@pytest.mark.mobile("ios")
def test_tc_231_logging_out_with_a_bearer_token_revokes_it(bare_context, app_token):
    # Control: the token works before logout.
    assert bare_context.get("/api/regulations?part=91", headers=app_headers(app_token)).status == 200

    out = bare_context.post("/api/auth/logout", headers=app_headers(app_token))
    assert out.status == 200
    assert out.json() == {"loggedOut": True}

    after = bare_context.get("/api/regulations?part=91", headers=app_headers(app_token))
    assert after.status == 401
    assert after.json() == SIGN_IN_REQUIRED


@pytest.mark.mobile("ios")
@pytest.mark.parametrize("token", ["abc", secrets.token_hex(32)], ids=["malformed", "unknown"])
def test_tc_232_malformed_or_unknown_bearer_tokens_are_rejected(bare_context, token):
    res = bare_context.get("/api/regulations?part=91", headers=app_headers(token))
    assert res.status == 401
    assert res.json() == SIGN_IN_REQUIRED

    me = bare_context.get("/api/auth/me", headers=app_headers(token))
    assert me.json() == {"authenticated": False}


def test_tc_233_api_client_js_loads_while_signed_out(bare_context):
    res = bare_context.get("/api-client.js")
    assert res.status == 200
    assert res.headers["content-type"] == "text/javascript; charset=utf-8"
