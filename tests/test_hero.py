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
    expect(musing).not_to_have_class(re.compile(r"\bis-open\b"))

    page.get_by_role("button", name="4y Test Automation").click()

    expect(musing).to_have_class(re.compile(r"\bis-open\b"))
    expect(page.locator(".musing__title")).to_have_text("4y Test Automation")
    expect(page.locator(".musing__body")).to_contain_text("stable")


def test_clicking_away_closes_musing(page: Page, live_server: str):
    _open(page, live_server)
    musing = page.locator("#musing")
    page.get_by_role("button", name="8y Fullstack Dev").click()
    expect(musing).to_have_class(re.compile(r"\bis-open\b"))

    # Clicking anywhere neutral dismisses it.
    page.get_by_text("Sebastian Rapp").click()
    expect(musing).not_to_have_class(re.compile(r"\bis-open\b"))


def test_opening_musing_does_not_move_flask_or_cards(page: Page, live_server: str):
    """The overlay must float on top; the flask and mini-cards must not shift."""
    _open(page, live_server)
    flask = page.locator(".flask-stage")
    card = page.get_by_role("button", name="8y Fullstack Dev")

    before_flask = _rounded(flask.bounding_box())
    before_card = _rounded(card.bounding_box())

    card.click()
    expect(page.locator("#musing")).to_have_class(re.compile(r"\bis-open\b"))

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
            f".skill-col--{side} .mini-card",
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


def _rounded(box):
    return {k: round(v) for k, v in box.items()}
