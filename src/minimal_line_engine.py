"""Studio v7 — Dark Minimalist Mono-Line Stick-Figure Storytelling Engine.

Inspired by the high-retention minimalist dark storytelling aesthetic:
- Matte obsidian charcoal canvas (#0E0E0E) with generous negative space
- 2x supersampled anti-aliased thin-line white (#EFEFEF) + soft pale yellow (#EAE86A) vector animation at 30fps
- Progressive stroke line-drawing, breathing stick figures, typing bubbles, tangled scribbles,
  stacking load boxes, 5-day habit pills, flowing yellow hourglass sand, minimal doorway arch,
  crescent moon stillness, and sequential dark outline research/quote cards
- Word-synced ALL-CAPS monospace subtitles with wide tracking & soft yellow keyword highlights
- Subtle spaced-out bottom brand watermark (h a b i t s a i n s)
- 100% FREE, zero paid APIs, blazing fast (~20-35s for a full 60s 1080x1920 30fps video)
"""

from __future__ import annotations

import asyncio
import math
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Exact palette discipline
BG_RGB = (14, 14, 14)          # #0E0E0E matte obsidian charcoal
CARD_BG = (20, 20, 20)         # #141414 subtle dark card fill
WHITE = (239, 239, 239)        # #EFEFEF crisp line & text white
YELLOW = (234, 232, 106)       # #EAE86A signature soft pale lemon yellow
GRAY_MID = (118, 118, 118)     # #767676 muted captions & watermark
GRAY_DIM = (62, 62, 62)        # #3E3E3E inactive rings & dividers
CARD_BORDER = (165, 165, 165)  # #A5A5A5 crisp 1.5px card outline


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def _ease_out_cubic(x: float) -> float:
    t = _clamp01(x)
    return 1.0 - (1.0 - t) ** 3


