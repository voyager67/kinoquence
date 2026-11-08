# Quality gates

A finished short should pass four different reviews. A zero-error JSON check is not a publish decision.

## 1. Story and factual integrity

- The opening beat creates a specific question or surprise.
- Every scene changes the story or advances the explanation.
- Narration is speakable at the planned pace.
- Factual claims are mapped to sources and verified by a human.
- No invented quotes, fake numbers, fake citations or deceptive reenactments are presented as actual footage.

## 2. Visual review

Review the rendered video at phone size and full size. Check composition, safe margins, readability, consistency, continuity, character anatomy, object scale, transitions, camera motion and whether the shot actually communicates the narration. Current vector renderer is a baseline style, not a full 3D engine.

## 3. Audio and accessibility

- Listen on headphones and a phone speaker.
- Check voice/music balance, clicks, clipping, sudden changes and silence.
- Check subtitle spelling, reading speed, line length and sync.
- Add human-reviewed captions for speech not represented in the narration field.

## 4. Technical QA

Run:

```bash
kinoquence qa exports/final.mp4
```

The FFmpeg pass reports black spans, long frozen sections, container metadata, loudness and true peak when available. Thresholds are heuristics; inspect the reported timestamps. Also check that the actual export is 9:16, the expected duration, frame rate and resolution.

## Release evidence

For each demo, keep `story.json`, prompts, provider/model/version, parameters, asset manifest, source map, hardware/OS, render command, render time, output file, QA report and a human review sheet. Publish failures and limitations as well as successful examples. Never compare models from one cherry-picked prompt only.
