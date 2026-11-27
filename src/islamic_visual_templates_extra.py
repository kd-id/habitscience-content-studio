"""Studio v10.5 Extended Visual Templates — Ref #1 (Nature Transform), Ref #3 (Paper-Cutout 3D), Ref #6 (Cinematic Metaphor).

Upgraded with True 4-Act Visual Storytelling & Animated Science Explainers:
  - ACT 1 (`HOOK`)      : Arabic Dalil HIDDEN -> animated visual Hook action + kinetic headline!
  - ACT 2 (`DALIL`)     : Center-stage Sacred Arabic Calligraphy spotlight synced to real Arabic VO!
  - ACT 3 (`EXPLAINER`) : Arabic exits -> full-screen animated science/habit diagram (`drawAct3ExplainerVisual`)!
  - ACT 4 (`CLIMAX`)    : Full emotional visual transformation + unmistakable bold Core Lesson Card!

All 3 engines:
  - Support BOTH 9:16 (720x1280 -> 1080x1920) AND 16:9 (1280x720 -> 1920x1080)
  - Embed OFL Amiri Arabic Calligraphy with crisp RTL harakat
  - Avoid slow software `backdrop-filter: blur()` so headless Chromium renders fast
  - Strictly respect Islamic adab (ZERO depiction of Prophets; Ref #3 presenter has zero facial features).
"""

from __future__ import annotations

import json
from typing import Any

from src.islamic_story_acts import STORY_ACTS_JS


# ---------------------------------------------------------------------------
# Format 1 (Ref #1 Minute Wisdom): `islamic_nature_transform`
# ACT 1: Roaring Fire & Hook Action -> ACT 2: Steam/Teardrop & Sacred Dalil
# -> ACT 3: Meadow Pool & Animated Mind Explainer -> ACT 4: Full Blooming Trees & Core Lesson
# ---------------------------------------------------------------------------

