import re
import time
import warnings

import pytest

from tests.support.users import register_user, unique_id

BAD_CREDENTIALS = "Username or password is incorrect."


def login(request_context, username, password):
    return request_context.post("/api/auth/login", data={"username": username, "password": password})


def test_tc_003_sign_in_with_an_email_address(request_context, fresh_user):
    res = login(request_context, fresh_user["email"], fresh_user["password"])

    assert res.status == 200
    assert res.json() == {"username": fresh_user["username"]}


def test_tc_125_sign_in_ignores_the_case_of_the_username_or_email(request_context):
    uid = unique_id()
    user = register_user(request_context, username=f"Pilot_{uid}", email=f"pilot_{uid}@test.com")

    by_upper_username = login(request_context, user["username"].upper(), user["password"])
    assert by_upper_username.status == 200
    assert by_upper_username.json() == {"username": f"Pilot_{uid}"}

    by_mixed_email = login(request_context, f"Pilot_{uid}@Test.com", user["password"])
    assert by_mixed_email.status == 200
    assert by_mixed_email.json() == {"username": f"Pilot_{uid}"}


def test_tc_129_the_session_cookie_lasts_7_days(request_context, fresh_user):
    res = login(request_context, fresh_user["username"], fresh_user["password"])

    assert res.status == 200
    assert re.fullmatch(
        r"study_session=[0-9a-f]{64}; Path=/; HttpOnly; SameSite=Strict; Max-Age=604800",
        res.headers["set-cookie"],
    )


@pytest.mark.smoke
def test_tc_213_sql_injection_in_the_login_identifier_fails(request_context, fresh_user):
    # fresh_user guarantees at least one account exists for the injection to target.
    assert fresh_user["username"]

    res = login(request_context, "' OR '1'='1' --", "anything at all here")

    assert res.status == 401
    assert res.json() == {"error": BAD_CREDENTIALS}
    assert "set-cookie" not in res.headers


def test_tc_215_login_errors_dont_reveal_whether_an_account_exists(request_context, fresh_user, record_property):
    started = time.perf_counter()
    wrong_password = login(request_context, fresh_user["username"], "definitely the wrong password")
    wrong_password_ms = (time.perf_counter() - started) * 1000

    started = time.perf_counter()
    unknown_user = login(request_context, f"nobody_{unique_id()}", "definitely the wrong password")
    unknown_user_ms = (time.perf_counter() - started) * 1000

    assert wrong_password.status == 401
    assert unknown_user.status == 401
    assert wrong_password.json() == {"error": BAD_CREDENTIALS}
    assert unknown_user.json() == {"error": BAD_CREDENTIALS}

    # "Similar response time": both paths run scrypt. Recorded, and only a warning (not a failure),
    # because wall-clock timing is noisy.
    record_property("wrong_password_ms", round(wrong_password_ms))
    record_property("unknown_user_ms", round(unknown_user_ms))
    ratio = max(wrong_password_ms, unknown_user_ms) / max(1, min(wrong_password_ms, unknown_user_ms))
    if ratio >= 5:
        warnings.warn(f"TC-215 response times differ {ratio:.1f}x ({wrong_password_ms:.0f} vs {unknown_user_ms:.0f} ms)")


def test_tc_301_login_with_an_unknown_user(request_context):
    res = login(request_context, f"nobody_{unique_id()}", "correct horse battery staple")

    assert res.status == 401
    assert res.json() == {"error": BAD_CREDENTIALS}


def test_tc_406_passwords_are_not_trimmed(request_context):
    user = register_user(request_context, password="  correct horse battery  ")

    trimmed = login(request_context, user["username"], "correct horse battery")
    assert trimmed.status == 401

    exact = login(request_context, user["username"], "  correct horse battery  ")
    assert exact.status == 200


def test_tc_427_the_login_identifier_is_trimmed(request_context, fresh_user):
    res = login(request_context, f"  {fresh_user['username']}  ", fresh_user["password"])

    assert res.status == 200
    assert res.json() == {"username": fresh_user["username"]}


@pytest.mark.smoke
def test_tc_208_page_scripts_cant_read_the_session_cookie(request_context, fresh_user):
    # Strategy rule 7: proved at the API layer by the cookie attributes. HttpOnly is what stops
    # document.cookie from exposing it; the browser's enforcement of HttpOnly is trusted.
    res = login(request_context, fresh_user["username"], fresh_user["password"])

    assert res.status == 200
    attributes = [part.strip() for part in res.headers["set-cookie"].split(";")]
    assert attributes[0].startswith("study_session=")
    assert "HttpOnly" in attributes
    assert "SameSite=Strict" in attributes
