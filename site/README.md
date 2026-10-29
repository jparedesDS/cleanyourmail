# Website

Static landing page for CleanYourMail. No build step, no framework, no external assets.

## Preview locally

From the repository root:

```bash
python -m http.server 8080 --directory site
```

Open <http://localhost:8080/>.

## Files

| Path | What it is |
|---|---|
| `index.html` | English landing page. |
| `es.html` | Spanish landing page. |
| `styles.css` | Shared styles. |
| `app.js` | Provider tabs, before/after toggle, copy buttons. |
| `assets/logo.svg`, `assets/favicon.svg` | Brand mark. |
| `assets/og.svg`, `assets/og.png` | Social preview image. |

## Deploy

The GitHub Actions workflow `.github/workflows/pages.yml` publishes the `site/` directory to the
`gh-pages` branch. In the repository settings, set **Pages → Build and deployment → Source** to
**Deploy from a branch**, branch **`gh-pages`**, folder **`/ (root)`**. The workflow runs on every
push to `master` and can also be started manually.

The site is plain HTML/CSS/JS. It does not read the mailbox, call an API, or include analytics.