def build_nature_transform_html(payload: dict[str, Any], font_css: str, width: int, height: int) -> str:
    cfg_json = json.dumps(payload, ensure_ascii=False)
    is_short = height >= width
    top_pad = 64 if is_short else 18
    ar_size = 54 if is_short else 42
    tr_size = 23 if is_short else 19
    en_size = 20 if is_short else 17
    sub_size = 31 if is_short else 27

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  {font_css}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: {width}px; height: {height}px; overflow: hidden;
    background: #1C0D0A;
    font-family: 'Georgia', 'Segoe UI', serif;
    color: #F8FAFC;
  }}
  #bgCanvas {{ position: absolute; inset: 0; width: {width}px; height: {height}px; display: block; }}

  /* Top Act Indicator + Dynamic Headline */
  .top-stage {{
    position: absolute; top: {top_pad}px; left: 28px; right: 28px;
    z-index: 6; display: flex; flex-direction: column; align-items: center; text-align: center;
    pointer-events: none;
  }}
  .act-pill {{
    display: inline-flex; align-items: center; gap: 8px;
    padding: 5px 18px; border-radius: 999px;
    background: rgba(12, 18, 28, 0.72);
    border: 1.5px solid rgba(253, 224, 71, 0.55);
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px; font-weight: 800; letter-spacing: 2.2px; text-transform: uppercase;
    color: #FDE68A; margin-bottom: {10 if is_short else 6}px;
  }}
  .scene-head {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: {36 if is_short else 30}px; font-weight: 900; line-height: 1.16;
    text-transform: uppercase; letter-spacing: 0.4px;
    max-width: {650 if is_short else 980}px;
    text-shadow: 0 3px 16px rgba(0,0,0,0.60);
  }}
  .mini-cit {{
    margin-top: 5px; font-family: 'Segoe UI', sans-serif;
    font-size: 12px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase;
    opacity: 0.85;
  }}

  /* ACT 2 ONLY: Center-stage Sacred Arabic Dalil Spotlight */
  .dalil-stage {{
    position: absolute; left: 50%; transform: translateX(-50%);
    top: {228 if is_short else 128}px;
    z-index: 7; width: {640 if is_short else 900}px;
    background: rgba(14, 22, 34, 0.84);
    border: 2px solid rgba(253, 224, 71, 0.78);
    border-radius: 22px;
    padding: {22 if is_short else 14}px {24 if is_short else 28}px;
    text-align: center;
    box-shadow: 0 0 36px rgba(253, 224, 71, 0.25), 0 16px 36px rgba(0,0,0,0.48);
    display: none;
  }}
  .ar-title {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; unicode-bidi: embed;
    font-size: {ar_size}px; font-weight: 700; line-height: 1.52;
    color: #FFFDF7;
    text-shadow: 0 2px 14px rgba(253, 224, 71, 0.35);
    margin-bottom: {10 if is_short else 4}px;
  }}
  .tr-sub {{
    font-family: 'Georgia', serif;
    font-size: {tr_size}px; font-weight: 600; line-height: 1.3;
    color: #FDE68A; margin-bottom: 6px;
  }}
  .en-sub {{
    font-family: 'Georgia', serif; font-style: italic;
    font-size: {en_size}px; line-height: 1.34;
    color: rgba(248,250,252,0.92); margin-bottom: 12px;
  }}
  .cit-chip {{
    display: inline-block; padding: 4px 16px; border-radius: 999px;
    font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 800; letter-spacing: 2px;
    text-transform: uppercase; color: #FDE68A;
    background: rgba(253, 224, 71, 0.16); border: 1px solid rgba(253, 224, 71, 0.55);
  }}

  /* ACT 4 ONLY: Bold Core Lesson Takeaway Card */
  .climax-card {{
    position: absolute; left: 50%; transform: translateX(-50%);
    top: {224 if is_short else 132}px;
    z-index: 7; width: {630 if is_short else 840}px;
    background: rgba(8, 28, 22, 0.86);
    border: 2.5px solid #34D399;
    border-radius: 22px;
    padding: {24 if is_short else 16}px 28px;
    text-align: center;
    box-shadow: 0 0 36px rgba(52, 211, 153, 0.28), 0 16px 36px rgba(0,0,0,0.42);
    display: none;
  }}
  .climax-kicker {{
    font-family: 'Segoe UI', sans-serif; font-size: 14px; font-weight: 900;
    letter-spacing: 3px; text-transform: uppercase; color: #6EE7B7; margin-bottom: 10px;
  }}
  .climax-lesson {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: {34 if is_short else 29}px; font-weight: 900; line-height: 1.24;
    color: #FFFFFF; margin-bottom: 14px;
  }}
  .climax-cit {{
    display: inline-block; padding: 4px 16px; border-radius: 999px;
    background: rgba(110, 231, 183, 0.16); border: 1px solid rgba(110, 231, 183, 0.50);
    font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 800; letter-spacing: 2px;
    color: #A7F3D0;
  }}

  /* Compact 1/7 .. 7/7 meadow progress dots above subtitle */
  .dots-wrap {{
    position: absolute; left: 0; right: 0;
    bottom: {232 if is_short else 124}px;
    z-index: 7; display: flex; align-items: center; justify-content: center; gap: 10px;
    pointer-events: none;
  }}
  .pdot {{
    width: 11px; height: 11px; border-radius: 50%;
    border: 2px solid rgba(255,255,255,0.52); background: transparent;
  }}
  .pdot.done {{ background: #34D399; border-color: #10B981; box-shadow: 0 0 8px rgba(52,211,153,0.85); }}
  .pdot.active {{ background: #6EE7B7; border-color: #FFFFFF; transform: scale(1.22); }}
  .counter-txt {{
    font-family: 'Segoe UI', sans-serif; font-size: 14px; font-weight: 800;
    letter-spacing: 1.8px; color: #FFFFFF; text-shadow: 0 2px 6px rgba(0,0,0,0.7);
    margin-left: 6px;
  }}

  .sub-area {{
    position: absolute; left: 28px; right: 28px;
    bottom: {72 if is_short else 28}px;
    z-index: 8; text-align: center;
  }}
  .sub-card {{
    display: inline-block; max-width: {640 if is_short else 960}px;
    padding: 10px 22px; border-radius: 14px;
    background: rgba(9, 14, 24, 0.78);
    border: 1px solid rgba(255,255,255,0.18);
    box-shadow: 0 8px 24px rgba(0,0,0,0.44);
  }}
  #subText {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: {sub_size}px; font-weight: 700; line-height: 1.26; color: #FFFFFF;
  }}
  #subText .hi {{ color: #6EE7B7; }}

  .brand-foot {{
    position: absolute; bottom: {22 if is_short else 6}px; left: 0; right: 0;
    z-index: 9; text-align: center;
    font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 700; letter-spacing: 2px;
    text-shadow: 0 2px 6px rgba(0,0,0,0.75); color: rgba(255,255,255,0.84);
  }}
</style>
</head>
<body>
<canvas id="bgCanvas" width="{width}" height="{height}"></canvas>

<div class="top-stage" id="topStage">
  <div class="act-pill" id="actPill">ACT 1 • HOOK</div>
  <div class="scene-head" id="sceneHead"></div>
  <div class="mini-cit" id="miniCit"></div>
</div>

<div class="dalil-stage" id="dalilStage">
  <div class="ar-title" id="arTitle"></div>
  <div class="tr-sub" id="trSub"></div>
  <div class="en-sub" id="enSub"></div>
  <div class="cit-chip" id="citChip"></div>
</div>

<div class="climax-card" id="climaxCard">
  <div class="climax-kicker">✦  THE LESSON  ✦</div>
  <div class="climax-lesson" id="climaxLesson"></div>
  <div class="climax-cit" id="climaxCit"></div>
</div>

<div class="dots-wrap">
  <span id="dotsRow" style="display:inline-flex;gap:9px;align-items:center;"></span>
  <span class="counter-txt" id="counterTxt">1 / 7</span>
</div>

<div class="sub-area"><div class="sub-card" id="subCard"><div id="subText"></div></div></div>
<div class="brand-foot" id="brandFoot"></div>

<script>
const CFG = {cfg_json};
const W = {width}, H = {height};
const IS_SHORT = H >= W;
const ctx = document.getElementById('bgCanvas').getContext('2d');
const STORY = CFG.story_acts || {{}};

{STORY_ACTS_JS}

const ACTS = computeFourActTiming(CFG);

document.getElementById('arTitle').textContent = CFG.dalil.arabic;
document.getElementById('trSub').textContent = CFG.dalil.transliteration;
document.getElementById('enSub').textContent = '"' + CFG.dalil.translation + '"';
document.getElementById('citChip').textContent = '✦  ' + CFG.dalil.citation + '  ✦';
document.getElementById('climaxLesson').textContent = STORY.core_lesson || CFG.dalil.translation;
document.getElementById('climaxCit').textContent = '✦  ' + CFG.dalil.citation + '  •  SAVE & SHARE  ✦';
document.getElementById('brandFoot').textContent = CFG.dalil.handle + '  •  MINUTE WISDOM & SUNNAH';

const TOTAL_DOTS = 7;
const dotsRow = document.getElementById('dotsRow');
for (let i = 0; i < TOTAL_DOTS; i++) {{
  const d = document.createElement('span');
  d.className = 'pdot';
  dotsRow.appendChild(d);
}}

const FLAMES = [];
for (let i = 0; i < 64; i++) {{
  const row = (i % 8) / 7;
  FLAMES.push({{
    x: ((i * 157.3 + (i % 3) * 41) % 1000) / 1000,
    depth: row,
    sz: 12 + row * 34 + (i % 4) * 5,
    ph: i * 0.87,
    extinguishAt: 0.24 + ((i * 37) % 100) / 100 * 0.26,
  }});
}}
const FLOWERS = [];
for (let i = 0; i < 95; i++) {{
  const cols = ['#FFFFFF', '#FDE047', '#F9A8D4', '#FDBA74', '#E0F2FE'];
  FLOWERS.push({{
    x: ((i * 173.1) % 1000) / 1000,
    y: ((i * 291.7) % 1000) / 1000,
    r: 2.2 + (i % 3) * 1.1,
    col: cols[i % cols.length],
    appearAt: 0.56 + (i % 20) * 0.012,
  }});
}}

function lerp(a, b, t) {{ return a + (b - a) * t; }}
function lerpRGB(c1, c2, t) {{
  return [Math.round(lerp(c1[0], c2[0], t)), Math.round(lerp(c1[1], c2[1], t)), Math.round(lerp(c1[2], c2[2], t))];
}}
function rgb(c, a = 1) {{ return `rgba(${{c[0]}},${{c[1]}},${{c[2]}},${{a}})`; }}

function drawHexCracks(horizonY, alpha) {{
  if (alpha <= 0.02) return;
  ctx.save();
  ctx.strokeStyle = `rgba(255, 190, 120, ${{0.22 * alpha}})`;
  ctx.lineWidth = 1.3;
  const rows = 10;
  for (let r = 0; r < rows; r++) {{
    const p0 = Math.pow(r / rows, 1.45);
    const p1 = Math.pow((r + 1) / rows, 1.45);
    const y0 = horizonY + p0 * (H - horizonY);
    const y1 = horizonY + p1 * (H - horizonY);
    const cols = Math.max(5, Math.round(14 - r * 0.7));
    const step = W / cols;
    const off = (r % 2) * (step * 0.5);
    for (let c = -1; c <= cols + 1; c++) {{
      const x = c * step + off;
      ctx.beginPath();
      ctx.moveTo(x, y0);
      ctx.lineTo(x + step * 0.5, (y0 + y1) * 0.5);
      ctx.lineTo(x + step, y0);
      ctx.moveTo(x + step * 0.5, (y0 + y1) * 0.5);
      ctx.lineTo(x + step * 0.5, y1);
      ctx.stroke();
    }}
  }}
  ctx.restore();
}}

function drawFlame(x, y, sz, t, ph, alpha) {{
  ctx.save();
  ctx.translate(x, y);
  const flick = Math.sin(t * 9 + ph) * (sz * 0.14);
  const h = sz * (1.25 + 0.16 * Math.sin(t * 7 + ph));
  ctx.fillStyle = `rgba(234, 88, 12, ${{0.92 * alpha}})`;
  ctx.beginPath();
  ctx.moveTo(-sz * 0.44, 0);
  ctx.quadraticCurveTo(-sz * 0.5, -h * 0.55, flick, -h);
  ctx.quadraticCurveTo(sz * 0.5, -h * 0.55, sz * 0.44, 0);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = `rgba(253, 224, 71, ${{0.92 * alpha}})`;
  ctx.beginPath();
  ctx.moveTo(-sz * 0.22, -2);
  ctx.quadraticCurveTo(-sz * 0.24, -h * 0.35, flick * 0.5, -h * 0.62);
  ctx.quadraticCurveTo(sz * 0.24, -h * 0.35, sz * 0.22, -2);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}}

function drawTree(x, baseY, scale, canopyColor, accentColor, grow, t) {{
  if (grow <= 0.02) return;
  const s = scale * grow;
  const sway = Math.sin(t * 1.4 + x * 0.02) * 4 * grow;
  ctx.save();
  ctx.translate(x, baseY);
  ctx.fillStyle = '#6B4423';
  ctx.fillRect(-10 * s, -120 * s, 20 * s, 122 * s);
  ctx.fillStyle = '#533319';
  ctx.fillRect(0, -120 * s, 10 * s, 122 * s);
  const puffs = [[-36, -134, 34], [34, -132, 32], [-18, -164, 38], [22, -162, 36], [0, -142, 42]];
  ctx.fillStyle = canopyColor;
  for (const [px, py, pr] of puffs) {{
    ctx.beginPath();
    ctx.arc(px * s + sway, py * s, pr * s, 0, Math.PI * 2);
    ctx.fill();
  }}
  ctx.fillStyle = accentColor;
  for (const [fx, fy] of [[-24, -145], [14, -168], [30, -128], [-6, -124], [8, -146]]) {{
    ctx.beginPath();
    ctx.arc(fx * s + sway, fy * s, 4.5 * s, 0, Math.PI * 2);
    ctx.fill();
  }}
  ctx.restore();
}}

window.renderAt = function(t) {{
  const act = getCurrentAct(t, ACTS);
  // Map environmental transformation directly to the 4 Acts for dramatic visual storytelling!
  // Act 1 HOOK: 0.00..0.24 (Fiery heat) | Act 2 DALIL: 0.24..0.50 (Steam & Cooling Rain)
  // Act 3 EXPLAINER: 0.50..0.78 (Teardrop & Green Meadow) | Act 4 CLIMAX: 0.78..1.00 (Full Bloom & Trees!)
  let envP = 0;
  if (act.name === 'HOOK') envP = act.localT * 0.22;
  else if (act.name === 'DALIL') envP = 0.22 + act.localT * 0.28;
  else if (act.name === 'EXPLAINER') envP = 0.50 + act.localT * 0.28;
  else envP = 0.78 + act.localT * 0.22;

  const horizonY = H * (IS_SHORT ? 0.62 : 0.66);

  // Sky transition tied to 4 Acts
  let topC, midC, botC;
  if (envP < 0.34) {{
    const u = envP / 0.34;
    topC = lerpRGB([46, 15, 10], [42, 34, 36], u);
    midC = lerpRGB([118, 42, 18], [76, 62, 58], u);
    botC = lerpRGB([184, 84, 28], [108, 96, 92], u);
  }} else if (envP < 0.58) {{
    const u = (envP - 0.34) / 0.24;
    topC = lerpRGB([42, 34, 36], [88, 158, 212], u);
    midC = lerpRGB([76, 62, 58], [156, 206, 232], u);
    botC = lerpRGB([108, 96, 92], [238, 232, 194], u);
  }} else {{
    const u = (envP - 0.58) / 0.42;
    topC = lerpRGB([88, 158, 212], [116, 184, 232], u);
    midC = lerpRGB([156, 206, 232], [192, 226, 240], u);
    botC = lerpRGB([238, 232, 194], [248, 243, 210], u);
  }}

  const skyG = ctx.createLinearGradient(0, 0, 0, horizonY);
  skyG.addColorStop(0, rgb(topC));
  skyG.addColorStop(0.6, rgb(midC));
  skyG.addColorStop(1, rgb(botC));
  ctx.fillStyle = skyG;
  ctx.fillRect(0, 0, W, horizonY + 12);

  // Soft clouds in Act 3 & Act 4
  if (envP > 0.48) {{
    const clA = Math.min((envP - 0.48) / 0.16, 0.85);
    ctx.fillStyle = `rgba(255, 255, 255, ${{clA}})`;
    for (const [cx0, cy, r] of [[0.18, 0.52, 26], [0.76, 0.48, 30], [0.50, 0.54, 22]]) {{
      const cx = ((cx0 * W + t * 8) % (W + 120)) - 60;
      const py = cy * H;
      ctx.beginPath();
      ctx.arc(cx, py, r, 0, Math.PI * 2);
      ctx.arc(cx + r * 0.9, py - 4, r * 0.85, 0, Math.PI * 2);
      ctx.arc(cx + r * 1.7, py + 2, r * 0.72, 0, Math.PI * 2);
      ctx.fill();
    }}
  }}

  // Distant rolling hills
  const hillCol = lerpRGB([46, 32, 26], [108, 166, 118], Math.min(Math.max((envP - 0.36) / 0.24, 0), 1));
  ctx.fillStyle = rgb(hillCol);
  ctx.beginPath();
  ctx.moveTo(0, horizonY + 8);
  ctx.quadraticCurveTo(W * 0.25, horizonY - 28, W * 0.52, horizonY - 8);
  ctx.quadraticCurveTo(W * 0.78, horizonY - 34, W, horizonY - 6);
  ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
  ctx.fill();

  // Foreground ground: dark cracked earth -> vibrant green meadow
  const grassMix = Math.min(Math.max((envP - 0.44) / 0.18, 0), 1);
  const gTop = lerpRGB([28, 22, 20], [122, 186, 86], grassMix);
  const gBot = lerpRGB([14, 10, 10], [74, 146, 58], grassMix);
  const gGrad = ctx.createLinearGradient(0, horizonY, 0, H);
  gGrad.addColorStop(0, rgb(gTop)); gGrad.addColorStop(1, rgb(gBot));
  ctx.fillStyle = gGrad;
  ctx.fillRect(0, horizonY, W, H - horizonY);
  drawHexCracks(horizonY, 1 - grassMix);

  // Act 1 & early Act 2: Flames extinguishing with steam
  if (envP < 0.54) {{
    for (const fl of FLAMES) {{
      const fy = horizonY + 22 + fl.depth * (H - horizonY - 40);
      const fx = fl.x * W;
      if (envP < fl.extinguishAt) {{
        const a = Math.min(1, (fl.extinguishAt - envP) / 0.08);
        drawFlame(fx, fy, fl.sz, t, fl.ph, a);
      }} else if (envP < fl.extinguishAt + 0.14) {{
        const sm = 1 - (envP - fl.extinguishAt) / 0.14;
        ctx.fillStyle = `rgba(220, 226, 234, ${{0.30 * sm}})`;
        ctx.beginPath();
        ctx.arc(fx + Math.sin(t * 2 + fl.ph) * 8, fy - (1 - sm) * 46, fl.sz * 0.55, 0, Math.PI * 2);
        ctx.fill();
      }}
    }}
  }}

  // Act 2..4: Teardrop into rippling pool
  const poolX = W * 0.5, poolY = horizonY + (H - horizonY) * (IS_SHORT ? 0.34 : 0.38);
  if (envP > 0.34) {{
    const poolGrow = Math.min((envP - 0.34) / 0.18, 1);
    const rx = (IS_SHORT ? 82 : 94) * poolGrow;
    const ry = (IS_SHORT ? 24 : 22) * poolGrow;
    ctx.fillStyle = '#8C7A65';
    ctx.beginPath(); ctx.ellipse(poolX, poolY, rx + 5, ry + 3, 0, 0, Math.PI * 2); ctx.fill();
    const pg = ctx.createRadialGradient(poolX, poolY - 4, 4, poolX, poolY, rx);
    pg.addColorStop(0, '#93D5FA'); pg.addColorStop(1, '#3B82B6');
    ctx.fillStyle = pg;
    ctx.beginPath(); ctx.ellipse(poolX, poolY, rx, ry, 0, 0, Math.PI * 2); ctx.fill();
    const rip = (t * 0.8) % 1.0;
    ctx.strokeStyle = `rgba(255,255,255,${{(1 - rip) * 0.65}})`;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.ellipse(poolX, poolY, 10 + rip * rx * 0.72, 4 + rip * ry * 0.72, 0, 0, Math.PI * 2);
    ctx.stroke();

    if (envP < 0.80) {{
      const dropCyc = (t * 0.72) % 1.0;
      const dy = lerp(horizonY - 82, poolY - 6, dropCyc * dropCyc);
      ctx.fillStyle = '#7DD3FC';
      ctx.beginPath();
      ctx.moveTo(poolX, dy - 22);
      ctx.bezierCurveTo(poolX + 12, dy - 2, poolX + 11, dy + 10, poolX, dy + 10);
      ctx.bezierCurveTo(poolX - 11, dy + 10, poolX - 12, dy - 2, poolX, dy - 22);
      ctx.fill();
    }}
  }}

  // Act 3 & Act 4: Wildflowers & blooming apple + cherry blossom trees!
  if (envP > 0.54) {{
    for (const fw of FLOWERS) {{
      if (envP < fw.appearAt) continue;
      const a = Math.min((envP - fw.appearAt) / 0.08, 1);
      const fx = fw.x * W;
      const fy = horizonY + 14 + fw.y * (H - horizonY - 26);
      if (Math.hypot((fx - poolX) / 96, (fy - poolY) / 36) < 1.1) continue;
      ctx.fillStyle = fw.col;
      ctx.globalAlpha = a * 0.92;
      ctx.beginPath(); ctx.arc(fx, fy, fw.r, 0, Math.PI * 2); ctx.fill();
    }}
    ctx.globalAlpha = 1;
    const treeGrow = Math.min(Math.max((envP - 0.74) / 0.16, 0), 1);
    const tScale = IS_SHORT ? 0.96 : 0.78;
    drawTree(W * 0.16, horizonY + (H - horizonY) * 0.34, tScale, '#3D9140', '#EF4444', treeGrow, t);
    drawTree(W * 0.84, horizonY + (H - horizonY) * 0.33, tScale * 0.94, '#F9A8D4', '#FCE7F3', treeGrow, t);
  }}

  // Draw Act-Specific Center-Stage Canvas Visuals!
  const pal = {{
    bgCard: 'rgba(10, 22, 28, 0.86)',
    border: 'rgba(110, 231, 183, 0.65)',
    ink: '#F8FAFC',
    muted: '#94A3B8',
    accent: '#FDE68A',
    good: '#34D399',
    light: false,
  }};
  const stageY = H * (IS_SHORT ? 0.39 : 0.44);
  if (act.name === 'HOOK') {{
    drawAct1HookVisual(ctx, STORY.hook_visual || 'racing_mind', W * 0.5, stageY, IS_SHORT ? 1.14 : 0.90, act.localT, t, pal);
  }} else if (act.name === 'EXPLAINER') {{
    drawAct3ExplainerVisual(ctx, STORY, W * 0.5, stageY, IS_SHORT ? 1.04 : 0.88, act.localT, t, pal);
  }}

  // Adaptive headline text color on bright meadow sky vs dark ember sky
  const lightSky = envP > 0.52;
  const headEl = document.getElementById('sceneHead');
  headEl.style.color = lightSky ? '#0F172A' : '#FFFDF7';
  headEl.style.textShadow = lightSky ? '0 2px 0 rgba(255,255,255,0.75)' : '0 3px 16px rgba(0,0,0,0.65)';
  document.getElementById('miniCit').style.color = lightSky ? '#0F5132' : '#FDE68A';

  // Active scene lookup
  let cur = CFG.scenes[CFG.scenes.length - 1];
  for (const s of CFG.scenes) {{
    if (t >= s.start && t <= s.end) {{ cur = s; break; }}
  }}

  // Strictly toggle 4-Act DOM overlays (ZERO premature Arabic spoiler!)
  const dalilStage = document.getElementById('dalilStage');
  const climaxCard = document.getElementById('climaxCard');
  const actPill = document.getElementById('actPill');
  const miniCit = document.getElementById('miniCit');
  const arWin = CFG.arabic_window;

  if (act.name === 'HOOK') {{
    dalilStage.style.display = 'none';
    climaxCard.style.display = 'none';
    actPill.textContent = 'ACT 1 • ' + (STORY.hook_kicker || 'THE HOOK');
    actPill.style.borderColor = '#F87171';
    actPill.style.color = '#FCA5A5';
    headEl.textContent = (CFG.scenes[0] && CFG.scenes[0].headline) || CFG.dalil.topic;
    miniCit.textContent = '';
  }} else if (act.name === 'DALIL') {{
    dalilStage.style.display = 'block';
    climaxCard.style.display = 'none';
    actPill.textContent = (arWin && arWin.is_qari) ? `ACT 2 • TILAWAH (${{arWin.reciter}})` : 'ACT 2 • VERIFIED PROPHETIC WISDOM';
    actPill.style.borderColor = '#FDE68A';
    actPill.style.color = '#FDE68A';
    headEl.textContent = CFG.dalil.citation;
    miniCit.textContent = '';
  }} else if (act.name === 'EXPLAINER') {{
    dalilStage.style.display = 'none';
    climaxCard.style.display = 'none';
    actPill.textContent = 'ACT 3 • THE SCIENCE';
    actPill.style.borderColor = '#34D399';
    actPill.style.color = '#6EE7B7';
    headEl.textContent = (cur && cur.headline) || 'HOW IT RESETS YOUR MIND';
    miniCit.textContent = '✦  ' + CFG.dalil.citation + '  ✦';
  }} else {{
    dalilStage.style.display = 'none';
    climaxCard.style.display = 'block';
    actPill.textContent = 'ACT 4 • THE TAKEAWAY';
    actPill.style.borderColor = '#34D399';
    actPill.style.color = '#A7F3D0';
    headEl.textContent = (cur && cur.headline) || 'DAILY BLOOM';
    miniCit.textContent = '';
  }}

  // Update 1/7 .. 7/7 glowing dots
  const stepNum = Math.min(TOTAL_DOTS, Math.floor(envP * TOTAL_DOTS) + 1);
  document.getElementById('counterTxt').textContent = `${{stepNum}} / ${{TOTAL_DOTS}}`;
  const dots = dotsRow.children;
  for (let i = 0; i < TOTAL_DOTS; i++) {{
    dots[i].className = 'pdot' + (i < stepNum - 1 ? ' done' : (i === stepNum - 1 ? ' active' : ''));
  }}

  // Synchronized bilingual subtitle
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


# ---------------------------------------------------------------------------
# Format 3 (Ref #3 @umam_c.u): `islamic_paper_craft`
# Pastel Sky Blue 3D Paper-Cutout Craft Diorama + Faceless Minimalist Presenter
# ACT 1: Presenter points to Hook Prop -> ACT 2: Open Book & Arabic Paper Ribbon
# -> ACT 3: Presenter teaches live Paper-Craft Science Explainer -> ACT 4: Arch Medallion + Core Lesson + Dua Pose!
# ---------------------------------------------------------------------------

def build_paper_craft_html(payload: dict[str, Any], font_css: str, width: int, height: int) -> str:
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
    background: #A9D2DD;
    font-family: 'Segoe UI', 'Trebuchet MS', Arial, sans-serif;
    color: #1E2F42;
  }}
  #bgCanvas {{ position: absolute; inset: 0; width: {width}px; height: {height}px; display: block; }}

  .top-paper {{
    position: absolute; top: {52 if is_short else 16}px; left: 30px; right: 30px;
    z-index: 6; display: flex; flex-direction: column; align-items: center; text-align: center;
    pointer-events: none;
  }}
  .pill-tag {{
    display: inline-block; padding: 5px 18px; border-radius: 999px;
    background: #1E2F42; color: #F5F1E3;
    font-size: 13px; font-weight: 900; letter-spacing: 2.2px; text-transform: uppercase;
    box-shadow: 0 6px 14px rgba(15, 28, 42, 0.22);
    margin-bottom: {10 if is_short else 5}px;
  }}
  .cutout-headline {{
    font-size: {38 if is_short else 32}px; font-weight: 900; line-height: 1.12;
    color: #1E2F42; text-transform: uppercase; letter-spacing: 0.4px;
    max-width: {640 if is_short else 960}px;
    text-shadow: 0 3px 0 #F5F1E3, 0 8px 16px rgba(15, 28, 42, 0.20);
  }}
  .mini-cit {{
    margin-top: 5px; font-size: 12px; font-weight: 800; letter-spacing: 2px;
    color: #0F5E48; text-transform: uppercase;
  }}

  /* ACT 2 ONLY: Arabic calligraphy cream paper card */
  .ar-ribbon {{
    position: absolute; left: 50%; transform: translateX(-50%);
    top: {222 if is_short else 124}px;
    z-index: 7; width: {640 if is_short else 880}px;
    background: #F7F3E6;
    border: 3px solid #D97706;
    border-radius: 20px;
    padding: {18 if is_short else 12}px 24px;
    text-align: center;
    box-shadow: 0 0 28px rgba(229, 190, 102, 0.55), 6px 12px 24px rgba(15, 28, 42, 0.24);
    display: none;
  }}
  .ar-script {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; unicode-bidi: embed;
    font-size: {42 if is_short else 34}px; font-weight: 700; line-height: 1.5;
    color: #1E2F42; margin-bottom: 6px;
  }}
  .ar-tr {{
    font-size: {18 if is_short else 16}px; font-weight: 700; color: #334155;
    margin-bottom: 6px;
  }}
  .ar-cit {{
    display: inline-block; padding: 3px 14px; border-radius: 999px;
    background: rgba(229, 190, 102, 0.30);
    font-size: 13px; font-weight: 800; letter-spacing: 2px;
    color: #92400E; text-transform: uppercase;
  }}

  /* ACT 4 ONLY: Cream & Gold Paper-Cutout Core Lesson Card */
  .climax-paper {{
    position: absolute; left: 50%; transform: translateX(-50%);
    top: {220 if is_short else 126}px;
    z-index: 7; width: {620 if is_short else 760}px;
    background: #FAF6EA;
    border: 3px solid #0F766E;
    border-radius: 20px;
    padding: {20 if is_short else 14}px 26px;
    text-align: center;
    box-shadow: 6px 12px 24px rgba(15, 28, 42, 0.24);
    display: none;
  }}
  .climax-kicker {{
    font-size: 13px; font-weight: 900; letter-spacing: 2.6px;
    color: #0F766E; text-transform: uppercase; margin-bottom: 8px;
  }}
  .climax-lesson {{
    font-size: {32 if is_short else 27}px; font-weight: 900; line-height: 1.22;
    color: #1E2F42; margin-bottom: 10px;
  }}
  .climax-cit {{
    display: inline-block; padding: 4px 14px; border-radius: 999px;
    background: #1E2F42; color: #F5D076;
    font-size: 12px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;
  }}

  .sub-area {{
    position: absolute; left: 28px; right: 28px;
    bottom: {64 if is_short else 24}px;
    z-index: 9; text-align: center;
  }}
  .sub-paper {{
    display: inline-block; max-width: {640 if is_short else 960}px;
    padding: 11px 22px; border-radius: 14px;
    background: #F6F2E6;
    border: 2px solid rgba(30, 47, 66, 0.18);
    box-shadow: 4px 10px 22px rgba(15, 28, 42, 0.24);
  }}
  #subText {{
    font-size: {30 if is_short else 26}px; font-weight: 800; line-height: 1.24; color: #1E2F42;
  }}
  #subText .hi {{
    color: #0F5E48; background: rgba(229, 190, 102, 0.42);
    padding: 0 5px; border-radius: 6px;
  }}

  .brand-foot {{
    position: absolute; bottom: {18 if is_short else 5}px; left: 0; right: 0;
    z-index: 9; text-align: center;
    font-size: 13px; font-weight: 800; letter-spacing: 2px; color: rgba(30, 47, 66, 0.70);
  }}
