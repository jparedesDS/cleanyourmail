# CleanYourMail — Forest Brand Identity & App Icon Guide

> **Primary app-first identity:** [Family](../final-family/README.md) — lavender envelope and gold return arrow aligned with CleanYourPhone. This package is the **Forest/Lime alternate**, kept for the classic CLI theme.

## 1. Brand idea & final decision

- **Name:** `CleanYourMail` (exact casing: capital **C**, **Y**, **M**; never rename, split with spaces, or publicly abbreviate).
- **Brand idea:** **Control, not magic.**
- **One-liner:** CleanYourMail is a local-first IMAP cleanup product: a Python CLI and agent skill today, with a desktop app in development. It reads headers only, plans before action, and gives every move a way back.
- **Tagline (EN):** **Your inbox, minus the noise.**
- **Tagline (ES):** **Tu bandeja, sin el ruido.**
- **Audience:** Non-technical people who want a calm visual app (the desktop app is in development), plus developers and coding agents who use the Python 3.11+ CLI engine. Today the CLI and agent skill are the available interfaces; the desktop app is the intended primary interface.

> The desktop app icon and app-first tokens are prepared for the planned app. Today the Python CLI and agent skill are the available interfaces.

### Three directions explored internally

1. **Orbit / Shielded Mail (Envelope + External Undo Loop):** Placed a circular counter-clockwise arrow around an envelope. Rejected because an external circular arrow around mail reads as a generic "refresh / sync inbox" button rather than reversible cleanup, and shrinking the envelope inside an outer ring degraded 16 px legibility.
2. **Plan Stack / Slotted Tray (Layered Header Rows + Checkmark):** Stacked horizontal bars representing message headers with a completion checkmark. Rejected because it lost immediate "mail" recognition, looked like a generic task manager on a desktop dock, and a checkmark implied automated approval rather than user review and a way back.
3. **Return Fold (Chosen):** An envelope whose right and bottom perimeter folds continuously into a bold left-return arrow (`↩`) below a classic symmetric V-flap. It unifies **mail** and **return / undo / control** into one continuous structural gesture with wide negative space, zero gradients, and no generic AI sparkle.

---

## 2. Three pillars & product truth

1. **Local by construction.** CleanYourMail runs locally today as a Python 3.11+ standard-library CLI and agent skill, with a desktop app in development. It is not a hosted SaaS. There is no CleanYourMail account, no telemetry, and no third-party API. It reads **headers only** (sender, subject, date, size, flags, and unsubscribe headers)—**say "headers only", never "no email data at all."** Message bodies and attachments are never fetched.
2. **Plan before action.** Every cleanup starts with an inspectable plan. Protected mail (personal, transactional, banking, security, medical, legal, travel, invoice, government, starred, answered, recent) is excluded from automatic actions, and there is **no permanent deletion**. Works with Gmail, Outlook/Microsoft 365, Yahoo, iCloud, Fastmail, Proton Bridge, and custom IMAP servers supporting `UIDPLUS` or `MOVE`.
3. **A way back.** Every move is recorded in an append-only local journal and verified by `Message-ID` (or `X-GM-MSGID`) before restore. **“Reversible” applies strictly to moves, not unsubscribe. Unsubscribe is a separate, irreversible flow.**

---

## 3. Logo construction

- **Symbol (`symbol.svg`, 512×512 viewBox):**
  - Dark canvas `#07100d` with a rounded-square lime tile (`x=40, y=40, width=432, height=432, rx=112`, fill `#b9f36a`).
  - Inside the tile, the Return Fold glyph uses a `30`-unit round-cap, round-join stroke (`#07100d`):
    - Envelope perimeter + bottom return shaft: `M116 276 V168 A28 28 0 0 1 144 140 H368 A28 28 0 0 1 396 168 V320 A28 28 0 0 1 368 348 H184`
    - Symmetric top V-flap: `M124 152 L240 238 Q256 250 272 238 L388 152`
    - Left-return arrowhead (`↩`): `M224 304 L178 348 L224 392`
  - The shortened left wall (`V168..276`) creates an intentional `72`-unit vertical and `62`-unit horizontal negative-space gate in front of the return arrowhead so the mark stays open and legible down to 16 px.
- **Favicon (`favicon.svg`, 64×64 viewBox):**
  - Redrawn on a 64-unit grid with the lime tile filling `x=2, y=2, width=60, height=60, rx=16` and a `4.5`-unit stroke (`#07100d`) so browser tabs and system trays at 16–32 px maximize icon area.
