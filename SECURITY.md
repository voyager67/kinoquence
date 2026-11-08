# Security policy

## Supported versions

Security fixes target the latest published release line. This is the `1.0.0-rc.3` candidate; it is not a long-term-support promise.

## Reporting a vulnerability

Please do not publish credentials, private media, or a working exploit in a public issue. Use GitHub's private vulnerability reporting for the repository when it is enabled. Include the affected version, steps to reproduce, expected impact, and logs with secrets removed.

## Credential and privacy handling

- The CLI accepts API keys only through environment variables or an untracked local `.env` file. It intentionally does not accept secret values in command-line arguments, where shell history and process listings can expose them.
- `.env`, other local environment variants, generated `projects/`, `exports/` and benchmark result files are ignored by Git. Verify `git status` before every commit; ignore rules are a safety net, not an access-control boundary. Keep `.env` permissions restricted to your user account (for example, `chmod 600 .env` on macOS/Linux). Never commit keys, private media, model prompts containing confidential data, or customer data.
- Gemini keys are sent in the `x-goog-api-key` request header, not in the URL. Provider HTTP error bodies are not logged.
- When an API key is configured, Kinoquence refuses a non-loopback HTTP endpoint. Use HTTPS for remote endpoints. Review any custom endpoint before sending prompts to it.
- Kinoquence sends the prompt and topic you explicitly submit to the configured model provider. It does not silently upload project folders, media assets or telemetry. Provider retention and training terms are controlled by that provider and your account settings.

## Safe-use notes

- Treat model-generated JSON and media metadata as untrusted input; validate before rendering.
- Storyboards have safety limits on duration, resolution and scene complexity.
- Keep project audio assets inside the project directory. The renderer rejects absolute paths and paths that resolve outside the project, including symlink escapes. Temporary renderer copies and temporary render props are deleted after each render attempt.
- Do not render untrusted projects in a privileged account or on a machine containing secrets you would not expose to project code.
- Use resource limits when processing untrusted or unusually large projects.
- The included secret-pattern scan is heuristic and is not a substitute for a repository secret scanner or independent security review.

- Render output cannot replace the approved `story.json` or declared narration/music/SFX input files. Symlink output targets are rejected. Renderer stdout/stderr is suppressed by default on failure because it may include local story text or file paths. FFmpeg/ffprobe diagnostic output is also suppressed in QA errors because it can contain local paths or media metadata.


## Credential handling safeguards

Provider API keys are read from environment variables or an untracked local environment file. Keys are rejected if they contain control characters or exceed 4096 characters, and remote credential-bearing endpoints must use HTTPS. Provider redirects are refused, and provider response bodies and low-level network exception details are not written to user-facing errors or logs. These controls reduce common accidental-disclosure risks; they are not a substitute for secret scanning, dependency review or secure host configuration.