</style>
</head>
<body>
<canvas id="bgCanvas" width="{width}" height="{height}"></canvas>

<div class="top-paper">
  <div class="pill-tag" id="pillTag">ACT 1 • HOOK</div>
  <div class="cutout-headline" id="headline"></div>
  <div class="mini-cit" id="miniCit"></div>
</div>

<div class="ar-ribbon" id="arRibbon">
  <div class="ar-script" id="arScript"></div>
  <div class="ar-tr" id="arTr"></div>
  <div class="ar-cit" id="arCit"></div>
</div>

<div class="climax-paper" id="climaxPaper">
  <div class="climax-kicker">✦  THE SUNNAH LESSON  ✦</div>
  <div class="climax-lesson" id="climaxLesson"></div>
  <div class="climax-cit" id="climaxCit"></div>
</div>

<div class="sub-area"><div class="sub-paper" id="subPaper"><div id="subText"></div></div></div>
<div class="brand-foot" id="brandFoot"></div>

<script>
const CFG = {cfg_json};
const W = {width}, H = {height};
const IS_SHORT = H >= W;
const ctx = document.getElementById('bgCanvas').getContext('2d');
const STORY = CFG.story_acts || {{}};

{STORY_ACTS_JS}

const ACTS = computeFourActTiming(CFG);