- **Wordmark (`wordmark.svg`, 604×96 viewBox):**
  - Outlined geometric sans-serif vector paths (`<path>`) with exact `CleanYourMail` capitalization (`CleanYour` in `#eef8ee`, `Mail` in `#b9f36a` on dark; `#102019` and `#3f721c` on light). Because the wordmark uses closed filled outlines, it has zero external font dependencies and scales uniformly at any resolution.

---

## 4. Desktop app icon usage

- **Primary App Icon (`app-icon.svg`, 1024×1024 viewBox):**
  - Designed for macOS Dock and Windows Taskbar/Start launchers with built-in OS safe margins (`96 px` transparent outer margin around an `832×832` rounded square, `rx=192`).
  - A dark forest outer shell (`#07100d` with an inner `#11231b` rim) frames the `#b9f36a` lime tile (`x=152, y=152, width=720, height=720, rx=156`) and `#07100d` Return Fold glyph (`stroke-width=52`). This dark structural bezel guarantees crisp edge contrast on both dark and light desktop docks/wallpapers without drop shadows or gradients.
- **Monochrome App Icon (`app-icon-mono.svg`, 1024×1024 viewBox):**
  - Uses the identical `832×832` rounded-square silhouette and `96 px` safe margin rendered in a single ink (`#07100d`, transparent interior) for monochrome docks, high-contrast OS themes, print manuals, and single-color system surfaces.

---

## 5. Clear space & minimum sizes

- **Clear space rule:** Let **X** equal **25% of the visible symbol tile width** (or **50% of the cap height** for the standalone wordmark). Maintain at least **X** of clear, unobstructed margin on all four sides of any symbol, app icon, or lockup.
- **Minimum reproduction sizes:**
  - `favicon.svg`: **16 × 16 px** minimum (optimized for 16–32 px).
  - `symbol.svg` / `mono.svg`: **16 × 16 px** minimum (**24 × 24 px** preferred when standalone).
  - `app-icon.svg` / `app-icon-mono.svg`: **32 × 32 px** taskbar/tray up to **1024 × 1024 px** store/bundle master.
  - `lockup-horizontal.svg` / `light.svg`: **160 px** minimum width.
  - `lockup-stacked.svg`: **160 × 160 px** minimum.
  - `wordmark.svg`: **120 px** minimum width.

---

## 6. Color tokens & contrast ratios

The existing dark forest, lime, and teal palette is preserved without gradients. Light-surface tokens provide accessible contrast for light mode and print documentation.

| Token | Hex | Role | WCAG contrast ratio |
|---|---|---|---|
| `background` | `#07100d` | Primary dark canvas & icon ink | — |
| `panel` | `#0d1a15` | App cards, dock bars, secondary containers | `16.41:1` with `#eef8ee` |
| `elevated` | `#11231b` | Borders, window headers, dividers | `15.48:1` with `#eef8ee` |
| `text` | `#eef8ee` | Primary text & `CleanYour` on dark | `17.72:1` on `#07100d` |
| `secondary` | `#9eb4a7` | Supporting copy & subtitles | `8.76:1` on `#07100d` (AAA) |
| `tertiary` | `#6f8578` | Technical labels, captions, metadata | `4.87:1` on `#07100d` (AA) |
| `accent` | `#b9f36a` | Lime tile, `Mail` on dark, primary step | `14.78:1` with `#07100d` (AAA) |
| `secondary-accent` | `#6ee7c8` | Teal step markers, Spanish tagline accent | `12.79:1` on `#07100d` (AAA) |
| `light-background` | `#f4f8f1` | Light mode / paper canvas | — |
| `light-text` | `#102019` | Primary text & dark tile on light | `15.73:1` on `#f4f8f1` (AAA) |
| `light-secondary` | `#42564b` | Supporting copy on light | `7.34:1` on `#f4f8f1` (AAA) |
| `light-accent` | `#3f721c` | `Mail` wordmark accent on light | `5.38:1` on `#f4f8f1` (AA) |

---

## 7. Typography

- **Wordmark & lockups:** `wordmark.svg`, `lockup-horizontal.svg`, `lockup-stacked.svg`, and `light.svg` use pre-outlined `<path>` geometry derived from geometric sans-serif letterforms (`CleanYourMail`). No font installation is needed to render any logo or lockup.
- **UI & supporting SVG copy (`banner.svg`, `social.svg`, `preview.html`):**
  - Primary UI / headline stack: `"Segoe UI", "Helvetica Neue", Arial, sans-serif`
  - Technical / CLI / badge stack: `Consolas, Menlo, monospace`
  - *Path/outline note:* `banner.svg` and `social.svg` use `<text>` elements with the system stacks above so copy remains accessible and editable; convert `<text>` to paths in a vector editor only if exporting to a print workflow without system fonts.

