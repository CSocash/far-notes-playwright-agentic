"""Builds the iOS app for device tests, pointed at the test server instead of the dev server on port 3000.

The bundled pages in mobile/ios/App/App/public are rebuilt for the test server, the app is built into
.test-data/ios-build, and the bundle is then rebuilt with the default settings, so Xcode keeps running
the normal app.
"""

import json
import os
import subprocess

from tests.support.server import ROOT, TEST_DATA

MOBILE = ROOT / "mobile"
BUILD_DIR = TEST_DATA / "ios-build"
APP_PATH = BUILD_DIR / "Build/Products/Debug-iphonesimulator/App.app"
BUNDLE_ID = "com.farnotes.studylog"


def _run(command, cwd, env=None):
    result = subprocess.run(command, cwd=cwd, env={**os.environ, **(env or {})}, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(command)} failed:\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}")


def _bundle_pages(api_url=None):
    env = {"FAR_NOTES_API_URL": api_url or ""}   # empty means the defaults in mobile/scripts/build-www.js
    _run(["npm", "run", "build", "--silent"], MOBILE, env)
    _run(["npx", "cap", "copy", "ios"], MOBILE, env)


def build_ios_app(api_url, simulator_udid):
    """Builds App.app for the simulator with api_url baked in, and returns its path."""
    try:
        _bundle_pages(api_url)
        _run(
            [
                "xcodebuild", "-project", "App.xcodeproj", "-scheme", "App", "-configuration", "Debug",
                "-destination", f"id={simulator_udid}", "-derivedDataPath", str(BUILD_DIR), "-quiet", "build",
            ],
            MOBILE / "ios/App",
        )
    finally:
        _bundle_pages()
    config = (APP_PATH / "public/config.js").read_text()
    assert json.dumps(api_url) in config, f"App.app was not built for {api_url}:\n{config}"
    return APP_PATH


def simulator_udid(name):
    """The id of the newest available iOS simulator with this name, e.g. "iPhone 17"."""
    result = subprocess.run(["xcrun", "simctl", "list", "devices", "available", "-j"], capture_output=True, text=True, check=True)
    runtimes = json.loads(result.stdout)["devices"]
    matches = [
        device["udid"]
        for runtime in sorted(runtimes, reverse=True)
        if "iOS" in runtime
        for device in runtimes[runtime]
        if device["name"] == name
    ]
    if not matches:
        raise RuntimeError(f"No available iOS simulator named {name!r}. Add one in Xcode › Window › Devices and Simulators.")
    return matches[0]
