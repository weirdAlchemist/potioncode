"""Regression tests for the PotionCode.io hero.

The suite exists because of one deceptively simple bug: the social icons
under the flask were *rendered perfectly* — right position, visible, correct
href — but not **clickable**. A sibling element painted on top and intercepted
the pointer events.

The lesson (and the point of these tests): "renders correctly" is not the same
as "works". A unit test, or a DOM-presence check in jsdom, sails right past this
class of bug because there is no layout engine and no compositing involved. Only
a test that exercises real layout + hit-testing in a real browser catches it.

Playwright's actionability check does exactly that. ``locator.click(trial=True)``
runs every pre-click check — including verifying the element actually *receives*
the pointer event — without performing the click (so no navigation side effects).
If anything covers the icon, the trial click fails. That single line would have
turned the original bug red automatically.
"""
import re

import pytest
from playwright.sync_api import Page, expect


def _open(page: Page, live_server: str) -> None:
    page.goto(f"{live_server}/index.html")
    # Freeze entrance animations (animate.css zoomIn/fade on the hero) and CSS
    # transitions so geometry is stable and assertions aren't racing the intro.
    # Test-only — it never touches the shipped page.
    page.add_style_tag(
        content="*, *::before, *::after { animation: none !important; transition: none !important; }"
    )
    # Explicitly load the Material Icons font before measuring geometry: it's
    # fetched lazily when the chevron first paints, so plain fonts.ready can
    # resolve before it's even requested, and the later swap from ligature text
    # to glyph would reflow the card mid-test.
    page.evaluate(
        "async () => { await document.fonts.load('1rem \"Material Icons\"'); await document.fonts.ready; }"
    )


# --- The bug that started it all ------------------------------------------

@pytest.mark.parametrize(
    "label, href_fragment",
    [
        ("GitHub", "github.com"),
        ("LinkedIn", "linkedin.com"),
        ("Email", "mailto:"),
    ],
)
def test_social_icon_is_clickable(page: Page, live_server: str, label, href_fragment):
    """Each social icon must actually receive clicks, not just be visible."""
    _open(page, live_server)
    icon = page.get_by_label(label)
    expect(icon).to_have_attribute("href", re.compile(href_fragment))
    # trial=True: full actionability/hit-test, but does NOT navigate.
    # Fails if another element covers the icon (the original regression).
    icon.click(trial=True)


# --- Musings feature -------------------------------------------------------

def test_clicking_card_opens_musing(page: Page, live_server: str):
    _open(page, live_server)
    musing = page.locator("#musing")
    expect(musing).not_to_have_class(re.compile(r"\bmusing--open\b"))

    page.get_by_role("button", name="4y Test Automation").click()

    expect(musing).to_have_class(re.compile(r"\bmusing--open\b"))
    expect(page.locator(".musing__title")).to_have_text("4y Test Automation")
    expect(page.locator(".musing__body")).to_contain_text("stable")


def test_musing_has_did_and_think_sections(page: Page, live_server: str):
    """An opened musing splits into a 'What I did' and a 'What I think' section."""
    _open(page, live_server)
    page.get_by_role("button", name="4y Test Automation").click()

    titles = page.locator(".musing__body .musing__section-title")
    expect(titles).to_have_count(2)
    expect(titles.nth(0)).to_have_text("What I did")
    expect(titles.nth(1)).to_have_text("What I think")
    # The current text lives under "What I think".
    expect(page.locator(".musing__section").nth(1)).to_contain_text("stable")


def test_every_interactive_card_opens_its_musing(page: Page, live_server: str):
    """Every clickable skill card reveals a musing titled with its own label."""
    _open(page, live_server)
    labels = page.eval_on_selector_all(
        ".mini-card--interactive .mini-card__label",
        "els => els.map(e => e.textContent.trim())",
    )
    assert len(labels) == 11, labels  # 8 skill cards + 3 Personal cards
    musing = page.locator("#musing")
    for label in labels:
        page.get_by_role("button", name=label, exact=True).click()
        expect(musing).to_have_class(re.compile(r"\bmusing--open\b"))
        expect(page.locator(".musing__title")).to_have_text(label)
        assert page.locator(".musing__body").inner_text().strip(), f"empty musing: {label}"
        page.keyboard.press("Escape")
        expect(musing).not_to_have_class(re.compile(r"\bmusing--open\b"))


def test_clicking_away_closes_musing(page: Page, live_server: str):
    _open(page, live_server)
    musing = page.locator("#musing")
    page.get_by_role("button", name="8y Fullstack Dev").click()
    expect(musing).to_have_class(re.compile(r"\bmusing--open\b"))

    # Clicking anywhere neutral dismisses it.
    page.get_by_text("Sebastian Rapp").click()
    expect(musing).not_to_have_class(re.compile(r"\bmusing--open\b"))


