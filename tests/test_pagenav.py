"""Regression tests for the page switcher (the tabs under the navbar).

This replaced the edge-rail carousel. The rails had their own suite because
they were positioned into the viewport gutters and could be covered; these
tabs are in normal flow, so the fragile parts are different: the tab widths
are fixed so the boxes stay uniform regardless of label, and the whole strip
has to stay welded to the navbar's bottom border while the page scrolls.
"""
import re

import pytest
from playwright.sync_api import Page, expect

ACCENT = "rgb(167, 139, 250)"   # --accent

# (path, label of the tab that should be marked current)
PAGES = [
    ("index.html", "Main"),
    ("projects.html", "Projects"),
    ("work.html", "Work"),
]

# Fixed across every page: the tabs must not reshuffle under the cursor.
ORDER = ["Projects", "Main", "Work"]
HREFS = {"Projects": "projects.html", "Main": "index.html", "Work": "work.html"}

# projects.html exists but isn't ready to be shown, so its tab is present but
# doesn't link anywhere. Drop this (and re-point the tab at projects.html) when
# the page goes live.
DISABLED = "Projects"


def _open(page: Page, live_server: str, path: str) -> None:
    page.goto(f"{live_server}/{path}")
    page.add_style_tag(
        content="*, *::before, *::after { animation: none !important; transition: none !important; }"
    )


@pytest.mark.parametrize("path, current", PAGES)
def test_every_page_has_the_same_tabs_in_the_same_order(page: Page, live_server: str, path, current):
    _open(page, live_server, path)
    assert page.locator(".pagenav__item").all_text_contents() == ORDER


@pytest.mark.parametrize("path, current", PAGES)
def test_tabs_are_uniform_width_regardless_of_label(page: Page, live_server: str, path, current):
    """"Projects" is more than twice as long as "Main" -- the boxes still have
    to match, so the strip doesn't jitter from page to page."""
    _open(page, live_server, path)
    widths = {
        round(page.locator(".pagenav__item").nth(i).bounding_box()["width"])
        for i in range(3)
    }
    assert len(widths) == 1, f"tab widths differ on {path}: {widths}"


@pytest.mark.parametrize("path, current", PAGES)
def test_current_page_tab_is_accented_and_not_a_link(page: Page, live_server: str, path, current):
    _open(page, live_server, path)
    tab = page.locator(".pagenav__item", has_text=current).first

    expect(tab).to_have_attribute("aria-current", "page")
    assert tab.evaluate("e => e.tagName") != "A", f"{current} tab is still a link on {path}"
    assert tab.evaluate("e => getComputedStyle(e).color") == ACCENT


@pytest.mark.parametrize("path, current", PAGES)
def test_other_tabs_link_to_their_pages_and_are_clickable(page: Page, live_server: str, path, current):
    _open(page, live_server, path)
    for label in ORDER:
        if label in (current, DISABLED):
            continue
        tab = page.locator(f".pagenav__item[href='{HREFS[label]}']")
        expect(tab).to_have_text(label)
        # Full hit-test without navigating: fails if anything covers the tab.
        tab.click(trial=True)


@pytest.mark.parametrize("path, current", PAGES)
def test_disabled_tab_is_shown_but_leads_nowhere(page: Page, live_server: str, path, current):
    """The Projects tab holds its place in the row -- so the switcher doesn't
    reflow when the page is turned back on -- without being reachable. On
    projects.html itself the tab is the current one instead, not disabled.
    """
    _open(page, live_server, path)
    tab = page.locator(".pagenav__item", has_text=DISABLED).first
    expect(tab).to_be_visible()

    if current == DISABLED:
        expect(tab).to_have_attribute("aria-current", "page")
        return

    assert tab.evaluate("e => e.tagName") == "SPAN", f"{DISABLED} is still a link on {path}"
    expect(tab).to_have_attribute("aria-disabled", "true")
    # Nothing anywhere on the page points at the hidden page.
    assert page.locator(f"a[href='{HREFS[DISABLED]}']").count() == 0


@pytest.mark.parametrize("path, current", PAGES)
def test_non_link_tabs_do_not_react_to_hover(page: Page, live_server: str, path, current):
    """:hover applies to spans too, so the hover rule is scoped to `a` -- a
    dead tab that lights up under the cursor reads as clickable."""
    _open(page, live_server, path)
    for tab in page.locator(".pagenav__item:not(a)").all():
        before = tab.evaluate("e => getComputedStyle(e).backgroundColor")
        tab.hover()
        page.wait_for_timeout(50)
        after = tab.evaluate("e => getComputedStyle(e).backgroundColor")
        assert before == after, (tab.inner_text(), before, after)


def test_clicking_a_tab_navigates(page: Page, live_server: str):
    _open(page, live_server, "index.html")
    page.locator(".pagenav__item[href='work.html']").click()
    expect(page).to_have_url(re.compile(r"work\.html$"))
    # ...and the destination marks itself as current.
    expect(page.locator(".pagenav__item--current")).to_have_text("Work")


def test_tabs_stay_attached_to_the_navbar_while_scrolling(page: Page, live_server: str):
    """The navbar is sticky. If only it were pinned, the tabs would scroll away
    and leave it floating with a bare border -- so the two are stuck as one
    block (.site-head) rather than the tabs carrying their own offset.
    """
    page.set_viewport_size({"width": 1280, "height": 800})
    _open(page, live_server, "work.html")
    page.add_style_tag(content="html { scroll-behavior: auto !important; }")

    def gap():
        nav = page.locator(".navbar").bounding_box()
        tab = page.locator(".pagenav__item").first.bounding_box()
        return round(tab["y"] - (nav["y"] + nav["height"]))

    before = gap()
    page.mouse.move(640, 400)
    page.mouse.wheel(0, 700)
    page.wait_for_timeout(300)

    assert page.evaluate("() => document.scrollingElement.scrollTop") > 0, "page didn't scroll"
    assert gap() == before, f"tabs detached from the navbar while scrolling ({before} -> {gap()})"
    # And the strip is still on screen at all.
    expect(page.locator(".pagenav")).to_be_in_viewport()
