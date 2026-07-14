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

- **`test_social_icon_is_clickable`** — the original regression: each icon
  (GitHub / LinkedIn / email) actually receives a click.
- **`test_clicking_card_opens_musing`** / **`test_clicking_away_closes_musing`**
  — the musings box opens with the right content and dismisses on an outside
  click.
- **`test_opening_musing_does_not_move_flask_or_cards`** — the overlay floats on
  top; the flask and mini-cards don't shift.
- **`test_mini_cards_share_one_width`** — the skill cards stay uniformly sized.