def _ease_out_back(x: float) -> float:
    t = _clamp01(x)
    c1 = 1.45
    c3 = c1 + 1.0
    return 1.0 + c3 * ((t - 1.0) ** 3) + c1 * ((t - 1.0) ** 2)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_color(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    u = _clamp01(t)
    return (
        int(round(c1[0] + (c2[0] - c1[0]) * u)),
        int(round(c1[1] + (c2[1] - c1[1]) * u)),
        int(round(c1[2] + (c2[2] - c1[2]) * u)),
    )


def _find_font(kind: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates_map = {
        "mono": [
            r"C:\Windows\Fonts\CascadiaMono.ttf",
            r"C:\Windows\Fonts\consola.ttf",
            r"C:\Windows\Fonts\cour.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        ],
        "mono_bold": [
            r"C:\Windows\Fonts\consolab.ttf",
            r"C:\Windows\Fonts\CascadiaMono.ttf",
            r"C:\Windows\Fonts\courbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
        ],
        "sans_bold": [
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ],
        "sans": [
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ],
    }
    for path in candidates_map.get(kind, candidates_map["mono"]):
        if Path(path).is_file():
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Anti-aliased 2x Supersampled Progressive Vector Drawing Primitives
# ---------------------------------------------------------------------------

def _sample_cubic_bezier(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    steps: int = 32,
) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(steps + 1):
        t = i / float(steps)
        mt = 1.0 - t
        x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


def _sample_circle(cx: float, cy: float, r: float, steps: int = 64, start_deg: float = -90.0, span_deg: float = 360.0) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(steps + 1):
        ang = math.radians(start_deg + span_deg * (i / float(steps)))
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def _sample_rounded_rect_path(x0: float, y0: float, x1: float, y1: float, r: float, steps_corner: int = 10) -> list[tuple[float, float]]:
    r = min(r, (x1 - x0) / 2.0, (y1 - y0) / 2.0)
    pts: list[tuple[float, float]] = []
    corners = [
        (x1 - r, y0 + r, -90.0, 0.0),
        (x1 - r, y1 - r, 0.0, 90.0),
        (x0 + r, y1 - r, 90.0, 180.0),
        (x0 + r, y0 + r, 180.0, 270.0),
    ]
    for cx, cy, a0, a1 in corners:
        for i in range(steps_corner + 1):
            ang = math.radians(a0 + (a1 - a0) * (i / float(steps_corner)))
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    pts.append(pts[0])
    return pts


def _draw_progressive_path(
    draw: ImageDraw.ImageDraw,
    pts: list[tuple[float, float]],
    progress: float,
    color: tuple[int, int, int],
    width: int,
) -> None:
    """Draw a smooth polyline progressively from 0.0 -> 1.0 with rounded caps (SVG stroke-dashoffset style)."""
    p = _clamp01(progress)
    if p <= 0.001 or len(pts) < 2:
        return

    seg_lens = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    total_len = sum(seg_lens)
    if total_len <= 1e-4:
        return

    target_len = total_len * p
    drawn: list[tuple[float, float]] = [pts[0]]
    acc = 0.0
    for i, sl in enumerate(seg_lens):
        if acc + sl <= target_len:
            drawn.append(pts[i + 1])
            acc += sl
        else:
            rem = max(target_len - acc, 0.0)
            frac = rem / max(sl, 1e-6)
            nx = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * frac
            ny = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * frac
            drawn.append((nx, ny))
            break

    if len(drawn) >= 2:
        draw.line(drawn, fill=color, width=width, joint="curve")
        rad = width / 2.0
        for px, py in (drawn[0], drawn[-1]):
            draw.ellipse([px - rad, py - rad, px + rad, py + rad], fill=color)


def _draw_tracked_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: float,
    y: float,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    color: tuple[int, int, int],
    letter_spacing: float = 0.0,
    anchor_center: bool = False,
) -> float:
    """Draw cleanly tracked (wide letter-spaced) text, returning total rendered width."""
    if not text:
        return 0.0
    widths: list[float] = []
    for ch in text:
        bb = draw.textbbox((0, 0), ch, font=font)
        adv = draw.textlength(ch, font=font) if hasattr(draw, "textlength") else (bb[2] - bb[0])
        widths.append(float(adv))
    total_w = sum(widths) + letter_spacing * max(len(text) - 1, 0)
    cx = x - total_w / 2.0 if anchor_center else x
    for ch, w in zip(text, widths):
        draw.text((cx, y), ch, font=font, fill=color)
        cx += w + letter_spacing
    return total_w


# ---------------------------------------------------------------------------
# 8 Distinct Animated Thin-Line Minimalist Scenes (Drawn at 2x Supersampling)
# ---------------------------------------------------------------------------

def _scene_sitting_overwhelmed(
    draw: ImageDraw.ImageDraw,
    t: float,
    dur: float,
    cx: float,
    cy: float,
    s: float,
    meta: dict[str, Any],
) -> None:
    """Exact homage to sample_p2 f_00/f_01: sitting stick-figure + typing bubble + yellow tangled scribble."""
    lw = max(int(round(5.0 * s)), 3)
    bob = math.sin(t * 2.4) * 3.0 * s

    # 1. Ground line expands outward from center
    g_p = _ease_out_cubic(t / 0.55)
    g_half = 330 * s * g_p
    gy = cy + 165 * s
    if g_p > 0.01:
        _draw_progressive_path(draw, [(cx - g_half, gy), (cx + g_half, gy)], 1.0, WHITE, lw)

    # 2. Sitting stick figure (profile, facing right)
    fig_x = cx - 125 * s
    # Legs (vertical shin + horizontal thigh)
    leg_pts = [
        (fig_x + 64 * s, gy),
        (fig_x + 64 * s, gy - 78 * s),
        (fig_x - 8 * s, gy - 84 * s),
        (fig_x - 12 * s, gy - 168 * s + bob),
    ]
    _draw_progressive_path(draw, leg_pts, _ease_out_cubic((t - 0.15) / 0.65), WHITE, lw)

    # Arm reaching slightly forward over lap
    arm_pts = [
        (fig_x - 10 * s, gy - 146 * s + bob),
        (fig_x + 28 * s, gy - 102 * s + bob * 0.5),
        (fig_x + 64 * s, gy - 102 * s + bob * 0.5),
    ]
    _draw_progressive_path(draw, arm_pts, _ease_out_cubic((t - 0.45) / 0.45), WHITE, lw)

    # Head circle
    head_r = 34 * s
    head_pts = _sample_circle(fig_x - 8 * s, gy - 208 * s + bob, head_r, steps=48, start_deg=90.0)
    _draw_progressive_path(draw, head_pts, _ease_out_cubic((t - 0.35) / 0.55), WHITE, lw)

    # 3. Rounded speech bubble with pointed bottom-left tail
    bx0, by0 = cx - 80 * s, cy - 170 * s
    bx1, by1 = cx + 195 * s, cy - 34 * s
    br = 26 * s
    # Construct single continuous path starting at tail tip
    bubble_pts: list[tuple[float, float]] = [
        (bx0 + 48 * s, by1),
        (bx0 + 42 * s, by1 + 42 * s),
        (bx0 + 88 * s, by1),
        (bx1 - br, by1),
    ]
    # Bottom-right corner -> top-right -> top-left -> bottom-left
    for c_x, c_y, a0, a1 in [
        (bx1 - br, by1 - br, 90.0, 0.0),
        (bx1 - br, by0 + br, 0.0, -90.0),
        (bx0 + br, by0 + br, -90.0, -180.0),
        (bx0 + br, by1 - br, -180.0, -270.0),
    ]:
        for i in range(11):
            ang = math.radians(a0 + (a1 - a0) * (i / 10.0))
            bubble_pts.append((c_x + br * math.cos(ang), c_y + br * math.sin(ang)))
    bubble_pts.append((bx0 + 48 * s, by1))
    _draw_progressive_path(draw, bubble_pts, _ease_out_cubic((t - 0.65) / 0.85), WHITE, lw)

    # 4. Three pulsing typing dots inside bubble
    dot_reveal = _ease_out_cubic((t - 1.25) / 0.45)
    if dot_reveal > 0.01:
        dot_y = (by0 + by1) / 2.0
        for idx_d, dx in enumerate((-48 * s, 0.0, 48 * s)):
            phase = (t * 2.4 - idx_d * 0.45) % 2.4
            wave = max(0.0, math.cos(min(phase, 1.2) * math.pi / 1.2))
            col = _lerp_color(GRAY_DIM, WHITE, 0.25 + 0.75 * wave)
            col = _lerp_color(BG_RGB, col, dot_reveal)
            dr = 9.5 * s
            draw.ellipse([cx + 58 * s + dx - dr, dot_y - dr, cx + 58 * s + dx + dr, dot_y + dr], fill=col)

    # 5. Tangled yellow scribble coil dynamically drawing upper-right (enters around t=3.2s or 38% of scene)
    sc_start = min(3.0, dur * 0.36)
    sc_p = _ease_out_cubic((t - sc_start) / 1.65)
    if sc_p > 0.01:
        sc_cx, sc_cy = bx1 + 65 * s, by0 - 25 * s
        scribble_pts: list[tuple[float, float]] = []
        num_steps = 180
        for i in range(num_steps + 1):
            u = i / float(num_steps)
            ang = u * 3.45 * 2.0 * math.pi - 0.8
            rx = (84 + 26 * math.sin(u * 9.0) + 12 * math.cos(u * 15.0)) * s
            ry = (96 + 22 * math.cos(u * 7.0) - 10 * math.sin(u * 13.0)) * s
            ox = 14 * math.sin(u * 5.2) * s
            oy = 12 * math.cos(u * 6.4) * s
            scribble_pts.append((sc_cx + ox + rx * math.cos(ang), sc_cy + oy + ry * math.sin(ang)))
        _draw_progressive_path(draw, scribble_pts, sc_p, YELLOW, max(int(round(4.5 * s)), 3))

    # 6. Quiet yellow side micro-caption under bubble
    lbl_a = _ease_out_cubic((t - (sc_start + 0.65)) / 0.55)
    if lbl_a > 0.01:
        lbl = str(meta.get("side_label") or "WHERE DO I START?").upper()
        fnt = _find_font("mono", int(round(32 * s)))
        col = _lerp_color(BG_RGB, YELLOW, lbl_a)
        _draw_tracked_text(draw, lbl, cx + 70 * s, by1 + 26 * s, fnt, col, letter_spacing=6 * s, anchor_center=False)


def _scene_cognitive_load_stack(
    draw: ImageDraw.ImageDraw,
    t: float,
    dur: float,
    cx: float,
    cy: float,
    s: float,
    meta: dict[str, Any],
) -> None:
    """Exact homage to sample_p2 f_03: stick-figure holding a growing stack of weight boxes."""
    lw = max(int(round(5.0 * s)), 3)
    gy = cy + 215 * s

    # Ground line
    g_p = _ease_out_cubic(t / 0.50)
    g_half = 330 * s * g_p
    if g_p > 0.01:
        _draw_progressive_path(draw, [(cx - g_half, gy), (cx + g_half, gy)], 1.0, WHITE, lw)

    # Subtle strain compression when boxes land
    strain = 0.0
    drop_times = [0.65, 1.35, 2.05, 2.75]
    for dt in drop_times:
        if t >= dt:
            age = t - dt
            strain += 4.0 * math.exp(-age * 5.0) * math.sin(age * 16.0)
    squash = strain * s

    # Stick figure standing centered with arms raised overhead
    fig_p = _ease_out_cubic((t - 0.10) / 0.60)
    # Left leg & right leg
    hip_y = gy - 115 * s + squash * 0.4
    neck_y = gy - 205 * s + squash
    _draw_progressive_path(draw, [(cx - 34 * s, gy + 18 * s), (cx, hip_y), (cx + 34 * s, gy + 18 * s)], fig_p, WHITE, lw)
    _draw_progressive_path(draw, [(cx, hip_y), (cx, neck_y)], fig_p, WHITE, lw)

    # Head circle
    head_r = 34 * s
    head_cy = neck_y - head_r + 2 * s
    _draw_progressive_path(draw, _sample_circle(cx, head_cy, head_r, steps=44), _ease_out_cubic((t - 0.25) / 0.45), WHITE, lw)

    # Raised arms supporting bottom box
    arm_p = _ease_out_cubic((t - 0.35) / 0.45)
    box_base_y = head_cy - head_r - 2 * s
    _draw_progressive_path(draw, [(cx, neck_y + 18 * s), (cx - 56 * s, box_base_y)], arm_p, WHITE, lw)
    _draw_progressive_path(draw, [(cx, neck_y + 18 * s), (cx + 56 * s, box_base_y)], arm_p, WHITE, lw)

    # 4 Stacked weight boxes (widest bottom -> narrowest top, box #3 yellow!)
    box_specs = [
        (170 * s, 64 * s, WHITE),
        (150 * s, 60 * s, WHITE),
        (134 * s, 58 * s, YELLOW),
        (110 * s, 54 * s, WHITE),
    ]
    cur_y = box_base_y
    for i, (bw, bh, bcol) in enumerate(box_specs):
        dt = drop_times[i]
        if t >= dt:
            ep = _ease_out_cubic((t - dt) / 0.42)
            drop_off = (1.0 - ep) * -120.0 * s
            fade_col = _lerp_color(BG_RGB, bcol, min(ep * 1.4, 1.0))
            x0, x1 = cx - bw / 2.0, cx + bw / 2.0
            y1 = cur_y + drop_off
            y0 = y1 - bh
            path = _sample_rounded_rect_path(x0, y0, x1, y1, r=10 * s)
            _draw_progressive_path(draw, path, 1.0, fade_col, lw)
        cur_y -= (bh + 6 * s)

    # Floating yellow mono label on right
    lbl_a = _ease_out_cubic((t - 2.35) / 0.60)
    if lbl_a > 0.01:
        side_lines = str(meta.get("side_label") or "COGNITIVE\nLOAD").upper().split("\n")
        fnt = _find_font("mono", int(round(32 * s)))
        col = _lerp_color(BG_RGB, YELLOW, lbl_a)
        ly = cy - 175 * s
        for line in side_lines[:2]:
            _draw_tracked_text(draw, line.strip(), cx + 190 * s, ly, fnt, col, letter_spacing=6 * s)
            ly += 44 * s


def _scene_habit_tracker_days(
    draw: ImageDraw.ImageDraw,
    t: float,
    dur: float,
    cx: float,
    cy: float,
    s: float,
    meta: dict[str, Any],
) -> None:
    """Exact homage to sample_p2 f_02: 5 rounded day pill cards with glowing yellow active dots."""
    lw = max(int(round(4.0 * s)), 2)
    days = ["MON", "TUE", "WED", "THU", "FRI"]
    active_days = {0, 1, 3}  # Consistent without needing perfection!

    pill_w = 108 * s
    pill_h = 152 * s
    gap = 20 * s
    total_w = len(days) * pill_w + (len(days) - 1) * gap
    start_x = cx - total_w / 2.0
    top_y = cy - 75 * s

    fnt_day = _find_font("mono", int(round(26 * s)))

    for i, day in enumerate(days):
        st = 0.25 + i * 0.22
        ep = _ease_out_cubic((t - st) / 0.45)
        if ep <= 0.01:
            continue
        dy = (1.0 - ep) * 28 * s
        x0 = start_x + i * (pill_w + gap)
        y0 = top_y + dy
        x1, y1 = x0 + pill_w, y0 + pill_h
        border_col = _lerp_color(BG_RGB, CARD_BORDER, ep)
        path = _sample_rounded_rect_path(x0, y0, x1, y1, r=28 * s)
        _draw_progressive_path(draw, path, 1.0, border_col, lw)

        # Day text
        txt_col = _lerp_color(BG_RGB, GRAY_MID, ep)
        _draw_tracked_text(draw, day, (x0 + x1) / 2.0, y0 + 28 * s, fnt_day, txt_col, letter_spacing=3 * s, anchor_center=True)

        # Circle dot below day label
        dot_cx = (x0 + x1) / 2.0
        dot_cy = y0 + 102 * s
        base_r = 21 * s
        if i in active_days:
            pop_t = _ease_out_back((t - (st + 0.45)) / 0.40)
            if t >= st + 0.45:
                r_now = base_r * max(0.05, min(pop_t, 1.12))
                draw.ellipse([dot_cx - r_now, dot_cy - r_now, dot_cx + r_now, dot_cy + r_now], fill=YELLOW)
            else:
                draw.ellipse([dot_cx - base_r, dot_cy - base_r, dot_cx + base_r, dot_cy + base_r], outline=GRAY_DIM, width=lw)
        else:
            ring_col = _lerp_color(BG_RGB, GRAY_DIM, ep)
            draw.ellipse([dot_cx - base_r, dot_cy - base_r, dot_cx + base_r, dot_cy + base_r], outline=ring_col, width=lw)

    # Subtle wide-tracked dim caption beneath pills
    cap_a = _ease_out_cubic((t - 1.55) / 0.65)
    if cap_a > 0.01:
        cap = str(meta.get("dim_caption") or "CONSISTENCY BEATS PERFECTION").upper()
        fnt_cap = _find_font("mono", int(round(27 * s)))
        col = _lerp_color(BG_RGB, GRAY_MID, cap_a)
        _draw_tracked_text(draw, cap, cx, top_y + pill_h + 54 * s, fnt_cap, col, letter_spacing=7 * s, anchor_center=True)


def _scene_hourglass_time(
    draw: ImageDraw.ImageDraw,
    t: float,
    dur: float,
    cx: float,
    cy: float,
    s: float,
    meta: dict[str, Any],
) -> None:
    """Exact homage to sample_p2 f_07: minimal thin-line hourglass with smoothly falling yellow sand."""
    lw = max(int(round(5.0 * s)), 3)
    top_y = cy - 220 * s
    bot_y = cy + 200 * s
    mid_y = (top_y + bot_y) / 2.0
    half_w = 88 * s

    # Top & bottom horizontal bars
    bar_p = _ease_out_cubic(t / 0.55)
    _draw_progressive_path(draw, [(cx - half_w * 1.15, top_y), (cx + half_w * 1.15, top_y)], bar_p, WHITE, lw)
    _draw_progressive_path(draw, [(cx - half_w * 1.15, bot_y), (cx + half_w * 1.15, bot_y)], bar_p, WHITE, lw)

    # Smooth symmetric glass curves (left & right Bezier silhouettes)
    glass_p = _ease_out_cubic((t - 0.18) / 0.85)
    left_top = _sample_cubic_bezier(
        (cx - half_w * 0.88, top_y),
        (cx - half_w * 0.88, top_y + 110 * s),
        (cx - 12 * s, mid_y - 36 * s),
        (cx - 6 * s, mid_y),
        steps=24,
    )
    left_bot = _sample_cubic_bezier(
        (cx - 6 * s, mid_y),
        (cx - 12 * s, mid_y + 36 * s),
        (cx - half_w * 0.88, bot_y - 110 * s),
        (cx - half_w * 0.88, bot_y),
        steps=24,
    )
    right_top = [(2 * cx - x, y) for x, y in left_top]
    right_bot = [(2 * cx - x, y) for x, y in left_bot]
    _draw_progressive_path(draw, left_top + left_bot, glass_p, WHITE, lw)
    _draw_progressive_path(draw, right_top + right_bot, glass_p, WHITE, lw)

    # Animated yellow sand flowing from top chamber -> bottom mound
    sand_a = _ease_out_cubic((t - 0.80) / 0.45)
    if sand_a > 0.01:
        flow = _clamp01((t - 0.80) / max(dur - 1.1, 2.0))
        sand_col = _lerp_color(BG_RGB, YELLOW, sand_a)

        # Top chamber shrinking yellow sand funnel
        top_fill = max(0.18, 1.0 - flow * 0.72)
        top_sand_h = 82 * s * top_fill
        top_sand_w = 60 * s * (0.45 + 0.55 * top_fill)
        top_poly = [
            (cx - top_sand_w, mid_y - 14 * s - top_sand_h),
            (cx + top_sand_w, mid_y - 14 * s - top_sand_h),
            (cx + 6 * s, mid_y - 4 * s),
            (cx - 6 * s, mid_y - 4 * s),
        ]
        draw.polygon(top_poly, fill=sand_col)

        # Trickling vertical center sand stream + falling grains
        stream_bot = bot_y - 14 * s - 90 * s * (0.15 + 0.75 * flow)
        draw.line([(cx, mid_y + 2 * s), (cx, max(stream_bot, mid_y + 18 * s))], fill=sand_col, width=max(int(round(3.5 * s)), 2))
        for g_i in range(4):
            gf = ((t * 1.9 + g_i * 0.25) % 1.0)
            gy_dot = _lerp(mid_y + 10 * s, bot_y - 26 * s, gf)
            gr = 3.5 * s
            draw.ellipse([cx - gr, gy_dot - gr, cx + gr, gy_dot + gr], fill=sand_col)

        # Growing yellow sand mound at bottom
        mound_h = (26 + 74 * flow) * s
        mound_w = (36 + 34 * flow) * s
        mound_pts = [
            (cx - mound_w, bot_y - 8 * s),
            (cx - mound_w * 0.42, bot_y - 8 * s - mound_h * 0.65),
            (cx, bot_y - 8 * s - mound_h),
            (cx + mound_w * 0.42, bot_y - 8 * s - mound_h * 0.65),
            (cx + mound_w, bot_y - 8 * s),
        ]
        draw.polygon(mound_pts, fill=sand_col)

    # Subtle wide-tracked dim caption beneath
    cap_a = _ease_out_cubic((t - 1.15) / 0.55)
    if cap_a > 0.01:
        cap = str(meta.get("dim_caption") or "NEURAL PATHWAYS TAKE TIME").upper()
        fnt_cap = _find_font("mono", int(round(27 * s)))
        col = _lerp_color(BG_RGB, GRAY_MID, cap_a)
        _draw_tracked_text(draw, cap, cx, bot_y + 58 * s, fnt_cap, col, letter_spacing=7 * s, anchor_center=True)


def _scene_focus_doorway_sparks(
    draw: ImageDraw.ImageDraw,
    t: float,
    dur: float,
    cx: float,
    cy: float,
    s: float,
    meta: dict[str, Any],
) -> None:
    """Exact homage to sample_p2 f_06: minimal tall doorway outline + inner yellow arch + rising yellow rings."""
    lw = max(int(round(5.0 * s)), 3)
    fw, fh = 290 * s, 430 * s
    x0, y0 = cx - fw / 2.0, cy - fh / 2.0 + 30 * s
    x1, y1 = cx + fw / 2.0, cy + fh / 2.0 + 30 * s

    # Outer white rounded frame
    frame_pts = _sample_rounded_rect_path(x0, y0, x1, y1, r=14 * s)
    _draw_progressive_path(draw, frame_pts, _ease_out_cubic(t / 0.85), WHITE, lw)

    # Subtle dashed stitch lines top & bottom inside frame
    dash_a = _ease_out_cubic((t - 0.55) / 0.45)
    if dash_a > 0.01:
        dcol = _lerp_color(BG_RGB, CARD_BORDER, dash_a)
        for dy_line in (y0 + 26 * s, y1 - 26 * s):
            dx = x0 + 28 * s
            while dx < x1 - 36 * s:
                draw.line([(dx, dy_line), (dx + 12 * s, dy_line)], fill=dcol, width=max(int(round(3.5 * s)), 2))
                dx += 24 * s

    # Inner glowing yellow arch drawing upward & around
    arch_p = _ease_out_cubic((t - 0.70) / 1.15)
    ax0, ax1 = x0 + 38 * s, x1 - 38 * s
    ay_bot = y1 - 32 * s
    ay_spring = y0 + 135 * s
    arch_r = (ax1 - ax0) / 2.0
    arch_pts: list[tuple[float, float]] = [(ax0, ay_bot), (ax0, ay_spring)]
    for i in range(37):
        ang = math.radians(180.0 + 180.0 * (i / 36.0))
        arch_pts.append((cx + arch_r * math.cos(ang), ay_spring + arch_r * 0.72 * math.sin(ang)))
    arch_pts.append((ax1, ay_bot))
    _draw_progressive_path(draw, arch_pts, arch_p, YELLOW, lw)

    # Floating thin-line yellow circles rising calmly above doorway
    sparks_a = _ease_out_cubic((t - 1.35) / 0.55)
    if sparks_a > 0.01:
        specs = [(cx + 46 * s, y0 - 46 * s, 16 * s, 0.0), (cx + 16 * s, y0 - 118 * s, 10 * s, 1.4), (cx - 28 * s, y0 - 84 * s, 7 * s, 2.7)]
        for sx, sy, sr, ph in specs:
            drift = math.sin(t * 1.6 + ph) * 14 * s
            pulse = 0.55 + 0.45 * math.sin(t * 2.1 + ph)
            scol = _lerp_color(BG_RGB, YELLOW, sparks_a * pulse)
            draw.ellipse([sx - sr, sy + drift - sr, sx + sr, sy + drift + sr], outline=scol, width=max(int(round(4.0 * s)), 2))

    # Dim caption beneath
    cap_a = _ease_out_cubic((t - 1.20) / 0.55)
    if cap_a > 0.01:
        cap = str(meta.get("dim_caption") or "ONE QUIET DOORWAY").upper()
        fnt_cap = _find_font("mono", int(round(27 * s)))
        col = _lerp_color(BG_RGB, GRAY_MID, cap_a)
        _draw_tracked_text(draw, cap, cx, y1 + 52 * s, fnt_cap, col, letter_spacing=7 * s, anchor_center=True)


def _scene_moon_calm_reset(
    draw: ImageDraw.ImageDraw,
    t: float,
    dur: float,
    cx: float,
    cy: float,
    s: float,
    meta: dict[str, Any],
) -> None:
    """Exact homage to sample_p2 f_05 & f_08: glowing thin-line yellow crescent moon + calm stick figure."""
    lw = max(int(round(5.0 * s)), 3)

    # Subtle twinkling dim stars in background
    star_a = _ease_out_cubic((t - 0.40) / 0.80)
    if star_a > 0.01:
        stars = [(-240, -190, 0.0), (190, -210, 1.3), (-60, -245, 2.4), (255, -80, 0.8), (-285, -35, 3.1)]
        for sx, sy, ph in stars:
            tw = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 2.2 + ph))
            col = _lerp_color(BG_RGB, GRAY_MID, star_a * tw)
            r = 3.5 * s
            draw.ellipse([cx + sx * s - r, cy + sy * s - r, cx + sx * s + r, cy + sy * s + r], fill=col)

    # Glowing yellow crescent moon upper-left
    moon_p = _ease_out_cubic(t / 1.05)
    mcx = cx - 175 * s
    mcy = cy - 115 * s + math.sin(t * 1.5) * 6 * s
    r_out = 72 * s
    outer_arc: list[tuple[float, float]] = []
    for i in range(41):
        ang = math.radians(110.0 + 235.0 * (i / 40.0))  # 110 -> 345 deg (left crescent outer)
        # Rotate cleanly so crescent opens to upper-right like f_05/f_08
        a_rot = math.radians(-115.0 - 205.0 * (i / 40.0))
        outer_arc.append((mcx + r_out * math.cos(a_rot), mcy + r_out * math.sin(a_rot)))
    # Inner concave crescent return curve
    p_start = outer_arc[-1]
    p_end = outer_arc[0]
    inner_arc = _sample_cubic_bezier(
        p_start,
        (mcx + 12 * s, mcy + 58 * s),
        (mcx - 28 * s, mcy - 18 * s),
        p_end,
        steps=32,
    )
    _draw_progressive_path(draw, outer_arc + inner_arc, moon_p, YELLOW, lw)

    # Minimalist calm standing stick-figure lower-right
    fig_p = _ease_out_cubic((t - 0.45) / 0.75)
    fx = cx + 150 * s
    fy_base = cy + 120 * s
    breath = math.sin(t * 2.0) * 2.5 * s
    _draw_progressive_path(draw, [(fx - 26 * s, fy_base), (fx, fy_base - 64 * s), (fx + 26 * s, fy_base)], fig_p, WHITE, lw)
    _draw_progressive_path(draw, [(fx, fy_base - 64 * s), (fx, fy_base - 134 * s + breath)], fig_p, WHITE, lw)
    _draw_progressive_path(draw, [(fx - 30 * s, fy_base - 92 * s + breath), (fx, fy_base - 122 * s + breath), (fx + 30 * s, fy_base - 92 * s + breath)], fig_p, WHITE, lw)
    _draw_progressive_path(draw, _sample_circle(fx, fy_base - 166 * s + breath, 28 * s, steps=40), _ease_out_cubic((t - 0.65) / 0.55), WHITE, lw)

    # Dim wide-tracked caption centered below
    cap_a = _ease_out_cubic((t - 1.15) / 0.60)
    if cap_a > 0.01:
        cap = str(meta.get("dim_caption") or "REST IS PART OF FOCUS").upper()
        fnt_cap = _find_font("mono", int(round(27 * s)))
        col = _lerp_color(BG_RGB, GRAY_MID, cap_a)
        _draw_tracked_text(draw, cap, cx, fy_base + 74 * s, fnt_cap, col, letter_spacing=7 * s, anchor_center=True)


