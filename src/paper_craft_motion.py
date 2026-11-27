"""Studio v12 — True Multi-Layer 2.5D Paper-Cutout Motion Engine (`paper_craft_motion.py`).

Production Format 3 (`islamic_paper_craft`) engine for BOTH 9:16 (Shorts/Reels/TikTok) & 16:9 (YouTube Long).
Every object in every scene is a separate transparent studio-lit 3D paper-cutout PNG sprite
(`assets/papercraft_kit/*.png`) animated independently with:
  - Elastic spring-physics pop-up entrances (`springOut` overshoot!)
  - Continuous 360-degree spinning 3D golden paper sunburst (`sunburst_3d.png`)
  - Drifting multi-depth 3D paper clouds (`cloud_3d.png`)
  - Walking / step-bobbing faceless navy-kurta presenter (`presenter_point`, `presenter_scroll`, `presenter_dua`)
  - Live directional studio drop-shadows that move with each layer
  - Physical 3D Page-Curl peels, 3D Card Fold-Downs, and Layered Paper Slide-Cuts
  - Dynamic topic-driven popping 3D extruded paper-block titles & exact millisecond-synced Amiri Arabic calligraphy
  - 100% Offline & FREE (Rp 0) on GitHub Actions Cloud using bundled `assets/papercraft_kit/*.png`!
"""

from __future__ import annotations

import base64
import json
import subprocess
import time
from pathlib import Path
from typing import Any

from src.islamic_story_acts import STORY_ACTS_JS

_KIT_CACHE: dict[str, str] = {}
_DEFAULT_KIT_DIR = Path(__file__).resolve().parent.parent / "assets" / "papercraft_kit"


def _load_kit_data_uris(kit_dir: Path | None = None) -> dict[str, str]:
    target = (kit_dir or _DEFAULT_KIT_DIR).resolve()
    use_cache = target == _DEFAULT_KIT_DIR.resolve()
    if use_cache and _KIT_CACHE:
        return _KIT_CACHE
    out: dict[str, str] = {}
    if target.exists():
        for p in sorted(target.glob("*.png")):
            out[p.stem] = "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")
    if use_cache and out:
        _KIT_CACHE.update(out)
    return out


