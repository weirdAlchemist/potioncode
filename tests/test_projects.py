"""Regression tests for the projects.html orbit page.

Covers the two pieces of interactive functionality added with the page:
the flask doubling as a GitHub link, and the five project nodes whose detail
panel is revealed on hover/focus. As with test_hero.py, actionability is
checked with a trial click rather than a DOM-presence check, since a
sibling element silently covering a target is exactly the kind of bug a
plain "is it in the document" assertion misses.
"""
import re

import pytest
from playwright.sync_api import Page, expect


def _open(page: Page, live_server: str) -> None:
    page.goto(f"{live_server}/projects.html")
    page.add_style_tag(
        content="*, *::before, *::after { animation: none !important; transition: none !important; }"
    )


# --- Flask-as-GitHub-link ----------------------------------------------------

def test_flask_is_a_clickable_github_link(page: Page, live_server: str):
    _open(page, live_server)
    # exact=True: the project nodes are also labelled "... on GitHub".
    link = page.get_by_label("GitHub", exact=True)
    expect(link).to_have_attribute("href", re.compile("github.com"))
    expect(link).to_have_attribute("target", "_blank")
    # trial=True: full hit-test, no navigation — fails if anything covers the flask.
    link.click(trial=True)


def test_hovering_flask_link_brightens_the_brand_icon(page: Page, live_server: str):
    """Sanity check that the hover affordance CSS actually applies to this element."""
    _open(page, live_server)
    link = page.get_by_label("GitHub", exact=True)
    icon = page.locator(".flask__brand-icon")

    before = icon.evaluate("el => getComputedStyle(el).fill")
    link.hover()
    after = icon.evaluate("el => getComputedStyle(el).fill")
    assert before != after, "expected .flask__brand-icon fill to change on hover"


# --- Project nodes -----------------------------------------------------------

# (display name, repo URL) — one per orbit node.
PROJECTS = [
    ("PotionCode", "https://github.com/weirdAlchemist/potioncode"),
    ("ChainTimer", "https://github.com/weirdAlchemist/ChainTimer"),
    ("MicroServiceExample", "https://github.com/weirdAlchemist/MicroServiceExample"),
    ("SummonerGate", "https://github.com/weirdAlchemist/summonergate"),
]


@pytest.mark.parametrize("name, repo_url", PROJECTS)
def test_project_node_links_to_its_repo(page: Page, live_server: str, name, repo_url):
    """Each node is a GitHub link opening the matching repo in a new tab."""
    _open(page, live_server)
    node = page.get_by_label(f"{name} on GitHub")
    expect(node).to_have_attribute("href", repo_url)
    expect(node).to_have_attribute("target", "_blank")
    # trial=True: full hit-test, no navigation — fails if anything covers the node.
    node.click(trial=True)


@pytest.mark.parametrize("name, _repo_url", PROJECTS)
def test_hovering_project_node_reveals_its_own_detail(page: Page, live_server: str, name, _repo_url):
    _open(page, live_server)
    node = page.get_by_label(f"{name} on GitHub")
    detail = node.locator(".project-node__detail")

    expect(detail).to_be_hidden()
    node.hover()
    expect(detail).to_be_visible()
    expect(detail.locator(".project-node__detail-title")).to_have_text(name)


def test_focusing_project_node_reveals_its_detail(page: Page, live_server: str):
    """Keyboard users get the same reveal via :focus-within, not just :hover."""
    _open(page, live_server)
    node = page.get_by_label("PotionCode on GitHub")
    detail = node.locator(".project-node__detail")

    expect(detail).to_be_hidden()
    node.focus()
    expect(detail).to_be_visible()


def test_only_the_hovered_node_shows_its_detail(page: Page, live_server: str):
    """Hovering one node must not leak another node's panel into view."""
    _open(page, live_server)
    one = page.get_by_label("PotionCode on GitHub")
    two = page.get_by_label("ChainTimer on GitHub")

    one.hover()
    expect(one.locator(".project-node__detail")).to_be_visible()
    expect(two.locator(".project-node__detail")).to_be_hidden()


def test_flask_stays_centered_during_reveal_animation(page: Page, live_server: str):
    """The orbit flask must zoom in *in place* at the viewport center, like the
    homepage flask — not slide in from the bottom-right. It regressed because
    the flask-stage was centered with a `translate(-50%, -50%)` that the zoomIn
    reveal's own `transform` overrode for the ~1s it ran. It's now centered with
    auto margins, so the transform only scales it. Let the real animation play
    (no freeze) and check the center holds throughout.
    """
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(f"{live_server}/projects.html")
    viewport = page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })")

    for _ in range(6):
        flask = page.locator(".flask-stage").bounding_box()
        assert abs(flask["x"] + flask["width"] / 2 - viewport["width"] / 2) <= 1, flask
        assert abs(flask["y"] + flask["height"] / 2 - viewport["height"] / 2) <= 1, flask
        page.wait_for_timeout(120)


# --- Responsive layout --------------------------------------------------------

def test_orbit_collapses_to_a_stacked_list_on_narrow_viewports(page: Page, live_server: str):
    page.set_viewport_size({"width": 390, "height": 900})
    _open(page, live_server)

    flask = page.locator(".flask-stage").bounding_box()
    first_node = page.get_by_label("PotionCode on GitHub").bounding_box()
    last_node = page.get_by_label("SummonerGate on GitHub").bounding_box()

    # Stacked: nodes fall below the flask in document order, not orbiting around it.
    assert first_node["y"] > flask["y"] + flask["height"], "expected nodes below the flask"
    assert last_node["y"] > first_node["y"], "expected nodes stacked top-to-bottom"