document.getElementById('arScript').textContent = CFG.dalil.arabic;
document.getElementById('arTr').textContent = CFG.dalil.transliteration;
document.getElementById('arCit').textContent = '✦  ' + CFG.dalil.citation + '  ✦';
document.getElementById('climaxLesson').textContent = STORY.core_lesson || CFG.dalil.translation;
document.getElementById('climaxCit').textContent = '✦  ' + CFG.dalil.citation + '  •  SAVE & SHARE  ✦';
document.getElementById('brandFoot').textContent = CFG.dalil.handle + '  •  PAPER CRAFT SUNNAH STORY';

function setPaperShadow(dx = 5, dy = 10, blur = 16, alpha = 0.22) {{
  ctx.shadowColor = `rgba(15, 28, 42, ${{alpha}})`;
  ctx.shadowBlur = blur; ctx.shadowOffsetX = dx; ctx.shadowOffsetY = dy;
}}
function clearShadow() {{
  ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0; ctx.shadowOffsetX = 0; ctx.shadowOffsetY = 0;
}}

function drawPaperCloud(x, y, s) {{
  ctx.save(); setPaperShadow(3, 7, 12, 0.16);
  ctx.fillStyle = '#F7F4EA';
  ctx.beginPath();
  ctx.arc(x, y, 22 * s, 0, Math.PI * 2);
  ctx.arc(x + 22 * s, y - 8 * s, 26 * s, 0, Math.PI * 2);
  ctx.arc(x + 48 * s, y, 20 * s, 0, Math.PI * 2);
  ctx.fillRect(x, y, 48 * s, 20 * s);
  ctx.fill(); ctx.restore();
}}