def build_paper_craft_25d_html(
    payload: dict[str, Any],
    font_css: str,
    width: int = 720,
    height: int = 1280,
    kit_dir: Path | None = None,
) -> str:
    """Build deterministic frame-by-frame Studio v12 Multi-Layer 2.5D Paper-Cutout Motion HTML5 engine.

    Supports BOTH 9:16 (720x1280 -> 1080x1920) AND 16:9 (1280x720 -> 1920x1080),
    dynamically driven by any episode's `scenes`, `story_acts`, and exact `arabic_window.word_timings`.
    """
    p = dict(payload)
    if not p.get("kit"):
        p["kit"] = _load_kit_data_uris(kit_dir)
    cfg_json = json.dumps(p, ensure_ascii=False)
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
    background: #A8D1DC;
    font-family: 'Segoe UI', 'Trebuchet MS', Arial, sans-serif;
    color: #1E2F42;
  }}
  #stageCanvas {{
    position: absolute; inset: 0; width: {width}px; height: {height}px; display: block;
  }}

  /* Diegetic Floating Cutout Kinetic Captions (NO heavy white bar — crisp paper cutout letters!) */
  .cap-float {{
    position: absolute; left: 28px; right: 28px;
    bottom: {52 if is_short else 22}px;
    z-index: 8; text-align: center; pointer-events: none;
  }}
  #capText {{
    display: inline-block; max-width: {650 if is_short else 1040}px;
    font-family: 'Segoe UI', 'Arial Black', sans-serif;
    font-size: {31 if is_short else 27}px; font-weight: 900; line-height: 1.24;
    color: #1D3146;
    -webkit-text-stroke: 6px #FAF6EB;
    paint-order: stroke fill;
    text-shadow: 0 4px 12px rgba(15, 28, 42, 0.32);
  }}
  #capText .hi {{
    color: #0F6B50;
    -webkit-text-stroke: 6px #FFF9E6;
  }}

  /* Sacred Arabic Plaque & Dome Calligraphic Overlays (embedded Amiri RTL!) */
  .dom-layer {{
    position: absolute; inset: 0; z-index: 6; pointer-events: none;
  }}
  .plaque-box {{
    position: absolute;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    text-align: center; opacity: 0;
  }}
  .plaque-ar {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; unicode-bidi: embed;
    font-weight: 700; line-height: 1.44; color: #1E2F42;
  }}
  .plaque-ar .arw {{ color: rgba(30, 47, 66, 0.34); }}
  .plaque-ar .arw.lit {{ color: #B4690E; text-shadow: 0 0 14px rgba(217, 154, 42, 0.42); }}
  .plaque-ar .arw.past {{ color: #1E2F42; }}
  .plaque-ar .arw-punct {{ color: #B47D22; opacity: 0.85; }}
  .plaque-tr {{
    font-family: 'Georgia', serif; font-weight: 700; font-style: italic;
    color: #3E5368; margin-top: 5px; line-height: 1.24;
  }}
  .plaque-rib {{
    margin-top: 10px; padding: 4px 16px; border-radius: 6px;
    background: #C9963A; color: #FFFDF7;
    font-family: 'Segoe UI', sans-serif; font-weight: 900;
    letter-spacing: 2px; text-transform: uppercase;
    box-shadow: 2px 5px 12px rgba(20, 32, 48, 0.25);
  }}

  .dome-box {{
    position: absolute;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    text-align: center; opacity: 0;
  }}
  .dome-kicker {{
    font-family: 'Segoe UI', sans-serif; font-weight: 900; letter-spacing: 2.2px;
    color: #0F766E; text-transform: uppercase; margin-bottom: 4px;
  }}
  .dome-allah {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; font-weight: 700; color: #1E2F42; line-height: 1.04;
    text-shadow: 1px 3px 0 rgba(235, 200, 118, 0.45), 0 6px 12px rgba(20,34,48,0.16);
  }}
  .dome-lead {{ font-family: 'Georgia', serif; font-weight: 700; color: #24394E; line-height: 1.24; }}
  .dome-gold {{ font-family: 'Georgia', serif; font-weight: 800; color: #B47D22; line-height: 1.22; }}

  .wm {{
    position: absolute; bottom: 14px; left: 20px; z-index: 9;
    font-size: 14px; font-weight: 800; letter-spacing: 0.8px;
    color: rgba(30, 47, 66, 0.72);
    -webkit-text-stroke: 3px rgba(247, 243, 230, 0.85);
    paint-order: stroke fill;
  }}
</style>
</head>
<body>
<canvas id="stageCanvas" width="{width}" height="{height}"></canvas>

<div class="dom-layer">
  <div class="plaque-box" id="plaqueBox">
    <div class="plaque-ar" id="plaqueAr"></div>
    <div class="plaque-tr" id="plaqueTr"></div>
    <div class="plaque-rib" id="plaqueRib"></div>
  </div>
  <div class="dome-box" id="domeBox">
    <div class="dome-kicker" id="domeKicker">✦ THE LESSON ✦</div>
    <div class="dome-lead" id="domeTop"></div>
    <div class="dome-allah" id="domeAllah">اللَّهُ</div>
    <div class="dome-lead" id="domeMid"></div>
    <div class="dome-gold" id="domeBot"></div>
  </div>
</div>

<div class="cap-float"><div id="capText"></div></div>
<div class="wm" id="wm"></div>

<script>
const CFG = {cfg_json};
const W = {width}, H = {height};
const IS_SHORT = H >= W;
const ctx = document.getElementById('stageCanvas').getContext('2d');
const STORY = CFG.story_acts || {{}};

{STORY_ACTS_JS}

const ACTS = computeFourActTiming(CFG);

// Build 6 dynamic paper-cutout slides automatically if caller did not pre-supply CFG.slides
function buildDynamicSlides() {{
  if (Array.isArray(CFG.slides) && CFG.slides.length >= 6) return CFG.slides;
  const arS = ACTS.arStart, arE = ACTS.arEnd, climS = ACTS.climaxStart, tot = ACTS.total;
  const expSpan = Math.max(climS - arE, 3.0);
  const e1 = arE + expSpan * 0.34;
  const e2 = arE + expSpan * 0.68;
  return [
    {{ idx: 0, start: 0.0,  end: arS,        transition: 'curl' }},
    {{ idx: 1, start: arS,  end: arE + 0.14, transition: 'curl' }},
    {{ idx: 2, start: arE + 0.14, end: e1,   transition: 'fold' }},
    {{ idx: 3, start: e1,   end: e2,         transition: 'slide' }},
    {{ idx: 4, start: e2,   end: climS,      transition: 'curl' }},
    {{ idx: 5, start: climS, end: tot + 0.5, transition: 'fold' }},
  ];
}}
const SLIDES = buildDynamicSlides();

// Dynamic 2-3 line cutout title generator from any scene headline or topic metadata
function splitPopTitle(rawText, fallbackLines) {{
  const clean = String(rawText || '').replace(/[^A-Za-z0-9'&\\-\\s]/g, ' ').replace(/\\s+/g, ' ').trim().toUpperCase();
  if (!clean) return fallbackLines;
  const words = clean.split(' ').filter(Boolean);
  if (words.length <= 3) return words;
  const lines = [];
  let cur = '';
  for (const w of words) {{
    if (lines.length >= 2) break;
    if (!cur) {{ cur = w; }}
    else if ((cur + ' ' + w).length <= 11) {{ cur += ' ' + w; }}
    else {{ lines.push(cur); cur = w; }}
  }}
  if (cur && lines.length < 3) lines.push(cur);
  return lines.length ? lines : fallbackLines;
}}

const scList = CFG.scenes || [];
const TITLE_S1 = splitPopTitle((scList[0] && scList[0].headline) || STORY.hook_kicker, ['THE', 'SUNNAH', 'RESET']);
const TITLE_S3 = splitPopTitle((scList[1] && scList[1].headline) || STORY.after_label, ['MIND', 'RESET']);
const TITLE_S4 = splitPopTitle((scList[2] && scList[2].headline) || STORY.stat_badge, ['CALM', 'CLARITY']);
const TITLE_S5 = splitPopTitle((scList[3] && scList[3].headline) || 'PEACE & BARAKAH', ['PEACE &', 'BARAKAH']);

// Split Core Lesson cleanly for Scene 6 Dome Medallion
function splitCoreLesson(lesson) {{
  const clean = String(lesson || 'peace, clarity & barakah').trim();
  const words = clean.split(/\\s+/).filter(Boolean);
  if (words.length <= 4) return ['bless your path with', clean];
  const half = Math.ceil(words.length / 2);
  return [words.slice(0, half).join(' '), words.slice(half).join(' ')];
}}
const [DOME_MID_AUTO, DOME_BOT_AUTO] = splitCoreLesson(STORY.core_lesson || CFG.dalil.translation);

document.getElementById('wm').textContent = CFG.dalil.handle || '@HabitSains';
document.getElementById('plaqueTr').textContent = CFG.dalil.transliteration;
document.getElementById('plaqueRib').textContent = CFG.dalil.citation;
document.getElementById('domeTop').textContent = CFG.finale_top || '';
document.getElementById('domeMid').textContent = CFG.finale_mid || DOME_MID_AUTO;
document.getElementById('domeBot').textContent = CFG.finale_bot || DOME_BOT_AUTO;

const AR_BUILT = buildArabicKaraokeHTML(CFG.dalil.arabic, 'arw', 'arw');
document.getElementById('plaqueAr').innerHTML = AR_BUILT.html;

// Preload all 11 transparent studio-lit 3D paper-cutout sprites
const SPRITES = {{}};
const kitEntries = Object.entries(CFG.kit || {{}});
window._assetsReady = Promise.all(kitEntries.map(([name, uri]) => new Promise((res) => {{
  const im = new Image();
  im.onload = () => {{ SPRITES[name] = im; res(); }};
  im.onerror = () => {{ SPRITES[name] = null; res(); }};
  im.src = uri;
}})));

// Offscreen subtle paper fiber grain pattern
const grainC = document.createElement('canvas');
grainC.width = 160; grainC.height = 160;
const gctx = grainC.getContext('2d');
for (let i = 0; i < 1600; i++) {{
  const gx = (i * 73) % 160, gy = (i * 137) % 160;
  gctx.fillStyle = (i % 2 === 0) ? 'rgba(255,255,255,0.045)' : 'rgba(20,45,62,0.032)';
  gctx.fillRect(gx, gy, 1.5, 1.5);
}}
const PAPER_GRAIN = ctx.createPattern(grainC, 'repeat');

const CONFETTI = [];
for (let i = 0; i < 28; i++) {{
  CONFETTI.push({{
    x: ((i * 157.3) % 1000) / 1000,
    y: ((i * 271.9) % 1000) / 1000,
    sz: 5 + (i % 4) * 2.5,
    sp: 0.04 + (i % 5) * 0.015,
    ph: i * 1.17,
    col: (i % 3 === 0) ? '#E2B44F' : ((i % 3 === 1) ? '#FAF6EA' : '#D5A23A'),
  }});
}}

function drawCardstockWall(t) {{
  const bg = ctx.createLinearGradient(0, 0, W * 0.4, H);
  bg.addColorStop(0, '#B4DAE4');
  bg.addColorStop(0.55, '#A6D0DC');
  bg.addColorStop(1, '#92C1CF');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, W, H);

  const lx = W * (0.18 + Math.sin(t * 0.25) * 0.05);
  const ly = H * 0.14;
  const keyG = ctx.createRadialGradient(lx, ly, 20, lx, ly, Math.max(W, H) * 0.85);
  keyG.addColorStop(0, 'rgba(255, 253, 245, 0.26)');
  keyG.addColorStop(1, 'rgba(255, 253, 245, 0)');
  ctx.fillStyle = keyG;
  ctx.fillRect(0, 0, W, H);

  if (PAPER_GRAIN) {{
    ctx.fillStyle = PAPER_GRAIN;
    ctx.fillRect(0, 0, W, H);
  }}
}}

function drawTableFloor(floorY) {{
  const fg = ctx.createLinearGradient(0, floorY, 0, H);
  fg.addColorStop(0, '#96C3D0');
  fg.addColorStop(1, '#82B3C2');
  ctx.fillStyle = fg;
  ctx.fillRect(0, floorY, W, H - floorY);
  ctx.fillStyle = 'rgba(25, 48, 66, 0.12)';
  ctx.fillRect(0, floorY, W, 2);
}}

function drawSprite(name, cx, cy, targetW, opts = {{}}) {{
  const im = SPRITES[name];
  if (!im) return;
  const aspect = im.height / im.width;
  const drawW = targetW;
  const drawH = targetW * aspect;
  const scX = (opts.scaleX !== undefined ? opts.scaleX : 1) * (opts.scale !== undefined ? opts.scale : 1);
  const scY = (opts.scaleY !== undefined ? opts.scaleY : 1) * (opts.scale !== undefined ? opts.scale : 1);
  if (Math.abs(scX) < 0.005 || Math.abs(scY) < 0.005) return;

  ctx.save();
  ctx.globalAlpha = opts.alpha !== undefined ? opts.alpha : 1.0;
  ctx.translate(cx, cy);
  if (opts.rot) ctx.rotate(opts.rot);
  if (opts.skewX) ctx.transform(1, 0, opts.skewX, 1, 0, 0);
  ctx.scale(scX, scY);

  if (opts.shadow !== false) {{
    ctx.shadowColor = opts.shadowColor || 'rgba(18, 36, 52, 0.30)';
    ctx.shadowBlur = opts.shadowBlur !== undefined ? opts.shadowBlur : 22;
    ctx.shadowOffsetX = opts.shadowX !== undefined ? opts.shadowX : 10;
    ctx.shadowOffsetY = opts.shadowY !== undefined ? opts.shadowY : 16;
  }}

  const pivX = opts.pivotX !== undefined ? opts.pivotX : 0.5;
  const pivY = opts.pivotY !== undefined ? opts.pivotY : 0.5;
  ctx.drawImage(im, -drawW * pivX, -drawH * pivY, drawW, drawH);
  ctx.restore();
}}

function drawAnimatedPresenter(name, startX, endX, footY, widthPx, localT, t, enterDelay = 0.25, enterDur = 1.05) {{
  const rawU = clamp01((localT - enterDelay) / enterDur);
  if (rawU <= 0) return;
  const moveU = easeOutCubic(rawU);
  const x = startX + (endX - startX) * moveU;
  const isWalking = rawU < 0.99;
  const walkFade = 1 - Math.pow(rawU, 3);
  const stepHop = isWalking ? Math.abs(Math.sin(rawU * Math.PI * 4)) * 18 * walkFade : 0;
  const walkLean = isWalking ? Math.sin(rawU * Math.PI * 4) * 0.048 * walkFade : 0;
  const breatheY = 1 + Math.sin(t * 2.4) * 0.012;
  const idleSway = Math.sin(t * 1.45) * 0.016 * (1 - walkFade);

  ctx.save();
  ctx.fillStyle = 'rgba(18, 38, 54, 0.22)';
  ctx.beginPath();
  ctx.ellipse(x + 4, footY - 4, widthPx * 0.38 * (1 - stepHop / 140), 10, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  drawSprite(name, x, footY - stepHop, widthPx, {{
    pivotX: 0.5, pivotY: 1.0,
    scaleY: breatheY,
    rot: walkLean + idleSway,
    shadowX: 10, shadowY: 14, shadowBlur: 18,
  }});
}}

function drawPoppingPaperTitle(words, x, y, fontSize, align, localT, startDelay = 0.40) {{
  ctx.save();
  ctx.font = `900 ${{fontSize}}px 'Arial Black', 'Segoe UI', Impact, sans-serif`;
  ctx.textBaseline = 'top';
  ctx.textAlign = align || 'center';
  const lineH = fontSize * 1.05;

  words.forEach((word, i) => {{
    const u = clamp01((localT - (startDelay + i * 0.14)) / 0.40);
    if (u <= 0) return;
    const sc = springOut(u);
    const wy = y + i * lineH;

    ctx.save();
    ctx.translate(x, wy + lineH * 0.45);
    ctx.scale(sc, sc);
    ctx.translate(0, -lineH * 0.45);

    ctx.shadowColor = 'rgba(15, 28, 42, 0.34)';
    ctx.shadowBlur = 16; ctx.shadowOffsetX = 5; ctx.shadowOffsetY = 12;
    ctx.lineJoin = 'round';
    ctx.lineWidth = Math.round(fontSize * 0.19);
    ctx.strokeStyle = '#F7F3E6';
    ctx.strokeText(word, 0, 0);

    ctx.shadowColor = 'transparent';
    ctx.fillStyle = '#CFC7B4';
    ctx.fillText(word, 0, 4);

    ctx.fillStyle = '#1E3348';
    ctx.fillText(word, 0, 0);
    ctx.restore();
  }});
  ctx.restore();
}}

function drawDriftingClouds(t, bands) {{
  for (const b of bands) {{
    const span = W + 240;
    const cx = (((b.x0 * W + t * b.speed) % span) + span) % span - 120;
    const cy = b.y * H + Math.sin(t * 0.9 + b.x0 * 7) * 5;
    drawSprite('cloud_3d', cx, cy, b.w, {{
      alpha: b.alpha || 0.96,
      shadowX: 6, shadowY: 12, shadowBlur: 16, shadowColor: 'rgba(18, 36, 52, 0.22)',
    }});
  }}
}}

function drawFloatingConfetti(t, alpha = 1.0) {{
  ctx.save();
  ctx.globalAlpha = alpha;
  for (const c of CONFETTI) {{
    const cx = c.x * W + Math.sin(t * 1.1 + c.ph) * 16;
    const cy = (((c.y - t * c.sp) % 1) + 1) % 1 * H;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(t * 1.6 + c.ph);
    ctx.scale(Math.cos(t * 2.2 + c.ph) * 0.5 + 0.55, 1);
    ctx.fillStyle = c.col;
    ctx.beginPath();
    ctx.moveTo(0, -c.sz); ctx.lineTo(c.sz * 0.65, 0);
    ctx.lineTo(0, c.sz); ctx.lineTo(-c.sz * 0.65, 0);
    ctx.closePath(); ctx.fill();
    ctx.restore();
  }}
  ctx.restore();
}}

function drawCalendarDatesOnSprite(calCx, calCy, calW, calH, rot, sc, localT, t) {{
  const gridAlpha = easeOutCubic(clamp01((localT - 0.52) / 0.42));
  if (gridAlpha <= 0.01) return;
  ctx.save();
  ctx.translate(calCx, calCy);
  ctx.rotate(rot);
  ctx.scale(sc, sc);
  ctx.globalAlpha = gridAlpha;

  const gx = -calW * 0.42, gy = -calH * 0.17;
  const gw = calW * 0.84, gh = calH * 0.54;
  const days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
  const colW = gw / 7;
  const isMonThu = String(CFG.dalil.badge_num || '').toUpperCase().includes('MON');
  ctx.font = `800 ${{Math.round(calW * 0.036)}}px 'Segoe UI', sans-serif`;
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  for (let c = 0; c < 7; c++) {{
    const hiCol = isMonThu ? (c === 1 || c === 4) : (c === 5);
    ctx.fillStyle = hiCol ? '#B45309' : '#475569';
    ctx.fillText(days[c], gx + (c + 0.5) * colW, gy + gh * 0.06);
  }}
  ctx.font = `800 ${{Math.round(calW * 0.050)}}px 'Segoe UI', sans-serif`;
  let d = 1;
  for (let r = 0; r < 5; r++) {{
    const rowPop = easeOutCubic(clamp01((localT - (0.62 + r * 0.10)) / 0.28));
    if (rowPop <= 0.01) continue;
    ctx.globalAlpha = gridAlpha * rowPop;
    for (let c = 0; c < 7; c++) {{
      if (r === 0 && c < 2) continue;
      if (d > 30) break;
      const dx = gx + (c + 0.5) * colW;
      const dy = gy + gh * (0.24 + r * 0.175);
      const hiCol = isMonThu ? (c === 1 || c === 4) : (c === 5);
      if (hiCol) {{
        const pulse = 1 + Math.sin(t * 5.0 + r) * 0.10;
        ctx.fillStyle = 'rgba(229, 178, 66, 0.38)';
        ctx.beginPath(); ctx.arc(dx, dy, colW * 0.39 * pulse, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#92400E';
      }} else {{
        ctx.fillStyle = '#1E2F42';
      }}
      ctx.fillText(String(d), dx, dy);
      d++;
    }}
  }}
  ctx.restore();
}}

function drawPageCurlWipe(p, snapCanvas) {{
  if (p >= 0.995) return;
  const e = easeInOutQuad(p);
  const diagMax = W + H;
  const kVal = diagMax * (1.02 - e * 1.18);

  ctx.save();
  const shOff = 18 + Math.sin(e * Math.PI) * 28;
  ctx.strokeStyle = `rgba(15, 28, 42, ${{0.30 * Math.sin(Math.min(e * 1.15, 1) * Math.PI)}})`;
  ctx.lineWidth = 44;
  ctx.beginPath(); ctx.moveTo(kVal - H + shOff, H + shOff); ctx.lineTo(kVal + shOff, shOff); ctx.stroke();
  ctx.restore();

  ctx.save();
  ctx.beginPath(); ctx.moveTo(-10, -10); ctx.lineTo(kVal, -10); ctx.lineTo(-10, kVal); ctx.closePath(); ctx.clip();
  if (snapCanvas) {{
    ctx.drawImage(snapCanvas, 0, 0);
  }} else {{
    const g = ctx.createLinearGradient(0, 0, W, H);
    g.addColorStop(0, '#A5CFD9'); g.addColorStop(0.55, '#B2D7E1'); g.addColorStop(1, '#98C4D1');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }}
  ctx.restore();

  if (e > 0.01 && e < 0.96) {{
    const curlW = Math.min(Math.min(W, H) * 0.44, (diagMax - kVal) * 0.48 + 38);
    const p1x = Math.min(W, kVal), p1y = Math.max(0, kVal - W);
    const p2x = Math.max(0, kVal - H), p2y = Math.min(H, kVal);
    const mx = (p1x + p2x) * 0.5, my = (p1y + p2y) * 0.5;
    const tipX = mx - curlW * 0.72, tipY = my - curlW * 0.72;
    ctx.save();
    ctx.shadowColor = 'rgba(15, 28, 42, 0.34)'; ctx.shadowBlur = 24;
    ctx.shadowOffsetX = -6; ctx.shadowOffsetY = -6;
    const backG = ctx.createLinearGradient(mx, my, tipX, tipY);
    backG.addColorStop(0, '#D7D0BE'); backG.addColorStop(0.35, '#FAF7EE');
    backG.addColorStop(0.75, '#F0EAD8'); backG.addColorStop(1, '#CFC6B2');
    ctx.fillStyle = backG;
    ctx.beginPath();
    ctx.moveTo(p1x, p1y);
    ctx.quadraticCurveTo(p1x - curlW * 0.55, p1y - curlW * 0.12, tipX, tipY);
    ctx.quadraticCurveTo(p2x - curlW * 0.12, p2y - curlW * 0.55, p2x, p2y);
    ctx.closePath(); ctx.fill();
    ctx.restore();
  }}
}}

function drawCardFoldWipe(p, snapCanvas) {{
  if (p >= 0.995 || !snapCanvas) return;
  const e = easeInOutQuad(p);
  const scaleY = Math.max(Math.cos(e * Math.PI * 0.5), 0.001);
  ctx.fillStyle = `rgba(15, 28, 42, ${{0.34 * (1 - e)}})`;
  ctx.fillRect(0, H * scaleY, W, 38 * (1 - e) + 8);
  ctx.save();
  ctx.scale(1, scaleY);
  ctx.drawImage(snapCanvas, 0, 0);
  ctx.fillStyle = `rgba(16, 28, 44, ${{e * 0.36}})`;
  ctx.fillRect(0, 0, W, H);
  ctx.restore();
}}

const prevSnap = document.createElement('canvas');
prevSnap.width = W; prevSnap.height = H;
const prevCtx = prevSnap.getContext('2d');
let lastSceneIdx = -1;

// Responsive unit U (720 for both 720x1280 and 1280x720!)
const U = Math.min(W, H);

function renderSceneContent(idx, localT, dur, t) {{
  drawCardstockWall(t);
  const plaqueBox = document.getElementById('plaqueBox');
  const domeBox = document.getElementById('domeBox');
  plaqueBox.style.opacity = '0';
  domeBox.style.opacity = '0';

  if (idx === 0) {{
    // ===== SCENE 1: HOOK — SPINNING SUNBURST + POP-UP CALENDAR + WALKING PRESENTER =====
    drawTableFloor(H * (IS_SHORT ? 0.87 : 0.86));
    drawDriftingClouds(t, [
      {{ x0: 0.08, y: IS_SHORT ? 0.28 : 0.22, w: U * 0.18, speed: 14 }},
      {{ x0: 0.72, y: IS_SHORT ? 0.34 : 0.26, w: U * 0.15, speed: 10 }},
    ]);

    const sunPop = springOut(clamp01((localT - 0.15) / 0.65));
    drawSprite('sunburst_3d', W * (IS_SHORT ? 0.84 : 0.88), H * (IS_SHORT ? 0.10 : 0.16), U * (IS_SHORT ? 0.66 : 0.46), {{
      scale: sunPop, rot: t * 0.24, shadowX: 8, shadowY: 14, shadowBlur: 20,
    }});

    const calU = clamp01((localT - 0.28) / 0.65);
    const calSc = springOut(calU);
    const calY = H * (IS_SHORT ? 0.54 : 0.50) + (1 - easeOutCubic(calU)) * 220;
    const calX = W * (IS_SHORT ? 0.68 : 0.69);
    const calRot = Math.sin(t * 1.4) * 0.022;
    const calW = U * (IS_SHORT ? 0.49 : 0.44);
    const calIm = SPRITES['calendar_3d'];
    const calH = calIm ? calW * (calIm.height / calIm.width) : calW * 1.2;
    drawSprite('calendar_3d', calX, calY, calW, {{
      scale: calSc, rot: calRot, shadowX: 12, shadowY: 20, shadowBlur: 24,
    }});
    drawCalendarDatesOnSprite(calX, calY, calW, calH, calRot, calSc, localT, t);

    drawAnimatedPresenter(
      'presenter_point', -190, W * (IS_SHORT ? 0.24 : 0.36), H * 0.90,
      U * (IS_SHORT ? 0.38 : 0.26), localT, t, 0.35, 1.00
    );

    drawPoppingPaperTitle(
      TITLE_S1, W * (IS_SHORT ? 0.07 : 0.045), H * (IS_SHORT ? 0.08 : 0.14),
      Math.round(U * (IS_SHORT ? 0.100 : 0.072)), 'left', localT, 0.45
    );

  }} else if (idx === 1) {{
    // ===== SCENE 2: DALIL — UNFOLDING ISLAMIC PLAQUE + EXACT ARABIC WORD KARAOKE + SCROLL PRESENTER =====
    drawTableFloor(H * 0.88);
    drawDriftingClouds(t, [
      {{ x0: 0.10, y: 0.18, w: U * 0.20, speed: 15 }},
      {{ x0: 0.78, y: 0.22, w: U * 0.19, speed: -12 }},
      {{ x0: 0.84, y: 0.52, w: U * 0.17, speed: 11 }},
    ]);

    const sunSc = springOut(clamp01((localT - 0.15) / 0.60));
    drawSprite('sunburst_3d', W * (IS_SHORT ? 0.72 : 0.68), H * (IS_SHORT ? 0.17 : 0.22), U * (IS_SHORT ? 0.42 : 0.34), {{
      scale: sunSc, rot: t * 0.22,
    }});

    const pU = clamp01((localT - 0.10) / 0.55);
    const pSc = springOut(pU);
    const pHover = Math.sin(t * 1.8) * 5;
    const pCx = W * (IS_SHORT ? 0.54 : 0.55);
    const pCy = H * (IS_SHORT ? 0.36 : 0.44) + pHover;
    const pW = U * (IS_SHORT ? 0.68 : 0.58);
    drawSprite('plaque_islamic', pCx, pCy, pW, {{
      scaleX: pSc, scaleY: easeOutCubic(pU),
      shadowX: 14, shadowY: 22, shadowBlur: 28,
    }});

    drawAnimatedPresenter(
      'presenter_scroll', -160, W * (IS_SHORT ? 0.22 : 0.20), H * 0.90,
      U * (IS_SHORT ? 0.31 : 0.26), localT, t, 0.22, 0.92
    );

    const textA = easeOutCubic(clamp01((localT - 0.42) / 0.35));
    const boxW = pW * 0.59;
    const boxH = pW * 0.74;
    plaqueBox.style.opacity = String(textA);
    plaqueBox.style.left = (pCx - boxW * 0.5) + 'px';
    plaqueBox.style.top = (pCy - boxH * 0.37) + 'px';
    plaqueBox.style.width = boxW + 'px';
    plaqueBox.style.height = boxH + 'px';
    const arScale = AR_BUILT.count > 9 ? 0.032 : (AR_BUILT.count > 6 ? 0.038 : 0.044);
    document.getElementById('plaqueAr').style.fontSize = Math.round(U * arScale) + 'px';
    document.getElementById('plaqueTr').style.fontSize = Math.round(U * 0.017) + 'px';
    document.getElementById('plaqueRib').style.fontSize = Math.round(U * 0.015) + 'px';

    const arProg = clamp01(localT / Math.max(dur, 0.5));
    updateArabicKaraokeAt(t, CFG.arabic_window, AR_BUILT.count, 'arw', 'arw', arProg);

  }} else if (idx === 2) {{
    // ===== SCENE 3: EXPLAINER A — RISING SPINNING SUN BEHIND POP-UP 3D LAYERED HILLS =====
    drawDriftingClouds(t, [
      {{ x0: 0.05, y: 0.30, w: U * 0.21, speed: 18 }},
      {{ x0: 0.78, y: 0.25, w: U * 0.18, speed: 13 }},
    ]);

    const riseU = easeOutCubic(clamp01((localT - 0.10) / 1.35));
    const sunY = H * (IS_SHORT ? (0.76 - riseU * 0.25) : (0.80 - riseU * 0.30));
    const halo = ctx.createRadialGradient(W * 0.62, sunY, 20, W * 0.62, sunY, U * 0.58);
    halo.addColorStop(0, `rgba(255, 232, 148, ${{0.42 * riseU}})`);
    halo.addColorStop(1, 'rgba(255, 232, 148, 0)');
    ctx.fillStyle = halo; ctx.fillRect(0, 0, W, H);
    drawSprite('sunburst_3d', W * 0.62, sunY, U * (IS_SHORT ? 0.62 : 0.48), {{
      rot: t * 0.20, shadowX: 6, shadowY: 12, shadowBlur: 18,
    }});

    const hillU = clamp01(localT / 0.70);
    const hillY = H + (1 - springOut(hillU)) * 320 + Math.sin(t * 1.1) * 4;
    const hillW = IS_SHORT ? W * 1.04 : Math.min(W * 0.78, U * 1.35);
    drawSprite('sunrise_hills_fg', W * 0.5, hillY + 12, hillW, {{
      pivotX: 0.5, pivotY: 1.0,
      shadowX: 0, shadowY: -6, shadowBlur: 18, shadowColor: 'rgba(15, 38, 28, 0.22)',
    }});

    drawPoppingPaperTitle(
      TITLE_S3, W * 0.5, H * (IS_SHORT ? 0.08 : 0.06),
      Math.round(U * (IS_SHORT ? 0.102 : 0.080)), 'center', localT, 0.30
    );

  }} else if (idx === 3) {{
    // ===== SCENE 4: EXPLAINER B — OPEN 3D POP-UP BOOK + ERUPTING SUNBURST + LIVE CLARITY COUNTER =====
    drawTableFloor(H * 0.85);
    drawFloatingConfetti(t, easeOutCubic(clamp01((localT - 0.35) / 0.5)));
    drawDriftingClouds(t, [
      {{ x0: 0.12, y: 0.24, w: U * 0.17, speed: 12 }},
      {{ x0: 0.76, y: 0.20, w: U * 0.15, speed: -10 }},
    ]);

    const eruptU = clamp01((localT - 0.28) / 0.82);
    const eruptSc = springOut(eruptU);
    const sunX = W * (IS_SHORT ? 0.54 : 0.55);
    const sunY = H * (IS_SHORT ? 0.49 : 0.45) + (1 - easeOutCubic(eruptU)) * 200;
    const sunW = U * (IS_SHORT ? 0.62 : 0.46);
    drawSprite('sunburst_3d', sunX, sunY, sunW, {{
      scale: eruptSc, rot: t * 0.30, shadowX: 10, shadowY: 16, shadowBlur: 22,
    }});

    if (eruptU > 0.15) {{
      const pct = Math.round(24 + easeOutCubic(clamp01((localT - 0.45) / 2.4)) * 71);
      ctx.save();
      ctx.translate(sunX, sunY);
      ctx.scale(eruptSc, eruptSc);
      ctx.fillStyle = '#F7F3E6';
      ctx.beginPath(); ctx.arc(0, 0, sunW * 0.235, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#1E3348';
      ctx.font = `900 ${{Math.round(sunW * 0.11)}}px 'Arial Black', sans-serif`;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(pct + '%', 0, -8);
      ctx.fillStyle = '#B47D22';
      ctx.font = `800 ${{Math.round(sunW * 0.042)}}px 'Segoe UI', sans-serif`;
      ctx.fillText('CLARITY', 0, 22);
      ctx.restore();
    }}

    const bkU = clamp01(localT / 0.62);
    const bkY = H * (IS_SHORT ? 0.86 : 0.90) + (1 - springOut(bkU)) * 260;
    drawSprite('open_book_3d', sunX, bkY, U * (IS_SHORT ? 0.96 : 0.72), {{
      pivotX: 0.5, pivotY: 1.0,
      scaleY: 0.65 + 0.35 * springOut(bkU),
      shadowX: 8, shadowY: 18, shadowBlur: 24,
    }});

    drawAnimatedPresenter(
      'presenter_point', -190, W * (IS_SHORT ? 0.22 : 0.20), H * 0.90,
      U * (IS_SHORT ? 0.36 : 0.27), localT, t, 0.32, 0.92
    );

    drawPoppingPaperTitle(
      TITLE_S4, W * (IS_SHORT ? 0.50 : 0.22), H * (IS_SHORT ? 0.06 : 0.10),
      Math.round(U * (IS_SHORT ? 0.092 : 0.074)), IS_SHORT ? 'center' : 'left', localT, 0.28
    );

  }} else if (idx === 4) {{
    // ===== SCENE 5: EXPLAINER C — 3D GARDEN ARCHWAY POP-UP + DOLLY-IN + WALKING PRESENTER =====
    drawDriftingClouds(t, [
      {{ x0: 0.14, y: 0.23, w: U * 0.19, speed: 15 }},
      {{ x0: 0.72, y: 0.27, w: U * 0.17, speed: -11 }},
    ]);

    drawSprite('sunburst_3d', W * 0.50, H * 0.56, U * 0.36, {{
      rot: t * 0.14, alpha: 0.45, shadow: false,
    }});

    const archU = clamp01(localT / 0.68);
    const archZoom = 1.0 + clamp01(localT / Math.max(dur, 1)) * 0.06;
    const archY = H + (1 - springOut(archU)) * 320;
    const archW = (IS_SHORT ? W * 1.04 : U * 1.08) * archZoom;
    drawSprite('garden_arch_fg', W * 0.5, archY + 14, archW, {{
      pivotX: 0.5, pivotY: 1.0, shadowX: 0, shadowY: -6, shadowBlur: 18,
    }});

    drawAnimatedPresenter(
      'presenter_point', -180, W * (IS_SHORT ? 0.23 : 0.22), H * 0.91,
      U * (IS_SHORT ? 0.35 : 0.27), localT, t, 0.36, 0.95
    );
    drawFloatingConfetti(t, 0.55);

    drawPoppingPaperTitle(
      TITLE_S5, W * 0.5, H * (IS_SHORT ? 0.07 : 0.05),
      Math.round(U * (IS_SHORT ? 0.098 : 0.076)), 'center', localT, 0.28
    );

  }} else {{
    // ===== SCENE 6: CLIMAX — BLOOMING GOLDEN ISLAMIC DOME + CORE LESSON + WALKING DUA PRESENTER =====
    drawTableFloor(H * 0.88);
    drawDriftingClouds(t, [
      {{ x0: 0.08, y: 0.14, w: U * 0.18, speed: 11 }},
      {{ x0: 0.78, y: 0.18, w: U * 0.16, speed: -9 }},
    ]);
    drawFloatingConfetti(t, 0.80);

    const dU = clamp01((localT - 0.10) / 0.72);
    const dSc = springOut(dU) * (1 + Math.sin(t * 1.7) * 0.015);
    const dRot = Math.sin(t * 1.1) * 0.016;
    const dCx = W * (IS_SHORT ? 0.45 : 0.44);
    const dCy = H * (IS_SHORT ? 0.44 : 0.46);
    const dW = U * (IS_SHORT ? 0.84 : 0.68);
    drawSprite('dome_medallion_3d', dCx, dCy, dW, {{
      scale: dSc, rot: dRot, shadowX: 12, shadowY: 20, shadowBlur: 26,
    }});

    drawAnimatedPresenter(
      'presenter_dua', W + 180, W * (IS_SHORT ? 0.78 : 0.76), H * 0.90,
      U * (IS_SHORT ? 0.34 : 0.27), localT, t, 0.28, 1.00
    );

    const aAll = easeOutCubic(clamp01((localT - 0.40) / 0.42));
    const dbW = dW * 0.60;
    const dbH = dW * 0.58;
    domeBox.style.opacity = String(aAll);
    domeBox.style.left = (dCx - dbW * 0.5) + 'px';
    domeBox.style.top = (dCy - dbH * 0.46) + 'px';
    domeBox.style.width = dbW + 'px';
    domeBox.style.height = dbH + 'px';
    document.getElementById('domeKicker').style.fontSize = Math.round(dW * 0.022) + 'px';
    document.getElementById('domeTop').style.fontSize = Math.round(dW * 0.032) + 'px';
    document.getElementById('domeAllah').style.fontSize = Math.round(dW * 0.115) + 'px';
    document.getElementById('domeMid').style.fontSize = Math.round(dW * 0.030) + 'px';
    document.getElementById('domeBot').style.fontSize = Math.round(dW * 0.032) + 'px';
    document.getElementById('domeTop').style.opacity = String(easeOutCubic(clamp01((localT - 0.45) / 0.35)));
    document.getElementById('domeAllah').style.opacity = String(easeOutCubic(clamp01((localT - 0.68) / 0.38)));
    document.getElementById('domeMid').style.opacity = String(easeOutCubic(clamp01((localT - 0.98) / 0.38)));
    document.getElementById('domeBot').style.opacity = String(easeOutCubic(clamp01((localT - 1.28) / 0.42)));
  }}
}}

window.renderAt = function(t) {{
  let curIdx = SLIDES.length - 1;
  for (let i = 0; i < SLIDES.length; i++) {{
    if (t >= SLIDES[i].start && t < SLIDES[i].end) {{ curIdx = i; break; }}
  }}
  const sl = SLIDES[curIdx];
  const localT = Math.max(t - sl.start, 0);
  const dur = Math.max(sl.end - sl.start, 1.0);

  if (curIdx !== lastSceneIdx && lastSceneIdx >= 0) {{
    prevCtx.clearRect(0, 0, W, H);
    prevCtx.drawImage(document.getElementById('stageCanvas'), 0, 0);
  }}
  lastSceneIdx = curIdx;

  renderSceneContent(curIdx, localT, dur, t);

  const transDur = (curIdx === 0) ? 0.95 : 0.65;
  if (localT < transDur) {{
    const tp = localT / transDur;
    if (curIdx === 0) {{
      drawPageCurlWipe(tp, null);
    }} else if (sl.transition === 'curl') {{
      drawPageCurlWipe(tp, prevSnap);
    }} else if (sl.transition === 'fold') {{
      drawCardFoldWipe(tp, prevSnap);
    }} else {{
      const e = easeInOutQuad(tp);
      ctx.save();
      ctx.shadowColor = 'rgba(15, 28, 42, 0.36)'; ctx.shadowBlur = 24; ctx.shadowOffsetX = 12;
      ctx.drawImage(prevSnap, -W * e, 0);
      ctx.restore();
    }}
  }}

  const act = getCurrentAct(t, ACTS);
  const inArabic = (act.name === 'DALIL');
  let cap = null;
  for (const c of (CFG.captions || [])) {{
    if (t >= c.start - 0.06 && t <= c.end + 0.14) {{ cap = c; break; }}
  }}
  const capEl = document.getElementById('capText');
  if (inArabic) {{
    capEl.innerHTML = `<span class="hi" style="font-style:italic">"${{CFG.dalil.translation}}"</span>`;
  }} else if (cap && cap.words && cap.words.length) {{
    capEl.innerHTML = cap.words.map(w => {{
      const isSpoken = t >= w.s && t <= w.e + 0.12;
      return isSpoken ? `<span class="hi">${{w.w}}</span>` : w.w;
    }}).join(' ');
  }} else {{
    capEl.textContent = '';
  }}
}};
</script>
</body>
</html>"""


def build_papercraft_25d_motion_html(payload: dict[str, Any], width: int = 720, height: int = 1280) -> str:
    """Backward-compatible wrapper that auto-loads embedded Amiri calligraphy CSS."""
    from src.islamic_visual_engine import _load_amiri_font_css

    return build_paper_craft_25d_html(payload, _load_amiri_font_css(), width=width, height=height)


def render_papercraft_25d_motion_video(
    scenes_meta: list[dict[str, Any]],
    audio_bundle: Any,
    out_video_path: Path,
    config: dict[str, Any],
    topic_meta: dict[str, Any],
    kit_dir: Path | None = None,
    finale_lines: tuple[str, str, str] | None = None,
) -> Path:
    """Standalone helper to render 1080x1920 30fps Studio v12 2.5D Paper-Cutout Motion MP4."""
    from playwright.sync_api import sync_playwright

    from src.arabic_audio import resolve_dalil_arabic_audio
    from src.html_motion_overlay import find_chrome_executable
    from src.islamic_story_acts import resolve_story_acts
    from src.islamic_visual_engine import (
        _assemble_bilingual_voice_and_timeline,
        _load_amiri_font_css,
        _resolve_dalil_payload,
    )
    from src.sfx_engine import mix_nature_voice_soundscape
    from src.voiceover import probe_duration_sec

    work_dir = out_video_path.parent / "_v12_papercraft_25d_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    dalil_payload = _resolve_dalil_payload(topic_meta=topic_meta, scenes_meta=scenes_meta)
    arabic_res = resolve_dalil_arabic_audio(dalil=dalil_payload, work_dir=work_dir, config=config, is_short=True)

    master_voice_wav, scene_items, captions, arabic_window, voice_dur = _assemble_bilingual_voice_and_timeline(
        scenes_meta=scenes_meta,
        audio_bundle=audio_bundle,
        arabic_res=arabic_res,
        pause_sec=0.26,
        work_dir=work_dir,
        is_short=True,
        safe_cap=58.0,
    )

    mixed_m4a = work_dir / "mixed_papercraft_25d.m4a"
    mix_nature_voice_soundscape(
        master_voice=master_voice_wav,
        duration_sec=voice_dur,
        out_audio=mixed_m4a,
        config=config,
        preset="dawn_breeze",
        tempo=1.0,
    )
    final_dur = probe_duration_sec(mixed_m4a)

    render_fps = 24
    out_fps = 30
    gl_w, gl_h = 720, 1280
    payload: dict[str, Any] = {
        "fps": render_fps,
        "total_dur": round(final_dur, 3),
        "dalil": dalil_payload,
        "story_acts": resolve_story_acts(topic_meta=topic_meta, scenes_meta=scenes_meta),
        "arabic_window": arabic_window,
        "scenes": scene_items,
        "captions": captions,
        "kit": _load_kit_data_uris(kit_dir),
    }
    if finale_lines:
        payload["finale_top"], payload["finale_mid"], payload["finale_bot"] = finale_lines

    html_doc = build_paper_craft_25d_html(payload, _load_amiri_font_css(), width=gl_w, height=gl_h, kit_dir=kit_dir)
    total_frames = max(int(round(final_dur * render_fps)), render_fps)
    silent_mp4 = work_dir / "papercraft_25d_silent.mp4"
    err_log = work_dir / "ffmpeg_err.log"

    cmd = [
        "ffmpeg", "-y", "-nostats", "-loglevel", "warning",
        "-f", "image2pipe", "-vcodec", "mjpeg", "-r", str(render_fps), "-i", "pipe:0",
        "-vf", "scale=1080:1920:flags=lanczos:in_range=full:out_range=tv,setsar=1,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv,format=yuv420p",
        "-r", str(out_fps),
        "-c:v", "libx264", "-profile:v", "main", "-level:v", "4.0", "-preset", "veryfast", "-crf", "19",
        "-g", "60", "-keyint_min", "30", "-sc_threshold", "0",
        "-pix_fmt", "yuv420p", "-color_range", "tv",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-map_metadata", "-1", "-an",
        str(silent_mp4),
    ]
    t0 = time.perf_counter()
    with err_log.open("wb") as err_fh:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=err_fh)
        assert proc.stdin is not None
        with sync_playwright() as pw:
            chrome = find_chrome_executable()
            lkw: dict[str, Any] = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
            if chrome:
                lkw["executable_path"] = chrome
            br = pw.chromium.launch(**lkw)
            page = br.new_page(viewport={"width": gl_w, "height": gl_h}, device_scale_factor=1.0)
            page.on("pageerror", lambda e: print("[v12-pageerror]", e, flush=True))
            page.set_content(html_doc, wait_until="load")
            page.evaluate("() => Promise.all([document.fonts.ready, window._assetsReady || Promise.resolve()])")
            try:
                for f_i in range(total_frames):
                    t = f_i / float(render_fps)
                    page.evaluate(f"window.renderAt({t:.4f})")
                    proc.stdin.write(page.screenshot(type="jpeg", quality=92))
                    if f_i > 0 and f_i % 120 == 0:
                        el = max(time.perf_counter() - t0, 0.01)
                        print(f"[v12-papercraft-25d] {f_i}/{total_frames} frames ({100*f_i/total_frames:.0f}%, {f_i/el:.1f} fps)", flush=True)
            finally:
                br.close()
                if proc.stdin and not proc.stdin.closed:
                    proc.stdin.close()
        ret = proc.wait()

    if ret != 0:
        err = err_log.read_text(encoding="utf-8", errors="ignore") if err_log.exists() else ""
        raise RuntimeError(f"FFmpeg v12 papercraft 2.5D failed ({ret}): {err[-300:]}")

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
    return out_video_path
