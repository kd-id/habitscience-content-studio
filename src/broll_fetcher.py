"""Multi-source FREE HD/4K Real Cinema B-Roll Video Fetcher (Zero Watermark, Commercial-Safe).

Priority order:
  1. Pexels Video API (PEXELS_API_KEY — free 200 req/hr at pexels.com/api)
  2. Pixabay Video API (PIXABAY_API_KEY — free 100 req/min at pixabay.com/api/docs/)
  3. Local user B-Roll folder (assets/broll/*.mp4|*.webm|*.mov)
  4. Visually-Verified Curated Wikimedia Commons CC0/CC-BY Cinema Pool (zero API key, zero watermarks/text!)
  5. Strict-filtered Wikimedia Commons dynamic HD video search fallback

All downloaded clips are cached under `assets/broll_cache/` so subsequent renders are instant.
"""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import Any

import requests

USER_AGENT = "HabitSainsContentStudio/6.0 (https://github.com/kd-id/habitscience-content-studio)"

# Visually verified pure cinema CC0/CC-BY HD clips (zero burned-in timestamps, zero logos, zero screencasts)
CURATED_WIKIMEDIA_CLIPS: list[dict[str, Any]] = [
    {
        "title": "File:Raindrops against the window in the night city, Las Palmas.webm",
        "tags": ("scroll", "phone", "night", "rain", "distract", "dopamine", "trap", "tired", "fog", "hook"),
        "orient": "landscape",
    },
    {
        "title": "File:Clock by Veo 2.webm",
        "tags": ("time", "clock", "23", "minute", "66", "90", "residue", "mechanism", "focus", "cycle", "study"),
        "orient": "landscape",
    },
    {
        "title": "File:Timelapse at Marine Drive Mumbai.webm",
        "tags": ("city", "scroll", "traffic", "fast", "feed", "stimulation", "dopamine", "night", "urban", "busy"),
        "orient": "landscape",
    },
    {
        "title": "File:Stars Over Seventh Lake.webm",
        "tags": ("brain", "neuron", "myelin", "neuroscience", "cosmos", "deep", "calm", "mind", "science", "residue"),
        "orient": "landscape",
    },
    {
        "title": "File:Second Glow (video).webm",
        "tags": ("morning", "sunrise", "dawn", "wake", "reset", "new", "day", "clarity", "experiment", "challenge"),
        "orient": "landscape",
    },
    {
        "title": "File:From the mountain high, the forest stretches like a green ocean, kissed by mist and rain — a silent breath of nature, and continue with move on.webm",
        "tags": ("protocol", "calm", "stillness", "forest", "nature", "reset", "breathe", "habit", "shield", "step"),
        "orient": "landscape",
    },
    {
        "title": "File:Clouds at sunset (time lapse).webm",
        "tags": ("sunset", "evening", "7-day", "days", "progress", "compound", "quiet", "peace", "time", "experiment"),
        "orient": "landscape",
    },
    {
        "title": "File:A cup of Kenyan Coffee.webm",
        "tags": ("coffee", "morning", "ritual", "desk", "routine", "habit", "wake", "protocol"),
        "orient": "portrait",
    },
]

