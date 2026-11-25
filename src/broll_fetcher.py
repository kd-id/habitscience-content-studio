"""FREE Real HD Moving Stock B-Roll Video Fetcher via Pexels Video API (Zero Watermark, Royalty-Free)."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import requests


def _extract_broll_query(scene: dict[str, Any]) -> str:
    raw = str(scene.get("broll_query") or scene.get("visual_headline") or scene.get("visual_prompt") or "").lower()
    mapping = [
        (("scroll", "phone", "smartphone", "notification"), "person scrolling smartphone night dark"),
        (("sleep", "morning", "sunrise", "dawn", "wake"), "morning sunlight desk coffee"),
        (("brain", "neuron", "dopamine", "mind", "science"), "abstract glowing particles dark blue"),
        (("focus", "deep work", "desk", "notebook", "journal", "write"), "person writing notebook desk minimal"),
        (("time", "clock", "hourglass", "minute", "days", "habit"), "hourglass timer clock macro"),
        (("stress", "burnout", "cliff", "tired", "fog", "procrastin"), "tired person working laptop night"),
    ]
    for keywords, query in mapping:
        if any(k in raw for k in keywords):
            return query
    words = [w for w in re.findall(r"[a-z]+", raw) if len(w) > 3][:3]
    return " ".join(words) if words else "minimalist desk focus working"


def fetch_pexels_broll_clip(
    scene: dict[str, Any],
    out_mp4: Path,
    is_short: bool = False,
    used_ids: set[int] | None = None,
) -> Path | None:
    """Download a free HD moving B-roll clip from Pexels if PEXELS_API_KEY is configured."""
    api_key = os.getenv("PEXELS_API_KEY", "").strip()
    if not api_key:
        return None

    query = _extract_broll_query(scene)
    orientation = "portrait" if is_short else "landscape"
    try:
        resp = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": api_key},
            params={"query": query, "orientation": orientation, "per_page": 8, "size": "medium"},
            timeout=20,
        )
        if resp.status_code != 200:
            print(f"[broll] Pexels HTTP {resp.status_code}: {resp.text[:140]}", flush=True)
            return None

        videos = resp.json().get("videos") or []
        chosen = None
        for v in videos:
            vid = int(v.get("id", 0))
            if used_ids is not None and vid in used_ids:
                continue
            chosen = v
            if used_ids is not None:
                used_ids.add(vid)
            break
        if not chosen and videos:
            chosen = videos[0]
        if not chosen:
            return None

        files = chosen.get("video_files") or []
        # Prefer 1080p/720p MP4 stream
        mp4s = [f for f in files if f.get("file_type") == "video/mp4" and f.get("link")]
        if not mp4s:
            return None
        mp4s.sort(key=lambda f: abs(int(f.get("width") or 1280) - (1080 if is_short else 1920)))
        dl_url = mp4s[0]["link"]

        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(dl_url, stream=True, timeout=45) as dl:
            dl.raise_for_status()
            with out_mp4.open("wb") as fh:
                for chunk in dl.iter_content(chunk_size=131072):
                    if chunk:
                        fh.write(chunk)

        if out_mp4.exists() and out_mp4.stat().st_size > 20_000:
            print(f"[broll] Downloaded FREE Pexels HD clip ({query}) -> {out_mp4.name}", flush=True)
            return out_mp4
    except Exception as exc:
        print(f"[broll] Pexels fetch failed ({type(exc).__name__}): {str(exc)[:140]}", flush=True)
    return None
