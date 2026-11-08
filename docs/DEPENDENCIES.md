# Dependencies and licensing notes

## Python runtime

The Python CLI and supporting modules use the Python standard library only. The project requires Python 3.10 or newer. No telemetry or mandatory Python network dependency is included.

## Renderer runtime

The renderer uses these exact direct package versions in `remotion/package.json`:

| Package | Version | Role |
|---|---:|---|
| `remotion` | `4.0.540` | Composition/runtime |
| `@remotion/cli` | `4.0.540` | Studio and render CLI |
| `@remotion/media` | `4.0.540` | Audio media component used by the composition |
| `react` | `19.1.0` | UI runtime |
| `react-dom` | `19.1.0` | DOM runtime |
| `typescript` | `5.8.3` | Type checking |
| `@types/react` | `19.1.8` | React type declarations |

These are direct dependency pins, not a complete dependency lock. The candidate does **not** contain a committed `package-lock.json`; npm may resolve transitive dependencies differently over time. For this release candidate, install with `npm install` from `remotion/`. Before creating a stable tag, create and review `package-lock.json` with the release Node/npm toolchain, then validate from a clean checkout with `npm ci`. Remotion and `@remotion/media` must use the same exact release. The composition imports the current `<Audio>` component from `@remotion/media`: <https://www.remotion.dev/docs/media/audio>. Package metadata for Remotion 4.0.540 was checked against npm on 4 November 2026: <https://www.npmjs.com/package/remotion?activeTab=versions>.

Remotion has its own licensing model. As checked 4 November 2026, its pricing page distinguishes free use for individuals and companies of up to three people, Company Licensing for larger collaborations/companies, and separate licensing for automated video products. Eligibility depends on the actual organization and use case: <https://www.remotion.dev/docs/license/pricing>.

## Media tools

FFmpeg and ffprobe are external executables and are not bundled. The precise FFmpeg build and enabled components affect licensing. Review <https://ffmpeg.org/legal.html> and the terms for the binary you install. Fonts, music, voice recordings, stock media and other imported assets keep their own licenses; record them in each project's `assets.csv`.

## Python package distribution

The supported installation path for this repository is a source checkout with `python -m pip install -e .`. A standalone Python wheel is not a complete renderer distribution: it does not bundle the Remotion source tree or Node dependencies. Do not publish the Python wheel as a self-contained Kinoquence release until packaging is redesigned and tested.

## License inventory

- Kinoquence source code: MIT (`LICENSE`).
- Project documentation and original written templates: CC BY 4.0 (`LICENSE-DOCS.md`).
- Remotion, React, TypeScript, FFmpeg and user-supplied media: their respective licenses; not relicensed by Kinoquence.
- No copyrighted reference frames from the inspiration repository are redistributed. See `NOTICE.md`.
