"""Keeps test browsers offline: only the server under test is reachable."""


def block_outside_requests(context, base_url):
    """Aborts every request from this browser context that doesn't go to base_url (Google Fonts, eCFR, ...).
    Page-level stubs in component tests are checked first, so they still answer their own requests."""
    context.route(lambda url: not url.startswith(f"{base_url}/"), lambda route: route.abort("blockedbyclient"))
