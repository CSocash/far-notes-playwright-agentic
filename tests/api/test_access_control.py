import secrets

import pytest

from tests.support.regulations import create_section, find_section, find_subsection, get_sections, patch_subsection

SIGN_IN_REQUIRED = {"error": "Sign in required."}


@pytest.mark.smoke
@pytest.mark.parametrize("pathname", ["/", "/index.html", "/app.js", "/app-core.js"])
def test_tc_200_a_signed_out_visit_to_the_tracker_redirects_to_login(request_context, pathname):
    res = request_context.get(pathname, max_redirects=0)

    assert res.status == 302
    assert res.headers["location"] == "/login"
    assert res.headers["cache-control"] == "no-store"


@pytest.mark.smoke
def test_tc_201_signed_out_api_calls_are_rejected(request_context, other_user):
    # other_user owns real data, so "no data changes" can be checked afterwards.
    # request_context has no session cookie.
    owner = other_user["api"]
    item = find_subsection(get_sections(owner, "91"), "91.103(a)")
    sections_before = len(get_sections(owner, "91"))

    responses = {
        "GET /api/regulations": request_context.get("/api/regulations?part=91"),
        "POST /api/regulations": request_context.post("/api/regulations?part=91", data={}),
        "PATCH /api/subsections": request_context.patch(f"/api/subsections/{item['id']}?part=91", data={"covered": True}),
    }

    for call, res in responses.items():
        assert res.status == 401, call
        assert res.json() == SIGN_IN_REQUIRED, call
    after = get_sections(owner, "91")
    assert len(after) == sections_before
    assert find_subsection(after, "91.103(a)")["covered"] is False


@pytest.mark.parametrize("pathname", ["/login", "/create-account"])
def test_tc_202_a_signed_in_user_is_sent_away_from_the_login_and_sign_up_pages(api, pathname):
    res = api.get(pathname, max_redirects=0)

    assert res.status == 302
    assert res.headers["location"] == "/"


@pytest.mark.smoke
def test_tc_203_another_users_subsection_cant_be_changed(api, other_user):
    u1_item = find_subsection(get_sections(api, "91"), "91.103(a)")

    res = patch_subsection(other_user["api"], "91", u1_item["id"], covered=True, notes="pwned")

    assert res.status == 404
    assert res.json() == {"error": "Subsection not found."}
    unchanged = find_subsection(get_sections(api, "91"), "91.103(a)")
    assert unchanged["covered"] is False
    assert unchanged["notes"] == ""


@pytest.mark.smoke
def test_tc_204_another_users_section_heading_cant_be_changed(api, other_user):
    u1_section = create_section(api, "91", "91.999 — U1 private topic")

    res = other_user["api"].patch(f"/api/regulations/{u1_section['id']}?part=91", data={"regulation": "pwned"})

    assert res.status == 404
    assert res.json() == {"error": "Regulation not found."}
    assert find_section(get_sections(api, "91"), "91.999")["regulation"] == "91.999 — U1 private topic"


@pytest.mark.smoke
def test_tc_209_a_session_token_stops_working_after_logout(playwright, base_url, request_context, fresh_user):
    login = request_context.post("/api/auth/login", data={"username": fresh_user["username"], "password": fresh_user["password"]})
    old_cookie = login.headers["set-cookie"].split(";")[0]          # "study_session=<token>"
    replay = playwright.request.new_context(base_url=base_url, extra_http_headers={"Cookie": old_cookie})
    try:
        # Control: the hand-sent cookie works before logout, so the later 401 is caused by logout.
        assert replay.get("/api/regulations?part=91").status == 200
        assert request_context.post("/api/auth/logout").status == 200

        res = replay.get("/api/regulations?part=91")
        assert res.status == 401
        assert res.json() == SIGN_IN_REQUIRED
    finally:
        replay.dispose()


@pytest.mark.smoke
def test_tc_210_a_forged_session_cookie_is_rejected(playwright, base_url):
    forged = playwright.request.new_context(
        base_url=base_url, extra_http_headers={"Cookie": f"study_session={secrets.token_hex(32)}"}
    )
    try:
        page = forged.get("/", max_redirects=0)
        assert page.status == 302
        assert page.headers["location"] == "/login"

        api = forged.get("/api/regulations?part=91")
        assert api.status == 401
        assert api.json() == SIGN_IN_REQUIRED
    finally:
        forged.dispose()


@pytest.mark.smoke
def test_tc_222_extra_fields_cant_unlock_or_move_a_section(api):
    locked = find_section(get_sections(api, "91"), "91.103")
    custom = create_section(api, "91", "91.998 — Custom")

    res = api.patch(f"/api/regulations/{locked['id']}?part=91", data={"regulation": "x", "is_locked": 0})
    assert res.status == 403
    still_locked = find_section(get_sections(api, "91"), "91.103")
    assert still_locked["isLocked"] is True
    assert still_locked["regulation"] == "91.103 — Preflight action"

    res = api.patch(
        f"/api/regulations/{custom['id']}?part=91",
        data={"regulation": "y", "user_id": 1, "part": "61", "is_locked": 1},
    )
    assert res.status == 200
    part_91 = {section["id"]: section for section in get_sections(api, "91")}
    assert custom["id"] in part_91                                    # same owner, still in Part 91
    assert part_91[custom["id"]]["regulation"] == "y"
    assert part_91[custom["id"]]["isLocked"] is False
    assert custom["id"] not in {section["id"] for section in get_sections(api, "61")}