def _scene_minimal_card(
    draw: ImageDraw.ImageDraw,
    t: float,
    dur: float,
    cx: float,
    cy: float,
    s: float,
    meta: dict[str, Any],
    is_closing: bool = False,
) -> None:
    """Exact homage to sample_p2 f_04 (research/reference card) & f_09 (closing 3-line highlight card)."""
    lw = max(int(round(3.5 * s)), 2)
    ep = _ease_out_cubic(t / 0.65)
    if ep <= 0.01:
        return

    card_w = 880 * s
    card_h = 470 * s
    scale = 0.96 + 0.04 * ep
    cw, ch = card_w * scale, card_h * scale
    x0, y0 = cx - cw / 2.0, cy - ch / 2.0
    x1, y1 = cx + cw / 2.0, cy + ch / 2.0

    fill_col = _lerp_color(BG_RGB, CARD_BG, ep)
    bdr_col = _lerp_color(BG_RGB, CARD_BORDER, ep)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=int(round(30 * s)), fill=fill_col, outline=bdr_col, width=lw)

    pad_x = 54 * s
    pad_y = 48 * s

    if not is_closing:
        # Top-left yellow circle icon + Bold title + muted citation + horizontal divider (like f_04!)
        ic_r = 30 * s
        ic_cx, ic_cy = x0 + pad_x + ic_r, y0 + pad_y + ic_r
        ycol = _lerp_color(BG_RGB, YELLOW, ep)
        draw.ellipse([ic_cx - ic_r, ic_cy - ic_r, ic_cx + ic_r, ic_cy + ic_r], outline=ycol, width=max(int(round(3.5 * s)), 2))
        # Tiny minimal open-book vector inside yellow circle
        bw, bh = 15 * s, 11 * s
        draw.line([(ic_cx, ic_cy - bh + 2 * s), (ic_cx, ic_cy + bh)], fill=ycol, width=max(int(round(3.0 * s)), 2))
        draw.line([(ic_cx - bw, ic_cy - bh), (ic_cx, ic_cy - bh + 4 * s), (ic_cx + bw, ic_cy - bh)], fill=ycol, width=max(int(round(3.0 * s)), 2))
        draw.line([(ic_cx - bw, ic_cy - bh), (ic_cx - bw, ic_cy + bh - 3 * s), (ic_cx, ic_cy + bh), (ic_cx + bw, ic_cy + bh - 3 * s), (ic_cx + bw, ic_cy - bh)], fill=ycol, width=max(int(round(3.0 * s)), 2))

        fnt_title = _find_font("sans_bold", int(round(40 * s)))
        fnt_sub = _find_font("sans", int(round(25 * s)))
        title = str(meta.get("card_title") or "Attention Residue")
        sub = str(meta.get("card_subtitle") or "UC Irvine • Cognitive Focus Study")
        draw.text((ic_cx + ic_r + 24 * s, y0 + pad_y - 2 * s), title, font=fnt_title, fill=_lerp_color(BG_RGB, WHITE, ep))
        draw.text((ic_cx + ic_r + 24 * s, y0 + pad_y + 48 * s), sub, font=fnt_sub, fill=_lerp_color(BG_RGB, GRAY_MID, ep))

        # Horizontal divider draws left -> right
        div_y = y0 + pad_y + 104 * s
        div_p = _ease_out_cubic((t - 0.35) / 0.55)
        if div_p > 0.01:
            draw.line([(x0 + pad_x, div_y), (x0 + pad_x + (cw - 2 * pad_x) * div_p, div_y)], fill=GRAY_DIM, width=max(int(round(2.5 * s)), 2))

        body_top = div_y + 42 * s
    else:
        # Closing card eyebrow (exact homage to f_09: "DOA UNTUKMU" -> "DAILY FOCUS PROTOCOL")
        eyebrow = str(meta.get("card_eyebrow") or "DAILY FOCUS PROTOCOL").upper()
        fnt_eye = _find_font("mono", int(round(24 * s)))
        _draw_tracked_text(draw, eyebrow, x0 + pad_x, y0 + pad_y, fnt_eye, _lerp_color(BG_RGB, YELLOW, ep), letter_spacing=5 * s)
        body_top = y0 + pad_y + 62 * s

    # 3 crisp lines that light up sequentially from muted gray -> bright white!
    lines = meta.get("card_lines") or [
        "Every quick scroll leaves fragments",
        "stuck inside your working memory,",
        "costing 23 minutes of deep focus.",
    ]
    fnt_body = _find_font("sans_bold", int(round(42 * s)))
    line_gap = 82 * s if len(lines) <= 3 else 68 * s
    span = max(dur - 1.6, 2.5)
    for idx_l, line_txt in enumerate(lines[:3]):
        lit_t = 0.55 + (idx_l / float(max(len(lines), 1))) * span * 0.78
        lit_p = _ease_out_cubic((t - lit_t) / 0.55)
        col = _lerp_color(GRAY_DIM, WHITE, lit_p)
        col = _lerp_color(BG_RGB, col, ep)
        draw.text((x0 + pad_x, body_top + idx_l * line_gap), str(line_txt), font=fnt_body, fill=col)


