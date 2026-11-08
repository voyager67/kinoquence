# Privacy and data flow

Kinoquence is designed as a local-first CLI and project format. It does not include telemetry, analytics, a cloud account, background uploads or hosted storage.

## What stays on the machine

- Storyboards, research notes, source records, asset manifests, generated audio, captions, export videos and QA reports are written to the local project or the locations you explicitly select.
- The renderer temporarily stages selected audio under `remotion/public/` and writes temporary render props under the project's `.kinoquence/` directory. Both temporary items are removed after the render attempt.
- A model draft is stored at `.kinoquence/last-draft.json`; the approved `story.json` is not replaced automatically.
- A provider smoke test stores provider/model identifiers, timestamps, structural pass/fail results, latency and response character counts. It does not store raw provider responses or raw error bodies.
- QA reports store the video filename, not the full local filesystem path. QA failure messages also suppress ffprobe/FFmpeg logs and local paths by default.

## What leaves the machine

When you run `kinoquence draft` or `kinoquence benchmark`, Kinoquence sends the prompt/topic or fixed smoke-test prompt to the API endpoint you configured. The content is sent to that provider under the provider's terms, privacy policy, retention settings and account configuration. Kinoquence cannot control what the provider retains or how it uses submitted content. Do not submit confidential work unless your provider agreement and settings permit it.

Consumer-app instruction packs are manual workflows. What you paste into ChatGPT, Claude, Gemini, Grok or another product is handled by that product, not by Kinoquence.

## Credentials

- API keys are read from environment variables or an untracked `.env` file.
- The command line deliberately does not accept raw key values.
- Gemini keys use the `x-goog-api-key` header rather than a URL query parameter.
- Provider error bodies and request URLs are not copied to error messages.
- A key-bearing request to a remote endpoint requires HTTPS. Plain HTTP is allowed only for loopback/local model servers.
- A custom HTTPS endpoint still receives the prompts and credentials you direct to it. Verify that endpoint before use.

## Publishing and sharing

The repository ignore rules exclude the default `projects/`, `exports/`, `benchmarks/results/` workspaces, local `.env` variants and common private key/certificate files. Before publishing a project, inspect `story.json`, `research/`, `.kinoquence/`, `assets.csv`, generated captions, QA output and media. They may contain unpublished ideas, local paths, private source notes, model output or personal information. Never publish `.env`, customer data, private assets, raw provider responses or unlicensed media.

These are implementation-level safeguards, not a security certification or a guarantee against malware, compromised machines, malicious dependencies or provider-side data handling.

## Diagnostics

Default render failures suppress renderer logs, which can contain private story text or local file paths. FFmpeg/ffprobe QA errors suppress diagnostic logs and local paths for the same reason. Detailed renderer debugging is intentionally a local/manual action.
