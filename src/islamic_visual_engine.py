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
import os
import struct
import subprocess
from pathlib import Path
from typing import Any

from src.arabic_audio import ArabicRecitationResult, resolve_dalil_arabic_audio
from src.html_motion_overlay import find_chrome_executable
from src.islamic_story_acts import STORY_ACTS_JS, resolve_story_acts
from src.islamic_visual_templates_extra import (
    build_cinematic_metaphor_html,
    build_nature_transform_html,
    build_paper_craft_html,
)
from src.sfx_engine import mix_nature_voice_soundscape
from src.voiceover import TrackAudioBundle, probe_duration_sec

ISLAMIC_VISUAL_MODES: tuple[str, ...] = (
    "islamic_nature_transform",
    "islamic_luminous_sky",
    "islamic_paper_craft",
    "islamic_gold_visualizer",
    "islamic_particle_map",
    "islamic_cinematic_metaphor",
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
    """Mode 2: `islamic_luminous_sky` (Ref #2 Prayer-Time Sky Cycle + Mosque Reflection + True 4-Act Storytelling)."""
    font_css = _load_amiri_font_css()
    cfg_json = json.dumps(payload, ensure_ascii=False)
    is_short = height >= width
    top_pad = 64 if is_short else 18
    ar_size = 52 if is_short else 40
    tr_size = 22 if is_short else 18
    en_size = 20 if is_short else 16
    sub_size = 31 if is_short else 28
    card_max_w = 640 if is_short else 900

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
    position: absolute; top: {top_pad}px; left: 30px; right: 30px; z-index: 6;
    display: flex; flex-direction: column; align-items: center; text-align: center;
    pointer-events: none;
  }}

  .act-pill {{
    display: inline-block; padding: 5px 18px; border-radius: 999px;
    background: rgba(7, 15, 32, 0.72);
    border: 1.5px solid rgba(245, 208, 118, 0.65);
    font-size: 13px; font-weight: 800; letter-spacing: 2.4px;
    text-transform: uppercase; color: #F5D076;
    margin-bottom: {10 if is_short else 6}px;
  }}

  .headline-pill {{
    font-size: {36 if is_short else 30}px; font-weight: 900; color: #FFFFFF;
    text-transform: uppercase; text-align: center; max-width: {card_max_w}px; line-height: 1.16;
    text-shadow: 0 3px 16px rgba(0,0,0,0.65);
  }}
  .mini-cit {{
    margin-top: 5px; font-size: 12px; font-weight: 700; letter-spacing: 2px;
    color: #FDE68A; text-transform: uppercase; text-shadow: 0 2px 8px rgba(0,0,0,0.65);
  }}

  /* ACT 2 ONLY: Center-Stage Sacred Dalil Card */
  .dalil-box {{
    position: absolute; left: 50%; transform: translateX(-50%);
    top: {228 if is_short else 128}px;
    z-index: 7; width: {card_max_w}px;
    background: rgba(7, 15, 32, 0.80);
    border: 2px solid rgba(245, 208, 118, 0.82);
    border-radius: 22px;
    padding: {22 if is_short else 14}px {26 if is_short else 28}px;
    text-align: center;
    box-shadow: 0 0 38px rgba(245, 208, 118, 0.28), 0 16px 36px rgba(0,0,0,0.45);
    display: none;
  }}

  .arabic-text {{
    font-family: 'AmiriCalligraphy', 'Amiri', 'Traditional Arabic', 'Segoe UI', serif;
    direction: rtl; unicode-bidi: embed;
    font-size: {ar_size}px; font-weight: 700; line-height: 1.56;
    color: #FFFDF7;
    text-shadow: 0 3px 16px rgba(245, 208, 118, 0.38), 0 2px 8px rgba(0,0,0,0.55);
    margin-bottom: 10px;
  }}

  .translit {{
    font-size: {tr_size}px; font-weight: 600; color: #FDE68A;
    line-height: 1.35; margin-bottom: 8px;
  }}

  .translation {{
    font-size: {en_size}px; font-style: italic; font-weight: 400;
    color: rgba(241, 245, 249, 0.92); line-height: 1.38; margin-bottom: 12px;
  }}

  .citation-row {{
    display: inline-flex; align-items: center; gap: 10px;
    padding: 5px 16px; border-radius: 999px;
    background: rgba(245, 208, 118, 0.16);
    border: 1px solid rgba(245, 208, 118, 0.55);
    font-size: 13px; font-weight: 800; letter-spacing: 2.2px;
    color: #FDE68A; text-transform: uppercase;
  }}

  /* ACT 4 ONLY: Core Lesson Takeaway Card */
  .climax-box {{
    position: absolute; left: 50%; transform: translateX(-50%);
    top: {228 if is_short else 132}px;
    z-index: 7; width: {620 if is_short else 840}px;
    background: rgba(8, 18, 40, 0.86);
    border: 2.5px solid #F5D076;
    border-radius: 22px;
    padding: {24 if is_short else 16}px 28px;
    text-align: center;
    box-shadow: 0 0 40px rgba(245, 208, 118, 0.30), 0 16px 36px rgba(0,0,0,0.48);
    display: none;
  }}
  .climax-kicker {{
    font-size: 14px; font-weight: 900; letter-spacing: 3px; color: #F5D076;
    text-transform: uppercase; margin-bottom: 10px;
  }}
  .climax-lesson {{
    font-size: {34 if is_short else 29}px; font-weight: 900; line-height: 1.24;
    color: #FFFFFF; margin-bottom: 14px;
  }}

  /* Compact 4-Act step indicator above subtitles */
  .step-pill {{
    position: absolute; left: 50%; transform: translateX(-50%);
    bottom: {236 if is_short else 128}px; z-index: 7;
    display: inline-flex; align-items: center; gap: 12px;
    padding: 6px 18px; border-radius: 999px;
    background: rgba(7, 15, 30, 0.68);
    border: 1px solid rgba(255,255,255,0.22);
    font-size: 13px; font-weight: 800; letter-spacing: 1.8px; color: #E2E8F0;
  }}
  .dots {{ display: inline-flex; align-items: center; gap: 8px; }}
  .dot {{ width: 10px; height: 10px; border-radius: 50%; background: rgba(255,255,255,0.28); }}
  .dot.done {{ background: #F5D076; box-shadow: 0 0 8px rgba(245,208,118,0.75); }}
  .dot.active {{ background: #FFFFFF; transform: scale(1.25); box-shadow: 0 0 12px #FDE68A; }}

  .sub-area {{
    position: absolute; left: 30px; right: 30px;
    bottom: {72 if is_short else 28}px;
    z-index: 8; text-align: center;
  }}
  .sub-card {{
    display: inline-block; max-width: {640 if is_short else 960}px;
    padding: 11px 22px; border-radius: 16px;
    background: rgba(5, 11, 24, 0.80);
    border: 1px solid rgba(255,255,255,0.18);
    box-shadow: 0 10px 28px rgba(0,0,0,0.48);
  }}
  .sub-text {{
    font-size: {sub_size}px; font-weight: 700; line-height: 1.26;
    color: #F8FAFC; text-shadow: 0 2px 6px rgba(0,0,0,0.65);
  }}
  .sub-text .hi {{ color: #FDE68A; }}

  .brand-foot {{
    position: absolute; bottom: {22 if is_short else 6}px; left: 0; right: 0;
    z-index: 9; text-align: center;
    font-size: 14px; font-weight: 600; letter-spacing: 2px;
    color: rgba(255,255,255,0.70); text-shadow: 0 2px 6px rgba(0,0,0,0.7);
  }}
</style>
</head>
<body>
<canvas id="bgCanvas" width="{width}" height="{height}"></canvas>

<div class="stage">
  <div class="act-pill" id="actPill">ACT 1 • HOOK</div>
  <div class="headline-pill" id="headline"></div>
  <div class="mini-cit" id="miniCit"></div>
</div>

<div class="dalil-box" id="dalilBox">
  <div class="arabic-text" id="arText"></div>
  <div class="translit" id="trText"></div>
  <div class="translation" id="enText"></div>
  <div class="citation-row" id="citText"></div>
</div>

<div class="climax-box" id="climaxBox">
  <div class="climax-kicker">✦  THE LESSON  ✦</div>
  <div class="climax-lesson" id="climaxLesson"></div>
  <div class="citation-row" id="climaxCit"></div>
</div>

<div class="step-pill">
  <span id="stepLabel">HOOK</span>
  <span class="dots" id="dotsWrap"></span>
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
const STORY = CFG.story_acts || {{}};

{STORY_ACTS_JS}

const ACTS = computeFourActTiming(CFG);

document.getElementById('arText').textContent = CFG.dalil.arabic;
document.getElementById('trText').textContent = CFG.dalil.transliteration;
document.getElementById('enText').textContent = '"' + CFG.dalil.translation + '"';
document.getElementById('citText').textContent = '✦  ' + CFG.dalil.citation + '  ✦';
document.getElementById('climaxLesson').textContent = STORY.core_lesson || CFG.dalil.translation;
document.getElementById('climaxCit').textContent = '✦  ' + CFG.dalil.citation + '  •  SAVE & SHARE  ✦';
document.getElementById('brandFoot').textContent = CFG.dalil.handle + '  •  Save & Share the Sunnah';

const dotsWrap = document.getElementById('dotsWrap');
for (let i = 0; i < 4; i++) {{
  const d = document.createElement('span');
  d.className = 'dot';
  dotsWrap.appendChild(d);
}}

const SKY_STAGES = [
  {{ top: [15, 23, 62],   mid: [49, 54, 118],  bot: [148, 92, 138], sunY: 0.72, sunCol: [253, 210, 152], starA: 0.72, mode: 'fajr' }},
  {{ top: [26, 75, 134],  mid: [72, 136, 186], bot: [238, 174, 126], sunY: 0.76, sunCol: [255, 224, 150], starA: 0.15, mode: 'sunrise' }},
  {{ top: [22, 92, 168],  mid: [64, 148, 212], bot: [164, 212, 240], sunY: 0.67, sunCol: [255, 246, 200], starA: 0.0,  mode: 'dhuhr' }},
  {{ top: [46, 74, 126],  mid: [182, 126, 88], bot: [246, 186, 108], sunY: 0.71, sunCol: [255, 216, 128], starA: 0.08, mode: 'asr' }},
  {{ top: [48, 26, 76],   mid: [158, 66, 92],  bot: [244, 146, 86],  sunY: 0.77, sunCol: [255, 166, 98],  starA: 0.45, mode: 'maghrib' }},
  {{ top: [7, 13, 34],    mid: [16, 29, 68],   bot: [34, 58, 106],   sunY: 0.68, sunCol: [248, 236, 186], starA: 0.95, mode: 'isha' }},
];

const STARS = [];
for (let i = 0; i < 85; i++) {{
  STARS.push({{ x: ((i * 197.3) % 1000) / 1000, y: ((i * 313.7) % 580) / 1000, r: 0.8 + (i % 4) * 0.45, ph: i * 1.13 }});
}}

function lerp(a, b, t) {{ return a + (b - a) * t; }}
function lerpRGB(c1, c2, t) {{
  return [Math.round(lerp(c1[0], c2[0], t)), Math.round(lerp(c1[1], c2[1], t)), Math.round(lerp(c1[2], c2[2], t))];
}}
function rgb(c, a = 1) {{ return `rgba(${{c[0]}},${{c[1]}},${{c[2]}},${{a}})`; }}

function drawMosqueSilhouette(horizonY, scale, t, isReflection) {{
  ctx.save();
  ctx.translate(W * 0.5, horizonY);
  if (isReflection) {{ ctx.scale(1, -0.58); ctx.globalAlpha = 0.32; }}
  ctx.fillStyle = isReflection ? '#070F24' : '#081022';

  ctx.beginPath();
  ctx.moveTo(-W * 0.52, 2);
  ctx.quadraticCurveTo(-W * 0.28, -26 * scale, 0, -14 * scale);
  ctx.quadraticCurveTo(W * 0.28, -28 * scale, W * 0.52, 2);
  ctx.closePath(); ctx.fill();

  const mw = 190 * scale, mh = 56 * scale;
  ctx.fillRect(-mw * 0.5, -mh, mw, mh + 4);
  ctx.beginPath();
  ctx.moveTo(-58 * scale, -mh);
  ctx.bezierCurveTo(-64 * scale, -mh - 48 * scale, -26 * scale, -mh - 84 * scale, 0, -mh - 102 * scale);
  ctx.bezierCurveTo(26 * scale, -mh - 84 * scale, 64 * scale, -mh - 48 * scale, 58 * scale, -mh);
  ctx.closePath(); ctx.fill();

  ctx.fillRect(-1.8 * scale, -mh - 122 * scale, 3.6 * scale, 22 * scale);
  ctx.beginPath(); ctx.arc(0, -mh - 126 * scale, 6 * scale, 0.25 * Math.PI, 1.85 * Math.PI); ctx.fill();

  for (const dir of [-1, 1]) {{
    ctx.beginPath(); ctx.arc(dir * 72 * scale, -mh, 28 * scale, Math.PI, 0); ctx.closePath(); ctx.fill();
    const mx = dir * 118 * scale;
    ctx.fillRect(mx - 8 * scale, -mh - 118 * scale, 16 * scale, mh + 120 * scale);
    ctx.fillRect(mx - 13 * scale, -mh - 92 * scale, 26 * scale, 7 * scale);
    ctx.beginPath();
    ctx.moveTo(mx - 8 * scale, -mh - 118 * scale);
    ctx.lineTo(mx, -mh - 152 * scale);
    ctx.lineTo(mx + 8 * scale, -mh - 118 * scale);
    ctx.closePath(); ctx.fill();
  }}

  ctx.fillStyle = isReflection ? 'rgba(253, 214, 120, 0.45)' : 'rgba(253, 214, 120, 0.78)';
  for (const wx of [-46, -23, 0, 23, 46]) {{
    ctx.beginPath();
    ctx.arc(wx * scale, -28 * scale, 6 * scale, Math.PI, 0);
    ctx.lineTo((wx + 6) * scale, -10 * scale);
    ctx.lineTo((wx - 6) * scale, -10 * scale);
    ctx.closePath(); ctx.fill();
  }}

  ctx.fillStyle = isReflection ? '#070F24' : '#081022';
  const sway = Math.sin(t * 0.9) * 5 * scale;
  for (const palm of [{{ x: -235, h: 112 }}, {{ x: -278, h: 86 }}, {{ x: 242, h: 108 }}, {{ x: 286, h: 82 }}]) {{
    const px = palm.x * scale, ph = palm.h * scale;
    ctx.beginPath();
    ctx.moveTo(px - 4 * scale, 4);
    ctx.quadraticCurveTo(px + sway * 0.5, -ph * 0.5, px + sway, -ph);
    ctx.lineTo(px + sway + 4 * scale, -ph);
    ctx.quadraticCurveTo(px + sway * 0.5 + 5 * scale, -ph * 0.5, px + 5 * scale, 4);
    ctx.closePath(); ctx.fill();
    for (let a = 0; a < 6; a++) {{
      const ang = -Math.PI + (a / 5) * Math.PI * 1.15;
      ctx.beginPath(); ctx.moveTo(px + sway, -ph);
      ctx.quadraticCurveTo(px + sway + Math.cos(ang) * 28 * scale, -ph + Math.sin(ang) * 20 * scale - 10 * scale,
        px + sway + Math.cos(ang) * 50 * scale, -ph + Math.sin(ang) * 26 * scale + 8 * scale);
      ctx.lineWidth = 3.2 * scale; ctx.strokeStyle = isReflection ? '#070F24' : '#081022'; ctx.stroke();
    }}
  }}
  ctx.restore();
}}

function drawPrayerSkyScene(progress, t) {{
  const horizonY = H * (IS_SHORT ? 0.76 : 0.80);
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

  const skyG = ctx.createLinearGradient(0, 0, 0, horizonY);
  skyG.addColorStop(0, rgb(topC)); skyG.addColorStop(0.56, rgb(midC)); skyG.addColorStop(1, rgb(botC));
  ctx.fillStyle = skyG; ctx.fillRect(0, 0, W, horizonY + 2);

  const topScrim = ctx.createLinearGradient(0, 0, 0, H * 0.48);
  topScrim.addColorStop(0, 'rgba(6, 13, 30, 0.50)'); topScrim.addColorStop(1, 'rgba(6, 13, 30, 0.0)');
  ctx.fillStyle = topScrim; ctx.fillRect(0, 0, W, H * 0.48);

  if (starA > 0.02) {{
    for (const st of STARS) {{
      const tw = 0.55 + 0.45 * Math.sin(t * 2.1 + st.ph);
      ctx.fillStyle = `rgba(255, 250, 232, ${{starA * tw * 0.85}})`;
      ctx.beginPath(); ctx.arc(st.x * W, st.y * horizonY, st.r, 0, Math.PI * 2); ctx.fill();
    }}
  }}

  const sunX = W * (0.20 + progress * 0.60);
  const halo = ctx.createRadialGradient(sunX, sunY, 8, sunX, sunY, 170);
  halo.addColorStop(0, rgb(sunC, 0.72)); halo.addColorStop(0.35, rgb(sunC, 0.24)); halo.addColorStop(1, rgb(sunC, 0.0));
  ctx.fillStyle = halo; ctx.fillRect(sunX - 180, sunY - 180, 360, 360);

  if (starA > 0.52) {{
    ctx.save(); ctx.fillStyle = rgb(sunC, 0.95);
    ctx.beginPath(); ctx.arc(sunX, sunY, 22, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = rgb(midC, 1);
    ctx.beginPath(); ctx.arc(sunX + 9, sunY - 5, 19, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }} else {{
    ctx.fillStyle = rgb(sunC, 0.92);
    ctx.beginPath(); ctx.arc(sunX, sunY, 26, 0, Math.PI * 2); ctx.fill();
  }}

  const waterG = ctx.createLinearGradient(0, horizonY, 0, H);
  waterG.addColorStop(0, rgb(botC, 0.78)); waterG.addColorStop(0.28, rgb(midC, 0.88)); waterG.addColorStop(1, rgb([6, 12, 26], 1));
  ctx.fillStyle = waterG; ctx.fillRect(0, horizonY, W, H - horizonY);

  for (let i = 0; i < 22; i++) {{
    const wy = horizonY + 8 + i * ((H - horizonY) / 22);
    const spread = 24 + i * 7.5;
    const wob = Math.sin(t * 2.2 + i * 0.9) * 14;
    ctx.fillStyle = rgb(sunC, Math.max(0.05, 0.34 - i * 0.013));
    ctx.fillRect(sunX - spread * 0.5 + wob, wy, spread, 2.2);
  }}

  const scale = IS_SHORT ? 1.0 : 0.68;
  drawMosqueSilhouette(horizonY, scale, t, true);
  drawMosqueSilhouette(horizonY, scale, t, false);
}}

window.renderAt = function(t) {{
  const act = getCurrentAct(t, ACTS);
  // Tie prayer sky progression directly to the 4 Acts: Fajr (Hook) -> Sunrise (Dalil) -> Dhuhr/Asr (Explainer) -> Maghrib/Isha (Climax)!
  let skyP = 0;
  if (act.name === 'HOOK') skyP = act.localT * 0.16;
  else if (act.name === 'DALIL') skyP = 0.18 + act.localT * 0.22;
  else if (act.name === 'EXPLAINER') skyP = 0.42 + act.localT * 0.30;
  else skyP = 0.76 + act.localT * 0.24;

  drawPrayerSkyScene(skyP, t);

  const pal = {{
    bgCard: 'rgba(7, 16, 36, 0.86)',
    border: 'rgba(245, 208, 118, 0.65)',
    ink: '#F8FAFC',
    muted: '#94A3B8',
    accent: '#F5D076',
    good: '#34D399',
    light: false,
  }};
  const stageY = H * (IS_SHORT ? 0.43 : 0.47);
  if (act.name === 'HOOK') {{
    drawAct1HookVisual(ctx, STORY.hook_visual || 'phone_chaos', W * 0.5, stageY, IS_SHORT ? 1.14 : 0.90, act.localT, t, pal);
  }} else if (act.name === 'EXPLAINER') {{
    drawAct3ExplainerVisual(ctx, STORY, W * 0.5, stageY, IS_SHORT ? 1.04 : 0.88, act.localT, t, pal);
  }}

  let cur = CFG.scenes[CFG.scenes.length - 1];
  for (const s of CFG.scenes) {{
    if (t >= s.start && t <= s.end) {{ cur = s; break; }}
  }}

  const actPill = document.getElementById('actPill');
  const headEl = document.getElementById('headline');
  const miniCit = document.getElementById('miniCit');
  const dalilBox = document.getElementById('dalilBox');
  const climaxBox = document.getElementById('climaxBox');
  const stepLabel = document.getElementById('stepLabel');
  const arWin = CFG.arabic_window;

  if (act.name === 'HOOK') {{
    dalilBox.style.display = 'none';
    climaxBox.style.display = 'none';
    actPill.textContent = 'ACT 1 • ' + (STORY.hook_kicker || 'THE HOOK');
    actPill.style.borderColor = '#F87171'; actPill.style.color = '#FCA5A5';
    headEl.textContent = (CFG.scenes[0] && CFG.scenes[0].headline) || CFG.dalil.topic;
    miniCit.textContent = '';
    stepLabel.textContent = '1. THE HOOK';
  }} else if (act.name === 'DALIL') {{
    dalilBox.style.display = 'block';
    climaxBox.style.display = 'none';
    actPill.textContent = (arWin && arWin.is_qari) ? `ACT 2 • TILAWAH (${{arWin.reciter}})` : 'ACT 2 • PROPHETIC SUNNAH';
    actPill.style.borderColor = '#F5D076'; actPill.style.color = '#F5D076';
    headEl.textContent = CFG.dalil.citation;
    miniCit.textContent = '';
    stepLabel.textContent = '2. VERIFIED DALIL';
  }} else if (act.name === 'EXPLAINER') {{
    dalilBox.style.display = 'none';
    climaxBox.style.display = 'none';
    actPill.textContent = 'ACT 3 • THE SCIENCE';
    actPill.style.borderColor = '#34D399'; actPill.style.color = '#6EE7B7';
    headEl.textContent = (cur && cur.headline) || 'HOW IT REWIRES YOUR DAY';
    miniCit.textContent = '✦  ' + CFG.dalil.citation + '  ✦';
    stepLabel.textContent = '3. MIND SCIENCE';
  }} else {{
    dalilBox.style.display = 'none';
    climaxBox.style.display = 'block';
    actPill.textContent = 'ACT 4 • THE LESSON';
    actPill.style.borderColor = '#F5D076'; actPill.style.color = '#FDE68A';
    headEl.textContent = (cur && cur.headline) || 'START TODAY';
    miniCit.textContent = '';
    stepLabel.textContent = '4. THE LESSON';
  }}

  const dots = dotsWrap.children;
  const activeIdx = act.num - 1;
  for (let i = 0; i < dots.length; i++) {{
    dots[i].className = 'dot' + (i < activeIdx ? ' done' : (i === activeIdx ? ' active' : ''));
  }}

  let cap = null;
  for (const c of CFG.captions) {{
    if (t >= c.start - 0.06 && t <= c.end + 0.14) {{ cap = c; break; }}
  }}
  const subCard = document.getElementById('subCard');
  const subText = document.getElementById('subText');
  if (act.name === 'DALIL') {{
    subCard.style.opacity = '1';
    subText.innerHTML = `<span class="hi" style="font-style:italic">"${{CFG.dalil.translation}}"</span>`;
  }} else if (cap && cap.words && cap.words.length) {{
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
    """Mode 4: `islamic_gold_visualizer` (Ref #4 Luxury Obsidian & 24k Gold Sunburst + True 4-Act Storytelling)."""
    font_css = _load_amiri_font_css()
    cfg_json = json.dumps(payload, ensure_ascii=False)
    is_short = height >= width
    ar_size = 52 if is_short else 44
    en_size = 30 if is_short else 27

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

  /* ACT 1, 3, 4 Top Bar (clean obsidian & gold header) */
  .act-header {{
    position: absolute; top: {62 if is_short else 18}px; left: 32px; right: 32px;
    z-index: 6; text-align: center;
    display: flex; flex-direction: column; align-items: center;
  }}
  .act-pill {{
    display: inline-block; padding: 5px 18px; border-radius: 999px;
    background: rgba(232, 197, 107, 0.14);
    border: 1.5px solid rgba(232, 197, 107, 0.65);
    font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 800;
    letter-spacing: 2.4px; text-transform: uppercase; color: #F4C95D;
    margin-bottom: {10 if is_short else 6}px;
  }}
  .act-title {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: {36 if is_short else 30}px; font-weight: 900; line-height: 1.16;
    text-transform: uppercase; color: #FFFDF7;
    max-width: {640 if is_short else 960}px;
    text-shadow: 0 3px 18px rgba(0,0,0,0.75);
  }}
  .mini-cit {{
    margin-top: 5px; font-size: 12px; font-weight: 700; letter-spacing: 2.2px;
    color: rgba(244, 201, 93, 0.85); text-transform: uppercase;
  }}

  /* ACT 2 ONLY: Sacred Surah/Ayah Header above 72-bar 24k Gold Sunburst! */
  .top-header {{
    position: absolute; top: {66 if is_short else 10}px; left: 0; right: 0;
    z-index: 6; text-align: center; display: none;
  }}
  .surah-ar {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; font-size: {38 if is_short else 30}px; font-weight: 700;
    color: #E8C56B; text-shadow: 0 0 18px rgba(232, 197, 107, 0.35); margin-bottom: 2px;
  }}
  .surah-en {{
    font-family: 'Georgia', serif; font-size: {16 if is_short else 13}px; font-weight: 700;
    letter-spacing: 3.4px; text-transform: uppercase; color: rgba(232, 197, 107, 0.88);
  }}

  /* ACT 2 ONLY: RTL Gold Arabic Word-by-Word Karaoke underneath Sunburst */
  .karaoke-wrap {{
    position: absolute; left: 36px; right: 36px;
    top: {60 if is_short else 63}%;
    z-index: 7; text-align: center;
    display: none; flex-direction: column; align-items: center;
  }}
  .ar-karaoke {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; unicode-bidi: embed;
    font-size: {ar_size}px; font-weight: 700; line-height: 1.50;
    max-width: {650 if is_short else 1040}px; margin-bottom: {12 if is_short else 4}px;
  }}
  .ar-w {{ color: rgba(255, 250, 238, 0.34); }}
  .ar-w.lit {{ color: #F4C95D; text-shadow: 0 0 22px rgba(244, 201, 93, 0.65); }}
  .ar-w.past {{ color: rgba(255, 248, 232, 0.90); }}
  .tr-line {{
    font-family: 'Georgia', serif; font-style: italic;
    font-size: {18 if is_short else 15}px; color: rgba(203, 213, 225, 0.72);
    margin-bottom: {14 if is_short else 6}px; max-width: {640 if is_short else 980}px;
  }}

  /* ACT 4 ONLY: Obsidian & 24k Gold Core Lesson Card */
  .climax-gold {{
    position: absolute; left: 50%; transform: translateX(-50%);
    top: {246 if is_short else 156}px;
    z-index: 7; width: {620 if is_short else 840}px;
    background: rgba(10, 10, 14, 0.92);
    border: 2.5px solid #F4C95D;
    border-radius: 22px;
    padding: {26 if is_short else 18}px 30px;
    text-align: center;
    box-shadow: 0 0 44px rgba(244, 201, 93, 0.28), 0 18px 40px rgba(0,0,0,0.65);
    display: none;
  }}
  .climax-kicker {{
    font-family: 'Segoe UI', sans-serif; font-size: 14px; font-weight: 900;
    letter-spacing: 3.2px; color: #F4C95D; text-transform: uppercase; margin-bottom: 12px;
  }}
  .climax-lesson {{
    font-family: 'Georgia', serif;
    font-size: {34 if is_short else 29}px; font-weight: 700; line-height: 1.28;
    color: #FFFDF7; margin-bottom: 16px;
  }}
  .climax-cit {{
    display: inline-block; padding: 5px 18px; border-radius: 999px;
    background: rgba(244, 201, 93, 0.14); border: 1px solid rgba(244, 201, 93, 0.55);
    font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 800; letter-spacing: 2px;
    color: #F4C95D; text-transform: uppercase;
  }}

  /* Clean bottom gold-highlighted English narration line (visible across ALL 4 Acts!) */
  .en-dock {{
    position: absolute; left: 36px; right: 36px;
    bottom: {116 if is_short else 62}px;
    z-index: 8; text-align: center;
  }}
  .en-karaoke {{
    display: inline-block;
    font-family: 'Georgia', 'Times New Roman', serif;
    font-size: {en_size}px; font-weight: 500; line-height: 1.34;
    max-width: {640 if is_short else 980}px;
  }}
  .en-w {{ color: rgba(248, 250, 252, 0.42); }}
  .en-w.lit {{ color: #F4C95D; font-weight: 700; text-shadow: 0 0 18px rgba(244, 201, 93, 0.45); }}
  .en-w.past {{ color: rgba(248, 250, 252, 0.96); }}

  .insight-pill {{
    position: absolute; bottom: {66 if is_short else 26}px; left: 50%; transform: translateX(-50%);
    z-index: 8; max-width: {620 if is_short else 860}px;
    padding: 5px 18px; border-radius: 999px;
    background: rgba(232, 197, 107, 0.11);
    border: 1px solid rgba(232, 197, 107, 0.38);
    font-family: 'Segoe UI', sans-serif; font-size: {13 if is_short else 12}px; font-weight: 700; letter-spacing: 1.4px;
    color: #F3D999; white-space: nowrap;
  }}
  .brand-foot {{
    position: absolute; bottom: {22 if is_short else 4}px; left: 0; right: 0;
    z-index: 8; text-align: center;
    font-family: 'Segoe UI', sans-serif; font-size: {13 if is_short else 11}px; font-weight: 600;
    letter-spacing: 2.6px; text-transform: uppercase; color: rgba(232, 197, 107, 0.54);
  }}
</style>
</head>
<body>
<canvas id="bgCanvas" width="{width}" height="{height}"></canvas>

<div class="act-header" id="actHeader">
  <div class="act-pill" id="actPill">ACT 1 • HOOK</div>
  <div class="act-title" id="actTitle"></div>
  <div class="mini-cit" id="miniCit"></div>
</div>

<div class="top-header" id="topHeader">
  <div class="surah-ar" id="surahAr"></div>
  <div class="surah-en" id="surahEn"></div>
</div>

<div class="karaoke-wrap" id="karaokeWrap">
  <div class="ar-karaoke" id="arKaraoke"></div>
  <div class="tr-line" id="trLine"></div>
</div>

<div class="climax-gold" id="climaxGold">
  <div class="climax-kicker">✦  THE LESSON  ✦</div>
  <div class="climax-lesson" id="climaxLesson"></div>
  <div class="climax-cit" id="climaxCit"></div>
</div>

<div class="en-dock"><div class="en-karaoke" id="enKaraoke"></div></div>
<div class="insight-pill" id="insightPill"></div>
<div class="brand-foot" id="brandFoot"></div>

<script>
const CFG = {cfg_json};
const W = {width}, H = {height};
const IS_SHORT = H >= W;
const ctx = document.getElementById('bgCanvas').getContext('2d');
const STORY = CFG.story_acts || {{}};

{STORY_ACTS_JS}

const ACTS = computeFourActTiming(CFG);

document.getElementById('surahAr').textContent = CFG.dalil.surah_ar;
document.getElementById('surahEn').textContent = CFG.dalil.citation;
document.getElementById('trLine').textContent = CFG.dalil.transliteration;
document.getElementById('climaxLesson').textContent = STORY.core_lesson || CFG.dalil.translation;
document.getElementById('climaxCit').textContent = '✦  ' + CFG.dalil.citation + '  •  SAVE & SHARE  ✦';
document.getElementById('brandFoot').textContent = CFG.dalil.handle + '  ·  QUR\\'AN & CALM MIND SCIENCE';

const AR_WORDS = CFG.dalil.arabic.split(/\\s+/).filter(Boolean);
document.getElementById('arKaraoke').innerHTML = AR_WORDS.map((w, i) => `<span class="ar-w" id="arw_${{i}}">${{w}}</span>`).join(' ');

const DUST = [];
for (let i = 0; i < 65; i++) {{
  DUST.push({{ x: ((i * 173.9) % 1000) / 1000, y: ((i * 289.1) % 1000) / 1000, r: 0.9 + (i % 4) * 0.55, sp: 0.012 + (i % 5) * 0.005, ph: i * 0.9 }});
}}

function drawIslamicStarPattern(cx, cy, t, alpha) {{
  ctx.save(); ctx.translate(cx, cy); ctx.rotate(t * 0.035);
  ctx.strokeStyle = `rgba(218, 178, 86, ${{alpha}})`; ctx.lineWidth = 1.2;
  const maxR = IS_SHORT ? 275 : 220;
  for (const r of [maxR * 0.58, maxR * 0.82, maxR]) {{
    for (const rot of [0, Math.PI / 4]) {{
      ctx.save(); ctx.rotate(rot); ctx.strokeRect(-r * 0.72, -r * 0.72, r * 1.44, r * 1.44); ctx.restore();
    }}
    ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke();
  }}
  ctx.restore();
}}

function drawGoldSunburst(cx, cy, amp, t) {{
  const baseR = IS_SHORT ? 114 : 70;
  const bars = 72;
  ctx.save(); ctx.translate(cx, cy);
  ctx.fillStyle = 'rgba(7, 7, 10, 0.92)';
  ctx.beginPath(); ctx.arc(0, 0, baseR - 2, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = 'rgba(244, 201, 93, 0.78)'; ctx.lineWidth = 2.0;
  ctx.beginPath(); ctx.arc(0, 0, baseR - 3, 0, Math.PI * 2); ctx.stroke();
  ctx.strokeStyle = 'rgba(244, 201, 93, 0.25)'; ctx.lineWidth = 1.2;
  ctx.beginPath(); ctx.arc(0, 0, baseR - 13, 0, Math.PI * 2); ctx.stroke();

  for (let i = 0; i < bars; i++) {{
    const ang = (i / bars) * Math.PI * 2 - Math.PI / 2;
    const wave = 0.52 + 0.48 * Math.sin(i * 0.55 + t * 5.2) * Math.cos(i * 0.25 - t * 3.1);
    const barLen = 10 + (amp * 68 + 10) * (0.35 + 0.65 * Math.abs(wave));
    const x1 = Math.cos(ang) * (baseR + 5), y1 = Math.sin(ang) * (baseR + 5);
    const x2 = Math.cos(ang) * (baseR + 5 + barLen), y2 = Math.sin(ang) * (baseR + 5 + barLen);
    const g = ctx.createLinearGradient(x1, y1, x2, y2);
    g.addColorStop(0, 'rgba(255, 224, 134, 0.96)');
    g.addColorStop(0.65, 'rgba(218, 165, 56, 0.78)');
    g.addColorStop(1, 'rgba(180, 125, 28, 0.08)');
    ctx.strokeStyle = g; ctx.lineWidth = IS_SHORT ? 3.2 : 2.8; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  }}

  const numText = CFG.dalil.badge_num;
  const numSize = numText.length <= 3 ? (IS_SHORT ? 60 : 50) : (numText.length <= 5 ? (IS_SHORT ? 44 : 38) : (IS_SHORT ? 32 : 28));
  ctx.fillStyle = '#F7D77C';
  ctx.font = `700 ${{numSize}}px Georgia, 'Times New Roman', serif`;
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(numText, 0, -10);
  ctx.fillStyle = 'rgba(232, 197, 107, 0.78)';
  ctx.font = `600 ${{IS_SHORT ? 14 : 12}}px 'Segoe UI', sans-serif`;
  ctx.fillText(CFG.dalil.badge_label, 0, 30);
  ctx.restore();
}}

window.renderAt = function(t) {{
  const act = getCurrentAct(t, ACTS);
  const fIdx = Math.min(Math.floor(t * CFG.fps), Math.max(CFG.rms.length - 1, 0));
  const amp = CFG.rms.length ? CFG.rms[fIdx] : 0.35;

  const cx = W * 0.5;
  const cy = H * (IS_SHORT ? 0.38 : 0.41);
  ctx.fillStyle = '#050507';
  ctx.fillRect(0, 0, W, H);

  const auraMult = act.name === 'CLIMAX' ? 1.35 : (act.name === 'DALIL' ? 1.15 : 0.75);
  const auraR = (IS_SHORT ? 330 : 280) * auraMult + amp * 36;
  const aura = ctx.createRadialGradient(cx, cy, 18, cx, cy, auraR);
  aura.addColorStop(0, `rgba(212, 168, 68, ${{(0.20 + amp * 0.16) * auraMult}})`);
  aura.addColorStop(0.5, 'rgba(142, 102, 32, 0.08)');
  aura.addColorStop(1, 'rgba(5, 5, 7, 0)');
  ctx.fillStyle = aura; ctx.fillRect(0, 0, W, H);

  drawIslamicStarPattern(cx, cy, t, act.name === 'DALIL' ? 0.095 : 0.06);

  for (const d of DUST) {{
    const dx = d.x * W + Math.sin(t * 0.6 + d.ph) * 14;
    const dy = ((d.y - t * d.sp) % 1 + 1) % 1 * H;
    const a = 0.18 + 0.34 * (0.5 + 0.5 * Math.sin(t * 1.8 + d.ph));
    ctx.fillStyle = `rgba(244, 206, 112, ${{a}})`;
    ctx.beginPath(); ctx.arc(dx, dy, d.r, 0, Math.PI * 2); ctx.fill();
  }}

  const pal = {{
    bgCard: 'rgba(12, 12, 16, 0.92)',
    border: 'rgba(244, 201, 93, 0.68)',
    ink: '#FFFDF7',
    muted: '#94A3B8',
    accent: '#F4C95D',
    good: '#34D399',
    light: false,
  }};

  if (act.name === 'HOOK') {{
    drawAct1HookVisual(ctx, STORY.hook_visual || 'racing_mind', cx, H * (IS_SHORT ? 0.45 : 0.48), IS_SHORT ? 1.16 : 0.90, act.localT, t, pal);
  }} else if (act.name === 'DALIL') {{
    drawGoldSunburst(cx, cy, amp, t);
  }} else if (act.name === 'EXPLAINER') {{
    drawAct3ExplainerVisual(ctx, STORY, cx, H * (IS_SHORT ? 0.45 : 0.47), IS_SHORT ? 1.05 : 0.88, act.localT, t, pal);
  }}

  let cur = CFG.scenes[CFG.scenes.length - 1];
  for (const s of CFG.scenes) {{
    if (t >= s.start && t <= s.end) {{ cur = s; break; }}
  }}

  const actHeader = document.getElementById('actHeader');
  const topHeader = document.getElementById('topHeader');
  const karaokeWrap = document.getElementById('karaokeWrap');
  const climaxGold = document.getElementById('climaxGold');
  const actPill = document.getElementById('actPill');
  const actTitle = document.getElementById('actTitle');
  const miniCit = document.getElementById('miniCit');
  const arWin = CFG.arabic_window;

  if (act.name === 'HOOK') {{
    actHeader.style.display = 'flex';
    topHeader.style.display = 'none';
    karaokeWrap.style.display = 'none';
    climaxGold.style.display = 'none';
    actPill.textContent = 'ACT 1 • ' + (STORY.hook_kicker || 'STILL LOUD INSIDE?');
    actPill.style.borderColor = '#F87171'; actPill.style.color = '#FCA5A5';
    actTitle.textContent = (CFG.scenes[0] && CFG.scenes[0].headline) || CFG.dalil.topic;
    miniCit.textContent = '';
  }} else if (act.name === 'DALIL') {{
    actHeader.style.display = 'none';
    topHeader.style.display = 'block';
    karaokeWrap.style.display = 'flex';
    climaxGold.style.display = 'none';
    const activeArIdx = Math.min(Math.floor(act.localT * AR_WORDS.length), AR_WORDS.length - 1);
    for (let i = 0; i < AR_WORDS.length; i++) {{
      const el = document.getElementById(`arw_${{i}}`);
      if (el) el.className = 'ar-w' + (i === activeArIdx ? ' lit' : (i < activeArIdx ? ' past' : ''));
    }}
  }} else if (act.name === 'EXPLAINER') {{
    actHeader.style.display = 'flex';
    topHeader.style.display = 'none';
    karaokeWrap.style.display = 'none';
    climaxGold.style.display = 'none';
    actPill.textContent = 'ACT 3 • THE SCIENCE';
    actPill.style.borderColor = '#34D399'; actPill.style.color = '#6EE7B7';
    actTitle.textContent = (cur && cur.headline) || 'HOW IT CALMS YOUR MIND';
    miniCit.textContent = '✦  ' + CFG.dalil.citation + '  ✦';
  }} else {{
    actHeader.style.display = 'flex';
    topHeader.style.display = 'none';
    karaokeWrap.style.display = 'none';
    climaxGold.style.display = 'block';
    actPill.textContent = 'ACT 4 • THE LESSON';
    actPill.style.borderColor = '#F4C95D'; actPill.style.color = '#F4C95D';
    actTitle.textContent = (cur && cur.headline) || 'PEACE OF MIND';
    miniCit.textContent = '';
  }}

  // English narration karaoke across ALL 4 Acts (or illuminated translation during Qari tilawah!)
  let cap = null;
  for (const c of CFG.captions) {{
    if (t >= c.start - 0.06 && t <= c.end + 0.14) {{ cap = c; break; }}
  }}
  const enEl = document.getElementById('enKaraoke');
  if (act.name === 'DALIL') {{
    const trWords = ('"' + CFG.dalil.translation + '"').split(/\\s+/).filter(Boolean);
    const litIdx = Math.floor(act.localT * trWords.length);
    enEl.innerHTML = trWords.map((w, i) => {{
      if (i === litIdx) return `<span class="en-w lit">${{w}}</span>`;
      if (i < litIdx) return `<span class="en-w past">${{w}}</span>`;
      return `<span class="en-w">${{w}}</span>`;
    }}).join(' ');
  }} else if (cap && cap.words && cap.words.length) {{
    enEl.innerHTML = cap.words.map(w => {{
      if (t >= w.s && t <= w.e + 0.10) return `<span class="en-w lit">${{w.w}}</span>`;
      if (t > w.e + 0.10) return `<span class="en-w past">${{w.w}}</span>`;
      return `<span class="en-w">${{w.w}}</span>`;
    }}).join(' ');
  }} else {{
    enEl.innerHTML = '';
  }}

  document.getElementById('insightPill').textContent = act.name === 'DALIL'
    ? (arWin && arWin.is_qari ? `✦  Tilawah • ${{arWin.reciter}}` : `✦  ${{CFG.dalil.citation}}`)
    : `✦  ACT ${{act.num}} OF 4  •  ${{act.name}}`;
}};
</script>
</body>
</html>"""


def _build_particle_map_html(payload: dict[str, Any], width: int, height: int) -> str:
    """Mode 5: `islamic_particle_map` (Ref #5 Cosmic Particle Constellations + True 4-Act Storytelling)."""
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

  .top-bar {{
    position: absolute; top: {46 if is_short else 16}px; left: 42px; right: 42px;
    z-index: 6; display: flex; flex-direction: column; align-items: center; gap: 10px;
  }}
  .prog-track {{
    width: 100%; max-width: {560 if is_short else 820}px; height: 4px;
    border-radius: 99px; background: rgba(255,255,255,0.14); overflow: hidden;
  }}
  #progFill {{
    height: 100%; width: 0%;
    background: linear-gradient(90deg, #38BDF8, #F4C95D); border-radius: 99px;
  }}
  .act-chip {{
    display: inline-block; padding: 4px 16px; border-radius: 999px;
    background: rgba(255,255,255,0.08);
    border: 1.5px solid rgba(244, 201, 93, 0.65);
    font-size: 13px; font-weight: 800; letter-spacing: 2.4px; text-transform: uppercase;
    color: #F4C95D;
  }}

  .hero-block {{
    position: absolute; top: {108 if is_short else 62}px; left: 32px; right: 32px;
    z-index: 7; text-align: center;
    display: flex; flex-direction: column; align-items: center;
  }}
  .scene-title {{
    font-size: {36 if is_short else 30}px; font-weight: 900; line-height: 1.15;
    color: #FFFFFF; text-transform: uppercase;
    text-shadow: 0 4px 20px rgba(0,0,0,0.70);
    max-width: {640 if is_short else 980}px;
  }}
  .mini-cit {{
    margin-top: 5px; font-size: 12px; font-weight: 700; letter-spacing: 2px;
    color: #FDE68A; text-transform: uppercase;
  }}

  /* ACT 2 ONLY: Sacred Cosmic Dalil Spotlight */
  .dalil-panel {{
    position: absolute; left: 50%; transform: translateX(-50%);
    top: {220 if is_short else 128}px;
    z-index: 7; width: {640 if is_short else 880}px;
    background: rgba(8, 14, 34, 0.84);
    border: 2px solid rgba(244, 201, 93, 0.78);
    border-radius: 22px;
    padding: {20 if is_short else 14}px 26px;
    text-align: center;
    box-shadow: 0 0 36px rgba(244, 201, 93, 0.25), 0 16px 36px rgba(0,0,0,0.52);
    display: none;
  }}
  .ar-quote {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; unicode-bidi: embed;
    font-size: {44 if is_short else 36}px; font-weight: 700; line-height: 1.52;
    color: #F4C95D; text-shadow: 0 0 20px rgba(244, 201, 93, 0.45);
    margin-bottom: 8px;
  }}
  .tr-quote {{
    font-family: 'Georgia', serif; font-size: {20 if is_short else 17}px;
    color: #E2E8F0; margin-bottom: 10px;
  }}
  .cit-badge {{
    display: inline-block; padding: 4px 16px; border-radius: 999px;
    background: rgba(244, 201, 93, 0.16);
    border: 1px solid rgba(244, 201, 93, 0.55);
    font-size: 13px; font-weight: 800; letter-spacing: 2px; color: #FDE68A;
  }}

  /* ACT 4 ONLY: Cosmic Core Lesson Card */
  .climax-cosmic {{
    position: absolute; left: 50%; transform: translateX(-50%);
    top: {230 if is_short else 138}px;
    z-index: 7; width: {620 if is_short else 840}px;
    background: rgba(12, 16, 38, 0.88);
    border: 2.5px solid #38BDF8;
    border-radius: 22px;
    padding: {24 if is_short else 16}px 28px;
    text-align: center;
    box-shadow: 0 0 40px rgba(56, 189, 248, 0.28), 0 18px 38px rgba(0,0,0,0.55);
    display: none;
  }}
  .climax-kicker {{
    font-size: 14px; font-weight: 900; letter-spacing: 3px; color: #7DD3FC;
    text-transform: uppercase; margin-bottom: 10px;
  }}
  .climax-lesson {{
    font-size: {34 if is_short else 29}px; font-weight: 900; line-height: 1.24;
    color: #FFFFFF; margin-bottom: 14px;
  }}

  .sub-area {{
    position: absolute; left: 30px; right: 30px;
    bottom: {122 if is_short else 60}px;
    z-index: 9; text-align: center;
  }}
  #subText {{
    display: inline-block; max-width: {640 if is_short else 980}px;
    font-size: {35 if is_short else 31}px; font-weight: 800; line-height: 1.24;
    color: #FFFFFF;
    -webkit-text-stroke: 1.8px rgba(5, 8, 18, 0.92);
    paint-order: stroke fill;
    text-shadow: 0 4px 16px rgba(0,0,0,0.85);
  }}
  #subText .gold {{ color: #FDE68A; }}

  .buckets {{
    position: absolute; bottom: {58 if is_short else 22}px; left: 32px; right: 32px;
    z-index: 8; display: flex; justify-content: center; gap: 8px;
  }}
  .bkt {{
    padding: 5px 14px; border-radius: 999px;
    background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.18);
    font-size: 12px; font-weight: 800; letter-spacing: 1.2px; color: rgba(226,232,240,0.58);
    text-transform: uppercase;
  }}
  .bkt.on {{
    background: rgba(244, 201, 93, 0.22); border-color: rgba(244, 201, 93, 0.80);
    color: #FEF3C7; box-shadow: 0 0 14px rgba(244, 201, 93, 0.30);
  }}

  .brand-foot {{
    position: absolute; bottom: {20 if is_short else 4}px; left: 0; right: 0;
    z-index: 8; text-align: center;
    font-size: 13px; font-weight: 600; letter-spacing: 2.2px; color: rgba(255,255,255,0.50);
  }}
</style>
</head>
<body>
<canvas id="bgCanvas" width="{width}" height="{height}"></canvas>

<div class="top-bar">
  <div class="prog-track"><div id="progFill"></div></div>
  <div class="act-chip" id="actChip">ACT 1 • HOOK</div>
</div>

<div class="hero-block">
  <div class="scene-title" id="sceneTitle"></div>
  <div class="mini-cit" id="miniCit"></div>
</div>

<div class="dalil-panel" id="dalilPanel">
  <div class="ar-quote" id="arQuote"></div>
  <div class="tr-quote" id="trQuote"></div>
  <div class="cit-badge" id="citBadge"></div>
</div>

<div class="climax-cosmic" id="climaxCosmic">
  <div class="climax-kicker">✦  THE LESSON  ✦</div>
  <div class="climax-lesson" id="climaxLesson"></div>
  <div class="cit-badge" id="climaxCit"></div>
</div>

<div class="sub-area"><div id="subText"></div></div>
<div class="buckets" id="bucketsWrap"></div>
<div class="brand-foot" id="brandFoot"></div>

<script>
const CFG = {cfg_json};
const W = {width}, H = {height};
const IS_SHORT = H >= W;
const ctx = document.getElementById('bgCanvas').getContext('2d');
const STORY = CFG.story_acts || {{}};

{STORY_ACTS_JS}

const ACTS = computeFourActTiming(CFG);

document.getElementById('arQuote').textContent = CFG.dalil.arabic;
document.getElementById('trQuote').textContent = CFG.dalil.transliteration;
document.getElementById('citBadge').textContent = '✦  ' + CFG.dalil.citation + '  ✦';
document.getElementById('climaxLesson').textContent = STORY.core_lesson || CFG.dalil.translation;
document.getElementById('climaxCit').textContent = '✦  ' + CFG.dalil.citation + '  •  SAVE & SHARE  ✦';
document.getElementById('brandFoot').textContent = CFG.dalil.handle + '  •  SUNNAH & MODERN BRAIN SCIENCE';

const bucketsWrap = document.getElementById('bucketsWrap');
const BKT_LABELS = ['1. HOOK', '2. DALIL', '3. SCIENCE', '4. LESSON'];
BKT_LABELS.forEach((lbl, i) => {{
  const el = document.createElement('div');
  el.className = 'bkt'; el.id = 'bkt_' + i; el.textContent = lbl;
  bucketsWrap.appendChild(el);
}});

const MOODS = [
  {{ c0: [14, 18, 48], c1: [6, 9, 24],  accent: [125, 211, 252] }},
  {{ c0: [10, 44, 42], c1: [5, 18, 22], accent: [244, 201, 93] }},
  {{ c0: [22, 32, 66], c1: [7, 10, 26], accent: [52, 211, 153] }},
  {{ c0: [52, 32, 18], c1: [14, 10, 16], accent: [251, 191, 36] }},
];

function lerp(a, b, t) {{ return a + (b - a) * t; }}
function lerpRGB(a, b, t) {{ return [Math.round(lerp(a[0], b[0], t)), Math.round(lerp(a[1], b[1], t)), Math.round(lerp(a[2], b[2], t))]; }}

const N_PART = 380;
const CX = W * 0.5;
const CY = H * (IS_SHORT ? 0.62 : 0.60);
const RAD = IS_SHORT ? 175 : 145;

function sampleShape(name) {{
  const pts = [];
  for (let i = 0; i < N_PART; i++) {{
    let x = 0, y = 0, sz = 2.0;
    if (name === 'crescent_stars') {{
      if (i < 260) {{
        const a = -0.78 * Math.PI + (i / 260) * 1.56 * Math.PI;
        const r = RAD * (0.76 + (i % 5) * 0.04);
        x = Math.cos(a) * r - 18; y = Math.sin(a) * r; sz = 2.6;
      }} else {{
        const k = i - 260; const sa = k * 2.39996; const sr = RAD * (0.35 + ((k * 37) % 100) / 115);
        x = Math.cos(sa) * sr + 28; y = Math.sin(sa) * sr; sz = (k % 4 === 0) ? 3.2 : 1.7;
      }}
    }} else if (name === 'ocean_drop') {{
      if (i < 160) {{
        const t = (i / 160) * Math.PI * 2; const dropR = RAD * 0.30;
        x = Math.sin(t) * dropR * (0.65 + 0.35 * Math.cos(t));
        y = -RAD * 0.36 - Math.cos(t) * dropR * 1.15; sz = 2.5;
      }} else {{
        const k = i - 160; const ring = k % 4; const a = (k / 220) * Math.PI * 2;
        x = Math.cos(a) * RAD * (0.48 + ring * 0.24);
        y = RAD * 0.38 + Math.sin(a) * RAD * (0.14 + ring * 0.075); sz = 2.1;
      }}
    }} else if (name === 'cave_arch') {{
      if (i < 230) {{
        const a = Math.PI + (i / 230) * Math.PI; const layer = (i % 4) * 16;
        x = Math.cos(a) * (RAD * 0.92 - layer); y = RAD * 0.42 + Math.sin(a) * (RAD * 1.08 - layer); sz = 2.6;
      }} else {{
        const k = i - 230; const r = (k / 150) * RAD * 0.56; const a = k * 2.39996;
        x = Math.cos(a) * r; y = RAD * 0.14 + Math.sin(a) * r * 0.85; sz = 2.2;
      }}
    }} else if (name === 'balance_scale') {{
      const grp = i % 3; const centerAng = -Math.PI / 2 + grp * (Math.PI * 2 / 3);
      const gx = Math.cos(centerAng) * (RAD * 0.46), gy = Math.sin(centerAng) * (RAD * 0.44);
      const a = (Math.floor(i / 3) / (N_PART / 3)) * Math.PI * 2;
      x = gx + Math.cos(a) * RAD * 0.38; y = gy + Math.sin(a) * RAD * 0.38; sz = 2.4;
    }} else if (name === 'brain_light') {{
      if (i < 280) {{
        const side = (i % 2 === 0) ? -1 : 1; const a = ((Math.floor(i / 2)) / 140) * Math.PI * 2;
        const fold = 1 + 0.10 * Math.sin(a * 5);
        x = side * (RAD * 0.32) + Math.cos(a) * RAD * 0.46 * fold; y = Math.sin(a) * RAD * 0.64 * fold; sz = 2.4;
      }} else {{
        const k = i - 280; x = -RAD * 0.95 + (k / 100) * RAD * 1.9;
        y = Math.sin((k / 100) * Math.PI * 4) * (RAD * 0.22); sz = 2.8;
      }}
    }} else if (name === 'sunrise_horizon') {{
      if (i < 190) {{
        const a = Math.PI + (i / 190) * Math.PI; const r = RAD * (0.48 + (i % 5) * 0.11);
        x = Math.cos(a) * r; y = RAD * 0.25 + Math.sin(a) * r; sz = 2.5;
      }} else {{
        const k = i - 190; const row = k % 3; const px = -RAD * 1.1 + ((Math.floor(k / 3)) / 64) * RAD * 2.2;
        x = px; y = RAD * (0.28 + row * 0.16) + Math.sin(px * 0.025 + row) * 14; sz = 2.1;
      }}
    }} else {{
      if (i < 220) {{
        const a = (i / 220) * Math.PI * 2; x = Math.cos(a) * (RAD * 0.84); y = Math.sin(a) * (RAD * 0.84); sz = 2.2;
      }} else {{
        const node = i % 4; const na = -Math.PI / 2 + node * (Math.PI / 2);
        const nx = Math.cos(na) * (RAD * 0.84), ny = Math.sin(na) * (RAD * 0.84);
        const a = ((i - 220) / 160) * Math.PI * 8;
        x = nx + Math.cos(a) * RAD * 0.18; y = ny + Math.sin(a) * RAD * 0.18; sz = 2.9;
      }}
    }}
    pts.push({{ x: CX + x, y: CY + y, sz, ph: i * 0.43 }});
  }}
  return pts;
}}

const SHAPE_NAMES = CFG.dalil.particle_shapes || ['crescent_stars', 'ocean_drop', 'brain_light', 'summary_constellation'];
const SHAPES = SHAPE_NAMES.map(sampleShape);

window.renderAt = function(t) {{
  const total = Math.max(CFG.total_dur, 1);
  const progress = Math.min(Math.max(t / total, 0), 1);
  document.getElementById('progFill').style.width = (progress * 100).toFixed(2) + '%';

  const act = getCurrentAct(t, ACTS);
  const mood = MOODS[Math.min(act.num - 1, MOODS.length - 1)];
  const c0 = mood.c0, c1 = mood.c1, acc = mood.accent;

  const bg = ctx.createRadialGradient(CX, CY, 20, CX, CY, Math.max(W, H) * 0.72);
  bg.addColorStop(0, `rgb(${{c0[0]}},${{c0[1]}},${{c0[2]}})`);
  bg.addColorStop(1, `rgb(${{c1[0]}},${{c1[1]}},${{c1[2]}})`);
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);

  // Pick constellation shape matched to the current Act
  const sIdx = Math.min(act.num - 1, SHAPES.length - 1);
  const A = SHAPES[sIdx];
  const fIdx = Math.min(Math.floor(t * CFG.fps), Math.max(CFG.rms.length - 1, 0));
  const amp = CFG.rms.length ? CFG.rms[fIdx] : 0.25;

  // Dim particles subtly behind Act 1 & Act 3 UI diagrams so diagrams pop razor-sharp, shine brightly in Act 2 & Act 4!
  const partAlpha = (act.name === 'DALIL' || act.name === 'CLIMAX') ? 0.95 : 0.34;
  ctx.save();
  ctx.globalAlpha = partAlpha;
  const halo = ctx.createRadialGradient(CX, CY, 12, CX, CY, RAD * 1.25);
  halo.addColorStop(0, `rgba(${{acc[0]}},${{acc[1]}},${{acc[2]}},${{0.18 + amp * 0.12}})`);
  halo.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = halo; ctx.fillRect(0, 0, W, H);

  ctx.strokeStyle = `rgba(${{acc[0]}},${{acc[1]}},${{acc[2]}}, 0.14)`; ctx.lineWidth = 1;
  ctx.beginPath();
  for (let i = 0; i < N_PART - 12; i += 12) {{
    if (Math.hypot(A[i + 12].x - A[i].x, A[i + 12].y - A[i].y) < 130) {{
      ctx.moveTo(A[i].x, A[i].y); ctx.lineTo(A[i + 12].x, A[i + 12].y);
    }}
  }}
  ctx.stroke();

  for (let i = 0; i < N_PART; i++) {{
    const pa = A[i];
    const px = pa.x + Math.sin(t * 1.3 + pa.ph) * 4.5;
    const py = pa.y + Math.cos(t * 1.1 + pa.ph * 1.3) * 4.5;
    const rad = pa.sz * (0.9 + amp * 0.30);
    const bright = 0.55 + 0.45 * Math.sin(t * 2.6 + pa.ph);
    ctx.fillStyle = (i % 3 === 0) ? `rgba(255, 245, 210, ${{bright}})` : `rgba(${{acc[0]}},${{acc[1]}},${{acc[2]}},${{bright * 0.92}})`;
    ctx.beginPath(); ctx.arc(px, py, rad, 0, Math.PI * 2); ctx.fill();
  }}
  ctx.restore();

  const pal = {{
    bgCard: 'rgba(8, 13, 32, 0.88)',
    border: 'rgba(125, 211, 252, 0.65)',
    ink: '#F8FAFC',
    muted: '#94A3B8',
    accent: '#F4C95D',
    good: '#34D399',
    light: false,
  }};
  const stageY = H * (IS_SHORT ? 0.46 : 0.49);
  if (act.name === 'HOOK') {{
    drawAct1HookVisual(ctx, STORY.hook_visual || 'racing_mind', W * 0.5, stageY, IS_SHORT ? 1.15 : 0.90, act.localT, t, pal);
  }} else if (act.name === 'EXPLAINER') {{
    drawAct3ExplainerVisual(ctx, STORY, W * 0.5, stageY, IS_SHORT ? 1.05 : 0.88, act.localT, t, pal);
  }}

  let cur = CFG.scenes[CFG.scenes.length - 1];
  for (const s of CFG.scenes) {{
    if (t >= s.start && t <= s.end) {{ cur = s; break; }}
  }}

  const actChip = document.getElementById('actChip');
  const titleEl = document.getElementById('sceneTitle');
  const miniCit = document.getElementById('miniCit');
  const dalilPanel = document.getElementById('dalilPanel');
  const climaxCosmic = document.getElementById('climaxCosmic');
  const arWin = CFG.arabic_window;

  if (act.name === 'HOOK') {{
    dalilPanel.style.display = 'none';
    climaxCosmic.style.display = 'none';
    actChip.textContent = 'ACT 1 • ' + (STORY.hook_kicker || 'THE FRAMEWORK');
    actChip.style.borderColor = '#F87171'; actChip.style.color = '#FCA5A5';
    titleEl.textContent = (CFG.scenes[0] && CFG.scenes[0].headline) || CFG.dalil.topic;
    miniCit.textContent = '';
  }} else if (act.name === 'DALIL') {{
    dalilPanel.style.display = 'block';
    climaxCosmic.style.display = 'none';
    actChip.textContent = (arWin && arWin.is_qari) ? `ACT 2 • TILAWAH (${{arWin.reciter}})` : 'ACT 2 • VERIFIED WISDOM';
    actChip.style.borderColor = '#F4C95D'; actChip.style.color = '#F4C95D';
    titleEl.textContent = CFG.dalil.citation;
    miniCit.textContent = '';
  }} else if (act.name === 'EXPLAINER') {{
    dalilPanel.style.display = 'none';
    climaxCosmic.style.display = 'none';
    actChip.textContent = 'ACT 3 • THE SCIENCE';
    actChip.style.borderColor = '#34D399'; actChip.style.color = '#6EE7B7';
    titleEl.textContent = (cur && cur.headline) || 'HOW IT WORKS';
    miniCit.textContent = '✦  ' + CFG.dalil.citation + '  ✦';
  }} else {{
    dalilPanel.style.display = 'none';
    climaxCosmic.style.display = 'block';
    actChip.textContent = 'ACT 4 • THE LESSON';
    actChip.style.borderColor = '#38BDF8'; actChip.style.color = '#7DD3FC';
    titleEl.textContent = (cur && cur.headline) || 'YOUR DAILY SHIFT';
    miniCit.textContent = '';
  }}

  const activeBkt = act.num - 1;
  for (let i = 0; i < 4; i++) {{
    const b = document.getElementById('bkt_' + i);
    if (b) b.className = 'bkt' + (i <= activeBkt ? ' on' : '');
  }}

  let cap = null;
  for (const c of CFG.captions) {{
    if (t >= c.start - 0.06 && t <= c.end + 0.14) {{ cap = c; break; }}
  }}
  const subEl = document.getElementById('subText');
  if (act.name === 'DALIL') {{
    subEl.innerHTML = `<span class="gold">"${{CFG.dalil.translation}}"</span>`;
  }} else if (cap && cap.words && cap.words.length) {{
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
    p = dict(payload)
    if not isinstance(p.get("story_acts"), dict):
        dalil_info = p.get("dalil") if isinstance(p.get("dalil"), dict) else {}
        p["story_acts"] = resolve_story_acts(
            topic_meta={"topic": dalil_info.get("topic", ""), "dalil": dalil_info},
            scenes_meta=p.get("scenes") or [],
        )
    m = (mode or "islamic_luminous_sky").lower().strip()
    if m == "islamic_nature_transform":
        return build_nature_transform_html(p, _load_amiri_font_css(), width, height)
    if m == "islamic_paper_craft":
        return build_paper_craft_html(p, _load_amiri_font_css(), width, height)
    if m == "islamic_cinematic_metaphor":
        return build_cinematic_metaphor_html(p, _load_amiri_font_css(), width, height)
    if m == "islamic_gold_visualizer":
        return _build_gold_visualizer_html(p, width, height)
    if m == "islamic_particle_map":
        return _build_particle_map_html(p, width, height)
    return _build_luminous_sky_html(p, width, height)


def _nature_preset_for_mode(mode: str) -> str:
    m = (mode or "").lower().strip()
    if m in ("islamic_gold_visualizer", "islamic_nature_transform"):
        return "gentle_rain"
    if m in ("islamic_particle_map", "islamic_cinematic_metaphor"):
        return "calm_water"
    return "dawn_breeze"


def _make_silence_wav(out_wav: Path, dur_sec: float) -> Path:
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
            "-t", f"{max(dur_sec, 0.05):.3f}", "-c:a", "pcm_s16le", str(out_wav),
        ],
        capture_output=True, check=True,
    )
    return out_wav


def _assemble_bilingual_voice_and_timeline(
    scenes_meta: list[dict[str, Any]],
    audio_bundle: TrackAudioBundle,
    arabic_res: ArabicRecitationResult | None,
    pause_sec: float,
    work_dir: Path,
    is_short: bool,
    safe_cap: float,
) -> tuple[Path, list[dict[str, Any]], list[dict[str, Any]], dict[str, Any] | None, float]:
    """Assemble bilingual English + Authentic Arabic (1.00x untouched!) voiceover WAV + exact synced timeline."""
    scene_results = audio_bundle.scene_results or []
    all_parts_exist = bool(scene_results) and all(Path(sr.audio_path).exists() for sr in scene_results)

    if arabic_res is None or not all_parts_exist:
        master_audio = Path(audio_bundle.master_audio_path)
        raw_dur = probe_duration_sec(master_audio)
        tempo = min(max(raw_dur / safe_cap, 1.02), 1.28) if (is_short and raw_dur > safe_cap) else 1.0
        out_wav = work_dir / "master_en_voice.wav"
        af = [f"atempo={tempo:.4f}"] if tempo > 1.01 else []
        af.append("aformat=sample_rates=48000:channel_layouts=stereo")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(master_audio), "-af", ",".join(af), "-c:a", "pcm_s16le", str(out_wav)],
            capture_output=True, check=True,
        )
        scene_items, captions, _ = _build_scene_and_caption_timeline(scenes_meta, audio_bundle, pause_sec, tempo=tempo)
        return out_wav, scene_items, captions, None, probe_duration_sec(out_wav)

    # Bilingual choreography: Scene 1 (Hook) -> 0.35s breath -> Arabic Recitation (1.00x untouched!) -> 0.45s breath -> Scenes 2..N
    pre_ar_pause = 0.35
    post_ar_pause = 0.45
    ar_dur = probe_duration_sec(arabic_res.audio_path)
    en_speech_sum = sum(probe_duration_sec(Path(sr.audio_path)) for sr in scene_results)
    en_pauses_sum = max(len(scene_results) - 1, 0) * pause_sec + pause_sec
    projected = en_speech_sum + en_pauses_sum + pre_ar_pause + ar_dur + post_ar_pause

    # If Short exceeds safe_cap, ONLY gently pace English narration (NEVER speed up Qur'an/Arabic recitation!)
    en_tempo = 1.0
    if is_short and projected > safe_cap:
        budget_en = max(safe_cap - (pre_ar_pause + ar_dur + post_ar_pause + en_pauses_sum) - 0.35, en_speech_sum * 0.70)
        en_tempo = min(max(en_speech_sum / max(budget_en, 1.0), 1.02), 1.32)
        print(
            f"[v10-bilingual] Keeping Arabic VO pure 1.00x ({ar_dur:.1f}s) & pacing English {en_tempo:.2f}x "
            f"to fit cleanly inside {safe_cap:.1f}s Shorts cap...",
            flush=True,
        )

    sil_scene = _make_silence_wav(work_dir / "_sil_scene.wav", max(pause_sec, 0.15))
    sil_pre_ar = _make_silence_wav(work_dir / "_sil_pre_ar.wav", pre_ar_pause)
    sil_post_ar = _make_silence_wav(work_dir / "_sil_post_ar.wav", post_ar_pause)

    concat_files: list[Path] = []
    scene_items: list[dict[str, Any]] = []
    captions: list[dict[str, Any]] = []
    cursor = 0.0
    scale = 1.0 / en_tempo
    arabic_window: dict[str, Any] | None = None
    insert_after_idx = 0  # Play authentic Arabic recitation right after Scene 1 hook!

    for idx, sr in enumerate(scene_results):
        en_wav = work_dir / f"_en_sc_{idx:02d}.wav"
        af_parts = [f"atempo={en_tempo:.4f}"] if en_tempo > 1.01 else []
        af_parts.append("loudnorm=I=-16:TP=-1.5:LRA=11,aformat=sample_rates=48000:channel_layouts=stereo")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(sr.audio_path), "-af", ",".join(af_parts), "-c:a", "pcm_s16le", str(en_wav)],
            capture_output=True, check=True,
        )
        s_dur = probe_duration_sec(en_wav)
        meta = scenes_meta[idx] if idx < len(scenes_meta) else {}
        headline = str(meta.get("visual_headline") or meta.get("section") or f"Step {idx + 1}").strip()
        badge = str(meta.get("badge") or meta.get("section") or f"STEP {idx + 1}").strip()
        callout = str(meta.get("on_screen_callout") or "").strip()
        bullets = [str(b).strip() for b in (meta.get("bullet_points") or []) if str(b).strip()][:3]

        scene_start = cursor
        concat_files.append(en_wav)

        # Word-timed captions for this English scene
        word_events = [t for t in (sr.word_timings or []) if t.get("type") == "WordBoundary" and t.get("text")]
        if word_events:
            words_timed = [
                {"w": str(we["text"]).strip(), "s": round(cursor + float(we["start"]) * scale, 3), "e": round(cursor + float(we["end"]) * scale, 3)}
                for we in word_events
            ]
        else:
            raw_words = sr.text.split()
            weights = [max(len(w), 3) + (4 if w.endswith((".", "!", "?")) else 2 if w.endswith((",", ";", "—")) else 0) for w in raw_words]
            tot_w = float(max(sum(weights), 1))
            wc = cursor
            words_timed = []
            for w, wt in zip(raw_words, weights):
                wd = s_dur * (wt / tot_w)
                words_timed.append({"w": w, "s": round(wc, 3), "e": round(wc + wd, 3)})
                wc += wd

        chunk_buf: list[dict[str, Any]] = []
        for wt in words_timed:
            chunk_buf.append(wt)
            ends_clause = wt["w"].endswith((".", "!", "?", "—", ";")) or (len(chunk_buf) >= 4 and wt["w"].endswith(","))
            if len(chunk_buf) >= 6 or ends_clause:
                captions.append({"start": chunk_buf[0]["s"], "end": max(chunk_buf[-1]["e"], chunk_buf[0]["s"] + 0.35), "words": chunk_buf})
                chunk_buf = []
        if chunk_buf:
            captions.append({"start": chunk_buf[0]["s"], "end": max(chunk_buf[-1]["e"], chunk_buf[0]["s"] + 0.35), "words": chunk_buf})

        cursor += s_dur

        if idx == insert_after_idx:
            # Close Scene 1 right as Arabic recitation begins
            scene_items.append({
                "idx": idx, "start": round(scene_start, 3), "end": round(cursor + pre_ar_pause, 3),
                "badge": badge, "headline": headline, "callout": callout, "bullets": bullets, "narration": sr.text.strip(),
            })
            concat_files.append(sil_pre_ar)
            cursor += pre_ar_pause

            ar_start = round(cursor, 3)
            concat_files.append(arabic_res.audio_path)
            cursor += ar_dur
            ar_end = round(cursor, 3)
            arabic_window = {
                "start": ar_start,
                "end": ar_end,
                "reciter": arabic_res.reciter_label,
                "is_qari": arabic_res.is_real_qari,
                "source": arabic_res.source,
            }

            concat_files.append(sil_post_ar)
            cursor += post_ar_pause
        else:
            concat_files.append(sil_scene)
            cursor += max(pause_sec, 0.15)
            scene_items.append({
                "idx": idx, "start": round(scene_start, 3), "end": round(cursor, 3),
                "badge": badge, "headline": headline, "callout": callout, "bullets": bullets, "narration": sr.text.strip(),
            })

    concat_txt = work_dir / "_bilingual_concat.txt"
    concat_txt.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in concat_files), encoding="utf-8")
    master_wav = work_dir / "master_bilingual_voice.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c:a", "pcm_s16le", str(master_wav)],
        capture_output=True, text=True, check=True,
    )
    return master_wav, scene_items, captions, arabic_window, probe_duration_sec(master_wav)


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

    # Render HTML5 Canvas at crisp 720p logical layout -> Lanczos upscale to 1080p!
    # In 2-vCPU GitHub Actions Cloud (HEADLESS_CLOUD=1), use adaptive render FPS (12fps Long / 16fps Short)
    # + device_scale_factor=0.75 (identical layout, 44% fewer pixels to rasterize -> ~4-5x faster so Cloud finishes in ~6m!).
    gl_w, gl_h = (720, 1280) if target_h >= target_w else (1280, 720)
    is_cloud = os.getenv("HEADLESS_CLOUD", "").strip() == "1"
    render_fps = (16 if is_short else 12) if is_cloud else 24
    out_fps = 30
    dsf = 0.75 if is_cloud else 1.0
    fps = render_fps
    safe_cap = min(max_short_sec - 0.8, 58.2) if is_short else 9999.0

    work_dir = out_video_path.parent / f"_v10_{mode}_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    dalil_payload = _resolve_dalil_payload(topic_meta=topic_meta, scenes_meta=scenes_meta)
    arabic_res = resolve_dalil_arabic_audio(dalil=dalil_payload, work_dir=work_dir, config=config, is_short=is_short)

    master_voice_wav, scene_items, captions, arabic_window, voice_dur = _assemble_bilingual_voice_and_timeline(
        scenes_meta=scenes_meta,
        audio_bundle=audio_bundle,
        arabic_res=arabic_res,
        pause_sec=pause_sec,
        work_dir=work_dir,
        is_short=is_short,
        safe_cap=safe_cap,
    )

    mixed_m4a = work_dir / f"mixed_{mode}.m4a"
    nature_preset = _nature_preset_for_mode(mode)
    mix_nature_voice_soundscape(
        master_voice=master_voice_wav,
        duration_sec=voice_dur,
        out_audio=mixed_m4a,
        config=config,
        preset=nature_preset,
        tempo=1.0,
    )
    final_dur = probe_duration_sec(mixed_m4a)
    if is_short and final_dur > 58.5:
        final_dur = 58.5

    rms_env = _extract_audio_rms_envelope(mixed_m4a, fps=fps, duration_sec=final_dur)

    story_acts = resolve_story_acts(topic_meta=topic_meta, scenes_meta=scenes_meta)
    render_payload: dict[str, Any] = {
        "mode": mode,
        "fps": fps,
        "total_dur": round(final_dur, 3),
        "dalil": dalil_payload,
        "story_acts": story_acts,
        "arabic_window": arabic_window,
        "scenes": scene_items,
        "captions": captions,
        "rms": rms_env,
    }
    html_doc = build_islamic_visual_html(mode=mode, payload=render_payload, width=gl_w, height=gl_h)
    total_frames = max(int(round(final_dur * fps)), fps)
    silent_mp4 = work_dir / f"video_{mode}_silent.mp4"

    print(
        f"[video] Rendering Studio v10 '{mode}' ({gl_w}x{gl_h} dsf={dsf} -> {target_w}x{target_h} "
        f"@ {render_fps}->{out_fps}fps, {final_dur:.1f}s, nature={nature_preset})...",
        flush=True,
    )
    ffmpeg_err_log = work_dir / f"ffmpeg_{mode}_err.log"
    cmd = [
        "ffmpeg", "-y", "-nostats", "-loglevel", "warning",
        "-f", "image2pipe", "-vcodec", "mjpeg", "-r", str(render_fps), "-i", "pipe:0",
        "-vf", (
            f"scale={target_w}:{target_h}:flags=lanczos:in_range=full:out_range=tv,"
            "setsar=1,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv,format=yuv420p"
        ),
        "-r", str(out_fps),
        "-c:v", "libx264", "-profile:v", "main", "-level:v", "4.0", "-preset", "veryfast", "-crf", "20",
        "-g", "60", "-keyint_min", "30", "-sc_threshold", "0",
        "-pix_fmt", "yuv420p", "-color_range", "tv",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-map_metadata", "-1", "-an",
        str(silent_mp4),
    ]
    import time as _time
    t_render0 = _time.perf_counter()
    with ffmpeg_err_log.open("wb") as err_fh:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=err_fh)
        assert proc.stdin is not None

        with sync_playwright() as pw:
            chrome = find_chrome_executable()
            launch_kw: dict[str, Any] = {
                "headless": True,
                "args": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"],
            }
            if chrome:
                launch_kw["executable_path"] = chrome
            br = pw.chromium.launch(**launch_kw)
            page = br.new_page(viewport={"width": gl_w, "height": gl_h}, device_scale_factor=dsf)
            page.set_content(html_doc, wait_until="load")
            # Ensure embedded Amiri Arabic calligraphy fonts finish loading before frame 0!
            page.evaluate("() => document.fonts.ready")

            jpg_q = 86 if is_cloud else 92
            try:
                for f_i in range(total_frames):
                    t = f_i / float(fps)
                    page.evaluate(f"window.renderAt({t:.4f})")
                    jpg_bytes = page.screenshot(type="jpeg", quality=jpg_q)
                    proc.stdin.write(jpg_bytes)
                    if f_i > 0 and f_i % 120 == 0:
                        el = max(_time.perf_counter() - t_render0, 0.01)
                        print(
                            f"[v10-{mode}] Rendered {f_i}/{total_frames} frames "
                            f"({100 * f_i / total_frames:.0f}%, {f_i / el:.1f} fps)...",
                            flush=True,
                        )
            finally:
                br.close()
                if proc.stdin and not proc.stdin.closed:
                    proc.stdin.close()

        ret = proc.wait()

    err = ffmpeg_err_log.read_text(encoding="utf-8", errors="ignore") if ffmpeg_err_log.exists() else ""
    if ret != 0:
        raise RuntimeError(f"FFmpeg v10 '{mode}' render failed ({ret}): {err[-300:]}")

    out_video_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(silent_mp4), "-i", str(mixed_m4a),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-map_metadata", "-1", "-movflags", "+faststart", "-shortest",
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
