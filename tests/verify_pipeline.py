"""Automated verification suite for a Content Automation Studio run directory."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image


def _probe_mean_volume_db(path: Path) -> float:
    res = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    m = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", res.stderr or "")
    return float(m.group(1)) if m else -99.0


def check_video(path: Path, expected_w: int, expected_h: int, max_sec: float | None = None) -> dict:
    assert path.exists(), f"Missing video: {path}"
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height",
        "-of",
        "json",
        str(path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)
    duration = float(data["format"]["duration"])
    v_streams = [s for s in data["streams"] if s["codec_type"] == "video"]
    a_streams = [s for s in data["streams"] if s["codec_type"] == "audio"]
    assert v_streams, f"No video stream in {path}"
    assert a_streams, f"No audio stream in {path}"
    assert v_streams[0]["width"] == expected_w, f"Width mismatch: {v_streams[0]['width']} != {expected_w}"
    assert v_streams[0]["height"] == expected_h, f"Height mismatch: {v_streams[0]['height']} != {expected_h}"
    assert duration > 2.0, f"Video too short: {duration}s"
    if max_sec is not None:
        assert duration <= max_sec, f"Video exceeds {max_sec}s limit: {duration}s"
    mean_db = _probe_mean_volume_db(path)
    assert mean_db > -40.0, f"Video audio appears silent/muted ({mean_db} dB) in {path}!"
    return {
        "file": path.name,
        "resolution": f"{v_streams[0]['width']}x{v_streams[0]['height']}",
        "video_codec": v_streams[0]["codec_name"],
        "audio_codec": a_streams[0]["codec_name"],
        "duration_sec": round(duration, 2),
        "mean_volume_db": mean_db,
        "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
    }


def check_image(path: Path, expected_w: int, expected_h: int) -> None:
    assert path.exists(), f"Missing image: {path}"
    with Image.open(path) as img:
        assert img.size == (expected_w, expected_h), f"Image size mismatch for {path.name}: {img.size} != {(expected_w, expected_h)}"


def verify_run(run_dir: Path) -> None:
    print(f"Verifying run directory: {run_dir}")
    assert (run_dir / "brief_and_scripts.json").exists()
    assert (run_dir / "PUBLISH_REPORT.md").exists()
    assert (run_dir / "report.json").exists()
    assert (run_dir / "publish_results.json").exists()
    assert (run_dir / "social_publish_payload.json").exists()

    # Verify Thumbnail & YouTube Long
    check_image(run_dir / "youtube_long" / "thumbnail.png", 1280, 720)
    long_info = check_video(run_dir / "youtube_long" / "video_16x9.mp4", 1920, 1080)
    assert (run_dir / "youtube_long" / "subtitles.srt").read_text(encoding="utf-8").strip()

    # Verify Shorts/Reels/TikTok
    short_info = check_video(run_dir / "shorts_reels_tiktok" / "video_9x16.mp4", 1080, 1920, max_sec=60.0)
    assert (run_dir / "shorts_reels_tiktok" / "subtitles.srt").read_text(encoding="utf-8").strip()

    # Verify 5 Carousel slides
    slides = sorted((run_dir / "carousel_social").glob("slide_*.png"))
    assert len(slides) == 5, f"Expected 5 carousel slides, found {len(slides)}"
    for s in slides:
        check_image(s, 1080, 1350)
    assert (run_dir / "carousel_social" / "captions_all_platforms.md").exists()

    # Verify Report JSON
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report["qa_passed_all"] is True, f"QA checks failed: {report['qa_checks']}"

    print("ALL VERIFICATION CHECKS PASSED!")
    print(json.dumps({"youtube_long": long_info, "shorts": short_info, "carousel_slides": len(slides), "qa_passed": True}, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        out_root = Path(__file__).resolve().parent.parent / "output"
        runs = sorted([p for p in out_root.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
        if not runs:
            raise SystemExit("No run directory found in output/")
        target = runs[0]
    else:
        target = Path(sys.argv[1]).resolve()
    verify_run(target)