---

## 8. Do / Don’t

### Do
- Keep the exact `CleanYourMail` casing (capital **C**, **Y**, **M**) and exact tagline punctuation.
- Lead with the **local-first product** and the **Python CLI engine** today; present the desktop app as **in development**, not shipped.
- State clearly that CleanYourMail reads **headers only** (sender, subject, date, size, flags, unsubscribe headers), never bodies or attachments.
- State clearly that **reversible applies to moves**, while **unsubscribe is separate and irreversible**.
- Use `favicon.svg` at 16–32 px, `app-icon.svg` for desktop bundles/docks, `light.svg` on light surfaces, and `mono.svg` / `app-icon-mono.svg` for one-ink contexts.

### Don’t
- Do not reintroduce the old 4-point AI sparkle, gradients, glows, robots, shields, magic wands, or cloud icons.
- Do not stretch, rotate, skew, crop the tile, or place the dark-background wordmark (`#eef8ee` / `#b9f36a`) directly on a light background.
- Do not claim "reads no email data at all", "everything is reversible", or "deletes spam forever".
- Do not invent user counts, testimonials, speed benchmarks, or fixed test counts in banners or marketing cards.

---

## 9. File map (`brand/final/`)

| File | Dimensions / ViewBox | Purpose |
|---|---|---|
| `symbol.svg` | `512 × 512` | Square Return Fold symbol on dark background (`#07100d`). |
| `favicon.svg` | `64 × 64` | Simplified symbol for 16–32 px browser tabs and small UI slots. |
| `app-icon.svg` | `1024 × 1024` | Rounded-square desktop app icon with `96 px` macOS/Windows safe margins. |
| `app-icon-mono.svg` | `1024 × 1024` | Single-color (`#07100d`) desktop app icon with `96 px` safe margins. |
| `wordmark.svg` | `604 × 96` | Outlined `<path>` wordmark (`CleanYourMail`) for dark surfaces. |
| `lockup-horizontal.svg` | `860 × 192` | Primary horizontal lockup (symbol + outlined wordmark on dark). |
| `lockup-stacked.svg` | `640 × 640` | Square stacked lockup for social avatars and square cards. |
| `mono.svg` | `512 × 512` | Single-color (`#07100d`) outlined symbol for stamps, embossing, and monochrome UI. |
| `light.svg` | `860 × 192` | Horizontal lockup on light background (`#f4f8f1`) with `#102019` tile and `#3f721c` accent. |
| `banner.svg` | `1600 × 440` | Repository header banner with app-first positioning, taglines, and guardrails. |
| `social.svg` | `1280 × 640` | Social / Open Graph preview card with EN/ES taglines and the 3-step loop. |
| `preview.html` | Responsive HTML | Self-contained offline visual QA sheet (scale test, dark/light dock mocks, lockups, cards). |
| `README.md` | Markdown | Complete brand identity and asset specification guide. |

Also see [`docs/BRAND.md`](../../docs/BRAND.md) for the one-page repository brand cheat sheet.

---

## 10. Integration notes (next step after review)

1. **Replace in `cleanyourmail` repo (step 2):**
   - Rasterize `brand/final/banner.svg` (1600×440) to replace `assets/banner.png` (or reference `brand/final/banner.svg` directly in `README.md` and translated `README.*.md` files).
   - Rasterize `brand/final/social.svg` (1280×640) to replace `assets/social-preview.png` for GitHub repository social preview metadata.
2. **Replace in `cleanyourmail-web` & desktop app shell (step 2):**
   - Replace `assets/logo.svg` (which uses a lime-to-teal gradient and AI sparkle) with `brand/final/symbol.svg` or `brand/final/lockup-horizontal.svg`.
   - Replace `assets/favicon.svg` with `brand/final/favicon.svg`.
   - Package `brand/final/app-icon.svg` (and `app-icon-mono.svg`) into `.icns` (macOS) and `.ico` (Windows) desktop bundles.
3. **Keep unchanged:**
   - Keep the exact product name `CleanYourMail`, English tagline `"Your inbox, minus the noise."`, Spanish tagline `"Tu bandeja, sin el ruido."`, dark green/lime/teal color tokens, and all safety guardrails in `SKILL.md` and `tools/`.
