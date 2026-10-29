import pytest

from tests.support.regulations import create_section, find_section, find_subsection, get_sections, patch_subsection
from tests.support.users import unique_id

EVIL = {"Origin": "http://evil.example"}
ORIGIN_REJECTED = {"error": "Request origin is not allowed."}


# Each case: (send the cross-origin request, then prove it had no effect).
# Bodies are otherwise valid, so the 403 can only come from the Origin check.
def _login(api, user):
    res = api.post("/api/auth/login", headers=EVIL, data={"username": user["username"], "password": user["password"]})
    return res, lambda: "set-cookie" not in res.headers


def _register(api, user):
    uid = unique_id()
    data = {"username": f"evil_{uid}", "email": f"evil_{uid}@test.com", "password": "correct horse battery staple"}
    res = api.post("/api/auth/register", headers=EVIL, data=data)
    # No account was created: logging in as it fails.
    return res, lambda: api.post("/api/auth/login", data={"username": data["username"], "password": data["password"]}).status == 401


def _logout(api, user):
    res = api.post("/api/auth/logout", headers=EVIL)
    return res, lambda: api.get("/api/regulations?part=91").status == 200   # session still valid


def _forgot_password(api, user):
    res = api.post("/api/auth/forgot-password", headers=EVIL, data={"email": user["email"]})
    return res, lambda: True   # its only effect is a console line, so the 403 is the whole check


def _reset_password(api, user):
    res = api.post("/api/auth/reset-password", headers=EVIL, data={"token": "a" * 64, "password": "a brand new long password"})
    return res, lambda: True


def _create_section(api, user):
    before = len(get_sections(api, "91"))
    res = api.post("/api/regulations?part=91", headers=EVIL, data={})
    return res, lambda: len(get_sections(api, "91")) == before


def _patch_section(api, user):
    section = create_section(api, "91", "91.999 — Origin test")
    res = api.patch(f"/api/regulations/{section['id']}?part=91", headers=EVIL, data={"regulation": "pwned"})
    return res, lambda: find_section(get_sections(api, "91"), "91.999")["regulation"] == "91.999 — Origin test"


def _patch_subsection(api, user):
    item = find_subsection(get_sections(api, "91"), "91.103(a)")
    res = api.patch(f"/api/subsections/{item['id']}?part=91", headers=EVIL, data={"covered": True, "notes": "pwned"})
    after = lambda: find_subsection(get_sections(api, "91"), "91.103(a)")
    return res, lambda: after()["covered"] is False and after()["notes"] == ""


CASES = {
    "POST /api/auth/login": _login,
    "POST /api/auth/register": _register,
    "POST /api/auth/logout": _logout,
    "POST /api/auth/forgot-password": _forgot_password,
    "POST /api/auth/reset-password": _reset_password,
    "POST /api/regulations": _create_section,
    "PATCH /api/regulations/:id": _patch_section,
    "PATCH /api/subsections/:id": _patch_subsection,
}


@pytest.mark.smoke
@pytest.mark.parametrize("endpoint", CASES)
def test_tc_206_cross_origin_writes_are_blocked(api, fresh_user, endpoint):
    res, had_no_effect = CASES[endpoint](api, fresh_user)

    assert res.status == 403
    assert res.json() == ORIGIN_REJECTED
    assert had_no_effect(), f"{endpoint} changed something despite the 403"
