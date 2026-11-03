"""The iOS app's screens for Appium, found by the accessibility labels VoiceOver reads.

The web view exposes the pages' accessible names to iOS, so these match the names the Playwright page
objects use: "Mark 91.103(a) as covered" is a switch, "Sign in" a button, and so on.
"""

import time

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from tests.support.ios_app import BUNDLE_ID


class IosApp:
    def __init__(self, driver, timeout=15, slowmo_ms=0):
        self.driver = driver
        self.timeout = timeout
        self.slowmo = slowmo_ms / 1000

    def pause(self):
        """Slow mode (`--slowmo 1000`): a pause after each action, so a person can follow the run."""
        if self.slowmo:
            time.sleep(self.slowmo)

    def tap(self, element):
        element.click()
        self.pause()

    def type_into(self, element, text):
        element.send_keys(text)
        self.pause()

    def element(self, kind, label):
        """An element by its type and accessibility label, e.g. ("Button", "Sign in")."""
        predicate = f"type == 'XCUIElementType{kind}' AND label == '{label}'"
        return WebDriverWait(self.driver, self.timeout).until(
            lambda driver: driver.find_element(AppiumBy.IOS_PREDICATE, predicate)
        )

    def wait_for_value(self, element, value):
        """Waits for an element's accessibility value, e.g. a switch turning "1"; returns the last value seen."""
        try:
            WebDriverWait(self.driver, self.timeout).until(lambda _: element.get_attribute("value") == value)
        except TimeoutException:
            pass   # the test's assertion reports the value it got
        return element.get_attribute("value")

    # Sign-in screen
    def sign_in(self, username, password):
        self.type_into(self.element("TextField", "Username or email"), username)
        self.type_into(self.element("SecureTextField", "Password"), password)
        self.tap(self.element("Button", "Sign in"))

    # Tracker
    def wait_for_tracker(self):
        status = self.element("StaticText", "Connected to SQLite")
        self.pause()
        return status

    def section_toggle(self, heading):
        return self.element("Button", f"Study items in {heading}")

    def covered_switch(self, reference):
        """The checkbox itself, for reading its value ("0" or "1"). It's a 1px hidden input, so iOS can't tap it."""
        return self.element("Switch", f"Mark {reference} as covered")

    def covered_control(self, reference):
        """What a person taps to mark an item covered: the checkmark box and its Yes/No label.
        It has no label of its own, so it's found as the switch's parent (the only XPath here)."""
        self.covered_switch(reference)
        return self.driver.find_element(AppiumBy.XPATH, f"//XCUIElementTypeSwitch[@label='Mark {reference} as covered']/..")

    def relaunch(self):
        """Quits the app and opens it again, like swiping it away and tapping its icon."""
        self.driver.terminate_app(BUNDLE_ID)
        self.pause()
        self.driver.activate_app(BUNDLE_ID)
        self.pause()