# ---------------------------------------------------------------------------
# Word-Synced Monospace ALL-CAPS Subtitle Renderer (Exact sample_p2 look!)
# ---------------------------------------------------------------------------

@dataclass
class WordEvent:
    text: str
    start_sec: float
    end_sec: float


def _chunk_words_into_phrases(words: list[WordEvent], max_words: int = 8) -> list[list[WordEvent]]:
    """Group word events into clean poetic 5-9 word phrases breaking at punctuation when possible."""
    chunks: list[list[WordEvent]] = []
    cur: list[WordEvent] = []
    for w in words:
        cur.append(w)
        ends_punct = bool(re.search(r"[\.\!\?,;:]$", w.text))
        if len(cur) >= max_words or (ends_punct and len(cur) >= 4):
            chunks.append(cur)
            cur = []
    if cur:
        if chunks and len(cur) <= 2 and len(chunks[-1]) <= 6:
            chunks[-1].extend(cur)
        else:
            chunks.append(cur)
    return chunks


def _draw_minimal_subtitles(
    img: Image.Image,
    t_sec: float,
    phrases: list[list[WordEvent]],
    highlight_words: set[str],
    width: int,
    height: int,
    is_short: bool,
) -> None:
    """Draw borderless ALL-CAPS wide-tracked monospace subtitles with soft yellow keyword highlights."""
    if not phrases:
        return

    # Find active phrase at t_sec
    active: list[WordEvent] | None = None
    for idx, ph in enumerate(phrases):
        st = ph[0].start_sec - 0.08
        next_st = phrases[idx + 1][0].start_sec - 0.08 if idx + 1 < len(phrases) else ph[-1].end_sec + 1.5
        if st <= t_sec < next_st:
            active = ph
            break
    if active is None:
        return

    # Reveal words progressively as spoken (gives that hypnotic typewriter storytelling cadence!)
    visible = [w for w in active if t_sec >= (w.start_sec - 0.06)]
    if not visible:
        visible = [active[0]]

    draw = ImageDraw.Draw(img)
    font_size = int(round(width * 0.041)) if is_short else int(round(height * 0.039))
    font = _find_font("mono", font_size)
    letter_sp = 5.5 if is_short else 5.0
    word_sp = 28.0 if is_short else 26.0
    max_line_w = width * (0.84 if is_short else 0.72)

    def _measure_word(word_upper: str) -> float:
        ws = [float(draw.textlength(ch, font=font)) for ch in word_upper]
        return sum(ws) + letter_sp * max(len(word_upper) - 1, 0)

    # Wrap ONLY the full active phrase first so lines NEVER jump/reflow mid-sentence!
    lines_full: list[list[WordEvent]] = []
    cur_line: list[WordEvent] = []
    cur_w = 0.0
    for w in active:
        wu = w.text.upper()
        ww = _measure_word(wu)
        add_w = ww if not cur_line else word_sp + ww
        if cur_line and cur_w + add_w > max_line_w:
            lines_full.append(cur_line)
            cur_line = [w]
            cur_w = ww
        else:
            cur_line.append(w)
            cur_w += add_w
    if cur_line:
        lines_full.append(cur_line)

    visible_ids = {id(w) for w in visible}
    line_h = int(round(font_size * 1.58))
    base_y = int(round(height * (0.675 if is_short else 0.755)))

    for l_idx, line_words in enumerate(lines_full[:4]):
        # Center each line cleanly based on its FULL width so words appear left-to-right smoothly without jitter
        word_widths = [_measure_word(w.text.upper()) for w in line_words]
        total_lw = sum(word_widths) + word_sp * max(len(line_words) - 1, 0)
        x_cursor = (width - total_lw) / 2.0
        y_line = base_y + l_idx * line_h

        for w, ww in zip(line_words, word_widths):
            if id(w) in visible_ids:
                age = max(t_sec - (w.start_sec - 0.06), 0.0)
                alpha = _ease_out_cubic(age / 0.16)
                clean_tok = re.sub(r"[^A-Z0-9]", "", w.text.upper())
                is_hl = clean_tok in highlight_words
                target_col = YELLOW if is_hl else WHITE
                col = _lerp_color(BG_RGB, target_col, alpha)
                _draw_tracked_text(draw, w.text.upper(), x_cursor, y_line, font, col, letter_spacing=letter_sp)
            x_cursor += ww + word_sp


