# Tests

Browser-driven regression tests for PotionCode.io, using **Playwright for
Python** + pytest. They run the real page in a real (headless) browser against a
throwaway `http.server` — no `node_modules`, same Python toolchain as the dev
server.

> These are **dev tooling only**. Nothing here is served with the site; the
> shipped page stays no-build / no-CDN / offline.

## Why browser tests (the point)

The suite was born from a good bug: the social icons under the flask were
rendered perfectly — correct position, visible, correct `href` — but **not
clickable**. A sibling element painted on top and swallowed the pointer events.

That class of bug is invisible to unit tests and to DOM-presence checks in
jsdom: there's no broken function, and jsdom has no layout engine or
compositing, so "is the `<a>` in the document?" passes while the page is broken.
Only a test that exercises **real layout + hit-testing in a real browser** sees
it.

Playwright's actionability check does precisely that. In
[`test_hero.py`](test_hero.py), each icon is verified with:

```python
icon.click(trial=True)   # full hit-test, but does NOT navigate
```

`trial=True` runs every pre-click check — including "does this element actually
receive the pointer event?" — without performing the click. If anything covers
the icon, it fails. **That one line would have caught the original bug
automatically.** The takeaway the suite guards: *"renders correctly" ≠ "works."*

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate on *nix)
pip install -r tests/requirements.txt
playwright install chromium
```

## Run

From the repo root:

```bash
pytest tests                      # headless
pytest tests --headed             # watch it drive the browser
pytest tests -k clickable         # just the social-icon regression
```

## What's covered

`test_hero.py` (index.html hero):
- **`test_social_icon_is_clickable`** — the original regression: each icon
  (GitHub / LinkedIn / email) actually receives a click.
- **`test_clicking_card_opens_musing`** / **`test_clicking_away_closes_musing`**
  — the musings box opens with the right content and dismisses on an outside
  click.
- **`test_opening_musing_does_not_move_flask_or_cards`** — the overlay floats on
  top; the flask and mini-cards don't shift.
- **`test_mini_cards_share_one_width`** — the skill cards stay uniformly sized.

`test_projects.py` (projects.html orbit):
- **`test_flask_is_a_clickable_github_link`** — the flask doubles as a GitHub
  link on this page and actually receives a click (same hit-test regression
  class as the hero's social icons).
- **`test_hovering_project_node_reveals_its_own_detail`** /
  **`test_focusing_project_node_reveals_its_detail`** /
  **`test_only_the_hovered_node_shows_its_detail`** — each of the five
  project nodes reveals its own (and only its own) detail panel on hover or
  keyboard focus.
- **`test_orbit_collapses_to_a_stacked_list_on_narrow_viewports`** — the
  circular orbit layout falls back to a stacked list under 900px.

`test_page_rail.py` (carousel prev/next arrows, both pages):
- **`test_rails_are_present_and_clickable`** — both rails point at the other
  page and actually receive clicks.
- **`test_clicking_rail_navigates_to_other_page`** — clicking a rail lands on
  the other page.
- **`test_rails_are_fixed_at_the_viewport_edges`** — rails are pinned
  full-height to the left/right edge regardless of scroll.
- **`test_rails_do_not_cover_navbar_or_footer_content`** — the body's
  reserved `--rail-w` padding actually keeps page content clear of the rails.
- **`test_rail_labels_hide_on_narrow_viewports`** — the rail shrinks and
  drops its label under 480px.
