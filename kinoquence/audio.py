from __future__ import annotations

import math
import random
from array import array
from collections.abc import Sequence
import struct
import wave
from pathlib import Path
from typing import Any

from .utils import project_child_path, project_story_path, read_json, write_json
from .validate import MAX_STORY_SECONDS, validate_story

SAMPLE_RATE = 48_000


def _write_mono_wav(path: Path, samples: Sequence[float], sample_rate: int = SAMPLE_RATE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    peak = max((abs(s) for s in samples), default=0.0)
    scale = min(0.92 / peak, 1.0) if peak > 0 else 1.0
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(sample_rate)
        block = bytearray()
        for sample in samples:
            value = int(max(-1.0, min(1.0, sample * scale)) * 32767)
            block.extend(struct.pack("<h", value))
        out.writeframes(block)


def generate_music(duration_seconds: float, seed: int = 21, sample_rate: int = SAMPLE_RATE) -> array:
    """Create an original, deterministic ambient bed; no sampled or third-party music."""
    try:
        finite_duration = math.isfinite(duration_seconds)
    except (OverflowError, TypeError):
        finite_duration = False
    if (
        not isinstance(duration_seconds, (int, float))
        or isinstance(duration_seconds, bool)
        or not finite_duration
        or not 0 < duration_seconds <= MAX_STORY_SECONDS
    ):
        raise ValueError(f"Audio duration must be greater than 0 and no more than {MAX_STORY_SECONDS:g} seconds")
    if not isinstance(sample_rate, int) or isinstance(sample_rate, bool) or not 8_000 <= sample_rate <= SAMPLE_RATE:
        raise ValueError(f"Sample rate must be a whole number between 8000 and {SAMPLE_RATE} Hz")
    rng = random.Random(seed)
    duration = max(1, int(duration_seconds * sample_rate))
    notes = [261.63, 329.63, 392.00, 493.88, 220.00, 261.63, 329.63, 440.00]
    # Float32 buffers use 8x less memory than Python float lists while retaining
    # ample precision for the final 16-bit PCM WAV output.
    output = array("f", [0.0]) * duration
    beat_seconds = 0.75
    beat_frames = int(beat_seconds * sample_rate)
    for frame in range(duration):
        time_s = frame / sample_rate
        beat = int(time_s / beat_seconds)
        note = notes[(beat // 2) % len(notes)]
        phase = 2 * math.pi * note * time_s
        pad = math.sin(phase) * 0.055 + math.sin(phase * 0.5) * 0.018
        shimmer = math.sin(phase * 2.01 + 0.4) * 0.009
        local = frame % beat_frames
        pulse = math.exp(-local / (sample_rate * 0.16)) if local < sample_rate * 0.6 else 0.0
        pluck = math.sin(2 * math.pi * notes[(beat + 3) % len(notes)] * time_s) * pulse * 0.025
        fade_in = min(1.0, time_s / 1.8)
        fade_out = min(1.0, max(0.0, (duration_seconds - time_s) / 2.2))
        output[frame] = (pad + shimmer + pluck) * fade_in * fade_out
    # Tiny deterministic variation prevents an entirely static synthetic tone bed.
    for _ in range(max(1, int(duration_seconds * 1.5))):
        start = rng.randrange(0, duration)
        length = min(int(sample_rate * 0.12), duration - start)
        freq = rng.choice([523.25, 587.33, 659.25, 783.99])
        phase_offset = rng.random() * math.tau
        amp = rng.uniform(0.004, 0.009)
        for index in range(length):
            envelope = math.sin(math.pi * index / max(1, length)) ** 2
            output[start + index] += math.sin(math.tau * freq * index / sample_rate + phase_offset) * amp * envelope
    return output


def generate_sfx(story: dict[str, Any], sample_rate: int = SAMPLE_RATE) -> array:
    issues = [issue for issue in validate_story(story) if issue.severity == "error"]
    if issues:
        raise ValueError("Cannot generate sound effects from an invalid story: " + "; ".join(map(str, issues[:8])))
    if not isinstance(sample_rate, int) or isinstance(sample_rate, bool) or not 8_000 <= sample_rate <= SAMPLE_RATE:
        raise ValueError(f"Sample rate must be a whole number between 8000 and {SAMPLE_RATE} Hz")
    duration = sum(float(scene["duration_seconds"]) for scene in story["scenes"])
    total = max(1, int(duration * sample_rate))
    output = array("f", [0.0]) * total
    cursor = 0.0
    rng = random.Random(101)
    cues = {
        "soft_pop": (0.22, 520.0), "whoosh": (0.38, 180.0), "impact": (0.24, 95.0),
        "chime": (0.55, 880.0), "warm_chime": (0.75, 659.25), "rain_light": (0.70, 0.0),
        "birds_soft": (0.6, 1250.0),
    }
    for scene in story.get("scenes", []):
        cues_for_scene = scene.get("sfx", [])
        for cue in cues_for_scene if isinstance(cues_for_scene, list) else []:
            if cue not in cues:
                continue
            length_s, freq = cues[cue]
            start = min(total, int((cursor + min(0.22, float(scene.get("duration_seconds", 1)) * 0.2)) * sample_rate))
            length = min(int(length_s * sample_rate), total - start)
            for index in range(length):
                t = index / sample_rate
                envelope = math.exp(-5.5 * t / max(length_s, 0.01))
                if freq <= 0:
                    sample = rng.uniform(-1.0, 1.0) * envelope * 0.07
                else:
                    sample = math.sin(math.tau * freq * t) * envelope * 0.12
                    sample += math.sin(math.tau * freq * 1.51 * t) * envelope * 0.025
                output[start + index] += sample
        cursor += float(scene.get("duration_seconds", 0))
    return output


def synthesize_project(path: Path, seed: int = 21) -> tuple[Path, Path]:
    story_path = project_story_path(path)
    story = read_json(story_path)
    issues = [issue for issue in validate_story(story) if issue.severity == "error"]
    if issues:
        raise ValueError("Cannot generate audio from an invalid story: " + "; ".join(map(str, issues[:8])))
    duration = sum(float(scene["duration_seconds"]) for scene in story["scenes"])
    music = generate_music(duration, seed=seed)
    sfx = generate_sfx(story)
    project_dir = story_path.parent
    music_path = project_child_path(project_dir, "assets/generated_music.wav")
    sfx_path = project_child_path(project_dir, "assets/generated_sfx.wav")
    _write_mono_wav(music_path, music)
    _write_mono_wav(sfx_path, sfx)
    story.setdefault("assets", {})["music_audio"] = "assets/generated_music.wav"
    story.setdefault("assets", {})["sfx_audio"] = "assets/generated_sfx.wav"
    write_json(story_path, story)
    return music_path, sfx_path
