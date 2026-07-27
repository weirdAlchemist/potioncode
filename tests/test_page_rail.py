"""Regression tests for the page-rail carousel arrows (index.html <-> projects.html).

The rails are thin strips pinned to the left/right edge of the viewport,
scoped to the content area (inside <main>) so they span only the hero and
never box in the navbar or footer. The body's matching left/right padding
reserves the gutter they live in. Guard both halves of that contract: the
rails must actually be clickable (nothing painted over them, echoing the
social-icon regression in test_hero.py) and the padding must actually reserve
the space so page content never ends up underneath a rail.
"""
import re

import pytest
from playwright.sync_api import Page, expect


def _open(page: Page, live_server: str, path: str) -> None:
    page.goto(f"{live_server}/{path}")
    page.add_style_tag(
        content="*, *::before, *::after { animation: none !important; transition: none !important; }"
    )


# (page, other page, label word used in both rail labels)
PAGES = [
    ("index.html", "projects.html", "Projects"),
    ("projects.html", "index.html", "Home"),
]


@pytest.mark.parametrize("path, target, label", PAGES)
def test_rails_are_present_and_clickable(page: Page, live_server: str, path, target, label):
    """Both rails point at the other page and actually receive clicks."""
    _open(page, live_server, path)

    left = page.get_by_label(f"Previous card: {label}")
    right = page.get_by_label(f"Next card: {label}")

    expect(left).to_have_attribute("href", target)
    expect(right).to_have_attribute("href", target)
    # trial=True: full hit-test, no navigation — fails if anything covers the rail.
    left.click(trial=True)
    right.click(trial=True)


@pytest.mark.parametrize("path, target, label", PAGES)
def test_clicking_rail_navigates_to_other_page(page: Page, live_server: str, path, target, label):
    _open(page, live_server, path)
    page.get_by_label(f"Next card: {label}").click()
    expect(page).to_have_url(re.compile(re.escape(target) + r"$"))


@pytest.mark.parametrize("path, _target, _label", PAGES)
def test_rails_hug_the_edges_of_the_content_area(page: Page, live_server: str, path, _target, _label):
    """Rails hug x=0 / the right edge and span only the content area between
    the navbar and footer — never boxing in the navbar or footer."""
    _open(page, live_server, path)
    viewport = page.viewport_size

    left_box = page.locator(".page-rail--left").bounding_box()
    right_box = page.locator(".page-rail--right").bounding_box()
    navbar = page.locator(".navbar").bounding_box()
    footer = page.locator(".footer").bounding_box()

    # Horizontally flush with the viewport edges.
    assert left_box["x"] == pytest.approx(0, abs=1)
    assert right_box["x"] + right_box["width"] == pytest.approx(viewport["width"], abs=1)

    # Vertically confined to the content area: start at/below the navbar's
    # bottom and end at/above the footer's top.
    nav_bottom = navbar["y"] + navbar["height"]
    footer_top = footer["y"]
    for box in (left_box, right_box):
        assert box["y"] >= nav_bottom - 1, (box, nav_bottom)
        assert box["y"] + box["height"] <= footer_top + 1, (box, footer_top)


@pytest.mark.parametrize("path, _target, _label", PAGES)
def test_navbar_and_footer_span_full_width(page: Page, live_server: str, path, _target, _label):
    """Navbar and footer run edge to edge. Only <main> carries the rail gutter
    (its left/right padding), so the chrome above and below the content is never
    inset by it, while hero content still clears the rails."""
    _open(page, live_server, path)
    vw = page.viewport_size["width"]
    rail_w = page.locator(".page-rail--left").bounding_box()["width"]

    for sel in (".navbar", ".footer"):
        box = page.locator(sel).bounding_box()
        assert box["x"] == pytest.approx(0, abs=1), (sel, box)
        assert box["x"] + box["width"] == pytest.approx(vw, abs=1), (sel, box)

    # The gutter that keeps content off the rails now lives on <main>, not body.
    pad_l, pad_r = page.eval_on_selector(
        "main",
        "m => { const s = getComputedStyle(m); return [parseFloat(s.paddingLeft), parseFloat(s.paddingRight)]; }",
    )
    assert pad_l >= rail_w - 1 and pad_r >= rail_w - 1, (pad_l, pad_r, rail_w)


def test_rail_labels_hide_on_narrow_viewports(page: Page, live_server: str):
    """Below 480px the rail shrinks and drops its rotated text label."""
    page.set_viewport_size({"width": 390, "height": 700})
    _open(page, live_server, "index.html")

    expect(page.locator(".page-rail__label").first).to_be_hidden()
    rail_w = page.locator(".page-rail--left").bounding_box()["width"]
    assert rail_w <= 40, rail_w
