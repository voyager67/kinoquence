# Model and provider adapters

Kinoquence separates the *model experience* from the *video pipeline*. Provider adapters use documented HTTP interfaces; prompt packs let users work in consumer apps manually.

| Provider | Adapter | Authentication | Notes |
|---|---|---|---|
| OpenAI API | Chat Completions | `OPENAI_API_KEY` | Uses API model IDs; a ChatGPT plan is not an API key |
| Anthropic API | Messages | `ANTHROPIC_API_KEY` | Dedicated request/response parser |
| Gemini API | Generate Content | `GEMINI_API_KEY` | Simple stateless text requests; key is sent in the `x-goog-api-key` header |
| xAI API | OpenAI-compatible Chat Completions | `XAI_API_KEY` | Uses xAI's OpenAI-compatible inference API |
| Ollama | OpenAI-compatible Chat Completions | optional `OLLAMA_API_KEY` for cloud; local server usually no key | Local models must be pulled and served separately |
| LM Studio | OpenAI-compatible Chat Completions | optional `LMSTUDIO_API_KEY` | Start its local server first |
| vLLM | OpenAI-compatible Chat Completions | optional `VLLM_API_KEY` | Use the endpoint and model identifier exposed by your deployment |
| llama.cpp server | OpenAI-compatible Chat Completions | optional `LLAMACPP_API_KEY` | Start its OpenAI-compatible server first |
| Other compatible services | configurable base URL | optional | API must implement the expected chat-completions request/response subset |

## Environment variables

Use a shell environment or a local `.env` file. Never commit a real API key. The CLI intentionally has no `--api-key` value parameter; do not put a secret in shell history or a process list. The optional `--api-key-env` flag accepts the *name* of an environment variable, not the secret itself.

| Provider | Default environment variable |
|---|---|
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Gemini | `GEMINI_API_KEY` |
| xAI | `XAI_API_KEY` |
| Ollama cloud | `OLLAMA_API_KEY` |

Create a private local `.env` from `.env.example`, then add only the keys you use. `.env` is excluded by `.gitignore`; on macOS/Linux, use `chmod 600 .env`.

For custom OpenAI-compatible endpoints, use `--base-url`. Provide the API root, commonly ending in `/v1`, not `/chat/completions`. When an API key is present, Kinoquence requires HTTPS for remote endpoints and permits plain HTTP only for loopback/local endpoints. Review custom endpoints before sending prompts.

## Consumer app workflow vs API workflow

ChatGPT, Claude, Gemini and Grok consumer applications may have features that are unavailable through their public APIs, and API keys are billed/managed separately. In a consumer app, use the prompt packs under `skills/` and manually export the returned JSON into `story.json`. Through the CLI, use the provider's API. The two workflows converge at the same portable storyboard schema.

## Compatibility claims

An adapter being implemented does not mean every model on that provider has been tested. Context length, model access, JSON consistency, tool restrictions, content filters, vision support and rate limits vary. Run the benchmark smoke test on the exact model and record the date/version. It measures only simple API/schema behavior—not script quality, animation quality or visual quality. Smoke-test artifacts store structural pass/fail results and response lengths, not raw provider responses.

**Gemini API note (checked 4 November 2026):** The current implementation uses `generateContent` for stateless text generation; it does not expose the Interactions API's state, background execution or tool orchestration. Google's API-key guidance recommends the `x-goog-api-key` header instead of putting keys in URLs: <https://ai.google.dev/gemini-api/docs/api-key> and <https://docs.cloud.google.com/docs/authentication/api-keys-best-practices>. The Gemini Interactions API documentation is at <https://ai.google.dev/gemini-api/docs/interactions-overview>.
