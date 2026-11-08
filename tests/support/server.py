"""Start and stop FAR Notes server processes for tests, always against a throwaway database."""

import os
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST_DATA = ROOT / ".test-data"


def is_up(base_url):
    try:
        with urllib.request.urlopen(f"{base_url}/login", timeout=1):
            return True
    except urllib.error.HTTPError:
        return True  # The server answered, just not with 2xx.
    except OSError:
        return False


def port_in_use(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


class ServerProcess:
    def __init__(self, port, db_path, rate_limit_disabled, fresh_db=False):
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"
        self.db_path = Path(db_path)
        # Without this check the new server fails to start, but the readiness check below gets an answer
        # from whatever already holds the port, and the tests silently run against the wrong server.
        if port_in_use(port):
            raise RuntimeError(f"Port {port} is already in use, so this test server can't start. "
                               f"Stop whatever is running there (lsof -nP -iTCP:{port} -sTCP:LISTEN), "
                               f"for example a server left over from a manual or load test run.")
        if fresh_db:
            self._remove_db()
        env = {
            **os.environ,
            "PORT": str(port),
            "FAR_NOTES_DB": str(self.db_path),
            "FAR_NOTES_DISABLE_RATE_LIMIT": "1" if rate_limit_disabled else "",
        }
        self.process = subprocess.Popen(
            ["node", "server.js"], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        self._wait_until_ready()

    def _wait_until_ready(self, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(f"Server on port {self.port} exited early:\n{self.process.stdout.read()}")
            if is_up(self.base_url):
                return
            time.sleep(0.1)  # Polling the process start-up, not inside a test.
        self.stop()
        raise RuntimeError(f"Server on port {self.port} did not start within {timeout}s")

    def stop(self, remove_db=False):
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
        if remove_db:
            self._remove_db()

    def _remove_db(self):
        for suffix in ("", "-wal", "-shm"):
            Path(f"{self.db_path}{suffix}").unlink(missing_ok=True)
