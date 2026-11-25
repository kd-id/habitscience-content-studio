"""True 30fps Programmatic Motion Graphics Engine (Python + NumPy + OpenCV + Pillow -> FFmpeg pipe).

Generates genuine 30fps moving vector/data/neural motion graphics—NOT static slideshows—
completely free locally and on GitHub Actions Ubuntu.
"""

from __future__ import annotations

import math
import random
import re
import subprocess
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.config_loader import resolve_font_path


def _hex_to_rgb(hex_color: str, fallback: tuple[int, int, int] = (9, 19, 27)) -> tuple[int, int, int]:
    h = hex_color.strip().lstrip("#")
    if len(h) == 6:
        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except ValueError:
            return fallback
    return fallback


def _ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def _ease_out_back(t: float) -> float:
    t = max(0.0, min(1.0, t))
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * ((t - 1.0) ** 3) + c1 * ((t - 1.0) ** 2)


def _ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _load_font(preferred: str | None, size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    fp = resolve_font_path(preferred, bold=bold)
    if fp:
        try:
            return ImageFont.truetype(fp, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def _make_text_sprite(
    text: str,
    font: ImageFont.ImageFont,
    color: tuple[int, int, int],
    max_width: int,
    max_lines: int = 3,
    align: str = "left",
    shadow: bool = True,
    line_spacing: float = 1.18,
) -> np.ndarray:
    """Render crisp TrueType multi-line text once into an RGBA numpy sprite."""
    dummy = Image.new("RGBA", (10, 10))
    draw = ImageDraw.Draw(dummy)
    words = text.split()
    lines: list[str] = []
    if words:
        cur = words[0]
        for w in words[1:]:
            cand = f"{cur} {w}"
            bb = draw.textbbox((0, 0), cand, font=font)
            if (bb[2] - bb[0]) <= max_width:
                cur = cand
            else:
                lines.append(cur)
                cur = w
                if len(lines) >= max_lines - 1:
                    break
        rem = sum(len(l.split()) for l in lines)
        tail = " ".join(words[rem:])
        while tail:
            bb = draw.textbbox((0, 0), tail, font=font)
            if (bb[2] - bb[0]) <= max_width:
                break
            parts = tail.split()
            if len(parts) <= 1:
                tail = tail[:-4] + "..." if len(tail) > 4 else tail
                break
            tail = " ".join(parts[:-1]) + "..."
        if tail and len(lines) < max_lines:
            lines.append(tail)

    if not lines:
        return np.zeros((4, 4, 4), dtype=np.uint8)

    line_boxes = [draw.textbbox((0, 0), l, font=font) for l in lines]
    widths = [b[2] - b[0] for b in line_boxes]
    heights = [b[3] - b[1] for b in line_boxes]
    base_h = max(heights) if heights else 24
    step_y = int(base_h * line_spacing)
    pad = 12
    sprite_w = max(widths) + pad * 2
    sprite_h = step_y * (len(lines) - 1) + base_h + pad * 2 + 6

    img = Image.new("RGBA", (sprite_w, sprite_h), (0, 0, 0, 0))
    idraw = ImageDraw.Draw(img)
    y = pad
    for line, lw, bb in zip(lines, widths, line_boxes):
        if align == "center":
            x = (sprite_w - lw) // 2
        elif align == "right":
            x = sprite_w - pad - lw
        else:
            x = pad
        if shadow:
            idraw.text((x + 3, y + 3 - bb[1]), line, font=font, fill=(0, 0, 0, 185))
        idraw.text((x, y - bb[1]), line, font=font, fill=(*color, 255))
        y += step_y

    return np.array(img, dtype=np.uint8)


def _make_pill_sprite(
    text: str,
    font: ImageFont.ImageFont,
    bg_rgba: tuple[int, int, int, int],
    fg_rgb: tuple[int, int, int],
    pad_x: int = 24,
    pad_y: int = 10,
) -> np.ndarray:
    dummy = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(dummy)
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    w = tw + pad_x * 2 + 4
    h = th + pad_y * 2 + 4
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    idraw = ImageDraw.Draw(img)
    idraw.rounded_rectangle((2, 2, w - 2, h - 2), radius=(h - 4) // 2, fill=bg_rgba)
    idraw.text((pad_x + 2, pad_y + 2 - bb[1]), text, font=font, fill=(*fg_rgb, 255))
    return np.array(img, dtype=np.uint8)


def _blit_rgba(frame_rgb: np.ndarray, sprite_rgba: np.ndarray, x: int, y: int, alpha_mult: float = 1.0) -> None:
    if alpha_mult <= 0.01 or sprite_rgba.size == 0:
        return
    fh, fw = frame_rgb.shape[:2]
    sh, sw = sprite_rgba.shape[:2]
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + sw, fw), min(y + sh, fh)
    if x1 <= x0 or y1 <= y0:
        return
    sx0, sy0 = x0 - x, y0 - y
    sx1, sy1 = sx0 + (x1 - x0), sy0 + (y1 - y0)

    sub_sprite = sprite_rgba[sy0:sy1, sx0:sx1]
    alpha = (sub_sprite[:, :, 3:4].astype(np.float32) / 255.0) * float(alpha_mult)
    dst = frame_rgb[y0:y1, x0:x1].astype(np.float32)
    src = sub_sprite[:, :, :3].astype(np.float32)
    frame_rgb[y0:y1, x0:x1] = np.clip(src * alpha + dst * (1.0 - alpha), 0, 255).astype(np.uint8)


def _build_base_canvas(w: int, h: int, bg_dark: tuple[int, int, int], bg_card: tuple[int, int, int], primary: tuple[int, int, int], accent: tuple[int, int, int], seed: int) -> np.ndarray:
    y_grad = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    c0 = np.array(bg_dark, dtype=np.float32)[None, None, :]
    c1 = np.array(bg_card, dtype=np.float32)[None, None, :]
    canvas = (c0 * (1.0 - y_grad) + c1 * y_grad)

    # Soft ambient radial glow gradients
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx1 = w * (0.78 if seed % 2 == 0 else 0.22)
    cy1 = h * 0.26
    r1 = min(w, h) * 0.58
    d1 = np.exp(-((xx - cx1) ** 2 + (yy - cy1) ** 2) / (2.0 * (r1 * 0.55) ** 2))[:, :, None]

    cx2 = w * (0.20 if seed % 2 == 0 else 0.80)
    cy2 = h * 0.72
    r2 = min(w, h) * 0.52
    d2 = np.exp(-((xx - cx2) ** 2 + (yy - cy2) ** 2) / (2.0 * (r2 * 0.55) ** 2))[:, :, None]

    canvas = canvas + d1 * np.array(primary, dtype=np.float32) * 0.22 + d2 * np.array(accent, dtype=np.float32) * 0.14
    return np.clip(canvas, 0, 255).astype(np.uint8)


def _pick_motion_template(scene: dict[str, Any], scene_idx: int) -> str:
    explicit = str(scene.get("motion_type") or "").strip().lower()
    if explicit in ("stat_counter", "dopamine_wave", "neural_network", "protocol_steps", "orbital_rings"):
        return explicit

    combined = f"{scene.get('section', '')} {scene.get('visual_headline', '')} {scene.get('narration', '')}".lower()
    if any(k in combined for k in ("protocol", "step", "shift", "anchor", "shrink", "three", "3-step")):
        return "protocol_steps"
    if any(k in combined for k in ("dopamine", "wave", "cycle", "ultradian", "spike", "baseline", "crash", "boring")):
        return "dopamine_wave"
    if any(k in combined for k in ("neuron", "neural", "myelin", "highway", "brain", "rewir", "cortex", "residue")):
        return "neural_network"
    if re.search(r"\b\d+\b", combined) or any(k in combined for k in ("myth", "lie", "days", "minutes", "21", "66", "23")):
        return "stat_counter"
    cycle = ["stat_counter", "neural_network", "dopamine_wave", "protocol_steps", "orbital_rings"]
    return cycle[(scene_idx - 1) % len(cycle)]


def _extract_metrics_for_counter(scene: dict[str, Any]) -> tuple[str, str, int, int, str]:
    text = f"{scene.get('visual_headline', '')} {scene.get('narration', '')}"
    nums = [int(n) for n in re.findall(r"\b(\d{1,3})\b", text)]
    low = text.lower()
    unit = "DAYS" if "day" in low else ("MIN" if "min" in low else ("%" if "%" in text else "X"))
    if len(nums) >= 2 and nums[0] != nums[1]:
        return f"{nums[0]} {unit}", f"{nums[1]} {unit}", nums[0], nums[1], unit
    if len(nums) == 1:
        target = nums[0]
        return f"0 {unit}", f"{target} {unit}", 0, target, unit
    if "twenty-one" in low or "21" in low:
        return "21 DAYS", "66 DAYS", 21, 66, "DAYS"
    if "twenty-three" in low:
        return "15 MIN", "23 MIN", 15, 23, "MIN"
    return "0%", "100%", 0, 100, "%"


def _extract_steps(scene: dict[str, Any]) -> list[str]:
    bullets = [str(b).lstrip("0123456789.-) ").strip() for b in (scene.get("bullet_points") or []) if str(b).strip()]
    if len(bullets) >= 2:
        return bullets[:3]
    callout = str(scene.get("on_screen_callout") or "").strip()
    if "," in callout and len(callout.split(",")) >= 3:
        return [p.strip().capitalize() for p in callout.split(",")[:3]]
    # Extract clean short clauses from narration
    sentences = [s.strip() for s in re.split(r"[.;]", str(scene.get("narration") or "")) if len(s.strip()) > 12]
    if len(sentences) >= 3:
        return [s[:54].rstrip() + ("..." if len(s) > 54 else "") for s in sentences[:3]]
    return [
        "Anchor to an existing morning cue",
        "Shrink the starting friction to 2 minutes",
        "Protect consistency across the full cycle",
    ]


def render_motion_scene_segment(
    scene: dict[str, Any],
    scene_idx: int,
    total_scenes: int,
    duration_sec: float,
    width: int,
    height: int,
    fps: int,
    out_mp4: Path,
    config: dict[str, Any],
    is_short: bool = False,
) -> Path:
    """Render a true 30fps animated motion graphics MP4 segment by piping raw RGB frames to FFmpeg."""
    branding = config.get("branding", {})
    bg_dark = _hex_to_rgb(branding.get("bg_dark", "#09131B"))
    bg_card = _hex_to_rgb(branding.get("bg_card", "#11212E"))
    primary = _hex_to_rgb(branding.get("primary_color", "#14B8A6"))
    secondary = _hex_to_rgb(branding.get("secondary_color", "#38BDF8"))
    accent = _hex_to_rgb(branding.get("accent_color", "#F59E0B"))
    text_primary = _hex_to_rgb(branding.get("text_primary", "#F8FAFC"))
    text_muted = _hex_to_rgb(branding.get("text_muted", "#CBD5E1"))
    handle = str(branding.get("watermark_text", "@habitsciencelab"))

    template = _pick_motion_template(scene, scene_idx)
    total_frames = max(int(round(duration_sec * fps)), fps)
    base_canvas = _build_base_canvas(width, height, bg_dark, bg_card, primary, accent, seed=scene_idx)

    # Pre-render static sprites once
    font_bold = branding.get("font_bold")
    font_reg = branding.get("font_regular")
    f_badge = _load_font(font_bold, 30 if is_short else 26, bold=True)
    f_head = _load_font(font_bold, 72 if is_short else 66, bold=True)
    f_sub = _load_font(font_reg, 36 if is_short else 32, bold=False)
    f_meta = _load_font(font_bold, 28 if is_short else 24, bold=True)
    f_big = _load_font(font_bold, 128 if is_short else 148, bold=True)
    f_card = _load_font(font_bold, 36 if is_short else 34, bold=True)

    section_txt = str(scene.get("badge") or scene.get("section") or f"{scene_idx:02d}/{total_scenes:02d}").upper()
    if not is_short:
        section_txt = f"{scene_idx:02d}/{total_scenes:02d}  •  {section_txt}"
    badge_sprite = _make_pill_sprite(section_txt, f_badge, bg_rgba=(*primary, 235), fg_rgb=(9, 19, 27))
    handle_sprite = _make_text_sprite(handle, f_meta, text_muted, max_width=400, max_lines=1, align="right")

    headline = str(scene.get("visual_headline") or "HabitScience Lab")
    head_max_w = int(width * (0.86 if is_short else 0.78))
    head_sprite = _make_text_sprite(headline, f_head, text_primary, max_width=head_max_w, max_lines=2, align="center" if is_short else "left")

    callout = str(scene.get("on_screen_callout") or "").strip()
    callout_sprite = (
        _make_text_sprite(callout, f_sub, text_muted, max_width=head_max_w, max_lines=2, align="center" if is_short else "left")
        if callout
        else np.zeros((4, 4, 4), dtype=np.uint8)
    )

    # Template-specific precomputations
    rng = random.Random(scene_idx * 997 + (17 if is_short else 3))
    particles = [
        {
            "x": rng.uniform(0, width),
            "y": rng.uniform(0, height),
            "vx": rng.uniform(-16, 16),
            "vy": rng.uniform(-22, -6),
            "r": rng.randint(2, 5),
            "col": primary if rng.random() < 0.65 else accent,
        }
        for _ in range(38)
    ]

    # Neural nodes + edges for neural_network template
    zone_top = int(height * (0.34 if is_short else 0.30))
    zone_bot = int(height * (0.72 if is_short else 0.78))
    zone_left = int(width * 0.10)
    zone_right = int(width * 0.90)
    nodes = [
        {
            "bx": rng.uniform(zone_left, zone_right),
            "by": rng.uniform(zone_top, zone_bot),
            "amp": rng.uniform(8, 22),
            "freq": rng.uniform(0.5, 1.3),
            "phase": rng.uniform(0, math.tau),
            "r": rng.randint(7, 13),
        }
        for _ in range(20)
    ]
    edges: list[tuple[int, int, float]] = []
    for i in range(len(nodes)):
        dists = sorted(
            [(math.hypot(nodes[i]["bx"] - nodes[j]["bx"], nodes[i]["by"] - nodes[j]["by"]), j) for j in range(len(nodes)) if j != i]
        )
        for _, j in dists[:2]:
            if i < j:
                edges.append((i, j, rng.uniform(0.0, 1.0)))

    # Metric counter setup
    old_label, new_label, start_num, end_num, unit = _extract_metrics_for_counter(scene)
    old_num_sprite = _make_text_sprite(old_label, f_big, (226, 232, 240), max_width=int(width * 0.85), max_lines=1, align="center")
    counter_cache: dict[int, np.ndarray] = {}

    # Protocol steps setup
    steps_list = _extract_steps(scene)
    step_sprites = [
        _make_text_sprite(f"{i+1}. {st}", f_card, text_primary, max_width=int(width * (0.76 if is_short else 0.68)), max_lines=2, align="left")
        for i, st in enumerate(steps_list)
    ]

    # Launch FFmpeg pipe for raw RGB24 -> H.264 MP4
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "pipe:0",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-an",
        str(out_mp4),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert proc.stdin is not None

    fade_frames = max(int(fps * 0.35), 1)
    grid_step = 72 if not is_short else 60

    try:
        for f_idx in range(total_frames):
            t_sec = f_idx / float(fps)
            prog = f_idx / float(max(total_frames - 1, 1))
            frame = base_canvas.copy()

            # 1. Subtle drifting architectural dot grid (true parallax motion!)
            shift_x = int((t_sec * 12) % grid_step)
            shift_y = int((t_sec * 8) % grid_step)
            for gx in range(shift_x, width, grid_step):
                cv2.line(frame, (gx, 0), (gx, height), (28, 42, 56), 1)
            for gy in range(shift_y, height, grid_step):
                cv2.line(frame, (0, gy), (width, gy), (28, 42, 56), 1)

            # 2. Drifting atmospheric light particles
            for p in particles:
                px = int((p["x"] + p["vx"] * t_sec) % width)
                py = int((p["y"] + p["vy"] * t_sec) % height)
                cv2.circle(frame, (px, py), p["r"], p["col"], -1, lineType=cv2.LINE_AA)

            # 3. Template-specific True 30fps Motion Graphics!
            if template == "neural_network":
                cur_pts: list[tuple[int, int]] = []
                for nd in nodes:
                    nx = int(nd["bx"] + math.cos(t_sec * nd["freq"] + nd["phase"]) * nd["amp"])
                    ny = int(nd["by"] + math.sin(t_sec * nd["freq"] * 0.9 + nd["phase"]) * nd["amp"])
                    cur_pts.append((nx, ny))
                # Draw strengthening myelin pathways + traveling luminous impulses
                myelin_thick = 2 + int(3 * _ease_in_out(prog))
                for i, j, ph in edges:
                    p1, p2 = cur_pts[i], cur_pts[j]
                    edge_col = (
                        int(primary[0] * (1 - prog * 0.4) + accent[0] * (prog * 0.4)),
                        int(primary[1] * (1 - prog * 0.4) + accent[1] * (prog * 0.4)),
                        int(primary[2] * (1 - prog * 0.4) + accent[2] * (prog * 0.4)),
                    )
                    cv2.line(frame, p1, p2, (24, 68, 82), myelin_thick + 2, lineType=cv2.LINE_AA)
                    cv2.line(frame, p1, p2, edge_col, max(1, myelin_thick - 1), lineType=cv2.LINE_AA)
                    # Traveling synaptic light pulse along edge
                    u = (t_sec * 0.65 + ph) % 1.0
                    sx = int(p1[0] + (p2[0] - p1[0]) * u)
                    sy = int(p1[1] + (p2[1] - p1[1]) * u)
                    cv2.circle(frame, (sx, sy), 9, accent, -1, lineType=cv2.LINE_AA)
                    cv2.circle(frame, (sx, sy), 4, (255, 255, 255), -1, lineType=cv2.LINE_AA)
                for (nx, ny), nd in zip(cur_pts, nodes):
                    pulse_r = nd["r"] + int(3 * math.sin(t_sec * 3.0 + nd["phase"]))
                    cv2.circle(frame, (nx, ny), pulse_r + 4, (20, 90, 96), -1, lineType=cv2.LINE_AA)
                    cv2.circle(frame, (nx, ny), pulse_r, primary, -1, lineType=cv2.LINE_AA)
                    cv2.circle(frame, (nx, ny), max(3, pulse_r // 3), (248, 250, 252), -1, lineType=cv2.LINE_AA)

            elif template == "dopamine_wave":
                # Live-drawing dual neuroscience curve: erratic amber spike vs steady teal balance
                gx0, gx1 = int(width * 0.09), int(width * 0.91)
                gy_mid = int(height * (0.54 if is_short else 0.56))
                amp_y = int(height * (0.12 if is_short else 0.16))
                # Axes & equilibrium baseline
                cv2.line(frame, (gx0, gy_mid), (gx1, gy_mid), (75, 102, 124), 2, lineType=cv2.LINE_AA)
                draw_steps = max(2, int(180 * _ease_out_cubic(min(prog / 0.78, 1.0))))
                pts_amber: list[tuple[int, int]] = []
                pts_teal: list[tuple[int, int]] = []
                for k in range(draw_steps):
                    u = k / 179.0
                    x = int(gx0 + (gx1 - gx0) * u)
                    # Erratic dopamine spike + crash curve
                    spike = math.sin(u * 19.0 + t_sec * 1.4) * (1.0 - 0.55 * u) + 0.45 * math.sin(u * 37.0)
                    crash_bias = -0.35 * max(0.0, u - 0.35)
                    ya = int(gy_mid - (spike * 0.72 + crash_bias) * amp_y)
                    pts_amber.append((x, ya))
                    # Smooth harmonic focus flow wave
                    yt = int(gy_mid - (math.sin(u * 7.5 - t_sec * 1.6) * 0.38 + 0.18 * u) * amp_y)
                    pts_teal.append((x, yt))
                if len(pts_amber) >= 2:
                    cv2.polylines(frame, [np.array(pts_amber, dtype=np.int32)], False, accent, 5, lineType=cv2.LINE_AA)
                    cv2.circle(frame, pts_amber[-1], 11, accent, -1, lineType=cv2.LINE_AA)
                    cv2.circle(frame, pts_amber[-1], 5, (255, 255, 255), -1, lineType=cv2.LINE_AA)
                if len(pts_teal) >= 2:
                    cv2.polylines(frame, [np.array(pts_teal, dtype=np.int32)], False, primary, 6, lineType=cv2.LINE_AA)
                    cv2.circle(frame, pts_teal[-1], 12, primary, -1, lineType=cv2.LINE_AA)
                    cv2.circle(frame, pts_teal[-1], 5, (255, 255, 255), -1, lineType=cv2.LINE_AA)

            elif template == "stat_counter":
                # Animated rotating glowing orbital ring + myth strike-through -> live animated number count!
                cx, cy = width // 2, int(height * (0.54 if is_short else 0.56))
                rad = int(min(width, height) * (0.28 if is_short else 0.25))
                rot = t_sec * 32.0
                cv2.ellipse(frame, (cx, cy), (rad + 22, rad + 22), rot, 0, 260, (32, 68, 86), 3, lineType=cv2.LINE_AA)
                sweep = int(360 * _ease_out_cubic(min(prog / 0.82, 1.0)))
                cv2.ellipse(frame, (cx, cy), (rad, rad), -90, 0, sweep, primary, 10, lineType=cv2.LINE_AA)
                cv2.ellipse(frame, (cx, cy), (rad - 18, rad - 18), -rot * 0.7, 0, 140, accent, 4, lineType=cv2.LINE_AA)

                if prog < 0.34 and start_num != end_num:
                    sc = _ease_out_back(min(prog / 0.16, 1.0))
                    ox = cx - old_num_sprite.shape[1] // 2
                    oy = cy - old_num_sprite.shape[0] // 2
                    _blit_rgba(frame, old_num_sprite, ox, oy, alpha_mult=min(sc, 1.0))
                    # Animated glowing strike-through bar
                    if prog > 0.18:
                        st_p = _ease_out_cubic((prog - 0.18) / 0.14)
                        lx0 = cx - old_num_sprite.shape[1] // 2
                        lx1 = int(lx0 + old_num_sprite.shape[1] * st_p)
                        cv2.line(frame, (lx0, cy), (lx1, cy), (239, 68, 68), 10, lineType=cv2.LINE_AA)
                else:
                    count_p = _ease_out_cubic(min(max((prog - 0.34) / 0.42, 0.0), 1.0))
                    val = int(round(start_num + (end_num - start_num) * count_p))
                    if val not in counter_cache:
                        lbl = f"{val} {unit}" if unit != "%" else f"{val}%"
                        counter_cache[val] = _make_text_sprite(lbl, f_big, accent, max_width=int(width * 0.85), max_lines=1, align="center")
                    sp = counter_cache[val]
                    _blit_rgba(frame, sp, cx - sp.shape[1] // 2, cy - sp.shape[0] // 2, alpha_mult=1.0)

            elif template == "protocol_steps":
                # Animated vertical spine + 3 sequential spring-sliding glass cards synced across the scene!
                card_w = int(width * (0.84 if is_short else 0.78))
                card_x = (width - card_w) // 2
                card_h = 148 if is_short else 118
                gap = 34 if is_short else 26
                start_y = int(height * (0.38 if is_short else 0.34))

                # Drawing spine line on left
                spine_x = card_x - 28
                spine_len = int((card_h + gap) * (len(step_sprites) - 1) + card_h)
                cur_spine = int(spine_len * _ease_out_cubic(min(prog / 0.72, 1.0)))
                cv2.line(frame, (spine_x, start_y), (spine_x, start_y + cur_spine), primary, 5, lineType=cv2.LINE_AA)

                for s_i, sp in enumerate(step_sprites):
                    appear_at = s_i * 0.24 + 0.04
                    if prog < appear_at:
                        continue
                    lp = _ease_out_cubic(min((prog - appear_at) / 0.16, 1.0))
                    slide_dx = int((1.0 - lp) * 110)
                    cy0 = start_y + s_i * (card_h + gap)
                    cx0 = card_x + slide_dx
                    is_active = (prog >= appear_at) and (s_i == len(step_sprites) - 1 or prog < (s_i + 1) * 0.24 + 0.04)
                    # Fast ROI card background blend (zero full-frame copy!)
                    rx0, ry0 = max(cx0, 0), max(cy0, 0)
                    rx1, ry1 = min(cx0 + card_w, width), min(cy0 + card_h, height)
                    if rx1 > rx0 and ry1 > ry0:
                        w_a = 0.82 * lp
                        roi = frame[ry0:ry1, rx0:rx1]
                        card_bg = np.full_like(roi, (18, 32, 46))
                        cv2.addWeighted(card_bg, w_a, roi, 1.0 - w_a, 0, roi)
                    border_col = accent if is_active else primary
                    cv2.rectangle(frame, (cx0, cy0), (cx0 + card_w, cy0 + card_h), border_col, 3 if is_active else 2, lineType=cv2.LINE_AA)
                    # Node pulse on spine
                    cv2.circle(frame, (spine_x, cy0 + card_h // 2), 11 if is_active else 8, border_col, -1, lineType=cv2.LINE_AA)
                    _blit_rgba(frame, sp, cx0 + 28, cy0 + (card_h - sp.shape[0]) // 2, alpha_mult=lp)

            else:
                # orbital_rings: Animated glowing focus rings + 7-day luminous milestone arc
                cx, cy = width // 2, int(height * (0.54 if is_short else 0.56))
                base_r = int(min(width, height) * 0.26)
                for ring_i, (rm, spd, col) in enumerate([(1.0, 22, primary), (0.76, -34, secondary), (0.52, 46, accent)]):
                    r = int(base_r * rm)
                    ang = t_sec * spd + ring_i * 45
                    cv2.ellipse(frame, (cx, cy), (r, r), ang, 0, 270, col, 6 - ring_i, lineType=cv2.LINE_AA)
                # 7 animated milestone nodes lighting up sequentially
                lit_nodes = min(7, 1 + int(prog * 7.5))
                for d_i in range(7):
                    theta = math.radians(-150 + d_i * (300 / 6.0))
                    nx = int(cx + math.cos(theta) * (base_r + 48))
                    ny = int(cy + math.sin(theta) * (base_r + 48))
                    is_lit = d_i < lit_nodes
                    cv2.circle(frame, (nx, ny), 16 if is_lit else 10, accent if is_lit else (52, 74, 92), -1, lineType=cv2.LINE_AA)
                    if is_lit:
                        cv2.circle(frame, (nx, ny), 7, (255, 255, 255), -1, lineType=cv2.LINE_AA)

            # 4. Top live continuous progress bar + crisp chapter badge + handle
            top_h = 6 if not is_short else 8
            cv2.rectangle(frame, (0, 0), (width, top_h), (24, 38, 52), -1)
            global_prog = ((scene_idx - 1) + prog) / float(max(total_scenes, 1))
            cv2.rectangle(frame, (0, 0), (int(width * global_prog), top_h), primary, -1)

            in_alpha = _ease_out_cubic(min(t_sec / 0.45, 1.0))
            in_dy = int((1.0 - in_alpha) * 24)
            if is_short:
                _blit_rgba(frame, badge_sprite, (width - badge_sprite.shape[1]) // 2, 168 + in_dy, alpha_mult=in_alpha)
                _blit_rgba(frame, head_sprite, (width - head_sprite.shape[1]) // 2, 248 + in_dy, alpha_mult=in_alpha)
                _blit_rgba(frame, handle_sprite, (width - handle_sprite.shape[1]) // 2, 92, alpha_mult=0.85)
            else:
                _blit_rgba(frame, badge_sprite, 68, 42 + in_dy, alpha_mult=in_alpha)
                _blit_rgba(frame, head_sprite, 68, 114 + in_dy, alpha_mult=in_alpha)
                if callout_sprite.shape[0] > 8:
                    _blit_rgba(frame, callout_sprite, 68, 118 + head_sprite.shape[0] + in_dy, alpha_mult=in_alpha * 0.9)
                _blit_rgba(frame, handle_sprite, width - 68 - handle_sprite.shape[1], 48, alpha_mult=0.85)

            # 5. Smooth fade-in and fade-out
            fade = 1.0
            if f_idx < fade_frames:
                fade = f_idx / float(fade_frames)
            elif f_idx > total_frames - fade_frames:
                fade = max(0.0, (total_frames - f_idx) / float(fade_frames))
            if fade < 0.999:
                frame = (frame.astype(np.float32) * fade).astype(np.uint8)

            proc.stdin.write(frame.tobytes())

        proc.stdin.close()
        stderr_out = proc.stderr.read().decode("utf-8", errors="ignore") if proc.stderr else ""
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"FFmpeg motion render failed (code {ret}): {stderr_out[-400:]}")
    finally:
        if proc.stdin and not proc.stdin.closed:
            proc.stdin.close()

    return out_mp4