# ---------------------------------------------------------------------------
# Public Scene Segment Renderer (30fps direct rawvideo pipe -> FFmpeg!)
# ---------------------------------------------------------------------------

def render_minimal_line_scene_segment(
    scene: dict[str, Any],
    word_events: list[WordEvent],
    duration_sec: float,
    width: int,
    height: int,
    fps: int,
    out_mp4: Path,
    watermark_text: str = "habitsains",
    is_short: bool = True,
) -> Path:
    """Render one 30fps Dark Minimalist Mono-Line scene directly into H.264 MP4."""
    scene_type = str(scene.get("scene_type") or "sitting_overwhelmed").strip().lower()
    raw_hl = scene.get("highlight_words") or []
    highlight_words = {re.sub(r"[^A-Z0-9]", "", str(w).upper()) for w in raw_hl if str(w).strip()}
    phrases = _chunk_words_into_phrases(word_events, max_words=8 if is_short else 10)

    # 2x supersampled center icon canvas box (small enough to be blazing fast, sharp enough to look like SVG!)
    box_w = int(round(width * (0.94 if is_short else 0.72)))
    box_h = int(round(height * (0.46 if is_short else 0.62)))
    box_x = (width - box_w) // 2
    box_y = int(round(height * (0.16 if is_short else 0.07)))
    ss = 2
    ss_w, ss_h = box_w * ss, box_h * ss
    icon_scale = (width / 1080.0 if is_short else height / 1080.0) * ss * (0.96 if is_short else 0.88)

    # Pre-render static matte background + subtle spaced bottom watermark ONCE!
    base_bg = Image.new("RGB", (width, height), BG_RGB)
    wm_draw = ImageDraw.Draw(base_bg)
    wm_clean = watermark_text.lstrip("@").strip().lower() or "habitsains"
    wm_font = _find_font("sans", int(round(width * 0.025 if is_short else height * 0.023)))
    _draw_tracked_text(
        wm_draw,
        wm_clean,
        width / 2.0,
        height * (0.925 if is_short else 0.935),
        wm_font,
        GRAY_MID,
        letter_spacing=10.0 if is_short else 9.0,
        anchor_center=True,
    )

    total_frames = max(int(round(duration_sec * fps)), fps)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}",
        "-r", str(fps),
        "-i", "pipe:0",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-an",
        str(out_mp4),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert proc.stdin is not None

    try:
        for f_idx in range(total_frames):
            t_sec = f_idx / float(fps)
            # Soft poetic fade-in / fade-out envelope on the icon & subtitles (watermark stays calm!)
            fade_in = _clamp01(t_sec / 0.35)
            fade_out = _clamp01((duration_sec - t_sec) / 0.38)
            env = min(fade_in, fade_out)

            frame = base_bg.copy()

            # Render 2x supersampled anti-aliased line-art icon stage
            ss_canvas = Image.new("RGB", (ss_w, ss_h), BG_RGB)
            ss_draw = ImageDraw.Draw(ss_canvas)
            scx, scy = ss_w / 2.0, ss_h / 2.0

            if scene_type == "sitting_overwhelmed":
                _scene_sitting_overwhelmed(ss_draw, t_sec, duration_sec, scx, scy, icon_scale, scene)
            elif scene_type == "cognitive_load_stack":
                _scene_cognitive_load_stack(ss_draw, t_sec, duration_sec, scx, scy, icon_scale, scene)
            elif scene_type == "habit_tracker_days":
                _scene_habit_tracker_days(ss_draw, t_sec, duration_sec, scx, scy, icon_scale, scene)
            elif scene_type == "hourglass_time":
                _scene_hourglass_time(ss_draw, t_sec, duration_sec, scx, scy, icon_scale, scene)
            elif scene_type == "focus_doorway_sparks":
                _scene_focus_doorway_sparks(ss_draw, t_sec, duration_sec, scx, scy, icon_scale, scene)
            elif scene_type == "moon_calm_reset":
                _scene_moon_calm_reset(ss_draw, t_sec, duration_sec, scx, scy, icon_scale, scene)
            elif scene_type == "minimal_research_card":
                _scene_minimal_card(ss_draw, t_sec, duration_sec, scx, scy, icon_scale, scene, is_closing=False)
            elif scene_type == "closing_protocol_card":
                _scene_minimal_card(ss_draw, t_sec, duration_sec, scx, scy, icon_scale, scene, is_closing=True)
            else:
                _scene_sitting_overwhelmed(ss_draw, t_sec, duration_sec, scx, scy, icon_scale, scene)

            down_arr = cv2.resize(np.asarray(ss_canvas), (box_w, box_h), interpolation=cv2.INTER_AREA)
            down = Image.fromarray(down_arr, mode="RGB")
            frame.paste(down, (box_x, box_y))

            # Draw synced ALL-CAPS monospace subtitles
            _draw_minimal_subtitles(frame, t_sec, phrases, highlight_words, width, height, is_short=is_short)

            # Smooth fade to matte #0E0E0E at scene boundaries (leaves bottom watermark untouched!)
            if env < 0.999:
                arr = np.asarray(frame, dtype=np.float32)
                cut_y = int(round(height * 0.89))
                bg_vec = np.array(BG_RGB, dtype=np.float32)
                arr[:cut_y] = bg_vec + (arr[:cut_y] - bg_vec) * env
                proc.stdin.write(arr.astype(np.uint8).tobytes())
            else:
                proc.stdin.write(frame.tobytes())

        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", errors="ignore") if proc.stderr else ""
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"FFmpeg minimal line render failed ({ret}): {err[-300:]}")
    finally:
        if proc.stdin and not proc.stdin.closed:
            proc.stdin.close()

    return out_mp4


