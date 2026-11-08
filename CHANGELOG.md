# Changelog

## 1.0.0-rc.3 — 2026-11-08

- Unified the public project identity as **Kinoquence** across the Python package, CLI, Remotion composition, visual assets, overview video and website.
- Added an original geometric K identity and refreshed the project banner, workflow illustration, artifact visual and 24-second motion-graphics overview.
- Updated the public README and showcase with concise feature descriptions, setup instructions, visuals and explicit verification boundaries.
- Retained model-provider adapters, portable storyboards, procedural audio, captions, asset credits, provenance support, technical QA, templates and provider instruction packs.
- Strengthened credential handling, path validation, safe error reporting and private-workspace exclusion.

This is a public release candidate. See [Known limitations](docs/KNOWN_LIMITATIONS.md) for renderer and live-provider verification status.


## Repository audit updates

- Removed duplicate prompt copies, obsolete Cursor filename and redundant placeholder files; kept only public user and contributor documentation.
- Added an explicit GitHub Pages deployment guide and disabled automatic deployment until the repository variable `PAGES_DEPLOY_ENABLED=true` is set.
- Added missing local-provider key placeholders and aligned cross-model skill references with the packaged prompt path.
- Rejected API keys containing control characters or exceeding the safety limit; added regression tests for header-injection and error-message leakage.
- Replaced Python-float audio sample lists with compact float32 buffers to reduce peak memory use for long projects.
- Updated GitHub Actions to Node 24-compatible action major versions.
