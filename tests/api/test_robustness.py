import pytest

from tests.support.regulations import create_section, find_subsection, get_sections, patch_subsection

NOT_FOUND = {"error": "Not found."}

# Source files, the catalog, the real database, git internals and traversal attempts.
# The client normalizes "/../" and "/%2e%2e/" to "/server.js"; the server must still refuse it.
FORBIDDEN_PATHS = [
    "/server.js",
    "/setup-user.js",
    "/package.json",
    "/regulation-subsections.json",
    "/data/part91.sqlite",
    "/../server.js",
    "/%2e%2e/server.js",
    "/.git/config",
]


@pytest.mark.smoke
@pytest.mark.parametrize("signed_in", [False, True], ids=["signed-out", "signed-in"])
@pytest.mark.parametrize("pathname", FORBIDDEN_PATHS)
def test_tc_221_only_allowlisted_files_are_served(request, request_context, pathname, signed_in):
    client = request.getfixturevalue("api") if signed_in else request_context

    res = client.get(pathname, max_redirects=0)

    assert res.status == 404
    assert res.json() == NOT_FOUND


# Supporting API checks for TC-211 and TC-212 (primary layer: component). The server must store
# HTML verbatim; the component tests prove the browser shows it as text.
def test_tc_211_heading_html_is_stored_verbatim(api):
    heading = '<img src=x onerror="window.__xss=1">91.1 test'

    created = create_section(api, "91", heading)

    assert created["regulation"] == heading
    assert heading in {section["regulation"] for section in get_sections(api, "91")}


def test_tc_212_note_html_is_stored_verbatim(api):
    note = "<script>window.__xss=1</script>"
    item = find_subsection(get_sections(api, "91"), "91.103(a)")

    res = patch_subsection(api, "91", item["id"], notes=note)

    assert res.status == 200
    assert find_subsection(get_sections(api, "91"), "91.103(a)")["notes"] == note