# ---------------------------------------------------------------------------
# Word-Boundary Neural Storytelling Audio + Meditative Ambient Soundscape
# ---------------------------------------------------------------------------

async def _synthesize_edge_with_word_timings(
    text: str,
    out_mp3: Path,
    voice: str = "en-US-BrianMultilingualNeural",
    rate: str = "-7%",
    pitch: str = "+0Hz",
) -> tuple[float, list[WordEvent]]:
    """Synthesize calm storytelling speech via Edge TTS and capture exact WordBoundary timestamps."""
    import edge_tts

    comm = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    words: list[WordEvent] = []
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    with out_mp3.open("wb") as fh:
        async for chunk in comm.stream():
            ctype = chunk.get("type")
            if ctype == "audio":
                fh.write(chunk["data"])
            elif ctype == "WordBoundary":
                w_txt = str(chunk.get("text", "")).strip()
                if w_txt:
                    st = float(chunk.get("offset", 0)) / 10_000_000.0
                    dur = float(chunk.get("duration", 0)) / 10_000_000.0
                    words.append(WordEvent(text=w_txt, start_sec=st, end_sec=st + max(dur, 0.12)))

    # Probe exact audio duration
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(out_mp3)],
        capture_output=True, text=True, check=True,
    )
    total_dur = max(float(res.stdout.strip() or 1.0), 1.0)

    # Preserve punctuation from source text onto word events so subtitles look natural!
    src_tokens = [tok for tok in text.strip().split() if tok]
    if words and len(src_tokens) == len(words):
        for w_ev, s_tok in zip(words, src_tokens):
            w_ev.text = s_tok
    elif not words and src_tokens:
        # Syllable/character + punctuation weighted word timing (natural speech cadence)
        weights = [
            len(re.sub(r"[^A-Za-z0-9]", "", tok)) + 2.5 + (6.0 if tok.endswith((".", "!", "?")) else (3.5 if tok.endswith((",", ";", ":")) else 0.0))
            for tok in src_tokens
        ]
        w_sum = sum(weights) or 1.0
        cur_t = 0.08
        usable = max(total_dur - 0.16, 0.5)
        words = []
        for tok, wt in zip(src_tokens, weights):
            d_tok = usable * (wt / w_sum)
            words.append(WordEvent(text=tok, start_sec=cur_t, end_sec=cur_t + d_tok))
            cur_t += d_tok

    return total_dur, words


