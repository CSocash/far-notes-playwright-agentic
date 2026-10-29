import re

import pytest
from playwright.sync_api import expect

from tests.mocks.routes import mock_login_rejected, mock_signed_out, serve_auth_pages_from_disk


@pytest.fixture(autouse=True)
def login_harness(page):
    """Every request is answered from disk or a stub, so these tests never touch the server."""
    serve_auth_pages_from_disk(page)
    mock_signed_out(page)


def test_tc_300_login_with_a_wrong_password(page, login_page):
    mock_login_rejected(page)
    login_page.goto()

    login_page.sign_in("pilot_existing", "definitely the wrong password")

    expect(login_page.error).to_have_text("Username or password is incorrect.")
    expect(login_page.password).to_be_focused()
    expect(page).to_have_url(re.compile(r"/login$"))


def test_tc_302_empty_login_fields_block_submission(page, login_page):
    login_requests = []
    mock_login_rejected(page, on_request=login_requests.append)
    login_page.goto()

    login_page.sign_in_button.click()

    assert login_page.username.evaluate("input => input.validity.valueMissing") is True
    expect(login_page.error).to_be_hidden()
    expect(page).to_have_url(re.compile(r"/login$"))
    assert login_requests == []


def test_tc_511_login_page_focus_and_the_error_state(page, login_page):
    mock_login_rejected(page)
    login_page.goto()

    expect(login_page.username).to_be_focused()

    login_page.sign_in("pilot_existing", "definitely the wrong password")

    expect(login_page.error).to_be_visible()
    expect(login_page.password).to_be_focused()
    expect(login_page.sign_in_button).to_be_enabled()
