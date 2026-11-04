"""Device tests: the real iOS app in the Simulator, driven by Appium. They run only with `pytest --run-device`.

Needs Xcode, Appium 3 with the XCUITest driver (`appium driver install xcuitest`) and the iPhone 17
simulator. Appium is started here if nothing is listening on APPIUM_URL. The app is rebuilt each session
against the shared test server (port 3100), never the dev server on port 3000.
"""

import json
import subprocess
import time
import urllib.request

import pytest
from appium import webdriver
from appium.options.ios import XCUITestOptions

from tests.pages.ios_app import IosApp
from tests.support.ios_app import BUNDLE_ID, build_ios_app, simulator_udid

APPIUM_URL = "http://127.0.0.1:4723"
SIMULATOR = "iPhone 17"   # not the simulator Xcode runs the app on, so a test run doesn't replace that copy


def _appium_is_up():
    try:
        with urllib.request.urlopen(f"{APPIUM_URL}/status", timeout=1) as res:
            return json.load(res)["value"]["ready"]
    except OSError:
        return False


@pytest.fixture(scope="session")
def appium_server():
    if _appium_is_up():
        yield APPIUM_URL
        return
    # --address keeps Appium on this Mac; by default it listens on every network address, without a password.
    process = subprocess.Popen(["appium", "--address", "127.0.0.1", "--port", APPIUM_URL.rsplit(":", 1)[1],
                                "--log-level", "warn"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + 30
    while not _appium_is_up():
        if process.poll() is not None or time.monotonic() > deadline:
            process.kill()
            raise RuntimeError("Appium did not start. Is it installed (`npm install -g appium`)?")
        time.sleep(0.2)   # polling start-up, not inside a test
    yield APPIUM_URL
    process.terminate()


@pytest.fixture(scope="session")
def ios_simulator():
    return simulator_udid(SIMULATOR)


@pytest.fixture(scope="session")
def ios_app_path(test_server, ios_simulator):
    return build_ios_app(test_server, ios_simulator)


@pytest.fixture
def ios_app(request, appium_server, ios_simulator, ios_app_path):
    """A fresh install of the app (no saved sign-in), wrapped in the IosApp screen object."""
    subprocess.run(["xcrun", "simctl", "uninstall", ios_simulator, BUNDLE_ID], capture_output=True)
    options = XCUITestOptions()
    options.udid = ios_simulator
    options.app = str(ios_app_path)
    options.bundle_id = BUNDLE_ID
    options.set_capability("appium:wdaLaunchTimeout", 240_000)   # the first run builds WebDriverAgent
    driver = webdriver.Remote(appium_server, options=options)
    app = IosApp(driver, slowmo_ms=float(request.config.getoption("slowmo") or 0))
    yield app
    app.pause()   # in slow mode, leave the final screen up for a moment
    driver.quit()
