# CleanYourMail — Spectrum Brand Identity & App Icon Guide

## 1. Brand idea & colorway overview

- **Name:** `CleanYourMail` (exact casing: capital **C**, **Y**, **M**; never rename, split with spaces, or publicly abbreviate).
- **Mark:** **Return Fold** (identical geometry to `brand/final/`): a rounded-square tile containing an envelope whose right and bottom perimeter folds continuously into a left-return arrow (`↩`) below a symmetric V-flap.
- **Brand idea:** **Control, not magic.**
- **One-liner:** CleanYourMail is a local-first IMAP cleanup product: a Python CLI and agent skill today, with a desktop app in development. It reads headers only, plans before action, and gives every move a way back.
- **Tagline (EN):** **Your inbox, minus the noise.**
- **Tagline (ES):** **Tu bandeja, sin el ruido.**

> The desktop app icon and app-first tokens are prepared for the planned app. Today the Python CLI and agent skill are the available interfaces.

The **Spectrum** colorway pairs a neutral carbon background (`#121316`) and warm off-white typography (`#F3F1EC`) with three semantic signal colors—**Orange (`#FFB38A`)**, **Yellow (`#FFE08A`)**, and **Mint (`#A8E6CF`)**—plus a restrained, horizontal three-stripe structural accent. It takes only the color palette and a generic three-stripe bar as inspiration; it avoids diagonal esports slashes, condensed gaming display fonts, or third-party trade dress.

---

## 2. Semantic color roles & contrast ratios

Rather than using orange, yellow, and mint at equal weight inside the logo, **Spectrum assigns each accent color to a distinct product truth**:

1. **Orange (`#FFB38A`) — Primary Action, Plan, CTA & Logo Tile:**
   - Used for the solid Return Fold logo tile, `Mail` in the dark-background wordmark, primary action buttons (`Review Plan`), and Step 1 (*Plan before action*).
   - Always use near-black (`#121316`) ink on orange fills (`10.67:1` AAA contrast).
2. **Mint (`#A8E6CF`) — Journal, Undo & Secondary Path:**
   - Used for append-only journal badges, undo step markers (Step 2: *Journal & undo moves*), and secondary structural accents.
   - Use for step markers, icons, and large headlines (`13.17:1` on `#121316`), **never** for small body copy on dark backgrounds.
3. **Yellow (`#FFE08A`) — Attention, Warnings & Irreversible Unsubscribe:**
   - Reserved for caution states and the separate, irreversible unsubscribe flow.
   - Use near-black (`#121316`) text on yellow badges (`14.40:1` AAA contrast).
4. **Neutral Foundation (`#121316`, `#2A2C31`, `#F3F1EC`, `#A19E96`):**
   - Carbon background `#121316`, elevated/border panel gray `#2A2C31`, warm off-white primary text `#F3F1EC`, and muted warm gray `#A19E96` for secondary copy.

### Exact color tokens & WCAG 2.1 contrast table

| Token | Hex | Role | WCAG contrast ratio |
|---|---|---|---|
| `background` | `#121316` | Primary dark canvas & Return Fold ink on orange/yellow | — |
| `panel` | `#2A2C31` | Card borders, window chrome, secondary surfaces | `12.38:1` with `#F3F1EC` (AAA) |
| `text` | `#F3F1EC` | Primary off-white text & `CleanYour` on dark | `16.46:1` on `#121316` (AAA) |
| `muted` | `#A19E96` | Secondary copy, subtitles, technical metadata | `6.94:1` on `#121316` (AA) / `5.22:1` on `#2A2C31` (AA) |
| `orange` | `#FFB38A` | Logo tile, `Mail` on dark, Plan / primary CTA | `10.67:1` with `#121316` (AAA) / `8.03:1` on `#2A2C31` (AAA) |
| `yellow` | `#FFE08A` | Warnings & irreversible unsubscribe badges | `14.40:1` with `#121316` (AAA) / `10.83:1` on `#2A2C31` (AAA) |
| `mint` | `#A8E6CF` | Journal & undo step markers, ribbon third segment | `13.17:1` on `#121316` (AA Large / UI) |
| `light-canvas` | `#F3F1EC` | Light-background surface (`light.svg`) | `16.46:1` with `#121316` (AAA) |
| `light-secondary` | `#4E4D48` | Supporting text on `#F3F1EC` light canvas | `7.50:1` on `#F3F1EC` (AAA) |
| `light-amber` | `#7A5A00` | Accessible `Mail` wordmark accent on `#F3F1EC` | `5.65:1` on `#F3F1EC` (AA) |

