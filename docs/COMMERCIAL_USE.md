# Commercial readiness and dependency notes

Kinoquence is a production workflow starter, not legal advice or a guarantee that an output is cleared for every commercial use.

## Important dependency considerations

- **Remotion:** as checked 4 November 2026, its pricing page states a free license for individuals and companies of up to three people, a Company License for collaborations/companies of four or more, and a separate Remotion for Automators plan for automated video products. Re-check eligibility, usage charges and current terms before monetising or building a hosted rendering product. <https://www.remotion.dev/docs/license/pricing>.
- **FFmpeg:** the default project/build is commonly LGPL, but optional GPL components change the applicable license. A distributor must check the exact binary/build configuration and comply with the relevant notices/source obligations. <https://ffmpeg.org/legal.html>
- **Fonts, music, voice, images and stock:** each asset has its own license and attribution requirements. Model output does not erase the rights of source assets used as inputs.
- **AI providers:** consumer chat subscriptions and API access are separate. API prices, model availability, rate limits, retention options, terms and geographic restrictions change; verify current official provider terms before commercial deployment.

## Product limitations in the 1.0.0 release candidate

The included renderer is a simple vector/2.5D scene compositor. The included audio generator creates a procedural music bed and a small set of synthetic sound cues. Word-level forced alignment, multilingual TTS, advanced 3D scene authoring, a GUI editor, hosted rendering and asset-library search are not included. These are not included in this release candidate; do not advertise them as current capabilities.

## Before selling a hosted service

1. Confirm Remotion licensing for your business/team and automated render volume.
2. Pin and audit all dependencies, including FFmpeg build flags.
3. Add privacy, retention, deletion and security controls for customer media and keys.
4. Isolate jobs and resource limits; validate model-generated data before passing it to a renderer or shell process.
5. Create a clear asset/source and user-output rights workflow.
6. Publish reproducible benchmarks, including failed cases and limitations.
