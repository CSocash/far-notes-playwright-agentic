"""Direct access to the TEST database (.test-data/), for setup the API can't do.

Never point this at data/part91.sqlite. The server keeps running while tests write here; SQLite (WAL mode)
handles the two connections."""

import hashlib
import secrets
import sqlite3
import time
from contextlib import closing

RESET_MAX_AGE_MS = 30 * 60 * 1000


class ScratchDatabase:
    def __init__(self, path):
        assert path.parent.name == ".test-data", f"Refusing to touch a non-test database: {path}"
        self.path = path

    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    def user_id(self, username):
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        assert row, f"No user {username} in the test database"
        return row["id"]

    def seed_reset_token(self, username, expires_in_ms=RESET_MAX_AGE_MS):
        """Inserts a reset token the way forgot-password does (only its SHA-256 is stored) and
        returns the raw token, which is what the emailed/console link would carry."""
        token = secrets.token_hex(32)
        user_id = self.user_id(username)
        with closing(self._connect()) as connection, connection:
            connection.execute("DELETE FROM password_resets WHERE user_id = ?", (user_id,))
            connection.execute(
                "INSERT INTO password_resets (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                (hashlib.sha256(token.encode()).hexdigest(), user_id, int(time.time() * 1000) + expires_in_ms),
            )
        return token
