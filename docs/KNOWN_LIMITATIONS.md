# Known limitations

Kinoquence `1.0.0-rc.3` is a public release candidate. The following boundaries matter when evaluating or using it.

## Renderer verification

- The repository includes a Remotion/React vector and 2.5D renderer, but a clean dependency installation, TypeScript check and complete Kinoquence-generated MP4 render have not yet been verified. The most recent npm install attempt timed out before creating a lockfile.
- The Remotion package manifest pins direct dependency versions but does not include a committed npm lockfile. Transitive dependency resolution may therefore change between installs.
- The bundled MP4 is an original motion-graphics overview of the project workflow. It is not a screen recording or a render produced by the Kinoquence renderer.

Before relying on the renderer, install dependencies in `remotion/`, run `npm run typecheck`, render a sample and inspect the resulting MP4 manually. Run `kinoquence qa` as an additional technical check, not as a substitute for visual review.

## Model and provider compatibility

- Provider adapters are implemented for the services listed in [Providers](PROVIDERS.md), but not every model, model version, endpoint or local server has been live-tested.
- Automated provider tests use controlled responses. They do not establish creative quality, universal compatibility, output consistency, cost or latency.
- Consumer chat-app workflows use instruction packs and manual JSON export; they are not hidden or automatic integrations with those apps.

Test the exact model ID, endpoint and settings you plan to use. Check output against the storyboard schema and manually review the resulting story.

## Production scope

- The renderer is a baseline vector/2.5D compositor, not a full 3D engine or professional nonlinear editor.
- Procedural audio provides a basic music bed and simple synthetic cues. It is not a replacement for licensed music libraries, professional sound design or voice production.
- FFmpeg checks selected technical conditions such as black spans, frozen sections and audio levels. These are heuristics and cannot judge storytelling, factual accuracy, copyright, accessibility or overall quality.
- Fact/source mapping is a traceability aid; a person must verify that cited sources support each factual claim.

## External requirements and licensing

The renderer requires Node.js/npm and Remotion dependencies. FFmpeg and ffprobe are external tools and are not bundled. Review [dependency notes](DEPENDENCIES.md), [asset licensing](ASSET_LICENSING.md) and [commercial-use considerations](COMMERCIAL_USE.md) for third-party license boundaries. API access and consumer subscriptions are separate; provider availability and terms can change.
