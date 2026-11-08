from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .providers import ProviderConfig, generate_text


CASES = [
    {
        "id": "schema-following",
        "prompt": 'Return exactly this JSON object and no markdown: {"ok":true,"count":3}',
        "expected": {"ok": True, "count": 3},
    },
    {
        "id": "short-pacing",
        "prompt": "Return JSON with an array named beats containing exactly 4 short phrases for a 20-second educational video. No other text.",
        "expected_keys": ["beats"],
    },
    {
        "id": "visual-planning",
        "prompt": "Return JSON with camera_move set to one of push_in, pull_out, pan_left, pan_right, tilt_up, tilt_down, drift, static and explain it in one short string field named reason.",
        "expected_keys": ["camera_move", "reason"],
    },
]


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-_")
    return (cleaned[:80] or "model").replace("..", "-")


def run_benchmark(config: ProviderConfig, output_dir: Path) -> Path:
    results: list[dict[str, Any]] = []
    for case in CASES:
        started = time.perf_counter()
        try:
            response = generate_text(
                config,
                "You are taking a deterministic API smoke test. Follow the requested output format exactly.",
                case["prompt"],
            )
            latency = round(time.perf_counter() - started, 3)
            candidate = response.strip().removeprefix("```json").removesuffix("```").strip()
            try:
                parsed = json.loads(candidate)
                parse_ok = isinstance(parsed, dict)
            except json.JSONDecodeError:
                parsed, parse_ok = None, False
            structure_ok = parse_ok
            if structure_ok and "expected" in case:
                structure_ok = parsed == case["expected"]
            if structure_ok and "expected_keys" in case:
                structure_ok = all(key in parsed for key in case["expected_keys"])
            results.append({
                "case_id": case["id"],
                "ok": bool(structure_ok),
                "parse_ok": parse_ok,
                "latency_seconds": latency,
                "response_characters": len(response),
            })
        except Exception as exc:  # Keep the smoke test running, but never persist raw error text.
            results.append({
                "case_id": case["id"],
                "ok": False,
                "error_type": type(exc).__name__,
                "latency_seconds": round(time.perf_counter() - started, 3),
            })

    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{_safe_filename(config.provider)}-{_safe_filename(config.model)}-{stamp}.json"
    output = output_dir / filename
    payload = {
        "schema_version": "1.0",
        "created_at_utc": stamp,
        "provider": config.provider,
        "model": config.model,
        "test_count": len(results),
        "passed": sum(1 for item in results if item.get("ok")),
        "results": results,
        "notice": "Smoke test only. This is not a quality benchmark or proof of general model compatibility. Raw provider responses and error messages are not stored.",
    }
    output.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return output
