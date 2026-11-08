# Story schema v1.0

A Kinoquence project is a normal directory containing `story.json`, media assets and provenance records. The schema is intentionally model-neutral and human-editable.

## Top-level fields

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | string | Currently `1.0` |
| `title` | string | Export title |
| `story_type` | enum | `fiction`, `nonfiction`, `hybrid`, `promotional`, `educational` |
| `language` | string | BCP-47 language tag recommended, e.g. `en`, `hi`, `en-IN` |
| `fps`, `width`, `height` | number | Render profile; default 30 fps, 1080×1920 |
| `target_duration_seconds` | number | Editorial target; actual duration is the sum of scene durations |
| `style` | string | Visual preset identifier |
| `palette` | string[] | Preferred CSS colours |
| `sources` | object[] | `id`, `title`, `url`, optional publisher/access date |
| `claims` | object[] | `claim`, `source_ids`; required for fact-based stories |
| `scenes` | object[] | Ordered shot/scene sequence |
| `assets` | object | Optional project-relative paths for `narration_audio`, `music_audio`, `sfx_audio` |

## Scene fields

- `id`: stable unique slug.
- `duration_seconds`: 0.5–60 seconds per scene; total duration is derived from all scenes and capped at 180 seconds.
- `narration`: voice-over text. Add a WAV track separately when ready.
- `caption`: short subtitle line for the scene.
- `sfx`: optional list of built-in procedural cue names.
- `camera_move`: `push_in`, `pull_out`, `pan_left`, `pan_right`, `tilt_up`, `tilt_down`, `drift`, or `static`.
- `visual`: `background`, optional `secondary_background`, optional title/subtitle and a list of visual elements.

## Visual elements

- `rect`, `ellipse`, `character`: `x`, `y`, `w`, `h`, optional `fill`, `rotation`.
- `line`: `x`, `y`, `x2`, `y2`, optional `stroke`, `stroke_width`.
- `polygon`: `points` as at least three `[x,y]` pairs, optional `fill`/`stroke`.
- `text`: `x`, `y`, `text`, optional `font_size` and `fill`.

Coordinates are expressed in a 100-unit-wide by 177.78-unit-high portrait grid. They are scaled into the configured output canvas. Colours must be six-digit hex values. A story can contain at most 100 scenes and 200 visual elements per scene; the canvas is capped at 8,294,400 pixels and each dimension at 3,840 pixels. The renderer currently implements this vector vocabulary; arbitrary SVG paths, imported image layers and generative video are not part of this release scope.

## Fact provenance

For a fact-based story, each factual claim must link to one or more source IDs in `sources`. This is a traceability structure, not a substitute for checking whether the sources actually support the claim. Keep primary sources where possible, record access dates, and review every claim manually before publication.
