---
name: kinoquence-short-studio
description: Plan, storyboard, render and quality-check original short-form animated videos using the Kinoquence portable story format. Use for documentary shorts, educational explainers, fictional mini-stories, promotional shorts, or when the user asks to use Kinoquence.
---

# Kinoquence skill for Claude

Read `docs/SCHEMA.md`, `docs/QUALITY.md` and `kinoquence/prompts/story_director.md` before editing the project. This skill is adapted for Claude Code; the core story format and CLI remain model-neutral.

## Production loop

1. Confirm format, audience, platform, language, target duration and story type.
2. For nonfiction, establish a source list and a claim-to-source map before writing. Mark unresolved claims; never improvise facts.
3. Produce a strong original script: hook → setup → escalation → reveal → explanation → consequence/payoff. Keep it conversational and timed.
4. Convert script into `story.json` with one main visual action per scene, concise captions, a camera move and normalized visual elements.
5. Run `kinoquence validate PROJECT`. Fix schema errors and review warnings.
6. Keep draft changes in `.kinoquence/last-draft.json` until approved. Do not overwrite the approved story silently.
7. Generate local audio, render with Remotion and run `kinoquence qa`. Inspect the resulting MP4; QA filters do not judge storytelling or fact integrity.
8. Export captions and credits. Check asset rights and citations before publication.

## Visual direction

Prefer intentional composition, clear silhouettes, layered depth, motivated camera movement, consistent character proportions, clean color contrast, readable captions and visual variety. The current vector/2.5D renderer supports vector primitives and a simple 2.5D camera transform; do not promise arbitrary 3D scenes or AI video generation.

## Safety and IP

Use original characters, voice scripts and stories. Do not reproduce existing creator videos, private reference footage, copyrighted characters or a living artist's distinctive style. Record licenses and attribution for all imported assets. Respect `CONTRIBUTING.md` and the codebase tests.
