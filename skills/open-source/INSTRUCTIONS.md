# Kinoquence instructions for open-source and local models

This prompt is intended for models served by Ollama, LM Studio, vLLM, llama.cpp or another OpenAI-compatible endpoint.

## Task
Produce an original short video story as one JSON object following `docs/SCHEMA.md`. Do not output markdown fences or commentary around the JSON. If the content is nonfiction/educational, include credible sources and a source ID for every factual claim. Never make up a source or exact measurement.

## Planning constraints
- Use a clear hook, setup, escalation, reveal and payoff.
- Keep one primary action per scene.
- Use normalized x/y visual coordinates, supported shape types and supported camera moves.
- Keep captions brief and narration speakable.
- Make scene durations positive and align them to a realistic speaking pace.
- Keep the composition vertical 9:16 unless requested otherwise.

## Reliability
If the output schema is too complex for the active model, ask for one scene at a time or generate a minimal plan first. Do not silently invent missing fields. The human operator runs `kinoquence validate` and reviews the draft before accepting it.