function drawPaperSunburst(cx, cy, r, t) {{
  ctx.save(); ctx.translate(cx, cy); ctx.rotate(t * 0.14);
  setPaperShadow(4, 8, 14, 0.18);
  const rays = 12;
  for (let i = 0; i < rays; i++) {{
    ctx.save(); ctx.rotate((i / rays) * Math.PI * 2);
    ctx.fillStyle = (i % 2 === 0) ? '#F7F4EA' : '#ECD082';
    ctx.beginPath();
    ctx.moveTo(-8, -r * 1.18); ctx.lineTo(8, -r * 1.18);
    ctx.lineTo(13, -r * 1.95); ctx.lineTo(-13, -r * 1.95);
    ctx.closePath(); ctx.fill(); ctx.restore();
  }}
  ctx.fillStyle = '#E6C167';
  ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill();
  clearShadow();
  ctx.fillStyle = '#EED082';
  ctx.beginPath(); ctx.arc(-4, -4, r * 0.78, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}}

function drawPaperTree(x, y, s, variant) {{
  ctx.save(); ctx.translate(x, y); setPaperShadow(4, 8, 12, 0.22);
  if (variant === 'pine') {{
    ctx.fillStyle = '#5B402D'; ctx.fillRect(-5 * s, -20 * s, 10 * s, 24 * s);
    for (let k = 0; k < 3; k++) {{
      ctx.fillStyle = k === 0 ? '#2E5B43' : (k === 1 ? '#3D7354' : '#4E8C65');
      const base = -18 * s - k * 24 * s; const hw = (36 - k * 7) * s;
      ctx.beginPath(); ctx.moveTo(-hw, base); ctx.lineTo(0, base - 38 * s); ctx.lineTo(hw, base); ctx.closePath(); ctx.fill();
    }}
  }} else {{
    ctx.fillStyle = '#6A4C36'; ctx.fillRect(-6 * s, -62 * s, 12 * s, 64 * s);
    ctx.fillStyle = '#4B7F52';
    ctx.beginPath();
    ctx.arc(0, -78 * s, 30 * s, 0, Math.PI * 2);
    ctx.arc(-22 * s, -64 * s, 22 * s, 0, Math.PI * 2);
    ctx.arc(22 * s, -62 * s, 22 * s, 0, Math.PI * 2);
    ctx.fill();
    clearShadow(); ctx.fillStyle = '#689F69';
    ctx.beginPath(); ctx.arc(-8 * s, -84 * s, 16 * s, 0, Math.PI * 2); ctx.fill();
  }}
  ctx.restore();
}}

// Respectful FACELESS minimalist Muslim presenter in navy kurta/koko — ZERO facial features!
function drawFacelessPresenter(x, baseY, s, pose, t) {{
  ctx.save(); ctx.translate(x, baseY + Math.sin(t * 2.2) * 3 * s);
  setPaperShadow(5, 10, 14, 0.24);
  ctx.fillStyle = '#182534';
  ctx.fillRect(-20 * s, -98 * s, 16 * s, 82 * s);
  ctx.fillRect(4 * s, -98 * s, 16 * s, 82 * s);
  ctx.fillStyle = '#3B2F2F';
  ctx.beginPath();
  ctx.roundRect(-24 * s, -16 * s, 22 * s, 12 * s, 5 * s);
  ctx.roundRect(2 * s, -16 * s, 22 * s, 12 * s, 5 * s);
  ctx.fill();
  ctx.fillStyle = '#1E3148';
  ctx.beginPath(); ctx.roundRect(-30 * s, -214 * s, 60 * s, 134 * s, 16 * s); ctx.fill();
  clearShadow(); ctx.fillStyle = '#2B425E'; ctx.fillRect(-3 * s, -212 * s, 6 * s, 54 * s);

  setPaperShadow(3, 6, 10, 0.20); ctx.fillStyle = '#1A2B3F';
  ctx.beginPath(); ctx.roundRect(-42 * s, -206 * s, 16 * s, 82 * s, 8 * s); ctx.fill();

  ctx.save(); ctx.translate(26 * s, -198 * s);
  if (pose === 'point') {{
    ctx.rotate(-0.85 + Math.sin(t * 2.5) * 0.06);
    ctx.fillStyle = '#1A2B3F'; ctx.beginPath(); ctx.roundRect(0, -8 * s, 72 * s, 16 * s, 8 * s); ctx.fill();
    ctx.fillStyle = '#E8C5A8'; ctx.beginPath(); ctx.arc(76 * s, 0, 9 * s, 0, Math.PI * 2); ctx.fill();
  }} else if (pose === 'dua') {{
    ctx.rotate(-2.1 + Math.sin(t * 1.8) * 0.05);
    ctx.fillStyle = '#1A2B3F'; ctx.beginPath(); ctx.roundRect(0, -8 * s, 54 * s, 15 * s, 7 * s); ctx.fill();
    ctx.fillStyle = '#E8C5A8'; ctx.beginPath(); ctx.arc(58 * s, 0, 8 * s, 0, Math.PI * 2); ctx.fill();
  }} else {{
    ctx.fillStyle = '#1A2B3F'; ctx.beginPath(); ctx.roundRect(-4 * s, 0, 16 * s, 80 * s, 8 * s); ctx.fill();
  }}
  ctx.restore();

  ctx.fillStyle = '#E8C5A8';
  ctx.beginPath(); ctx.roundRect(-18 * s, -264 * s, 36 * s, 44 * s, 16 * s); ctx.fill();
  clearShadow(); ctx.fillStyle = '#18222F';
  ctx.beginPath(); ctx.arc(0, -252 * s, 19 * s, Math.PI * 1.05, Math.PI * 1.95);
  ctx.lineTo(18 * s, -242 * s); ctx.lineTo(-18 * s, -242 * s); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.arc(0, -234 * s, 18 * s, 0.1 * Math.PI, 0.9 * Math.PI); ctx.fill();
  ctx.restore();
}}

function drawPaperHillsScene(t) {{
  const baseH = H * (IS_SHORT ? 0.80 : 0.84);
  ctx.save(); setPaperShadow(0, -4, 14, 0.16);
  ctx.fillStyle = '#82B378';
  ctx.beginPath(); ctx.moveTo(0, baseH - 70);
  ctx.quadraticCurveTo(W * 0.28, baseH - 150, W * 0.56, baseH - 85);
  ctx.quadraticCurveTo(W * 0.82, baseH - 140, W, baseH - 78);
  ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath(); ctx.fill();

  ctx.fillStyle = '#558B59';
  ctx.beginPath(); ctx.moveTo(0, baseH - 12);
  ctx.quadraticCurveTo(W * 0.30, baseH - 80, W * 0.62, baseH - 22);
  ctx.quadraticCurveTo(W * 0.85, baseH - 60, W, baseH - 18);
  ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath(); ctx.fill();

  ctx.fillStyle = '#3B6E4A';
  ctx.beginPath(); ctx.moveTo(0, baseH + 40);
  ctx.quadraticCurveTo(W * 0.48, baseH - 10, W, baseH + 34);
  ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath(); ctx.fill();
  ctx.restore();

  const sc = IS_SHORT ? 1.0 : 0.76;
  drawPaperTree(W * 0.12, baseH - 18, sc * 0.88, 'pine');
  drawPaperTree(W * 0.88, baseH - 22, sc * 1.0, 'round');
  drawPaperTree(W * 0.78, baseH + 14, sc * 0.72, 'pine');
}}

function drawOpenPaperBookProp(cx, cy, s, t) {{
  ctx.save(); ctx.translate(cx, cy); setPaperShadow(6, 12, 18, 0.22);
  for (let layer = 2; layer >= 0; layer--) {{
    const dy = layer * 7 * s;
    ctx.fillStyle = layer === 0 ? '#FAF7EE' : (layer === 1 ? '#EAE4D3' : '#D4CCB7');
    ctx.beginPath();
    ctx.moveTo(0, dy);
    ctx.quadraticCurveTo(-85 * s, -22 * s + dy, -175 * s, 4 * s + dy);
    ctx.lineTo(-160 * s, 56 * s + dy);
    ctx.quadraticCurveTo(-80 * s, 32 * s + dy, 0, 52 * s + dy);
    ctx.quadraticCurveTo(80 * s, 32 * s + dy, 160 * s, 56 * s + dy);
    ctx.lineTo(175 * s, 4 * s + dy);
    ctx.quadraticCurveTo(85 * s, -22 * s + dy, 0, dy);
    ctx.closePath(); ctx.fill();
  }}
  clearShadow();
  drawPaperSunburst(0, -104 * s + Math.sin(t * 2.0) * 6 * s, 44 * s, t);
  ctx.restore();
}}

function drawIslamicArchMedallion(cx, cy, s) {{
  ctx.save(); ctx.translate(cx, cy); setPaperShadow(6, 12, 20, 0.22);
  ctx.fillStyle = '#E5BE66';
  ctx.beginPath();
  ctx.moveTo(0, -135 * s);
  ctx.bezierCurveTo(85 * s, -105 * s, 118 * s, -25 * s, 108 * s, 52 * s);
  ctx.bezierCurveTo(92 * s, 112 * s, 36 * s, 124 * s, 0, 138 * s);
  ctx.bezierCurveTo(-36 * s, 124 * s, -92 * s, 112 * s, -108 * s, 52 * s);
  ctx.bezierCurveTo(-118 * s, -25 * s, -85 * s, -105 * s, 0, -135 * s);
  ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#FAF6EA';
  ctx.beginPath(); ctx.arc(0, 4 * s, 92 * s, 0, Math.PI * 2); ctx.fill();
  clearShadow();
  ctx.fillStyle = '#1E2F42';
  ctx.font = `900 ${{24 * s}}px 'Segoe UI', sans-serif`;
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText('PEACE &', 0, -12 * s);
  ctx.fillStyle = '#0F766E';
  ctx.fillText('BARAKAH', 0, 18 * s);
  ctx.restore();
}}

window.renderAt = function(t) {{
  const act = getCurrentAct(t, ACTS);

  const bg = ctx.createLinearGradient(0, 0, 0, H);
  bg.addColorStop(0, '#9ECAD6'); bg.addColorStop(0.65, '#B7DCE6'); bg.addColorStop(1, '#CEE7EE');
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);

  drawPaperCloud(((W * 0.10 + t * 9) % (W + 140)) - 70, H * (IS_SHORT ? 0.24 : 0.26), IS_SHORT ? 0.95 : 0.80);
  drawPaperCloud(((W * 0.72 + t * 6) % (W + 140)) - 70, H * (IS_SHORT ? 0.28 : 0.30), IS_SHORT ? 0.82 : 0.70);

  const sc = IS_SHORT ? 1.0 : 0.72;
  const pal = {{
    bgCard: '#FAF6EA',
    border: '#E5BE66',
    ink: '#1E2F42',
    muted: '#64748B',
    accent: '#B45309',
    good: '#059669',
    light: true,
  }};

  drawPaperHillsScene(t);

  if (act.name === 'HOOK') {{
    drawPaperSunburst(W * 0.84, H * 0.28, 42 * sc, t);
    drawFacelessPresenter(W * (IS_SHORT ? 0.20 : 0.20), H * (IS_SHORT ? 0.86 : 0.90), sc * 0.96, 'point', t);
    const hx = IS_SHORT ? W * 0.54 : W * 0.56;
    const hy = H * (IS_SHORT ? 0.45 : 0.48);
    drawAct1HookVisual(ctx, STORY.hook_visual || 'rushing_calendar', hx, hy, IS_SHORT ? 1.08 : 0.88, act.localT, t, pal);
  }} else if (act.name === 'DALIL') {{
    drawOpenPaperBookProp(W * 0.56, H * (IS_SHORT ? 0.67 : 0.68), sc * 0.96, t);
    drawFacelessPresenter(W * (IS_SHORT ? 0.20 : 0.22), H * (IS_SHORT ? 0.86 : 0.90), sc * 0.96, 'point', t);
  }} else if (act.name === 'EXPLAINER') {{
    drawFacelessPresenter(W * (IS_SHORT ? 0.20 : 0.18), H * (IS_SHORT ? 0.87 : 0.90), sc * 0.92, 'point', t);
    const ex = IS_SHORT ? W * 0.50 : W * 0.57;
    const ey = H * (IS_SHORT ? 0.43 : 0.48);
    drawAct3ExplainerVisual(ctx, STORY, ex, ey, IS_SHORT ? 1.02 : 0.88, act.localT, t, pal);
  }} else {{
    drawIslamicArchMedallion(W * (IS_SHORT ? 0.42 : 0.46), H * (IS_SHORT ? 0.68 : 0.68), sc * 0.84);
    drawFacelessPresenter(W * (IS_SHORT ? 0.78 : 0.76), H * (IS_SHORT ? 0.86 : 0.90), sc * 0.98, 'dua', t);
  }}

  let cur = CFG.scenes[CFG.scenes.length - 1];
  for (const s of CFG.scenes) {{
    if (t >= s.start && t <= s.end) {{ cur = s; break; }}
  }}

  const pillTag = document.getElementById('pillTag');
  const headEl = document.getElementById('headline');
  const miniCit = document.getElementById('miniCit');
  const arRibbon = document.getElementById('arRibbon');
  const climaxPaper = document.getElementById('climaxPaper');
  const arWin = CFG.arabic_window;

  if (act.name === 'HOOK') {{
    arRibbon.style.display = 'none';
    climaxPaper.style.display = 'none';
    pillTag.textContent = 'ACT 1 • ' + (STORY.hook_kicker || 'THE HOOK');
    pillTag.style.background = '#B91C1C';
    headEl.textContent = (CFG.scenes[0] && CFG.scenes[0].headline) || CFG.dalil.topic;
    miniCit.textContent = '';
  }} else if (act.name === 'DALIL') {{
    arRibbon.style.display = 'block';
    climaxPaper.style.display = 'none';
    pillTag.textContent = (arWin && arWin.is_qari) ? `ACT 2 • TILAWAH` : 'ACT 2 • VERIFIED HADITH';
    pillTag.style.background = '#B45309';
    headEl.textContent = CFG.dalil.citation;
    miniCit.textContent = '';
  }} else if (act.name === 'EXPLAINER') {{
    arRibbon.style.display = 'none';
    climaxPaper.style.display = 'none';
    pillTag.textContent = 'ACT 3 • THE SCIENCE';
    pillTag.style.background = '#0F766E';
    headEl.textContent = (cur && cur.headline) || 'WHY IT WORKS';
    miniCit.textContent = '✦  ' + CFG.dalil.citation + '  ✦';
  }} else {{
    arRibbon.style.display = 'none';
    climaxPaper.style.display = 'block';
    pillTag.textContent = 'ACT 4 • THE LESSON';
    pillTag.style.background = '#1E2F42';
    headEl.textContent = (cur && cur.headline) || 'DAILY SUNNAH';
    miniCit.textContent = '';
  }}

  let cap = null;
  for (const c of CFG.captions) {{
    if (t >= c.start - 0.06 && t <= c.end + 0.14) {{ cap = c; break; }}
  }}
  const subPaper = document.getElementById('subPaper');
  const subText = document.getElementById('subText');
  if (act.name === 'DALIL') {{
    subPaper.style.opacity = '1';
    subText.innerHTML = `<span class="hi" style="font-style:italic">"${{CFG.dalil.translation}}"</span>`;
  }} else if (cap && cap.words && cap.words.length) {{
    subPaper.style.opacity = '1';
    subText.innerHTML = cap.words.map(w => {{
      const isSpoken = t >= w.s && t <= w.e + 0.12;
      return isSpoken ? `<span class="hi">${{w.w}}</span>` : w.w;
    }}).join(' ');
  }} else {{
    subPaper.style.opacity = '0';
  }}
}};
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Format 6 (Ref #6 Hadith Qudsi Ocean Metaphor): `islamic_cinematic_metaphor`
# ACT 1: Full-Bleed Sunlit Ocean Needle (ZERO Arabic spoiler!)
# ACT 2: Midnight Moonlit Ocean + Center-Stage Sacred Arabic Reveal
# ACT 3: Endless Twilight Plain & Mirror Ripples + Animated Mind Explainer Card
# ACT 4: Radiant Rose-Gold Sunset Clouds + Unmistakable Core Lesson Card!
# ---------------------------------------------------------------------------

def build_cinematic_metaphor_html(payload: dict[str, Any], font_css: str, width: int, height: int) -> str:
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
    background: #08121E;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    color: #FFFFFF;
  }}
  #bgCanvas {{ position: absolute; inset: 0; width: {width}px; height: {height}px; display: block; }}

  .top-head {{
    position: absolute; top: {56 if is_short else 18}px; left: 32px; right: 32px;
    z-index: 6; text-align: center; pointer-events: none;
    display: flex; flex-direction: column; align-items: center;
  }}
  .act-chip {{
    display: inline-block; padding: 5px 18px; border-radius: 999px;
    background: rgba(6, 12, 22, 0.70);
    border: 1.5px solid rgba(253, 224, 130, 0.55);
    font-size: 13px; font-weight: 800; letter-spacing: 2.2px; color: #FDE68A;
    text-transform: uppercase; margin-bottom: 8px;
  }}
  .hook-head {{
    font-size: {36 if is_short else 30}px; font-weight: 900; line-height: 1.15;
    text-transform: uppercase; color: #FFFFFF;
    max-width: {640 if is_short else 960}px;
    text-shadow: 0 3px 18px rgba(0,0,0,0.85);
  }}
  .mini-cit {{
    margin-top: 4px; font-size: 12px; font-weight: 700; letter-spacing: 2px;
    color: #FDE68A; text-shadow: 0 2px 8px rgba(0,0,0,0.85);
  }}

  /* ACT 2 ONLY: Center-stage Sacred Arabic Spotlight */
  .dalil-spotlight {{
    position: absolute; left: 50%; transform: translateX(-50%);
    top: {246 if is_short else 142}px;
    z-index: 7; width: {640 if is_short else 900}px;
    background: rgba(7, 15, 28, 0.80);
    border: 2px solid rgba(253, 224, 130, 0.72);
    border-radius: 22px;
    padding: {24 if is_short else 16}px 28px;
    text-align: center;
    box-shadow: 0 0 38px rgba(253, 224, 130, 0.25), 0 16px 36px rgba(0,0,0,0.55);
    display: none;
  }}
  .ar-float {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; unicode-bidi: embed;
    font-size: {48 if is_short else 38}px; font-weight: 700; line-height: 1.54;
    color: #FFFDF7;
    text-shadow: 0 2px 16px rgba(253, 224, 130, 0.40);
    margin-bottom: 10px;
  }}
  .tr-float {{
    font-family: 'Georgia', serif; font-size: {21 if is_short else 18}px;
    color: #FDE68A; margin-bottom: 8px;
  }}
  .cit-pill {{
    display: inline-block; padding: 4px 16px; border-radius: 999px;
    background: rgba(253, 224, 130, 0.16);
    border: 1px solid rgba(253, 224, 130, 0.55);
    font-size: 13px; font-weight: 800; letter-spacing: 2.2px; color: #FDE68A;
    text-transform: uppercase;
  }}

  /* ACT 4 ONLY: Sunset Core Lesson Takeaway Card */
  .climax-card {{
    position: absolute; left: 50%; transform: translateX(-50%);
    top: {240 if is_short else 144}px;
    z-index: 7; width: {620 if is_short else 840}px;
    background: rgba(16, 12, 34, 0.82);
    border: 2px solid rgba(253, 224, 130, 0.80);
    border-radius: 22px;
    padding: {24 if is_short else 16}px 28px;
    text-align: center;
    box-shadow: 0 0 42px rgba(251, 191, 36, 0.28), 0 18px 38px rgba(0,0,0,0.55);
    display: none;
  }}
  .climax-kicker {{
    font-size: 14px; font-weight: 900; letter-spacing: 3px; color: #FDE68A;
    text-transform: uppercase; margin-bottom: 10px;
  }}
  .climax-lesson {{
    font-size: {34 if is_short else 29}px; font-weight: 900; line-height: 1.24;
    color: #FFFFFF; margin-bottom: 14px;
  }}

  /* Ref #6 crisp centered white-outlined subtitles kept strictly clear of center action stage */
  .sub-center {{
    position: absolute; left: 32px; right: 32px;
    top: {76 if is_short else 82}%;
    transform: translateY(-50%);
    z-index: 9; text-align: center; pointer-events: none;
  }}
  #subText {{
    display: inline-block; max-width: {630 if is_short else 980}px;
    font-size: {36 if is_short else 32}px; font-weight: 800; line-height: 1.24;
    color: #FFFFFF;
    -webkit-text-stroke: 2.2px rgba(6, 10, 18, 0.94);
    paint-order: stroke fill;
    text-shadow: 0 4px 18px rgba(0,0,0,0.88);
  }}
  #subText .gold {{ color: #FDE68A; }}

  .brand-foot {{
    position: absolute; bottom: {28 if is_short else 10}px; left: 0; right: 0;
    z-index: 9; text-align: center;
    font-size: 13px; font-weight: 600; letter-spacing: 2.4px;
    color: rgba(255,255,255,0.68); text-shadow: 0 2px 8px rgba(0,0,0,0.8);
  }}
