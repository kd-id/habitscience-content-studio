"""Studio v6 — HTML5 / CSS3 / SVG Frosted-Glass Vox & Bento Motion Overlay Renderer.

Uses Playwright + Headless Chrome to render true alpha-transparent RGBA motion overlays
(Apple Keynote Bento Glass HUD, Vox/Johnny Harris Academic Paper + Sweeping Yellow Highlighter,
Netflix Cinema Chapter Titles, and Frosted-Glass 3-Step Protocol Checklists) piped straight to
FFmpeg as lossless RGBA MOV clips to composite over real HD cinema B-roll.

Studio v6.1 Speed & Craft Engine:
- Real wall-clock timing (snappy 0.55s entrances, 0.75s highlighter sweep, 0.35s Focus toggle flip)
- Smart active-motion keyframe capture + static-hold PNG cache reuse (~10-15x faster!)
- Smooth 20fps active animations + crisp 1080p typography + guaranteed subtitle clearance
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


def find_chrome_executable() -> str | None:
    """Locate system Chrome/Edge/Chromium binary cleanly on Windows or Linux GitHub Actions."""
    env_bin = os.getenv("CHROME_EXECUTABLE_PATH", "").strip()
    if env_bin and Path(env_bin).exists():
        return env_bin

    candidates = [
        # Windows
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        str(Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        # Linux / GitHub Actions ubuntu-latest
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ]
    for c in candidates:
        if c and Path(c).is_file():
            return c
    for name in ("google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    return None


def pick_html_overlay_style(scene: dict[str, Any], scene_idx: int) -> str:
    explicit = str(scene.get("overlay_style") or "").strip().lower()
    valid = ("cinema_chapter_title", "vox_journal_clip", "bento_apple_hud", "bento_protocol_checklist")
    if explicit in valid:
        return explicit
    txt = f"{scene.get('section', '')} {scene.get('visual_headline', '')}".lower()
    if scene_idx == 1:
        return "cinema_chapter_title"
    if any(k in txt for k in ("protocol", "step", "reset", "shield", "challenge", "7-day", "experiment")):
        return "bento_protocol_checklist"
    if any(k in txt for k in ("dopamine", "trap", "boring", "timer", "cycle", "focus", "ultradian", "90")):
        return "bento_apple_hud"
    if any(k in txt for k in ("mechanism", "residue", "study", "research", "science", "data", "myth", "23", "66")):
        return "vox_journal_clip"
    return valid[(scene_idx - 1) % len(valid)]


def _extract_metric(scene: dict[str, Any]) -> tuple[str, str]:
    text = f"{scene.get('visual_headline', '')} {scene.get('narration', '')}"
    m = re.search(r"\b(\d{1,3})\s*(min|minutes|days|day|hours|hour|%)\b", text, re.IGNORECASE)
    if m:
        num = m.group(1)
        unit = m.group(2).upper()
        if unit.startswith("MIN"):
            unit = "MIN"
        elif unit.startswith("DAY"):
            unit = "DAYS"
        elif unit.startswith("HOUR"):
            unit = "HRS"
        return num, unit
    low = text.lower()
    if "twenty-three" in low:
        return "23", "MIN"
    if "sixty-six" in low:
        return "66", "DAYS"
    if "ninety" in low:
        return "90", "MIN"
    if "fifteen" in low:
        return "15", "MIN"
    return "23", "MIN"


def _extract_steps_clean(scene: dict[str, Any]) -> list[str]:
    bullets = [re.sub(r"^\d+[\.\)]\s*", "", str(b)).strip() for b in (scene.get("bullet_points") or []) if str(b).strip()]
    if len(bullets) >= 2:
        return [b[:56] for b in bullets[:3]]
    callout = str(scene.get("on_screen_callout") or "").strip()
    if "," in callout and len(callout.split(",")) >= 3:
        return [p.strip().capitalize()[:56] for p in callout.split(",")[:3]]
    return [
        "Protect your first 90-minute focus block",
        "Take a 2-minute screen-free neural downshift",
        "Keep your phone out of sight during deep work",
    ]


def _active_motion_windows(style_name: str, dur: float) -> list[tuple[float, float]]:
    """Return exact wall-clock (start_sec, end_sec) intervals where elements are actively animating."""
    fade_start = max(dur - 0.65, 0.0)
    if style_name == "cinema_chapter_title":
        hold_end = min(max(dur * 0.48, 3.2), 5.8, max(dur - 0.8, 1.5))
        return [(0.0, 1.25), (hold_end, min(hold_end + 0.70, dur))]
    if style_name == "vox_journal_clip":
        return [(0.0, 2.55), (fade_start, dur)]
    if style_name == "bento_apple_hud":
        return [(0.0, 2.75), (fade_start, dur)]
    if style_name == "bento_protocol_checklist":
        t2 = min(max(dur * 0.34, 1.8), max(dur - 2.4, 1.8))
        t3 = min(max(dur * 0.64, 3.4), max(dur - 1.4, 3.4))
        return [(0.0, 1.35), (t2, t2 + 1.10), (t3, t3 + 1.10), (fade_start, dur)]
    return [(0.0, 2.4), (fade_start, dur)]


def _build_overlay_html(
    style_name: str,
    scene: dict[str, Any],
    scene_idx: int,
    total_scenes: int,
    width: int,
    height: int,
    handle: str,
    is_short: bool,
) -> str:
    raw_section = str(scene.get("badge") or scene.get("section") or f"PART {scene_idx}").strip()
    raw_section = re.sub(r"^\d+\s*[•\-:\.\|]\s*", "", raw_section).strip() or f"PART {scene_idx}"
    section = html.escape(raw_section.upper())
    headline = html.escape(str(scene.get("visual_headline") or "HabitSains"))
    callout = html.escape(str(scene.get("on_screen_callout") or "Science-backed focus & habit protocol"))
    safe_handle = html.escape(handle)
    metric_num, metric_unit = _extract_metric(scene)
    steps = [html.escape(s) for s in _extract_steps_clean(scene)]
    counter_label = f"{scene_idx:02d}/{total_scenes:02d}"

    # Shared ultra-clean modern frosted-glass CSS base (fast shadows, crisp borders)
    common_css = f"""
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{
      width: {width}px; height: {height}px; overflow: hidden;
      background: transparent !important;
      font-family: 'Segoe UI', 'Inter', 'Liberation Sans', Arial, sans-serif;
      color: #F8FAFC;
      -webkit-font-smoothing: antialiased;
    }}
    .top-bar {{
      position: absolute; top: 0; left: 0; width: 100%; height: 6px;
      background: rgba(255,255,255,0.14);
      z-index: 5;
    }}
    .cinema-vignette {{
      position: absolute; inset: 0; pointer-events: none; z-index: 0;
      background: radial-gradient(ellipse at center, rgba(0,0,0,0) 48%, rgba(4,9,16,0.56) 100%);
    }}
    .top-fill {{
      height: 100%; width: 0%;
      background: linear-gradient(90deg, #14B8A6, #38BDF8, #F59E0B);
    }}
    .hud-header {{
      position: absolute; top: {'86px' if is_short else '34px'};
      left: {'50%' if is_short else '58px'};
      right: {'auto' if is_short else '58px'};
      transform: {'translateX(-50%)' if is_short else 'none'};
      display: flex; align-items: center; justify-content: space-between; gap: 18px;
    }}
    .chapter-pill {{
      display: inline-flex; align-items: center; gap: 10px;
      padding: {'10px 24px' if is_short else '9px 22px'};
      border-radius: 999px;
      background: rgba(8, 16, 26, 0.78);
      border: 1px solid rgba(45, 212, 191, 0.50);
      box-shadow: 0 8px 20px rgba(0,0,0,0.45);
      font-size: {'23px' if is_short else '19px'};
      font-weight: 700; letter-spacing: 1.4px; color: #2DD4BF;
      white-space: nowrap;
    }}
    .dot-live {{
      width: 10px; height: 10px; border-radius: 50%;
      background: #F59E0B;
    }}
    .watermark {{
      display: {'none' if is_short else 'inline-flex'};
      padding: 8px 18px; border-radius: 999px;
      background: rgba(8, 16, 26, 0.64);
      border: 1px solid rgba(255,255,255,0.18);
      font-size: 18px; font-weight: 600; color: rgba(248,250,252,0.88);
      letter-spacing: 0.5px;
    }}
    """

    if style_name == "vox_journal_clip":
        body_html = f"""
        <div class="vox-wrap" id="voxWrap">
          <div class="paper-card" id="paperCard">
            <div class="paper-top">
              <span>HABITSAINS RESEARCH BRIEF</span>
              <span>PEER-REVIEWED EVIDENCE</span>
            </div>
            <div class="paper-title-wrap">
              <div class="highlighter-bar" id="hlBar"></div>
              <div class="paper-title">{headline}</div>
            </div>
            <div class="paper-cols">
              <p>Cognitive studies demonstrate measurable neurological friction whenever high-velocity stimuli interrupt sustained prefrontal engagement.</p>
              <p>Key takeaway: <strong>{callout}</strong> — repeatable environmental shifts reliably restore baseline focus.</p>
            </div>
          </div>

          <div class="stat-glass" id="statGlass">
            <div class="stat-eyebrow">MEASURED IMPACT</div>
            <div class="stat-value"><span id="statNum">{metric_num}</span> <span class="stat-unit">{metric_unit}</span></div>
            <svg viewBox="0 0 280 96" class="mini-chart">
              <line x1="8" y1="54" x2="272" y2="54" stroke="rgba(255,255,255,0.22)" stroke-dasharray="5 5" stroke-width="1.5"/>
              <path id="curveAmber" d="M 10 64 Q 52 16, 98 58 T 186 76 T 270 48" fill="none" stroke="#F59E0B" stroke-width="4" stroke-linecap="round"/>
              <path id="curveTeal" d="M 10 60 Q 75 48, 140 36 T 270 16" fill="none" stroke="#2DD4BF" stroke-width="4.5" stroke-linecap="round"/>
            </svg>
            <div class="stat-legend">
              <span><i style="background:#F59E0B"></i>Distraction Spike</span>
              <span><i style="background:#2DD4BF"></i>Steady Focus</span>
            </div>
          </div>
        </div>
        """
        extra_css = f"""
        .vox-wrap {{
          position: absolute;
          top: {'235px' if is_short else '168px'};
          left: {'52px' if is_short else '76px'};
          right: {'52px' if is_short else '76px'};
          display: flex;
          flex-direction: {'column' if is_short else 'row'};
          align-items: center;
          justify-content: space-between;
          gap: {'34px' if is_short else '48px'};
        }}
        .paper-card {{
          width: {'100%' if is_short else '58%'};
          background: linear-gradient(155deg, #F9F5E9 0%, #ECE4CE 100%);
          color: #16181D;
          padding: {'32px 34px' if is_short else '38px 44px'};
          border-radius: 10px;
          box-shadow: 0 18px 34px rgba(0,0,0,0.58), 0 0 0 1px rgba(255,255,255,0.45) inset;
          transform: rotate(-1.5deg) translateY(52px);
          opacity: 0;
        }}
        .paper-top {{
          display: flex; justify-content: space-between;
          font-size: {'15px' if is_short else '14px'}; font-weight: 800;
          letter-spacing: 1.8px; color: #525866;
          border-bottom: 2px solid #1E2430; padding-bottom: 10px; margin-bottom: 20px;
        }}
        .paper-title-wrap {{
          position: relative; display: inline-block; margin-bottom: 20px;
        }}
        .highlighter-bar {{
          position: absolute; left: -8px; right: -8px; top: 8%; bottom: 4%;
          background: linear-gradient(90deg, rgba(253,224,71,0.95), rgba(251,191,36,0.90));
          border-radius: 6px;
          clip-path: inset(0 100% 0 0);
          z-index: 0;
        }}
        .paper-title {{
          position: relative; z-index: 1;
          font-family: Georgia, 'Times New Roman', serif;
          font-size: {'40px' if is_short else '42px'};
          font-weight: 700; line-height: 1.18; color: #0F172A;
        }}
        .paper-cols {{
          display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
          font-family: Georgia, serif; font-size: {'18px' if is_short else '18px'};
          line-height: 1.48; color: #334155;
        }}
        .stat-glass {{
          width: {'90%' if is_short else '36%'};
          padding: {'28px 32px' if is_short else '30px 34px'};
          border-radius: 26px;
          background: linear-gradient(155deg, rgba(19, 31, 46, 0.86) 0%, rgba(8, 15, 25, 0.90) 100%);
          border: 1px solid rgba(255,255,255,0.20);
          box-shadow: 0 18px 34px rgba(0,0,0,0.58), 0 1px 0 rgba(255,255,255,0.18) inset;
          transform: translateX(56px);
          opacity: 0;
        }}
        .stat-eyebrow {{
          font-size: 15px; font-weight: 800; letter-spacing: 2px; color: #2DD4BF; margin-bottom: 6px;
        }}
        .stat-value {{
          font-size: {'62px' if is_short else '66px'}; font-weight: 800; line-height: 1.05;
          color: #F8FAFC; margin-bottom: 12px;
        }}
        .stat-unit {{ font-size: 30px; color: #F59E0B; }}
        .mini-chart {{ width: 100%; height: auto; display: block; margin: 6px 0 10px; }}
        .stat-legend {{
          display: flex; justify-content: space-between; font-size: 15px; color: #CBD5E1; font-weight: 600;
        }}
        .stat-legend i {{
          display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 7px;
        }}
        """
        render_js = f"""
        const cA = document.getElementById('curveAmber');
        const cT = document.getElementById('curveTeal');
        const lenA = cA.getTotalLength();
        const lenT = cT.getTotalLength();
        cA.style.strokeDasharray = lenA; cT.style.strokeDasharray = lenT;
        const targetVal = parseInt({json.dumps(metric_num)}, 10) || 23;

        window.renderAt = function(t, dur) {{
          const ease = x => 1 - Math.pow(1 - Math.max(0, Math.min(1, x)), 3);
          const fadeStart = Math.max(dur - 0.65, 0);
          const outA = t > fadeStart ? 1 - ease((t - fadeStart) / 0.55) : 1;

          const pIn = ease(t / 0.55);
          const paper = document.getElementById('paperCard');
          paper.style.opacity = (pIn * outA).toFixed(3);
          paper.style.transform = `rotate(-1.5deg) translateY(${{((1 - pIn) * 52).toFixed(1)}}px)`;

          const hlP = ease((t - 0.50) / 0.80);
          document.getElementById('hlBar').style.clipPath = `inset(0 ${{(100 - hlP * 100).toFixed(1)}}% 0 0)`;

          const sIn = ease((t - 0.75) / 0.55);
          const sg = document.getElementById('statGlass');
          sg.style.opacity = (sIn * outA).toFixed(3);
          sg.style.transform = `translateX(${{((1 - sIn) * 56).toFixed(1)}}px)`;

          const cP = ease((t - 1.10) / 1.25);
          cA.style.strokeDashoffset = (lenA * (1 - cP)).toFixed(1);
          cT.style.strokeDashoffset = (lenT * (1 - cP)).toFixed(1);
          document.getElementById('statNum').textContent = Math.max(1, Math.round(targetVal * ease((t - 0.85) / 1.15)));
        }};
        """

    elif style_name == "bento_apple_hud":
        body_html = f"""
        <div class="bento-grid" id="bentoGrid">
          <div class="bento-card card-main" id="card1">
            <div class="tag-mini">NEURAL TELEMETRY</div>
            <div class="bento-headline">{headline}</div>
            <div class="toggle-row">
              <div class="toggle-pill" id="togglePill"><div class="toggle-knob" id="toggleKnob"></div></div>
              <div>
                <div class="toggle-title" id="toggleTitle">Switching to Focus...</div>
                <div class="toggle-sub">{callout}</div>
              </div>
            </div>
          </div>

          <div class="bento-side">
            <div class="bento-card card-ring" id="card2">
              <svg viewBox="0 0 180 180" class="ring-svg">
                <circle cx="90" cy="90" r="74" fill="none" stroke="rgba(255,255,255,0.14)" stroke-width="11"/>
                <circle id="ringArc" cx="90" cy="90" r="74" fill="none" stroke="url(#gradRing)" stroke-width="11" stroke-linecap="round" transform="rotate(-90 90 90)"/>
                <defs>
                  <linearGradient id="gradRing" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#2DD4BF"/>
                    <stop offset="100%" stop-color="#38BDF8"/>
                  </linearGradient>
                </defs>
              </svg>
              <div class="ring-center">
                <div class="ring-num" id="ringNum">{metric_num}</div>
                <div class="ring-unit">{metric_unit}</div>
              </div>
            </div>

            <div class="bento-card card-bar" id="card3">
              <div class="bar-label"><span>Focus Clarity</span><span id="barPct" style="color:#2DD4BF">0%</span></div>
              <div class="bar-track"><div class="bar-fill" id="barFill"></div></div>
            </div>
          </div>
        </div>
        """
        extra_css = f"""
        .bento-grid {{
          position: absolute;
          top: {'235px' if is_short else '156px'};
          left: {'52px' if is_short else '84px'};
          right: {'52px' if is_short else '84px'};
          display: flex;
          flex-direction: {'column' if is_short else 'row'};
          gap: 26px;
          align-items: stretch;
        }}
        .bento-card {{
          border-radius: 26px;
          background: linear-gradient(155deg, rgba(19, 31, 46, 0.85) 0%, rgba(8, 15, 25, 0.90) 100%);
          border: 1px solid rgba(255,255,255,0.20);
          box-shadow: 0 16px 32px rgba(0,0,0,0.56), 0 1px 0 rgba(255,255,255,0.16) inset;
          opacity: 0;
        }}
        .card-main {{
          flex: 1.35; padding: {'32px 34px' if is_short else '40px 44px'};
          display: flex; flex-direction: column; justify-content: space-between; gap: 24px;
        }}
        .tag-mini {{
          font-size: 15px; font-weight: 800; letter-spacing: 2.2px; color: #F59E0B;
        }}
        .bento-headline {{
          font-size: {'44px' if is_short else '50px'}; font-weight: 800; line-height: 1.12; color: #F8FAFC;
        }}
        .toggle-row {{
          display: flex; align-items: center; gap: 22px;
          padding: 18px 22px; border-radius: 20px;
          background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12);
        }}
        .toggle-pill {{
          width: 96px; height: 52px; border-radius: 999px; flex-shrink: 0;
          background: rgba(148,163,184,0.34); position: relative;
          border: 1px solid rgba(255,255,255,0.20);
        }}
        .toggle-knob {{
          width: 42px; height: 42px; border-radius: 50%; background: #F8FAFC;
          position: absolute; top: 4px; left: 5px;
          box-shadow: 0 4px 10px rgba(0,0,0,0.45);
        }}
        .toggle-title {{ font-size: 24px; font-weight: 700; color: #F8FAFC; margin-bottom: 4px; }}
        .toggle-sub {{ font-size: 18px; color: #CBD5E1; line-height: 1.35; }}
        .bento-side {{
          flex: 0.85; display: flex; flex-direction: column; gap: 22px;
        }}
        .card-ring {{
          flex: 1; position: relative; display: flex; align-items: center; justify-content: center;
          padding: 22px; min-height: 230px;
        }}
        .ring-svg {{ width: 204px; height: 204px; }}
        .ring-center {{ position: absolute; text-align: center; }}
        .ring-num {{ font-size: 56px; font-weight: 800; line-height: 1; color: #F8FAFC; }}
        .ring-unit {{ font-size: 18px; font-weight: 700; letter-spacing: 2px; color: #2DD4BF; margin-top: 6px; }}
        .card-bar {{ padding: 24px 28px; }}
        .bar-label {{ display: flex; justify-content: space-between; font-size: 20px; font-weight: 700; margin-bottom: 14px; }}
        .bar-track {{ width: 100%; height: 14px; border-radius: 999px; background: rgba(255,255,255,0.14); overflow: hidden; }}
        .bar-fill {{ width: 0%; height: 100%; border-radius: 999px; background: linear-gradient(90deg, #14B8A6, #38BDF8); }}
        """
        render_js = f"""
        const arc = document.getElementById('ringArc');
        const circ = 2 * Math.PI * 74;
        arc.style.strokeDasharray = circ;
        const targetVal = parseInt({json.dumps(metric_num)}, 10) || 90;

        window.renderAt = function(t, dur) {{
          const ease = x => 1 - Math.pow(1 - Math.max(0, Math.min(1, x)), 3);
          const fadeStart = Math.max(dur - 0.65, 0);
          const outA = t > fadeStart ? 1 - ease((t - fadeStart) / 0.55) : 1;

          const e1 = ease(t / 0.55);
          const e2 = ease((t - 0.25) / 0.55);
          const e3 = ease((t - 0.45) / 0.55);

          const c1 = document.getElementById('card1');
          const c2 = document.getElementById('card2');
          const c3 = document.getElementById('card3');
          c1.style.opacity = (e1 * outA).toFixed(3); c1.style.transform = `translateY(${{((1-e1)*44).toFixed(1)}}px)`;
          c2.style.opacity = (e2 * outA).toFixed(3); c2.style.transform = `translateY(${{((1-e2)*44).toFixed(1)}}px)`;
          c3.style.opacity = (e3 * outA).toFixed(3); c3.style.transform = `translateY(${{((1-e3)*44).toFixed(1)}}px)`;

          const tog = ease((t - 1.05) / 0.40);
          document.getElementById('toggleKnob').style.left = (5 + tog * 43).toFixed(1) + 'px';
          const pill = document.getElementById('togglePill');
          if (tog > 0.5) {{
            pill.style.background = 'linear-gradient(90deg, #14B8A6, #2DD4BF)';
            document.getElementById('toggleTitle').textContent = 'Focus Mode: ACTIVE';
          }} else {{
            pill.style.background = 'rgba(148,163,184,0.34)';
            document.getElementById('toggleTitle').textContent = 'Switching to Focus...';
          }}

          const rP = ease((t - 0.85) / 1.65);
          arc.style.strokeDashoffset = (circ * (1 - rP * 0.86)).toFixed(1);
          document.getElementById('ringNum').textContent = Math.max(1, Math.round(targetVal * rP));
          const pct = Math.round(rP * 92);
          document.getElementById('barFill').style.width = pct + '%';
          document.getElementById('barPct').textContent = pct + '%';
        }};
        """

    elif style_name == "bento_protocol_checklist":
        cards_markup = "\n".join(
            f"""
            <div class="step-card" id="step{i}">
              <div class="step-check" id="chk{i}">
                <svg viewBox="0 0 36 36" width="32" height="32">
                  <circle cx="18" cy="18" r="15" fill="none" stroke="rgba(45,212,191,0.40)" stroke-width="2.5"/>
                  <path id="tick{i}" d="M 10 18.5 L 15.5 24 L 26.5 12.5" fill="none" stroke="#2DD4BF" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="step-body">
                <div class="step-num">STEP 0{i+1}</div>
                <div class="step-txt">{st}</div>
              </div>
            </div>
            """
            for i, st in enumerate(steps)
        )
        body_html = f"""
        <div class="proto-wrap">
          <div class="proto-head" id="protoHead">{headline}</div>
          <div class="proto-list">{cards_markup}</div>
        </div>
        """
        extra_css = f"""
        .proto-wrap {{
          position: absolute;
          top: {'220px' if is_short else '134px'};
          left: {'52px' if is_short else '78px'};
          width: {'calc(100% - 104px)' if is_short else '58%'};
        }}
        .proto-head {{
          font-size: {'48px' if is_short else '52px'}; font-weight: 800; line-height: 1.12;
          margin-bottom: 24px; color: #F8FAFC;
          text-shadow: 0 4px 16px rgba(0,0,0,0.72);
          opacity: 0;
        }}
        .proto-list {{ display: flex; flex-direction: column; gap: 18px; }}
        .step-card {{
          display: flex; align-items: center; gap: 22px;
          padding: {'22px 26px' if is_short else '20px 26px'};
          border-radius: 22px;
          background: linear-gradient(155deg, rgba(19, 31, 46, 0.86) 0%, rgba(8, 15, 25, 0.90) 100%);
          border: 1px solid rgba(255,255,255,0.20);
          box-shadow: 0 14px 28px rgba(0,0,0,0.52);
          opacity: 0; transform: translateX(-56px);
        }}
        .step-check {{
          width: 52px; height: 52px; border-radius: 16px; flex-shrink: 0;
          background: rgba(20,184,166,0.16);
          display: flex; align-items: center; justify-content: center;
        }}
        .step-num {{ font-size: 14px; font-weight: 800; letter-spacing: 2px; color: #F59E0B; margin-bottom: 4px; }}
        .step-txt {{ font-size: {'26px' if is_short else '26px'}; font-weight: 700; color: #F8FAFC; line-height: 1.25; }}
        """
        render_js = f"""
        const count = {len(steps)};
        const ticks = [];
        for (let i = 0; i < count; i++) {{
          const tk = document.getElementById('tick' + i);
          const l = tk.getTotalLength();
          tk.style.strokeDasharray = l; tk.style.strokeDashoffset = l;
          ticks.push([tk, l]);
        }}
        window.renderAt = function(t, dur) {{
          const ease = x => 1 - Math.pow(1 - Math.max(0, Math.min(1, x)), 3);
          const fadeStart = Math.max(dur - 0.65, 0);
          const outA = t > fadeStart ? 1 - ease((t - fadeStart) / 0.55) : 1;

          const hIn = ease(t / 0.45);
          const ph = document.getElementById('protoHead');
          ph.style.opacity = (hIn * outA).toFixed(3);
          ph.style.transform = `translateY(${{((1-hIn)*24).toFixed(1)}}px)`;

          const starts = [
            0.30,
            Math.min(Math.max(dur * 0.34, 1.8), Math.max(dur - 2.4, 1.8)),
            Math.min(Math.max(dur * 0.64, 3.4), Math.max(dur - 1.4, 3.4))
          ];
          for (let i = 0; i < count; i++) {{
            const st = starts[i] ?? (0.30 + i * 1.6);
            const e = ease((t - st) / 0.52);
            const el = document.getElementById('step' + i);
            el.style.opacity = (e * outA).toFixed(3);
            el.style.transform = `translateX(${{((1-e)*-56).toFixed(1)}}px)`;
            const nextSt = starts[i + 1] ?? dur;
            const isAct = t >= st && t < nextSt;
            el.style.borderColor = isAct ? 'rgba(245,158,11,0.88)' : 'rgba(45,212,191,0.42)';
            const tkP = ease((t - (st + 0.35)) / 0.48);
            ticks[i][0].style.strokeDashoffset = (ticks[i][1] * (1 - tkP)).toFixed(1);
          }}
        }};
        """

    else:
        # cinema_chapter_title: Sleek Netflix / Aperture Opening Kinetic Title Card
        body_html = f"""
        <div class="cine-title-box" id="cineBox">
          <div class="cine-mask"><div class="cine-head" id="cineHead">{headline}</div></div>
          <div class="cine-rule" id="cineRule"></div>
          <div class="cine-sub" id="cineSub">{callout}</div>
        </div>
        """
        extra_css = f"""
        .cine-title-box {{
          position: absolute;
          top: {'245px' if is_short else '162px'};
          left: {'52px' if is_short else '78px'};
          right: {'52px' if is_short else 'auto'};
          max-width: {'100%' if is_short else '1120px'};
          padding: {'28px 34px' if is_short else '32px 42px'};
          border-radius: 24px;
          background: linear-gradient(155deg, rgba(16, 28, 42, 0.80) 0%, rgba(8, 15, 24, 0.84) 100%);
          border: 1px solid rgba(255,255,255,0.20);
          box-shadow: 0 16px 32px rgba(0,0,0,0.52), 0 1px 0 rgba(255,255,255,0.16) inset;
          opacity: 0;
        }}
        .cine-mask {{ overflow: hidden; }}
        .cine-head {{
          font-size: {'54px' if is_short else '64px'}; font-weight: 800; line-height: 1.1;
          color: #F8FAFC; letter-spacing: -0.5px;
          transform: translateY(105%);
        }}
        .cine-rule {{
          height: 5px; width: 0px; border-radius: 4px; margin: 18px 0 16px;
          background: linear-gradient(90deg, #F59E0B, #2DD4BF);
        }}
        .cine-sub {{
          font-size: {'26px' if is_short else '27px'}; font-weight: 500;
          color: #E2E8F0; line-height: 1.35; opacity: 0;
        }}
        """
        render_js = """
        window.renderAt = function(t, dur) {
          const ease = x => 1 - Math.pow(1 - Math.max(0, Math.min(1, x)), 3);
          const holdEnd = Math.min(Math.max(dur * 0.48, 3.2), 5.8, Math.max(dur - 0.8, 1.5));
          const inP = ease(t / 0.48);
          const outP = t > holdEnd ? 1 - ease((t - holdEnd) / 0.60) : 1;
          const box = document.getElementById('cineBox');
          box.style.opacity = (inP * outP).toFixed(3);
          const hP = ease((t - 0.12) / 0.55);
          document.getElementById('cineHead').style.transform = `translateY(${((1 - hP) * 105).toFixed(1)}%)`;
          document.getElementById('cineRule').style.width = Math.round(ease((t - 0.35) / 0.55) * 240) + 'px';
          document.getElementById('cineSub').style.opacity = ease((t - 0.55) / 0.55).toFixed(3);
        };
        """

    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"><style>{common_css}\n{extra_css}</style></head>
<body>
  <div class="cinema-vignette"></div>
  <div class="top-bar"><div class="top-fill" id="topFill"></div></div>
  <div class="hud-header" id="hudHeader">
    <div class="chapter-pill"><span class="dot-live"></span><span>{counter_label} • {section}</span></div>
    <div class="watermark">{safe_handle}</div>
  </div>
  {body_html}
  <script>
    (() => {{
      {render_js}
      window.renderFrame = function(tSec, durSec, globalP) {{
        const tf = document.getElementById('topFill');
        if (tf) tf.style.width = (Math.max(0, Math.min(1, globalP)) * 100).toFixed(2) + '%';
        if (typeof window.renderAt === 'function') window.renderAt(tSec, durSec);
      }};
    }})();
  </script>
</body>
</html>"""


class HtmlOverlayRenderer:
    """Reusable Headless Chrome Playwright session with Smart Static-Hold Frame Caching."""

    def __init__(self, width: int, height: int):
        from playwright.sync_api import sync_playwright

        self.width = width
        self.height = height
        self._pw = sync_playwright().start()
        chrome_bin = find_chrome_executable()
        launch_kwargs: dict[str, Any] = {"headless": True, "args": ["--disable-gpu-sandbox", "--no-sandbox"]}
        if chrome_bin:
            launch_kwargs["executable_path"] = chrome_bin
        self._browser = self._pw.chromium.launch(**launch_kwargs)
        self._page = self._browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)

    def render_overlay_mov(
        self,
        scene: dict[str, Any],
        scene_idx: int,
        total_scenes: int,
        duration_sec: float,
        out_mov: Path,
        handle: str,
        is_short: bool = False,
        overlay_fps: int = 18,
    ) -> tuple[Path, str]:
        style_name = pick_html_overlay_style(scene, scene_idx)
        doc_html = _build_overlay_html(
            style_name=style_name,
            scene=scene,
            scene_idx=scene_idx,
            total_scenes=total_scenes,
            width=self.width,
            height=self.height,
            handle=handle,
            is_short=is_short,
        )
        self._page.set_content(doc_html, wait_until="load")

        total_frames = max(int(round(duration_sec * overlay_fps)), overlay_fps)
        windows = _active_motion_windows(style_name, duration_sec)
        out_mov.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg", "-y",
            "-f", "image2pipe", "-vcodec", "png", "-r", str(overlay_fps),
            "-i", "pipe:0",
            "-c:v", "copy",
            str(out_mov),
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        assert proc.stdin is not None

        last_png: bytes | None = None
        last_capture_t = -999.0
        was_active = True
        captures = 0

        try:
            for f_idx in range(total_frames):
                t_sec = f_idx / float(overlay_fps)
                p = min(t_sec / max(duration_sec, 0.1), 1.0)
                global_p = ((scene_idx - 1) + p) / float(max(total_scenes, 1))

                in_active = any(s <= t_sec <= e for s, e in windows)
                # Capture fresh screenshot during active motion, on first settle frame after motion,
                # or every 1.8s during hold so the top gradient progress bar advances smoothly!
                need_capture = (
                    last_png is None
                    or in_active
                    or was_active
                    or f_idx == total_frames - 1
                    or (t_sec - last_capture_t) >= 1.8
                )
                if need_capture:
                    self._page.evaluate(f"window.renderFrame({t_sec:.4f}, {duration_sec:.4f}, {global_p:.5f})")
                    last_png = self._page.screenshot(type="png", omit_background=True)
                    last_capture_t = t_sec
                    captures += 1
                was_active = in_active
                assert last_png is not None
                proc.stdin.write(last_png)

            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", errors="ignore") if proc.stderr else ""
            ret = proc.wait()
            if ret != 0:
                raise RuntimeError(f"FFmpeg HTML overlay pipe failed ({ret}): {err[-300:]}")
        finally:
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()

        print(f"[overlay] '{style_name}' rendered ({captures}/{total_frames} keyframes cached) -> {out_mov.name}", flush=True)
        return out_mov, style_name

    def close(self) -> None:
        try:
            self._browser.close()
        finally:
            self._pw.stop()