REJECT_TITLE_KEYWORDS = (
    "wikipedia", "wikimedia", "wiki", "promo", "tutorial", "screencast", "screenshot",
    "lecture", "interview", "speech", "conference", "presentation", "logo", "banner",
    "trailer", "dvorak", "diagram", "blender", "minecraft", "foundation", "test", "demo",
)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _cache_dir() -> Path:
    d = _project_root() / "assets" / "broll_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def build_broll_queries_for_scene(scene: dict[str, Any], count: int = 3) -> list[str]:
    """Generate distinct visual B-roll search queries for fast 4-5s cinema cuts within one scene."""
    raw = f"{scene.get('broll_query', '')} {scene.get('section', '')} {scene.get('visual_headline', '')} {scene.get('narration', '')}".lower()
    pool: list[str] = []

    rules = [
        (("scroll", "phone", "smartphone", "feed", "swipe", "app"), ["smartphone night dark", "city lights bokeh night", "typing laptop desk"]),
        (("morning", "sunrise", "dawn", "wake", "coffee"), ["sunrise clouds timelapse", "coffee pouring morning", "morning sunlight window"]),
        (("brain", "neuron", "dopamine", "myelin", "neuroscience", "residue"), ["stars night sky timelapse", "abstract light particles", "city traffic timelapse night"]),
        (("focus", "deep work", "study", "read", "write", "notebook", "journal"), ["writing notebook desk", "minimalist workspace coffee", "calm library study"]),
        (("time", "clock", "hourglass", "minute", "days", "21", "66", "23", "90"), ["clock macro gears", "sunset clouds timelapse", "sand hourglass"]),
        (("habit", "protocol", "step", "bridge", "reset", "calm", "stillness"), ["forest morning mist", "calm ocean waves aerial", "mountain sunrise timelapse"]),
        (("boring", "tired", "fog", "burnout", "stress", "exhaust"), ["raindrops window night", "working late desk", "foggy forest morning"]),
    ]
    for triggers, queries in rules:
        if any(t in raw for t in triggers):
            for q in queries:
                if q not in pool:
                    pool.append(q)

    evergreen = [
        "city night timelapse",
        "sunrise clouds timelapse",
        "raindrops window night",
        "clock macro gears",
        "stars night sky timelapse",
        "forest sunlight morning",
        "sunset clouds timelapse",
    ]
    for q in evergreen:
        if q not in pool:
            pool.append(q)

    return pool[: max(count, 1)]


def _download_with_cache(url: str, cache_key: str, ext: str = ".mp4", max_bytes: int = 45 * 1024 * 1024) -> Path | None:
    digest = hashlib.sha1(cache_key.encode("utf-8")).hexdigest()[:12]
    target = _cache_dir() / f"{digest}{ext}"
    if target.exists() and target.stat().st_size > 25_000:
        return target

    tmp = target.with_suffix(ext + ".part")
    try:
        with requests.get(url, headers={"User-Agent": USER_AGENT}, stream=True, timeout=45) as resp:
            resp.raise_for_status()
            clen = int(resp.headers.get("Content-Length") or 0)
            if clen and clen > max_bytes:
                return None
            written = 0
            with tmp.open("wb") as fh:
                for chunk in resp.iter_content(chunk_size=131072):
                    if not chunk:
                        continue
                    written += len(chunk)
                    if written > max_bytes:
                        fh.close()
                        tmp.unlink(missing_ok=True)
                        return None
                    fh.write(chunk)
        if tmp.exists() and tmp.stat().st_size > 25_000:
            tmp.replace(target)
            return target
    except Exception:
        tmp.unlink(missing_ok=True)
    return None


def _fetch_from_pexels(query: str, is_short: bool, used_keys: set[str]) -> Path | None:
    api_key = os.getenv("PEXELS_API_KEY", "").strip()
    if not api_key:
        return None
    orientation = "portrait" if is_short else "landscape"
    try:
        resp = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": api_key, "User-Agent": USER_AGENT},
            params={"query": query, "orientation": orientation, "per_page": 10, "size": "medium"},
            timeout=20,
        )
        if resp.status_code != 200:
            return None
        for v in resp.json().get("videos") or []:
            key = f"pexels:{v.get('id')}"
            if key in used_keys:
                continue
            files = [f for f in (v.get("video_files") or []) if f.get("file_type") == "video/mp4" and f.get("link")]
            if not files:
                continue
            target_w = 1080 if is_short else 1920
            files.sort(key=lambda f: abs(int(f.get("width") or 1280) - target_w))
            clip = _download_with_cache(files[0]["link"], key, ext=".mp4")
            if clip:
                used_keys.add(key)
                print(f"[broll] Pexels HD clip ({query}) -> {clip.name}", flush=True)
                return clip
    except Exception:
        return None
    return None


