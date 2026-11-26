"""Studio v9 (HabitSains Edition) — 3D Cel-Shaded First-Person POV Cognitive Survival Engine.

Applies the viral @you.have.72hours 3D First-Person POV format directly to the HabitSains niche
(Science-Backed Focus, Habits & Cognitive Performance):
- Real-time 3D WebGL Cel-Shaded Bedroom & Deep-Work Desk (Three.js + uniform black comic ink outlines)
- First-Person POV camera + foreground 3D hoodie-sleeved hands reaching & reacting in real time
- Nightstand with rattling twin-bell alarm clock + vibrating glowing 3D smartphone (19 NOTIFICATIONS -> URGENT x3)
- Swirling 3D red notification storm cubes erupting when POV reaches for morning scrolling
- Articulated 3D "Prefrontal Cortex" Partner character (HabitSains teal beanie + amber puffer jacket + lip-sync)
- 3D Brain Scan Tablet prop showing live DOPAMINE CRASH / FOCUS -40% neuroscience readout
- 3D Deep-Work Study Desk with open laptop (PROJECT DUE 5:00 PM • 0 WORDS), desk lamp, coffee mug & books
- Live HUD: YOUR BEDROOM • 7:01 AM, NEW SERIES: THE 7 AM TRAP, ticking FOCUS WINDOW 05:59:59,
  2-speaker thick-outlined subtitles (YELLOW Brain Guide vs WHITE POV), and viral [A]/[B] cliffhanger card
- 2-speaker neural dialogue + procedural SFX (alarm ring, trap slam, HUD beep, 3 phone buzz+pings, bass drop)
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from src.html_motion_overlay import find_chrome_executable
from src.pov_3d_toon_engine import _synth_edge_line
from src.scriptwriter import normalize_pov_3d_episode


# ---------------------------------------------------------------------------
# Procedural HabitSains Cognitive Thriller Soundscape (100% Free FFmpeg)
# ---------------------------------------------------------------------------

def _build_habitsains_soundscape(
    dialogue_events: list[dict[str, Any]],
    total_dur: float,
    trap_time: float,
    timer_time: float,
    ping_time: float,
    endcard_time: float,
    out_m4a: Path,
    work_dir: Path,
) -> Path:
    """Mix 2-speaker dialogue + morning alarm + warning slam + HUD beep + 3 phone buzz/pings + bass drop."""
    alarm_wav = work_dir / "_hs_alarm.wav"
    slam_wav = work_dir / "_hs_slam.wav"
    beep_wav = work_dir / "_hs_beep.wav"
    ping_wav = work_dir / "_hs_ping.wav"
    boom_wav = work_dir / "_hs_boom.wav"

    try:
        # 1. Morning digital/bell alarm chime (0.0s - 1.5s)
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                "aevalsrc='0.45*sin(2*PI*880*t)*(gte(mod(t,0.42),0.0)*lt(mod(t,0.42),0.14)+gte(mod(t,0.42),0.18)*lt(mod(t,0.42),0.30))*exp(-1.1*t)':s=44100:d=1.45",
                "-af", "lowpass=f=2400,volume=-10dB", "-c:a", "pcm_s16le", str(alarm_wav),
            ],
            capture_output=True, check=True,
        )
        # 2. Dramatic STOP! / Dopamine Trap warning impact
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                "aevalsrc='(0.85*sin(2*PI*(110-65*t)*t)*exp(-6.5*t)+0.35*sin(2*PI*520*t)*exp(-14*t))':s=44100:d=0.65",
                "-af", "lowpass=f=1500,volume=-5dB", "-c:a", "pcm_s16le", str(slam_wav),
            ],
            capture_output=True, check=True,
        )
        # 3. Focus Window HUD activation beep
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                "aevalsrc='0.55*sin(2*PI*1240*t)*exp(-16*t)':s=44100:d=0.18",
                "-af", "volume=-11dB", "-c:a", "pcm_s16le", str(beep_wav),
            ],
            capture_output=True, check=True,
        )
        # 4. Crisp phone notification PING + low table vibrate BUZZ!
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                "aevalsrc='(0.55*sin(2*PI*1320*t)*exp(-16*t)+0.40*sin(2*PI*1760*t)*exp(-14*max(0,t-0.06))*gte(t,0.06)+0.50*sin(2*PI*135*t)*exp(-9*t))':s=44100:d=0.38",
                "-af", "lowpass=f=3200,volume=-4dB", "-c:a", "pcm_s16le", str(ping_wav),
            ],
            capture_output=True, check=True,
        )
        # 5. Deep suspense cliffhanger bass drop
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                "aevalsrc='0.9*sin(2*PI*(62-22*t)*t)*exp(-1.9*t)':s=44100:d=1.6",
                "-af", "lowpass=f=240,volume=-5dB", "-c:a", "pcm_s16le", str(boom_wav),
            ],
            capture_output=True, check=True,
        )

        # Warm-tense cognitive focus synth drone throughout
        drone_expr = "0.24*sin(2*PI*65.41*t)+0.18*sin(2*PI*98.0*t)+0.11*sin(2*PI*130.81*t)*(0.72+0.28*sin(2*PI*0.32*t))"
        inputs: list[str] = [
            "-f", "lavfi", "-t", f"{total_dur:.2f}", "-i", f"aevalsrc='{drone_expr}':s=44100:c=stereo",
            "-i", str(alarm_wav),
            "-i", str(slam_wav),
            "-i", str(beep_wav),
            "-i", str(boom_wav),
        ]
        filters: list[str] = [
            f"[0:a]lowpass=f=280,volume=-22dB,afade=t=in:st=0:d=0.8,afade=t=out:st={max(total_dur - 1.4, 0.5):.2f}:d=1.3[drone]",
            "[1:a]adelay=80:all=1,aformat=channel_layouts=stereo[alarm]",
            f"[2:a]adelay={int(trap_time * 1000)}:all=1,aformat=channel_layouts=stereo[slam]",
            f"[3:a]adelay={int(timer_time * 1000)}:all=1,aformat=channel_layouts=stereo[beep]",
            f"[4:a]adelay={int(endcard_time * 1000)}:all=1,aformat=channel_layouts=stereo[boom]",
        ]
        mix = ["[drone]", "[alarm]", "[slam]", "[beep]", "[boom]"]
        nxt = 5

        # 3 urgent phone notification PING+BUZZ bursts!
        for p_i, p_off in enumerate((0.0, 0.54, 1.08)):
            ms = max(int((ping_time + p_off) * 1000), 0)
            inputs.extend(["-i", str(ping_wav)])
            filters.append(f"[{nxt}:a]adelay={ms}:all=1,aformat=channel_layouts=stereo[pg{p_i}]")
            mix.append(f"[pg{p_i}]")
            nxt += 1

        # Add every dialogue clip cleanly at its exact timestamp
        for d_i, ev in enumerate(dialogue_events):
            ms = max(int(ev["start"] * 1000), 0)
            inputs.extend(["-i", str(ev["wav_path"])])
            filters.append(f"[{nxt}:a]adelay={ms}:all=1,volume=+1.5dB,aformat=channel_layouts=stereo[dlg{d_i}]")
            mix.append(f"[dlg{d_i}]")
            nxt += 1

        filters.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:dropout_transition=2:normalize=0,alimiter=limit=0.95[out]")
        subprocess.run(
            ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", str(out_m4a)],
            capture_output=True, text=True, check=True,
        )
        return out_m4a
    finally:
        for f in (alarm_wav, slam_wav, beep_wav, ping_wav, boom_wav):
            f.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Three.js 3D Cel-Shaded POV HabitSains Bedroom + Focus Desk Scene Template
# ---------------------------------------------------------------------------

def _build_habitsains_3d_html(three_js_src: str, timeline_cfg: dict[str, Any], width: int, height: int) -> str:
    cfg_json = json.dumps(timeline_cfg)
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: {width}px; height: {height}px; overflow: hidden;
    background: #000; font-family: 'Segoe UI', Impact, 'Arial Black', Arial, sans-serif;
  }}
  #gl {{ position: absolute; inset: 0; width: {width}px; height: {height}px; display: block; }}

  /* Top-left location & time stamp */
  #locStamp {{
    position: absolute; top: 102px; left: 32px; z-index: 10;
    opacity: 0;
  }}
  .loc-main {{
    font-size: 29px; font-weight: 900; color: #FFFFFF; letter-spacing: 0.6px;
    text-shadow: -2px -2px 0 #111, 2px -2px 0 #111, -2px 2px 0 #111, 2px 2px 0 #111, 0 4px 10px rgba(0,0,0,0.8);
  }}
  .loc-sub {{
    font-size: 23px; font-weight: 800; color: #2DD4BF; margin-top: 2px;
    text-shadow: -2px -2px 0 #111, 2px -2px 0 #111, -2px 2px 0 #111, 2px 2px 0 #111;
  }}

  /* HabitSains Series Banner */
  #seriesBanner {{
    position: absolute; top: 186px; left: 50%; transform: translateX(-50%);
    z-index: 11; padding: 14px 40px 16px; border-radius: 16px;
    background: linear-gradient(180deg, #E11D48 0%, #B91C3C 100%);
    border: 3px solid #881337;
    box-shadow: 0 12px 32px rgba(0,0,0,0.65);
    text-align: center; opacity: 0; white-space: nowrap;
  }}
  .sb-eyebrow {{
    font-size: 16px; font-weight: 800; letter-spacing: 3px; color: rgba(255,255,255,0.92);
    margin-bottom: 4px;
  }}
  .sb-title {{
    font-size: 40px; font-weight: 900; letter-spacing: 1px; color: #FFFFFF;
    display: flex; align-items: center; justify-content: center; gap: 12px;
  }}

  /* Live Ticking FOCUS WINDOW HUD + Focus Bar */
  #timerHud {{
    position: absolute; top: 106px; left: 50%; transform: translateX(-50%);
    z-index: 12; padding: 10px 26px 12px; border-radius: 14px;
    background: rgba(14, 16, 26, 0.93);
    border: 3px solid #EF4444;
    box-shadow: 0 0 22px rgba(239,68,68,0.45), 0 10px 24px rgba(0,0,0,0.65);
    text-align: center; opacity: 0; min-width: 280px;
  }}
  .tm-lbl {{
    font-size: 15px; font-weight: 800; letter-spacing: 3.5px; color: #F87171;
    margin-bottom: 2px;
  }}
  .tm-val {{
    font-size: 38px; font-weight: 900; color: #FFFFFF; letter-spacing: 2px;
    font-variant-numeric: tabular-nums;
  }}
  .tm-bar-wrap {{
    margin-top: 6px; width: 100%; height: 9px; border-radius: 99px;
    background: rgba(255,255,255,0.14); overflow: hidden;
  }}
  #focusBarFill {{
    height: 100%; width: 100%; background: #2DD4BF; border-radius: 99px;
  }}
  .tm-cap {{
    margin-top: 4px; font-size: 13px; font-weight: 800; letter-spacing: 1.5px; color: #E2E8F0;
  }}

  /* Bold Thick-Outlined Dialogue Subtitles (Yellow Prefrontal Cortex / White POV) */
  #subWrap {{
    position: absolute; left: 32px; right: 32px; top: 72.5%;
    transform: translateY(-50%);
    z-index: 15; text-align: center; pointer-events: none;
  }}
  #subText {{
    display: inline-block;
    font-family: 'Arial Black', Impact, 'Segoe UI', sans-serif;
    font-size: 44px; font-weight: 900; line-height: 1.15;
    letter-spacing: 0.4px; text-transform: uppercase;
    -webkit-text-stroke: 3.2px #111111;
    paint-order: stroke fill;
    text-shadow: 0 5px 0 #111111, 0 8px 18px rgba(0,0,0,0.85);
    padding: 0 10px;
  }}

  /* Viral Interactive A/B Cliffhanger End Screen */
  #endCard {{
    position: absolute; inset: 0; z-index: 30;
    background: #05070E;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 44px; opacity: 0; pointer-events: none;
  }}
  .ec-top {{
    font-size: 23px; font-weight: 800; letter-spacing: 4px; color: #2DD4BF;
    margin-bottom: 16px;
  }}
  .ec-head {{
    font-family: 'Arial Black', Impact, sans-serif;
    font-size: 64px; font-weight: 900; line-height: 1.04; color: #FFFFFF;
    text-align: center; margin-bottom: 42px; letter-spacing: 1px;
  }}
  .ec-btn {{
    width: 100%; border-radius: 20px; padding: 22px 24px;
    display: flex; align-items: center; gap: 20px;
    box-shadow: 0 12px 28px rgba(0,0,0,0.5);
  }}
  .ec-btn-a {{ background: linear-gradient(180deg, #14B8A6 0%, #0D9488 100%); border: 2px solid #5EEAD4; }}
  .ec-btn-b {{ background: linear-gradient(180deg, #E11D48 0%, #BE123C 100%); border: 2px solid #FDA4AF; }}
  .ec-badge {{
    width: 60px; height: 60px; border-radius: 14px; background: #FFFFFF; color: #111827;
    font-size: 36px; font-weight: 900; display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }}
  .ec-label {{
    font-family: 'Arial Black', 'Segoe UI', sans-serif;
    font-size: 28px; font-weight: 900; color: #FFFFFF; line-height: 1.18; text-transform: uppercase;
  }}
  .ec-or {{
    font-size: 28px; font-weight: 900; color: #FBBF24; margin: 18px 0; letter-spacing: 2px;
  }}
  .ec-cta {{
    margin-top: 44px; font-size: 28px; font-weight: 800; color: #FFFFFF; text-align: center;
  }}
  .ec-cta b {{ color: #2DD4BF; }}
  .ec-sub {{
    margin-top: 8px; font-size: 21px; font-weight: 700; color: #94A3B8;
  }}
  .ec-arrow {{ font-size: 38px; color: #FBBF24; margin-top: 8px; }}
</style>
</head>
<body>
<canvas id="gl" width="{width}" height="{height}"></canvas>

<div id="locStamp">
  <div class="loc-main" id="locMain">YOUR BEDROOM • 7:01 AM</div>
  <div class="loc-sub" id="locSub">@HabitSains • Part 1</div>
</div>

<div id="seriesBanner">
  <div class="sb-eyebrow" id="sbEyebrow">NEW SERIES</div>
  <div class="sb-title">
    <svg width="32" height="32" viewBox="0 0 24 24" fill="#FDE047"><path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z"/></svg>
    <span id="seriesTitle">THE 7 AM TRAP</span>
  </div>
</div>

<div id="timerHud">
  <div class="tm-lbl" id="tmLbl">FOCUS WINDOW</div>
  <div class="tm-val" id="timerVal">05:59:59</div>
  <div class="tm-bar-wrap"><div id="focusBarFill"></div></div>
  <div class="tm-cap" id="focusCap">BRAIN FOCUS: 100%</div>
</div>

<div id="subWrap"><span id="subText"></span></div>

<div id="endCard">
  <div class="ec-top" id="ecTop">PART 1 • YOU DECIDE</div>
  <div class="ec-head">WHAT WOULD<br>YOU DO?</div>
  <div class="ec-btn ec-btn-a"><div class="ec-badge">A</div><div class="ec-label" id="optA">LOCK PHONE IN ANOTHER ROOM &amp; GET SUNLIGHT</div></div>
  <div class="ec-or">OR</div>
  <div class="ec-btn ec-btn-b"><div class="ec-badge">B</div><div class="ec-label" id="optB">"JUST TWO MINUTES" OF MORNING SCROLLING</div></div>
  <div class="ec-cta">Comment <b>A</b> or <b>B</b> below</div>
  <div class="ec-sub" id="ecSub">Part 2 reveals your brain at 3:00 PM</div>
  <div class="ec-arrow">↓</div>
</div>

<script>{three_js_src}</script>
<script>
(() => {{
  const CFG = {cfg_json};
  const W = {width}, H = {height};
  const IS_LAND = W > H;

  // Populate dynamic topic-aware HUD labels from CFG (falls back cleanly to 7 AM Trap defaults)
  document.getElementById('locMain').textContent = CFG.loc_main || 'YOUR BEDROOM • 7:01 AM';
  document.getElementById('locSub').textContent = CFG.loc_sub || '@HabitSains • Part 1';
  document.getElementById('sbEyebrow').textContent = CFG.series_eyebrow || 'NEW SERIES';
  document.getElementById('seriesTitle').textContent = CFG.series_title || 'THE 7 AM TRAP';
  document.getElementById('tmLbl').textContent = CFG.timer_label || 'FOCUS WINDOW';
  document.getElementById('ecTop').textContent = CFG.end_top || 'PART 1 • YOU DECIDE';
  document.getElementById('optA').textContent = CFG.option_a || 'LOCK PHONE IN ANOTHER ROOM & GET SUNLIGHT';
  document.getElementById('optB').textContent = CFG.option_b || '"JUST TWO MINUTES" OF MORNING SCROLLING';
  document.getElementById('ecSub').textContent = CFG.end_sub || 'Part 2 reveals your brain at 3:00 PM';

  if (IS_LAND) {{
    document.getElementById('locStamp').style.top = '34px';
    document.getElementById('seriesBanner').style.top = '36px';
    document.getElementById('timerHud').style.top = '28px';
    document.getElementById('subWrap').style.top = '82%';
    document.getElementById('subText').style.fontSize = '38px';
    document.querySelector('#endCard').style.padding = '28px 180px';
    document.querySelector('.ec-head').style.fontSize = '48px';
    document.querySelector('.ec-head').style.marginBottom = '22px';
    document.querySelectorAll('.ec-btn').forEach(b => {{ b.style.padding = '14px 20px'; }});
    document.querySelectorAll('.ec-label').forEach(l => {{ l.style.fontSize = '22px'; }});
    document.querySelector('.ec-cta').style.marginTop = '22px';
  }}

  // --- THREE.JS CEL-SHADED TOON RENDERER ---
  const canvas = document.getElementById('gl');
  const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true, preserveDrawingBuffer: true }});
  renderer.setSize(W, H, false);
  renderer.outputEncoding = THREE.sRGBEncoding;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x1b2338);

  const camera = new THREE.PerspectiveCamera(62, W / H, 0.08, 80);
  scene.add(camera);

  // 3-step quantized toon gradient map
  const gradData = new Uint8Array([92, 92, 92, 255, 178, 178, 178, 255, 255, 255, 255, 255]);
  const toonGrad = new THREE.DataTexture(gradData, 3, 1, THREE.RGBAFormat);
  toonGrad.minFilter = THREE.NearestFilter;
  toonGrad.magFilter = THREE.NearestFilter;
  toonGrad.needsUpdate = true;

  function makeOutlineMat(thickness = 0.020) {{
    return new THREE.ShaderMaterial({{
      side: THREE.BackSide,
      uniforms: {{ uThick: {{ value: thickness }} }},
      vertexShader: `
        uniform float uThick;
        void main() {{
          vec3 p = position + normal * uThick;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
        }}
      `,
      fragmentShader: `void main() {{ gl_FragColor = vec4(0.06, 0.07, 0.10, 1.0); }}`
    }});
  }}

  function toonMat(colorHex, mapTex = null) {{
    const opts = {{ color: colorHex, gradientMap: toonGrad }};
    if (mapTex) opts.map = mapTex;
    return new THREE.MeshToonMaterial(opts);
  }}

  function outlinedMesh(geo, mat, outlineThick = 0.018) {{
    const mesh = new THREE.Mesh(geo, mat);
    if (outlineThick > 0) {{
      mesh.add(new THREE.Mesh(geo, makeOutlineMat(outlineThick)));
    }}
    return mesh;
  }}

  // --- PROCEDURAL TEXTURES (Bedroom Walls, Wood Planks, Phone Screens, Brain Scan Tablet, Laptop) ---
  function makeWallTexture() {{
    const tc = document.createElement('canvas');
    tc.width = 512; tc.height = 512;
    const ctx = tc.getContext('2d');
    ctx.fillStyle = '#36415E';
    ctx.fillRect(0, 0, 512, 512);
    // Subtle cozy vertical architectural paneling + soft plaster grain
    ctx.fillStyle = 'rgba(255,255,255,0.035)';
    for (let x = 0; x < 512; x += 64) ctx.fillRect(x, 0, 28, 512);
    ctx.strokeStyle = '#252E45';
    ctx.lineWidth = 3;
    for (let x = 0; x <= 512; x += 64) {{
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 512); ctx.stroke();
    }}
    // Wainscoting baseboard strip along bottom
    ctx.fillStyle = '#2A334B';
    ctx.fillRect(0, 410, 512, 102);
    ctx.strokeStyle = '#1B2133'; ctx.lineWidth = 5;
    ctx.beginPath(); ctx.moveTo(0, 410); ctx.lineTo(512, 410); ctx.stroke();
    const tex = new THREE.CanvasTexture(tc);
    tex.wrapS = THREE.RepeatWrapping; tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.repeat.set(2.4, 1);
    tex.encoding = THREE.sRGBEncoding;
    return tex;
  }}

  function makeWoodTexture() {{
    const tc = document.createElement('canvas');
    tc.width = 512; tc.height = 512;
    const ctx = tc.getContext('2d');
    ctx.fillStyle = '#6E4F37';
    ctx.fillRect(0, 0, 512, 512);
    ctx.strokeStyle = '#4B3322'; ctx.lineWidth = 4;
    for (let y = 0; y < 512; y += 64) {{
      ctx.fillStyle = (y % 128 === 0) ? 'rgba(255,220,175,0.07)' : 'rgba(25,14,8,0.08)';
      ctx.fillRect(0, y, 512, 64);
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(512, y); ctx.stroke();
    }}
    const tex = new THREE.CanvasTexture(tc);
    tex.wrapS = THREE.RepeatWrapping; tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(3, 3);
    tex.encoding = THREE.sRGBEncoding;
    return tex;
  }}

  function makePhoneTex(urgentMode) {{
    const tc = document.createElement('canvas');
    tc.width = 280; tc.height = 500;
    const ctx = tc.getContext('2d');
    ctx.fillStyle = urgentMode ? '#1F0C14' : '#0F1322';
    ctx.fillRect(0, 0, 280, 500);
    // Header time
    ctx.fillStyle = '#FFFFFF'; ctx.font = 'bold 68px Arial'; ctx.textAlign = 'center';
    ctx.fillText(CFG.phone_time || '7:01', 140, 108, 250);
    ctx.fillStyle = urgentMode ? '#FB7185' : '#2DD4BF';
    ctx.font = 'bold 20px Arial';
    ctx.fillText(urgentMode ? (CFG.phone_urgent_hdr || '3 URGENT ALERTS!') : (CFG.phone_norm_hdr || '19 NOTIFICATIONS'), 140, 148, 254);

    const defUrgent = [
      ['#E11D48', 'BOSS • URGENT', 'Can you reply right now?!'],
      ['#F59E0B', 'VIRAL REEL', 'You were tagged in 4 posts'],
      ['#E11D48', 'BREAKING NEWS', 'Tap to see what happened'],
    ];
    const defNorm = [
      ['#E11D48', 'SOCIAL FEED', '14 new likes & comments'],
      ['#3B82F6', 'MESSAGES', '3 unread group chats'],
      ['#F59E0B', 'SHORT VIDEOS', 'Just 2 minutes? Tap now'],
    ];
    const customCards = urgentMode ? CFG.phone_urgent_cards : CFG.phone_norm_cards;
    const cards = (Array.isArray(customCards) && customCards.length === 3) ? customCards : (urgentMode ? defUrgent : defNorm);
    cards.forEach(([col, title, sub], idx) => {{
      const cy = 182 + idx * 86;
      ctx.fillStyle = urgentMode ? '#331420' : '#1E253D';
      ctx.fillRect(18, cy, 244, 72);
      ctx.fillStyle = col || '#E11D48';
      ctx.fillRect(18, cy, 10, 72);
      ctx.textAlign = 'left';
      ctx.fillStyle = '#FFFFFF'; ctx.font = 'bold 18px Arial';
      ctx.fillText(String(title || ''), 38, cy + 28, 214);
      ctx.fillStyle = '#CBD5E1'; ctx.font = '15px Arial';
      ctx.fillText(String(sub || ''), 38, cy + 54, 214);
    }});

    // Glowing swipe prompt
    ctx.fillStyle = urgentMode ? '#F43F5E' : '#2DD4BF';
    ctx.fillRect(46, 444, 188, 34);
    ctx.fillStyle = '#FFFFFF'; ctx.textAlign = 'center'; ctx.font = 'bold 17px Arial';
    ctx.fillText(urgentMode ? (CFG.phone_cta_urgent || 'OPEN NOW') : (CFG.phone_cta_norm || 'SWIPE TO SCROLL'), 140, 467, 178);

    const tex = new THREE.CanvasTexture(tc);
    tex.encoding = THREE.sRGBEncoding;
    return tex;
  }}

  function makeBrainScanTex() {{
    const tc = document.createElement('canvas');
    tc.width = 340; tc.height = 460;
    const ctx = tc.getContext('2d');
    ctx.fillStyle = '#0D1326'; ctx.fillRect(0, 0, 340, 460);
    ctx.strokeStyle = '#2DD4BF'; ctx.lineWidth = 6;
    ctx.strokeRect(8, 8, 324, 444);

    ctx.fillStyle = '#2DD4BF'; ctx.font = 'bold 20px Arial'; ctx.textAlign = 'center';
    ctx.fillText(CFG.scan_title || 'NEURAL DOPAMINE SCAN', 170, 46, 304);
    ctx.fillStyle = '#F43F5E'; ctx.font = 'bold 42px Arial';
    ctx.fillText(CFG.scan_stat || '-40% FOCUS', 170, 108, 304);
    ctx.fillStyle = '#FBBF24'; ctx.font = 'bold 18px Arial';
    ctx.fillText(CFG.scan_sub || 'CRASH LASTS 6 HOURS', 170, 140, 304);

    // Draw Baseline vs Spike-Crash Graph!
    ctx.fillStyle = '#161E38'; ctx.fillRect(26, 166, 288, 175);
    // Dashed baseline
    ctx.strokeStyle = '#2DD4BF'; ctx.lineWidth = 3; ctx.setLineDash([8, 6]);
    ctx.beginPath(); ctx.moveTo(36, 245); ctx.lineTo(304, 245); ctx.stroke();
    ctx.setLineDash([]);
    // Sharp spike then deep red crash!
    ctx.strokeStyle = '#F43F5E'; ctx.lineWidth = 7;
    ctx.beginPath();
    ctx.moveTo(36, 245);
    ctx.lineTo(84, 242);
    ctx.lineTo(116, 182);
    ctx.lineTo(156, 316);
    ctx.lineTo(240, 310);
    ctx.lineTo(300, 294);
    ctx.stroke();

    ctx.fillStyle = '#94A3B8'; ctx.font = 'bold 15px Arial'; ctx.textAlign = 'left';
    ctx.fillText(CFG.scan_left_lbl || '7:01 AM SCROLL', 32, 368, 134);
    ctx.fillStyle = '#F43F5E'; ctx.textAlign = 'right';
    ctx.fillText(CFG.scan_right_lbl || '3:00 PM FOG', 308, 368, 134);

    ctx.fillStyle = '#1E293B'; ctx.fillRect(26, 388, 288, 48);
    ctx.fillStyle = '#FFFFFF'; ctx.textAlign = 'center'; ctx.font = 'bold 18px Arial';
    ctx.fillText(CFG.scan_footer || 'REWARD SYSTEM: DEPLETED', 170, 419, 276);

    const tex = new THREE.CanvasTexture(tc);
    tex.encoding = THREE.sRGBEncoding;
    return tex;
  }}

  function makeLaptopTex() {{
    const tc = document.createElement('canvas');
    tc.width = 480; tc.height = 300;
    const ctx = tc.getContext('2d');
    ctx.fillStyle = '#F8FAFC'; ctx.fillRect(0, 0, 480, 300);
    ctx.fillStyle = '#1E293B'; ctx.fillRect(0, 0, 480, 46);
    ctx.fillStyle = '#2DD4BF'; ctx.font = 'bold 19px Arial'; ctx.textAlign = 'left';
    ctx.fillText(CFG.laptop_hdr || 'DEEP WORK • BIG PROJECT', 18, 30, 300);
    ctx.fillStyle = '#F43F5E'; ctx.textAlign = 'right';
    ctx.fillText(CFG.laptop_due || 'DUE 5:00 PM', 462, 30, 140);

    ctx.fillStyle = '#0F172A'; ctx.textAlign = 'left'; ctx.font = 'bold 26px Arial';
    ctx.fillText(CFG.laptop_title || 'Chapter 1: Core Strategy', 28, 102, 424);
    ctx.fillStyle = '#94A3B8'; ctx.font = '22px Arial';
    ctx.fillText(CFG.laptop_status || '|  (0 words written...)', 28, 152, 424);
    ctx.fillStyle = '#FEE2E2'; ctx.fillRect(28, 206, 424, 58);
    ctx.fillStyle = '#BE123C'; ctx.font = 'bold 20px Arial'; ctx.textAlign = 'center';
    ctx.fillText(CFG.laptop_callout || 'REQUIRES 3 HOURS OF DEEP FOCUS', 240, 243, 408);

    const tex = new THREE.CanvasTexture(tc);
    tex.encoding = THREE.sRGBEncoding;
    return tex;
  }}

  const wallTex = makeWallTexture();
  const woodTex = makeWoodTexture();
  const phoneNormTex = makePhoneTex(false);
  const phoneUrgentTex = makePhoneTex(true);
  const brainScanTex = makeBrainScanTex();
  const laptopTex = makeLaptopTex();

  // --- LIGHTING (Warm Cozy Morning Bedroom + Crisp Teal Rim + Dynamic Red Alert Glow) ---
  const ambLight = new THREE.AmbientLight(0xb8c4dc, 0.50);
  scene.add(ambLight);
  const roomLamp = new THREE.PointLight(0xffd28a, 1.05, 14, 1.4);
  roomLamp.position.set(0.2, 3.0, 0.1);
  scene.add(roomLamp);
  const alertLight = new THREE.PointLight(0xff2e4c, 0.0, 10, 1.5);
  alertLight.position.set(1.55, 1.35, 1.45);
  scene.add(alertLight);
  const windowSun = new THREE.DirectionalLight(0xffe0a3, 0.45);
  windowSun.position.set(4, 6, 4);
  scene.add(windowSun);

  // --- 3D CEL-SHADED BEDROOM + STUDY ROOM (W=5.6, H=3.4, D=6.0) ---
  const room = new THREE.Group();
  scene.add(room);

  const wallMat = toonMat(0xffffff, wallTex);
  const floorMat = toonMat(0xffffff, woodTex);
  const ceilMat = toonMat(0x283047);

  const floor = new THREE.Mesh(new THREE.PlaneGeometry(5.8, 6.2), floorMat);
  floor.rotation.x = -Math.PI / 2;
  room.add(floor);

  const ceil = new THREE.Mesh(new THREE.PlaneGeometry(5.8, 6.2), ceilMat);
  ceil.rotation.x = Math.PI / 2;
  ceil.position.y = 3.4;
  room.add(ceil);

  // 4 Walls
  const backW = new THREE.Mesh(new THREE.PlaneGeometry(5.8, 3.4), wallMat);
  backW.position.set(0, 1.7, -3.0);
  const frontW = new THREE.Mesh(new THREE.PlaneGeometry(5.8, 3.4), wallMat);
  frontW.rotation.y = Math.PI; frontW.position.set(0, 1.7, 3.0);
  const leftW = new THREE.Mesh(new THREE.PlaneGeometry(6.2, 3.4), wallMat);
  leftW.rotation.y = Math.PI / 2; leftW.position.set(-2.8, 1.7, 0);
  const rightW = new THREE.Mesh(new THREE.PlaneGeometry(6.2, 3.4), wallMat);
  rightW.rotation.y = -Math.PI / 2; rightW.position.set(2.8, 1.7, 0);
  room.add(backW, frontW, leftW, rightW);

  // Cozy Pendant Ceiling Light
  const lampCord = outlinedMesh(new THREE.CylinderGeometry(0.02, 0.02, 0.45, 8), toonMat(0x1b1e28), 0.008);
  lampCord.position.set(0.2, 3.18, 0.0);
  const lampShade = outlinedMesh(new THREE.ConeGeometry(0.36, 0.24, 16), toonMat(0xf59e0b), 0.015);
  lampShade.position.set(0.2, 2.94, 0.0);
  room.add(lampCord, lampShade);

  // Framed HabitSains Minimal Poster on Back Wall
  const posterFrame = outlinedMesh(new THREE.BoxGeometry(1.15, 0.78, 0.06), toonMat(0x181c2b), 0.014);
  posterFrame.position.set(1.55, 2.18, -2.95);
  const posterInner = new THREE.Mesh(new THREE.PlaneGeometry(1.02, 0.65), toonMat(0x14b8a6));
  posterInner.position.set(1.55, 2.18, -2.91);
  room.add(posterFrame, posterInner);

  // Morning Bedroom Window on Right Wall (+X = 2.74, z = -0.3)
  const winFrame = outlinedMesh(new THREE.BoxGeometry(0.10, 1.55, 1.85), toonMat(0x232a3d), 0.016);
  winFrame.position.set(2.74, 1.92, -0.35);
  const winGlass = new THREE.Mesh(new THREE.PlaneGeometry(1.68, 1.38), new THREE.MeshBasicMaterial({{ color: 0xf7b267 }}));
  winGlass.rotation.y = -Math.PI / 2;
  winGlass.position.set(2.68, 1.92, -0.35);
  const winBarV = outlinedMesh(new THREE.BoxGeometry(0.11, 1.45, 0.07), toonMat(0x232a3d), 0.008);
  winBarV.position.set(2.72, 1.92, -0.35);
  const winBarH = outlinedMesh(new THREE.BoxGeometry(0.11, 0.07, 1.75), toonMat(0x232a3d), 0.008);
  winBarH.position.set(2.72, 1.92, -0.35);
  room.add(winFrame, winGlass, winBarV, winBarH);

  // --- BED + NIGHTSTAND + ALARM CLOCK + GLOWING 3D SMARTPHONE (Right Side +X, +Z) ---
  const woodDarkMat = toonMat(0x5b3f2b);
  const bedBase = outlinedMesh(new THREE.BoxGeometry(1.75, 0.52, 2.15), toonMat(0x13887b), 0.018);
  bedBase.position.set(0.35, 0.26, 1.75);
  const pillow = outlinedMesh(new THREE.BoxGeometry(1.25, 0.22, 0.55), toonMat(0xeef2f7), 0.016);
  pillow.position.set(0.35, 0.62, 2.45);
  room.add(bedBase, pillow);

  // Nightstand right at (+1.95, y=0..0.82, z=1.35)
  const stand = outlinedMesh(new THREE.BoxGeometry(0.92, 0.82, 0.78), woodDarkMat, 0.018);
  stand.position.set(1.95, 0.41, 1.35);
  const drawer = outlinedMesh(new THREE.BoxGeometry(0.76, 0.26, 0.06), toonMat(0x7c583d), 0.012);
  drawer.position.set(1.95, 0.56, 0.94);
  const knob = outlinedMesh(new THREE.SphereGeometry(0.045, 10, 10), toonMat(0xfbbf24), 0.008);
  knob.position.set(1.95, 0.56, 0.90);
  room.add(stand, drawer, knob);

  // Classic Twin-Bell 3D Alarm Clock on nightstand!
  const alarmGrp = new THREE.Group();
  alarmGrp.position.set(2.15, 0.96, 1.15);
  alarmGrp.rotation.y = -Math.PI * 0.65;
  const clkBody = outlinedMesh(new THREE.CylinderGeometry(0.15, 0.15, 0.10, 18), toonMat(0xe11d48), 0.012);
  clkBody.rotation.x = Math.PI / 2;
  const clkFace = new THREE.Mesh(new THREE.CircleGeometry(0.125, 18), new THREE.MeshBasicMaterial({{ color: 0xf8fafc }}));
  clkFace.position.z = 0.056;
  const bellL = outlinedMesh(new THREE.SphereGeometry(0.065, 10, 10), toonMat(0xfbbf24), 0.009);
  bellL.position.set(-0.12, 0.14, 0);
  const bellR = outlinedMesh(new THREE.SphereGeometry(0.065, 10, 10), toonMat(0xfbbf24), 0.009);
  bellR.position.set(0.12, 0.14, 0);
  alarmGrp.add(clkBody, clkFace, bellL, bellR);
  room.add(alarmGrp);

  // Glowing 3D Nightstand Smartphone on sleek charging dock (sits 100% flush on nightstand top y=0.82!)
  const dockBase = outlinedMesh(new THREE.BoxGeometry(0.28, 0.06, 0.22), toonMat(0x232b3e), 0.010);
  dockBase.position.set(1.74, 0.85, 1.32);
  dockBase.rotation.y = -Math.PI * 0.58;
  room.add(dockBase);

  const standPhoneGrp = new THREE.Group();
  standPhoneGrp.position.set(1.74, 1.13, 1.32);
  standPhoneGrp.rotation.set(-0.14, -Math.PI * 0.58, 0.0);
  const spBody = outlinedMesh(new THREE.BoxGeometry(0.30, 0.52, 0.036), toonMat(0x141724), 0.012);
  const spScrMat = new THREE.MeshBasicMaterial({{ map: phoneNormTex }});
  const spScr = new THREE.Mesh(new THREE.PlaneGeometry(0.265, 0.47), spScrMat);
  spScr.position.z = 0.022;
  standPhoneGrp.add(spBody, spScr);
  room.add(standPhoneGrp);

  // Crisp Labeled 3D Floating Notification Cards (Topic-Matched Swarm orbiting cleanly around phone!)
  function makeNotifBadgeTex(bgHex, label) {{
    const tc = document.createElement('canvas');
    tc.width = 160; tc.height = 110;
    const ctx = tc.getContext('2d');
    ctx.fillStyle = bgHex; ctx.fillRect(0, 0, 160, 110);
    ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = 8; ctx.strokeRect(6, 6, 148, 98);
    const txt = String(label || 'ALERT');
    const fs = txt.length <= 4 ? 44 : (txt.length <= 5 ? 36 : 30);
    ctx.fillStyle = '#FFFFFF'; ctx.font = `bold ${{fs}}px Arial`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(txt, 80, 58, 138);
    const tex = new THREE.CanvasTexture(tc);
    tex.encoding = THREE.sRGBEncoding;
    return tex;
  }}
  const badgeColors = ['#E11D48', '#F59E0B', '#3B82F6', '#E11D48', '#EC4899', '#F43F5E'];
  const badgeLabels = (Array.isArray(CFG.swarm_badges) && CFG.swarm_badges.length >= 6)
    ? CFG.swarm_badges.slice(0, 6)
    : ['99+', 'PING!', 'MSG', 'LIVE', 'LIKE', 'ALERT'];
  const notifSpecs = badgeLabels.map((lbl, idx) => [badgeColors[idx % badgeColors.length], lbl]);
  const notifMats = notifSpecs.map(([bg, lbl]) => new THREE.MeshBasicMaterial({{ map: makeNotifBadgeTex(bg, lbl) }}));

  const notifSwarm = new THREE.Group();
  room.add(notifSwarm);
  const notifCubes = [];
  for (let i = 0; i < 10; i++) {{
    const card = new THREE.Group();
    const box = outlinedMesh(new THREE.BoxGeometry(0.24, 0.16, 0.03), toonMat(0x1f2433), 0.008);
    const faceF = new THREE.Mesh(new THREE.PlaneGeometry(0.22, 0.145), notifMats[i % notifMats.length]);
    faceF.position.z = 0.018;
    const faceB = new THREE.Mesh(new THREE.PlaneGeometry(0.22, 0.145), notifMats[i % notifMats.length]);
    faceB.position.z = -0.018; faceB.rotation.y = Math.PI;
    card.add(box, faceF, faceB);
    notifSwarm.add(card);
    // Clean horseshoe halo behind/beside phone (always z/y spread, never colliding with camera!)
    const slotAng = -1.15 + (i / 9.0) * 2.30;
    notifCubes.push({{ mesh: card, slotAng, rad: 0.36 + (i % 3) * 0.14, baseY: 1.05 + (i % 4) * 0.24, ph: i * 0.85 }});
  }}
  notifSwarm.visible = false;

  // --- DEEP-WORK STUDY DESK ON LEFT WALL (-X = -2.25) ---
  const deskGrp = new THREE.Group();
  deskGrp.position.set(-2.22, 0, -0.55);
  deskGrp.rotation.y = Math.PI / 2;
  room.add(deskGrp);

  const deskTop = outlinedMesh(new THREE.BoxGeometry(2.35, 0.10, 0.92), toonMat(0x7c593c), 0.016);
  deskTop.position.set(0, 0.92, 0);
  deskGrp.add(deskTop);
  for (const dx of [-1.06, 1.06]) {{
    for (const dz of [-0.36, 0.36]) {{
      const dLeg = outlinedMesh(new THREE.BoxGeometry(0.10, 0.92, 0.10), woodDarkMat, 0.012);
      dLeg.position.set(dx, 0.46, dz);
      deskGrp.add(dLeg);
    }}
  }}
  // Open 3D Laptop facing right toward POV!
  const lapBase = outlinedMesh(new THREE.BoxGeometry(0.76, 0.04, 0.50), toonMat(0x334155), 0.012);
  lapBase.position.set(-0.08, 0.99, 0.04);
  const lapLid = outlinedMesh(new THREE.BoxGeometry(0.76, 0.50, 0.035), toonMat(0x1e293b), 0.012);
  lapLid.position.set(-0.08, 1.24, -0.22);
  lapLid.rotation.x = -0.14;
  const lapScr = new THREE.Mesh(new THREE.PlaneGeometry(0.70, 0.44), new THREE.MeshBasicMaterial({{ map: laptopTex }}));
  lapScr.position.set(-0.08, 1.24, -0.198);
  lapScr.rotation.x = -0.14;
  deskGrp.add(lapBase, lapLid, lapScr);

  // Warm Desk Lamp + Coffee Mug + Stacked Books
  const dlBase = outlinedMesh(new THREE.CylinderGeometry(0.12, 0.14, 0.05, 14), toonMat(0x14b8a6), 0.010);
  dlBase.position.set(0.78, 0.99, -0.18);
  const dlArm = outlinedMesh(new THREE.CylinderGeometry(0.025, 0.025, 0.62, 10), toonMat(0x334155), 0.008);
  dlArm.position.set(0.78, 1.30, -0.18);
  const dlHead = outlinedMesh(new THREE.ConeGeometry(0.18, 0.22, 14), toonMat(0xf59e0b), 0.012);
  dlHead.position.set(0.68, 1.56, -0.12);
  dlHead.rotation.z = 0.45;
  const mug = outlinedMesh(new THREE.CylinderGeometry(0.075, 0.068, 0.16, 14), toonMat(0xf8fafc), 0.010);
  mug.position.set(0.55, 1.05, 0.22);
  const book1 = outlinedMesh(new THREE.BoxGeometry(0.38, 0.08, 0.28), toonMat(0x14b8a6), 0.010);
  book1.position.set(-0.78, 1.01, -0.05);
  const book2 = outlinedMesh(new THREE.BoxGeometry(0.34, 0.08, 0.25), toonMat(0xfbbf24), 0.010);
  book2.position.set(-0.76, 1.09, -0.04);
  book2.rotation.y = 0.18;
  deskGrp.add(dlBase, dlArm, dlHead, mug, book1, book2);

  // --- ARTICULATED 3D PARTNER CHARACTER: "YOUR PREFRONTAL CORTEX" (Teal Beanie + HabitSains Amber/Navy Puffer!) ---
  const partner = new THREE.Group();
  partner.position.set(0.05, 0, -1.35);
  room.add(partner);

  const jacketMat = toonMat(0x1e3a5f);
  const jacketRingMat = toonMat(0x132642);
  const beanieMat = toonMat(0x14b8a6);
  const beanieRibMat = toonMat(0x0d9488);
  const skinMat = toonMat(0xe6dcc8);
  const pantsMat = toonMat(0x283244);
  const eyeMat = new THREE.MeshBasicMaterial({{ color: 0x10131a }});
  const whiteMat = new THREE.MeshBasicMaterial({{ color: 0xffffff }});
  const mouthMat = new THREE.MeshBasicMaterial({{ color: 0x5c1922 }});

  for (const sx of [-0.17, 0.17]) {{
    const leg = outlinedMesh(new THREE.CylinderGeometry(0.145, 0.135, 0.85, 14), pantsMat, 0.018);
    leg.position.set(sx, 0.45, 0);
    const shoe = outlinedMesh(new THREE.BoxGeometry(0.24, 0.14, 0.36), toonMat(0xf59e0b), 0.014);
    shoe.position.set(sx, 0.07, 0.06);
    partner.add(leg, shoe);
  }}
  const belt = outlinedMesh(new THREE.TorusGeometry(0.35, 0.042, 8, 22), toonMat(0x0f172a), 0.014);
  belt.rotation.x = Math.PI / 2; belt.position.y = 0.88;
  partner.add(belt);

  const torso = new THREE.Group();
  torso.position.y = 1.32;
  partner.add(torso);
  const tBody = outlinedMesh(new THREE.CylinderGeometry(0.34, 0.31, 0.88, 18), jacketMat, 0.022);
  torso.add(tBody);
  for (const ry of [-0.26, -0.02, 0.22]) {{
    const baffle = outlinedMesh(new THREE.TorusGeometry(0.345, 0.032, 8, 22), jacketRingMat, 0.010);
    baffle.rotation.x = Math.PI / 2; baffle.position.y = ry;
    torso.add(baffle);
  }}
  // Vibrant Amber Collar & Zipper Accent (HabitSains Palette!)
  const collar = outlinedMesh(new THREE.TorusGeometry(0.24, 0.075, 10, 20), toonMat(0xf59e0b), 0.016);
  collar.rotation.x = Math.PI / 2; collar.position.y = 0.44;
  const zip = outlinedMesh(new THREE.BoxGeometry(0.036, 0.86, 0.04), toonMat(0xf59e0b), 0.008);
  zip.position.set(0, 0, 0.34);
  const zipTab = outlinedMesh(new THREE.BoxGeometry(0.07, 0.11, 0.05), toonMat(0x2dd4bf), 0.008);
  zipTab.position.set(0, 0.33, 0.36);
  torso.add(collar, zip, zipTab);

  // Head + Expressive Eyes + Talking Mouth + Signature Teal Ribbed Beanie!
  const headGrp = new THREE.Group();
  headGrp.position.y = 0.78;
  torso.add(headGrp);
  headGrp.add(outlinedMesh(new THREE.SphereGeometry(0.36, 22, 18), skinMat, 0.022));

  for (const ex of [-0.125, 0.125]) {{
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.056, 12, 12), eyeMat);
    eye.scale.set(0.84, 1.26, 0.45);
    eye.position.set(ex, 0.02, 0.335);
    const gl = new THREE.Mesh(new THREE.SphereGeometry(0.020, 8, 8), whiteMat);
    gl.position.set(ex - 0.014, 0.052, 0.358);
    headGrp.add(eye, gl);
  }}
  const mouth = new THREE.Mesh(new THREE.SphereGeometry(0.055, 12, 10), mouthMat);
  mouth.scale.set(1.15, 0.45, 0.4);
  mouth.position.set(0, -0.115, 0.345);
  headGrp.add(mouth);

  const beanieDome = outlinedMesh(new THREE.SphereGeometry(0.375, 22, 14, 0, Math.PI * 2, 0, Math.PI * 0.52), beanieMat, 0.020);
  beanieDome.position.y = 0.06;
  const cuff = outlinedMesh(new THREE.CylinderGeometry(0.39, 0.395, 0.145, 22), beanieMat, 0.018);
  cuff.position.y = 0.11;
  // Tiny amber badge right on center front of cuff!
  const badge = outlinedMesh(new THREE.BoxGeometry(0.11, 0.09, 0.04), toonMat(0xfbbf24), 0.008);
  badge.position.set(0, 0.11, 0.40);
  headGrp.add(beanieDome, cuff, badge);
  for (let r = 0; r < 14; r++) {{
    const ang = (r / 14) * Math.PI * 2;
    const rib = outlinedMesh(new THREE.BoxGeometry(0.024, 0.145, 0.03), beanieRibMat, 0.005);
    rib.position.set(Math.cos(ang) * 0.395, 0.11, Math.sin(ang) * 0.395);
    rib.rotation.y = -ang;
    headGrp.add(rib);
  }}

  function buildArm(side) {{
    const sh = new THREE.Group();
    sh.position.set(side * 0.42, 0.30, 0);
    const puff = outlinedMesh(new THREE.SphereGeometry(0.145, 14, 12), jacketMat, 0.016);
    const upper = outlinedMesh(new THREE.CylinderGeometry(0.115, 0.105, 0.56, 14), jacketMat, 0.016);
    upper.position.y = -0.28;
    const armRing = outlinedMesh(new THREE.TorusGeometry(0.118, 0.024, 8, 16), jacketRingMat, 0.008);
    armRing.rotation.x = Math.PI / 2; armRing.position.y = -0.28;
    const hand = outlinedMesh(new THREE.SphereGeometry(0.11, 14, 12), skinMat, 0.015);
    hand.scale.set(0.95, 0.72, 1.15); hand.position.y = -0.60;
    sh.add(puff, upper, armRing, hand);
    return sh;
  }}
  const armL = buildArm(-1);
  const armR = buildArm(1);
  torso.add(armL, armR);

  // 3D Brain Scan Tablet Prop on Partner's Left Hand!
  const scanProp = new THREE.Group();
  const scanBody = outlinedMesh(new THREE.BoxGeometry(0.42, 0.56, 0.038), toonMat(0x111827), 0.012);
  const scanScrF = new THREE.Mesh(new THREE.PlaneGeometry(0.38, 0.51), new THREE.MeshBasicMaterial({{ map: brainScanTex }}));
  scanScrF.position.z = 0.022;
  const scanScrB = new THREE.Mesh(new THREE.PlaneGeometry(0.38, 0.51), new THREE.MeshBasicMaterial({{ map: brainScanTex }}));
  scanScrB.position.z = -0.022; scanScrB.rotation.y = Math.PI;
  scanProp.add(scanBody, scanScrF, scanScrB);
  scanProp.position.set(0.06, -0.68, 0.08);
  scanProp.rotation.set(Math.PI * 0.52, 0.14, 0.06);
  scanProp.visible = false;
  armL.add(scanProp);

  // --- FIRST-PERSON POV CARTOON HANDS (Warm Hoodie Sleeves) ---
  const povHands = new THREE.Group();
  camera.add(povHands);
  const povSkinMat = toonMat(0xdca87c);
  const hoodieMat = toonMat(0x2a3b4e);
  function buildPovHand(side) {{
    const g = new THREE.Group();
    const fist = outlinedMesh(new THREE.SphereGeometry(0.112, 14, 12), povSkinMat, 0.012);
    fist.scale.set(1.04, 0.84, 1.32);
    const thumb = outlinedMesh(new THREE.SphereGeometry(0.056, 10, 10), povSkinMat, 0.009);
    thumb.position.set(-side * 0.086, 0.02, 0.02);
    const cuff = outlinedMesh(new THREE.CylinderGeometry(0.095, 0.11, 0.28, 12), hoodieMat, 0.012);
    cuff.rotation.x = Math.PI / 2; cuff.position.z = 0.22;
    g.add(fist, thumb, cuff);
    g.position.set(side * 0.24, -0.28, -0.52);
    return g;
  }}
  const povHandL = buildPovHand(-1);
  const povHandR = buildPovHand(1);
  povHands.add(povHandL, povHandR);

  // --- CHOREOGRAPHED 3D FRAME RENDERER ---
  const lerp = (a, b, u) => a + (b - a) * Math.max(0, Math.min(1, u));
  const smooth = u => {{ const x = Math.max(0, Math.min(1, u)); return x * x * (3 - 2 * x); }};

  const T_TRAP = CFG.t_trap;
  const T_EXPLAIN = CFG.t_explain;
  const T_TIMER = CFG.t_timer;
  const T_SCAN = CFG.t_scan;
  const T_DESK = CFG.t_desk;
  const T_AGREE = (typeof CFG.t_agree === 'number') ? CFG.t_agree : (T_DESK + (CFG.t_ping - T_DESK) * 0.62);
  const T_PING = CFG.t_ping;
  const T_END = CFG.t_endcard;

  const locEl = document.getElementById('locStamp');
  const serEl = document.getElementById('seriesBanner');
  const tmEl = document.getElementById('timerHud');
  const tmVal = document.getElementById('timerVal');
  const barFill = document.getElementById('focusBarFill');
  const capEl = document.getElementById('focusCap');
  const subEl = document.getElementById('subText');
  const endEl = document.getElementById('endCard');

  window.renderAt = function(t) {{
    if (t >= T_END) {{
      const eP = smooth((t - T_END) / 0.35);
      endEl.style.opacity = eP.toFixed(3);
      subEl.textContent = '';
      tmEl.style.opacity = '0';
      locEl.style.opacity = '0';
      serEl.style.opacity = '0';
      return;
    }}
    endEl.style.opacity = '0';

    // 1. Alarm clock rattle during intro + phone vibrate/urgent mode during ping!
    if (t < 1.8) {{
      alarmGrp.rotation.z = Math.sin(t * 48) * 0.14;
    }} else {{
      alarmGrp.rotation.z = 0;
    }}

    const isUrgent = t >= T_PING;
    spScrMat.map = isUrgent ? phoneUrgentTex : phoneNormTex;
    spScrMat.needsUpdate = true;

    let camShake = 0.0;
    let phoneVib = 0.0;
    for (const pOff of [0.0, 0.54, 1.08]) {{
      const age = t - (T_PING + pOff);
      if (age >= 0 && age < 0.34) {{
        const imp = Math.sin((age / 0.34) * Math.PI);
        phoneVib = Math.max(phoneVib, imp);
        camShake = Math.max(camShake, 0.032 * imp);
      }}
    }}
    standPhoneGrp.position.x = 1.74 + Math.sin(t * 68) * 0.025 * phoneVib;
    standPhoneGrp.rotation.z = Math.sin(t * 72) * 0.09 * phoneVib;

    // 2. Red Notification Card Halo erupting cleanly around smartphone in Beat 2 (Dopamine Trap!)
    const trapActive = (t >= T_TRAP && t < T_EXPLAIN);
    notifSwarm.visible = trapActive;
    if (trapActive) {{
      const p = smooth((t - T_TRAP) / 0.50);
      for (const nc of notifCubes) {{
        const sw = Math.sin(t * 2.6 + nc.ph) * 0.14;
        const a = nc.slotAng + sw;
        // Fan out across YZ plane right around the glowing phone (x stays safely >= 1.50, zero camera clipping!)
        const rx = 1.66 + Math.abs(Math.sin(a)) * 0.18;
        const rz = 1.32 + Math.sin(a) * nc.rad * (0.45 + 0.75 * p);
        const ry = nc.baseY + Math.cos(a) * 0.26 * p + Math.sin(t * 4.2 + nc.ph) * 0.05;
        nc.mesh.position.set(rx, ry, rz);
        nc.mesh.rotation.set(Math.sin(t * 3 + nc.ph) * 0.12, -Math.PI * 0.56 + sw * 0.4, Math.cos(t * 2.5 + nc.ph) * 0.12);
      }}
      alertLight.intensity = 1.35 * p;
      camShake = Math.max(camShake, 0.038 * Math.max(0, 1 - (t - T_TRAP) / 0.7));
    }} else if (isUrgent) {{
      alertLight.intensity = 0.55 + 1.15 * phoneVib;
    }} else {{
      alertLight.intensity = 0.0;
    }}
    roomLamp.intensity = 1.05 - alertLight.intensity * 0.22;

    // 3. First-Person POV Camera Choreography across 6 HabitSains Beats!
    let camPos = new THREE.Vector3(0.45, 1.45, 1.45);
    let lookAt = new THREE.Vector3(1.75, 1.12, 1.32);
    let reachR = 0.0;
    let handRaise = 0.0;

    if (t < T_TRAP) {{
      // Beat 1: Waking up in bed at 7:01 AM looking over at the nightstand alarm & glowing phone!
      const u = smooth(t / T_TRAP);
      camPos.set(lerp(0.35, 0.62, u), lerp(1.40, 1.38, u), lerp(1.65, 1.38, u));
      lookAt.set(lerp(1.90, 1.74, u), lerp(1.06, 1.13, u), lerp(1.22, 1.32, u));
      reachR = lerp(0.0, 0.62, smooth((t - 1.2) / 2.2));
    }} else if (t < T_EXPLAIN) {{
      // Beat 2: STOP! POV recoils back in shock as glowing notification badges erupt in a halo around the phone!
      const u = smooth((t - T_TRAP) / 0.75);
      camPos.set(lerp(0.62, 0.34, u), lerp(1.38, 1.44, u), lerp(1.38, 1.34, u));
      lookAt.set(1.74, lerp(1.13, 1.24, u), 1.32);
      handRaise = 0.32;
    }} else if (t < T_SCAN) {{
      // Beat 3 & 4: Facing Prefrontal Cortex Partner cleanly inside bedroom (+ FOCUS WINDOW HUD headroom!)
      const u = smooth((t - T_EXPLAIN) / 0.85);
      camPos.set(lerp(0.34, 0.05, u), lerp(1.44, 1.88, u), lerp(1.34, 0.65, u));
      lookAt.set(lerp(1.74, 0.05, u), lerp(1.24, 1.84, u), lerp(1.32, -1.35, u));
      handRaise = 0.06;
    }} else if (t < T_DESK) {{
      // Beat 5: Partner raises 3D Brain Scan Tablet (-40% FOCUS / CRASH LASTS 6 HOURS)!
      const u = smooth((t - T_SCAN) / 0.65);
      camPos.set(lerp(0.05, -0.04, u), 1.84, lerp(0.65, 0.38, u));
      lookAt.set(-0.08, 1.82, -1.35);
      handRaise = 0.02;
    }} else if (t < T_PING) {{
      // Beat 6: POV pans LEFT to inspect the 3D Deep-Work Study Desk & Laptop, then turns back to Partner on T_AGREE!
      const local = t - T_DESK;
      const splitAt = Math.max(1.2, T_AGREE - T_DESK);
      if (local < splitAt) {{
        const u = smooth(local / 0.90);
        camPos.set(lerp(-0.04, -0.58, u), lerp(1.84, 1.54, u), lerp(0.38, -0.45, u));
        lookAt.set(lerp(-0.08, -2.22, u), lerp(1.82, 1.24, u), lerp(-1.35, -0.55, u));
      }} else {{
        const u = smooth((local - splitAt) / 0.75);
        camPos.set(lerp(-0.58, 0.05, u), lerp(1.54, 1.84, u), lerp(-0.45, 0.48, u));
        lookAt.set(lerp(-2.22, 0.05, u), lerp(1.24, 1.84, u), lerp(-0.55, -1.35, u));
        handRaise = lerp(0.05, 0.25, u);
      }}
    }} else {{
      // Beat 7: BUZZ! BUZZ! BUZZ! POV snaps RIGHT back to the nightstand phone glowing red (3 URGENT ALERTS)!
      const u = smooth((t - T_PING) / 0.55);
      camPos.set(lerp(0.05, 0.68, u), lerp(1.84, 1.32, u), lerp(0.48, 1.34, u));
      lookAt.set(lerp(0.05, 1.74, u), lerp(1.84, 1.07, u), lerp(-1.35, 1.32, u));
      reachR = lerp(0.0, 0.55, smooth((t - (T_PING + 1.1)) / 1.8));
      handRaise = 0.16;
    }}

    const sx = Math.sin(t * 47) * camShake;
    const sy = Math.sin(t * 2.6) * 0.020 + Math.cos(t * 53) * camShake;
    camera.position.set(camPos.x + sx, camPos.y + sy, camPos.z);
    camera.lookAt(lookAt);

    // Animate POV foreground hands (right hand reaches toward phone during temptation beats!)
    const hb = Math.sin(t * 3.0) * 0.012;
    povHandL.position.set(-0.24, -0.28 + handRaise * 0.14 + hb, -0.52);
    povHandR.position.set(0.24 - reachR * 0.08, -0.28 + handRaise * 0.14 + reachR * 0.12 - hb, -0.52 - reachR * 0.16);
    povHandL.rotation.set(handRaise * 0.42, 0.24, -0.16);
    povHandR.rotation.set(handRaise * 0.42 - reachR * 0.35, -0.24, 0.16);

    // 4. Partner Acting & Lip-Sync
    let activeLine = null;
    for (const dl of CFG.dialogue) {{
      if (t >= dl.start && t <= dl.end + 0.12) {{
        activeLine = dl;
        break;
      }}
    }}
    const partnerSpeaking = activeLine && activeLine.speaker === 'partner';
    mouth.scale.y = partnerSpeaking ? (0.45 + 0.85 * Math.abs(Math.sin(t * 16.5))) : 0.36;
    headGrp.rotation.y = Math.sin(t * 1.4) * 0.09;
    headGrp.rotation.z = Math.sin(t * 1.9) * 0.05;

    const scanIn = (t >= T_SCAN && t < T_DESK)
      ? Math.min(smooth((t - T_SCAN) / 0.55), smooth((T_DESK - t) / 0.45))
      : 0;
    scanProp.visible = scanIn > 0.05;
    armL.rotation.x = lerp(partnerSpeaking ? (-0.45 + Math.sin(t * 4.5 + 1) * 0.22) : -0.12, -1.78, scanIn);
    armL.rotation.z = lerp(-0.14, 0.25, scanIn);
    armR.rotation.x = partnerSpeaking ? (-0.42 + Math.sin(t * 5.2) * 0.24) : -0.14;
    armR.rotation.z = 0.14;

    // 5. HUD Overlays
    const introA = t < T_TRAP ? Math.min(smooth(t / 0.4), smooth((T_TRAP - t) / 0.45)) : 0;
    locEl.style.opacity = introA.toFixed(3);
    serEl.style.opacity = introA.toFixed(3);

    if (t >= T_TIMER) {{
      tmEl.style.opacity = smooth((t - T_TIMER) / 0.35).toFixed(3);
      const elapsedSec = Math.max(0, Math.floor(t - T_TIMER));
      const rem = Math.max(0, 6 * 3600 - 1 - elapsedSec);
      const hh = Math.floor(rem / 3600);
      const mm = Math.floor((rem % 3600) / 60);
      const ss = rem % 60;
      tmVal.textContent = `${{String(hh).padStart(2,'0')}}:${{String(mm).padStart(2,'0')}}:${{String(ss).padStart(2,'0')}}`;

      // Animate live Focus Capacity bar dropping from 100% -> 60% during scan/ping!
      let pct = 100;
      if (t >= T_PING) {{
        pct = Math.round(lerp(60, 42, smooth((t - T_PING) / 2.5)));
      }} else if (t >= T_SCAN) {{
        pct = Math.round(lerp(100, 60, smooth((t - T_SCAN) / 2.0)));
      }}
      barFill.style.width = `${{pct}}%`;
      barFill.style.background = pct > 75 ? '#2DD4BF' : (pct > 50 ? '#F59E0B' : '#F43F5E');
      capEl.textContent = pct <= 55 ? `FOCUS AT RISK: ${{pct}}%` : `BRAIN FOCUS: ${{pct}}%`;
    }} else {{
      tmEl.style.opacity = '0';
    }}

    if (activeLine) {{
      const words = activeLine.text.split(/\\s+/);
      const chunkSz = 5;
      const chunks = [];
      for (let i = 0; i < words.length; i += chunkSz) chunks.push(words.slice(i, i + chunkSz).join(' '));
      const frac = Math.max(0, Math.min(0.999, (t - activeLine.start) / Math.max(activeLine.end - activeLine.start, 0.2)));
      subEl.textContent = chunks[Math.floor(frac * chunks.length)] || activeLine.text;
      subEl.style.color = (activeLine.speaker === 'partner') ? '#F8D43C' : '#FFFFFF';
    }} else {{
      subEl.textContent = '';
    }}

    renderer.render(scene, camera);
  }};
}})();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Full HabitSains 3D POV Episode Demo Builder ("THE 7 AM TRAP • Part 1")
# ---------------------------------------------------------------------------

HABITSAINS_7AM_SCRIPT: list[dict[str, Any]] = [
    {"beat": "intro", "speaker": "pov", "text": "Ugh... seven AM already. Let me just check my phone for two minutes."},
    {"beat": "trap", "speaker": "partner", "text": "STOP! Don't touch that screen! You're walking straight into the seven AM dopamine trap!"},
    {"beat": "explain", "speaker": "partner", "text": "Listen closely. Your brain wakes up with clean baseline dopamine. One scroll session spikes it artificially... then crashes your focus for the next six hours."},
    {"beat": "timer_react", "speaker": "pov", "text": "Wait... six whole hours ruined from two minutes?!"},
    {"beat": "scan", "speaker": "partner", "text": "Look at the scan. Your focus capacity drops forty percent, and every hard task feels unbearable."},
    {"beat": "desk", "speaker": "partner", "text": "That project on your desk needs deep work today... not a fried reward system."},
    {"beat": "agree", "speaker": "pov", "text": "Okay, okay... I won't check it."},
    {"beat": "ping", "speaker": "partner", "text": "There it goes—three urgent alerts hitting at once. Your hand is already reaching for it!"},
]


def build_habitsains_3d_pov_demo(
    out_mp4: Path,
    width: int = 720,
    height: int = 1280,
    fps: int = 24,
) -> dict[str, Any]:
    """Render complete HabitSains 3D Cel-Shaded First-Person POV Demo ('THE 7 AM TRAP • Part 1')."""
    from playwright.sync_api import sync_playwright

    project_root = Path(__file__).resolve().parent.parent
    three_js_path = project_root / "assets" / "vendor" / "three.min.js"
    if not three_js_path.exists():
        raise FileNotFoundError(f"Missing local Three.js bundle at {three_js_path}")

    work_dir = out_mp4.parent / "_hs_3d_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    voice_partner = "en-US-ChristopherNeural"
    voice_pov = "en-US-AndrewMultilingualNeural"

    dialogue_events: list[dict[str, Any]] = []
    beat_starts: dict[str, float] = {}
    cursor = 0.70

    print("[v9-habitsains] Synthesizing 2-speaker neuroscience POV dialogue...", flush=True)
    for idx, line in enumerate(HABITSAINS_7AM_SCRIPT):
        mp3 = work_dir / f"dlg_{idx:02d}.mp3"
        wav = work_dir / f"dlg_{idx:02d}.wav"
        voice = voice_partner if line["speaker"] == "partner" else voice_pov
        rate = "+5%" if line["speaker"] == "partner" else "+6%"
        dur = asyncio.run(_synth_edge_line(line["text"], mp3, voice=voice, rate=rate))
        subprocess.run(["ffmpeg", "-y", "-i", str(mp3), "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(wav)], capture_output=True, check=True)

        if line["beat"] == "trap":
            cursor += 0.25
        elif line["beat"] == "explain":
            cursor += 0.55
        elif line["beat"] == "ping":
            cursor += 1.35

        beat_starts[line["beat"]] = cursor
        dialogue_events.append({
            "beat": line["beat"],
            "speaker": line["speaker"],
            "text": line["text"],
            "start": round(cursor, 3),
            "end": round(cursor + dur, 3),
            "wav_path": str(wav),
        })
        cursor += dur + 0.34

    t_trap = beat_starts["trap"] - 0.15
    t_explain = beat_starts["explain"] - 0.35
    t_timer = beat_starts["timer_react"] - 0.25
    t_scan = beat_starts["scan"] - 0.25
    t_desk = beat_starts["desk"] - 0.25
    t_ping = beat_starts["ping"] - 1.25
    t_endcard = cursor + 0.55
    total_dur = t_endcard + 4.4

    print(f"[v9-habitsains] Mixing HabitSains cognitive thriller soundscape (total {total_dur:.1f}s)...", flush=True)
    audio_m4a = work_dir / "master_habitsains.m4a"
    _build_habitsains_soundscape(
        dialogue_events=dialogue_events,
        total_dur=total_dur,
        trap_time=t_trap,
        timer_time=t_timer,
        ping_time=t_ping,
        endcard_time=t_endcard,
        out_m4a=audio_m4a,
        work_dir=work_dir,
    )

    timeline_cfg = {
        "t_trap": round(t_trap, 3),
        "t_explain": round(t_explain, 3),
        "t_timer": round(t_timer, 3),
        "t_scan": round(t_scan, 3),
        "t_desk": round(t_desk, 3),
        "t_ping": round(t_ping, 3),
        "t_endcard": round(t_endcard, 3),
        "dialogue": [
            {"speaker": e["speaker"], "text": e["text"], "start": e["start"], "end": e["end"]}
            for e in dialogue_events
        ],
    }

    html_doc = _build_habitsains_3d_html(three_js_path.read_text(encoding="utf-8"), timeline_cfg, width, height)
    total_frames = int(round(total_dur * fps))
    silent_mp4 = work_dir / "video_hs_3d_silent.mp4"

    print(f"[v9-habitsains] Rendering {total_frames} real 3D WebGL toon frames ({width}x{height} @ {fps}fps)...", flush=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "image2pipe", "-vcodec", "mjpeg", "-r", str(fps), "-i", "pipe:0",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-an",
        str(silent_mp4),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert proc.stdin is not None

    with sync_playwright() as pw:
        chrome = find_chrome_executable()
        launch_kw: dict[str, Any] = {
            "headless": True,
            "args": ["--no-sandbox", "--enable-webgl", "--ignore-gpu-blocklist", "--use-gl=angle", "--use-angle=swiftshader"],
        }
        if chrome:
            launch_kw["executable_path"] = chrome
        br = pw.chromium.launch(**launch_kw)
        page = br.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        page.set_content(html_doc, wait_until="load")

        last_end_jpg: bytes | None = None
        try:
            for f_i in range(total_frames):
                t = f_i / float(fps)
                if t > t_endcard + 0.45 and last_end_jpg is not None:
                    proc.stdin.write(last_end_jpg)
                    continue
                page.evaluate(f"window.renderAt({t:.4f})")
                jpg_bytes = page.screenshot(type="jpeg", quality=92)
                if t > t_endcard + 0.45:
                    last_end_jpg = jpg_bytes
                proc.stdin.write(jpg_bytes)
                if f_i > 0 and f_i % 240 == 0:
                    print(f"[v9-habitsains] Rendered {f_i}/{total_frames} frames ({100*f_i/total_frames:.0f}%)...", flush=True)
        finally:
            br.close()
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()

    err = proc.stderr.read().decode("utf-8", errors="ignore") if proc.stderr else ""
    ret = proc.wait()
    if ret != 0:
        raise RuntimeError(f"FFmpeg HabitSains v9 3D pipe failed ({ret}): {err[-300:]}")

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(silent_mp4), "-i", str(audio_m4a),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest",
            str(out_mp4),
        ],
        capture_output=True, check=True,
    )

    for p in work_dir.glob("*"):
        p.unlink(missing_ok=True)
    try:
        work_dir.rmdir()
    except OSError:
        pass

    return {
        "output": str(out_mp4),
        "duration_sec": round(total_dur, 2),
        "size_mb": round(out_mp4.stat().st_size / (1024 * 1024), 2),
        "beats": {
            "intro": 2.0,
            "trap": round(t_trap + 1.8, 2),
            "explain": round(t_explain + 2.2, 2),
            "timer": round(t_timer + 0.7, 2),
            "scan": round(t_scan + 2.2, 2),
            "desk": round(t_desk + 1.8, 2),
            "ping": round(t_ping + 2.0, 2),
            "endcard": round(t_endcard + 1.5, 2),
        },
    }


# ---------------------------------------------------------------------------
# Dynamic Pipeline Adapter (Any Daily Topic -> 3D Cel-Shaded POV Episode!)
# ---------------------------------------------------------------------------

def _mix_pipeline_audio_with_sfx(
    master_voice_path: Path,
    total_dur: float,
    trap_time: float,
    timer_time: float,
    ping_time: float,
    endcard_time: float,
    out_m4a: Path,
    work_dir: Path,
) -> Path:
    """Layer pipeline voiceover with HabitSains 3D POV cognitive thriller SFX + ambient bed."""
    alarm_wav = work_dir / "_pl_alarm.wav"
    slam_wav = work_dir / "_pl_slam.wav"
    beep_wav = work_dir / "_pl_beep.wav"
    ping_wav = work_dir / "_pl_ping.wav"
    boom_wav = work_dir / "_pl_boom.wav"

    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                "aevalsrc='0.42*sin(2*PI*880*t)*(gte(mod(t,0.42),0.0)*lt(mod(t,0.42),0.14)+gte(mod(t,0.42),0.18)*lt(mod(t,0.42),0.30))*exp(-1.1*t)':s=44100:d=1.35",
                "-af", "lowpass=f=2400,volume=-12dB", "-c:a", "pcm_s16le", str(alarm_wav),
            ],
            capture_output=True, check=True,
        )
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                "aevalsrc='(0.85*sin(2*PI*(110-65*t)*t)*exp(-6.5*t)+0.35*sin(2*PI*520*t)*exp(-14*t))':s=44100:d=0.60",
                "-af", "lowpass=f=1500,volume=-7dB", "-c:a", "pcm_s16le", str(slam_wav),
            ],
            capture_output=True, check=True,
        )
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                "aevalsrc='0.55*sin(2*PI*1240*t)*exp(-16*t)':s=44100:d=0.18",
                "-af", "volume=-13dB", "-c:a", "pcm_s16le", str(beep_wav),
            ],
            capture_output=True, check=True,
        )
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                "aevalsrc='(0.55*sin(2*PI*1320*t)*exp(-16*t)+0.40*sin(2*PI*1760*t)*exp(-14*max(0,t-0.06))*gte(t,0.06)+0.45*sin(2*PI*135*t)*exp(-9*t))':s=44100:d=0.35",
                "-af", "lowpass=f=3200,volume=-6dB", "-c:a", "pcm_s16le", str(ping_wav),
            ],
            capture_output=True, check=True,
        )
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                "aevalsrc='0.9*sin(2*PI*(62-22*t)*t)*exp(-1.9*t)':s=44100:d=1.5",
                "-af", "lowpass=f=240,volume=-6dB", "-c:a", "pcm_s16le", str(boom_wav),
            ],
            capture_output=True, check=True,
        )

        drone_expr = "0.24*sin(2*PI*65.41*t)+0.18*sin(2*PI*98.0*t)+0.11*sin(2*PI*130.81*t)*(0.72+0.28*sin(2*PI*0.32*t))"
        inputs: list[str] = [
            "-f", "lavfi", "-t", f"{total_dur:.2f}", "-i", f"aevalsrc='{drone_expr}':s=44100:c=stereo",
            "-i", str(master_voice_path),
            "-i", str(alarm_wav),
            "-i", str(slam_wav),
            "-i", str(beep_wav),
            "-i", str(boom_wav),
        ]
        filters: list[str] = [
            f"[0:a]lowpass=f=280,volume=-24dB,afade=t=in:st=0:d=0.7,afade=t=out:st={max(total_dur - 1.2, 0.5):.2f}:d=1.1[drone]",
            f"[1:a]aresample=44100,aformat=channel_layouts=stereo,apad=whole_dur={total_dur:.2f},volume=+1.0dB[voice]",
            "[2:a]adelay=80:all=1,aformat=channel_layouts=stereo[alarm]",
            f"[3:a]adelay={max(int(trap_time * 1000), 0)}:all=1,aformat=channel_layouts=stereo[slam]",
            f"[4:a]adelay={max(int(timer_time * 1000), 0)}:all=1,aformat=channel_layouts=stereo[beep]",
            f"[5:a]adelay={max(int(endcard_time * 1000), 0)}:all=1,aformat=channel_layouts=stereo[boom]",
        ]
        mix = ["[drone]", "[voice]", "[alarm]", "[slam]", "[beep]", "[boom]"]
        nxt = 6
        for p_i, p_off in enumerate((0.0, 0.52, 1.04)):
            ms = max(int((ping_time + p_off) * 1000), 0)
            inputs.extend(["-i", str(ping_wav)])
            filters.append(f"[{nxt}:a]adelay={ms}:all=1,aformat=channel_layouts=stereo[pg{p_i}]")
            mix.append(f"[pg{p_i}]")
            nxt += 1

        filters.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:dropout_transition=2:normalize=0,alimiter=limit=0.95[out]")
        subprocess.run(
            ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", str(out_m4a)],
            capture_output=True, text=True, check=True,
        )
        return out_m4a
    finally:
        for f in (alarm_wav, slam_wav, beep_wav, ping_wav, boom_wav):
            f.unlink(missing_ok=True)


def _derive_dynamic_pov_labels(scenes_meta: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, str]:
    """Dynamically tailor 3D bedroom/desk props, HUD badges, and A/B cliffhanger to ANY daily topic."""
    handle = str(config.get("branding", {}).get("watermark_text", "@HabitSains"))
    all_text = " ".join(
        f"{s.get('visual_headline', '')} {s.get('on_screen_callout', '')} {s.get('narration', '')}"
        for s in scenes_meta
    )
    low = all_text.lower()

    # Location & time stamp
    if any(k in low for k in ("sleep", "bed", "night", "midnight", "insomnia", "evening")):
        loc_main, phone_time = "YOUR BEDROOM • 11:42 PM", "11:42"
    elif any(k in low for k in ("morning", "wake", "7 am", "7:00", "alarm", "sunlight")):
        loc_main, phone_time = "YOUR BEDROOM • 7:01 AM", "7:01"
    else:
        loc_main, phone_time = "YOUR DESK • 2:14 PM", "2:14"

    # Short punchy 2-4 word Series Banner title from Scene 1 visual headline
    raw_hl = str(scenes_meta[0].get("visual_headline", "") if scenes_meta else "").strip()
    clean_hl = re.sub(r"[^A-Za-z0-9\s\-]", "", raw_hl).strip()
    hl_words = [w for w in clean_hl.split() if w][:4]
    series_title = " ".join(hl_words).upper() if hl_words else "THE FOCUS TRAP"
    if len(series_title) > 22:
        series_title = " ".join(hl_words[:3]).upper()[:22]

    # Extract any sharp numeric stat (e.g. "40%", "23 min", "6 hours") for the 3D Brain Scan Tablet!
    stat_match = re.search(r"(\d{1,3}\s?%|\d{1,2}\s?(?:min|minutes|hours|hrs|days))", all_text, re.IGNORECASE)
    if stat_match:
        tok = stat_match.group(1).upper().replace("MINUTES", "MIN").replace("HOURS", "HRS")
        scan_stat = f"-{tok} FOCUS" if "%" in tok else f"{tok} COST"
    else:
        scan_stat = "-40% FOCUS"

    mid_scene = scenes_meta[len(scenes_meta) // 2] if scenes_meta else {}
    mid_hl = re.sub(r"[^A-Za-z0-9\s\-]", "", str(mid_scene.get("visual_headline", ""))).strip().upper()
    scan_sub = (mid_hl[:24] if mid_hl else "DOPAMINE CRASH EFFECT")

    # Laptop project headline
    lap_title = str(mid_scene.get("on_screen_callout") or raw_hl or "Core Deep Work Session").strip()[:28]

    # Tailored interactive [A]/[B] decision card
    if any(k in low for k in ("sleep", "night", "bed", "rest")):
        opt_a = "PHONE OUTSIDE BEDROOM & SLEEP ON TIME"
        opt_b = '"ONE MORE VIDEO" UNTIL 1:00 AM'
    elif any(k in low for k in ("procrastin", "start", "deadline", "work", "study")):
        opt_a = "AIRPLANE MODE & 5-MINUTE FOCUS SPRINT"
        opt_b = "CHECK 1 MESSAGE & LOSE 23 MINUTES"
    elif any(k in low for k in ("dopamine", "scroll", "phone", "social", "screen")):
        opt_a = "LOCK PHONE IN ANOTHER ROOM (60 MIN)"
        opt_b = '"JUST TWO MINUTES" OF AUTOPILOT SCROLLING'
    else:
        opt_a = "PROTECT 60 MIN OF DISTRACTION-FREE FOCUS"
        opt_b = "GIVE IN TO AUTOPILOT DISTRACTIONS"

    return {
        "loc_main": loc_main,
        "loc_sub": f"{handle} • Part 1",
        "series_eyebrow": "HABITSAINS POV",
        "series_title": series_title,
        "timer_label": "FOCUS WINDOW",
        "phone_time": phone_time,
        "phone_norm_hdr": "19 NOTIFICATIONS",
        "phone_urgent_hdr": "3 URGENT ALERTS!",
        "scan_title": "NEURAL FOCUS SCAN",
        "scan_stat": scan_stat,
        "scan_sub": scan_sub,
        "laptop_hdr": "DEEP WORK • PRIORITY",
        "laptop_due": "DUE TODAY",
        "laptop_title": lap_title,
        "laptop_status": "|  (Waiting for deep focus...)",
        "laptop_callout": "PROTECT YOUR PREFRONTAL CORTEX",
        "end_top": "YOU DECIDE",
        "option_a": opt_a,
        "option_b": opt_b,
        "end_sub": f"Comment below • Follow {handle} for Part 2",
    }


def _fmt_srt_ts(sec: float) -> str:
    ms = max(int(round(sec * 1000)), 0)
    hh, rem = divmod(ms, 3600000)
    mm, rem = divmod(rem, 60000)
    ss, msec = divmod(rem, 1000)
    return f"{hh:02d}:{mm:02d}:{ss:02d},{msec:03d}"


def _write_pov_srt(dialogue_events: list[dict[str, Any]], srt_path: Path) -> None:
    blocks: list[str] = []
    for idx, ev in enumerate(dialogue_events, start=1):
        blocks.append(
            f"{idx}\n{_fmt_srt_ts(float(ev['start']))} --> {_fmt_srt_ts(float(ev['end']))}\n{ev['text']}\n"
        )
    srt_path.parent.mkdir(parents=True, exist_ok=True)
    srt_path.write_text("\n".join(blocks), encoding="utf-8")


def _schedule_pov_dialogue_events(
    raw_clips: list[dict[str, Any]],
    gap_scale: float = 1.0,
    endcard_dur: float = 3.6,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    """Compute exact beat timestamps & camera cuts locked directly to each spoken clip's real duration."""
    dialogue_events: list[dict[str, Any]] = []
    beat_starts: dict[str, float] = {}
    cursor = 0.65 * gap_scale

    for clip in raw_clips:
        beat = clip["beat"]
        dur = float(clip["dur"])
        if beat == "trap":
            cursor += 0.22 * gap_scale
        elif beat == "explain":
            cursor += 0.45 * gap_scale
        elif beat == "ping":
            cursor += 1.25 * gap_scale

        beat_starts[beat] = cursor
        dialogue_events.append({
            "beat": beat,
            "speaker": clip["speaker"],
            "text": clip["text"],
            "start": round(cursor, 3),
            "end": round(cursor + dur, 3),
            "wav_path": clip["wav_path"],
        })
        cursor += dur + (0.28 * gap_scale)

    t_trap = max(beat_starts["trap"] - 0.14 * gap_scale, 0.8)
    t_explain = max(beat_starts["explain"] - 0.30 * gap_scale, t_trap + 0.8)
    t_timer = max(beat_starts["timer_react"] - 0.22 * gap_scale, t_explain + 0.8)
    t_scan = max(beat_starts["scan"] - 0.22 * gap_scale, t_timer + 0.8)
    t_desk = max(beat_starts["desk"] - 0.22 * gap_scale, t_scan + 0.8)
    t_agree = max(beat_starts["agree"] - 0.18 * gap_scale, t_desk + 1.0)
    t_ping = max(beat_starts["ping"] - 1.15 * gap_scale, t_agree + 0.6)
    t_endcard = cursor + 0.40 * gap_scale
    total_dur = t_endcard + endcard_dur
    timings = {
        "t_trap": round(t_trap, 3),
        "t_explain": round(t_explain, 3),
        "t_timer": round(t_timer, 3),
        "t_scan": round(t_scan, 3),
        "t_desk": round(t_desk, 3),
        "t_agree": round(t_agree, 3),
        "t_ping": round(t_ping, 3),
        "t_endcard": round(t_endcard, 3),
        "total_dur": round(total_dur, 3),
    }
    return dialogue_events, timings


