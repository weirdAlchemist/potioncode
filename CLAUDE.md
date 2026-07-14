# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

**PotionCode.io** — a personal website / "web business card" for Sebastian Rapp, a
software developer & tester (brand: *PotionCode*). Single page, static, **no build step**.
All libraries are vendored locally under `vendor/`, so the site works fully offline —
just open it over a local HTTP server.

## ⚗️ The central flask — do NOT change without being asked

The **pure-CSS bubbling potion flask** is the hero centerpiece and the identity of the
whole site (the "PotionCode" brand — *"programming is more akin to alchemy than
chemistry"*). It lives in:

- **Markup:** the `.flask-hero` → `.flask` block in `index.html` (the `.flask__body`,
  `.flask__liquid`, `.bubble`, `.fizz`, etc.).
- **Styles:** the `/* ---------- CSS potion flask ---------- */` section and the
  `/* Big central flask */` block in `css/styles.css` (roughly the `.flask*`,
  `.flask-hero`, `.flask-stage` rules).

**Treat the flask as locked.** Do not restyle, resize, re-animate, replace, or "improve"
it — including its colors, glow, scale, bubbles, or fizz — **unless the user explicitly
asks you to touch the flask.** When editing nearby layout (hero columns, spacing,
responsive rules), leave the flask's own rules alone. If a requested change would affect
the flask as a side effect, call it out and confirm first.

## Structure

```
index.html            Content & markup (Materialize + custom classes)
css/styles.css        Custom theme layered on Materialize. Brand colors in :root at top.
js/main.js            Materialize init, scroll-in animations, stat count-up. Site works if JS fails.
vendor/               materialize.min.*, animate.min.css, material-icons.css, fonts/  (all local)
assets/               resume.pdf and images go here
.claude/launch.json   `python -m http.server 4173` for local preview
```

**Treat README.md as locked.** Do not add or change content of this file.

## Tech / conventions

- **Materialize CSS 1.0.0** (Material Design components) + **Animate.css 4.1.1**
  (scroll-in animations) + **Material Icons** (offline font). All vendored — **no CDN,
  no npm, no build.** Do not add a build step or pull libraries from a CDN unless asked.
- **Theme is dark-only.** Brand colors live in the `:root` block at the top of
  `css/styles.css` (`--bg`, `--accent` violet, `--accent-2` emerald "potion" glow,
  `--accent-grad`). Tweak these first for color changes.
- Custom CSS is **layered on top of** Materialize — keep that separation; don't edit
  files under `vendor/`.
- Scroll animations: add `class="will-animate"` + `data-anim="animate__…"` (optional
  `data-delay`) to an element; `js/main.js` reveals it via IntersectionObserver.
- Stat count-up: `.stat-num[data-count]` elements animate up when scrolled into view.

## Current state

The hero shows a three-part stage: **Tester** (left) · **flask** (center, with GitHub /
LinkedIn / email links) · **Developer** (right). The older About / Skills / Portfolio /
Contact sections have been removed and are marked *"to be redesigned"* in `index.html`.
(The `README.md` still describes some of those older sections and a light theme — it is
partly out of date; trust the code.)

## Run locally

Serve over HTTP (local fonts/JS won't load from `file://`):

```
python -m http.server 4173     # then visit http://localhost:4173
```

## Tests

Browser-driven regression tests live in `tests/` — **Playwright for Python** +
pytest. They serve the site with a throwaway `http.server` and drive it in a
real headless browser. **Dev-only tooling** — nothing under `tests/` is served
with the site, so the shipped page stays no-build / no-CDN / offline.

```
pip install -r tests/requirements.txt   # (in a venv)
playwright install chromium
pytest tests
```

Why a real browser and not unit tests: the suite was born from a bug where the
social icons rendered perfectly but weren't *clickable* (a sibling painted on
top and ate the pointer events). Unit / jsdom tests can't see that — only real
layout + hit-testing catches it. Each icon is checked with
`locator.click(trial=True)`, which runs the full actionability/hit-test without
navigating and fails if anything covers the element. See `tests/README.md` for
the details (including the animation/font/`:hover` gotchas the tests guard
against). Keep these green when touching the hero, and note the flask-lock rule
still applies to the flask itself.