def _fetch_from_pixabay(query: str, is_short: bool, used_keys: set[str]) -> Path | None:
    api_key = os.getenv("PIXABAY_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        resp = requests.get(
            "https://pixabay.com/api/videos/",
            headers={"User-Agent": USER_AGENT},
            params={"key": api_key, "q": query, "per_page": 10, "safesearch": "true"},
            timeout=20,
        )
        if resp.status_code != 200:
            return None
        for hit in resp.json().get("hits") or []:
            key = f"pixabay:{hit.get('id')}"
            if key in used_keys:
                continue
            vids = hit.get("videos") or {}
            chosen = vids.get("medium") or vids.get("large") or vids.get("small")
            if not chosen or not chosen.get("url"):
                continue
            clip = _download_with_cache(chosen["url"], key, ext=".mp4")
            if clip:
                used_keys.add(key)
                print(f"[broll] Pixabay HD clip ({query}) -> {clip.name}", flush=True)
                return clip
    except Exception:
        return None
    return None


def _fetch_from_local_broll(used_keys: set[str]) -> Path | None:
    broll_dir = _project_root() / "assets" / "broll"
    if not broll_dir.exists():
        return None
    clips = sorted([p for p in broll_dir.iterdir() if p.suffix.lower() in (".mp4", ".webm", ".mov")])
    for c in clips:
        key = f"local:{c.name}"
        if key not in used_keys:
            used_keys.add(key)
            return c
    return None


def _fetch_wikimedia_by_title(title: str) -> Path | None:
    """Resolve an exact verified Wikimedia Commons File: title cleanly (uses cache first!)."""
    cache_key = f"wikimedia:{title}"
    digest = hashlib.sha1(cache_key.encode("utf-8")).hexdigest()[:12]
    for ext in (".webm", ".mp4"):
        cached = _cache_dir() / f"{digest}{ext}"
        if cached.exists() and cached.stat().st_size > 25_000:
            return cached

    try:
        time.sleep(0.25)
        resp = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            headers={"User-Agent": USER_AGENT},
            params={
                "action": "query",
                "titles": title,
                "prop": "videoinfo",
                "viprop": "url|size|mime",
                "format": "json",
            },
            timeout=20,
        )
        if resp.status_code != 200:
            return None
        pages = (resp.json().get("query") or {}).get("pages") or {}
        for page in pages.values():
            vi_list = page.get("videoinfo") or []
            if not vi_list:
                continue
            vi = vi_list[0]
            url = str(vi.get("url", ""))
            mime = str(vi.get("mime", "")).lower()
            if not url:
                continue
            ext = ".webm" if "webm" in mime else ".mp4"
            clip = _download_with_cache(url, cache_key, ext=ext, max_bytes=36 * 1024 * 1024)
            if clip:
                print(f"[broll] Verified Cinema CC clip -> {clip.name} ({title[:42]})", flush=True)
                return clip
    except Exception:
        return None
    return None