---

## 3. Three-stripe ribbon usage

- **Keep the symbol solid:** `symbol.svg`, `favicon.svg`, `app-icon.svg`, `mono.svg`, and `app-icon-mono.svg` never split the tile or glyph into three colors. The tile is solid `#FFB38A` with `#121316` ink.
- **Unequal, orange-led weighting:** The three-stripe accent uses a **2 : 1 : 1** or **3 : 1 : 1** ratio (`#FFB38A` orange first and widest, followed by `#FFE08A` yellow and `#A8E6CF` mint) so orange remains the unmistakable primary brand color.
- **Calm, horizontal structure:** Use the ribbon as a thin (`4–6 px`) horizontal top border on banners/cards or as a compact (`128–144 px` wide, `4–5 px` tall) horizontal section divider beneath lockup headers.
- **Where not to use:** Never angle the ribbon as a diagonal background slash, never place it behind body text, and never include it inside `favicon.svg` or `symbol.svg`.

---

## 4. Logo, wordmark & desktop app icon rules

- **Symbol (`symbol.svg`, 512×512):** `#121316` background, `#FFB38A` tile (`x=40, y=40, width=432, height=432, rx=112`), `#121316` Return Fold stroke (`stroke-width=30`). Minimum size: `16 px` (`24 px` standalone).
- **Favicon (`favicon.svg`, 64×64):** Simplified 64-unit grid (`x=2, y=2, width=60, height=60, rx=16`, `stroke-width=4.5`) for `16–32 px` browser tabs.
- **Desktop App Icon (`app-icon.svg`, 1024×1024):** `832×832` rounded square (`rx=192`) with `96 px` OS safe margins, `#121316` outer bezel, `#2A2C31` inner rim, and `#FFB38A` inner badge (`720×720`, `rx=156`). Works cleanly on both dark and light macOS Docks and Windows taskbars from `32 px` to `1024 px`.
- **Monochrome (`mono.svg` & `app-icon-mono.svg`):** Single `#121316` ink outline with transparent fill for embossing, stamps, and monochrome system trays.
- **Wordmark (`wordmark.svg`, 604×96) & Lockups (`lockup-horizontal.svg`, `lockup-stacked.svg`, `light.svg`):** Outlined `<path>` geometry (`CleanYourMail`). Minimum width: `120 px` for wordmark alone, `160 px` for horizontal/light/stacked lockups. Clear space around any mark is `25%` of the visible tile width.
- **Supporting typography (`banner.svg`, `social.svg`, `preview.html`):** System UI stack `"Segoe UI", "Helvetica Neue", Arial, sans-serif` and technical stack `Consolas, Menlo, monospace`. Convert `<text>` in banners/cards to outlines only if required by a print vendor.

---

## 5. Do / Don’t

### Do
- Keep the exact `CleanYourMail` casing and both taglines (*“Your inbox, minus the noise.”* / *“Tu bandeja, sin el ruido.”*).
- State clearly that CleanYourMail reads **headers only** (never bodies/attachments) and that **reversible applies to moves, while unsubscribe is separate and irreversible**.
- Use near-black `#121316` text on `#FFB38A` orange and `#FFE08A` yellow fills.
- Use `#7A5A00` (not `#FFB38A`) for the `Mail` wordmark accent on light `#F3F1EC` backgrounds so text contrast stays above `4.5:1` (`5.65:1`).

