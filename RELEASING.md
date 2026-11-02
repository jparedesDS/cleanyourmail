# Releasing CleanYourMail

This is the maintainer checklist. CleanYourMail is distributed as a checkout, not as a wheel.

## Versioning

- **Patch** (`1.1.x`): documentation, CI, website metadata, or a small fix with no behavior change.
- **Minor** (`1.x.0`): new CLI behavior, provider support, or a safety rule that stays backward compatible.
- **Major** (`x.0.0`): an incompatible plan, journal, or configuration format.

The version lives in `tools/cym_version.py`. `CHANGELOG.md` is the source of the release notes.

## Before tagging

- [ ] Update `tools/cym_version.py` and add a `CHANGELOG.md` entry with its comparison link.
- [ ] Run the offline suite:
  ```bash
  python -m compileall -q tools tests
  python -m unittest discover -s tests -v
  python -m ruff check tools tests
  ```
- [ ] Update `softwareVersion` in `cleanyourmail-web/index.html` and `es.html`.
- [ ] If the JSON-LD block changed, recompute the CSP `sha256` hash in both pages and run the web tests:
  ```bash
  cd cleanyourmail-web
  python -m unittest discover -s tests -v
  ```
- [ ] Check the README command tables against `python tools/mail.py --help` in every translation.
- [ ] Run the provider smoke test in [`docs/VALIDATION.md`](docs/VALIDATION.md) for every provider you claim.
- [ ] Confirm the live website loads both languages and the release badge resolves.
- [ ] Upload `assets/social-preview.png` in **Settings → Social preview** (manual; the API is read-only).
- [ ] Confirm Discussions is enabled if the issue template or `AGENTS.md` links to it.

## Tag and publish

```bash
git tag -a vX.Y.Z -m "CleanYourMail X.Y.Z"
git push origin master
git push origin vX.Y.Z
gh release create vX.Y.Z --title "CleanYourMail X.Y.Z — short title" --notes "Release notes"
```

After publishing, verify the release page, the tag, the README badge, and the website metadata. If the
release changes the CLI, update `docs/VALIDATION.md` with the new tested version.
