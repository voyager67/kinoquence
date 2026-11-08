# Architecture

```text
ChatGPT / Claude / Gemini / Grok / local model
                 │
     prompt packs or provider HTTP adapter
                 │
       story.json (portable format)
                 │
       schema + provenance validation
                 │
  ┌──────────────┼──────────────┐
  │              │              │
Captions      Local audio    Asset/source audit
  │              │              │
  └──────────────┼──────────────┘
                 │
        Remotion + React renderer
                 │
             MP4 export
                 │
       FFmpeg / ffprobe QA report
                 │
       video + SRT + credits + QA
```

## Design decisions

- **Models plan; deterministic code renders.** The model is not asked to simulate a video editor or return binary video. It returns a structured plan that can be validated and edited.
- **Portable project format.** JSON, CSV, SRT, WAV and MP4 avoid account lock-in. The Python CLI uses only the standard library.
- **Provider adapters remain small.** OpenAI-compatible chat completions covers OpenAI, xAI and a number of local inference servers; Anthropic and Gemini have dedicated adapters.
- **Drafts are not auto-approved.** Model output is saved to `.kinoquence/last-draft.json`; the approved `story.json` is left untouched until a human accepts it.
- **Local-first privacy.** Files are not uploaded by the CLI. A provider call sends only the prompt/context the user chooses to provide.
- **Evidence over claims.** A compatibility smoke test records API/format behavior. It does not score creative quality or establish broad model reliability.
- **Human review is a release gate.** The QA filter catches selected technical faults, not bad storytelling, unsafe facts, copyright problems or misleading edits.

## Main modules

- `providers.py`: HTTP adapters and response parsing.
- `draft.py`: prompt + model response parsing; keeps candidate drafts separate.
- `validate.py`: schema, timing and attribution checks.
- `audio.py`: original procedural music/SFX generation.
- `captions.py`: scene-timed SRT output.
- `render.py`: project-media staging and Remotion invocation.
- `qa.py`: ffprobe metadata, FFmpeg black/freeze/loudness inspection.
- `assets.py`: attribution page generation from manifest.
