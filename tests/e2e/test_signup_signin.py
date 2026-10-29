import pytest
from playwright.sync_api import expect

from tests.support.users import DEFAULT_PASSWORD, unique_id


@pytest.mark.smoke
def test_tc_002_sign_in_with_a_username(page, base_url, fresh_user, login_page, tracker_page):
    login_page.goto()

    login_page.sign_in(fresh_user["username"], fresh_user["password"])

    expect(page).to_have_url(f"{base_url}/")
    expect(tracker_page.current_user).to_have_text(fresh_user["username"])
    expect(tracker_page.brand_part).to_have_text("PART 91")
    expect(tracker_page.connection_status).to_have_text("Connected to SQLite")


@pytest.mark.smoke
def test_tc_001_create_an_account_through_the_ui(page, base_url, login_page, create_account_page):
    uid = unique_id()
    login_page.goto()
    login_page.create_account_link.click()
    expect(page).to_have_url(f"{base_url}/create-account")

    with page.expect_response(lambda r: r.url.endswith("/api/auth/register")) as register:
        create_account_page.create_account(f"pilot_{uid}", f"pilot_{uid}@test.com", DEFAULT_PASSWORD)

    assert register.value.status == 201
    assert register.value.json() == {"accountCreated": True}
    expect(create_account_page.form).to_be_hidden()
    expect(create_account_page.success).to_have_text(
        "Account created successfully. Return to the login page to sign in."
    )
    expect(create_account_page.return_to_login).to_have_attribute("href", "/login")


@pytest.mark.smoke
def test_tc_015_log_out(signed_in_page, base_url, tracker_page):
    page = signed_in_page
    # The app navigates to /login right after logout, and a response body can't be read once the
    # page has navigated away. So record it on the way through: route.fetch() sends the request to
    # the real server and the real response is passed on unchanged. An observer, not a stub.
    logout_responses = []

    def record_logout(route):
        response = route.fetch()
        logout_responses.append((response.status, response.json()))
        route.fulfill(response=response)

    page.route("**/api/auth/logout", record_logout)
    tracker_page.goto()

    tracker_page.log_out.click()

    expect(page).to_have_url(f"{base_url}/login")
    assert logout_responses == [(200, {"loggedOut": True})]
    assert page.request.get("/api/auth/me").json() == {"authenticated": False}
