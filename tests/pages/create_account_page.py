from playwright.sync_api import Page


class CreateAccountPage:
    def __init__(self, page: Page):
        self.page = page
        self.form = page.locator("#create-account-form")   # the form has no accessible name
        self.username = page.get_by_label("Username")
        self.email = page.get_by_label("Email address")
        self.password = page.get_by_label("Password")
        self.create_account_button = page.get_by_role("button", name="Create account")
        self.success = page.get_by_role("status")
        self.return_to_login = page.get_by_role("link", name="Return to the login page")

    def goto(self):
        self.page.goto("/create-account")

    def create_account(self, username, email, password):
        self.username.fill(username)
        self.email.fill(email)
        self.password.fill(password)
        self.create_account_button.click()
