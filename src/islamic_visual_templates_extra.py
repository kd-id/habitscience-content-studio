"""Studio v10 Extended Visual Templates — Ref #1 (Nature Transform), Ref #3 (Paper-Cutout 3D), Ref #6 (Cinematic Metaphor).

All 3 engines:
  - Support BOTH 9:16 (720x1280 -> 1080x1920) AND 16:9 (1280x720 -> 1920x1080)
  - Embed OFL Amiri Arabic Calligraphy with crisp RTL harakat
  - Sync live with `arabic_window` (Mishary Alafasy real Qari / Saudi Arabic VO) + English word karaoke
  - Avoid slow software `backdrop-filter: blur()` so headless Chromium renders steadily at 12-15 fps
  - Strictly respect Islamic adab (ZERO depiction of Prophets; Ref #3 presenter has zero facial features).
"""

from __future__ import annotations

import json
from typing import Any


# ---------------------------------------------------------------------------
# Format 1 (Ref #1 Minute Wisdom): `islamic_nature_transform`
# Hexagonal Cracked Fire Earth -> Extinguishing Steam -> Raindrop Pool -> Blooming Trees & Meadow
# ---------------------------------------------------------------------------

def build_nature_transform_html(payload: dict[str, Any], font_css: str, width: int, height: int) -> str:
    cfg_json = json.dumps(payload, ensure_ascii=False)
    is_short = height >= width
    top_pad = 92 if is_short else 24
    ar_size = 58 if is_short else 44
    tr_size = 24 if is_short else 20
    en_size = 21 if is_short else 18
    sub_size = 32 if is_short else 28

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

  .header-stage {{
    position: absolute; top: {top_pad}px; left: 32px; right: 32px;
    z-index: 6; display: flex; flex-direction: column; align-items: center; text-align: center;
    pointer-events: none;
  }}
  .ar-title {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; unicode-bidi: embed;
    font-size: {ar_size}px; font-weight: 700; line-height: 1.52;
    max-width: {650 if is_short else 980}px;
    margin-bottom: {10 if is_short else 4}px;
  }}
  .tr-sub {{
    font-family: 'Georgia', serif;
    font-size: {tr_size}px; font-weight: 600; line-height: 1.3;
    max-width: {640 if is_short else 920}px;
    margin-bottom: 5px;
  }}
  .en-sub {{
    font-family: 'Georgia', serif; font-style: italic;
    font-size: {en_size}px; line-height: 1.32;
    max-width: {640 if is_short else 900}px;
    margin-bottom: {14 if is_short else 8}px;
  }}
  .dots-row {{
    display: inline-flex; align-items: center; gap: 10px;
    margin-bottom: 5px;
  }}
  .pdot {{
    width: 12px; height: 12px; border-radius: 50%;
    border: 2px solid rgba(255,255,255,0.45);
    background: transparent;
  }}
  .pdot.done {{
    background: #34D399; border-color: #10B981;
    box-shadow: 0 0 10px rgba(52, 211, 153, 0.85);
  }}
  .pdot.active {{
    background: #6EE7B7; border-color: #FFFFFF; transform: scale(1.22);
    box-shadow: 0 0 14px rgba(110, 231, 183, 0.95);
  }}
  .counter-txt {{
    font-family: 'Segoe UI', sans-serif; font-size: 16px; font-weight: 700;
    letter-spacing: 2px;
  }}
  .cit-chip {{
    margin-top: 6px; padding: 3px 14px; border-radius: 999px;
    font-family: 'Segoe UI', sans-serif; font-size: 12px; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase;
  }}

  .sub-area {{
    position: absolute; left: 28px; right: 28px;
    bottom: {96 if is_short else 34}px;
    z-index: 8; text-align: center;
  }}
  .sub-card {{
    display: inline-block; max-width: {640 if is_short else 960}px;
    padding: 10px 22px; border-radius: 14px;
    background: rgba(9, 14, 24, 0.72);
    border: 1px solid rgba(255,255,255,0.18);
    box-shadow: 0 8px 24px rgba(0,0,0,0.40);
  }}
  #subText {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: {sub_size}px; font-weight: 700; line-height: 1.26; color: #FFFFFF;
  }}
  #subText .hi {{ color: #6EE7B7; }}

  .brand-foot {{
    position: absolute; bottom: {26 if is_short else 10}px; left: 0; right: 0;
    z-index: 9; text-align: center;
    font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 700; letter-spacing: 2px;
    text-shadow: 0 2px 6px rgba(0,0,0,0.65); color: rgba(255,255,255,0.82);
  }}
</style>
</head>
<body>
<canvas id="bgCanvas" width="{width}" height="{height}"></canvas>

<div class="header-stage" id="headerStage">
  <div class="ar-title" id="arTitle"></div>
  <div class="tr-sub" id="trSub"></div>
  <div class="en-sub" id="enSub"></div>
  <div class="dots-row" id="dotsRow"></div>
  <div class="counter-txt" id="counterTxt">1 / 7</div>
  <div class="cit-chip" id="citChip"></div>
</div>

<div class="sub-area"><div class="sub-card" id="subCard"><div id="subText"></div></div></div>
<div class="brand-foot" id="brandFoot"></div>

<script>
const CFG = {cfg_json};
const W = {width}, H = {height};
const IS_SHORT = H >= W;
const ctx = document.getElementById('bgCanvas').getContext('2d');

document.getElementById('arTitle').textContent = CFG.dalil.arabic;
document.getElementById('trSub').textContent = CFG.dalil.transliteration;
document.getElementById('enSub').textContent = CFG.dalil.translation;
document.getElementById('citChip').textContent = '✦  ' + CFG.dalil.citation + '  ✦';
document.getElementById('brandFoot').textContent = CFG.dalil.handle + '  •  MINUTE WISDOM & SUNNAH';

const TOTAL_DOTS = 7;
const dotsRow = document.getElementById('dotsRow');
for (let i = 0; i < TOTAL_DOTS; i++) {{
  const d = document.createElement('span');
  d.className = 'pdot';
  dotsRow.appendChild(d);
}}

