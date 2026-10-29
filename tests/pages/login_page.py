from playwright.sync_api import Page


class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username = page.get_by_label("Username or email")
        self.password = page.get_by_label("Password")
        self.sign_in_button = page.get_by_role("button", name="Sign in")
        self.error = page.get_by_role("alert")
        self.create_account_link = page.get_by_role("link", name="Create an account")

    def goto(self):
        self.page.goto("/login")

    def sign_in(self, identifier, password):
        self.username.fill(identifier)
        self.password.fill(password)
        self.sign_in_button.click()
