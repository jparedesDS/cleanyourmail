# CleanYourMail — Brand Cheat Sheet

**Final decision: Return Fold.** CleanYourMail replaces the old gradient-and-sparkle icon with the **Return Fold** mark: a bold envelope whose right and bottom perimeter folds continuously into a left-return undo arrow (`↩`) below a classic symmetric V-flap. It expresses mail plus a verified way back—**Control, not magic**—at every size from a 16 px favicon to a 1024 px desktop app icon. Full specifications and SVG masters live in [`brand/final/README.md`](../brand/final/README.md).

## Identity essentials

- **Name:** `CleanYourMail` (exact casing: capital **C**, **Y**, **M**; never rename, add spaces, or abbreviate).
- **One-liner:** CleanYourMail is a local-first desktop app—powered by a standard-library Python CLI engine—for reversible IMAP inbox cleanup that reads headers only, plans before action, and gives every move a way back.
- **Tagline (EN):** **Your inbox, minus the noise.**
- **Tagline (ES):** **Tu bandeja, sin el ruido.**
- **Core idea:** **Control, not magic.**

## Three pillars

1. **Local by construction.** Runs locally as a desktop GUI app with a Python 3.11+ stdlib CLI engine (MIT). No CleanYourMail account, no telemetry, no third-party API. Reads **headers only** (sender, subject, date, size, flags, unsubscribe headers)—never bodies or attachments.
2. **Plan before action.** Generates a reviewable plan before moving a single message. Protected mail stays untouched, and there is **no permanent deletion**. Supports Gmail, Outlook/Microsoft 365, Yahoo, iCloud, Fastmail, Proton Bridge, and custom IMAP with `UIDPLUS`/`MOVE`.
3. **A way back.** Every move is logged in an append-only local journal and verified by `Message-ID` (or `X-GM-MSGID`) on undo. **Reversible applies to moves, not unsubscribe; unsubscribe is separate and irreversible.**

## Voice rules

- **Calm, concrete, local-first.** Speak like a trustworthy local utility, not a "magic AI" assistant or growth SaaS.
- **Use exact verbs:** *scan headers*, *plan*, *review*, *move*, *archive*, *journal*, *verify*, *undo*.
- **State limits honestly:** Always distinguish reversible folder/archive moves from irreversible unsubscribe requests, and say *"headers only"* rather than *"no email data at all."*

## Do / Don’t

- **Do** lead with the desktop app as the primary visual interface and the Python CLI as the engine for power users and coding agents.
- **Do** use `app-icon.svg` for macOS/Windows docks and launchers, `favicon.svg` at 16–32 px, `light.svg` on light surfaces, and `mono.svg` / `app-icon-mono.svg` for single-ink uses.
- **Don’t** use sparkles, magic wands, robots, shields, clouds, or gradients.
- **Don’t** distort, rotate, recolor, or place the dark-surface wordmark on a light background.
- **Don’t** include fake user counts, testimonials, benchmark claims, or fixed test counts in brand visuals.

## Color, typography, logo & app-icon quick reference

- **Dark palette:** Background `#07100d` · Panel `#0d1a15` · Elevated `#11231b` · Text `#eef8ee` (17.72:1) · Secondary `#9eb4a7` (8.76:1) · Tertiary `#6f8578` (4.87:1) · Lime accent `#b9f36a` (14.78:1 with `#07100d`) · Teal secondary accent `#6ee7c8` (12.79:1).
- **Light palette (`light.svg`):** Canvas `#f4f8f1` · Primary ink/tile `#102019` (15.73:1) · Secondary `#42564b` (7.34:1) · Accessible deep-green `Mail` accent `#3f721c` (5.38:1). Never set small text in `#b9f36a` on light backgrounds.
- **Typography:** Wordmark (`wordmark.svg` and lockups) is font-independent outlined `<path>` geometry. Supporting UI/banner copy uses `"Segoe UI", "Helvetica Neue", Arial, sans-serif` and `Consolas, Menlo, monospace`.
- **Logo & app-icon assets (`brand/final/`):**
  - `symbol.svg` (512×512 dark symbol, min 16 px) · `favicon.svg` (64×64 simplified for 16–32 px) · `mono.svg` (512×512 one-ink stamp).
  - `app-icon.svg` (1024×1024 rounded-square desktop icon with `96 px` OS safe margins) · `app-icon-mono.svg` (1024×1024 single-color app icon).
  - `wordmark.svg` (min 120 px wide) · `lockup-horizontal.svg` & `light.svg` (min 160 px wide) · `lockup-stacked.svg` (640×640, min 160 px wide).
  - `banner.svg` (1600×440 repo banner) · `social.svg` (1280×640 OG card) · `preview.html` (offline QA page). Clear space around any mark is 25% of the visible tile width.
