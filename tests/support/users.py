"""API helpers for creating and signing in test users."""

import uuid

DEFAULT_PASSWORD = "correct horse battery staple"


def unique_id():
    return uuid.uuid4().hex[:10]


def register_user(request_context, **overrides):
    """Registers a user through the API. Does not sign in (register never sets a cookie)."""
    uid = unique_id()
    user = {"username": f"pilot_{uid}", "email": f"pilot_{uid}@test.com", "password": DEFAULT_PASSWORD, **overrides}
    res = request_context.post("/api/auth/register", data=user)
    assert res.status == 201, f"register {user['username']}: {res.status} {res.text()}"
    return user


def sign_in(request_context, identifier, password):
    """Signs a request context in. Its cookie jar keeps the session for later calls."""
    res = request_context.post("/api/auth/login", data={"username": identifier, "password": password})
    assert res.status == 200, f"login {identifier}: {res.status} {res.text()}"
    return res