### Don’t
- Do not color the envelope flap, body, and arrow in three different colors inside the symbol or app icon.
- Do not copy diagonal esports stripes, skewed parallelogram boxes, or condensed gaming typography.
- Do not use `#A8E6CF` mint for small body text on `#121316` or `#2A2C31`.
- Do not add AI sparkles, gradients, glows, fake user counts, testimonials, benchmark claims, or fixed test counts.

---

## 6. File map (`brand/final-spectrum/`)

| File | Dimensions / ViewBox | Purpose |
|---|---|---|
| `symbol.svg` | `512 × 512` | Solid orange `#FFB38A` Return Fold symbol on `#121316` background. |
| `favicon.svg` | `64 × 64` | Simplified `16–32 px` orange tile + `#121316` glyph (no ribbon). |
| `app-icon.svg` | `1024 × 1024` | Rounded-square desktop app icon with `96 px` safe margins and `#121316`/`#2A2C31` bezel. |
| `app-icon-mono.svg` | `1024 × 1024` | Single-color (`#121316`) desktop app icon with `96 px` safe margins. |
| `wordmark.svg` | `604 × 96` | Outlined `<path>` wordmark (`#F3F1EC` `CleanYour` + `#FFB38A` `Mail`). |
| `lockup-horizontal.svg` | `860 × 192` | Primary horizontal lockup with restrained 3-stripe structural accent. |
| `lockup-stacked.svg` | `640 × 640` | Square stacked lockup with centered 3-stripe structural bar. |
| `mono.svg` | `512 × 512` | Single-ink (`#121316`) outlined symbol. |
| `light.svg` | `860 × 192` | Light-background (`#F3F1EC`) lockup with `#121316` tile and `#7A5A00` accessible `Mail` accent. |
| `banner.svg` | `1600 × 440` | Repository banner with restrained top ribbon, taglines, and semantic step card. |
| `social.svg` | `1280 × 640` | Social / OG card with orange plan, mint undo, and yellow irreversible-unsubscribe roles. |
| `preview.html` | Responsive HTML | Offline QA preview including side-by-side comparison with `brand/final/`. |
| `README.md` | Markdown | Full Spectrum brand guide and recommendation. |

See [`docs/BRAND-SPECTRUM.md`](../../docs/BRAND-SPECTRUM.md) for the one-page cheat sheet and [`brand/final/README.md`](../final/README.md) for the original forest/lime package.

---

## 7. Recommendation: Replace Green or Keep Spectrum as an Alternate?

**Recommendation: Adopt Spectrum (`brand/final-spectrum/`) as the primary app-first identity—or offer it as the default dark theme while retaining Forest/Lime (`brand/final/`) as a classic CLI theme.**

Why **Spectrum** is exceptionally strong for an **app-first** CleanYourMail:
1. **Built-in semantic hierarchy for a safety-critical GUI:** Unlike the monochrome green/teal palette (where both safe moves and warnings have to borrow outside colors or rely on subtle green shades), Spectrum gives the desktop app a native, high-contrast functional vocabulary right out of the brand palette:
   - **Orange (`#FFB38A`)** = *Plan / Review before action* (primary constructive action).
   - **Mint (`#A8E6CF`)** = *Journal / Undo* (the verified way back).
   - **Yellow (`#FFE08A`)** = *Irreversible Unsubscribe / Caution* (visually separating irreversible network actions from reversible IMAP folder moves).
2. **Superior desktop dock differentiation:** Most developer and productivity utilities on macOS/Windows docks cluster in blues, teals, or dark greens. A warm `#FFB38A` badge framed in `#121316` carbon (`app-icon.svg`) is immediately scannable at `32 px` and `64 px` on both dark and light docks while feeling like an industrial-grade local tool (akin to classic hardware instruments and diagnostic tools).
3. **Neutral carbon UI surfaces (`#121316` / `#2A2C31`):** Dense email header tables (sender, subject, date, size, flags) are easier to scan over neutral warm carbon (`#121316` with `#F3F1EC` warm paper text at `16.46:1`) than over tinted green backgrounds, while reducing visual fatigue during long inbox triage sessions.