def _fetch_from_curated_wikimedia(scene: dict[str, Any], is_short: bool, used_keys: set[str], allow_reuse: bool = False) -> Path | None:
    """Pick the best mood-matched clip from our visually-verified cinema pool."""
    raw = f"{scene.get('broll_query', '')} {scene.get('section', '')} {scene.get('visual_headline', '')} {scene.get('narration', '')}".lower()
    scored: list[tuple[int, dict[str, Any]]] = []
    for item in CURATED_WIKIMEDIA_CLIPS:
        title = item["title"]
        key = f"wikimedia:{title}"
        if not allow_reuse and key in used_keys:
            continue
        # Keep vertical-only clip reserved for Shorts (or last resort for landscape)
        orient = item["orient"]
        if not is_short and orient == "portrait":
            orient_score = -20
        elif is_short and orient == "portrait":
            orient_score = 10
        else:
            orient_score = 4
        tag_hits = sum(3 for t in item["tags"] if t in raw)
        scored.append((orient_score + tag_hits, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    for _, item in scored:
        title = item["title"]
        clip = _fetch_wikimedia_by_title(title)
        if clip:
            used_keys.add(f"wikimedia:{title}")
            return clip
    return None


def _fetch_from_wikimedia_search(query: str, is_short: bool, used_keys: set[str]) -> Path | None:
    """Strict-filtered Wikimedia Commons HD video fallback when more clips are needed."""
    try:
        time.sleep(0.35)
        resp = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            headers={"User-Agent": USER_AGENT},
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": f"filetype:video {query}",
                "gsrnamespace": 6,
                "gsrlimit": 10,
                "prop": "videoinfo",
                "viprop": "url|size|mime",
                "format": "json",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        pages = (resp.json().get("query") or {}).get("pages") or {}
        candidates: list[tuple[int, str, str, str]] = []
        for page in pages.values():
            title = str(page.get("title", ""))
            low_t = title.lower()
            if any(bad in low_t for bad in REJECT_TITLE_KEYWORDS):
                continue
            vi_list = page.get("videoinfo") or []
            if not vi_list:
                continue
            vi = vi_list[0]
            mime = str(vi.get("mime", "")).lower()
            url = str(vi.get("url", ""))
            w = int(vi.get("width") or 0)
            h = int(vi.get("height") or 0)
            size = int(vi.get("size") or 0)
            dur = float(vi.get("duration") or 0.0)
            if not url or ("webm" not in mime and "mp4" not in mime):
                continue
            if size <= 150_000 or size > 32 * 1024 * 1024 or dur < 3.5 or max(w, h) < 960:
                continue
            orient_bonus = 1000 if ((is_short and h >= w) or (not is_short and w >= h)) else 0
            ext = ".webm" if "webm" in mime else ".mp4"
            candidates.append((orient_bonus + min(w, 1920), title, url, ext))

        candidates.sort(key=lambda x: x[0], reverse=True)
        for _, title, url, ext in candidates:
            key = f"wikimedia:{title}"
            if key in used_keys:
                continue
            clip = _download_with_cache(url, key, ext=ext, max_bytes=32 * 1024 * 1024)
            if clip:
                used_keys.add(key)
                print(f"[broll] Wikimedia HD clip ({query}) -> {clip.name}", flush=True)
                return clip
    except Exception:
        return None
    return None


def fetch_broll_sequence(
    scene: dict[str, Any],
    num_clips: int = 3,
    is_short: bool = False,
    used_keys: set[str] | None = None,
) -> list[Path]:
    """Fetch `num_clips` distinct real moving HD cinema B-roll clips for fast 4-5s cuts."""
    if used_keys is None:
        used_keys = set()

    queries = build_broll_queries_for_scene(scene, count=max(num_clips + 2, 5))
    clips: list[Path] = []
    scene_paths: set[Path] = set()

    for idx_q in range(num_clips):
        q = queries[idx_q % len(queries)]
        clip = (
            _fetch_from_pexels(q, is_short=is_short, used_keys=used_keys)
            or _fetch_from_pixabay(q, is_short=is_short, used_keys=used_keys)
            or _fetch_from_local_broll(used_keys=used_keys)
            or _fetch_from_curated_wikimedia(scene, is_short=is_short, used_keys=used_keys, allow_reuse=False)
        )
        if clip and clip not in scene_paths:
            clips.append(clip)
            scene_paths.add(clip)

    # If a long multi-scene video exhausted unique curated clips, cycle curated pool cleanly across scenes
    # without repeating the same clip back-to-back inside the same scene!
    if len(clips) < num_clips:
        for item in CURATED_WIKIMEDIA_CLIPS:
            if len(clips) >= num_clips:
                break
            if not is_short and item["orient"] == "portrait":
                continue
            clip = _fetch_wikimedia_by_title(item["title"])
            if clip and clip not in scene_paths:
                clips.append(clip)
                scene_paths.add(clip)

    if not clips:
        fallback = _fetch_from_wikimedia_search(queries[0], is_short=is_short, used_keys=used_keys)
        if fallback:
            clips.append(fallback)

    return clips


# Backwards compatibility wrapper
def fetch_pexels_broll_clip(
    scene: dict[str, Any],
    out_mp4: Path,
    is_short: bool = False,
    used_ids: set[int] | None = None,
) -> Path | None:
    keys: set[str] = {f"legacy:{i}" for i in (used_ids or set())}
    seq = fetch_broll_sequence(scene, num_clips=1, is_short=is_short, used_keys=keys)
    return seq[0] if seq else None
