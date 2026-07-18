"""Regression tests for the page-rail carousel arrows (index.html <-> projects.html).

The rails are fixed, full-height strips pinned to the left/right edge of the
viewport, with the body given matching left/right padding so the rails never
sit on top of the navbar, hero, or footer. Guard both halves of that contract:
the rails must actually be clickable (nothing painted over them, echoing the
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
def test_rails_are_fixed_at_the_viewport_edges(page: Page, live_server: str, path, _target, _label):
    """Rails span the full viewport height and hug x=0 / the right edge."""
    _open(page, live_server, path)
    viewport = page.viewport_size

    left_box = page.locator(".page-rail--left").bounding_box()
    right_box = page.locator(".page-rail--right").bounding_box()

    assert left_box["x"] == pytest.approx(0, abs=1)
    assert left_box["y"] == pytest.approx(0, abs=1)
    assert left_box["height"] == pytest.approx(viewport["height"], abs=1)

    assert right_box["x"] + right_box["width"] == pytest.approx(viewport["width"], abs=1)
    assert right_box["height"] == pytest.approx(viewport["height"], abs=1)


@pytest.mark.parametrize("path, _target, _label", PAGES)
def test_rails_do_not_cover_navbar_or_footer_content(page: Page, live_server: str, path, _target, _label):
    """The body's --rail-w padding must actually keep content clear of the rails."""
    _open(page, live_server, path)

    rail_w = page.locator(".page-rail--left").bounding_box()["width"]
    brand = page.locator(".brand-logo").bounding_box()
    footer = page.locator(".footer__inner").bounding_box()

    assert brand["x"] >= rail_w - 1, (brand, rail_w)
    assert footer["x"] >= rail_w - 1, (footer, rail_w)


def test_rail_labels_hide_on_narrow_viewports(page: Page, live_server: str):
    """Below 480px the rail shrinks and drops its rotated text label."""
    page.set_viewport_size({"width": 390, "height": 700})
    _open(page, live_server, "index.html")

    expect(page.locator(".page-rail__label").first).to_be_hidden()
    rail_w = page.locator(".page-rail--left").bounding_box()["width"]
    assert rail_w <= 40, rail_w
