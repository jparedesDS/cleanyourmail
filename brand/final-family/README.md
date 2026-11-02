# CleanYourMail — Family Brand Identity

## 1. The idea

CleanYourMail now follows the **CleanYourPhone family** language: a carbon rounded-square tile, a lavender outline and a single gold action. The mark is the **Return Fold**: an envelope whose right and bottom perimeter folds into a left-return arrow. The envelope is lavender; the return arrow is gold. The wordmark keeps “CleanYour” in off-white and “Mail” in lavender.

- **Name:** `CleanYourMail` (capital **C**, **Y**, **M**).
- **One-liner:** CleanYourMail is a local-first IMAP cleanup product: a Python CLI and agent skill today, with a desktop app in development. It reads headers only, plans before action, and gives every move a way back.
- **Taglines:** **Your inbox, minus the noise.** · **Tu bandeja, sin el ruido.**
- **Family idea:** **Control, not magic.**

## 2. Palette

| Token | Hex | Role |
|---|---|---|
| `carbon` | `#15161A` | Background and logo tile |
| `panel` | `#1C1E24` | Cards, terminal and secondary surfaces |
| `panel-2` | `#23252D` | Elevated panels and borders |
| `text` | `#ECE9E2` | Primary text |
| `muted` | `#A8A39B` | Secondary copy |
| `muted-2` | `#8E8A82` | Technical metadata |
| `gold` | `#E2C15C` | Primary action, plan, CTA, return arrow |
| `lavender` | `#A78BFA` | Envelope outline, links, journal/undo |
| `lavender-bright` | `#C4B5FD` | “Mail” wordmark accent |
| `coral` | `#D97A5E` | Functional warning and irreversible unsubscribe |

Contrast on carbon `#15161A`: gold **10.34:1**, lavender **6.64:1**, lavender bright **9.79:1**, text **14.91:1**, muted **7.21:1**, muted-2 **5.26:1**, coral **5.94:1**. Use near-black `#15161A` text on gold and coral fills.

## 3. Logo construction

- **Symbol:** 512×512 carbon tile (`rx=112`), lavender envelope (`#A78BFA`, 30-unit round stroke), gold return arrow (`#E2C15C`, 30-unit round stroke).
- **Favicon:** 64×64 simplified version for 16–32 px, same lavender/gold split.
- **App icon:** 1024×1024 carbon rounded square with 96 px safe margins and a subtle `#23252D` inner rim.
- **Wordmark:** outlined vector paths: `CleanYour` in `#ECE9E2`, `Mail` in `#C4B5FD`.
- **Lockups:** horizontal and stacked, with no three-stripe ribbon. The family uses a clean two-color mark, not a decorative spectrum bar.
- **Clear space:** 25% of the visible tile width around any mark.
- **Minimum sizes:** favicon 16 px; symbol 24 px standalone; horizontal/light lockup 160 px wide; wordmark 120 px wide.

## 4. Do / Don't

### Do

- Keep the lavender envelope and gold return arrow.
- Use gold for primary actions and plan/review.
- Use lavender for links, journal and undo.
- Reserve coral for the irreversible unsubscribe state only.
- Use the exact `CleanYourMail` casing.
- Say **headers only**, never “no email data at all”.
- Say **reversible moves**, not “everything is reversible”.

### Don't

- Don’t fill the symbol tile with gold or use the old sparkle.
- Don’t use purple gradients, neon glows, robots, shields or magic wands.
- Don’t use coral as a general brand color.
- Don’t put the dark-background wordmark on a light background without `light.svg`.
- Don’t include fake testimonials, user counts or fixed test counts.

## 5. File map

| File | Purpose |
|---|---|
| `symbol.svg` | 512×512 carbon symbol with lavender envelope and gold arrow |
| `favicon.svg` | 64×64 simplified mark for 16–32 px |
| `app-icon.svg` | 1024×1024 desktop app icon with safe margins |
| `app-icon-mono.svg` | Single-light-ink app icon |
| `wordmark.svg` | Outlined `CleanYourMail` wordmark |
| `lockup-horizontal.svg` | Primary horizontal lockup |
| `lockup-stacked.svg` | Stacked lockup for square placements |
| `light.svg` | Light-background horizontal lockup |
| `mono.svg` | Single-ink symbol for stamps |
| `banner.svg` | 1600×440 repository banner |
| `social.svg` | 1280×640 social/OG card |
| `preview.html` | Offline visual QA page |

## 6. Integration notes

- Website: replace `assets/logo.svg` and `assets/favicon.svg` with `favicon.svg`; replace `assets/banner.svg`/`banner.png` and `assets/og.svg`/`og.png` with the family assets.
- Repository: replace `assets/banner.png` and `assets/social-preview.png` with the family exports.
- Desktop app: use `app-icon.svg` for macOS/Windows bundles; `app-icon-mono.svg` for monochrome surfaces.
- The desktop app is in development. Today the CLI and agent skill are the available interfaces.
- Keep the CleanYourPhone family palette and the envelope/return-arrow split; do not reintroduce the previous Spectrum Pastel or Forest palettes as primary.