def _probe_audio_duration(path: Path) -> float:
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return max(float(res.stdout.strip() or 1.0), 0.6)


def render_pov_3d_toon_video_for_pipeline(
    scenes_meta: list[dict[str, Any]],
    audio_bundle: Any,
    out_video_path: Path,
    config: dict[str, Any],
    is_short: bool = True,
    pov_episode: dict[str, Any] | None = None,
    topic_meta: dict[str, Any] | None = None,
) -> Path:
    """Pipeline adapter: render any daily HabitSains episode in Studio v9 3D Cel-Shaded POV style.

    Uses a beat-locked 2-speaker POV script + topic-matched 3D props (phone cards, floating badges,
    Brain Scan tablet, study desk laptop, [A]/[B] cliffhanger) so EVERY spoken line, SFX, and
    3D camera cut matches the exact visual action on screen.

    Renders WebGL cleanly at 720x1280 (vertical) or 1280x720 (landscape) @ 24fps and upscales via
    FFmpeg Lanczos directly to exact target resolution (1080x1920 or 1920x1080), keeping Shorts
    strictly <= 58.2s with yuv420p TV-range Main profile + 48kHz stereo AAC for Meta & YouTube.
    """
    from playwright.sync_api import sync_playwright

    project_root = Path(__file__).resolve().parent.parent
    three_js_path = project_root / "assets" / "vendor" / "three.min.js"
    if not three_js_path.exists():
        raise FileNotFoundError(f"Missing local Three.js bundle at {three_js_path}")

    vid_cfg = config.get("video", {}).get("shorts" if is_short else "youtube_long", {})
    target_w = int(vid_cfg.get("width", 1080 if is_short else 1920))
    target_h = int(vid_cfg.get("height", 1920 if is_short else 1080))
    max_short_sec = float(vid_cfg.get("max_duration_sec", 59.0)) if is_short else 9999.0

    # Render Three.js WebGL at crisp 720p (2.25x faster headless SwiftShader) -> Lanczos upscale to target 1080p!
    gl_w, gl_h = (720, 1280) if target_h >= target_w else (1280, 720)
    fps = 24

    # Resolve & sanitize beat-locked 2-speaker POV episode matched to TODAY'S EXACT TOPIC!
    meta = topic_meta or {}
    inferred_topic = str(
        meta.get("topic")
        or (scenes_meta[0].get("visual_headline", "") if scenes_meta else "")
        or "Science-Backed Deep Focus"
    ).strip()
    episode = normalize_pov_3d_episode(
        raw_ep=pov_episode,
        topic=inferred_topic,
        angle=str(meta.get("angle", "")),
        hook=str(meta.get("hook", "")),
        scenes_meta=scenes_meta,
        config=config,
    )
    props = episode["props"]
    script_lines = episode["dialogue"]

    work_dir = out_video_path.parent / "_v9_pov_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    # Synthesize true 2-speaker neural dialogue (ChristopherNeural Brain Guide vs AndrewMultilingualNeural POV)
    voice_partner = "en-US-ChristopherNeural"
    voice_pov = "en-US-AndrewMultilingualNeural"
    raw_clips: list[dict[str, Any]] = []
    print(f"[v9-pov] Synthesizing 8 beat-locked 2-speaker POV lines for: {props.get('series_title')}...", flush=True)
    for idx, line in enumerate(script_lines):
        mp3 = work_dir / f"dlg_{idx:02d}.mp3"
        wav = work_dir / f"dlg_{idx:02d}.wav"
        is_partner = line["speaker"] == "partner"
        voice = voice_partner if is_partner else voice_pov
        rate = "+7%" if is_partner else "+8%"
        dur = asyncio.run(_synth_edge_line(line["text"], mp3, voice=voice, rate=rate))
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp3), "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(wav)],
            capture_output=True, check=True,
        )
        raw_clips.append({
            "beat": line["beat"],
            "speaker": line["speaker"],
            "text": line["text"],
            "dur": dur,
            "wav_path": str(wav),
        })

    # Schedule exact beat timestamps & enforce safe <= 58.2s Shorts ceiling without ever clipping a word!
    safe_cap = min(max_short_sec - 0.8, 58.2) if is_short else 9999.0
    endcard_dur = 3.5 if is_short else 4.2
    dialogue_events, timings = _schedule_pov_dialogue_events(raw_clips, gap_scale=1.0, endcard_dur=endcard_dur)

    if is_short and timings["total_dur"] > safe_cap:
        # Step 1: Slightly tighten inter-beat pauses while keeping camera choreography intact
        dialogue_events, timings = _schedule_pov_dialogue_events(raw_clips, gap_scale=0.72, endcard_dur=3.1)

    if is_short and timings["total_dur"] > safe_cap:
        # Step 2: Uniform gentle atempo speedup on speech clips so zero sentences are ever cut off!
        speech_sum = sum(c["dur"] for c in raw_clips)
        overhead = timings["total_dur"] - speech_sum
        target_speech = max(safe_cap - overhead - 0.4, speech_sum * 0.78)
        tempo = min(max(speech_sum / max(target_speech, 1.0), 1.03), 1.24)
        print(f"[v9-pov] Adjusting 2-speaker pacing by {tempo:.2f}x to fit cleanly inside {safe_cap:.1f}s Shorts cap...", flush=True)
        for idx, clip in enumerate(raw_clips):
            fast_wav = work_dir / f"dlg_{idx:02d}_fast.wav"
            subprocess.run(
                ["ffmpeg", "-y", "-i", clip["wav_path"], "-af", f"atempo={tempo:.3f}", "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(fast_wav)],
                capture_output=True, check=True,
            )
            clip["wav_path"] = str(fast_wav)
            clip["dur"] = _probe_audio_duration(fast_wav)
        dialogue_events, timings = _schedule_pov_dialogue_events(raw_clips, gap_scale=0.72, endcard_dur=3.0)

    t_trap = timings["t_trap"]
    t_explain = timings["t_explain"]
    t_timer = timings["t_timer"]
    t_scan = timings["t_scan"]
    t_desk = timings["t_desk"]
    t_agree = timings["t_agree"]
    t_ping = timings["t_ping"]
    t_endcard = timings["t_endcard"]
    total_dur = timings["total_dur"]

    mixed_m4a = work_dir / "mixed_v9_pov.m4a"
    _build_habitsains_soundscape(
        dialogue_events=dialogue_events,
        total_dur=total_dur,
        trap_time=t_trap,
        timer_time=t_timer,
        ping_time=t_ping,
        endcard_time=t_endcard,
        out_m4a=mixed_m4a,
        work_dir=work_dir,
    )

    # Keep pipeline subtitles.srt & audio_bundle metadata synced with the real spoken 2-speaker POV script!
    srt_path_str = getattr(audio_bundle, "srt_path", "") if audio_bundle is not None else ""
    if srt_path_str:
        _write_pov_srt(dialogue_events, Path(srt_path_str))
    if audio_bundle is not None and hasattr(audio_bundle, "total_duration_sec"):
        try:
            audio_bundle.total_duration_sec = round(total_dur, 2)
        except Exception:
            pass

    timeline_cfg: dict[str, Any] = {
        **props,
        "t_trap": t_trap,
        "t_explain": t_explain,
        "t_timer": t_timer,
        "t_scan": t_scan,
        "t_desk": t_desk,
        "t_agree": t_agree,
        "t_ping": t_ping,
        "t_endcard": t_endcard,
        "dialogue": [
            {"speaker": e["speaker"], "text": e["text"], "start": e["start"], "end": e["end"]}
            for e in dialogue_events
        ],
    }

    html_doc = _build_habitsains_3d_html(three_js_path.read_text(encoding="utf-8"), timeline_cfg, gl_w, gl_h)
    total_frames = int(round(total_dur * fps))
    silent_mp4 = work_dir / "video_v9_pov_silent.mp4"

    print(
        f"[video] Rendering Story-Synced Studio v9 3D POV ({gl_w}x{gl_h} -> {target_w}x{target_h} @ {fps}fps, {total_dur:.1f}s)...",
        flush=True,
    )
    cmd = [
        "ffmpeg", "-y",
        "-f", "image2pipe", "-vcodec", "mjpeg", "-r", str(fps), "-i", "pipe:0",
        "-vf", f"scale={target_w}:{target_h}:flags=lanczos:in_range=full:out_range=tv,format=yuv420p",
        "-c:v", "libx264", "-profile:v", "main", "-level:v", "4.0", "-preset", "veryfast", "-crf", "21",
        "-pix_fmt", "yuv420p", "-color_range", "tv", "-an",
        str(silent_mp4),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert proc.stdin is not None

    with sync_playwright() as pw:
        chrome = find_chrome_executable()
        launch_kw: dict[str, Any] = {
            "headless": True,
            "args": ["--no-sandbox", "--enable-webgl", "--ignore-gpu-blocklist", "--use-gl=angle", "--use-angle=swiftshader"],
        }
        if chrome:
            launch_kw["executable_path"] = chrome
        br = pw.chromium.launch(**launch_kw)
        page = br.new_page(viewport={"width": gl_w, "height": gl_h}, device_scale_factor=1)
        page.set_content(html_doc, wait_until="load")

        last_end_jpg: bytes | None = None
        try:
            for f_i in range(total_frames):
                t = f_i / float(fps)
                if t > t_endcard + 0.45 and last_end_jpg is not None:
                    proc.stdin.write(last_end_jpg)
                    continue
                page.evaluate(f"window.renderAt({t:.4f})")
                jpg_bytes = page.screenshot(type="jpeg", quality=93)
                if t > t_endcard + 0.45:
                    last_end_jpg = jpg_bytes
                proc.stdin.write(jpg_bytes)
                if f_i > 0 and f_i % 240 == 0:
                    print(f"[v9-pov] Rendered {f_i}/{total_frames} frames ({100*f_i/total_frames:.0f}%)...", flush=True)
        finally:
            br.close()
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()

    err = proc.stderr.read().decode("utf-8", errors="ignore") if proc.stderr else ""
    ret = proc.wait()
    if ret != 0:
        raise RuntimeError(f"FFmpeg v9 POV pipeline render failed ({ret}): {err[-300:]}")

    out_video_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(silent_mp4), "-i", str(mixed_m4a),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest",
            str(out_video_path),
        ],
        capture_output=True, check=True,
    )

    for p in work_dir.glob("*"):
        p.unlink(missing_ok=True)
    try:
        work_dir.rmdir()
    except OSError:
        pass

    return out_video_path


if __name__ == "__main__":
    out_file = Path("output/_v9_3d_pov_demo/habitsains_7am_trap_3d_pov_9x16.mp4")
    info = build_habitsains_3d_pov_demo(out_file)
    print("V9 HABITSAINS DEMO COMPLETE:", json.dumps(info, indent=2))
