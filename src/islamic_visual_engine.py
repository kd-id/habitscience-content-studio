"""Studio v10 — Islamic Luminous Visuals Engine (3 Distinct Programmatic HTML5/Canvas Modes).

Inspired directly by classic luminous Islamic educational shorts & contemplative storytelling:
  1. `islamic_luminous_sky`    — Prayer-time sky cycle (Fajr -> Dhuhr -> Asr -> Maghrib -> Isha) OR
                                 symbolic nature transformation (embers/storm -> rain -> blooming meadow),
                                 mosque & palm silhouettes reflected in rippling water, crisp Amiri Arabic
                                 calligraphy + transliteration + verified citation + guided step pill counter.
  2. `islamic_gold_visualizer` — Luxury Obsidian Black & 24k Gold canvas, subtle rotating Islamic geometric
                                 star pattern, real voice-reactive radial golden sunburst visualizer with
                                 Surah/Ayah centerpiece badge, synchronized word-by-word gold Arabic &
                                 English karaoke reflection + brain/peace insight pill.
  3. `islamic_particle_map`    — Deep cosmic mood-shifting storytelling canvas with 420+ glowing particles
                                 morphing smoothly via spring physics between symbolic shapes (crescent,
                                 ocean droplet ripple, protective cave arch, calm mind waves, 1/3 balance
                                 rings, sunrise horizon, and circular constellation summary map), paired
                                 with crisp white-outlined conversational subtitles & verified dalil badge.

All 3 modes:
  - Support BOTH 9:16 (1080x1920 Shorts/Reels/TikTok) AND 16:9 (1920x1080 YouTube Long)
  - Embed open-source OFL Amiri calligraphy fonts (works identically offline on Windows & Ubuntu)
  - Use 100% instrument-free nature ambiance (dawn_breeze / gentle_rain / calm_water)
  - Strictly respect Islamic adab (zero depiction of Prophets, crisp RTL Arabic with harakat)
  - Output Meta & YouTube compliant H.264 Main yuv420p (TV range), 48kHz stereo AAC, +faststart, <=58.2s Shorts.
"""

from __future__ import annotations

import base64
import json
import math
import struct
import subprocess
from pathlib import Path
from typing import Any

from src.html_motion_overlay import find_chrome_executable
from src.sfx_engine import mix_nature_voice_soundscape
from src.voiceover import TrackAudioBundle, probe_duration_sec

ISLAMIC_VISUAL_MODES: tuple[str, ...] = (
    "islamic_luminous_sky",
    "islamic_gold_visualizer",
    "islamic_particle_map",
)

_FONT_B64_CACHE: dict[str, str] = {}


def _load_amiri_font_css() -> str:
    """Embed local OFL Amiri Regular & Bold TTF fonts as base64 @font-face for deterministic RTL Arabic."""
    root = Path(__file__).resolve().parent.parent / "assets" / "fonts"
    rules: list[str] = []
    for fname, weight in (("Amiri-Regular.ttf", "400"), ("Amiri-Bold.ttf", "700")):
        fpath = root / fname
        if not fpath.exists():
            continue
        if fname not in _FONT_B64_CACHE:
            _FONT_B64_CACHE[fname] = base64.b64encode(fpath.read_bytes()).decode("ascii")
        b64 = _FONT_B64_CACHE[fname]
        rules.append(
            f"@font-face {{ font-family: 'AmiriCalligraphy'; src: url(data:font/ttf;base64,{b64}) format('truetype'); "
            f"font-weight: {weight}; font-style: normal; font-display: block; }}"
        )
    return "\n".join(rules)


def _extract_audio_rms_envelope(audio_path: Path, fps: int, duration_sec: float) -> list[float]:
    """Compute smooth normalized [0.0..1.0] per-frame RMS amplitude envelope from voiceover audio."""
    total_frames = max(int(round(duration_sec * fps)), 1)
    sample_rate = 8000
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(audio_path),
        "-ac", "1", "-ar", str(sample_rate), "-f", "s16le", "pipe:1",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, check=True)
        raw = res.stdout
    except Exception:
        return [0.25 + 0.15 * abs(math.sin(i * 0.25)) for i in range(total_frames)]

    total_samples = len(raw) // 2
    if total_samples < 100:
        return [0.2] * total_frames

    samples = struct.unpack(f"<{total_samples}h", raw[: total_samples * 2])
    spf = max(int(sample_rate / float(fps)), 1)
    rms_vals: list[float] = []
    for f_i in range(total_frames):
        st = min(f_i * spf, total_samples - 1)
        en = min(st + spf, total_samples)
        chunk = samples[st:en]
        if not chunk:
            rms_vals.append(0.0)
            continue
        mean_sq = sum(s * s for s in chunk) / float(len(chunk))
        rms_vals.append(math.sqrt(mean_sq) / 32768.0)

    peak = max(max(rms_vals), 1e-4)
    # Smooth envelope lightly for fluid visualizer motion
    norm = [min(v / (peak * 0.85), 1.0) for v in rms_vals]
    smooth: list[float] = []
    prev = 0.0
    for v in norm:
        prev = prev * 0.45 + v * 0.55
        smooth.append(round(prev, 3))
    return smooth


def _build_scene_and_caption_timeline(
    scenes_meta: list[dict[str, Any]],
    audio_bundle: TrackAudioBundle,
    pause_sec: float,
    tempo: float = 1.0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float]:
    """Align scene cards and word-level subtitle captions accurately with TrackAudioBundle (adjusted for tempo)."""
    scene_items: list[dict[str, Any]] = []
    captions: list[dict[str, Any]] = []
    cursor = 0.0
    scale = 1.0 / max(tempo, 0.5)

    for idx, sr in enumerate(audio_bundle.scene_results):
        s_dur = max(sr.duration_sec * scale, 1.0)
        seg_dur = s_dur + (pause_sec * scale)
        meta = scenes_meta[idx] if idx < len(scenes_meta) else {}

        headline = str(meta.get("visual_headline") or meta.get("section") or f"Step {idx + 1}").strip()
        badge = str(meta.get("badge") or meta.get("section") or f"STEP {idx + 1}").strip()
        callout = str(meta.get("on_screen_callout") or "").strip()
        bullets = [str(b).strip() for b in (meta.get("bullet_points") or []) if str(b).strip()][:3]

        scene_items.append({
            "idx": idx,
            "start": round(cursor, 3),
            "end": round(cursor + seg_dur, 3),
            "badge": badge,
            "headline": headline,
            "callout": callout,
            "bullets": bullets,
            "narration": sr.text.strip(),
        })

        # Build crisp word-timed caption chunks (4-6 words per chunk) for smooth synchronized display
        word_events = [t for t in (sr.word_timings or []) if t.get("type") == "WordBoundary" and t.get("text")]
        if word_events:
            words_timed = [
                {
                    "w": str(we["text"]).strip(),
                    "s": round(cursor + float(we["start"]) * scale, 3),
                    "e": round(cursor + float(we["end"]) * scale, 3),
                }
                for we in word_events
            ]
        else:
            raw_words = sr.text.split()
            if raw_words:
                weights = [max(len(w), 3) + (4 if w.endswith((".", "!", "?")) else 2 if w.endswith((",", ";", "—")) else 0) for w in raw_words]
                tot_w = float(max(sum(weights), 1))
                wc = cursor
                words_timed = []
                for w, wt in zip(raw_words, weights):
                    wd = s_dur * (wt / tot_w)
                    words_timed.append({"w": w, "s": round(wc, 3), "e": round(wc + wd, 3)})
                    wc += wd
            else:
                words_timed = []

        # Group timed words into readable 5-7 word lines
        chunk_buf: list[dict[str, Any]] = []
        for wt in words_timed:
            chunk_buf.append(wt)
            ends_clause = wt["w"].endswith((".", "!", "?", "—", ";")) or (len(chunk_buf) >= 4 and wt["w"].endswith(","))
            if len(chunk_buf) >= 6 or ends_clause:
                captions.append({
                    "start": chunk_buf[0]["s"],
                    "end": max(chunk_buf[-1]["e"], chunk_buf[0]["s"] + 0.35),
                    "words": chunk_buf,
                })
                chunk_buf = []
        if chunk_buf:
            captions.append({
                "start": chunk_buf[0]["s"],
                "end": max(chunk_buf[-1]["e"], chunk_buf[0]["s"] + 0.35),
                "words": chunk_buf,
            })

        cursor += seg_dur

    return scene_items, captions, round(max(cursor, 2.0), 3)


