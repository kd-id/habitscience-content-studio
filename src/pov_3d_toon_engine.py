"""Studio v9 — 3D Cel-Shaded Toon First-Person POV Survival/Decision Story Engine.

Inspired by the viral @you.have.72hours 3D POV interactive storytelling format:
- Genuine real-time 3D WebGL scene powered by local Three.js + Headless Chrome (Playwright)
- Quantized 3-step cel-shading (MeshToonMaterial) + crisp uniform normal-extruded black ink outlines
- First-Person POV camera with breathing bob, storm shake, head turns & foreground 3D cartoon gloved hands
- Connected 3D Exterior Storm (spinning funnel tornado, flying debris, farmhouse) & Underground Concrete Bunker
  (textured cinderblock walls, stairs + yellow rails, hinged steel hatch + red wheel, stocked food/water shelf)
- Articulated 3D beanie/puffer companion character with animated lip-sync, gestures & 3D smartphone prop
- Live HUD: location/time stamp, red series banner, ticking red-bordered countdown clock (SURVIVE 71:59:xx),
  2-speaker bold outlined subtitles (YELLOW partner vs WHITE POV), and viral interactive A/B cliffhanger card
- 2-speaker neural dialogue + procedural thriller SFX (tornado roar, hatch slam, timer beep, eerie knocks, bass drop)
- 100% FREE, zero paid APIs, works locally on Windows and on GitHub Actions Linux.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any

from src.html_motion_overlay import find_chrome_executable


# ---------------------------------------------------------------------------
# 2-Speaker Dialogue Audio Synthesis (with Timeout + Retry)
# ---------------------------------------------------------------------------

async def _synth_edge_line(text: str, out_mp3: Path, voice: str, rate: str = "+4%") -> float:
    import edge_tts

    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    last_err: Exception | None = None
    for attempt in range(1, 4):
        try:
            async def _once() -> None:
                comm = edge_tts.Communicate(text=text, voice=voice, rate=rate)
                with out_mp3.open("wb") as fh:
                    async for ch in comm.stream():
                        if ch.get("type") == "audio":
                            fh.write(ch["data"])

            await asyncio.wait_for(_once(), timeout=25.0)
            if out_mp3.exists() and out_mp3.stat().st_size > 800:
                last_err = None
                break
        except Exception as exc:
            last_err = exc
            print(f"[v9-tts] Retry {attempt}/3 ({type(exc).__name__})", flush=True)
            await asyncio.sleep(1.0)
    if last_err is not None and (not out_mp3.exists() or out_mp3.stat().st_size <= 800):
        raise last_err

    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(out_mp3)],
        capture_output=True, text=True, check=True,
    )
    return max(float(res.stdout.strip() or 1.0), 0.8)


def _build_thriller_soundscape(
    dialogue_events: list[dict[str, Any]],
    total_dur: float,
    slam_time: float,
    timer_time: float,
    knock_time: float,
    endcard_time: float,
    out_m4a: Path,
    work_dir: Path,
) -> Path:
    """Mix 2-speaker dialogue + roaring tornado wind + hatch metal slam + tense bunker hum + 3 eerie knocks + boom."""
    wind_wav = work_dir / "_sfx_wind.wav"
    slam_wav = work_dir / "_sfx_slam.wav"
    beep_wav = work_dir / "_sfx_beep.wav"
    knock_wav = work_dir / "_sfx_knock.wav"
    boom_wav = work_dir / "_sfx_boom.wav"

    try:
        # 1. Roaring tornado wind (plays from 0s until hatch slams shut!)
        wind_dur = max(slam_time + 0.6, 4.0)
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i", f"anoisesrc=color=brown:sample_rate=44100:duration={wind_dur:.2f}",
                "-af", f"bandpass=f=220:width_type=h:w=340,volume=-11dB,afade=t=in:st=0:d=0.6,afade=t=out:st={max(slam_time - 0.1, 0.5):.2f}:d=0.55",
                "-c:a", "pcm_s16le", str(wind_wav),
            ],
            capture_output=True, check=True,
        )
        # 2. Heavy metallic bunker hatch SLAM!
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                "aevalsrc='(0.9*sin(2*PI*(95-55*t)*t)*exp(-7*t)+0.4*sin(2*PI*420*t)*exp(-14*t))':s=44100:d=0.65",
                "-af", "lowpass=f=1200,volume=-4dB", "-c:a", "pcm_s16le", str(slam_wav),
            ],
            capture_output=True, check=True,
        )
        # 3. Digital survival timer activation beep
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                "aevalsrc='0.6*sin(2*PI*1180*t)*exp(-18*t)':s=44100:d=0.16",
                "-af", "volume=-12dB", "-c:a", "pcm_s16le", str(beep_wav),
            ],
            capture_output=True, check=True,
        )
        # 4. Eerie hollow metallic KNOCK-KNOCK-KNOCK on steel hatch!
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                "aevalsrc='(0.85*sin(2*PI*155*t)+0.45*sin(2*PI*318*t)+0.25*sin(2*PI*620*t))*exp(-15*t)':s=44100:d=0.28",
                "-af", "lowpass=f=1400,volume=-4dB", "-c:a", "pcm_s16le", str(knock_wav),
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

        # Tense dark underground ambient drone throughout video
        drone_expr = "0.28*sin(2*PI*55*t)+0.20*sin(2*PI*82.41*t)+0.12*sin(2*PI*110.5*t)*(0.7+0.3*sin(2*PI*0.35*t))"
        inputs: list[str] = [
            "-f", "lavfi", "-t", f"{total_dur:.2f}", "-i", f"aevalsrc='{drone_expr}':s=44100:c=stereo",
            "-i", str(wind_wav),
            "-i", str(slam_wav),
            "-i", str(beep_wav),
            "-i", str(boom_wav),
        ]
        filters: list[str] = [
            f"[0:a]lowpass=f=260,volume=-22dB,afade=t=in:st=0:d=1.0,afade=t=out:st={max(total_dur - 1.5, 0.5):.2f}:d=1.4[drone]",
            "[1:a]aformat=channel_layouts=stereo[wind]",
            f"[2:a]adelay={int(slam_time * 1000)}:all=1,aformat=channel_layouts=stereo[slam]",
            f"[3:a]adelay={int(timer_time * 1000)}:all=1,aformat=channel_layouts=stereo[beep]",
            f"[4:a]adelay={int(endcard_time * 1000)}:all=1,aformat=channel_layouts=stereo[boom]",
        ]
        mix = ["[drone]", "[wind]", "[slam]", "[beep]", "[boom]"]
        nxt = 5

        # 3 spaced eerie knocks (THUD ... THUD ... THUD!)
        for k_i, k_off in enumerate((0.0, 0.58, 1.16)):
            ms = max(int((knock_time + k_off) * 1000), 0)
            inputs.extend(["-i", str(knock_wav)])
            filters.append(f"[{nxt}:a]adelay={ms}:all=1,aformat=channel_layouts=stereo[kn{k_i}]")
            mix.append(f"[kn{k_i}]")
            nxt += 1

        # Add every dialogue clip at its exact timestamp!
        for d_i, ev in enumerate(dialogue_events):
            ms = max(int(ev["start"] * 1000), 0)
            inputs.extend(["-i", str(ev["wav_path"])])
            filters.append(f"[{nxt}:a]adelay={ms}:all=1,volume=+1.5dB,aformat=channel_layouts=stereo[dlg{d_i}]")
            mix.append(f"[dlg{d_i}]")
            nxt += 1

        filters.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:dropout_transition=2:normalize=0,alimiter=limit=0.95[out]")
        subprocess.run(
            ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]", "-c:a", "aac", "-b:a", "192k", str(out_m4a)],
            capture_output=True, text=True, check=True,
        )
        return out_m4a
    finally:
        for f in (wind_wav, slam_wav, beep_wav, knock_wav, boom_wav):
            f.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Self-Contained Three.js 3D Cel-Shaded Toon POV Bunker Engine HTML Template
# ---------------------------------------------------------------------------

def _build_3d_pov_html(three_js_src: str, timeline_cfg: dict[str, Any], width: int, height: int) -> str:
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

  /* Top-left location & part stamp (exact @you.have.72hours look!) */
  #locStamp {{
    position: absolute; top: 108px; left: 32px; z-index: 10;
    opacity: 0; transition: none;
  }}
  .loc-main {{
    font-size: 29px; font-weight: 900; color: #FFFFFF; letter-spacing: 0.6px;
    text-shadow: -2px -2px 0 #111, 2px -2px 0 #111, -2px 2px 0 #111, 2px 2px 0 #111, 0 4px 10px rgba(0,0,0,0.8);
  }}
  .loc-sub {{
    font-size: 23px; font-weight: 800; color: #F5D547; margin-top: 2px;
    text-shadow: -2px -2px 0 #111, 2px -2px 0 #111, -2px 2px 0 #111, 2px 2px 0 #111;
  }}

  /* Red Series Banner */
  #seriesBanner {{
    position: absolute; top: 192px; left: 50%; transform: translateX(-50%);
    z-index: 11; padding: 14px 44px 16px; border-radius: 16px;
    background: linear-gradient(180deg, #D91E36 0%, #B31328 100%);
    border: 3px solid #880C1C;
    box-shadow: 0 12px 32px rgba(0,0,0,0.65);
    text-align: center; opacity: 0; white-space: nowrap;
  }}
  .sb-eyebrow {{
    font-size: 17px; font-weight: 800; letter-spacing: 3px; color: rgba(255,255,255,0.92);
    margin-bottom: 4px;
  }}
  .sb-title {{
    font-size: 42px; font-weight: 900; letter-spacing: 1px; color: #FFFFFF;
    display: flex; align-items: center; justify-content: center; gap: 14px;
  }}

  /* Live Ticking Countdown HUD (SURVIVE 71:59:xx) */
  #timerHud {{
    position: absolute; top: 118px; left: 50%; transform: translateX(-50%);
    z-index: 12; padding: 10px 26px 12px; border-radius: 14px;
    background: rgba(14, 14, 18, 0.92);
    border: 3px solid #E12D39;
    box-shadow: 0 0 22px rgba(225,45,57,0.45), 0 10px 24px rgba(0,0,0,0.65);
    text-align: center; opacity: 0;
  }}
  .tm-lbl {{
    font-size: 16px; font-weight: 800; letter-spacing: 4px; color: #F04B56;
    margin-bottom: 2px;
  }}
  .tm-val {{
    font-size: 40px; font-weight: 900; color: #FFFFFF; letter-spacing: 2px;
    font-variant-numeric: tabular-nums;
  }}

  /* Bold Thick-Outlined Dialogue Subtitles (Yellow Partner / White POV) */
  #subWrap {{
    position: absolute; left: 32px; right: 32px; top: 69.5%;
    transform: translateY(-50%);
    z-index: 15; text-align: center; pointer-events: none;
  }}
  #subText {{
    display: inline-block;
    font-family: 'Arial Black', Impact, 'Segoe UI', sans-serif;
    font-size: 45px; font-weight: 900; line-height: 1.15;
    letter-spacing: 0.5px; text-transform: uppercase;
    -webkit-text-stroke: 3.2px #111111;
    paint-order: stroke fill;
    text-shadow: 0 5px 0 #111111, 0 8px 18px rgba(0,0,0,0.85);
    padding: 0 10px;
  }}

  /* Viral Interactive A/B Cliffhanger End Screen (exact b_09!) */
  #endCard {{
    position: absolute; inset: 0; z-index: 30;
    background: #000000;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 46px; opacity: 0; pointer-events: none;
  }}
  .ec-top {{
    font-size: 24px; font-weight: 800; letter-spacing: 4px; color: #F2C94C;
    margin-bottom: 18px;
  }}
  .ec-head {{
    font-family: 'Arial Black', Impact, sans-serif;
    font-size: 66px; font-weight: 900; line-height: 1.04; color: #FFFFFF;
    text-align: center; margin-bottom: 44px; letter-spacing: 1px;
  }}
  .ec-btn {{
    width: 100%; border-radius: 20px; padding: 22px 26px;
    display: flex; align-items: center; gap: 22px;
    box-shadow: 0 12px 28px rgba(0,0,0,0.5);
  }}
  .ec-btn-a {{ background: linear-gradient(180deg, #4B8BE0 0%, #3872C2 100%); border: 2px solid #74AFF5; }}
  .ec-btn-b {{ background: linear-gradient(180deg, #E62E4D 0%, #C41C38 100%); border: 2px solid #F7647D; }}
  .ec-badge {{
    width: 62px; height: 62px; border-radius: 14px; background: #FFFFFF; color: #121212;
    font-size: 36px; font-weight: 900; display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }}
  .ec-label {{
    font-family: 'Arial Black', 'Segoe UI', sans-serif;
    font-size: 30px; font-weight: 900; color: #FFFFFF; line-height: 1.18; text-transform: uppercase;
  }}
  .ec-or {{
    font-size: 30px; font-weight: 900; color: #F2C94C; margin: 18px 0; letter-spacing: 2px;
  }}
  .ec-cta {{
    margin-top: 46px; font-size: 30px; font-weight: 800; color: #FFFFFF;
  }}
  .ec-cta b {{ color: #F2C94C; }}
  .ec-arrow {{ font-size: 40px; color: #F2C94C; margin-top: 10px; }}
</style>
</head>
<body>
<canvas id="gl" width="{width}" height="{height}"></canvas>

<div id="locStamp">
  <div class="loc-main" id="locMain">MORRIS FARM • 4:17 PM</div>
  <div class="loc-sub" id="locSub">Kansas • Part 1</div>
</div>

<div id="seriesBanner">
  <div class="sb-eyebrow">NEW SERIES</div>
  <div class="sb-title">
    <svg width="34" height="34" viewBox="0 0 24 24" fill="#FFFFFF"><path d="M12 3L2 12h3v8h6v-5h2v5h6v-8h3L12 3z"/></svg>
    <span id="seriesTitle">THE BUNKER</span>
  </div>
</div>

<div id="timerHud">
  <div class="tm-lbl">SURVIVE</div>
  <div class="tm-val" id="timerVal">71:59:59</div>
</div>

<div id="subWrap"><span id="subText"></span></div>

<div id="endCard">
  <div class="ec-top" id="ecTop">PART 1 • YOU DECIDE</div>
  <div class="ec-head">WHAT WOULD<br>YOU DO?</div>
  <div class="ec-btn ec-btn-a" id="btnA"><div class="ec-badge">A</div><div class="ec-label" id="optA">OPEN THE BUNKER DOOR</div></div>
  <div class="ec-or">OR</div>
  <div class="ec-btn ec-btn-b" id="btnB"><div class="ec-badge">B</div><div class="ec-label" id="optB">STAY INSIDE AND IGNORE THE KNOCKING</div></div>
  <div class="ec-cta">Comment <b>A</b> or <b>B</b> below</div>
  <div class="ec-arrow">↓</div>
</div>

<script>{three_js_src}</script>
<script>
(() => {{
  const CFG = {cfg_json};
  const W = {width}, H = {height};

  // Fill static HUD texts from config
  document.getElementById('locMain').textContent = CFG.loc_main || 'MORRIS FARM • 4:17 PM';
  document.getElementById('locSub').textContent = CFG.loc_sub || 'Kansas • Part 1';
  document.getElementById('seriesTitle').textContent = CFG.series_title || 'THE BUNKER';
  document.getElementById('optA').textContent = CFG.option_a || 'OPEN THE BUNKER DOOR';
  document.getElementById('optB').textContent = CFG.option_b || 'STAY INSIDE AND IGNORE THE KNOCKING';

  // --- THREE.JS CEL-SHADED TOON RENDERER ---
  const canvas = document.getElementById('gl');
  const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true, preserveDrawingBuffer: true }});
  renderer.setSize(W, H, false);
  renderer.outputEncoding = THREE.sRGBEncoding;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x363e34);
  scene.fog = new THREE.Fog(0x363e34, 14, 42);

  const camera = new THREE.PerspectiveCamera(64, W / H, 0.08, 120);
  scene.add(camera);

  // Quantized 3-step toon gradient map for authentic anime/comic cel-shading!
  const gradData = new Uint8Array([95, 95, 95, 255, 178, 178, 178, 255, 255, 255, 255, 255]);
  const toonGrad = new THREE.DataTexture(gradData, 3, 1, THREE.RGBAFormat);
  toonGrad.minFilter = THREE.NearestFilter;
  toonGrad.magFilter = THREE.NearestFilter;
  toonGrad.needsUpdate = true;

  // Normal-extruded uniform black comic ink outline shader!
  function makeOutlineMat(thickness = 0.022) {{
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
      fragmentShader: `void main() {{ gl_FragColor = vec4(0.07, 0.07, 0.08, 1.0); }}`
    }});
  }}

  function toonMat(colorHex, mapTex = null) {{
    const opts = {{ color: colorHex, gradientMap: toonGrad }};
    if (mapTex) opts.map = mapTex;
    return new THREE.MeshToonMaterial(opts);
  }}

  function outlinedMesh(geo, mat, outlineThick = 0.020) {{
    const mesh = new THREE.Mesh(geo, mat);
    if (outlineThick > 0) {{
      const out = new THREE.Mesh(geo, makeOutlineMat(outlineThick));
      mesh.add(out);
    }}
    return mesh;
  }}

  // --- PROCEDURAL CONCRETE BLOCK & PHONE SCREEN TEXTURES ---
  function makeBrickTexture(baseHex, mortarHex) {{
    const tc = document.createElement('canvas');
    tc.width = 512; tc.height = 512;
    const ctx = tc.getContext('2d');
    ctx.fillStyle = baseHex;
    ctx.fillRect(0, 0, 512, 512);
    // Subtle mottled concrete grime blobs (signature texture from @you.have.72hours!)
    for (let i = 0; i < 65; i++) {{
      const rx = (i * 97) % 512, ry = (i * 173) % 512, rr = 14 + (i % 24);
      ctx.fillStyle = (i % 2 === 0) ? 'rgba(40,36,28,0.12)' : 'rgba(210,200,175,0.08)';
      ctx.beginPath(); ctx.arc(rx, ry, rr, 0, Math.PI * 2); ctx.fill();
    }}
    ctx.strokeStyle = mortarHex;
    ctx.lineWidth = 4;
    const rows = 8, rh = 512 / rows;
    for (let r = 0; r <= rows; r++) {{
      ctx.beginPath(); ctx.moveTo(0, r * rh); ctx.lineTo(512, r * rh); ctx.stroke();
      const offset = (r % 2) * 64;
      for (let x = offset; x < 512; x += 128) {{
        ctx.beginPath(); ctx.moveTo(x, r * rh); ctx.lineTo(x, (r + 1) * rh); ctx.stroke();
      }}
    }}
    const tex = new THREE.CanvasTexture(tc);
    tex.wrapS = THREE.RepeatWrapping; tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(2.2, 1.5);
    tex.encoding = THREE.sRGBEncoding;
    return tex;
  }}

  function makePhoneScreenTexture() {{
    const tc = document.createElement('canvas');
    tc.width = 256; tc.height = 460;
    const ctx = tc.getContext('2d');
    ctx.fillStyle = '#12131A'; ctx.fillRect(0, 0, 256, 460);
    ctx.fillStyle = '#EE3D4B'; ctx.font = 'bold 20px Arial'; ctx.textAlign = 'center';
    ctx.fillText('NO SERVICE', 128, 52);
    ctx.fillStyle = '#FFFFFF'; ctx.font = 'bold 74px Arial';
    ctx.fillText('4:19', 128, 160);
    ctx.fillStyle = '#252734';
    ctx.fillRect(26, 210, 204, 110);
    ctx.fillStyle = '#F2F4F8'; ctx.font = 'bold 24px Arial';
    ctx.fillText('Call failed', 128, 255);
    ctx.fillStyle = '#B8BDC9'; ctx.font = '18px Arial';
    ctx.fillText('No network available', 128, 290);
    // Red signal bars
    for (let i = 0; i < 4; i++) {{
      ctx.fillStyle = i === 0 ? '#EE3D4B' : '#3A3D4C';
      ctx.fillRect(92 + i * 20, 385 - i * 10, 12, 18 + i * 10);
    }}
    const tex = new THREE.CanvasTexture(tc);
    tex.encoding = THREE.sRGBEncoding;
    return tex;
  }}

  const brickTex = makeBrickTexture('#8F8A73', '#494538');
  const floorTex = makeBrickTexture('#767362', '#524F43');
  const phoneTex = makePhoneScreenTexture();

  // --- LIGHTING (Moody Dim Underground Bulb + Muted Storm Light — Exact @you.have.72hours Tone!) ---
  const ambLight = new THREE.AmbientLight(0x9a9484, 0.36);
  scene.add(ambLight);
  const bunkerBulb = new THREE.PointLight(0xffcb78, 1.02, 13, 1.6);
  bunkerBulb.position.set(0, 3.05, -0.2);
  scene.add(bunkerBulb);
  const stormLight = new THREE.DirectionalLight(0xa4b4a0, 0.42);
  stormLight.position.set(-4, 14, 10);
  scene.add(stormLight);

  // --- UNDERGROUND CONCRETE BUNKER ROOM (W=5.6, H=3.4, D=6.2) ---
  const bunkerGroup = new THREE.Group();
  scene.add(bunkerGroup);

  const wallMat = toonMat(0xffffff, brickTex);
  const ceilMat = toonMat(0x88816c, floorTex);
  const flrMat = toonMat(0x73705e, floorTex);

  // Floor
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(5.8, 6.4), flrMat);
  floor.rotation.x = -Math.PI / 2;
  bunkerGroup.add(floor);

  // Back wall (z = -3.0)
  const backWall = new THREE.Mesh(new THREE.PlaneGeometry(5.8, 3.4), wallMat);
  backWall.position.set(0, 1.7, -3.0);
  bunkerGroup.add(backWall);

  // Left wall (x = -2.8)
  const leftWall = new THREE.Mesh(new THREE.PlaneGeometry(6.4, 3.4), wallMat);
  leftWall.rotation.y = Math.PI / 2;
  leftWall.position.set(-2.8, 1.7, 0.1);
  bunkerGroup.add(leftWall);

  // Right wall (x = +2.8)
  const rightWall = new THREE.Mesh(new THREE.PlaneGeometry(6.4, 3.4), wallMat);
  rightWall.rotation.y = -Math.PI / 2;
  rightWall.position.set(2.8, 1.7, 0.1);
  bunkerGroup.add(rightWall);

  // Front solid bulkhead wall sealing bunker at z = +3.1 (zero exterior leak beneath stairs!)
  const frontWallFull = new THREE.Mesh(new THREE.PlaneGeometry(5.8, 3.4), wallMat);
  frontWallFull.rotation.y = Math.PI;
  frontWallFull.position.set(0, 1.7, 3.12);
  bunkerGroup.add(frontWallFull);
  // Stairwell side cheeks framing the hatch opening cleanly
  for (const sx of [-1.18, 1.18]) {{
    const cheek = new THREE.Mesh(new THREE.BoxGeometry(0.18, 3.4, 2.1), wallMat);
    cheek.position.set(sx, 1.7, 2.15);
    bunkerGroup.add(cheek);
  }}

  // Ceiling (leaving exact hatch opening above stairs at x = -1.1..1.1, z = 1.25..3.10)
  const ceilMain = new THREE.Mesh(new THREE.PlaneGeometry(5.8, 4.35), ceilMat);
  ceilMain.rotation.x = Math.PI / 2;
  ceilMain.position.set(0, 3.35, -0.92);
  const ceilSideL = new THREE.Mesh(new THREE.PlaneGeometry(1.85, 2.0), ceilMat);
  ceilSideL.rotation.x = Math.PI / 2; ceilSideL.position.set(-1.98, 3.35, 2.15);
  const ceilSideR = new THREE.Mesh(new THREE.PlaneGeometry(1.85, 2.0), ceilMat);
  ceilSideR.rotation.x = Math.PI / 2; ceilSideR.position.set(1.98, 3.35, 2.15);
  bunkerGroup.add(ceilMain, ceilSideL, ceilSideR);

  // Hanging ceiling bulb fixture
  const bulbMesh = outlinedMesh(new THREE.SphereGeometry(0.11, 14, 14), new THREE.MeshBasicMaterial({{ color: 0xfff0b8 }}), 0.012);
  bulbMesh.position.set(0, 3.24, 0.2);
  bunkerGroup.add(bulbMesh);

  // Concrete stairs leading UP toward hatch (+Z = 0.7 -> 3.0, Y = 0.0 -> 2.3)
  const stairMat = toonMat(0x888672);
  for (let s = 0; s < 8; s++) {{
    const step = outlinedMesh(new THREE.BoxGeometry(2.15, 0.28, 0.34), stairMat, 0.015);
    step.position.set(0, 0.14 + s * 0.28, 0.85 + s * 0.30);
    bunkerGroup.add(step);
  }}
  // Iconic YELLOW metal handrails along stairs!
  const railMat = toonMat(0xdcb432);
  for (const side of [-1, 1]) {{
    const rail = outlinedMesh(new THREE.CylinderGeometry(0.035, 0.035, 2.75, 10), railMat, 0.012);
    rail.position.set(side * 0.96, 1.65, 1.80);
    rail.rotation.x = -Math.PI * 0.26;
    bunkerGroup.add(rail);
    for (const pIdx of [0, 1]) {{
      const post = outlinedMesh(new THREE.CylinderGeometry(0.032, 0.032, 0.92, 10), railMat, 0.010);
      post.position.set(side * 0.96, 0.72 + pIdx * 0.95, 1.05 + pIdx * 1.15);
      bunkerGroup.add(post);
    }}
  }}

  // Wooden bench against back wall + red emergency generator/toolbox right!
  const woodMat = toonMat(0x7c5c3e);
  const benchTop = outlinedMesh(new THREE.BoxGeometry(2.1, 0.14, 0.65), woodMat, 0.016);
  benchTop.position.set(-0.2, 0.68, -2.55);
  bunkerGroup.add(benchTop);
  for (const bx of [-1.1, 0.7]) {{
    const leg = outlinedMesh(new THREE.BoxGeometry(0.14, 0.68, 0.56), woodMat, 0.014);
    leg.position.set(bx, 0.34, -2.55);
    bunkerGroup.add(leg);
  }}
  const redBox = outlinedMesh(new THREE.BoxGeometry(0.95, 0.68, 0.62), toonMat(0xc91e2b), 0.018);
  redBox.position.set(1.95, 0.34, -1.85);
  const boxLid = outlinedMesh(new THREE.BoxGeometry(0.99, 0.14, 0.66), toonMat(0x23252a), 0.016);
  boxLid.position.set(1.95, 0.72, -1.85);
  bunkerGroup.add(redBox, boxLid);

  // --- STOCKED 3-TIER SUPPLY SHELF ON LEFT WALL (Exact b_06!) ---
  const shelfGroup = new THREE.Group();
  shelfGroup.position.set(-2.35, 0, -0.75);
  shelfGroup.rotation.y = Math.PI / 2;
  bunkerGroup.add(shelfGroup);

  for (const py of [0.55, 1.32, 2.08]) {{
    const plank = outlinedMesh(new THREE.BoxGeometry(2.85, 0.08, 0.54), woodMat, 0.014);
    plank.position.set(0, py, 0);
    shelfGroup.add(plank);
  }}
  for (const px of [-1.36, 1.36]) {{
    for (const pz of [-0.24, 0.24]) {{
      const post = outlinedMesh(new THREE.BoxGeometry(0.08, 2.38, 0.08), woodMat, 0.012);
      post.position.set(px, 1.19, pz);
      shelfGroup.add(post);
    }}
  }}
  // 7 Teal Water Jugs with Blue Caps on bottom shelf!
  const jugMat = toonMat(0x7ca6a2);
  const capMat = toonMat(0x3a6484);
  for (let j = 0; j < 7; j++) {{
    const jx = -1.14 + j * 0.38;
    const jug = outlinedMesh(new THREE.BoxGeometry(0.28, 0.44, 0.30), jugMat, 0.013);
    jug.position.set(jx, 0.81, 0);
    const cap = outlinedMesh(new THREE.CylinderGeometry(0.055, 0.055, 0.09, 10), capMat, 0.010);
    cap.position.set(jx, 1.06, 0);
    shelfGroup.add(jug, cap);
  }}
  // Colorful Two-Tone Food Cans on middle & top shelves!
  const canColors = [0xd63638, 0x4ca64c, 0x3b8ea5, 0xe8b630, 0x56a84c, 0xd63638];
  for (let row = 0; row < 2; row++) {{
    const sy = row === 0 ? 1.36 : 2.12;
    for (let c = 0; c < 6; c++) {{
      const cx = -1.05 + c * 0.42;
      const ch = 0.20 + ((c + row) % 3) * 0.11;
      const can = outlinedMesh(new THREE.CylinderGeometry(0.095, 0.095, ch, 12), toonMat(canColors[(c + row * 2) % canColors.length]), 0.012);
      can.position.set(cx, sy + ch / 2, 0);
      shelfGroup.add(can);
      if (ch > 0.25) {{
        const stripe = outlinedMesh(new THREE.CylinderGeometry(0.098, 0.098, ch * 0.45, 12), toonMat(canColors[(c + row + 3) % canColors.length]), 0.006);
        stripe.position.set(cx, sy + ch * 0.25, 0);
        shelfGroup.add(stripe);
      }}
    }}
  }}

  // --- HINGED STEEL BUNKER HATCH (Hinged on RIGHT +X edge so opening reveals full tornado on left/center like b_01!) ---
  const hatchPivot = new THREE.Group();
  hatchPivot.position.set(1.12, 3.32, 2.18);
  bunkerGroup.add(hatchPivot);

  const steelMat = toonMat(0x52585c);
  const beamMat = toonMat(0x2d3236);
  const redWheelMat = toonMat(0xc41a24);

  const hatchLeaf = new THREE.Group();
  hatchPivot.add(hatchLeaf);
  const doorSlab = outlinedMesh(new THREE.BoxGeometry(2.26, 0.14, 1.92), steelMat, 0.020);
  doorSlab.position.set(-1.12, 0, 0);
  hatchLeaf.add(doorSlab);
  // Structural cross ribs on underside of hatch
  for (const bx of [-1.85, -0.38]) {{
    const rib = outlinedMesh(new THREE.BoxGeometry(0.11, 0.08, 1.88), beamMat, 0.010);
    rib.position.set(bx, -0.09, 0);
    hatchLeaf.add(rib);
  }}
  for (const bz of [-0.56, 0.56]) {{
    const rib = outlinedMesh(new THREE.BoxGeometry(2.22, 0.08, 0.11), beamMat, 0.010);
    rib.position.set(-1.12, -0.09, bz);
    hatchLeaf.add(rib);
  }}
  // Glass porthole window
  const portRing = outlinedMesh(new THREE.TorusGeometry(0.32, 0.055, 10, 22), beamMat, 0.012);
  portRing.rotation.x = Math.PI / 2;
  portRing.position.set(-1.32, -0.08, 0.05);
  const portGlass = new THREE.Mesh(new THREE.CircleGeometry(0.28, 20), toonMat(0x88a0a4));
  portGlass.rotation.x = Math.PI / 2;
  portGlass.position.set(-1.32, -0.075, 0.05);
  hatchLeaf.add(portRing, portGlass);

  // Iconic RED 6-spoke wheel!
  const wheelGrp = new THREE.Group();
  wheelGrp.position.set(-0.56, -0.14, -0.44);
  const rim = outlinedMesh(new THREE.TorusGeometry(0.28, 0.042, 10, 22), redWheelMat, 0.012);
  rim.rotation.x = Math.PI / 2;
  wheelGrp.add(rim);
  for (let sp = 0; sp < 3; sp++) {{
    const spoke = outlinedMesh(new THREE.CylinderGeometry(0.025, 0.025, 0.54, 8), redWheelMat, 0.008);
    spoke.rotation.z = Math.PI / 2;
    spoke.rotation.y = (sp * Math.PI) / 3;
    wheelGrp.add(spoke);
  }}
  const hub = outlinedMesh(new THREE.CylinderGeometry(0.065, 0.065, 0.09, 12), beamMat, 0.010);
  wheelGrp.add(hub);
  hatchLeaf.add(wheelGrp);

  // Yellow locking bar & red handle bar
  const yBar = outlinedMesh(new THREE.CylinderGeometry(0.032, 0.032, 0.88, 8), railMat, 0.010);
  yBar.rotation.x = Math.PI / 2;
  yBar.position.set(-1.12, -0.12, 0.44);
  const rHandle = outlinedMesh(new THREE.CylinderGeometry(0.036, 0.036, 0.72, 8), redWheelMat, 0.010);
  rHandle.rotation.z = Math.PI / 2;
  rHandle.position.set(-1.12, -0.12, 0.68);
  hatchLeaf.add(yBar, rHandle);

  // --- EXTERIOR TORNADO STORM WORLD (Above Hatch, Y >= 3.34, Z >= 3.12) ---
  const stormGroup = new THREE.Group();
  scene.add(stormGroup);

  // Exterior lawn starts cleanly at z = 3.12 (flush with front bunker lip — never covers opening!)
  const grass = new THREE.Mesh(new THREE.PlaneGeometry(64, 48), toonMat(0x4f7234));
  grass.rotation.x = -Math.PI / 2;
  grass.position.set(0, 3.34, 27.12);
  stormGroup.add(grass);

  // Concrete storm-shelter sill/curb right along the front hatch lip
  const hatchCurb = outlinedMesh(new THREE.BoxGeometry(2.7, 0.16, 0.24), stairMat, 0.014);
  hatchCurb.position.set(0, 3.36, 3.16);
  stormGroup.add(hatchCurb);

  // Classic white farmhouse with red roof outside bunker (b_01!)
  const houseGrp = new THREE.Group();
  houseGrp.position.set(-2.35, 4.74, 10.2);
  const hBody = outlinedMesh(new THREE.BoxGeometry(3.6, 2.8, 3.0), toonMat(0xede6ce), 0.035);
  const hRoof = outlinedMesh(new THREE.ConeGeometry(2.95, 1.55, 4), toonMat(0xa82a2a), 0.035);
  hRoof.rotation.y = Math.PI / 4;
  hRoof.position.y = 2.15;
  const hWin = outlinedMesh(new THREE.BoxGeometry(0.85, 0.85, 0.12), toonMat(0x283546), 0.020);
  hWin.position.set(0.65, 0.2, -1.52);
  houseGrp.add(hBody, hRoof, hWin);
  stormGroup.add(houseGrp);

  // Brooding cel-shaded supercell storm clouds looming above the funnel!
  const cloudMat = toonMat(0x2a312c);
  for (const [cx, cy, cz, cr] of [[-4.5, 15.8, 17.0, 5.2], [0.8, 16.5, 16.0, 6.0], [6.2, 15.6, 17.5, 5.0], [-1.2, 15.0, 13.5, 4.2]]) {{
    const cl = outlinedMesh(new THREE.SphereGeometry(cr, 14, 10), cloudMat, 0.03);
    cl.scale.set(1.5, 0.42, 1.0);
    cl.position.set(cx, cy, cz);
    stormGroup.add(cl);
  }}

  // MASSIVE SPINNING 3D TORNADO FUNNEL (24 stacked swirling rings!)
  const tornadoGrp = new THREE.Group();
  tornadoGrp.position.set(0.65, 3.38, 15.2);
  stormGroup.add(tornadoGrp);
  const tornadoRings = [];
  for (let i = 0; i < 24; i++) {{
    const u = i / 23.0;
    const rad = 0.55 + Math.pow(u, 1.45) * 4.8;
    const col = i % 2 === 0 ? 0x3b423c : 0x2c322d;
    const ring = outlinedMesh(new THREE.TorusGeometry(rad, 0.28 + u * 0.24, 8, 20), toonMat(col), 0.025);
    ring.rotation.x = Math.PI / 2;
    ring.position.y = i * 0.58;
    tornadoGrp.add(ring);
    tornadoRings.push({{ mesh: ring, baseY: i * 0.58, phase: i * 0.55, amp: 0.22 + u * 0.55 }});
  }}

  // Swirling 3D flying wood/roof debris planks + white wind streaks
  const debris = [];
  const debMats = [toonMat(0x7c5432), toonMat(0xc4282e), toonMat(0xdcd8c6)];
  for (let i = 0; i < 22; i++) {{
    const plank = outlinedMesh(new THREE.BoxGeometry(0.18 + (i % 3) * 0.14, 0.07, 0.65 + (i % 4) * 0.25), debMats[i % 3], 0.015);
    stormGroup.add(plank);
    debris.push({{ mesh: plank, ang: i * 0.9, rad: 1.8 + (i % 5) * 1.1, y: 4.5 + (i % 8) * 1.15, spd: 2.2 + (i % 4) * 0.6 }});
  }}
  const windStreaks = [];
  const streakMat = new THREE.MeshBasicMaterial({{ color: 0xeef4ee, transparent: true, opacity: 0.62 }});
  for (let i = 0; i < 10; i++) {{
    const st = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 0.055), streakMat);
    stormGroup.add(st);
    windStreaks.push({{ mesh: st, ph: i * 0.37, y: 3.8 + (i % 5) * 0.9 }});
  }}

  // --- ARTICULATED 3D TOON PARTNER CHARACTER (Rich Burnt Orange Beanie + Warm Mustard Puffer Jacket!) ---
  const partner = new THREE.Group();
  partner.position.set(0.08, 0, -1.35);
  bunkerGroup.add(partner);

  const jacketMat = toonMat(0xc87f16);
  const jacketRingMat = toonMat(0x9a5c0c);
  const beanieMat = toonMat(0xb83a0e);
  const skinMat = toonMat(0xdcd4be);
  const pantsMat = toonMat(0x324a5e);
  const eyeMat = new THREE.MeshBasicMaterial({{ color: 0x111114 }});
  const whiteMat = new THREE.MeshBasicMaterial({{ color: 0xffffff }});
  const mouthMat = new THREE.MeshBasicMaterial({{ color: 0x52161a }});

  // Legs + shoes
  for (const sx of [-0.17, 0.17]) {{
    const leg = outlinedMesh(new THREE.CylinderGeometry(0.145, 0.135, 0.85, 14), pantsMat, 0.018);
    leg.position.set(sx, 0.45, 0);
    const shoe = outlinedMesh(new THREE.BoxGeometry(0.24, 0.14, 0.36), toonMat(0x5a351c), 0.015);
    shoe.position.set(sx, 0.07, 0.06);
    partner.add(leg, shoe);
  }}
  // Belt + buckle
  const belt = outlinedMesh(new THREE.TorusGeometry(0.35, 0.042, 8, 22), toonMat(0x2d4354), 0.014);
  belt.rotation.x = Math.PI / 2;
  belt.position.y = 0.88;
  partner.add(belt);

  // Segmented Yellow Puffer Torso (exact capsule + baffle rings from b_03..b_07!)
  const torso = new THREE.Group();
  torso.position.y = 1.32;
  partner.add(torso);
  const tBody = outlinedMesh(new THREE.CylinderGeometry(0.34, 0.31, 0.88, 18), jacketMat, 0.022);
  torso.add(tBody);
  for (const ry of [-0.26, -0.02, 0.22]) {{
    const baffle = outlinedMesh(new THREE.TorusGeometry(0.345, 0.032, 8, 22), jacketRingMat, 0.010);
    baffle.rotation.x = Math.PI / 2;
    baffle.position.y = ry;
    torso.add(baffle);
  }}
  // Collar + front zipper + silver zipper pull!
  const collar = outlinedMesh(new THREE.TorusGeometry(0.24, 0.075, 10, 20), jacketMat, 0.016);
  collar.rotation.x = Math.PI / 2;
  collar.position.y = 0.44;
  const zip = outlinedMesh(new THREE.BoxGeometry(0.035, 0.86, 0.04), jacketRingMat, 0.008);
  zip.position.set(0.0, 0.0, 0.34);
  const zipTab = outlinedMesh(new THREE.BoxGeometry(0.065, 0.10, 0.05), toonMat(0xdcd8cc), 0.008);
  zipTab.position.set(0.0, 0.34, 0.36);
  torso.add(collar, zip, zipTab);

  // Head + Expressive Eyes + Talking Mouth + Orange Ribbed Beanie!
  const headGrp = new THREE.Group();
  headGrp.position.y = 0.78;
  torso.add(headGrp);

  const headSphere = outlinedMesh(new THREE.SphereGeometry(0.36, 22, 18), skinMat, 0.022);
  headGrp.add(headSphere);

  // Black oval eyes + crisp white catchlight dots!
  for (const ex of [-0.125, 0.125]) {{
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.056, 12, 12), eyeMat);
    eye.scale.set(0.82, 1.25, 0.45);
    eye.position.set(ex, 0.02, 0.335);
    const gl = new THREE.Mesh(new THREE.SphereGeometry(0.019, 8, 8), whiteMat);
    gl.position.set(ex - 0.014, 0.052, 0.358);
    headGrp.add(eye, gl);
  }}
  // Animated talking oval mouth!
  const mouth = new THREE.Mesh(new THREE.SphereGeometry(0.055, 12, 10), mouthMat);
  mouth.scale.set(1.15, 0.45, 0.4);
  mouth.position.set(0, -0.115, 0.345);
  headGrp.add(mouth);

  // Orange ribbed knit beanie!
  const beanieDome = outlinedMesh(new THREE.SphereGeometry(0.375, 22, 14, 0, Math.PI * 2, 0, Math.PI * 0.52), beanieMat, 0.020);
  beanieDome.position.y = 0.06;
  headGrp.add(beanieDome);
  const cuff = outlinedMesh(new THREE.CylinderGeometry(0.39, 0.395, 0.145, 22), beanieMat, 0.018);
  cuff.position.y = 0.11;
  headGrp.add(cuff);
  for (let r = 0; r < 14; r++) {{
    const ang = (r / 14) * Math.PI * 2;
    const rib = outlinedMesh(new THREE.BoxGeometry(0.024, 0.145, 0.03), toonMat(0xb63f0e), 0.005);
    rib.position.set(Math.cos(ang) * 0.395, 0.11, Math.sin(ang) * 0.395);
    rib.rotation.y = -ang;
    headGrp.add(rib);
  }}

  // Articulated Left & Right Puffer Arms + Cute Hands!
  function buildArm(side) {{
    const sh = new THREE.Group();
    sh.position.set(side * 0.42, 0.30, 0);
    const puff = outlinedMesh(new THREE.SphereGeometry(0.145, 14, 12), jacketMat, 0.016);
    const upper = outlinedMesh(new THREE.CylinderGeometry(0.115, 0.105, 0.56, 14), jacketMat, 0.016);
    upper.position.y = -0.28;
    const armRing = outlinedMesh(new THREE.TorusGeometry(0.118, 0.024, 8, 16), jacketRingMat, 0.008);
    armRing.rotation.x = Math.PI / 2; armRing.position.y = -0.28;
    const hand = outlinedMesh(new THREE.SphereGeometry(0.11, 14, 12), skinMat, 0.015);
    hand.scale.set(0.95, 0.72, 1.15);
    hand.position.y = -0.60;
    sh.add(puff, upper, armRing, hand);
    return sh;
  }}
  const armL = buildArm(-1);
  const armR = buildArm(1);
  torso.add(armL, armR);

  // 3D Smartphone Prop attached to Partner's Left Hand (raised cleanly facing camera in Beat 4!)
  const phoneProp = new THREE.Group();
  const phoneBody = outlinedMesh(new THREE.BoxGeometry(0.32, 0.56, 0.038), toonMat(0x181a22), 0.012);
  // Put readable NO SERVICE screen on BOTH faces so camera angle always reads crystal-clear!
  const phoneScrF = new THREE.Mesh(new THREE.PlaneGeometry(0.28, 0.50), new THREE.MeshBasicMaterial({{ map: phoneTex }}));
  phoneScrF.position.z = 0.022;
  const phoneScrB = new THREE.Mesh(new THREE.PlaneGeometry(0.28, 0.50), new THREE.MeshBasicMaterial({{ map: phoneTex }}));
  phoneScrB.position.z = -0.022;
  phoneScrB.rotation.y = Math.PI;
  phoneProp.add(phoneBody, phoneScrF, phoneScrB);
  phoneProp.position.set(0.06, -0.68, 0.06);
  phoneProp.rotation.set(Math.PI * 0.52, 0.14, 0.06);
  phoneProp.visible = false;
  armL.add(phoneProp);

  // --- FIRST-PERSON POV CARTOON GLOVED HANDS ATTACHED TO CAMERA! ---
  const povHands = new THREE.Group();
  camera.add(povHands);
  const gloveMat = toonMat(0xa66434);
  const sleeveMat = toonMat(0x243b42);
  function buildPovHand(side) {{
    const g = new THREE.Group();
    const fist = outlinedMesh(new THREE.SphereGeometry(0.115, 14, 12), gloveMat, 0.012);
    fist.scale.set(1.05, 0.85, 1.35);
    const thumb = outlinedMesh(new THREE.SphereGeometry(0.058, 10, 10), gloveMat, 0.009);
    thumb.position.set(-side * 0.088, 0.02, 0.02);
    const cuff = outlinedMesh(new THREE.CylinderGeometry(0.095, 0.11, 0.28, 12), sleeveMat, 0.012);
    cuff.rotation.x = Math.PI / 2;
    cuff.position.z = 0.22;
    g.add(fist, thumb, cuff);
    g.position.set(side * 0.25, -0.28, -0.52);
    return g;
  }}
  const povHandL = buildPovHand(-1);
  const povHandR = buildPovHand(1);
  povHands.add(povHandL, povHandR);

  // --- CHOREOGRAPHED 3D FRAME RENDERER ---
  const lerp = (a, b, u) => a + (b - a) * Math.max(0, Math.min(1, u));
  const smooth = u => {{ const x = Math.max(0, Math.min(1, u)); return x * x * (3 - 2 * x); }};

  const T_STORM = CFG.t_storm;
  const T_SLAM = CFG.t_slam;
  const T_TIMER = CFG.t_timer;
  const T_PHONE = CFG.t_phone;
  const T_SHELF = CFG.t_shelf;
  const T_KNOCK = CFG.t_knock;
  const T_END = CFG.t_endcard;

  const locEl = document.getElementById('locStamp');
  const serEl = document.getElementById('seriesBanner');
  const tmEl = document.getElementById('timerHud');
  const tmVal = document.getElementById('timerVal');
  const subEl = document.getElementById('subText');
  const endEl = document.getElementById('endCard');

  window.renderAt = function(t) {{
    // 1. Check End Card Cliffhanger
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

    // 2. Spin 3D Tornado & Flying Debris outside hatch
    tornadoGrp.rotation.y = t * 3.8;
    for (const r of tornadoRings) {{
      r.mesh.position.x = Math.sin(t * 4.5 + r.phase) * r.amp;
      r.mesh.position.z = Math.cos(t * 3.8 + r.phase) * r.amp;
    }}
    for (const db of debris) {{
      const a = db.ang + t * db.spd;
      db.mesh.position.set(0.8 + Math.cos(a) * db.rad, db.y + Math.sin(t * 3 + db.ang) * 0.4, 14.0 + Math.sin(a) * db.rad);
      db.mesh.rotation.set(t * 4 + db.ang, t * 3, db.ang);
    }}
    for (const ws of windStreaks) {{
      const cyc = ((t * 2.2 + ws.ph) % 1.0);
      ws.mesh.position.set(lerp(-4.5, 4.5, cyc), ws.y, 4.2 + (ws.ph * 2) % 3);
      ws.mesh.rotation.z = -0.18;
    }}
    // Farmhouse collapses dramatically right before hatch slams!
    if (t > T_STORM + 2.6 && t < T_SLAM + 0.5) {{
      const colP = smooth((t - (T_STORM + 2.6)) / 1.4);
      houseGrp.position.y = lerp(4.7, 3.3, colP);
      houseGrp.rotation.z = lerp(0, 0.42, colP);
      houseGrp.rotation.x = lerp(0, -0.25, colP);
    }} else if (t <= T_STORM + 2.6) {{
      houseGrp.position.y = 4.7;
      houseGrp.rotation.set(0, 0, Math.sin(t * 18) * 0.03);
    }}

    // 3. Hatch Door Swings UPWARD & LEFT (+X hinge) framing the massive unobstructed Tornado + Farmhouse!
    let hatchAngleZ = 0.0;
    let camShake = 0.0;
    let closeP = 0.0;
    if (t < T_SLAM) {{
      closeP = t > (T_SLAM - 0.65) ? smooth((t - (T_SLAM - 0.65)) / 0.65) : 0;
      hatchAngleZ = lerp(-Math.PI * 0.36 + Math.sin(t * 22) * 0.05, 0.0, closeP);
      camShake = t > T_STORM ? 0.045 : 0.015;
    }} else {{
      hatchAngleZ = 0.0;
      const slamImpact = Math.max(0, 1 - (t - T_SLAM) / 0.45);
      camShake = slamImpact * 0.095;
      wheelGrp.rotation.y = smooth((t - T_SLAM) / 0.7) * Math.PI * 1.5;
    }}
    // Eerie metallic knocks at T_KNOCK!
    for (const kOff of [0.0, 0.58, 1.16]) {{
      const kAge = t - (T_KNOCK + kOff);
      if (kAge >= 0 && kAge < 0.24) {{
        const imp = Math.sin((kAge / 0.24) * Math.PI);
        hatchAngleZ = -0.05 * imp;
        camShake = Math.max(camShake, 0.045 * imp);
      }}
    }}
    hatchPivot.rotation.z = hatchAngleZ;
    bunkerBulb.intensity = 1.02 + Math.sin(t * 11) * 0.05 - (camShake * 2.2);

    // 4. First-Person POV Camera Choreography across all 6 Beats!
    let camPos = new THREE.Vector3(0, 2.35, 1.75);
    let lookAt = new THREE.Vector3(0, 1.25, -1.6);
    let handRaise = 0.0;

    // Keep Partner cleanly positioned off-left during stairs intro, then step to center inside bunker!
    const stepIn = smooth((t - (T_STORM + 1.0)) / 1.5);
    partner.position.set(lerp(-1.15, 0.08, stepIn), 0, lerp(-1.85, -1.35, stepIn));

    if (t < T_STORM) {{
      // Beat 1: Descending concrete stairs with yellow handrails (exact b_00 composition!)
      const u = smooth(t / T_STORM);
      camPos.set(0, lerp(3.05, 2.25, u), lerp(2.70, 1.55, u));
      lookAt.set(0.08, lerp(0.55, 1.05, u), lerp(-0.8, -1.3, u));
      handRaise = 0.0;
    }} else if (t < T_SLAM + 0.5) {{
      // Beat 2: Peering straight OUT over hatch sill at giant roaring Tornado + Red-Roofed Farmhouse + open steel hatch!
      // Smoothly ducks back under hatch right as closeP slams the steel door shut (zero clipping!).
      const u = smooth((t - T_STORM) / 0.75);
      const duckP = t > (T_SLAM - 0.75) ? smooth((t - (T_SLAM - 0.75)) / 0.70) : 0.0;
      const cy = lerp(lerp(2.25, 3.84, u), 2.38, duckP);
      const cz = lerp(lerp(1.55, 1.72, u), 1.55, duckP);
      camPos.set(lerp(0.0, -0.06, u * (1 - duckP)), cy, cz);
      lookAt.set(-0.22, lerp(lerp(1.2, 5.75, u), 3.35, duckP), lerp(lerp(0.5, 13.5, u), 2.6, duckP));
      handRaise = 0.28;
    }} else if (t < T_PHONE) {{
      // Beat 3: Sealed inside bunker facing Partner with generous headroom for SURVIVE timer!
      const u = smooth((t - (T_SLAM + 0.5)) / 0.90);
      camPos.set(0, lerp(2.38, 1.88, u), lerp(1.55, 0.65, u));
      lookAt.set(0.08, lerp(3.35, 1.82, u), lerp(2.6, -1.35, u));
      handRaise = 0.05;
    }} else if (t < T_SHELF) {{
      // Beat 4: Partner raises glowing NO SERVICE smartphone clearly toward POV camera (exact b_05!)
      const u = smooth((t - T_PHONE) / 0.65);
      camPos.set(lerp(0, -0.04, u), 1.84, lerp(0.65, 0.35, u));
      lookAt.set(-0.08, 1.80, -1.35);
      handRaise = 0.02;
    }} else if (t < T_KNOCK) {{
      // Beat 5: POV pans LEFT to inspect stocked food/water shelf, then back to Partner!
      const dur5 = T_KNOCK - T_SHELF;
      const local = t - T_SHELF;
      if (local < dur5 * 0.55) {{
        const u = smooth(local / 0.95);
        camPos.set(lerp(-0.04, -0.15, u), 1.65, lerp(0.35, -0.10, u));
        lookAt.set(lerp(-0.08, -2.35, u), lerp(1.80, 1.32, u), lerp(-1.35, -0.75, u));
      }} else {{
        const u = smooth((local - dur5 * 0.55) / 0.85);
        camPos.set(lerp(-0.15, 0.05, u), 1.84, lerp(-0.10, 0.48, u));
        lookAt.set(lerp(-2.35, 0.08, u), lerp(1.32, 1.88, u), lerp(-0.75, -1.35, u));
        handRaise = lerp(0.05, 0.34, u);
      }}
    }} else {{
      // Beat 6: Eerie KNOCK-KNOCK-KNOCK! POV snaps sharply UP stairs at the sealed steel hatch & red wheel!
      const u = smooth((t - T_KNOCK) / 0.60);
      camPos.set(lerp(0.05, 0.0, u), lerp(1.84, 1.15, u), lerp(0.48, 0.25, u));
      lookAt.set(0.0, lerp(1.88, 3.05, u), lerp(-1.35, 2.25, u));
      handRaise = 0.22;
    }}

    // Breathing bob + camera shake
    const sx = (Math.sin(t * 47) * camShake);
    const sy = Math.sin(t * 2.8) * 0.022 + (Math.cos(t * 53) * camShake);
    camera.position.set(camPos.x + sx, camPos.y + sy, camPos.z);
    camera.lookAt(lookAt);

    // Animate POV foreground cartoon gloved hands clearly in frame!
    const hb = Math.sin(t * 3.1) * 0.014;
    povHandL.position.set(-0.24, -0.27 + handRaise * 0.16 + hb, -0.52);
    povHandR.position.set(0.24, -0.27 + handRaise * 0.16 - hb, -0.52);
    povHandL.rotation.set(handRaise * 0.45, 0.25, -0.18);
    povHandR.rotation.set(handRaise * 0.45, -0.25, 0.18);

    // 5. Partner Character Acting & Lip-Sync!
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

    // Phone raise animation on Partner's LEFT arm (displays cleanly on left-center of frame like b_05!)
    const phoneIn = (t >= T_PHONE && t < T_SHELF)
      ? Math.min(smooth((t - T_PHONE) / 0.55), smooth((T_SHELF - t) / 0.45))
      : 0;
    phoneProp.visible = phoneIn > 0.05;
    armL.rotation.x = lerp(partnerSpeaking ? (-0.45 + Math.sin(t * 4.5 + 1) * 0.22) : -0.12, -1.72, phoneIn);
    armL.rotation.z = lerp(-0.14, 0.24, phoneIn);
    armR.rotation.x = partnerSpeaking ? (-0.42 + Math.sin(t * 5.2) * 0.24) : -0.14;
    armR.rotation.z = 0.14;

    // 6. HUD Overlays (Location Stamp, Red Banner, Ticking Countdown Clock, Bold Outlined Subtitles)
    const introA = t < T_STORM ? Math.min(smooth(t / 0.4), smooth((T_STORM - t) / 0.45)) : 0;
    locEl.style.opacity = introA.toFixed(3);
    serEl.style.opacity = introA.toFixed(3);

    if (t >= T_TIMER) {{
      tmEl.style.opacity = smooth((t - T_TIMER) / 0.35).toFixed(3);
      const elapsedSec = Math.max(0, Math.floor(t - T_TIMER));
      const rem = Math.max(0, 72 * 3600 - 1 - elapsedSec);
      const hh = Math.floor(rem / 3600);
      const mm = Math.floor((rem % 3600) / 60);
      const ss = rem % 60;
      tmVal.textContent = `${{String(hh).padStart(2,'0')}}:${{String(mm).padStart(2,'0')}}:${{String(ss).padStart(2,'0')}}`;
    }} else {{
      tmEl.style.opacity = '0';
    }}

    if (activeLine) {{
      // Split long lines cleanly into snappy 4-6 word caption beats!
      const words = activeLine.text.split(/\\s+/);
      const chunkSz = 5;
      const chunks = [];
      for (let i = 0; i < words.length; i += chunkSz) chunks.push(words.slice(i, i + chunkSz).join(' '));
      const frac = Math.max(0, Math.min(0.999, (t - activeLine.start) / Math.max(activeLine.end - activeLine.start, 0.2)));
      const chunkTxt = chunks[Math.floor(frac * chunks.length)] || activeLine.text;
      subEl.textContent = chunkTxt;
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
# Full Studio v9 3D POV Bunker Episode Demo Builder
# ---------------------------------------------------------------------------

BUNKER_DEMO_SCRIPT: list[dict[str, Any]] = [
    {"beat": "intro", "speaker": "partner", "text": "Get down the stairs! The tornado is right here!"},
    {"beat": "storm", "speaker": "pov", "text": "Grab the wheel! It's not holding—the house just collapsed!"},
    {"beat": "sealed", "speaker": "partner", "text": "We're locked in. Listen carefully. The hatch is buried under debris. Rescue won't reach us for seventy-two hours."},
    {"beat": "timer_react", "speaker": "pov", "text": "Seventy-two hours?!"},
    {"beat": "phone", "speaker": "partner", "text": "No service. Zero bars. Nobody even knows we made it down here."},
    {"beat": "shelf", "speaker": "partner", "text": "We have food and water for three days... but there's one problem."},
    {"beat": "problem", "speaker": "pov", "text": "Wait... what problem?"},
    {"beat": "knock", "speaker": "partner", "text": "Nobody else lives within five miles of this farm... so who is knocking on the hatch?!"},
]


def build_3d_pov_bunker_demo(
    out_mp4: Path,
    width: int = 720,
    height: int = 1280,
    fps: int = 24,
) -> dict[str, Any]:
    """Render complete Studio v9 3D Cel-Shaded First-Person POV Survival Demo."""
    from playwright.sync_api import sync_playwright

    project_root = Path(__file__).resolve().parent.parent
    three_js_path = project_root / "assets" / "vendor" / "three.min.js"
    if not three_js_path.exists():
        raise FileNotFoundError(f"Missing local Three.js bundle at {three_js_path}")

    work_dir = out_mp4.parent / "_v9_3d_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    # 1. Synthesize 2-speaker neural dialogue with exact beat timing!
    voice_partner = "en-US-ChristopherNeural"
    voice_pov = "en-US-AndrewMultilingualNeural"

    dialogue_events: list[dict[str, Any]] = []
    beat_starts: dict[str, float] = {}
    cursor = 0.55

    print("[v9-3d-pov] Synthesizing 2-speaker thriller dialogue...", flush=True)
    for idx, line in enumerate(BUNKER_DEMO_SCRIPT):
        mp3 = work_dir / f"dlg_{idx:02d}.mp3"
        wav = work_dir / f"dlg_{idx:02d}.wav"
        voice = voice_partner if line["speaker"] == "partner" else voice_pov
        rate = "+4%" if line["speaker"] == "partner" else "+6%"
        dur = asyncio.run(_synth_edge_line(line["text"], mp3, voice=voice, rate=rate))
        subprocess.run(["ffmpeg", "-y", "-i", str(mp3), "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(wav)], capture_output=True, check=True)

        # Extra dramatic pauses before hatch slam and eerie knocking!
        if line["beat"] == "sealed":
            cursor += 0.95
        elif line["beat"] == "knock":
            cursor += 1.45

        beat_starts[line["beat"]] = cursor
        dialogue_events.append({
            "beat": line["beat"],
            "speaker": line["speaker"],
            "text": line["text"],
            "start": round(cursor, 3),
            "end": round(cursor + dur, 3),
            "wav_path": str(wav),
        })
        cursor += dur + 0.38

    t_storm = beat_starts["storm"] - 0.25
    t_slam = beat_starts["sealed"] - 0.65
    t_timer = beat_starts["timer_react"] - 0.25
    t_phone = beat_starts["phone"] - 0.25
    t_shelf = beat_starts["shelf"] - 0.25
    t_knock = beat_starts["knock"] - 1.30
    t_endcard = cursor + 0.55
    total_dur = t_endcard + 4.4  # Hold interactive A/B cliffhanger end screen 4.4s!

    # 2. Mix 2-speaker dialogue + procedural thriller SFX soundscape!
    print(f"[v9-3d-pov] Mixing thriller soundscape (total {total_dur:.1f}s)...", flush=True)
    audio_m4a = work_dir / "master_thriller.m4a"
    _build_thriller_soundscape(
        dialogue_events=dialogue_events,
        total_dur=total_dur,
        slam_time=t_slam,
        timer_time=t_timer,
        knock_time=t_knock,
        endcard_time=t_endcard,
        out_m4a=audio_m4a,
        work_dir=work_dir,
    )

    # 3. Render real-time Three.js 3D WebGL Toon frames straight to FFmpeg H.264!
    timeline_cfg = {
        "loc_main": "MORRIS FARM • 4:17 PM",
        "loc_sub": "Kansas • Part 1",
        "series_title": "THE BUNKER",
        "option_a": "OPEN THE BUNKER DOOR",
        "option_b": "STAY INSIDE AND IGNORE THE KNOCKING",
        "t_storm": round(t_storm, 3),
        "t_slam": round(t_slam, 3),
        "t_timer": round(t_timer, 3),
        "t_phone": round(t_phone, 3),
        "t_shelf": round(t_shelf, 3),
        "t_knock": round(t_knock, 3),
        "t_endcard": round(t_endcard, 3),
        "dialogue": [
            {"speaker": e["speaker"], "text": e["text"], "start": e["start"], "end": e["end"]}
            for e in dialogue_events
        ],
    }

    html_doc = _build_3d_pov_html(three_js_path.read_text(encoding="utf-8"), timeline_cfg, width, height)
    total_frames = int(round(total_dur * fps))
    silent_mp4 = work_dir / "video_3d_silent.mp4"

    print(f"[v9-3d-pov] Rendering {total_frames} real 3D WebGL toon frames ({width}x{height} @ {fps}fps)...", flush=True)
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
                # Static endcard optimization after fade-in finishes!
                if t > t_endcard + 0.45 and last_end_jpg is not None:
                    proc.stdin.write(last_end_jpg)
                    continue
                page.evaluate(f"window.renderAt({t:.4f})")
                jpg_bytes = page.screenshot(type="jpeg", quality=92)
                if t > t_endcard + 0.45:
                    last_end_jpg = jpg_bytes
                proc.stdin.write(jpg_bytes)
                if f_i > 0 and f_i % 240 == 0:
                    print(f"[v9-3d-pov] Rendered {f_i}/{total_frames} frames ({100*f_i/total_frames:.0f}%)...", flush=True)
        finally:
            br.close()
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()

    err = proc.stderr.read().decode("utf-8", errors="ignore") if proc.stderr else ""
    ret = proc.wait()
    if ret != 0:
        raise RuntimeError(f"FFmpeg v9 3D pipe failed ({ret}): {err[-300:]}")

    # 4. Mux 3D video + thriller soundscape!
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
            "intro": 1.8,
            "storm": round(t_storm + 1.8, 2),
            "sealed": round(t_slam + 2.4, 2),
            "timer": round(t_timer + 0.6, 2),
            "phone": round(t_phone + 2.0, 2),
            "shelf": round(t_shelf + 1.6, 2),
            "knock": round(t_knock + 1.8, 2),
            "endcard": round(t_endcard + 1.5, 2),
        },
    }


if __name__ == "__main__":
    out_file = Path("output/_v9_3d_pov_demo/the_bunker_3d_pov_demo_9x16.mp4")
    info = build_3d_pov_bunker_demo(out_file)
    print("V9 3D DEMO COMPLETE:", json.dumps(info, indent=2))
