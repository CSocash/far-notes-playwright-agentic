import pytest

from tests.support.users import sign_in


@pytest.mark.smoke
def test_tc_126_a_password_reset_signs_the_user_out_everywhere(playwright, base_url, request_context, fresh_user, test_db):
    # Hook from the strategy: the reset token is seeded into the test database instead of being
    # read from the server console.
    session_a = playwright.request.new_context(base_url=base_url)
    session_b = playwright.request.new_context(base_url=base_url)
    try:
        for session in (session_a, session_b):
            sign_in(session, fresh_user["username"], fresh_user["password"])
            assert session.get("/api/regulations?part=91").status == 200   # control: both signed in

        token = test_db.seed_reset_token(fresh_user["username"])
        res = request_context.post("/api/auth/reset-password", data={"token": token, "password": "a brand new long passphrase"})
        assert res.status == 200
        assert res.json() == {"passwordUpdated": True}

        tracker = session_a.get("/", max_redirects=0)
        assert tracker.status == 302
        assert tracker.headers["location"] == "/login"

        api_call = session_b.get("/api/regulations?part=91")
        assert api_call.status == 401
        assert api_call.json() == {"error": "Sign in required."}
    finally:
        session_a.dispose()
        session_b.dispose()