</style>
</head>
<body>
<canvas id="bgCanvas" width="{width}" height="{height}"></canvas>

<div class="top-head">
  <div class="act-chip" id="actChip">ACT 1 • HOOK</div>
  <div class="hook-head" id="hookHead"></div>
  <div class="mini-cit" id="miniCit"></div>
</div>

<div class="dalil-spotlight" id="dalilSpotlight">
  <div class="ar-float" id="arFloat"></div>
  <div class="tr-float" id="trFloat"></div>
  <div class="cit-pill" id="citPill"></div>
</div>

<div class="climax-card" id="climaxCard">
  <div class="climax-kicker">✦  THE LESSON  ✦</div>
  <div class="climax-lesson" id="climaxLesson"></div>
  <div class="cit-pill" id="climaxCit"></div>
</div>

<div class="sub-center"><div id="subText"></div></div>
<div class="brand-foot" id="brandFoot"></div>

<script>
const CFG = {cfg_json};
const W = {width}, H = {height};
const IS_SHORT = H >= W;
const ctx = document.getElementById('bgCanvas').getContext('2d');
const STORY = CFG.story_acts || {{}};

{STORY_ACTS_JS}

const ACTS = computeFourActTiming(CFG);

document.getElementById('citPill').textContent = '✦  ' + CFG.dalil.citation + '  ✦';
document.getElementById('arFloat').textContent = CFG.dalil.arabic;
document.getElementById('trFloat').textContent = CFG.dalil.transliteration;
document.getElementById('climaxLesson').textContent = STORY.core_lesson || CFG.dalil.translation;
document.getElementById('climaxCit').textContent = '✦  ' + CFG.dalil.citation + '  •  SAVE & SHARE  ✦';
document.getElementById('brandFoot').textContent = CFG.dalil.handle + '  •  REFLECTIVE WISDOM';

