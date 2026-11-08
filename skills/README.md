# Cross-model instruction packs

| Environment | Entry point |
|---|---|
| ChatGPT Projects / custom GPT / Codex | `chatgpt/INSTRUCTIONS.md` |
| Claude Code | `claude/SKILL.md` |
| Gemini CLI / Gemini chat | `gemini/GEMINI.md` |
| Grok chat / xAI API | `grok/INSTRUCTIONS.md` |
| Ollama / LM Studio / vLLM / llama.cpp | `open-source/INSTRUCTIONS.md` |
| Cursor | `cursor/storyforge.mdc` |
| Other agents | Adapt the closest instruction pack to your environment; all packs use the shared schema in `docs/SCHEMA.md` |

All packs converge on the same `story.json` schema. They are instructions, not hidden integrations: availability of each model, tool call, API or consumer-app feature depends on the platform/account in use.
