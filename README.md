# PotionCode.io — Web Business Card

The personal site of **PotionCode**, a software developer / tester. A single-page site built with **Material Design**
(Materialize CSS) and **Animate.css** scroll animations. **No build step, no CDN needed** —
all libraries are vendored locally, so it works fully offline. Open `index.html` in a
browser, or drop the folder on any static host (GitHub Pages, Netlify, Vercel, Cloudflare Pages).

## Tech / libraries (all local, in `vendor/`)

- **Materialize CSS 1.0.0** — Material Design components (navbar, cards, chips, buttons, waves)
- **Animate.css 4.1.1** — entrance animations, triggered on scroll
- **Material Icons** — icon font, bundled offline (`vendor/fonts/MaterialIcons-Regular.ttf`)

## Structure

```
index.html            Content & sections (Material markup)
css/styles.css        Custom theme layered on Materialize (colors in :root at top)
js/main.js            Materialize init, theme toggle, scroll animations, stat count-up
vendor/               materialize.*, animate.min.css, material-icons.css, fonts/
assets/               Put resume.pdf and any images here
.claude/launch.json   `python -m http.server 4173` for local preview
```

## Run locally

Because it uses local fonts/JS, serve it over HTTP rather than opening the file directly:

```
python -m http.server 4173
# then visit http://localhost:4173
```

## Sections

- **Hero / business card** — name, role, tagline, call-to-action buttons
- **About** — short bio + animated stats
- **Skills** — Development / Test Automation / QA cards
- **Portfolio** — project cards (duplicate a `.project` block to add more)
- **Contact / social** — email + social links

## Make it yours

1. **Text** — edit the copy directly in `index.html` (name, tagline, projects, links).
2. **Social links** — update the `href`s in the `.socials` list at the bottom.
3. **Colors** — change the variables in the `:root` block at the top of `css/styles.css`.
4. **CV** — drop your file at `assets/resume.pdf` (the "Download CV" button points there).
5. **Avatar** — the hero shows initials; swap the `.hero__avatar` div for an `<img>` if you prefer a photo.
6. **Favicon** — currently an inline emoji in `<head>`; replace with your own if you like.

## Theme

Dark by default, with a light theme. The toggle (top-right) remembers the visitor's
choice and otherwise follows their OS preference.