const PLAIN_FIGS = [];
for (let i = 0; i < 160; i++) {{
  const row = (i % 16) / 15;
  PLAIN_FIGS.push({{ x: ((i * 197.7 + (i % 5) * 43) % 1000) / 1000, depth: row, luminous: (i % 17 === 0), ph: i * 0.7 }});
}}
const STARS = [];
for (let i = 0; i < 95; i++) {{
  STARS.push({{ x: ((i * 211.3) % 1000) / 1000, y: ((i * 349.1) % 620) / 1000, r: 0.9 + (i % 4) * 0.45, ph: i * 1.1 }});
}}

function drawNeedleOceanShot(lt, t) {{
  const horY = H * 0.36;
  const skyG = ctx.createLinearGradient(0, 0, 0, horY + 30);
  skyG.addColorStop(0, '#4A4E57'); skyG.addColorStop(0.58, '#C8B998'); skyG.addColorStop(1, '#FCE7A2');
  ctx.fillStyle = skyG; ctx.fillRect(0, 0, W, horY + 30);

  const seaG = ctx.createLinearGradient(0, horY, 0, H);
  seaG.addColorStop(0, '#D4C99E'); seaG.addColorStop(0.22, '#6BA8B2');
  seaG.addColorStop(0.65, '#3E7B8C'); seaG.addColorStop(1, '#1E4658');
  ctx.fillStyle = seaG; ctx.fillRect(0, horY, W, H - horY);

  for (let i = 0; i < 42; i++) {{
    const p = Math.pow(i / 42, 1.55);
    const wy = horY + p * (H - horY);
    const shift = Math.sin(t * 1.6 + i * 0.7) * (12 + p * 28);
    ctx.fillStyle = `rgba(254, 240, 192, ${{0.30 * (1 - p * 0.55)}})`;
    ctx.fillRect(W * 0.08 + shift, wy, W * 0.84, 2 + p * 7);
  }}

  const tipY = H * (IS_SHORT ? 0.42 : 0.44) + Math.sin(t * 1.2) * 8;
  const nGrad = ctx.createLinearGradient(W * 0.5 - 16, 0, W * 0.5 + 16, 0);
  nGrad.addColorStop(0, 'rgba(190, 224, 240, 0.75)');
  nGrad.addColorStop(0.5, 'rgba(255, 255, 255, 0.98)');
  nGrad.addColorStop(1, 'rgba(170, 205, 225, 0.70)');
  ctx.fillStyle = nGrad;
  ctx.beginPath();
  ctx.moveTo(W * 0.5 - 15, H * 0.16); ctx.lineTo(W * 0.5 + 15, H * 0.16);
  ctx.lineTo(W * 0.5 + 12, tipY - 68); ctx.lineTo(W * 0.5, tipY);
  ctx.lineTo(W * 0.5 - 12, tipY - 68); ctx.closePath(); ctx.fill();

  const dropY = tipY + 36 + Math.sin(t * 1.8) * 5;
  const glow = ctx.createRadialGradient(W * 0.5, dropY, 4, W * 0.5, dropY, 74);
  glow.addColorStop(0, 'rgba(255, 252, 236, 0.96)');
  glow.addColorStop(0.36, 'rgba(254, 232, 168, 0.42)');
  glow.addColorStop(1, 'rgba(254, 232, 168, 0)');
  ctx.fillStyle = glow; ctx.fillRect(W * 0.5 - 78, dropY - 78, 156, 156);
  ctx.fillStyle = '#FFFDF5';
  ctx.beginPath(); ctx.arc(W * 0.5, dropY, 24, 0, Math.PI * 2); ctx.fill();
}}