// Deterministic flames, wildflowers, clouds
const FLAMES = [];
for (let i = 0; i < 64; i++) {{
  const row = (i % 8) / 7;
  FLAMES.push({{
    x: ((i * 157.3 + (i % 3) * 41) % 1000) / 1000,
    depth: row,
    sz: 12 + row * 34 + (i % 4) * 5,
    ph: i * 0.87,
    extinguishAt: 0.10 + ((i * 37) % 100) / 100 * 0.36,
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
    appearAt: 0.48 + (i % 20) * 0.014,
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
  // Outer orange flame
  ctx.fillStyle = `rgba(234, 88, 12, ${{0.92 * alpha}})`;
  ctx.beginPath();
  ctx.moveTo(-sz * 0.44, 0);
  ctx.quadraticCurveTo(-sz * 0.5, -h * 0.55, flick, -h);
  ctx.quadraticCurveTo(sz * 0.5, -h * 0.55, sz * 0.44, 0);
  ctx.closePath();
  ctx.fill();
  // Inner yellow core
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
  // Trunk
  ctx.fillStyle = '#6B4423';
  ctx.fillRect(-10 * s, -120 * s, 20 * s, 122 * s);
  ctx.fillStyle = '#533319';
  ctx.fillRect(0, -120 * s, 10 * s, 122 * s);
  // Puff canopy clusters
  const puffs = [[-36, -134, 34], [34, -132, 32], [-18, -164, 38], [22, -162, 36], [0, -142, 42]];
  ctx.fillStyle = canopyColor;
  for (const [px, py, pr] of puffs) {{
    ctx.beginPath();
    ctx.arc(px * s + sway, py * s, pr * s, 0, Math.PI * 2);
    ctx.fill();
  }}
  // Tiny blossoms / fruits
  ctx.fillStyle = accentColor;
  for (const [fx, fy] of [[-24, -145], [14, -168], [30, -128], [-6, -124], [8, -146]]) {{
    ctx.beginPath();
    ctx.arc(fx * s + sway, fy * s, 4.5 * s, 0, Math.PI * 2);
    ctx.fill();
  }}
  ctx.restore();
}}

window.renderAt = function(t) {{
  const total = Math.max(CFG.total_dur, 1);
  const progress = Math.min(Math.max(t / total, 0), 1);
  const horizonY = H * (IS_SHORT ? 0.56 : 0.60);

  // Smooth sky transition: Smoky Fire Orange (0..0.38) -> Cool Storm Gray (0.38..0.55) -> Bright Sky Blue & Cream Horizon (0.55..1.0)
  let topC, midC, botC;
  if (progress < 0.36) {{
    const u = progress / 0.36;
    topC = lerpRGB([44, 16, 10], [42, 34, 34], u);
    midC = lerpRGB([112, 44, 18], [76, 62, 58], u);
    botC = lerpRGB([176, 82, 28], [108, 96, 92], u);
  }} else if (progress < 0.58) {{
    const u = (progress - 0.36) / 0.22;
    topC = lerpRGB([42, 34, 34], [116, 178, 224], u);
    midC = lerpRGB([76, 62, 58], [174, 214, 236], u);
    botC = lerpRGB([108, 96, 92], [242, 236, 198], u);
  }} else {{
    const u = (progress - 0.58) / 0.42;
    topC = lerpRGB([116, 178, 224], [124, 188, 234], u);
    midC = lerpRGB([174, 214, 236], [198, 228, 240], u);
    botC = lerpRGB([242, 236, 198], [248, 243, 210], u);
  }}

  const skyG = ctx.createLinearGradient(0, 0, 0, horizonY);
  skyG.addColorStop(0, rgb(topC));
  skyG.addColorStop(0.6, rgb(midC));
  skyG.addColorStop(1, rgb(botC));
  ctx.fillStyle = skyG;
  ctx.fillRect(0, 0, W, horizonY + 12);

  // Adaptive Ref #1 typography contrast: warm cream on dark fire sky -> crisp deep slate on bright blue meadow sky!
  const lightSky = Math.min(Math.max((progress - 0.42) / 0.16, 0), 1);
  const txtC = lerpRGB([250, 246, 238], [22, 34, 48], lightSky);
  const subC = lerpRGB([226, 216, 204], [52, 68, 86], lightSky);
  const hdr = document.getElementById('headerStage');
  hdr.style.color = rgb(txtC);
  document.getElementById('arTitle').style.color = rgb(txtC);
  document.getElementById('trSub').style.color = rgb(txtC);
  document.getElementById('enSub').style.color = rgb(subC);
  document.getElementById('counterTxt').style.color = rgb(txtC);
  const chip = document.getElementById('citChip');
  chip.style.color = lightSky > 0.5 ? '#0F5132' : '#FDE68A';
  chip.style.background = lightSky > 0.5 ? 'rgba(16, 185, 129, 0.16)' : 'rgba(253, 224, 71, 0.16)';
  chip.style.border = lightSky > 0.5 ? '1px solid rgba(16, 185, 129, 0.45)' : '1px solid rgba(253, 224, 71, 0.42)';

  // Soft white clouds drifting in meadow stage
  if (progress > 0.44) {{
    const clA = Math.min((progress - 0.44) / 0.18, 0.85);
    ctx.fillStyle = `rgba(255, 255, 255, ${{clA}})`;
    for (const [cx0, cy, r] of [[0.18, 0.46, 26], [0.76, 0.43, 30], [0.50, 0.49, 22]]) {{
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
  const hillCol = lerpRGB([46, 32, 26], [108, 166, 118], Math.min(Math.max((progress - 0.36) / 0.24, 0), 1));
  ctx.fillStyle = rgb(hillCol);
  ctx.beginPath();
  ctx.moveTo(0, horizonY + 8);
  ctx.quadraticCurveTo(W * 0.25, horizonY - 28, W * 0.52, horizonY - 8);
  ctx.quadraticCurveTo(W * 0.78, horizonY - 34, W, horizonY - 6);
  ctx.lineTo(W, H);
  ctx.lineTo(0, H);
  ctx.closePath();
  ctx.fill();

  // Foreground ground: dark scorched earth -> vibrant green meadow!
  const grassMix = Math.min(Math.max((progress - 0.40) / 0.18, 0), 1);
  const gTop = lerpRGB([28, 22, 20], [122, 186, 86], grassMix);
  const gBot = lerpRGB([14, 10, 10], [74, 146, 58], grassMix);
  const gGrad = ctx.createLinearGradient(0, horizonY, 0, H);
  gGrad.addColorStop(0, rgb(gTop));
  gGrad.addColorStop(1, rgb(gBot));
  ctx.fillStyle = gGrad;
  ctx.fillRect(0, horizonY, W, H - horizonY);

  // Hexagonal cracked earth fading out as grass blooms
  drawHexCracks(horizonY, 1 - grassMix);

  // Stage 1: Stylized flames extinguishing with soft white steam wisps
  if (progress < 0.48) {{
    for (const fl of FLAMES) {{
      const fy = horizonY + 22 + fl.depth * (H - horizonY - 40);
      const fx = fl.x * W;
      if (progress < fl.extinguishAt) {{
        const a = Math.min(1, (fl.extinguishAt - progress) / 0.08);
        drawFlame(fx, fy, fl.sz, t, fl.ph, a);
      }} else if (progress < fl.extinguishAt + 0.12) {{
        const sm = 1 - (progress - fl.extinguishAt) / 0.12;
        ctx.fillStyle = `rgba(220, 226, 234, ${{0.28 * sm}})`;
        ctx.beginPath();
        ctx.arc(fx + Math.sin(t * 2 + fl.ph) * 8, fy - (1 - sm) * 44, fl.sz * 0.55, 0, Math.PI * 2);
        ctx.fill();
      }}
    }}
  }}

  // Stage 2: Iconic Ref #1 falling blue teardrop into glowing meadow pool!
  const poolX = W * 0.5, poolY = horizonY + (H - horizonY) * (IS_SHORT ? 0.36 : 0.40);
  if (progress > 0.34) {{
    const poolGrow = Math.min((progress - 0.34) / 0.18, 1);
    const rx = (IS_SHORT ? 84 : 96) * poolGrow;
    const ry = (IS_SHORT ? 26 : 24) * poolGrow;
    // Soft pool edge
    ctx.fillStyle = '#8C7A65';
    ctx.beginPath();
    ctx.ellipse(poolX, poolY, rx + 5, ry + 3, 0, 0, Math.PI * 2);
    ctx.fill();
    // Sky-blue pool water
    const pg = ctx.createRadialGradient(poolX, poolY - 4, 4, poolX, poolY, rx);
    pg.addColorStop(0, '#93D5FA');
    pg.addColorStop(1, '#3B82B6');
    ctx.fillStyle = pg;
    ctx.beginPath();
    ctx.ellipse(poolX, poolY, rx, ry, 0, 0, Math.PI * 2);
    ctx.fill();

    // Water ripples inside pool
    const rip = (t * 0.8) % 1.0;
    ctx.strokeStyle = `rgba(255,255,255,${{(1 - rip) * 0.65}})`;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.ellipse(poolX, poolY, 10 + rip * rx * 0.72, 4 + rip * ry * 0.72, 0, 0, Math.PI * 2);
    ctx.stroke();

    // Falling teardrop between 0.36..0.72
    if (progress < 0.76) {{
      const dropCyc = (t * 0.72) % 1.0;
      const dy = lerp(horizonY - 95, poolY - 6, dropCyc * dropCyc);
      ctx.fillStyle = '#7DD3FC';
      ctx.beginPath();
      ctx.moveTo(poolX, dy - 22);
      ctx.bezierCurveTo(poolX + 12, dy - 2, poolX + 11, dy + 10, poolX, dy + 10);
      ctx.bezierCurveTo(poolX - 11, dy + 10, poolX - 12, dy - 2, poolX, dy - 22);
      ctx.fill();
    }}
  }}

  // Stage 3: Blooming wildflowers & fruit + cherry blossom trees (exact Ref #1 frame 6!)
  if (progress > 0.48) {{
    for (const fw of FLOWERS) {{
      if (progress < fw.appearAt) continue;
      const a = Math.min((progress - fw.appearAt) / 0.08, 1);
      const fx = fw.x * W;
      const fy = horizonY + 14 + fw.y * (H - horizonY - 26);
      if (Math.hypot((fx - poolX) / 96, (fy - poolY) / 36) < 1.1) continue;
      ctx.fillStyle = fw.col;
      ctx.globalAlpha = a * 0.92;
      ctx.beginPath();
      ctx.arc(fx, fy, fw.r, 0, Math.PI * 2);
      ctx.fill();
    }}
    ctx.globalAlpha = 1;

    const treeGrow = Math.min(Math.max((progress - 0.66) / 0.22, 0), 1);
    const tScale = IS_SHORT ? 1.0 : 0.82;
    drawTree(W * 0.16, horizonY + (H - horizonY) * 0.36, tScale, '#3D9140', '#EF4444', treeGrow, t);
    drawTree(W * 0.84, horizonY + (H - horizonY) * 0.35, tScale * 0.94, '#F9A8D4', '#FCE7F3', treeGrow, t);
  }}

  // Update 1/7 .. 7/7 glowing progress dots
  const stepNum = Math.min(TOTAL_DOTS, Math.floor(progress * TOTAL_DOTS) + 1);
  document.getElementById('counterTxt').textContent = `${{stepNum}} / ${{TOTAL_DOTS}}`;
  const dots = dotsRow.children;
  for (let i = 0; i < TOTAL_DOTS; i++) {{
    dots[i].className = 'pdot' + (i < stepNum - 1 ? ' done' : (i === stepNum - 1 ? ' active' : ''));
    if (lightSky > 0.5 && i >= stepNum) dots[i].style.borderColor = 'rgba(30, 41, 59, 0.35)';
    else if (i >= stepNum) dots[i].style.borderColor = 'rgba(255,255,255,0.45)';
  }}

  // Bilingual Arabic VO / English subtitle card
  const arWin = CFG.arabic_window;
  const inArabic = !!(arWin && t >= arWin.start - 0.05 && t <= arWin.end + 0.12);
  let cap = null;
  for (const c of CFG.captions) {{
    if (t >= c.start - 0.06 && t <= c.end + 0.14) {{ cap = c; break; }}
  }}
  const subCard = document.getElementById('subCard');
  const subText = document.getElementById('subText');
  if (inArabic) {{
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

  /* Clean layered paper ribbon header at top */
  .top-paper {{
    position: absolute; top: {56 if is_short else 20}px; left: 32px; right: 32px;
    z-index: 6; display: flex; flex-direction: column; align-items: center; text-align: center;
    pointer-events: none;
  }}
  .pill-tag {{
    display: inline-block; padding: 5px 18px; border-radius: 999px;
    background: #1E2F42; color: #F5F1E3;
    font-size: 13px; font-weight: 800; letter-spacing: 2.2px; text-transform: uppercase;
    box-shadow: 0 6px 14px rgba(15, 28, 42, 0.22);
    margin-bottom: {12 if is_short else 6}px;
  }}
  .cutout-headline {{
    font-size: {40 if is_short else 34}px; font-weight: 900; line-height: 1.12;
    color: #1E2F42; text-transform: uppercase; letter-spacing: 0.4px;
    max-width: {640 if is_short else 960}px;
    text-shadow: 0 3px 0 #F5F1E3, 0 8px 16px rgba(15, 28, 42, 0.22);
  }}

  /* Arabic calligraphy paper card (flips softly into spotlight during Arabic recitation) */
  .ar-ribbon {{
    position: absolute; left: 50%; transform: translateX(-50%);
    top: {222 if is_short else 124}px;
    z-index: 7; width: {640 if is_short else 880}px;
    background: #F6F2E6;
    border: 2px solid #E5BE66;
    border-radius: 18px;
    padding: {14 if is_short else 9}px 22px;
    text-align: center;
    box-shadow: 5px 10px 22px rgba(15, 28, 42, 0.20);
  }}
  .ar-script {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; unicode-bidi: embed;
    font-size: {36 if is_short else 30}px; font-weight: 700; line-height: 1.48;
    color: #1E2F42;
  }}
  .ar-cit {{
    margin-top: 3px; font-size: 12px; font-weight: 800; letter-spacing: 2px;
    color: #B48224; text-transform: uppercase;
  }}

  /* Clean paper-strip bottom subtitle */
  .sub-area {{
    position: absolute; left: 28px; right: 28px;
    bottom: {66 if is_short else 28}px;
    z-index: 9; text-align: center;
  }}
  .sub-paper {{
    display: inline-block; max-width: {640 if is_short else 960}px;
    padding: 11px 22px; border-radius: 14px;
    background: #F6F2E6;
    border: 2px solid rgba(30, 47, 66, 0.16);
    box-shadow: 4px 10px 22px rgba(15, 28, 42, 0.24);
  }}
  #subText {{
    font-size: {30 if is_short else 27}px; font-weight: 800; line-height: 1.24; color: #1E2F42;
  }}
  #subText .hi {{
    color: #0F5E48; background: rgba(229, 190, 102, 0.35);
    padding: 0 5px; border-radius: 6px;
  }}

  .brand-foot {{
    position: absolute; bottom: {20 if is_short else 6}px; left: 0; right: 0;
    z-index: 9; text-align: center;
    font-size: 13px; font-weight: 800; letter-spacing: 2px; color: rgba(30, 47, 66, 0.65);
  }}
</style>
</head>
<body>
<canvas id="bgCanvas" width="{width}" height="{height}"></canvas>

<div class="top-paper">
  <div class="pill-tag" id="pillTag">SUNNAH PAPER STORY</div>
  <div class="cutout-headline" id="headline"></div>
</div>

<div class="ar-ribbon" id="arRibbon">
  <div class="ar-script" id="arScript"></div>
  <div class="ar-cit" id="arCit"></div>
</div>

<div class="sub-area"><div class="sub-paper" id="subPaper"><div id="subText"></div></div></div>
<div class="brand-foot" id="brandFoot"></div>

<script>
const CFG = {cfg_json};
const W = {width}, H = {height};
const IS_SHORT = H >= W;
const ctx = document.getElementById('bgCanvas').getContext('2d');

document.getElementById('arScript').textContent = CFG.dalil.arabic;
document.getElementById('arCit').textContent = '✦  ' + CFG.dalil.citation + '  ✦';
document.getElementById('brandFoot').textContent = CFG.dalil.handle + '  •  PAPER CRAFT SUNNAH STORY';

function setPaperShadow(dx = 5, dy = 10, blur = 16, alpha = 0.22) {{
  ctx.shadowColor = `rgba(15, 28, 42, ${{alpha}})`;
  ctx.shadowBlur = blur;
  ctx.shadowOffsetX = dx;
  ctx.shadowOffsetY = dy;
}}
function clearShadow() {{
  ctx.shadowColor = 'transparent';
  ctx.shadowBlur = 0; ctx.shadowOffsetX = 0; ctx.shadowOffsetY = 0;
}}

function drawPaperCloud(x, y, s) {{
  ctx.save();
  setPaperShadow(3, 7, 12, 0.16);
  ctx.fillStyle = '#F7F4EA';
  ctx.beginPath();
  ctx.arc(x, y, 22 * s, 0, Math.PI * 2);
  ctx.arc(x + 22 * s, y - 8 * s, 26 * s, 0, Math.PI * 2);
  ctx.arc(x + 48 * s, y, 20 * s, 0, Math.PI * 2);
  ctx.fillRect(x, y, 48 * s, 20 * s);
  ctx.fill();
  ctx.restore();
}}

function drawPaperSunburst(cx, cy, r, t) {{
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(t * 0.14);
  setPaperShadow(4, 8, 14, 0.18);
  const rays = 12;
  for (let i = 0; i < rays; i++) {{
    ctx.save();
    ctx.rotate((i / rays) * Math.PI * 2);
    ctx.fillStyle = (i % 2 === 0) ? '#F7F4EA' : '#ECD082';
    ctx.beginPath();
    ctx.moveTo(-8, -r * 1.18);
    ctx.lineTo(8, -r * 1.18);
    ctx.lineTo(13, -r * 1.95);
    ctx.lineTo(-13, -r * 1.95);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }}
  ctx.fillStyle = '#E6C167';
  ctx.beginPath();
  ctx.arc(0, 0, r, 0, Math.PI * 2);
  ctx.fill();
  clearShadow();
  ctx.fillStyle = '#EED082';
  ctx.beginPath();
  ctx.arc(-4, -4, r * 0.78, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}}

function drawPaperTree(x, y, s, variant) {{
  ctx.save();
  ctx.translate(x, y);
  setPaperShadow(4, 8, 12, 0.22);
  if (variant === 'pine') {{
    ctx.fillStyle = '#5B402D';
    ctx.fillRect(-5 * s, -20 * s, 10 * s, 24 * s);
    for (let k = 0; k < 3; k++) {{
      ctx.fillStyle = k === 0 ? '#2E5B43' : (k === 1 ? '#3D7354' : '#4E8C65');
      const base = -18 * s - k * 24 * s;
      const hw = (36 - k * 7) * s;
      ctx.beginPath();
      ctx.moveTo(-hw, base);
      ctx.lineTo(0, base - 38 * s);
      ctx.lineTo(hw, base);
      ctx.closePath();
      ctx.fill();
    }}
  }} else {{
    ctx.fillStyle = '#6A4C36';
    ctx.fillRect(-6 * s, -62 * s, 12 * s, 64 * s);
    ctx.fillStyle = '#4B7F52';
    ctx.beginPath();
    ctx.arc(0, -78 * s, 30 * s, 0, Math.PI * 2);
    ctx.arc(-22 * s, -64 * s, 22 * s, 0, Math.PI * 2);
    ctx.arc(22 * s, -62 * s, 22 * s, 0, Math.PI * 2);
    ctx.fill();
    clearShadow();
    ctx.fillStyle = '#689F69';
    ctx.beginPath();
    ctx.arc(-8 * s, -84 * s, 16 * s, 0, Math.PI * 2);
    ctx.fill();
  }}
  ctx.restore();
}}

// Respectful FACELESS minimalist Muslim presenter in navy kurta/koko (exact Ref #3 silhouette — ZERO facial features!)
function drawFacelessPresenter(x, baseY, s, pose, t) {{
  ctx.save();
  ctx.translate(x, baseY);
  const bob = Math.sin(t * 2.2) * 3 * s;
  ctx.translate(0, bob);
  setPaperShadow(5, 10, 14, 0.24);

  // Sandals & trousers
  ctx.fillStyle = '#182534';
  ctx.fillRect(-20 * s, -98 * s, 16 * s, 82 * s);
  ctx.fillRect(4 * s, -98 * s, 16 * s, 82 * s);
  // Sandals
  ctx.fillStyle = '#3B2F2F';
  ctx.beginPath();
  ctx.roundRect(-24 * s, -16 * s, 22 * s, 12 * s, 5 * s);
  ctx.roundRect(2 * s, -16 * s, 22 * s, 12 * s, 5 * s);
  ctx.fill();

  // Long navy kurta / baju koko tunic
  ctx.fillStyle = '#1E3148';
  ctx.beginPath();
  ctx.roundRect(-30 * s, -214 * s, 60 * s, 134 * s, 16 * s);
  ctx.fill();
  // Subtle center placket seam
  clearShadow();
  ctx.fillStyle = '#2B425E';
  ctx.fillRect(-3 * s, -212 * s, 6 * s, 54 * s);

  // Left arm (relaxed)
  setPaperShadow(3, 6, 10, 0.20);
  ctx.fillStyle = '#1A2B3F';
  ctx.beginPath();
  ctx.roundRect(-42 * s, -206 * s, 16 * s, 82 * s, 8 * s);
  ctx.fill();

  // Right arm (gesturing toward prop OR raised in calm Dua)
  ctx.save();
  ctx.translate(26 * s, -198 * s);
  if (pose === 'point') {{
    ctx.rotate(-0.68 + Math.sin(t * 2.5) * 0.06);
    ctx.fillStyle = '#1A2B3F';
    ctx.beginPath();
    ctx.roundRect(0, -8 * s, 72 * s, 16 * s, 8 * s);
    ctx.fill();
    ctx.fillStyle = '#E8C5A8';
    ctx.beginPath();
    ctx.arc(76 * s, 0, 9 * s, 0, Math.PI * 2);
    ctx.fill();
  }} else if (pose === 'dua') {{
    ctx.rotate(-2.1 + Math.sin(t * 1.8) * 0.05);
    ctx.fillStyle = '#1A2B3F';
    ctx.beginPath();
    ctx.roundRect(0, -8 * s, 54 * s, 15 * s, 7 * s);
    ctx.fill();
    ctx.fillStyle = '#E8C5A8';
    ctx.beginPath();
    ctx.arc(58 * s, 0, 8 * s, 0, Math.PI * 2);
    ctx.fill();
  }} else {{
    ctx.fillStyle = '#1A2B3F';
    ctx.beginPath();
    ctx.roundRect(-4 * s, 0, 16 * s, 80 * s, 8 * s);
    ctx.fill();
  }}
  ctx.restore();

  // Head silhouette (warm skin tone, neat dark hair & beard trim — STRICTLY ZERO eyes/nose/mouth!)
  ctx.fillStyle = '#E8C5A8';
  ctx.beginPath();
  ctx.roundRect(-18 * s, -264 * s, 36 * s, 44 * s, 16 * s);
  ctx.fill();
  // Hair cap
  clearShadow();
  ctx.fillStyle = '#18222F';
  ctx.beginPath();
  ctx.arc(0, -252 * s, 19 * s, Math.PI * 1.05, Math.PI * 1.95);
  ctx.lineTo(18 * s, -242 * s);
  ctx.lineTo(-18 * s, -242 * s);
  ctx.closePath();
  ctx.fill();
  // Soft beard silhouette framing chin
  ctx.beginPath();
  ctx.arc(0, -234 * s, 18 * s, 0.1 * Math.PI, 0.9 * Math.PI);
  ctx.fill();

  ctx.restore();
}}

function drawPaperHillsScene(t, stageIdx) {{
  const baseH = H * (IS_SHORT ? 0.80 : 0.84);
  // Layer 1 distant hill
  ctx.save();
  setPaperShadow(0, -4, 14, 0.16);
  ctx.fillStyle = '#82B378';
  ctx.beginPath();
  ctx.moveTo(0, baseH - 70);
  ctx.quadraticCurveTo(W * 0.28, baseH - 150, W * 0.56, baseH - 85);
  ctx.quadraticCurveTo(W * 0.82, baseH - 140, W, baseH - 78);
  ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
  ctx.fill();

  // Layer 2 mid emerald hill
  ctx.fillStyle = '#558B59';
  ctx.beginPath();
  ctx.moveTo(0, baseH - 12);
  ctx.quadraticCurveTo(W * 0.30, baseH - 80, W * 0.62, baseH - 22);
  ctx.quadraticCurveTo(W * 0.85, baseH - 60, W, baseH - 18);
  ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
  ctx.fill();

  // Layer 3 foreground sage meadow
  ctx.fillStyle = '#3B6E4A';
  ctx.beginPath();
  ctx.moveTo(0, baseH + 40);
  ctx.quadraticCurveTo(W * 0.48, baseH - 10, W, baseH + 34);
  ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
  ctx.fill();
  ctx.restore();

  const sc = IS_SHORT ? 1.0 : 0.78;
  drawPaperTree(W * 0.14, baseH - 18, sc * 0.9, 'pine');
  drawPaperTree(W * 0.86, baseH - 22, sc * 1.05, 'round');
  drawPaperTree(W * 0.76, baseH + 14, sc * 0.75, 'pine');
}}

function drawPaperCalendarProp(cx, cy, s, t) {{
  ctx.save();
  ctx.translate(cx, cy);
  setPaperShadow(8, 14, 22, 0.24);
  const w = 230 * s, h = 235 * s;
  // Main cream page
  ctx.fillStyle = '#F7F3E6';
  ctx.beginPath();
  ctx.roundRect(-w * 0.5, -h * 0.5, w, h, 14 * s);
  ctx.fill();
  // Navy top header
  clearShadow();
  ctx.fillStyle = '#1E2F42';
  ctx.beginPath();
  ctx.roundRect(-w * 0.5, -h * 0.5, w, 54 * s, [14 * s, 14 * s, 0, 0]);
  ctx.fill();
  // Gold hanger tabs
  ctx.fillStyle = '#E5BE66';
  ctx.fillRect(-w * 0.30, -h * 0.5 - 12 * s, 14 * s, 26 * s);
  ctx.fillRect(w * 0.30 - 14 * s, -h * 0.5 - 12 * s, 14 * s, 26 * s);
  // Subtle stars in header
  ctx.fillStyle = '#F5D076';
  ctx.font = `700 ${{18 * s}}px sans-serif`;
  ctx.textAlign = 'center';
  ctx.fillText('★    ✦    ★', 0, -h * 0.5 + 34 * s);
  // Big word / badge inside calendar
  ctx.fillStyle = '#1E2F42';
  ctx.font = `900 ${{34 * s}}px 'Segoe UI', sans-serif`;
  ctx.fillText(CFG.dalil.badge_num || 'SUNNAH', 0, 6 * s);
  ctx.fillStyle = '#558B59';
  ctx.font = `700 ${{16 * s}}px 'Segoe UI', sans-serif`;
  ctx.fillText('DAILY HABIT', 0, 42 * s);

  // Cute curling bottom-right paper corner!
  const curl = (28 + Math.sin(t * 2.5) * 6) * s;
  ctx.fillStyle = '#DED7C5';
  ctx.beginPath();
  ctx.moveTo(w * 0.5 - curl, h * 0.5);
  ctx.lineTo(w * 0.5, h * 0.5 - curl);
  ctx.lineTo(w * 0.5 - curl, h * 0.5 - curl);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}}

function drawOpenPaperBookProp(cx, cy, s, t) {{
  ctx.save();
  ctx.translate(cx, cy);
  setPaperShadow(6, 12, 18, 0.22);
  // Left & right fanned layered pages
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
    ctx.closePath();
    ctx.fill();
  }}
  // Floating golden light medallion rising from the open book (Ref #3 frame 3!)
  clearShadow();
  const rise = Math.sin(t * 2.0) * 6 * s;
  drawPaperSunburst(0, -110 * s + rise, 48 * s, t);
  ctx.restore();
}}

function drawIslamicArchMedallion(cx, cy, s, t) {{
  ctx.save();
  ctx.translate(cx, cy);
  setPaperShadow(6, 12, 20, 0.22);
  // Outer golden dome arch
  ctx.fillStyle = '#E5BE66';
  ctx.beginPath();
  ctx.moveTo(0, -155 * s);
  ctx.bezierCurveTo(95 * s, -120 * s, 130 * s, -30 * s, 118 * s, 60 * s);
  ctx.bezierCurveTo(100 * s, 125 * s, 40 * s, 140 * s, 0, 155 * s);
  ctx.bezierCurveTo(-40 * s, 140 * s, -100 * s, 125 * s, -118 * s, 60 * s);
  ctx.bezierCurveTo(-130 * s, -30 * s, -95 * s, -120 * s, 0, -155 * s);
  ctx.closePath();
  ctx.fill();

  // Inner cream cutout medallion
  ctx.fillStyle = '#FAF6EA';
  ctx.beginPath();
  ctx.arc(0, 6 * s, 108 * s, 0, Math.PI * 2);
  ctx.fill();

  clearShadow();
  ctx.fillStyle = '#1E2F42';
  ctx.font = `900 ${{28 * s}}px 'Segoe UI', sans-serif`;
  ctx.textAlign = 'center';
  ctx.fillText('SAVE & SHARE', 0, -4 * s);
  ctx.fillStyle = '#4B7F52';
  ctx.font = `700 ${{18 * s}}px 'Segoe UI', sans-serif`;
  ctx.fillText('PEACE & BARAKAH', 0, 28 * s);
  ctx.restore();
}}

window.renderAt = function(t) {{
  const total = Math.max(CFG.total_dur, 1);
  const progress = Math.min(Math.max(t / total, 0), 1);

  // Clean pastel sky-blue paper backdrop (Ref #3 exact tone)
  const bg = ctx.createLinearGradient(0, 0, 0, H);
  bg.addColorStop(0, '#9ECAD6');
  bg.addColorStop(0.65, '#B7DCE6');
  bg.addColorStop(1, '#CEE7EE');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, W, H);

  // Subtle floating paper clouds
  drawPaperCloud(((W * 0.10 + t * 9) % (W + 140)) - 70, H * (IS_SHORT ? 0.31 : 0.34), IS_SHORT ? 1.0 : 0.85);
  drawPaperCloud(((W * 0.72 + t * 6) % (W + 140)) - 70, H * (IS_SHORT ? 0.35 : 0.38), IS_SHORT ? 0.85 : 0.72);

  // Rotate cleanly across 4 iconic Ref #3 paper-craft setups across the episode!
  const stage = Math.min(3, Math.floor(progress * 4));
  const sc = IS_SHORT ? 1.0 : 0.72;
  const centerY = H * (IS_SHORT ? 0.62 : 0.65);

  if (stage === 0) {{
    drawPaperSunburst(W * (IS_SHORT ? 0.78 : 0.82), H * (IS_SHORT ? 0.36 : 0.38), 52 * sc, t);
    drawPaperHillsScene(t, stage);
    drawPaperCalendarProp(W * 0.56, centerY - 22 * sc, sc, t);
    drawFacelessPresenter(W * (IS_SHORT ? 0.24 : 0.28), H * (IS_SHORT ? 0.86 : 0.90), sc * 1.05, 'point', t);
  }} else if (stage === 1) {{
    drawPaperHillsScene(t, stage);
    drawOpenPaperBookProp(W * 0.55, centerY + 46 * sc, sc, t);
    drawFacelessPresenter(W * (IS_SHORT ? 0.22 : 0.26), H * (IS_SHORT ? 0.86 : 0.90), sc * 1.02, 'point', t);
  }} else if (stage === 2) {{
    drawPaperSunburst(W * 0.50, H * (IS_SHORT ? 0.48 : 0.50), 58 * sc, t);
    drawPaperHillsScene(t, stage);
    drawFacelessPresenter(W * (IS_SHORT ? 0.25 : 0.30), H * (IS_SHORT ? 0.86 : 0.90), sc * 1.04, 'stand', t);
    drawPaperCalendarProp(W * 0.66, centerY + 8 * sc, sc * 0.86, t);
  }} else {{
    drawPaperHillsScene(t, stage);
    drawIslamicArchMedallion(W * 0.45, centerY - 24 * sc, sc * 0.96, t);
    drawFacelessPresenter(W * (IS_SHORT ? 0.78 : 0.74), H * (IS_SHORT ? 0.86 : 0.90), sc * 1.02, 'dua', t);
  }}

  // Bilingual Arabic VO sync + scene headline
  const arWin = CFG.arabic_window;
  const inArabic = !!(arWin && t >= arWin.start - 0.05 && t <= arWin.end + 0.12);
  let cur = inArabic ? CFG.scenes[0] : CFG.scenes[CFG.scenes.length - 1];
  if (!inArabic) {{
    for (const s of CFG.scenes) {{
      if (t >= s.start && t <= s.end) {{ cur = s; break; }}
    }}
  }}
  document.getElementById('pillTag').textContent = inArabic
    ? (arWin.is_qari ? `TILAWAH • ${{arWin.reciter}}` : 'ARABIC RECITATION')
    : CFG.dalil.pillar_label;
  document.getElementById('headline').textContent = inArabic ? CFG.dalil.citation : (cur ? cur.headline : CFG.dalil.topic);

  const rib = document.getElementById('arRibbon');
  rib.style.borderColor = inArabic ? '#D97706' : '#E5BE66';
  rib.style.boxShadow = inArabic
    ? '0 0 28px rgba(229, 190, 102, 0.75), 5px 10px 22px rgba(15, 28, 42, 0.24)'
    : '5px 10px 22px rgba(15, 28, 42, 0.20)';

  let cap = null;
  for (const c of CFG.captions) {{
    if (t >= c.start - 0.06 && t <= c.end + 0.14) {{ cap = c; break; }}
  }}
  const subPaper = document.getElementById('subPaper');
  const subText = document.getElementById('subText');
  if (inArabic) {{
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
# Full-Bleed Scene-by-Scene Atmospheric Metaphors + Centered White-Outlined Subtitles
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

  /* Minimal luminous floating Arabic header (keeps 82%+ of canvas unobstructed for cinematic storytelling!) */
  .top-float {{
    position: absolute; top: {62 if is_short else 22}px; left: 36px; right: 36px;
    z-index: 6; text-align: center; pointer-events: none;
  }}
  .cit-pill {{
    display: inline-block; padding: 4px 15px; border-radius: 999px;
    background: rgba(6, 12, 22, 0.45);
    border: 1px solid rgba(253, 224, 130, 0.42);
    font-size: 12px; font-weight: 700; letter-spacing: 2.2px; color: #FDE68A;
    text-transform: uppercase; margin-bottom: 8px;
  }}
  .ar-float {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; unicode-bidi: embed;
    font-size: {36 if is_short else 30}px; font-weight: 700; line-height: 1.48;
    color: #FFFDF7;
    text-shadow: 0 3px 16px rgba(0,0,0,0.85), 0 0 18px rgba(253, 224, 130, 0.30);
    max-width: {640 if is_short else 960}px; margin: 0 auto;
  }}

  /* Iconic Ref #6 centered crisp white-outlined conversational subtitles right in the visual sweet spot! */
  .sub-center {{
    position: absolute; left: 32px; right: 32px;
    top: {65 if is_short else 74}%;
    transform: translateY(-50%);
    z-index: 9; text-align: center; pointer-events: none;
  }}
  #subText {{
    display: inline-block; max-width: {630 if is_short else 980}px;
    font-size: {38 if is_short else 34}px; font-weight: 800; line-height: 1.24;
    color: #FFFFFF;
    -webkit-text-stroke: 2.2px rgba(6, 10, 18, 0.94);
    paint-order: stroke fill;
    text-shadow: 0 4px 18px rgba(0,0,0,0.88);
  }}
  #subText .gold {{ color: #FDE68A; }}

  .brand-foot {{
    position: absolute; bottom: {32 if is_short else 16}px; left: 0; right: 0;
    z-index: 9; text-align: center;
    font-size: 13px; font-weight: 600; letter-spacing: 2.4px;
    color: rgba(255,255,255,0.62); text-shadow: 0 2px 8px rgba(0,0,0,0.8);
  }}
</style>
</head>
<body>
<canvas id="bgCanvas" width="{width}" height="{height}"></canvas>

<div class="top-float">
  <div class="cit-pill" id="citPill"></div>
  <div class="ar-float" id="arFloat"></div>
</div>

<div class="sub-center"><div id="subText"></div></div>
<div class="brand-foot" id="brandFoot"></div>

<script>
const CFG = {cfg_json};
const W = {width}, H = {height};
const IS_SHORT = H >= W;
const ctx = document.getElementById('bgCanvas').getContext('2d');

document.getElementById('citPill').textContent = '✦  ' + CFG.dalil.citation + '  ✦';
document.getElementById('arFloat').textContent = CFG.dalil.arabic;
document.getElementById('brandFoot').textContent = CFG.dalil.handle + '  •  REFLECTIVE WISDOM';

// Deterministic silhouettes on endless plain (Ref #6 frame 3!)
const PLAIN_FIGS = [];
for (let i = 0; i < 160; i++) {{
  const row = (i % 16) / 15;
  PLAIN_FIGS.push({{
    x: ((i * 197.7 + (i % 5) * 43) % 1000) / 1000,
    depth: row,
    luminous: (i % 17 === 0),
    ph: i * 0.7,
  }});
}}
const STARS = [];
for (let i = 0; i < 95; i++) {{
  STARS.push({{ x: ((i * 211.3) % 1000) / 1000, y: ((i * 349.1) % 620) / 1000, r: 0.9 + (i % 4) * 0.45, ph: i * 1.1 }});
}}

// Shot 1: Luminous silver needle + glowing pearl water droplet hovering over golden-teal endless ocean (Ref #6 frame 1!)
function drawNeedleOceanShot(lt, t) {{
  const horY = H * 0.34;
  // Warm golden mist sky
  const skyG = ctx.createLinearGradient(0, 0, 0, horY + 30);
  skyG.addColorStop(0, '#5B5956');
  skyG.addColorStop(0.58, '#C8B998');
  skyG.addColorStop(1, '#FCE7A2');
  ctx.fillStyle = skyG;
  ctx.fillRect(0, 0, W, horY + 30);

  // Endless shimmering sunlit teal ocean
  const seaG = ctx.createLinearGradient(0, horY, 0, H);
  seaG.addColorStop(0, '#D4C99E');
  seaG.addColorStop(0.22, '#6BA8B2');
  seaG.addColorStop(0.65, '#3E7B8C');
  seaG.addColorStop(1, '#1E4658');
  ctx.fillStyle = seaG;
  ctx.fillRect(0, horY, W, H - horY);

  // Perspective wave bands catching warm horizon glow
  for (let i = 0; i < 42; i++) {{
    const p = Math.pow(i / 42, 1.55);
    const wy = horY + p * (H - horY);
    const bandH = 2 + p * 7;
    const shift = Math.sin(t * 1.6 + i * 0.7) * (12 + p * 28);
    ctx.fillStyle = `rgba(254, 240, 192, ${{0.30 * (1 - p * 0.55)}})`;
    ctx.fillRect(W * 0.08 + shift, wy, W * 0.84, bandH);
  }}

  // Sleek translucent luminous silver needle descending from top center
  const tipY = H * (IS_SHORT ? 0.35 : 0.39) + Math.sin(t * 1.2) * 8;
  const nGrad = ctx.createLinearGradient(W * 0.5 - 16, 0, W * 0.5 + 16, 0);
  nGrad.addColorStop(0, 'rgba(190, 224, 240, 0.75)');
  nGrad.addColorStop(0.5, 'rgba(255, 255, 255, 0.98)');
  nGrad.addColorStop(1, 'rgba(170, 205, 225, 0.70)');
  ctx.fillStyle = nGrad;
  ctx.beginPath();
  ctx.moveTo(W * 0.5 - 15, 0);
  ctx.lineTo(W * 0.5 + 15, 0);
  ctx.lineTo(W * 0.5 + 12, tipY - 68);
  ctx.lineTo(W * 0.5, tipY);
  ctx.lineTo(W * 0.5 - 12, tipY - 68);
  ctx.closePath();
  ctx.fill();

  // Single radiant glowing pearl droplet hovering just below the needle tip!
  const dropY = tipY + 34 + Math.sin(t * 1.8) * 5;
  const glow = ctx.createRadialGradient(W * 0.5, dropY, 4, W * 0.5, dropY, 72);
  glow.addColorStop(0, 'rgba(255, 252, 236, 0.96)');
  glow.addColorStop(0.36, 'rgba(254, 232, 168, 0.42)');
  glow.addColorStop(1, 'rgba(254, 232, 168, 0)');
  ctx.fillStyle = glow;
  ctx.fillRect(W * 0.5 - 76, dropY - 76, 152, 152);
  ctx.fillStyle = '#FFFDF5';
  ctx.beginPath();
  ctx.arc(W * 0.5, dropY, 24, 0, Math.PI * 2);
  ctx.fill();
}}

// Shot 2: Vast deep-indigo midnight ocean horizon with diagonal moonbeam ripples (Ref #6 frame 4!)
function drawDeepOceanVistaShot(lt, t) {{
  const horY = H * 0.44;
  const skyG = ctx.createLinearGradient(0, 0, 0, horY);
  skyG.addColorStop(0, '#1B2844');
  skyG.addColorStop(1, '#314468');
  ctx.fillStyle = skyG;
  ctx.fillRect(0, 0, W, horY + 4);

  for (const st of STARS) {{
    const tw = 0.45 + 0.55 * Math.sin(t * 1.8 + st.ph);
    ctx.fillStyle = `rgba(255,255,255,${{0.65 * tw}})`;
    ctx.beginPath();
    ctx.arc(st.x * W, st.y * horY, st.r, 0, Math.PI * 2);
    ctx.fill();
  }}

  // Distant island ridge silhouette
  ctx.fillStyle = '#121D34';
  ctx.beginPath();
  ctx.moveTo(0, horY + 2);
  ctx.quadraticCurveTo(W * 0.25, horY - 14, W * 0.50, horY - 2);
  ctx.quadraticCurveTo(W * 0.78, horY - 8, W, horY + 2);
  ctx.closePath();
  ctx.fill();

  // Deep ocean water
  const seaG = ctx.createLinearGradient(0, horY, 0, H);
  seaG.addColorStop(0, '#172947');
  seaG.addColorStop(0.55, '#1D3354');
  seaG.addColorStop(1, '#0F1C32');
  ctx.fillStyle = seaG;
  ctx.fillRect(0, horY, W, H - horY);

  // Diagonal shimmering moonlight waves
  ctx.save();
  for (let i = 0; i < 28; i++) {{
    const p = i / 28;
    const wy = horY + 18 + Math.pow(p, 1.35) * (H - horY);
    const drift = Math.sin(t * 1.1 + i * 0.6) * 24;
    ctx.strokeStyle = `rgba(148, 184, 224, ${{0.14 + 0.12 * p}})`;
    ctx.lineWidth = 2 + p * 8;
    ctx.beginPath();
    ctx.moveTo(-40 + drift, wy - 28);
    ctx.lineTo(W + 40 + drift, wy + 52);
    ctx.stroke();
  }}
  ctx.restore();
}}

// Shot 3: Infinite vast twilight plain with hundreds of tiny tranquil silhouettes (Ref #6 frame 3!)
function drawEndlessPlainShot(lt, t) {{
  const horY = H * 0.22;
  const skyG = ctx.createLinearGradient(0, 0, 0, horY + 40);
  skyG.addColorStop(0, '#182438');
  skyG.addColorStop(1, '#3B4A5E');
  ctx.fillStyle = skyG;
  ctx.fillRect(0, 0, W, horY + 40);

  // Sweeping misty plain
  const pG = ctx.createLinearGradient(0, horY, 0, H);
  pG.addColorStop(0, '#4A5154');
  pG.addColorStop(0.45, '#5E6566');
  pG.addColorStop(1, '#2D343B');
  ctx.fillStyle = pG;
  ctx.fillRect(0, horY, W, H - horY);

  // Soft volumetric top light
  const ray = ctx.createRadialGradient(W * 0.5, horY, 10, W * 0.5, horY + 120, W * 0.72);
  ray.addColorStop(0, 'rgba(254, 236, 188, 0.22)');
  ray.addColorStop(1, 'rgba(254, 236, 188, 0)');
  ctx.fillStyle = ray;
  ctx.fillRect(0, 0, W, H);

  // Perspective minimal human silhouettes standing quietly across the boundless plain
  for (const fg of PLAIN_FIGS) {{
    const p = Math.pow(fg.depth, 1.4);
    const fy = horY + 24 + p * (H - horY - 56);
    const fx = fg.x * W;
    const h = 10 + p * 26;
    if (fg.luminous) {{
      const g = ctx.createRadialGradient(fx, fy - h * 0.5, 1, fx, fy - h * 0.5, h * 0.9);
      g.addColorStop(0, 'rgba(255, 250, 230, 0.85)');
      g.addColorStop(1, 'rgba(255, 250, 230, 0)');
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(fx, fy - h * 0.5, h * 0.9, 0, Math.PI * 2);
      ctx.fill();
    }}
    ctx.fillStyle = fg.luminous ? '#F8FAFC' : 'rgba(22, 30, 42, 0.78)';
    ctx.beginPath();
    ctx.arc(fx, fy - h, h * 0.16, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = fg.luminous ? '#F8FAFC' : 'rgba(22, 30, 42, 0.78)';
    ctx.lineWidth = Math.max(1.2, h * 0.08);
    ctx.beginPath();
    ctx.moveTo(fx, fy - h * 0.84);
    ctx.lineTo(fx, fy - h * 0.28);
    ctx.moveTo(fx, fy - h * 0.28);
    ctx.lineTo(fx - h * 0.18, fy);
    ctx.moveTo(fx, fy - h * 0.28);
    ctx.lineTo(fx + h * 0.18, fy);
    ctx.stroke();
  }}
}}

// Shot 4: Radiant golden-rose twilight sun glowing through dreamy soft violet clouds (Ref #6 frame 6!)
function drawWarmSunsetCloudsShot(lt, t) {{
  const sunX = W * 0.52;
  const sunY = H * (IS_SHORT ? 0.72 : 0.70) - Math.sin(t * 0.3) * 14;
  const bg = ctx.createLinearGradient(0, 0, 0, H);
  bg.addColorStop(0, '#2B2B6E');
  bg.addColorStop(0.42, '#73578E');
  bg.addColorStop(0.72, '#D0838C');
  bg.addColorStop(1, '#F0B484');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, W, H);

  // Soft glowing sunset orb diffusing through clouds
  const orb = ctx.createRadialGradient(sunX, sunY, 12, sunX, sunY, W * 0.58);
  orb.addColorStop(0, 'rgba(255, 250, 214, 0.98)');
  orb.addColorStop(0.24, 'rgba(255, 212, 134, 0.72)');
  orb.addColorStop(0.58, 'rgba(232, 134, 138, 0.28)');
  orb.addColorStop(1, 'rgba(43, 43, 110, 0)');
  ctx.fillStyle = orb;
  ctx.fillRect(0, 0, W, H);

  // Layered dreamy soft cloud puffs drifting across twilight
  for (let i = 0; i < 14; i++) {{
    const cx = ((i * 193 + t * (7 + (i % 3) * 4)) % (W + 260)) - 130;
    const cy = H * (0.28 + (i % 6) * 0.11);
    const rr = 75 + (i % 4) * 32;
    const cg = ctx.createRadialGradient(cx, cy, 8, cx, cy, rr);
    cg.addColorStop(0, i > 6 ? 'rgba(255, 206, 172, 0.28)' : 'rgba(130, 96, 152, 0.24)');
    cg.addColorStop(1, 'rgba(255, 206, 172, 0)');
    ctx.fillStyle = cg;
    ctx.fillRect(cx - rr, cy - rr, rr * 2, rr * 2);
  }}
}}

// Shot 5: Glowing macro droplet falling into calm dark mirror water with golden light ripples
function drawMirrorRippleShot(lt, t) {{
  const bg = ctx.createRadialGradient(W * 0.5, H * 0.52, 12, W * 0.5, H * 0.52, Math.max(W, H) * 0.7);
  bg.addColorStop(0, '#1A344D');
  bg.addColorStop(1, '#070E19');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, W, H);

  const cy = H * 0.54;
  for (let r = 0; r < 6; r++) {{
    const cyc = (t * 0.42 + r / 6) % 1.0;
    ctx.strokeStyle = `rgba(253, 224, 130, ${{(1 - cyc) * 0.52}})`;
    ctx.lineWidth = 2.4 * (1 - cyc * 0.5);
    ctx.beginPath();
    ctx.ellipse(W * 0.5, cy, 18 + cyc * W * 0.46, 6 + cyc * H * 0.12, 0, 0, Math.PI * 2);
    ctx.stroke();
  }}
  const fall = (t * 0.84) % 1.0;
  const dy = H * 0.24 + fall * fall * (cy - H * 0.24);
  ctx.fillStyle = '#FEF3C7';
  ctx.beginPath();
  ctx.arc(W * 0.5, dy, 10 * (1 - fall * 0.3), 0, Math.PI * 2);
  ctx.fill();
}}

const SHOTS = [drawNeedleOceanShot, drawDeepOceanVistaShot, drawEndlessPlainShot, drawMirrorRippleShot, drawWarmSunsetCloudsShot];

window.renderAt = function(t) {{
  const total = Math.max(CFG.total_dur, 1);
  const progress = Math.min(Math.max(t / total, 0), 1);

  // Switch cleanly between atmospheric cinematic visual metaphors beat-by-beat!
  const sFloat = progress * SHOTS.length;
  const sIdx = Math.min(Math.floor(sFloat), SHOTS.length - 1);
  const localT = sFloat - sIdx;
  SHOTS[sIdx](localT, t);

  // Soft top vignette so floating Arabic calligraphy stays legible on bright shots
  const topV = ctx.createLinearGradient(0, 0, 0, H * 0.26);
  topV.addColorStop(0, 'rgba(6, 10, 18, 0.56)');
  topV.addColorStop(1, 'rgba(6, 10, 18, 0)');
  ctx.fillStyle = topV;
  ctx.fillRect(0, 0, W, H * 0.26);

  // Bilingual Arabic VO highlight + Ref #6 centered crisp white-outlined conversational subtitles
  const arWin = CFG.arabic_window;
  const inArabic = !!(arWin && t >= arWin.start - 0.05 && t <= arWin.end + 0.12);
  const arEl = document.getElementById('arFloat');
  arEl.style.color = inArabic ? '#FDE68A' : '#FFFDF7';

  let cap = null;
  for (const c of CFG.captions) {{
    if (t >= c.start - 0.06 && t <= c.end + 0.14) {{ cap = c; break; }}
  }}
  const subEl = document.getElementById('subText');
  if (inArabic) {{
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