def test_opening_musing_does_not_move_flask_or_cards(page: Page, live_server: str):
    """The overlay must float on top; the flask and mini-cards must not shift."""
    _open(page, live_server)
    flask = page.locator(".flask-stage")
    card = page.get_by_role("button", name="8y Fullstack Dev")

    before_flask = _rounded(flask.bounding_box())
    before_card = _rounded(card.bounding_box())

    card.click()
    expect(page.locator("#musing")).to_have_class(re.compile(r"\bmusing--open\b"))

    # Move the mouse off the card: Playwright leaves it hovering after the
    # click, and .mini-card:hover lifts the card by 3px (intended hover
    # affordance) — that would masquerade as a layout shift here.
    page.mouse.move(0, 0)

    assert _rounded(flask.bounding_box()) == before_flask
    assert _rounded(card.bounding_box()) == before_card


# --- Layout ----------------------------------------------------------------

def test_mini_cards_share_one_width(page: Page, live_server: str):
    """Cards are exactly uniform within a column and match across columns."""
    _open(page, live_server)
    per_col = {
        side: page.eval_on_selector_all(
            f".skill-column--{side} .mini-card",
            "els => els.map(e => Math.round(e.getBoundingClientRect().width))",
        )
        for side in ("left", "right")
    }
    # Each column shrink-wraps to its widest card, so its cards are identical.
    for side, widths in per_col.items():
        assert widths, f"expected mini-cards in {side} column"
        assert len(set(widths)) == 1, (side, widths)
    # The two columns match within sub-pixel rounding.
    all_widths = [w for widths in per_col.values() for w in widths]
    assert max(all_widths) - min(all_widths) <= 2, per_col


def test_musing_visible_in_stacked_view(page: Page, live_server: str):
    """Narrow/stacked layout: the musing opens below the sticky navbar and stays
    on-screen — no scrolling up required to see it."""
    page.set_viewport_size({"width": 390, "height": 700})
    _open(page, live_server)

    # Confirm we're actually stacked: the columns sit below the flask, not beside it.
    flask = page.locator(".flask-stage").bounding_box()
    left = page.locator(".skill-column--left").bounding_box()
    assert left["y"] > flask["y"] + 100, "expected the stacked (single-column) layout"

    # Playwright scrolls the (lower) card into view before clicking — so an
    # absolute box anchored to the top of the page would end up off-screen.
    page.get_by_role("button", name="8y Fullstack Dev").click()
    expect(page.locator("#musing")).to_have_class(re.compile(r"\bmusing--open\b"))

    # Pinned to the viewport, so scrolling can't push it off the top of the page.
    assert page.eval_on_selector("#musing", "e => getComputedStyle(e).position") == "fixed"

    nav = page.locator("nav").bounding_box()
    card = page.locator(".musing__card").bounding_box()
    viewport_h = page.evaluate("() => window.innerHeight")
    # Below the navbar...
    assert card["y"] >= nav["y"] + nav["height"] - 1, ("overlaps navbar", card, nav)
    # ...and fully within the viewport.
    assert 0 <= card["y"] and card["y"] + card["height"] <= viewport_h, ("off-screen", card, viewport_h)


def test_personal_group_row_on_desktop_column_when_stacked(page: Page, live_server: str):
    """The Personal group is a horizontal row on desktop and switches to a
    vertical column (as the last group) in the stacked layout."""
    page.set_viewport_size({"width": 1280, "height": 900})
    _open(page, live_server)

    labels = page.eval_on_selector_all(
        ".personal__cards .mini-card__label", "els => els.map(e => e.textContent.trim())"
    )
    assert labels == ["City", "Self", "Interests"], labels

    def card_positions():
        return page.eval_on_selector_all(
            ".personal__cards .mini-card",
            "els => els.map(e => { const r = e.getBoundingClientRect();"
            " return {x: Math.round(r.x), y: Math.round(r.y)}; })",
        )

    # Desktop: same row (equal y), left-to-right.
    desk = card_positions()
    assert desk[0]["y"] == desk[1]["y"] == desk[2]["y"], desk
    assert desk[0]["x"] < desk[1]["x"] < desk[2]["x"], desk

    # Stacked: vertical column (increasing y), and the group sits last —
    # below the Development column.
    page.set_viewport_size({"width": 390, "height": 800})
    stacked = card_positions()
    assert stacked[0]["y"] < stacked[1]["y"] < stacked[2]["y"], stacked
    dev = page.locator(".skill-column--right").bounding_box()
    personal = page.locator(".personal").bounding_box()
    assert personal["y"] > dev["y"], ("Personal should be last", personal, dev)


def _rounded(box):
    return {k: round(v) for k, v in box.items()}