function drawDeepOceanVistaShot(lt, t) {{
  const horY = H * 0.44;
  const skyG = ctx.createLinearGradient(0, 0, 0, horY);
  skyG.addColorStop(0, '#16223C'); skyG.addColorStop(1, '#2D4164');
  ctx.fillStyle = skyG; ctx.fillRect(0, 0, W, horY + 4);
  for (const st of STARS) {{
    const tw = 0.45 + 0.55 * Math.sin(t * 1.8 + st.ph);
    ctx.fillStyle = `rgba(255,255,255,${{0.65 * tw}})`;
    ctx.beginPath(); ctx.arc(st.x * W, st.y * horY, st.r, 0, Math.PI * 2); ctx.fill();
  }}
  const seaG = ctx.createLinearGradient(0, horY, 0, H);
  seaG.addColorStop(0, '#172947'); seaG.addColorStop(0.55, '#1D3354'); seaG.addColorStop(1, '#0F1C32');
  ctx.fillStyle = seaG; ctx.fillRect(0, horY, W, H - horY);
  for (let i = 0; i < 28; i++) {{
    const p = i / 28;
    const wy = horY + 18 + Math.pow(p, 1.35) * (H - horY);
    const drift = Math.sin(t * 1.1 + i * 0.6) * 24;
    ctx.strokeStyle = `rgba(148, 184, 224, ${{0.14 + 0.12 * p}})`;
    ctx.lineWidth = 2 + p * 8;
    ctx.beginPath(); ctx.moveTo(-40 + drift, wy - 28); ctx.lineTo(W + 40 + drift, wy + 52); ctx.stroke();
  }}
}}

function drawEndlessPlainShot(lt, t) {{
  const horY = H * 0.24;
  const skyG = ctx.createLinearGradient(0, 0, 0, horY + 40);
  skyG.addColorStop(0, '#182438'); skyG.addColorStop(1, '#3B4A5E');
  ctx.fillStyle = skyG; ctx.fillRect(0, 0, W, horY + 40);
  const pG = ctx.createLinearGradient(0, horY, 0, H);
  pG.addColorStop(0, '#4A5154'); pG.addColorStop(0.45, '#5E6566'); pG.addColorStop(1, '#2D343B');
  ctx.fillStyle = pG; ctx.fillRect(0, horY, W, H - horY);
  for (const fg of PLAIN_FIGS) {{
    const p = Math.pow(fg.depth, 1.4);
    const fy = horY + 24 + p * (H - horY - 56);
    const fx = fg.x * W; const h = 10 + p * 26;
    ctx.fillStyle = fg.luminous ? '#F8FAFC' : 'rgba(22, 30, 42, 0.78)';
    ctx.beginPath(); ctx.arc(fx, fy - h, h * 0.16, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = fg.luminous ? '#F8FAFC' : 'rgba(22, 30, 42, 0.78)';
    ctx.lineWidth = Math.max(1.2, h * 0.08);
    ctx.beginPath(); ctx.moveTo(fx, fy - h * 0.84); ctx.lineTo(fx, fy - h * 0.28);
    ctx.moveTo(fx, fy - h * 0.28); ctx.lineTo(fx - h * 0.18, fy);
    ctx.moveTo(fx, fy - h * 0.28); ctx.lineTo(fx + h * 0.18, fy); ctx.stroke();
  }}
}}

function drawMirrorRippleShot(lt, t) {{
  const bg = ctx.createRadialGradient(W * 0.5, H * 0.52, 12, W * 0.5, H * 0.52, Math.max(W, H) * 0.7);
  bg.addColorStop(0, '#1A344D'); bg.addColorStop(1, '#070E19');
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
  const cy = H * 0.62;
  for (let r = 0; r < 6; r++) {{
    const cyc = (t * 0.42 + r / 6) % 1.0;
    ctx.strokeStyle = `rgba(253, 224, 130, ${{(1 - cyc) * 0.52}})`;
    ctx.lineWidth = 2.4 * (1 - cyc * 0.5);
    ctx.beginPath(); ctx.ellipse(W * 0.5, cy, 18 + cyc * W * 0.46, 6 + cyc * H * 0.12, 0, 0, Math.PI * 2); ctx.stroke();
  }}
}}

function drawWarmSunsetCloudsShot(lt, t) {{
  const sunX = W * 0.52;
  const sunY = H * (IS_SHORT ? 0.70 : 0.68) - Math.sin(t * 0.3) * 14;
  const bg = ctx.createLinearGradient(0, 0, 0, H);
  bg.addColorStop(0, '#2B2B6E'); bg.addColorStop(0.42, '#73578E');
  bg.addColorStop(0.72, '#D0838C'); bg.addColorStop(1, '#F0B484');
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
  const orb = ctx.createRadialGradient(sunX, sunY, 12, sunX, sunY, W * 0.58);
  orb.addColorStop(0, 'rgba(255, 250, 214, 0.98)'); orb.addColorStop(0.24, 'rgba(255, 212, 134, 0.72)');
  orb.addColorStop(0.58, 'rgba(232, 134, 138, 0.28)'); orb.addColorStop(1, 'rgba(43, 43, 110, 0)');
  ctx.fillStyle = orb; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 14; i++) {{
    const cx = ((i * 193 + t * (7 + (i % 3) * 4)) % (W + 260)) - 130;
    const cy = H * (0.28 + (i % 6) * 0.11); const rr = 75 + (i % 4) * 32;
    const cg = ctx.createRadialGradient(cx, cy, 8, cx, cy, rr);
    cg.addColorStop(0, i > 6 ? 'rgba(255, 206, 172, 0.28)' : 'rgba(130, 96, 152, 0.24)');
    cg.addColorStop(1, 'rgba(255, 206, 172, 0)');
    ctx.fillStyle = cg; ctx.fillRect(cx - rr, cy - rr, rr * 2, rr * 2);
  }}
}}

window.renderAt = function(t) {{
  const act = getCurrentAct(t, ACTS);
  const pal = {{
    bgCard: 'rgba(7, 15, 28, 0.86)',
    border: 'rgba(253, 224, 130, 0.65)',
    ink: '#F8FAFC',
    muted: '#94A3B8',
    accent: '#FDE68A',
    good: '#34D399',
    light: false,
  }};

  // Choreograph atmospheric shots cleanly to each of the 4 Acts!
  if (act.name === 'HOOK') {{
    drawNeedleOceanShot(act.localT, t);
    if (STORY.hook_visual && STORY.hook_visual !== 'needle_ocean') {{
      drawAct1HookVisual(ctx, STORY.hook_visual, W * 0.5, H * (IS_SHORT ? 0.44 : 0.46), IS_SHORT ? 1.05 : 0.84, act.localT, t, pal);
    }}
  }} else if (act.name === 'DALIL') {{
    drawDeepOceanVistaShot(act.localT, t);
  }} else if (act.name === 'EXPLAINER') {{
    if (act.localT < 0.50) drawEndlessPlainShot(act.localT * 2, t);
    else drawMirrorRippleShot((act.localT - 0.50) * 2, t);
    drawAct3ExplainerVisual(ctx, STORY, W * 0.5, H * (IS_SHORT ? 0.42 : 0.45), IS_SHORT ? 1.04 : 0.86, act.localT, t, pal);
  }} else {{
    drawWarmSunsetCloudsShot(act.localT, t);
  }}

  // Top scrim for crisp legibility
  const topV = ctx.createLinearGradient(0, 0, 0, H * 0.24);
  topV.addColorStop(0, 'rgba(6, 10, 18, 0.62)'); topV.addColorStop(1, 'rgba(6, 10, 18, 0)');
  ctx.fillStyle = topV; ctx.fillRect(0, 0, W, H * 0.24);

  let cur = CFG.scenes[CFG.scenes.length - 1];
  for (const s of CFG.scenes) {{
    if (t >= s.start && t <= s.end) {{ cur = s; break; }}
  }}

  const actChip = document.getElementById('actChip');
  const hookHead = document.getElementById('hookHead');
  const miniCit = document.getElementById('miniCit');
  const dalilSpot = document.getElementById('dalilSpotlight');
  const climaxCard = document.getElementById('climaxCard');
  const arWin = CFG.arabic_window;

  if (act.name === 'HOOK') {{
    dalilSpot.style.display = 'none';
    climaxCard.style.display = 'none';
    actChip.textContent = 'ACT 1 • ' + (STORY.hook_kicker || 'PICTURE THIS');
    hookHead.textContent = (CFG.scenes[0] && CFG.scenes[0].headline) || CFG.dalil.topic;
    miniCit.textContent = '';
  }} else if (act.name === 'DALIL') {{
    dalilSpot.style.display = 'block';
    climaxCard.style.display = 'none';
    actChip.textContent = (arWin && arWin.is_qari) ? `ACT 2 • TILAWAH (${{arWin.reciter}})` : 'ACT 2 • SACRED WISDOM';
    hookHead.textContent = CFG.dalil.citation;
    miniCit.textContent = '';
  }} else if (act.name === 'EXPLAINER') {{
    dalilSpot.style.display = 'none';
    climaxCard.style.display = 'none';
    actChip.textContent = 'ACT 3 • THE MIND SHIFT';
    hookHead.textContent = (cur && cur.headline) || 'HOW IT TRANSFORMS YOU';
    miniCit.textContent = '✦  ' + CFG.dalil.citation + '  ✦';
  }} else {{
    dalilSpot.style.display = 'none';
    climaxCard.style.display = 'block';
    actChip.textContent = 'ACT 4 • THE LESSON';
    hookHead.textContent = (cur && cur.headline) || 'QUIET SURRENDER';
    miniCit.textContent = '';
  }}

  let cap = null;
  for (const c of CFG.captions) {{
    if (t >= c.start - 0.06 && t <= c.end + 0.14) {{ cap = c; break; }}
  }}
  const subEl = document.getElementById('subText');
  if (act.name === 'DALIL') {{
    subEl.innerHTML = `<span class="gold" style="font-style:italic">"${{CFG.dalil.translation}}"</span>`;
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
