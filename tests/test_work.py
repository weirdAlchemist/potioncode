"""Regression tests for the work.html career timeline.

The timeline is a CSS construction: an absolutely-positioned spine drawn as a
::before on the list, with each stage's marker offset back over it by a calc()
chain. That is exactly the kind of layout that keeps *looking* fine in the DOM
while drifting visually, so the alignment is asserted from real geometry rather
than from class names -- same reasoning as the hit-testing in test_hero.py.

Content assertions stay deliberately structural (a stage has a company, a
duration, responsibilities and a closing musing) so rewording a musing doesn't
break the suite, but dropping half a stage does.
"""
import pytest
from playwright.sync_api import Page, expect


def _open(page: Page, live_server: str) -> None:
    page.goto(f"{live_server}/work.html")
    page.add_style_tag(
        content="*, *::before, *::after { animation: none !important; transition: none !important; }"
    )
    # The stages reveal on scroll; force them visible so geometry is measurable
    # regardless of where the IntersectionObserver happens to have fired.
    page.add_style_tag(content=".will-animate { opacity: 1 !important; }")


# --- Structure ---------------------------------------------------------------

def test_timeline_lists_every_stage(page: Page, live_server: str):
    _open(page, live_server)
    expect(page.locator(".work-timeline__stage")).to_have_count(2)


def test_stages_run_newest_first(page: Page, live_server: str):
    """LIS (most recent) sits above IDEA. Guards against the list being
    reordered or appended to at the wrong end."""
    _open(page, live_server)
    companies = page.locator(".work-timeline__company").all_text_contents()
    assert companies == ["LIS GmbH", "IDEA Data Solutions GmbH"], companies

    boxes = [
        page.locator(".work-timeline__stage").nth(i).bounding_box()["y"]
        for i in range(2)
    ]
    assert boxes[0] < boxes[1], boxes


@pytest.mark.parametrize(
    "company, years, bullets",
    [
        ("LIS GmbH", "4 years", 4),
        ("IDEA Data Solutions GmbH", "8 years", 3),
    ],
)
def test_every_stage_is_complete(page: Page, live_server: str, company, years, bullets):
    """Each stage carries all five parts: company, duration, what I did, the
    skill badges, and what I think."""
    _open(page, live_server)
    stage = page.locator(".work-timeline__stage").filter(has_text=company)

    expect(stage.locator(".work-timeline__company")).to_have_text(company)
    expect(stage.locator(".work-timeline__years")).to_contain_text(years)
    expect(stage.locator(".work-timeline__list li")).to_have_count(bullets)
    expect(stage.locator(".work-timeline__badge").first).to_be_visible()

    musing = stage.locator(".work-timeline__musing")
    expect(musing).to_be_visible()
    # The closing line is the italic emerald quote, same voice as the home-page
    # musings -- a stage without one is missing its point.
    expect(musing.locator("em")).to_be_visible()
    assert musing.locator("em").inner_text().strip(), "musing quote is empty"


@pytest.mark.parametrize(
    "company, skills",
    [
        ("LIS GmbH", ["C#", "Selenium", "Playwright", "Azure"]),
        ("IDEA Data Solutions GmbH", ["C#", "ASP.NET", "SQL", "CouchDB"]),
    ],
)
def test_stage_lists_its_skill_badges(page: Page, live_server: str, company, skills):
    _open(page, live_server)
    stage = page.locator(".work-timeline__stage").filter(has_text=company)
    assert stage.locator(".work-timeline__badge").all_text_contents() == skills


def test_badges_sit_between_the_bullets_and_the_musing(page: Page, live_server: str):
    """Reading order is what I did -> what I used -> what I think. The divider
    above 'What I think' is an adjacent-sibling rule, so inserting the badge row
    in the wrong place would silently drop it."""
    _open(page, live_server)
    stage = page.locator(".work-timeline__stage").first

    bullets_bottom = stage.locator(".work-timeline__list").bounding_box()
    badges = stage.locator(".work-timeline__badges").bounding_box()
    musing = stage.locator(".work-timeline__musing").bounding_box()

    assert bullets_bottom["y"] + bullets_bottom["height"] <= badges["y"] + 1
    assert badges["y"] + badges["height"] <= musing["y"] + 1

    # The section divider survived the insertion.
    border = stage.locator(".work-timeline__label").last.evaluate(
        "el => getComputedStyle(el).borderTopWidth"
    )
    assert border != "0px", "section divider above 'What I think' is missing"


# --- Geometry ----------------------------------------------------------------

def test_markers_sit_centred_on_the_spine(page: Page, live_server: str):
    """The marker offset is a calc() off the list's padding; if the gutter and
    the offset ever disagree the markers slide off the line."""
    _open(page, live_server)

    spine = page.evaluate(
        """() => {
            const tl = document.querySelector('.work-timeline');
            const cs = getComputedStyle(tl, '::before');
            const box = tl.getBoundingClientRect();
            return {
                left: parseFloat(cs.left),
                width: parseFloat(cs.width),
                originX: box.x,
            };
        }"""
    )
    spine_centre = spine["left"] + spine["width"] / 2

    markers = page.locator(".work-timeline__marker")
    assert markers.count() == 2
    for i in range(markers.count()):
        box = markers.nth(i).bounding_box()
        centre = box["x"] + box["width"] / 2 - spine["originX"]
        assert centre == pytest.approx(spine_centre, abs=1.5), (i, centre, spine_centre)


def test_markers_stay_on_the_spine_on_narrow_viewports(page: Page, live_server: str):
    """The 600px breakpoint shrinks both the marker and the gutter -- they have
    to shrink together."""
    page.set_viewport_size({"width": 390, "height": 800})
    _open(page, live_server)

    spine = page.evaluate(
        """() => {
            const tl = document.querySelector('.work-timeline');
            const cs = getComputedStyle(tl, '::before');
            return {
                centre: parseFloat(cs.left) + parseFloat(cs.width) / 2,
                originX: tl.getBoundingClientRect().x,
            };
        }"""
    )
    box = page.locator(".work-timeline__marker").first.bounding_box()
    centre = box["x"] + box["width"] / 2 - spine["originX"]
    assert centre == pytest.approx(spine["centre"], abs=1.5), (centre, spine)


@pytest.mark.parametrize("width", [1280, 900, 390])
def test_page_never_scrolls_sideways(page: Page, live_server: str, width):
    """Cards live inside main's rail gutter; long company names must wrap
    rather than push the page wider than the viewport."""
    page.set_viewport_size({"width": width, "height": 800})
    _open(page, live_server)
    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 0, f"{overflow}px of horizontal overflow at {width}px"
