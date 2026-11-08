from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


class QAError(RuntimeError):
    pass


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, capture_output=True, text=True, check=False, timeout=900)
    except FileNotFoundError as exc:
        raise QAError(f"Required executable not found: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise QAError(f"QA command timed out while running {Path(command[0]).name}") from exc


def inspect_video(video: Path) -> dict[str, Any]:
    if not video.is_file():
        raise QAError("Video file does not exist or is not a readable file")
    ffprobe = shutil.which("ffprobe")
    ffmpeg = shutil.which("ffmpeg")
    if not ffprobe or not ffmpeg:
        raise QAError("Both ffprobe and ffmpeg must be installed and available on PATH")

    probe = _run([ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)])
    if probe.returncode != 0:
        raise QAError(
            f"ffprobe failed (exit {probe.returncode}); diagnostic output was suppressed because it may contain local paths or metadata"
        )
    try:
        metadata = json.loads(probe.stdout)
    except json.JSONDecodeError as exc:
        raise QAError("ffprobe returned invalid JSON") from exc

    streams = metadata.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = float(metadata.get("format", {}).get("duration", 0) or 0)
    width = int(video_stream.get("width", 0) or 0)
    height = int(video_stream.get("height", 0) or 0)
    fps = video_stream.get("avg_frame_rate", "0/1")

    filters = "blackdetect=d=0.25:pix_th=0.10,freezedetect=n=-50dB:d=1.0"
    command = [ffmpeg, "-hide_banner", "-i", str(video), "-vf", filters]
    if audio_stream:
        command += ["-af", "ebur128=peak=true"]
    command += ["-f", "null", "-"]
    scan = _run(command)
    log = scan.stderr
    if scan.returncode != 0:
        raise QAError(
            f"ffmpeg QA scan failed (exit {scan.returncode}); diagnostic output was suppressed because it may contain local paths or metadata"
        )

    black = [{"start": float(a), "end": float(b), "duration": float(b) - float(a)}
             for a, b in re.findall(r"black_start:([0-9.]+)\s+black_end:([0-9.]+)", log)]
    freezes = [{"start": float(a), "end": float(b), "duration": float(b) - float(a)}
               for a, b in re.findall(r"freeze_start:([0-9.]+).*?freeze_end:([0-9.]+)", log, re.S)]
    integrated = re.findall(r"\bI:\s*(-?[0-9.]+)\s*LUFS", log)
    true_peak = re.findall(r"Peak:\s*(-?[0-9.]+)\s*dBFS", log)
    warnings: list[str] = []
    if height and width and height < width:
        warnings.append("Output is landscape; vertical shorts are usually 9:16.")
    if duration <= 0:
        warnings.append("Could not determine a positive video duration.")
    if any(item["duration"] >= 0.25 for item in black):
        warnings.append("Black frames or black gaps detected; inspect the timestamps.")
    if any(item["duration"] >= 1.0 for item in freezes):
        warnings.append("Potential frozen section detected; inspect the timestamps.")
    if audio_stream and not integrated:
        warnings.append("Audio loudness could not be parsed from ffmpeg output.")

    return {
        "file": video.name,
        "duration_seconds": duration,
        "width": width,
        "height": height,
        "fps": fps,
        "video_codec": video_stream.get("codec_name"),
        "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
        "black_spans": black,
        "freeze_spans": freezes,
        "integrated_loudness_lufs": float(integrated[-1]) if integrated else None,
        "true_peak_dbfs": float(true_peak[-1]) if true_peak else None,
        "warnings": warnings,
        "ffmpeg_exit_code": scan.returncode,
    }


def write_report(report: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return output