def _mix_meditative_soundscape(
    voice_track: Path,
    scene_starts: list[float],
    total_dur: float,
    out_m4a: Path,
    work_dir: Path,
) -> Path:
    """Mix calm storytelling voice + warm minimalist ambient piano-like pad (-24 dB) + gentle soft chime."""
    chime_wav = work_dir / "_minimal_chime.wav"
    try:
        # Ultra-soft warm bell/chime (0.28s, very subtle -22dB)
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "aevalsrc='(0.6*sin(2*PI*523.25*t)+0.4*sin(2*PI*783.99*t))*exp(-11*t)':s=44100:d=0.30",
                "-af", "lowpass=f=1800,volume=-22dB",
                "-c:a", "pcm_s16le",
                str(chime_wav),
            ],
            capture_output=True, check=True,
        )
        # Warm meditative Cmaj9 ambient pad (very gentle, intimate dark vibe)
        fade_out_st = max(total_dur - 2.2, 0.5)
        pad_expr = (
            "0.26*sin(2*PI*130.81*t)+0.20*sin(2*PI*196.00*t)+0.16*sin(2*PI*246.94*t)"
            "+0.12*sin(2*PI*293.66*t)*(0.75+0.25*sin(2*PI*0.14*t))"
        )
        inputs = [
            "-i", str(voice_track),
            "-f", "lavfi", "-t", f"{total_dur + 0.5:.2f}", "-i", f"aevalsrc='{pad_expr}':s=44100:c=stereo",
        ]
        filters = [
            f"[1:a]lowpass=f=420,volume=-24dB,afade=t=in:st=0:d=1.6,afade=t=out:st={fade_out_st:.2f}:d=2.0[pad]",
        ]
        mix_labels = ["[0:a]", "[pad]"]
        nxt = 2
        for idx_s, st in enumerate(scene_starts[1:8], start=1):
            ms = max(int(round(st * 1000)), 0)
            inputs.extend(["-i", str(chime_wav)])
            filters.append(f"[{nxt}:a]adelay={ms}|{ms}[ch{idx_s}]")
            mix_labels.append(f"[ch{idx_s}]")
            nxt += 1

        filters.append(f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:dropout_transition=2:normalize=0[out]")
        subprocess.run(
            ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]", "-c:a", "aac", "-b:a", "192k", str(out_m4a)],
            capture_output=True, text=True, check=True,
        )
        if out_m4a.exists() and out_m4a.stat().st_size > 1024:
            return out_m4a
    except Exception as exc:
        print(f"[minimal-audio] Soundscape fallback: {exc}", flush=True)
    finally:
        chime_wav.unlink(missing_ok=True)
    return voice_track


def build_minimal_line_demo_video(
    scenes: list[dict[str, Any]],
    out_mp4: Path,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    watermark: str = "habitsains",
    voice: str = "en-US-BrianMultilingualNeural",
) -> dict[str, Any]:
    """Build a complete end-to-end Dark Minimalist Mono-Line Storytelling video."""
    is_short = height > width
    work_dir = out_mp4.parent / "_v7_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    seg_videos: list[Path] = []
    seg_audios: list[Path] = []
    scene_starts: list[float] = []
    cursor = 0.0
    pause_sec = 0.65

    for idx, sc in enumerate(scenes, start=1):
        mp3_path = work_dir / f"voice_{idx:02d}.mp3"
        dur, w_events = asyncio.run(_synthesize_edge_with_word_timings(sc["narration"], mp3_path, voice=voice))
        # Pad scene audio with brief contemplative silence pause
        padded_wav = work_dir / f"voice_{idx:02d}_pad.wav"
        seg_dur = dur + pause_sec
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(mp3_path),
                "-af", f"apad=pad_dur={pause_sec:.2f}",
                "-t", f"{seg_dur:.3f}",
                "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le",
                str(padded_wav),
            ],
            capture_output=True, check=True,
        )
        seg_audios.append(padded_wav)
        scene_starts.append(cursor)
        cursor += seg_dur

        seg_mp4 = work_dir / f"seg_{idx:02d}.mp4"
        print(f"[v7-minimal] Rendering scene {idx}/{len(scenes)} ({sc['scene_type']}, {seg_dur:.1f}s @ {fps}fps)...", flush=True)
        render_minimal_line_scene_segment(
            scene=sc,
            word_events=w_events,
            duration_sec=seg_dur,
            width=width,
            height=height,
            fps=fps,
            out_mp4=seg_mp4,
            watermark_text=watermark,
            is_short=is_short,
        )
        seg_videos.append(seg_mp4)

    # Concat video segments
    vid_list = work_dir / "vconcat.txt"
    vid_list.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in seg_videos), encoding="utf-8")
    merged_vid = work_dir / "merged_vid.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(vid_list), "-c", "copy", str(merged_vid)], capture_output=True, check=True)

    # Concat audio segments
    aud_list = work_dir / "aconcat.txt"
    aud_list.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in seg_audios), encoding="utf-8")
    merged_voice = work_dir / "merged_voice.wav"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(aud_list), "-c", "copy", str(merged_voice)], capture_output=True, check=True)

    # Mix meditative soundscape
    mixed_m4a = work_dir / "mixed_audio.m4a"
    final_audio = _mix_meditative_soundscape(merged_voice, scene_starts, cursor, mixed_m4a, work_dir)

    # Final mux
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(merged_vid), "-i", str(final_audio),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest",
            str(out_mp4),
        ],
        capture_output=True, check=True,
    )

    # Cleanup temp work dir
    for p in work_dir.glob("*"):
        p.unlink(missing_ok=True)
    try:
        work_dir.rmdir()
    except OSError:
        pass

    return {
        "output": str(out_mp4),
        "duration_sec": round(cursor, 2),
        "size_mb": round(out_mp4.stat().st_size / (1024 * 1024), 2),
        "scene_starts": [round(x, 2) for x in scene_starts],
    }


