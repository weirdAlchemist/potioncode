"""Cross-page document-level invariants.

Small stuff that isn't tied to any one page's layout, but that silently
changes how every other rule behaves when it regresses.
"""
import pytest
from playwright.sync_api import Page

# Every page that ships. projects.html is included even while it's unlinked:
# the file is still served, and this asserts a static property of it, not
# anything about being reachable.
PAGES = ["index.html", "projects.html", "work.html"]


@pytest.mark.parametrize("path", PAGES)
def test_page_renders_in_standards_mode(page: Page, live_server: str, path):
    """All three pages once lacked a <!DOCTYPE html> and rendered in quirks
    mode. Nothing looked broken -- it was spotted only because
    document.scrollingElement was <body> instead of <html> -- but quirks
    changes box-sizing and margin-collapsing underneath every other rule, so
    it's a trap waiting for the next layout change rather than a live bug.

    The doctype has to be the very first thing in the file; putting the
    licence comment above it is enough to lose standards mode in some
    browsers, which is exactly the kind of edit that looks harmless.
    """
    page.goto(f"{live_server}/{path}")
    assert page.evaluate("() => document.compatMode") == "CSS1Compat", (
        f"{path} is in quirks mode -- is <!DOCTYPE html> still the first line?"
    )
