# PotionCode.io — Web Business Card

The personal site of **PotionCode** (Sebastian Rapp), a software developer & tester. A
single-page "web business card" built with **Material Design** (Materialize CSS) and
**Animate.css** scroll animations, centered on a hand-built **pure-CSS potion flask**.
**No build step, no CDN needed** — all libraries are vendored locally, so it works fully
offline. Open it over a local HTTP server, or drop the folder on any static host
(GitHub Pages, Netlify, Vercel, Cloudflare Pages).

## Tech / libraries (all local, in `vendor/`)

- **Materialize CSS 1.0.0** — Material Design components (waves, buttons, layout helpers)
- **Animate.css 4.1.1** — entrance animations, triggered on scroll
- **Material Icons** — icon font, bundled offline (`vendor/fonts/MaterialIcons-Regular.ttf`)

## Structure

```
index.html            Content & markup (Materialize + custom classes)
css/styles.css        Custom theme layered on Materialize (brand colors in :root at top)
js/main.js            Materialize init, scroll animations, stat count-up
vendor/               materialize.*, animate.min.css, material-icons.css, fonts/
assets/               Put resume.pdf and any images here
.claude/launch.json   `python -m http.server 4173` for local preview
CLAUDE.md             Guidance for AI coding assistants
```

## Run locally

Because it uses local fonts/JS, serve it over HTTP rather than opening the file directly:

```
python -m http.server 4173
# then visit http://localhost:4173
```

## The hero

A single full-page hero, laid out as three parts:

- **Tester** (left) — automation experience, Selenium, Playwright
- **The flask** (center) — a pure-CSS bubbling potion flask, the site's centerpiece and
  brand identity, with GitHub / LinkedIn / email links beneath it
- **Developer** (right) — fullstack experience, C# / Python

The older About / Skills / Portfolio / Contact sections have been removed and are marked
*"to be redesigned"* in `index.html`.

> ⚗️ **The central flask is intentionally locked.** It's the identity of the whole site —
> don't restyle, resize, re-animate, or replace it unless that's specifically what you're
> setting out to change. See `CLAUDE.md` for details.

## Make it yours

1. **Text** — edit the copy directly in `index.html` (name, motto, skill cards, links).
2. **Social links** — update the `href`s on the `.hero-socials` icons.
3. **Colors** — change the variables in the `:root` block at the top of `css/styles.css`.
4. **CV** — drop your file at `assets/resume.pdf`.
5. **Favicon** — currently an inline emoji in `<head>`; replace with your own if you like.

## Theme

Dark-only. Brand colors (violet accent + emerald "potion" glow) live in the `:root`
block at the top of `css/styles.css` — tweak those first.