def render_minimal_line_video_for_pipeline(
    scenes_meta: list[dict[str, Any]],
    audio_bundle: Any,
    out_video_path: Path,
    config: dict[str, Any],
    is_short: bool = False,
) -> Path:
    """Render full Studio v7 Dark Minimalist Mono-Line Storytelling video directly inside src.video_builder."""
    video_root = config.get("video", {})
    vid_cfg = video_root.get("shorts" if is_short else "youtube_long", {})
    width = int(vid_cfg.get("width", 1080 if is_short else 1920))
    height = int(vid_cfg.get("height", 1920 if is_short else 1080))
    fps = int(vid_cfg.get("fps", 30))
    pause_sec = float(vid_cfg.get("padding_after_audio_sec", 0.30 if is_short else 0.45))
    watermark = str(config.get("branding", {}).get("watermark_text", "habitsains")).lstrip("@").lower()

    work_dir = out_video_path.parent / "_minimal_v7_work"
    work_dir.mkdir(parents=True, exist_ok=True)
    cycle = [
        "sitting_overwhelmed", "cognitive_load_stack", "minimal_research_card",
        "habit_tracker_days", "hourglass_time", "focus_doorway_sparks",
        "moon_calm_reset", "closing_protocol_card",
    ]

    total_scenes = len(audio_bundle.scene_results)
    seg_videos: list[Path] = []
    scene_starts: list[float] = []
    cursor = 0.0

    for idx, scene_audio in enumerate(audio_bundle.scene_results, start=1):
        seg_dur = max(float(scene_audio.duration_sec) + pause_sec, 1.0)
        scene_starts.append(cursor)
        cursor += seg_dur

        s_raw = scenes_meta[idx - 1] if scenes_meta and idx - 1 < len(scenes_meta) else {"visual_headline": f"Part {idx}", "narration": scene_audio.text}
        stype = "closing_protocol_card" if (idx == total_scenes and total_scenes >= 3) else cycle[(idx - 1) % (len(cycle) - 1)]
        bullets = [re.sub(r"^\d+[\.\)]\s*", "", str(b)).strip() for b in (s_raw.get("bullet_points") or []) if str(b).strip()]
        headline = str(s_raw.get("visual_headline") or f"Part {idx}").strip()
        callout = str(s_raw.get("on_screen_callout") or "Consistency beats perfection").strip()

        # Build WordEvent list from pipeline audio timings (supports both Gemini TTS & Edge TTS!)
        text = str(getattr(scene_audio, "text", "") or "").strip()
        src_tokens = [tok for tok in text.split() if tok]
        w_events: list[WordEvent] = []
        raw_t = getattr(scene_audio, "word_timings", None) or []
        for wt in raw_t:
            if wt.get("type") == "WordBoundary" and str(wt.get("text", "")).strip():
                w_events.append(WordEvent(text=str(wt["text"]).strip(), start_sec=float(wt.get("start", 0.0)), end_sec=float(wt.get("end", 0.12))))
        if w_events and len(w_events) == len(src_tokens):
            for we, tok in zip(w_events, src_tokens):
                we.text = tok
        elif src_tokens:
            weights = [len(re.sub(r"[^A-Za-z0-9]", "", tok)) + 2.5 + (5.5 if tok.endswith((".", "!", "?")) else 0.0) for tok in src_tokens]
            w_sum = sum(weights) or 1.0
            cur_t, usable = 0.08, max(float(scene_audio.duration_sec) - 0.16, 0.5)
            w_events = []
            for tok, wt in zip(src_tokens, weights):
                dt = usable * (wt / w_sum)
                w_events.append(WordEvent(text=tok, start_sec=cur_t, end_sec=cur_t + dt))
                cur_t += dt

        sc = {
            "scene_type": stype,
            "highlight_words": ["FOCUS", "BRAIN", "HABITS", "TIME", "QUIET", "RESIDUE", "SCIENCE", "MINUTES", "RESET", "DEEP"],
            "side_label": headline[:22].upper(),
            "dim_caption": callout[:34].upper(),
            "card_title": headline[:28],
            "card_subtitle": "HabitSains • Evidence-Based Focus",
            "card_eyebrow": "DAILY FOCUS PROTOCOL",
            "card_lines": (bullets[:3] if len(bullets) >= 2 else [headline[:38], callout[:38], "Trust the slow science of habits."]),
        }
        seg_mp4 = work_dir / f"seg_{idx:02d}.mp4"
        print(f"[v7-minimal] Rendering scene {idx}/{total_scenes} ({stype}, {seg_dur:.1f}s @ {fps}fps)...", flush=True)
        render_minimal_line_scene_segment(sc, w_events, seg_dur, width, height, fps, seg_mp4, watermark_text=watermark, is_short=is_short)
        seg_videos.append(seg_mp4)

    vlist = work_dir / "v.txt"
    vlist.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in seg_videos), encoding="utf-8")
    merged_v = work_dir / "merged_v.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(vlist), "-c", "copy", str(merged_v)], capture_output=True, check=True)

    mixed_a = work_dir / "mixed_min.m4a"
    final_a = _mix_meditative_soundscape(Path(audio_bundle.master_audio_path), scene_starts, float(audio_bundle.total_duration_sec), mixed_a, work_dir)
    out_video_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(merged_v), "-i", str(final_a), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(out_video_path)],
        capture_output=True, check=True,
    )
    for p in work_dir.glob("*"):
        p.unlink(missing_ok=True)
    try:
        work_dir.rmdir()
    except OSError:
        pass
    return out_video_path


HABITSAINS_DEMO_SCENES: list[dict[str, Any]] = [
    {
        "scene_type": "sitting_overwhelmed",
        "narration": "For anyone who sits down to work, and suddenly feels their mind go completely blank. You have ten things to finish, yet you don't even know where to start.",
        "highlight_words": ["BLANK", "START"],
        "side_label": "WHERE DO I START?",
    },
    {
        "scene_type": "cognitive_load_stack",
        "narration": "It isn't because you are lazy. It's because before nine A.M., your brain is already carrying an invisible stack of unfinished noise.",
        "highlight_words": ["LAZY", "BRAIN", "INVISIBLE", "NOISE"],
        "side_label": "COGNITIVE\nLOAD",
    },
    {
        "scene_type": "minimal_research_card",
        "narration": "Neuroscientists call this attention residue. Every quick scroll leaves fragments stuck in your working memory for twenty-three minutes.",
        "highlight_words": ["ATTENTION", "RESIDUE", "TWENTYTHREE", "MINUTES"],
        "card_title": "Attention Residue",
        "card_subtitle": "UC Irvine • Cognitive Focus Study",
        "card_lines": [
            "Every quick scroll leaves fragments",
            "stuck inside your working memory,",
            "costing 23 minutes of deep focus.",
        ],
    },
    {
        "scene_type": "habit_tracker_days",
        "narration": "And here is the quiet truth about rewiring your focus. You don't have to win every single day to change your brain.",
        "highlight_words": ["QUIET", "FOCUS", "EVERY", "CHANGE"],
        "dim_caption": "CONSISTENCY BEATS PERFECTION",
    },
    {
        "scene_type": "hourglass_time",
        "narration": "Deep focus is a biological skill, not a sudden burst of willpower. Real neural pathways simply take quiet repetition and time.",
        "highlight_words": ["BIOLOGICAL", "SKILL", "TIME"],
        "dim_caption": "NEURAL PATHWAYS TAKE TIME",
    },
    {
        "scene_type": "focus_doorway_sparks",
        "narration": "Start with one tiny doorway tomorrow morning. Just fifteen screen-free minutes before the world enters your mind.",
        "highlight_words": ["DOORWAY", "FIFTEEN", "SCREENFREE"],
        "dim_caption": "ONE QUIET DOORWAY",
    },
    {
        "scene_type": "moon_calm_reset",
        "narration": "And tonight, put the phone across the room. Let your nervous system finally breathe in the dark.",
        "highlight_words": ["PHONE", "BREATHE", "DARK"],
        "dim_caption": "REST IS PART OF FOCUS",
    },
    {
        "scene_type": "closing_protocol_card",
        "narration": "Protect your first quiet hour. Clear the noise before you begin. And trust the slow science of small habits.",
        "highlight_words": ["PROTECT", "QUIET", "CLEAR", "SCIENCE", "HABITS"],
        "card_eyebrow": "DAILY FOCUS PROTOCOL",
        "card_lines": [
            "Protect your first quiet hour,",
            "clear the noise before you begin,",
            "and trust the science of small habits.",
        ],
    },
]


if __name__ == "__main__":
    import json

    out_file = Path("output/_v7_minimal_line_demo/habitsains_minimal_line_demo_9x16.mp4")
    info = build_minimal_line_demo_video(
        scenes=HABITSAINS_DEMO_SCENES,
        out_mp4=out_file,
        width=1080,
        height=1920,
        fps=30,
        watermark="habitsains",
        voice="en-US-BrianMultilingualNeural",
    )
    print("DEMO COMPLETE:", json.dumps(info, indent=2))
