# CleanYourMail — Spectrum Brand Cheat Sheet

> **Primary app-first identity:** [Family](BRAND-FAMILY.md) — lavender envelope and gold return arrow aligned with CleanYourPhone. This document covers the **Spectrum Pastel alternate**.

**Previous colorway: Return Fold in the Spectrum palette.** CleanYourMail pairs the **Return Fold** envelope-and-undo mark (`↩`) with a neutral carbon canvas (`#121316`), warm off-white text (`#F3F1EC`), and three semantic signal colors: **Orange `#FFB38A`** (plan, primary action, logo tile), **Mint `#A8E6CF`** (journal & undo), and **Yellow `#FFE08A`** (attention & irreversible unsubscribe). Full specifications live in [`brand/final-spectrum/README.md`](../brand/final-spectrum/README.md).

## Identity essentials

- **Name:** `CleanYourMail` (capital **C**, **Y**, **M**; never rename, add spaces, or abbreviate).
- **One-liner:** CleanYourMail is a local-first IMAP cleanup product: a Python CLI and agent skill today, with a desktop app in development. It reads headers only, plans before action, and gives every move a way back.
- **Taglines:** **Your inbox, minus the noise.** · **Tu bandeja, sin el ruido.**
- **Brand idea:** **Control, not magic.**

## Semantic color roles & contrast ratios

- **Orange `#FFB38A` (Primary / Plan / Logo Tile):** Solid Return Fold tile, `Mail` in dark wordmark, primary CTAs, Step 1 (*Plan*). Always pair orange fills with near-black `#121316` text/ink (**10.67:1** AAA; `#FFB38A` on `#2A2C31` panel is **8.03:1** AAA).
- **Yellow `#FFE08A` (Attention / Irreversible Unsubscribe):** Warning states and separate unsubscribe badges. Always use near-black `#121316` text on yellow fills (**14.40:1** AAA; `#FFE08A` on `#2A2C31` is **10.83:1** AAA).
- **Mint `#A8E6CF` (Journal / Undo / Secondary Path):** Undo markers, journal badges, and third ribbon segment (**13.17:1** on `#121316`; **9.90:1** on `#2A2C31`). Use for step markers, icons, and large accents—never small body text on dark.
- **Neutrals:** Carbon background `#121316` · Panel gray `#2A2C31` · Off-white text `#F3F1EC` (**16.46:1** on `#121316`, **12.38:1** on `#2A2C31`) · Muted gray `#A19E96` (**6.94:1** on `#121316`, **5.22:1** on `#2A2C31`).
- **Light surface (`light.svg` on `#F3F1EC`):** Near-black tile/text `#121316` (**16.46:1**), secondary `#4E4D48` (**7.50:1**), and accessible deep amber `Mail` accent `#7A5A00` (**5.65:1** AA).

## Three-stripe ribbon & logo rules

- **Solid symbol tile:** Keep `symbol.svg`, `favicon.svg`, and `app-icon.svg` as a single solid `#FFB38A` tile with `#121316` ink. Never split the symbol into three colors or place the ribbon inside the 16 px favicon.
- **Restrained horizontal ribbon:** Use a thin (`4–6 px`), orange-dominant (`#FFB38A` / `#FFE08A` / `#A8E6CF`) horizontal rule as a top banner border or small section divider under lockup headers. Never use diagonal esports stripes or put the ribbon behind body copy.
- **Typography:** Wordmark (`wordmark.svg` and lockups) uses outlined `<path>` vectors. Supporting copy uses `"Segoe UI", "Helvetica Neue", Arial, sans-serif` and `Consolas, Menlo, monospace`.
- **Guardrail copy:** Always state **"headers only"** (never *"no email data at all"*) and state that **reversible applies to moves, while unsubscribe is separate and irreversible**.

## Asset map (`brand/final-spectrum/`) & recommendation

- **Icons & marks:** `symbol.svg` (512×512), `favicon.svg` (64×64 for 16–32 px), `app-icon.svg` (1024×1024 desktop icon with `96 px` safe margins), `app-icon-mono.svg` (1024×1024 one-ink), `mono.svg` (512×512 one-ink).
- **Wordmark & lockups:** `wordmark.svg` (604×96), `lockup-horizontal.svg` (860×192), `lockup-stacked.svg` (640×640), `light.svg` (860×192).
- **Cards & QA:** `banner.svg` (1600×440), `social.svg` (1280×640), `preview.html` (offline preview with side-by-side comparison against `brand/final/`).
- **Recommendation:** Adopt **Spectrum** as the primary app-first identity (or default dark UI theme) because its semantic triad—**Orange (Plan)**, **Mint (Undo/Journal)**, and **Yellow (Irreversible Unsubscribe)**—maps directly to CleanYourMail's safety architecture on a neutral `#121316` carbon workspace, while the `#FFB38A` app icon achieves standout visibility on desktop docks.