def _resolve_dalil_payload(topic_meta: dict[str, Any] | None, scenes_meta: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract verified Arabic verse/hadith + citation payload with safe reverent defaults."""
    meta = topic_meta or {}
    dalil = meta.get("dalil") if isinstance(meta.get("dalil"), dict) else {}

    arabic = str(dalil.get("arabic") or "أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ").strip()
    translit = str(dalil.get("transliteration") or "Ala bi-dhikrillahi tatma'innul-qulub").strip()
    translation = str(dalil.get("translation") or "Verily, in the remembrance of Allah do hearts find rest.").strip()
    citation = str(dalil.get("citation") or "QUR'AN 13:28").strip()
    surah_ar = str(dalil.get("surah_or_book_ar") or "حِكْمَة وَسُنَّة").strip()
    badge_num = str(dalil.get("badge_num") or "").strip()
    if not badge_num:
        # Derive clean badge number from citation (e.g. "QUR'AN 13:28" -> "13:28", "SAHIH AL-BUKHARI 6464" -> "6464")
        parts = citation.split()
        badge_num = parts[-1] if parts and any(ch.isdigit() for ch in parts[-1]) else "SUNNAH"

    badge_label = "AYAH" if "QUR" in citation.upper() else "HADITH"
    visual_theme = str(dalil.get("visual_theme") or "prayer_sky").strip()
    particle_shapes = dalil.get("particle_shapes")
    if not isinstance(particle_shapes, list) or not particle_shapes:
        particle_shapes = ["crescent_stars", "ocean_drop", "brain_light", "summary_constellation"]

    topic = str(meta.get("topic") or (scenes_meta[0].get("visual_headline") if scenes_meta else "Prophetic Wisdom & Calm Mind")).strip()
    pillar_label = str(meta.get("pillar_label") or "Prophetic Habits & Brain Science").strip()
    handle = str(meta.get("channel_handle") or "@HabitSains").strip()

    return {
        "topic": topic,
        "pillar_label": pillar_label,
        "handle": handle,
        "arabic": arabic,
        "transliteration": translit,
        "translation": translation,
        "citation": citation.upper(),
        "surah_ar": surah_ar,
        "badge_num": badge_num,
        "badge_label": badge_label,
        "visual_theme": visual_theme,
        "particle_shapes": [str(s) for s in particle_shapes],
    }


# ---------------------------------------------------------------------------
# HTML5 Canvas + Amiri Calligraphy Templates for All 3 Studio v10 Modes
# ---------------------------------------------------------------------------

def _build_luminous_sky_html(payload: dict[str, Any], width: int, height: int) -> str:
    """Mode 1: `islamic_luminous_sky` (Ref #1 Minute Wisdom + Ref #2 5 Duas Sky-Cycle Mosque Reflection)."""
    font_css = _load_amiri_font_css()
    cfg_json = json.dumps(payload, ensure_ascii=False)
    is_short = height >= width
    top_pad = 96 if is_short else 44
    ar_size = 56 if is_short else 52
    tr_size = 24 if is_short else 22
    en_size = 21 if is_short else 20
    sub_size = 33 if is_short else 32
    card_max_w = 640 if is_short else 980

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  {font_css}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: {width}px; height: {height}px; overflow: hidden;
    background: #081226;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    color: #F8FAFC;
  }}
  #bgCanvas {{ position: absolute; inset: 0; width: {width}px; height: {height}px; display: block; }}

  .stage {{
    position: absolute; inset: 0; z-index: 5;
    display: flex; flex-direction: column; align-items: center;
    padding: {top_pad}px 36px 40px;
    pointer-events: none;
  }}

  .eyebrow {{
    font-size: {16 if is_short else 15}px; font-weight: 700; letter-spacing: 3.4px;
    text-transform: uppercase; color: #F5D076;
    text-shadow: 0 2px 10px rgba(0,0,0,0.45);
    margin-bottom: {14 if is_short else 8}px;
  }}

  .headline-pill {{
    font-size: {22 if is_short else 20}px; font-weight: 700; color: rgba(255,255,255,0.95);
    text-align: center; max-width: {card_max_w}px; line-height: 1.28;
    text-shadow: 0 3px 14px rgba(0,0,0,0.52);
    margin-bottom: {20 if is_short else 12}px;
  }}

  .dalil-box {{
    width: 100%; max-width: {card_max_w}px;
    background: rgba(8, 16, 34, 0.34);
    border: 1px solid rgba(245, 208, 118, 0.28);
    border-radius: 22px;
    padding: {22 if is_short else 16}px {26 if is_short else 30}px;
    text-align: center;
    backdrop-filter: blur(8px);
    box-shadow: 0 14px 36px rgba(0,0,0,0.28);
  }}

  .arabic-text {{
    font-family: 'AmiriCalligraphy', 'Amiri', 'Traditional Arabic', 'Segoe UI', serif;
    direction: rtl; unicode-bidi: embed;
    font-size: {ar_size}px; font-weight: 700; line-height: 1.58;
    color: #FFFDF7;
    text-shadow: 0 3px 16px rgba(245, 208, 118, 0.38), 0 2px 8px rgba(0,0,0,0.55);
    margin-bottom: 10px;
  }}

  .translit {{
    font-size: {tr_size}px; font-weight: 600; color: #FFFFFF;
    letter-spacing: 0.2px; line-height: 1.35;
    text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    margin-bottom: 8px;
  }}

  .translation {{
    font-size: {en_size}px; font-style: italic; font-weight: 400;
    color: rgba(241, 245, 249, 0.90); line-height: 1.38;
    margin-bottom: 14px;
  }}

  .citation-row {{
    display: inline-flex; align-items: center; gap: 10px;
    padding: 5px 16px; border-radius: 999px;
    background: rgba(245, 208, 118, 0.16);
    border: 1px solid rgba(245, 208, 118, 0.50);
    font-size: 14px; font-weight: 700; letter-spacing: 2.2px;
    color: #FDE68A; text-transform: uppercase;
  }}

  /* Guided step progress pill (Ref #1 & Ref #2 signature!) */
  .step-pill {{
    margin-top: {18 if is_short else 12}px;
    display: inline-flex; align-items: center; gap: 12px;
    padding: 8px 20px; border-radius: 999px;
    background: rgba(7, 15, 30, 0.48);
    border: 1px solid rgba(255,255,255,0.22);
    font-size: 14px; font-weight: 700; letter-spacing: 1.8px; color: #E2E8F0;
  }}
  .dots {{ display: inline-flex; align-items: center; gap: 7px; }}
  .dot {{
    width: 10px; height: 10px; border-radius: 50%;
    background: rgba(255,255,255,0.28);
    transition: transform 0.2s ease;
  }}
  .dot.done {{ background: #F5D076; box-shadow: 0 0 8px rgba(245,208,118,0.75); }}
  .dot.active {{ background: #FFFFFF; transform: scale(1.28); box-shadow: 0 0 12px #FDE68A; }}

  /* Synchronized conversational subtitle above the horizon/water */
  .sub-area {{
    position: absolute; left: 32px; right: 32px;
    bottom: {195 if is_short else 72}px;
    z-index: 8; text-align: center;
  }}
  .sub-card {{
    display: inline-block; max-width: {640 if is_short else 960}px;
    padding: 12px 24px; border-radius: 16px;
    background: rgba(5, 11, 24, 0.62);
    border: 1px solid rgba(255,255,255,0.16);
    backdrop-filter: blur(6px);
    box-shadow: 0 10px 28px rgba(0,0,0,0.45);
  }}
  .sub-text {{
    font-size: {sub_size}px; font-weight: 700; line-height: 1.28;
    color: #F8FAFC;
    text-shadow: 0 2px 6px rgba(0,0,0,0.65);
  }}
  .sub-text .hi {{ color: #FDE68A; }}

  .brand-foot {{
    position: absolute; bottom: {32 if is_short else 20}px; left: 0; right: 0;
    z-index: 9; text-align: center;
    font-size: 15px; font-weight: 600; letter-spacing: 2px;
    color: rgba(255,255,255,0.68);
    text-shadow: 0 2px 6px rgba(0,0,0,0.7);
  }}
</style>
</head>
<body>
<canvas id="bgCanvas" width="{width}" height="{height}"></canvas>
<div class="stage">
  <div class="eyebrow" id="eyebrow">PROPHETIC HABIT • 1 OF 6</div>
  <div class="headline-pill" id="headline"></div>
  <div class="dalil-box" id="dalilBox">
    <div class="arabic-text" id="arText"></div>
    <div class="translit" id="trText"></div>
    <div class="translation" id="enText"></div>
    <div class="citation-row" id="citText"></div>
  </div>
  <div class="step-pill">
    <span id="stepLabel">REFLECT</span>
    <span class="dots" id="dotsWrap"></span>
  </div>
</div>

<div class="sub-area">
  <div class="sub-card" id="subCard"><div class="sub-text" id="subText"></div></div>
</div>
<div class="brand-foot" id="brandFoot"></div>

<script>
const CFG = {cfg_json};
const W = {width}, H = {height};
const IS_SHORT = H >= W;
const ctx = document.getElementById('bgCanvas').getContext('2d');

// Pre-populate static dalil elements
document.getElementById('arText').textContent = CFG.dalil.arabic;
document.getElementById('trText').textContent = CFG.dalil.transliteration;
document.getElementById('enText').textContent = '"' + CFG.dalil.translation + '"';
document.getElementById('citText').textContent = '✦  ' + CFG.dalil.citation + '  ✦';
document.getElementById('brandFoot').textContent = CFG.dalil.handle + '  •  Save & Share the Sunnah';

const dotsWrap = document.getElementById('dotsWrap');
const numScenes = Math.max(CFG.scenes.length, 1);
for (let i = 0; i < numScenes; i++) {{
  const d = document.createElement('span');
  d.className = 'dot';
  dotsWrap.appendChild(d);
}}

// 5-stage luminous prayer sky palettes: Fajr -> Sunrise -> Dhuhr -> Asr -> Maghrib -> Isha
// sunY kept in the clear open sky band (0.66..0.78 of horizonY) right above the mosque silhouette!
const SKY_STAGES = [
  {{ top: [15, 23, 62],   mid: [49, 54, 118],  bot: [148, 92, 138], sunY: 0.72, sunCol: [253, 210, 152], starA: 0.72, mode: 'fajr' }},
  {{ top: [26, 75, 134],  mid: [72, 136, 186], bot: [238, 174, 126], sunY: 0.76, sunCol: [255, 224, 150], starA: 0.15, mode: 'sunrise' }},
  {{ top: [22, 92, 168],  mid: [64, 148, 212], bot: [164, 212, 240], sunY: 0.67, sunCol: [255, 246, 200], starA: 0.0,  mode: 'dhuhr' }},
  {{ top: [46, 74, 126],  mid: [182, 126, 88], bot: [246, 186, 108], sunY: 0.71, sunCol: [255, 216, 128], starA: 0.08, mode: 'asr' }},
  {{ top: [48, 26, 76],   mid: [158, 66, 92],  bot: [244, 146, 86],  sunY: 0.77, sunCol: [255, 166, 98],  starA: 0.45, mode: 'maghrib' }},
  {{ top: [7, 13, 34],    mid: [16, 29, 68],   bot: [34, 58, 106],   sunY: 0.68, sunCol: [248, 236, 186], starA: 0.95, mode: 'isha' }},
];

// Deterministic stars & fireflies/raindrops
const STARS = [];
for (let i = 0; i < 85; i++) {{
  STARS.push({{
    x: ((i * 197.3) % 1000) / 1000,
    y: ((i * 313.7) % 580) / 1000,
    r: 0.8 + (i % 4) * 0.45,
    ph: i * 1.13,
  }});
}}
const DROPS = [];
for (let i = 0; i < 42; i++) {{
  DROPS.push({{
    x: ((i * 137.5) % 1000) / 1000,
    speed: 0.42 + (i % 5) * 0.09,
    offset: (i * 0.23) % 1.0,
    len: 14 + (i % 4) * 5,
  }});
}}

function lerp(a, b, t) {{ return a + (b - a) * t; }}
function lerpRGB(c1, c2, t) {{
  return [Math.round(lerp(c1[0], c2[0], t)), Math.round(lerp(c1[1], c2[1], t)), Math.round(lerp(c1[2], c2[2], t))];
}}
function rgb(c, a = 1) {{ return `rgba(${{c[0]}},${{c[1]}},${{c[2]}},${{a}})`; }}

function drawMosqueSilhouette(horizonY, scale, t, isReflection) {{
  ctx.save();
  ctx.translate(W * 0.5, horizonY);
  if (isReflection) {{
    ctx.scale(1, -0.58);
    ctx.globalAlpha = 0.32;
  }}

  ctx.fillStyle = isReflection ? '#070F24' : '#081022';

  // Rolling distant ground
  ctx.beginPath();
  ctx.moveTo(-W * 0.52, 2);
  ctx.quadraticCurveTo(-W * 0.28, -26 * scale, 0, -14 * scale);
  ctx.quadraticCurveTo(W * 0.28, -28 * scale, W * 0.52, 2);
  ctx.closePath();
  ctx.fill();

  // Main mosque base
  const mw = 190 * scale, mh = 56 * scale;
  ctx.fillRect(-mw * 0.5, -mh, mw, mh + 4);

  // Central grand onion dome
  ctx.beginPath();
  ctx.moveTo(-58 * scale, -mh);
  ctx.bezierCurveTo(-64 * scale, -mh - 48 * scale, -26 * scale, -mh - 84 * scale, 0, -mh - 102 * scale);
  ctx.bezierCurveTo(26 * scale, -mh - 84 * scale, 64 * scale, -mh - 48 * scale, 58 * scale, -mh);
  ctx.closePath();
  ctx.fill();

  // Spire + crescent atop central dome
  ctx.fillRect(-1.8 * scale, -mh - 122 * scale, 3.6 * scale, 22 * scale);
  ctx.beginPath();
  ctx.arc(0, -mh - 126 * scale, 6 * scale, 0.25 * Math.PI, 1.85 * Math.PI);
  ctx.fill();

  // Twin side domes
  for (const dir of [-1, 1]) {{
    ctx.beginPath();
    ctx.arc(dir * 72 * scale, -mh, 28 * scale, Math.PI, 0);
    ctx.closePath();
    ctx.fill();
  }}

  // Twin slender minarets
  for (const dir of [-1, 1]) {{
    const mx = dir * 118 * scale;
    ctx.fillRect(mx - 8 * scale, -mh - 118 * scale, 16 * scale, mh + 120 * scale);
    ctx.fillRect(mx - 13 * scale, -mh - 92 * scale, 26 * scale, 7 * scale);
    ctx.beginPath();
    ctx.moveTo(mx - 8 * scale, -mh - 118 * scale);
    ctx.lineTo(mx, -mh - 152 * scale);
    ctx.lineTo(mx + 8 * scale, -mh - 118 * scale);
    ctx.closePath();
    ctx.fill();
  }}

  // Warm illuminated arched windows (only upright & soft glow in reflection)
  ctx.fillStyle = isReflection ? 'rgba(253, 214, 120, 0.45)' : 'rgba(253, 214, 120, 0.78)';
  for (const wx of [-46, -23, 0, 23, 46]) {{
    ctx.beginPath();
    ctx.arc(wx * scale, -28 * scale, 6 * scale, Math.PI, 0);
    ctx.lineTo((wx + 6) * scale, -10 * scale);
    ctx.lineTo((wx - 6) * scale, -10 * scale);
    ctx.closePath();
    ctx.fill();
  }}

  // Gentle swaying palm silhouettes on left & right banks
  ctx.fillStyle = isReflection ? '#070F24' : '#081022';
  const sway = Math.sin(t * 0.9) * 5 * scale;
  for (const palm of [{{ x: -235, h: 112 }}, {{ x: -278, h: 86 }}, {{ x: 242, h: 108 }}, {{ x: 286, h: 82 }}]) {{
    const px = palm.x * scale, ph = palm.h * scale;
    ctx.beginPath();
    ctx.moveTo(px - 4 * scale, 4);
    ctx.quadraticCurveTo(px + sway * 0.5, -ph * 0.5, px + sway, -ph);
    ctx.lineTo(px + sway + 4 * scale, -ph);
    ctx.quadraticCurveTo(px + sway * 0.5 + 5 * scale, -ph * 0.5, px + 5 * scale, 4);
    ctx.closePath();
    ctx.fill();
    // Fronds
    for (let a = 0; a < 6; a++) {{
      const ang = -Math.PI + (a / 5) * Math.PI * 1.15;
      ctx.beginPath();
      ctx.moveTo(px + sway, -ph);
      ctx.quadraticCurveTo(
        px + sway + Math.cos(ang) * 28 * scale,
        -ph + Math.sin(ang) * 20 * scale - 10 * scale,
        px + sway + Math.cos(ang) * 50 * scale,
        -ph + Math.sin(ang) * 26 * scale + 8 * scale
      );
      ctx.lineWidth = 3.2 * scale;
      ctx.strokeStyle = isReflection ? '#070F24' : '#081022';
      ctx.stroke();
    }}
  }}
  ctx.restore();
}}

function drawNatureTransformScene(progress, t) {{
  // Ref #1 Minute Wisdom symbolic transformation: dark embers/storm (0..0.33) -> cool rain (0.33..0.66) -> blooming meadow (0.66..1.0)
  const horizonY = H * (IS_SHORT ? 0.74 : 0.72);
  let topC, midC, botC;
  if (progress < 0.35) {{
    const u = progress / 0.35;
    topC = lerpRGB([28, 12, 18], [26, 36, 64], u);
    midC = lerpRGB([74, 24, 20], [54, 72, 108], u);
    botC = lerpRGB([164, 58, 24], [96, 126, 158], u);
  }} else if (progress < 0.68) {{
    const u = (progress - 0.35) / 0.33;
    topC = lerpRGB([26, 36, 64], [30, 96, 156], u);
    midC = lerpRGB([54, 72, 108], [86, 164, 214], u);
    botC = lerpRGB([96, 126, 158], [176, 224, 232], u);
  }} else {{
    const u = (progress - 0.68) / 0.32;
    topC = lerpRGB([30, 96, 156], [22, 82, 134], u);
    midC = lerpRGB([86, 164, 214], [98, 178, 172], u);
    botC = lerpRGB([176, 224, 232], [238, 220, 162], u);
  }}

  const skyG = ctx.createLinearGradient(0, 0, 0, horizonY);
  skyG.addColorStop(0, rgb(topC));
  skyG.addColorStop(0.55, rgb(midC));
  skyG.addColorStop(1, rgb(botC));
  ctx.fillStyle = skyG;
  ctx.fillRect(0, 0, W, H);

  // Subtle dark top scrim so calligraphy & typography stay crisp in bright stages
  const topScrim = ctx.createLinearGradient(0, 0, 0, H * 0.56);
  topScrim.addColorStop(0, 'rgba(6,12,26,0.52)');
  topScrim.addColorStop(1, 'rgba(6,12,26,0.0)');
  ctx.fillStyle = topScrim;
  ctx.fillRect(0, 0, W, H * 0.56);

  // Rising warm glow in meadow phase
  if (progress > 0.52) {{
    const alpha = Math.min((progress - 0.52) / 0.35, 1);
    const sunG = ctx.createRadialGradient(W * 0.5, horizonY - 40, 10, W * 0.5, horizonY - 40, W * 0.45);
    sunG.addColorStop(0, `rgba(255, 240, 180, ${{0.65 * alpha}})`);
    sunG.addColorStop(1, 'rgba(255, 220, 130, 0)');
    ctx.fillStyle = sunG;
    ctx.fillRect(0, 0, W, horizonY + 80);
  }}

  // Phase 1: Soft rising glowing embers/sparks fading out
  if (progress < 0.42) {{
    const fireA = 1 - Math.max(0, (progress - 0.20) / 0.22);
    for (let i = 0; i < 36; i++) {{
      const px = ((i * 79 + t * (18 + (i % 4) * 8)) % W);
      const py = horizonY + 30 - ((t * (48 + (i % 5) * 14) + i * 47) % (H * 0.34));
      const r = 2 + (i % 4) * 1.5;
      ctx.fillStyle = `rgba(255, ${{130 + (i % 5) * 20}}, 48, ${{0.68 * fireA}})`;
      ctx.beginPath();
      ctx.arc(px, py, r, 0, Math.PI * 2);
      ctx.fill();
    }}
  }}

  // Phase 2: Gentle cleansing raindrops & water ripples
  if (progress > 0.24 && progress < 0.78) {{
    const rainA = Math.sin(((progress - 0.24) / 0.54) * Math.PI);
    ctx.strokeStyle = `rgba(210, 238, 255, ${{0.55 * rainA}})`;
    ctx.lineWidth = 1.6;
    for (const d of DROPS) {{
      const rx = d.x * W;
      const ry = ((t * d.speed + d.offset) % 1.0) * (horizonY + 40);
      ctx.beginPath();
      ctx.moveTo(rx, ry);
      ctx.lineTo(rx - 2, ry + d.len);
      ctx.stroke();
    }}
    // Ripples at horizon pool
    for (let r_i = 0; r_i < 4; r_i++) {{
      const cyc = (t * 0.55 + r_i * 0.25) % 1.0;
      ctx.strokeStyle = `rgba(220, 245, 255, ${{(1 - cyc) * 0.45 * rainA}})`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.ellipse(W * (0.25 + r_i * 0.17), horizonY + 44 + (r_i % 2) * 22, 14 + cyc * 62, 5 + cyc * 14, 0, 0, Math.PI * 2);
      ctx.stroke();
    }}
  }}

  // Ground transformation: dark cracked earth -> emerald lush hills
  const g1 = lerpRGB([32, 16, 14], [24, 72, 52], Math.min(Math.max((progress - 0.3) / 0.55, 0), 1));
  const g2 = lerpRGB([18, 9, 10], [12, 42, 34], Math.min(Math.max((progress - 0.3) / 0.55, 0), 1));
  const gGrad = ctx.createLinearGradient(0, horizonY - 24, 0, H);
  gGrad.addColorStop(0, rgb(g1));
  gGrad.addColorStop(1, rgb(g2));
  ctx.fillStyle = gGrad;
  ctx.beginPath();
  ctx.moveTo(0, horizonY + 18);
  ctx.quadraticCurveTo(W * 0.25, horizonY - 34, W * 0.55, horizonY - 6);
  ctx.quadraticCurveTo(W * 0.80, horizonY + 18, W, horizonY - 24);
  ctx.lineTo(W, H);
  ctx.lineTo(0, H);
  ctx.closePath();
  ctx.fill();

  // Phase 3: Blooming meadow stalks & golden blossoms swaying gently
  if (progress > 0.50) {{
    const bloom = Math.min((progress - 0.50) / 0.38, 1);
    for (let i = 0; i < 48; i++) {{
      const bx = (i / 47) * W;
      const baseH = (26 + (i * 29) % 58) * bloom;
      const sway = Math.sin(t * 1.4 + i * 0.6) * 8 * bloom;
      const by = horizonY + 14 + ((i * 37) % 120);
      ctx.strokeStyle = `rgba(74, 184, 118, ${{0.65 * bloom}})`;
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.moveTo(bx, by);
      ctx.quadraticCurveTo(bx + sway * 0.5, by - baseH * 0.5, bx + sway, by - baseH);
      ctx.stroke();
      if (i % 3 === 0) {{
        ctx.fillStyle = i % 6 === 0 ? `rgba(253, 224, 130, ${{0.9 * bloom}})` : `rgba(255, 255, 255, ${{0.85 * bloom}})`;
        ctx.beginPath();
        ctx.arc(bx + sway, by - baseH, 3.6 * bloom, 0, Math.PI * 2);
        ctx.fill();
      }}
    }}
  }}
}}

function drawPrayerSkyScene(progress, t) {{
  const horizonY = H * (IS_SHORT ? 0.74 : 0.72);
  const fIdx = progress * (SKY_STAGES.length - 1);
  const i0 = Math.min(Math.floor(fIdx), SKY_STAGES.length - 2);
  const frac = fIdx - i0;
  const s0 = SKY_STAGES[i0], s1 = SKY_STAGES[i0 + 1];

  const topC = lerpRGB(s0.top, s1.top, frac);
  const midC = lerpRGB(s0.mid, s1.mid, frac);
  const botC = lerpRGB(s0.bot, s1.bot, frac);
  const sunC = lerpRGB(s0.sunCol, s1.sunCol, frac);
  const starA = lerp(s0.starA, s1.starA, frac);
  const sunY = lerp(s0.sunY, s1.sunY, frac) * horizonY;

  // Sky gradient
  const skyG = ctx.createLinearGradient(0, 0, 0, horizonY);
  skyG.addColorStop(0, rgb(topC));
  skyG.addColorStop(0.56, rgb(midC));
  skyG.addColorStop(1, rgb(botC));
  ctx.fillStyle = skyG;
  ctx.fillRect(0, 0, W, horizonY + 2);

  // Subtle top vignette for crisp typography legibility on bright Dhuhr/Asr skies
  const topScrim = ctx.createLinearGradient(0, 0, 0, H * 0.52);
  topScrim.addColorStop(0, 'rgba(6, 13, 30, 0.42)');
  topScrim.addColorStop(1, 'rgba(6, 13, 30, 0.0)');
  ctx.fillStyle = topScrim;
  ctx.fillRect(0, 0, W, H * 0.52);

  // Twinkling stars
  if (starA > 0.02) {{
    for (const st of STARS) {{
      const tw = 0.55 + 0.45 * Math.sin(t * 2.1 + st.ph);
      ctx.fillStyle = `rgba(255, 250, 232, ${{starA * tw * 0.85}})`;
      ctx.beginPath();
      ctx.arc(st.x * W, st.y * horizonY, st.r, 0, Math.PI * 2);
      ctx.fill();
    }}
  }}

  // Radiant Sun or Crescent Moon halo
  const sunX = W * (0.22 + progress * 0.56);
  const halo = ctx.createRadialGradient(sunX, sunY, 8, sunX, sunY, 170);
  halo.addColorStop(0, rgb(sunC, 0.72));
  halo.addColorStop(0.35, rgb(sunC, 0.24));
  halo.addColorStop(1, rgb(sunC, 0.0));
  ctx.fillStyle = halo;
  ctx.fillRect(sunX - 180, sunY - 180, 360, 360);

  if (starA > 0.52) {{
    // Luminous crescent moon
    ctx.save();
    ctx.fillStyle = rgb(sunC, 0.95);
    ctx.beginPath();
    ctx.arc(sunX, sunY, 22, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = rgb(midC, 1);
    ctx.beginPath();
    ctx.arc(sunX + 9, sunY - 5, 19, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }} else {{
    ctx.fillStyle = rgb(sunC, 0.92);
    ctx.beginPath();
    ctx.arc(sunX, sunY, 26, 0, Math.PI * 2);
    ctx.fill();
  }}

  // Calm shimmering water basin below horizon
  const waterG = ctx.createLinearGradient(0, horizonY, 0, H);
  waterG.addColorStop(0, rgb(botC, 0.78));
  waterG.addColorStop(0.28, rgb(midC, 0.88));
  waterG.addColorStop(1, rgb([6, 12, 26], 1));
  ctx.fillStyle = waterG;
  ctx.fillRect(0, horizonY, W, H - horizonY);

  // Shimmering light path on water
  for (let i = 0; i < 22; i++) {{
    const wy = horizonY + 8 + i * ((H - horizonY) / 22);
    const spread = 24 + i * 7.5;
    const wob = Math.sin(t * 2.2 + i * 0.9) * 14;
    ctx.fillStyle = rgb(sunC, Math.max(0.05, 0.34 - i * 0.013));
    ctx.fillRect(sunX - spread * 0.5 + wob, wy, spread, 2.2);
  }}

  const scale = IS_SHORT ? 1.02 : 1.15;
  drawMosqueSilhouette(horizonY, scale, t, true);
  drawMosqueSilhouette(horizonY, scale, t, false);
}}

window.renderAt = function(t) {{
  const total = Math.max(CFG.total_dur, 1);
  const progress = Math.min(Math.max(t / total, 0), 1);

  if (CFG.dalil.visual_theme === 'nature_transform') {{
    drawNatureTransformScene(progress, t);
  }} else {{
    drawPrayerSkyScene(progress, t);
  }}

  // Active scene lookup
  let cur = CFG.scenes[CFG.scenes.length - 1];
  for (const s of CFG.scenes) {{
    if (t >= s.start && t <= s.end) {{ cur = s; break; }}
  }}
  const idx = cur ? cur.idx : 0;
  document.getElementById('eyebrow').textContent = `${{CFG.dalil.pillar_label}}  •  ${{idx + 1}} OF ${{numScenes}}`;
  document.getElementById('headline').textContent = cur ? cur.headline : CFG.dalil.topic;
  document.getElementById('stepLabel').textContent = (cur && cur.badge) ? cur.badge.replace(/^\\d+\\s*[•\\-]?\\s*/, '').slice(0, 18) : `STEP ${{idx + 1}}`;

  const dots = dotsWrap.children;
  for (let i = 0; i < dots.length; i++) {{
    dots[i].className = 'dot' + (i < idx ? ' done' : (i === idx ? ' active' : ''));
  }}

  // Active synchronized caption with warm gold highlight on current spoken word
  let cap = null;
  for (const c of CFG.captions) {{
    if (t >= c.start - 0.06 && t <= c.end + 0.14) {{ cap = c; break; }}
  }}
  const subCard = document.getElementById('subCard');
  const subText = document.getElementById('subText');
  if (cap && cap.words && cap.words.length) {{
    subCard.style.opacity = '1';
    subText.innerHTML = cap.words.map(w => {{
      const isSpoken = t >= w.s && t <= w.e + 0.12;
      return isSpoken ? `<span class="hi">${{w.w}}</span>` : w.w;
    }}).join(' ');
  }} else {{
    subCard.style.opacity = '0';
  }}
}};
</script>
</body>
</html>"""


def _build_gold_visualizer_html(payload: dict[str, Any], width: int, height: int) -> str:
    """Mode 2: `islamic_gold_visualizer` (Ref #4 Surah Ar-Ra'd Obsidian Black + Gold Radial Sunburst + Word Karaoke)."""
    font_css = _load_amiri_font_css()
    cfg_json = json.dumps(payload, ensure_ascii=False)
    is_short = height >= width
    ar_size = 54 if is_short else 48
    en_size = 30 if is_short else 28

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  {font_css}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: {width}px; height: {height}px; overflow: hidden;
    background: #050507;
    font-family: 'Segoe UI', 'Georgia', serif;
    color: #F8FAFC;
  }}
  #bgCanvas {{ position: absolute; inset: 0; width: {width}px; height: {height}px; display: block; }}

  .top-header {{
    position: absolute; top: {82 if is_short else 18}px; left: 0; right: 0;
    z-index: 6; text-align: center;
  }}
  .surah-ar {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; font-size: {38 if is_short else 34}px; font-weight: 700;
    color: #E8C56B; letter-spacing: 0.5px;
    text-shadow: 0 0 18px rgba(232, 197, 107, 0.35);
    margin-bottom: 4px;
  }}
  .surah-en {{
    font-family: 'Georgia', 'Times New Roman', serif;
    font-size: {16 if is_short else 15}px; font-weight: 600;
    letter-spacing: 3.6px; text-transform: uppercase;
    color: rgba(232, 197, 107, 0.85);
  }}
  .topic-sub {{
    margin-top: 8px; font-family: 'Segoe UI', sans-serif;
    font-size: {16 if is_short else 15}px; font-weight: 500;
    color: rgba(226, 232, 240, 0.72);
    padding: 0 36px;
  }}

  /* Lower-half synchronized gold karaoke block (matches Ref #4 exact layout!) */
  .karaoke-wrap {{
    position: absolute; left: 36px; right: 36px;
    top: {62 if is_short else 66}%;
    z-index: 7; text-align: center;
    display: flex; flex-direction: column; align-items: center;
  }}
  .ar-karaoke {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; unicode-bidi: embed;
    font-size: {ar_size}px; font-weight: 700; line-height: 1.56;
    max-width: {650 if is_short else 1040}px;
    margin-bottom: {14 if is_short else 8}px;
  }}
  .ar-w {{ color: rgba(255, 250, 238, 0.34); transition: color 0.12s; }}
  .ar-w.lit {{
    color: #F4C95D;
    text-shadow: 0 0 22px rgba(244, 201, 93, 0.55);
  }}
  .ar-w.past {{ color: rgba(255, 248, 232, 0.88); }}

  .tr-line {{
    font-family: 'Georgia', serif; font-style: italic;
    font-size: {18 if is_short else 17}px; color: rgba(203, 213, 225, 0.65);
    margin-bottom: {18 if is_short else 10}px;
    max-width: {640 if is_short else 980}px;
  }}

  .en-karaoke {{
    font-family: 'Georgia', 'Times New Roman', serif;
    font-size: {en_size}px; font-weight: 500; line-height: 1.38;
    max-width: {640 if is_short else 980}px;
    min-height: {84 if is_short else 54}px;
  }}
  .en-w {{ color: rgba(248, 250, 252, 0.38); }}
  .en-w.lit {{
    color: #F4C95D; font-weight: 700;
    text-shadow: 0 0 18px rgba(244, 201, 93, 0.45);
  }}
  .en-w.past {{ color: rgba(248, 250, 252, 0.94); }}

  .insight-pill {{
    position: absolute; bottom: {82 if is_short else 42}px; left: 50%; transform: translateX(-50%);
    z-index: 8; max-width: {620 if is_short else 860}px;
    padding: 8px 22px; border-radius: 999px;
    background: rgba(232, 197, 107, 0.11);
    border: 1px solid rgba(232, 197, 107, 0.34);
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px; font-weight: 600; letter-spacing: 1.2px;
    color: #F3D999; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }}

  .brand-foot {{
    position: absolute; bottom: {32 if is_short else 14}px; left: 0; right: 0;
    z-index: 8; text-align: center;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px; font-weight: 600; letter-spacing: 2.8px; text-transform: uppercase;
    color: rgba(232, 197, 107, 0.56);
  }}
</style>
</head>
<body>
<canvas id="bgCanvas" width="{width}" height="{height}"></canvas>

<div class="top-header">
  <div class="surah-ar" id="surahAr"></div>
  <div class="surah-en" id="surahEn"></div>
  <div class="topic-sub" id="topicSub"></div>
</div>

<div class="karaoke-wrap">
  <div class="ar-karaoke" id="arKaraoke"></div>
  <div class="tr-line" id="trLine"></div>
  <div class="en-karaoke" id="enKaraoke"></div>
</div>

<div class="insight-pill" id="insightPill"></div>
<div class="brand-foot" id="brandFoot"></div>

<script>
const CFG = {cfg_json};
const W = {width}, H = {height};
const IS_SHORT = H >= W;
const ctx = document.getElementById('bgCanvas').getContext('2d');

document.getElementById('surahAr').textContent = CFG.dalil.surah_ar;
document.getElementById('surahEn').textContent = CFG.dalil.citation;
document.getElementById('topicSub').textContent = CFG.dalil.topic;
document.getElementById('trLine').textContent = CFG.dalil.transliteration;
document.getElementById('brandFoot').textContent = CFG.dalil.handle + '  ·  QUR\\'AN & CALM MIND SCIENCE';

const AR_WORDS = CFG.dalil.arabic.split(/\\s+/).filter(Boolean);
const arWrap = document.getElementById('arKaraoke');
arWrap.innerHTML = AR_WORDS.map((w, i) => `<span class="ar-w" id="arw_${{i}}">${{w}}</span>`).join(' ');

// Floating golden dust motes
const DUST = [];
for (let i = 0; i < 65; i++) {{
  DUST.push({{
    x: ((i * 173.9) % 1000) / 1000,
    y: ((i * 289.1) % 1000) / 1000,
    r: 0.9 + (i % 4) * 0.55,
    sp: 0.012 + (i % 5) * 0.005,
    ph: i * 0.9,
  }});
}}

function drawIslamicStarPattern(cx, cy, t) {{
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(t * 0.035);
  ctx.strokeStyle = 'rgba(218, 178, 86, 0.075)';
  ctx.lineWidth = 1.2;
  const maxR = IS_SHORT ? 275 : 220;
  for (const r of [maxR * 0.58, maxR * 0.82, maxR]) {{
    // Two overlaid rotated squares = classic Rub el Hizb 8-point star
    for (const rot of [0, Math.PI / 4]) {{
      ctx.save();
      ctx.rotate(rot);
      ctx.strokeRect(-r * 0.72, -r * 0.72, r * 1.44, r * 1.44);
      ctx.restore();
    }}
    ctx.beginPath();
    ctx.arc(0, 0, r, 0, Math.PI * 2);
    ctx.stroke();
  }}
  ctx.restore();
}}

window.renderAt = function(t) {{
  const total = Math.max(CFG.total_dur, 1);
  const progress = Math.min(Math.max(t / total, 0), 1);
  const fIdx = Math.min(Math.floor(t * CFG.fps), Math.max(CFG.rms.length - 1, 0));
  const amp = CFG.rms.length ? CFG.rms[fIdx] : 0.35;

  // Pitch obsidian velvet backdrop with warm golden radial aura
  const cx = W * 0.5;
  const cy = H * (IS_SHORT ? 0.39 : 0.415);
  ctx.fillStyle = '#050507';
  ctx.fillRect(0, 0, W, H);

  const auraR = (IS_SHORT ? 330 : 280) + amp * 36;
  const aura = ctx.createRadialGradient(cx, cy, 18, cx, cy, auraR);
  aura.addColorStop(0, `rgba(212, 168, 68, ${{0.22 + amp * 0.16}})`);
  aura.addColorStop(0.5, 'rgba(142, 102, 32, 0.08)');
  aura.addColorStop(1, 'rgba(5, 5, 7, 0)');
  ctx.fillStyle = aura;
  ctx.fillRect(0, 0, W, H);

  // Subtle rotating geometric Islamic lattice
  drawIslamicStarPattern(cx, cy, t);

  // Drifting golden dust motes
  for (const d of DUST) {{
    const dx = d.x * W + Math.sin(t * 0.6 + d.ph) * 14;
    const dy = ((d.y - t * d.sp) % 1 + 1) % 1 * H;
    const a = 0.18 + 0.34 * (0.5 + 0.5 * Math.sin(t * 1.8 + d.ph));
    ctx.fillStyle = `rgba(244, 206, 112, ${{a}})`;
    ctx.beginPath();
    ctx.arc(dx, dy, d.r, 0, Math.PI * 2);
    ctx.fill();
  }}

  // Audio-reactive Golden Radial Sunburst Visualizer (72 bars)
  const baseR = IS_SHORT ? 116 : 84;
  const bars = 72;
  ctx.save();
  ctx.translate(cx, cy);

  // Soft inner obsidian medallion
  ctx.fillStyle = 'rgba(7, 7, 10, 0.92)';
  ctx.beginPath();
  ctx.arc(0, 0, baseR - 2, 0, Math.PI * 2);
  ctx.fill();

  // Double gold hairline rings
  ctx.strokeStyle = 'rgba(244, 201, 93, 0.72)';
  ctx.lineWidth = 2.0;
  ctx.beginPath();
  ctx.arc(0, 0, baseR - 3, 0, Math.PI * 2);
  ctx.stroke();
  ctx.strokeStyle = 'rgba(244, 201, 93, 0.25)';
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  ctx.arc(0, 0, baseR - 13, 0, Math.PI * 2);
  ctx.stroke();

  // Radial sunburst bars reacting directly to voiceover RMS envelope
  for (let i = 0; i < bars; i++) {{
    const ang = (i / bars) * Math.PI * 2 - Math.PI / 2;
    const wave = 0.52 + 0.48 * Math.sin(i * 0.55 + t * 5.2) * Math.cos(i * 0.25 - t * 3.1);
    const barLen = 10 + (amp * 68 + 10) * (0.35 + 0.65 * Math.abs(wave));
    const x1 = Math.cos(ang) * (baseR + 5);
    const y1 = Math.sin(ang) * (baseR + 5);
    const x2 = Math.cos(ang) * (baseR + 5 + barLen);
    const y2 = Math.sin(ang) * (baseR + 5 + barLen);

    const g = ctx.createLinearGradient(x1, y1, x2, y2);
    g.addColorStop(0, 'rgba(255, 224, 134, 0.95)');
    g.addColorStop(0.65, 'rgba(218, 165, 56, 0.75)');
    g.addColorStop(1, 'rgba(180, 125, 28, 0.08)');
    ctx.strokeStyle = g;
    ctx.lineWidth = IS_SHORT ? 3.2 : 2.8;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }}

  // Centerpiece Ayah / Hadith Number inside medallion (Ref #4 signature!)
  const numText = CFG.dalil.badge_num;
  const numSize = numText.length <= 3 ? (IS_SHORT ? 62 : 52) : (numText.length <= 5 ? (IS_SHORT ? 46 : 40) : (IS_SHORT ? 34 : 30));
  ctx.fillStyle = '#F7D77C';
  ctx.font = `700 ${{numSize}}px Georgia, 'Times New Roman', serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(numText, 0, -10);

  ctx.fillStyle = 'rgba(232, 197, 107, 0.75)';
  ctx.font = `600 ${{IS_SHORT ? 15 : 13}}px 'Segoe UI', sans-serif`;
  ctx.fillText(CFG.dalil.badge_label, 0, 32);
  ctx.restore();

  // Progressive RTL gold illumination across Arabic verse words
  const activeArIdx = Math.min(Math.floor(progress * AR_WORDS.length), AR_WORDS.length - 1);
  for (let i = 0; i < AR_WORDS.length; i++) {{
    const el = document.getElementById(`arw_${{i}}`);
    if (!el) continue;
    el.className = 'ar-w' + (i === activeArIdx ? ' lit' : (i < activeArIdx ? ' past' : ''));
  }}

  // Synchronized English spoken karaoke
  let cap = null;
  for (const c of CFG.captions) {{
    if (t >= c.start - 0.06 && t <= c.end + 0.14) {{ cap = c; break; }}
  }}
  const enEl = document.getElementById('enKaraoke');
  if (cap && cap.words && cap.words.length) {{
    enEl.innerHTML = cap.words.map(w => {{
      if (t >= w.s && t <= w.e + 0.10) return `<span class="en-w lit">${{w.w}}</span>`;
      if (t > w.e + 0.10) return `<span class="en-w past">${{w.w}}</span>`;
      return `<span class="en-w">${{w.w}}</span>`;
    }}).join(' ');
  }} else {{
    enEl.innerHTML = `<span class="en-w past">"${{CFG.dalil.translation}}"</span>`;
  }}

  // Scene-synced Brain & Peace Insight pill
  let cur = CFG.scenes[CFG.scenes.length - 1];
  for (const s of CFG.scenes) {{
    if (t >= s.start && t <= s.end) {{ cur = s; break; }}
  }}
  document.getElementById('insightPill').textContent = (cur && cur.headline) ? `✦  ${{cur.headline}}` : CFG.dalil.pillar_label;
}};
</script>
</body>
</html>"""


def _build_particle_map_html(payload: dict[str, Any], width: int, height: int) -> str:
    """Mode 3: `islamic_particle_map` (Ref #5 Al-Kahfi Particle Constellations + Ref #6 Metaphor Subtitles)."""
    font_css = _load_amiri_font_css()
    cfg_json = json.dumps(payload, ensure_ascii=False)
    is_short = height >= width

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  {font_css}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: {width}px; height: {height}px; overflow: hidden;
    background: #060916;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    color: #F8FAFC;
  }}
  #bgCanvas {{ position: absolute; inset: 0; width: {width}px; height: {height}px; display: block; }}

  /* Top subtle progress track + crescent emblem (Ref #5 signature) */
  .top-bar {{
    position: absolute; top: {52 if is_short else 22}px; left: 48px; right: 48px;
    z-index: 6; display: flex; flex-direction: column; align-items: center; gap: 12px;
  }}
  .prog-track {{
    width: 100%; max-width: {560 if is_short else 820}px; height: 4px;
    border-radius: 99px; background: rgba(255,255,255,0.14); overflow: hidden;
  }}
  #progFill {{
    height: 100%; width: 0%;
    background: linear-gradient(90deg, #38BDF8, #F4C95D);
    border-radius: 99px;
  }}
  .pillar-chip {{
    font-size: 13px; font-weight: 700; letter-spacing: 2.8px; text-transform: uppercase;
    color: rgba(244, 201, 93, 0.90);
  }}

  /* Bold Editorial Scene Header + Verified Dalil Strip */
  .hero-block {{
    position: absolute; top: {106 if is_short else 60}px; left: 36px; right: 36px;
    z-index: 7; text-align: center;
    display: flex; flex-direction: column; align-items: center;
  }}
  .scene-title {{
    font-size: {38 if is_short else 34}px; font-weight: 900; line-height: 1.16;
    letter-spacing: 0.4px; color: #FFFFFF;
    text-transform: uppercase;
    text-shadow: 0 4px 20px rgba(0,0,0,0.65);
    max-width: {640 if is_short else 980}px;
    margin-bottom: 12px;
  }}
  .ar-quote {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; unicode-bidi: embed;
    font-size: {34 if is_short else 30}px; font-weight: 700; line-height: 1.5;
    color: #F4C95D;
    text-shadow: 0 2px 14px rgba(244, 201, 93, 0.35);
    max-width: {640 if is_short else 960}px;
    margin-bottom: 8px;
  }}
  .cit-badge {{
    display: inline-block; padding: 4px 14px; border-radius: 999px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(244, 201, 93, 0.40);
    font-size: 13px; font-weight: 700; letter-spacing: 2px; color: #FDE68A;
  }}

  /* Clean centered white-outlined conversational subtitles (Ref #6 signature!) */
  .sub-area {{
    position: absolute; left: 32px; right: 32px;
    bottom: {136 if is_short else 62}px;
    z-index: 9; text-align: center;
  }}
  #subText {{
    display: inline-block; max-width: {640 if is_short else 980}px;
    font-size: {36 if is_short else 33}px; font-weight: 800; line-height: 1.24;
    color: #FFFFFF;
    -webkit-text-stroke: 1.8px rgba(5, 8, 18, 0.92);
    paint-order: stroke fill;
    text-shadow: 0 4px 16px rgba(0,0,0,0.85);
  }}
  #subText .gold {{ color: #FDE68A; }}

  /* Bottom scene milestone pills (Ref #5 bucket indicators) */
  .buckets {{
    position: absolute; bottom: {66 if is_short else 24}px; left: 36px; right: 36px;
    z-index: 8; display: flex; justify-content: center; gap: 8px; flex-wrap: nowrap;
  }}
  .bkt {{
    padding: 5px 12px; border-radius: 999px;
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.16);
    font-size: 12px; font-weight: 700; letter-spacing: 1px; color: rgba(226,232,240,0.62);
    text-transform: uppercase;
  }}
  .bkt.on {{
    background: rgba(244, 201, 93, 0.20);
    border-color: rgba(244, 201, 93, 0.72);
    color: #FEF3C7;
    box-shadow: 0 0 14px rgba(244, 201, 93, 0.30);
  }}

  .brand-foot {{
    position: absolute; bottom: {26 if is_short else 6}px; left: 0; right: 0;
    z-index: 8; text-align: center;
    font-size: 13px; font-weight: 600; letter-spacing: 2.2px;
    color: rgba(255,255,255,0.48);
  }}
</style>
</head>
<body>
<canvas id="bgCanvas" width="{width}" height="{height}"></canvas>

<div class="top-bar">
  <div class="prog-track"><div id="progFill"></div></div>
  <div class="pillar-chip" id="pillarChip"></div>
</div>

<div class="hero-block">
  <div class="scene-title" id="sceneTitle"></div>
  <div class="ar-quote" id="arQuote"></div>
  <div class="cit-badge" id="citBadge"></div>
</div>

<div class="sub-area"><div id="subText"></div></div>
<div class="buckets" id="bucketsWrap"></div>
<div class="brand-foot" id="brandFoot"></div>

<script>
const CFG = {cfg_json};
const W = {width}, H = {height};
const IS_SHORT = H >= W;
const ctx = document.getElementById('bgCanvas').getContext('2d');

document.getElementById('pillarChip').textContent = '☾  ' + CFG.dalil.pillar_label;
document.getElementById('arQuote').textContent = CFG.dalil.arabic;
document.getElementById('citBadge').textContent = CFG.dalil.citation;
document.getElementById('brandFoot').textContent = CFG.dalil.handle + '  •  SUNNAH & MODERN BRAIN SCIENCE';

// Build 4 milestone buckets
const bucketsWrap = document.getElementById('bucketsWrap');
const BKT_LABELS = ['REFLECT', 'SUNNAH', 'SCIENCE', 'HABIT'];
BKT_LABELS.forEach((lbl, i) => {{
  const el = document.createElement('div');
  el.className = 'bkt';
  el.id = 'bkt_' + i;
  el.textContent = lbl;
  bucketsWrap.appendChild(el);
}});

// Mood-shifting cosmic backdrop palettes per stage (Ref #5 exact shift: Indigo -> Emerald -> Teal -> Amber)
const MOODS = [
  {{ c0: [12, 18, 48], c1: [6, 9, 24],  accent: [125, 211, 252] }},
  {{ c0: [10, 44, 42], c1: [5, 18, 22], accent: [52, 211, 153] }},
  {{ c0: [24, 28, 62], c1: [8, 10, 26], accent: [244, 201, 93] }},
  {{ c0: [52, 32, 16], c1: [14, 10, 14], accent: [251, 191, 36] }},
];

function lerp(a, b, t) {{ return a + (b - a) * t; }}
function lerpRGB(a, b, t) {{ return [Math.round(lerp(a[0], b[0], t)), Math.round(lerp(a[1], b[1], t)), Math.round(lerp(a[2], b[2], t))]; }}

// Generate target coordinates for 380 luminous particles in 7 iconic storytelling shapes!
const N_PART = 380;
const CX = W * 0.5;
const CY = H * (IS_SHORT ? 0.56 : 0.57);
const RAD = IS_SHORT ? 185 : 155;

function sampleShape(name) {{
  const pts = [];
  for (let i = 0; i < N_PART; i++) {{
    const u = i / N_PART;
    const ang = u * Math.PI * 2;
    let x = 0, y = 0, sz = 2.0;

    if (name === 'crescent_stars') {{
      if (i < 260) {{
        const a = -0.78 * Math.PI + (i / 260) * 1.56 * Math.PI;
        const r = RAD * (0.76 + (i % 5) * 0.04);
        x = Math.cos(a) * r - 18;
        y = Math.sin(a) * r;
        sz = 2.6;
      }} else {{
        // Sparkling constellation stars around crescent
        const k = i - 260;
        const sa = k * 2.39996;
        const sr = RAD * (0.35 + ((k * 37) % 100) / 115);
        x = Math.cos(sa) * sr + 28;
        y = Math.sin(sa) * sr;
        sz = (k % 4 === 0) ? 3.2 : 1.7;
      }}
    }} else if (name === 'ocean_drop') {{
      if (i < 160) {{
        // Glowing teardrop descending center
        const t = (i / 160) * Math.PI * 2;
        const dropR = RAD * 0.30;
        x = Math.sin(t) * dropR * (0.65 + 0.35 * Math.cos(t));
        y = -RAD * 0.36 - Math.cos(t) * dropR * 1.15;
        sz = 2.5;
      }} else {{
        // Vast shimmering ocean waves & ripples
        const k = i - 160;
        const ring = k % 4;
        const a = (k / 220) * Math.PI * 2;
        const rx = RAD * (0.48 + ring * 0.24);
        const ry = RAD * (0.14 + ring * 0.075);
        x = Math.cos(a) * rx;
        y = RAD * 0.38 + Math.sin(a) * ry;
        sz = 2.1;
      }}
    }} else if (name === 'cave_arch') {{
      if (i < 230) {{
        // Majestic luminous stone cave arch (Ashabul Kahfi Ref #5!)
        const a = Math.PI + (i / 230) * Math.PI;
        const layer = (i % 4) * 16;
        x = Math.cos(a) * (RAD * 0.92 - layer);
        y = RAD * 0.42 + Math.sin(a) * (RAD * 1.08 - layer);
        sz = 2.6;
      }} else {{
        // Radiant inner light beam emerging from cave center
        const k = i - 230;
        const r = (k / 150) * RAD * 0.56;
        const a = k * 2.39996;
        x = Math.cos(a) * r;
        y = RAD * 0.14 + Math.sin(a) * r * 0.85;
        sz = 2.2;
      }}
    }} else if (name === 'balance_scale') {{
      // Three luminous harmonic rings (1/3 Food, 1/3 Water, 1/3 Breath / Sunnah Balance)
      const grp = i % 3;
      const centerAng = -Math.PI / 2 + grp * (Math.PI * 2 / 3);
      const gx = Math.cos(centerAng) * (RAD * 0.46);
      const gy = Math.sin(centerAng) * (RAD * 0.44);
      const a = (Math.floor(i / 3) / (N_PART / 3)) * Math.PI * 2;
      const rr = RAD * 0.38;
      x = gx + Math.cos(a) * rr;
      y = gy + Math.sin(a) * rr;
      sz = 2.4;
    }} else if (name === 'brain_light') {{
      // Calm bilateral mind/neural calm wave (two luminous hemispheres + peaceful wave)
      if (i < 280) {{
        const side = (i % 2 === 0) ? -1 : 1;
        const a = ((Math.floor(i / 2)) / 140) * Math.PI * 2;
        const rx = RAD * 0.46;
        const ry = RAD * 0.64;
        const fold = 1 + 0.10 * Math.sin(a * 5);
        x = side * (RAD * 0.32) + Math.cos(a) * rx * fold;
        y = Math.sin(a) * ry * fold;
        sz = 2.4;
      }} else {{
        const k = i - 280;
        const px = -RAD * 0.95 + (k / 100) * RAD * 1.9;
        x = px;
        y = Math.sin((k / 100) * Math.PI * 4) * (RAD * 0.22);
        sz = 2.8;
      }}
    }} else if (name === 'sunrise_horizon') {{
      if (i < 190) {{
        // Rising dawn sun arc + rays
        const a = Math.PI + (i / 190) * Math.PI;
        const r = RAD * (0.48 + (i % 5) * 0.11);
        x = Math.cos(a) * r;
        y = RAD * 0.25 + Math.sin(a) * r;
        sz = 2.5;
      }} else {{
        // Layered rolling horizon waves
        const k = i - 190;
        const row = k % 3;
        const px = -RAD * 1.1 + ((Math.floor(k / 3)) / 64) * RAD * 2.2;
        x = px;
        y = RAD * (0.28 + row * 0.16) + Math.sin(px * 0.025 + row) * 14;
        sz = 2.1;
      }}
    }} else {{
      // summary_constellation: Glowing circular 4-node wisdom map (Ref #5 finale!)
      if (i < 220) {{
        const a = (i / 220) * Math.PI * 2;
        x = Math.cos(a) * (RAD * 0.84);
        y = Math.sin(a) * (RAD * 0.84);
        sz = 2.2;
      }} else {{
        const node = i % 4;
        const na = -Math.PI / 2 + node * (Math.PI / 2);
        const nx = Math.cos(na) * (RAD * 0.84);
        const ny = Math.sin(na) * (RAD * 0.84);
        const a = ((i - 220) / 160) * Math.PI * 8;
        const nr = RAD * 0.18;
        x = nx + Math.cos(a) * nr;
        y = ny + Math.sin(a) * nr;
        sz = 2.9;
      }}
    }}
    pts.push({{ x: CX + x, y: CY + y, sz, ph: i * 0.43 }});
  }}
  return pts;
}}

const SHAPE_NAMES = CFG.dalil.particle_shapes || ['crescent_stars', 'ocean_drop', 'brain_light', 'summary_constellation'];
const SHAPES = SHAPE_NAMES.map(sampleShape);

function smoothstep(x) {{
  const c = Math.min(Math.max(x, 0), 1);
  return c * c * (3 - 2 * c);
}}

window.renderAt = function(t) {{
  const total = Math.max(CFG.total_dur, 1);
  const progress = Math.min(Math.max(t / total, 0), 1);
  document.getElementById('progFill').style.width = (progress * 100).toFixed(2) + '%';

  // Interpolate cosmic mood gradient
  const mf = progress * (MOODS.length - 1);
  const m0 = Math.min(Math.floor(mf), MOODS.length - 2);
  const mFrac = mf - m0;
  const c0 = lerpRGB(MOODS[m0].c0, MOODS[m0 + 1].c0, mFrac);
  const c1 = lerpRGB(MOODS[m0].c1, MOODS[m0 + 1].c1, mFrac);
  const acc = lerpRGB(MOODS[m0].accent, MOODS[m0 + 1].accent, mFrac);

  const bg = ctx.createRadialGradient(CX, CY, 20, CX, CY, Math.max(W, H) * 0.72);
  bg.addColorStop(0, `rgb(${{c0[0]}},${{c0[1]}},${{c0[2]}})`);
  bg.addColorStop(1, `rgb(${{c1[0]}},${{c1[1]}},${{c1[2]}})`);
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, W, H);

  // Determine particle morph interpolation across the shapes sequence
  const sf = progress * (SHAPES.length - 1);
  const s0 = Math.min(Math.floor(sf), Math.max(SHAPES.length - 2, 0));
  const s1 = Math.min(s0 + 1, SHAPES.length - 1);
  // Hold each shape cleanly, then glide smoothly in the last 32% of each stage
  const rawFrac = sf - s0;
  const morphT = rawFrac < 0.65 ? 0 : smoothstep((rawFrac - 0.65) / 0.35);

  const A = SHAPES[s0], B = SHAPES[s1];
  const fIdx = Math.min(Math.floor(t * CFG.fps), Math.max(CFG.rms.length - 1, 0));
  const amp = CFG.rms.length ? CFG.rms[fIdx] : 0.25;

  // Soft glowing core halo behind particle art
  const halo = ctx.createRadialGradient(CX, CY, 12, CX, CY, RAD * 1.25);
  halo.addColorStop(0, `rgba(${{acc[0]}},${{acc[1]}},${{acc[2]}},${{0.16 + amp * 0.12}})`);
  halo.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = halo;
  ctx.fillRect(0, 0, W, H);

  // Subtle constellation connecting lines on sparse points
  ctx.strokeStyle = `rgba(${{acc[0]}},${{acc[1]}},${{acc[2]}}, 0.12)`;
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let i = 0; i < N_PART - 12; i += 12) {{
    const p1x = lerp(A[i].x, B[i].x, morphT);
    const p1y = lerp(A[i].y, B[i].y, morphT);
    const p2x = lerp(A[i + 12].x, B[i + 12].x, morphT);
    const p2y = lerp(A[i + 12].y, B[i + 12].y, morphT);
    if (Math.hypot(p2x - p1x, p2y - p1y) < 130) {{
      ctx.moveTo(p1x, p1y);
      ctx.lineTo(p2x, p2y);
    }}
  }}
  ctx.stroke();

  // Draw all 380 glowing animated particles
  for (let i = 0; i < N_PART; i++) {{
    const pa = A[i], pb = B[i];
    const driftX = Math.sin(t * 1.3 + pa.ph) * (3.5 + morphT * 9);
    const driftY = Math.cos(t * 1.1 + pa.ph * 1.3) * (3.5 + morphT * 9);
    const px = lerp(pa.x, pb.x, morphT) + driftX;
    const py = lerp(pa.y, pb.y, morphT) + driftY;
    const rad = lerp(pa.sz, pb.sz, morphT) * (0.9 + amp * 0.32);
    const bright = 0.55 + 0.45 * Math.sin(t * 2.6 + pa.ph);

    ctx.fillStyle = (i % 3 === 0)
      ? `rgba(255, 245, 210, ${{bright}})`
      : `rgba(${{acc[0]}},${{acc[1]}},${{acc[2]}},${{bright * 0.92}})`;
    ctx.beginPath();
    ctx.arc(px, py, rad, 0, Math.PI * 2);
    ctx.fill();
  }}

  // Active scene headline
  let cur = CFG.scenes[CFG.scenes.length - 1];
  for (const s of CFG.scenes) {{
    if (t >= s.start && t <= s.end) {{ cur = s; break; }}
  }}
  document.getElementById('sceneTitle').textContent = cur ? cur.headline : CFG.dalil.topic;

  // Highlight active milestone bucket
  const activeBkt = Math.min(Math.floor(progress * 4), 3);
  for (let i = 0; i < 4; i++) {{
    const b = document.getElementById('bkt_' + i);
    if (b) b.className = 'bkt' + (i <= activeBkt ? ' on' : '');
  }}

  // Crisp centered white-outlined subtitles
  let cap = null;
  for (const c of CFG.captions) {{
    if (t >= c.start - 0.06 && t <= c.end + 0.14) {{ cap = c; break; }}
  }}
  const subEl = document.getElementById('subText');
  if (cap && cap.words && cap.words.length) {{
    subEl.innerHTML = cap.words.map(w => {{
      const isHi = t >= w.s && t <= w.e + 0.12;
      return isHi ? `<span class="gold">${{w.w}}</span>` : w.w;
    }}).join(' ');
  }} else {{
    subEl.textContent = '';
  }}
}};
</script>
</body>
</html>"""


def build_islamic_visual_html(mode: str, payload: dict[str, Any], width: int, height: int) -> str:
    m = (mode or "islamic_luminous_sky").lower().strip()
    if m == "islamic_gold_visualizer":
        return _build_gold_visualizer_html(payload, width, height)
    if m == "islamic_particle_map":
        return _build_particle_map_html(payload, width, height)
    return _build_luminous_sky_html(payload, width, height)


def _nature_preset_for_mode(mode: str) -> str:
    m = (mode or "").lower().strip()
    if m == "islamic_gold_visualizer":
        return "gentle_rain"
    if m == "islamic_particle_map":
        return "calm_water"
    return "dawn_breeze"


def render_islamic_visual_video_for_pipeline(
    mode: str,
    scenes_meta: list[dict[str, Any]],
    audio_bundle: TrackAudioBundle,
    out_video_path: Path,
    config: dict[str, Any],
    is_short: bool = False,
    topic_meta: dict[str, Any] | None = None,
) -> Path:
    """Render any of the 3 Studio v10 Islamic Luminous Visuals modes to Meta/YT-compliant MP4."""
    from playwright.sync_api import sync_playwright

    vid_root = config.get("video", {})
    vid_cfg = vid_root.get("shorts" if is_short else "youtube_long", {})
    target_w = int(vid_cfg.get("width", 1080 if is_short else 1920))
    target_h = int(vid_cfg.get("height", 1920 if is_short else 1080))
    pause_sec = float(vid_cfg.get("padding_after_audio_sec", 0.30 if is_short else 0.45))
    max_short_sec = float(vid_cfg.get("max_duration_sec", 59.0))

    # Render HTML5 Canvas at crisp 720p @ 24fps (super fast headless Chromium) -> Lanczos upscale to 1080p!
    gl_w, gl_h = (720, 1280) if target_h >= target_w else (1280, 720)
    fps = 24

    master_audio = Path(audio_bundle.master_audio_path)
    raw_dur = probe_duration_sec(master_audio)
    safe_cap = min(max_short_sec - 0.8, 58.2) if is_short else 9999.0
    tempo = 1.0
    if is_short and raw_dur > safe_cap:
        tempo = min(max(raw_dur / safe_cap, 1.02), 1.28)
        print(f"[v10-islamic] Gently pacing narration ({tempo:.2f}x) to fit safely inside {safe_cap:.1f}s Shorts cap...", flush=True)

    work_dir = out_video_path.parent / f"_v10_{mode}_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    mixed_m4a = work_dir / f"mixed_{mode}.m4a"
    nature_preset = _nature_preset_for_mode(mode)
    mix_nature_voice_soundscape(
        master_voice=master_audio,
        duration_sec=raw_dur / tempo,
        out_audio=mixed_m4a,
        config=config,
        preset=nature_preset,
        tempo=tempo,
    )
    final_dur = probe_duration_sec(mixed_m4a)
    if is_short and final_dur > 58.5:
        final_dur = 58.5

    scene_items, captions, _ = _build_scene_and_caption_timeline(
        scenes_meta=scenes_meta,
        audio_bundle=audio_bundle,
        pause_sec=pause_sec,
        tempo=tempo,
    )
    rms_env = _extract_audio_rms_envelope(mixed_m4a, fps=fps, duration_sec=final_dur)
    dalil_payload = _resolve_dalil_payload(topic_meta=topic_meta, scenes_meta=scenes_meta)

    render_payload: dict[str, Any] = {
        "mode": mode,
        "fps": fps,
        "total_dur": round(final_dur, 3),
        "dalil": dalil_payload,
        "scenes": scene_items,
        "captions": captions,
        "rms": rms_env,
    }
    html_doc = build_islamic_visual_html(mode=mode, payload=render_payload, width=gl_w, height=gl_h)
    total_frames = max(int(round(final_dur * fps)), fps)
    silent_mp4 = work_dir / f"video_{mode}_silent.mp4"

    print(
        f"[video] Rendering Studio v10 '{mode}' ({gl_w}x{gl_h} -> {target_w}x{target_h} @ {fps}fps, "
        f"{final_dur:.1f}s, nature={nature_preset})...",
        flush=True,
    )
    cmd = [
        "ffmpeg", "-y",
        "-f", "image2pipe", "-vcodec", "mjpeg", "-r", str(fps), "-i", "pipe:0",
        "-vf", f"scale={target_w}:{target_h}:flags=lanczos:in_range=full:out_range=tv,format=yuv420p",
        "-c:v", "libx264", "-profile:v", "main", "-level:v", "4.0", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-color_range", "tv", "-an",
        str(silent_mp4),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert proc.stdin is not None

    with sync_playwright() as pw:
        chrome = find_chrome_executable()
        launch_kw: dict[str, Any] = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-gpu-sandbox"],
        }
        if chrome:
            launch_kw["executable_path"] = chrome
        br = pw.chromium.launch(**launch_kw)
        page = br.new_page(viewport={"width": gl_w, "height": gl_h}, device_scale_factor=1)
        page.set_content(html_doc, wait_until="load")
        # Ensure embedded Amiri Arabic calligraphy fonts finish loading before frame 0!
        page.evaluate("() => document.fonts.ready")

        try:
            for f_i in range(total_frames):
                t = f_i / float(fps)
                page.evaluate(f"window.renderAt({t:.4f})")
                jpg_bytes = page.screenshot(type="jpeg", quality=93)
                proc.stdin.write(jpg_bytes)
                if f_i > 0 and f_i % 240 == 0:
                    print(f"[v10-{mode}] Rendered {f_i}/{total_frames} frames ({100 * f_i / total_frames:.0f}%)...", flush=True)
        finally:
            br.close()
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()

    err = proc.stderr.read().decode("utf-8", errors="ignore") if proc.stderr else ""
    ret = proc.wait()
    if ret != 0:
        raise RuntimeError(f"FFmpeg v10 '{mode}' render failed ({ret}): {err[-300:]}")

    out_video_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(silent_mp4), "-i", str(mixed_m4a),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", "-shortest",
            str(out_video_path),
        ],
        capture_output=True, check=True,
    )

    if audio_bundle is not None and hasattr(audio_bundle, "total_duration_sec"):
        try:
            audio_bundle.total_duration_sec = round(final_dur, 2)
        except Exception:
            pass

    for p in work_dir.glob("*"):
        p.unlink(missing_ok=True)
    try:
        work_dir.rmdir()
    except OSError:
        pass

    return out_video_path
