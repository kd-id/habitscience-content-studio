"""Studio v8.2 — Cozy Midnight-Indigo 2D Diorama + Pastel Cream Cards Engine (HabitSains Edition).

Combines 100% of referensi.mp4's cozy midnight-indigo illustrated 2D visual language with
6 bespoke, story-matched HabitSains dioramas and dynamic vector icons:
  1. bedroom_morning_scroll  : Dim dawn bedroom, bed, nightstand, glowing phone screen
  2. bedroom_scroll_flood    : Zoomed bedroom + 5 golden dots + rising swarm of pastel clip/notification bubbles
  3. desk_cognitive_fog      : Cozy wooden study desk + laptop + floating residue wisps + 3-row Pastel Cream Card
  4. focus_shield_repel      : Cozy warm study room + glowing cyan shield ring PHYSICALLY repelling distraction icons
  5. cozy_deep_work_desk     : Striped study room + pendant lamp + steaming coffee mug + journal + dawn window + speech bubble
  6. neural_pathway_stars    : Warm golden connecting neural-constellation arc + 2-row Pastel Cream Protocol Card
  7. closing_dual_cards      : Cozy evening room (phone resting far away on shelf) + Gold & Teal recap cards with bespoke icons

Includes fast cached soft shadows (~3x faster 30fps rendering) and Georgia Bold Serif karaoke subtitles.
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
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Exact cozy midnight-indigo palette from referensi.mp4
SKY_TOP = (22, 16, 44)          # Deep midnight indigo
SKY_MID = (38, 29, 68)          # Soft twilight violet
FLOOR_DARK = (9, 7, 16)         # Velvet dark bottom vignette for subtitles
WOOD_DARK = (106, 70, 38)       # Cozy walnut wood desk/bedframe
WOOD_MID = (146, 98, 52)        # Warm honey oak wood
WOOD_LIGHT = (176, 122, 68)     # Highlight wood trim
GOLD_GLOW = (244, 198, 88)      # Warm amber pendant lamp & dawn glow
GOLD_TEXT = (233, 190, 82)      # Honey-gold highlight words & pill outline
PHONE_BLUE = (118, 186, 248)    # Cool blue smartphone screen glow
TEAL_SHIELD = (126, 206, 214)   # Luminous cyan protective shield ring
TEAL_ACCENT = (54, 140, 152)    # Deep teal closing card header
GOLD_ACCENT = (206, 154, 42)    # Rich gold closing card header

CREAM_CARD = (244, 242, 232)    # #F4F2E8 warm ivory card
CARD_TITLE = (34, 28, 60)       # Deep indigo card title
CARD_CITE = (172, 70, 58)       # Warm terracotta citation eyebrow
CARD_MUTED = (146, 142, 134)    # Inactive row text
CARD_INK = (26, 22, 40)         # Crisp active ink text
CARD_ITALIC = (78, 70, 92)      # Editorial italic subtitle

PASTEL_ROWS = [
    ((247, 231, 189), (235, 184, 68)),   # Warm Amber
    ((242, 216, 220), (226, 138, 155)),  # Soft Blush Rose
    ((213, 233, 232), (104, 190, 196)),  # Soft Mint Teal
]

SUB_DIM = (108, 104, 120)
SUB_WHITE = (250, 248, 244)
PILL_BG = (20, 16, 38)

_SHADOW_CACHE: dict[tuple[int, int, int], Image.Image] = {}


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def _ease_out_cubic(x: float) -> float:
    t = _clamp01(x)
    return 1.0 - (1.0 - t) ** 3


def _ease_out_back(x: float) -> float:
    t = _clamp01(x)
    c1 = 1.35
    c3 = c1 + 1.0
    return 1.0 + c3 * ((t - 1.0) ** 3) + c1 * ((t - 1.0) ** 2)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * _clamp01(t)


def _lerp_rgb(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    u = _clamp01(t)
    return (
        int(round(c1[0] + (c2[0] - c1[0]) * u)),
        int(round(c1[1] + (c2[1] - c1[1]) * u)),
        int(round(c1[2] + (c2[2] - c1[2]) * u)),
    )


def _find_font(kind: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    table = {
        "serif_bold": [
            r"C:\Windows\Fonts\georgiab.ttf",
            r"C:\Windows\Fonts\cambriab.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        ],
        "serif_italic": [
            r"C:\Windows\Fonts\georgiai.ttf",
            r"C:\Windows\Fonts\segoeuii.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
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
    for p in table.get(kind, table["sans"]):
        if Path(p).is_file():
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def _fast_downscale_rgba(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    arr = np.asarray(img)
    resized = cv2.resize(arr, (target_w, target_h), interpolation=cv2.INTER_AREA)
    return Image.fromarray(resized, mode=img.mode)


def _make_radial_glow(radius: int, color: tuple[int, int, int], max_alpha: int) -> Image.Image:
    size = radius * 2
    yy, xx = np.mgrid[0:size, 0:size]
    dist = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2) / max(float(radius), 1.0)
    falloff = np.clip(1.0 - dist, 0.0, 1.0) ** 2.15
    alpha = (falloff * max_alpha).astype(np.uint8)
    rgba = np.zeros((size, size, 4), dtype=np.uint8)
    rgba[..., 0] = color[0]
    rgba[..., 1] = color[1]
    rgba[..., 2] = color[2]
    rgba[..., 3] = alpha
    return Image.fromarray(rgba, mode="RGBA")


def _get_cached_card_shadow(cw: int, ch: int, pad: int, radius: int = 32) -> Image.Image:
    key = (cw, ch, pad)
    cached = _SHADOW_CACHE.get(key)
    if cached is not None:
        return cached
    sh = Image.new("RGBA", (cw + pad * 2, ch + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [pad, pad + 12, pad + cw, pad + ch + 12],
        radius=radius,
        fill=(6, 4, 14, 155),
    )
    sh = sh.filter(ImageFilter.GaussianBlur(radius=14))
    _SHADOW_CACHE[key] = sh
    return sh


def _scale_rgba_alpha(img: Image.Image, factor: float) -> Image.Image:
    if factor >= 0.995:
        return img
    arr = np.asarray(img).copy()
    arr[..., 3] = (arr[..., 3].astype(np.float32) * _clamp01(factor)).astype(np.uint8)
    return Image.fromarray(arr, mode="RGBA")


def _paste_alpha(dst: Image.Image, src: Image.Image, x: int, y: int) -> None:
    dw, dh = dst.size
    sw, sh = src.size
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(dw, x + sw), min(dh, y + sh)
    if x0 >= x1 or y0 >= y1:
        return
    sx0, sy0 = x0 - x, y0 - y
    sx1, sy1 = sx0 + (x1 - x0), sy0 + (y1 - y0)
    comp = Image.alpha_composite(dst.crop((x0, y0, x1, y1)), src.crop((sx0, sy0, sx1, sy1)))
    dst.paste(comp, (x0, y0))


def _build_striped_midnight_wall(width: int, height: int, floor_frac: float = 0.625) -> Image.Image:
    """Signature cozy midnight-indigo vertical striped wallpaper fading into velvety dark floor."""
    arr = np.zeros((height, width, 4), dtype=np.uint8)
    y_norm = np.linspace(0.0, 1.0, height)[:, None]
    for c_i in range(3):
        upper = SKY_TOP[c_i] + (SKY_MID[c_i] - SKY_TOP[c_i]) * np.clip(y_norm / floor_frac, 0.0, 1.0)
        lower_t = np.clip((y_norm - floor_frac) / 0.18, 0.0, 1.0) ** 1.3
        col = upper * (1.0 - lower_t) + FLOOR_DARK[c_i] * lower_t
        arr[..., c_i] = np.clip(col, 0, 255).astype(np.uint8)
    arr[..., 3] = 255

    wall_cut = int(height * floor_frac)
    stripe_w = max(width // 18, 24)
    for sx in range(0, width, stripe_w * 2):
        arr[:wall_cut, sx : min(sx + stripe_w, width), :3] = np.clip(
            arr[:wall_cut, sx : min(sx + stripe_w, width), :3].astype(np.int16) + 5, 0, 255
        ).astype(np.uint8)
    return Image.fromarray(arr, mode="RGBA")


def _apply_bottom_velvet_vignette(base: Image.Image, start_frac: float = 0.635) -> Image.Image:
    width, height = base.size
    vig = np.zeros((height, width, 4), dtype=np.uint8)
    y_norm = np.linspace(0.0, 1.0, height)[:, None]
    v_alpha = np.clip((y_norm - start_frac) / 0.16, 0.0, 1.0) ** 1.3
    vig[..., 0] = FLOOR_DARK[0]
    vig[..., 1] = FLOOR_DARK[1]
    vig[..., 2] = FLOOR_DARK[2]
    vig[..., 3] = (v_alpha * 255).astype(np.uint8)
    return Image.alpha_composite(base, Image.fromarray(vig, mode="RGBA"))


# ---------------------------------------------------------------------------
# Pre-rendered 2x Anti-Aliased Expressive Cozy 2D Character Rig (6 Moods + Blink!)
# ---------------------------------------------------------------------------

def _draw_smooth_arc_line(
    d: ImageDraw.ImageDraw,
    pts: list[tuple[float, float]],
    color: tuple[int, int, int, int],
    width: int,
) -> None:
    if len(pts) < 2:
        return
    d.line(pts, fill=color, width=width, joint="curve")
    r = width / 2.0
    for px, py in (pts[0], pts[-1]):
        d.ellipse([px - r, py - r, px + r, py + r], fill=color)


def _quad_curve(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    steps: int = 16,
) -> list[tuple[float, float]]:
    pts = []
    for i in range(steps + 1):
        t = i / float(steps)
        mt = 1.0 - t
        x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
        y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
        pts.append((x, y))
    return pts


def _build_expressive_character(
    height_px: int,
    mood: str = "deep_focus",  # sleepy_scroll | overwhelmed | protected_calm | deep_focus | inspired_wonder | peaceful_rest
    prop: str = "journal",     # journal | phone | none
    blink: bool = False,
    body_top: tuple[int, int, int] = (132, 118, 208),
    body_bot: tuple[int, int, int] = (92, 80, 166),
    outline_col: tuple[int, int, int] = (50, 40, 102),
    rim_light: str = "warm",   # warm | blue | cyan
) -> Image.Image:
    """Render a charming, expressive 2x anti-aliased cozy 2D character matching referensi.mp4's palette."""
    ss = 2
    w = int(round(height_px * 0.78))
    h = height_px
    cw, ch = w * ss, h * ss
    img = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cw / 2.0

    skin = (244, 214, 192)
    skin_shadow = (224, 186, 164)
    hair_dark = (38, 30, 72)
    hair_hi = (78, 66, 132)
    ink_face = (36, 28, 66, 255)

    # 1. Soft ground shadow
    draw.ellipse([cx - cw * 0.34, ch - 26, cx + cw * 0.34, ch - 4], fill=(8, 6, 16, 135))

    # 2. Cozy turtleneck/hoodie bell-dome torso (rich lavender gradient)
    body_top_y = ch * 0.42
    body_bot_y = ch - 18
    body_half_bot = cw * 0.32
    left_pts, right_pts = [], []
    for i in range(37):
        u = i / 36.0
        y = _lerp(body_top_y, body_bot_y, u)
        hw = body_half_bot * (0.34 + 0.66 * (math.sin(u * math.pi * 0.5) ** 0.62))
        left_pts.append((cx - hw, y))
        right_pts.append((cx + hw, y))
    poly = left_pts + list(reversed(right_pts))

    mask = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    g_arr = np.zeros((ch, cw, 4), dtype=np.uint8)
    ys = np.clip((np.arange(ch)[:, None] - body_top_y) / max(body_bot_y - body_top_y, 1.0), 0.0, 1.0)
    for c_i in range(3):
        g_arr[..., c_i] = (body_top[c_i] + (body_bot[c_i] - body_top[c_i]) * ys).astype(np.uint8)
    g_arr[..., 3] = 255
    img.paste(Image.fromarray(g_arr, mode="RGBA"), (0, 0), mask)
    draw = ImageDraw.Draw(img)
    draw.line(poly + [poly[0]], fill=(*outline_col, 225), width=5, joint="curve")

    # Subtle hoodie pocket / cozy sleeve fold crease on left torso for depth
    fold = _quad_curve((cx - body_half_bot * 0.56, body_top_y + 72), (cx - body_half_bot * 0.68, body_top_y + 150), (cx - body_half_bot * 0.44, body_top_y + 210))
    _draw_smooth_arc_line(draw, fold, (*outline_col, 110), 4)

    # Cozy turtleneck collar + subtle warm neck
    neck_w = cw * 0.11
    draw.rounded_rectangle([cx - neck_w, body_top_y - 26, cx + neck_w, body_top_y + 14], radius=12, fill=(*skin_shadow, 255))
    collar_w = cw * 0.165
    draw.rounded_rectangle(
        [cx - collar_w, body_top_y - 6, cx + collar_w, body_top_y + 30],
        radius=16,
        fill=(min(body_top[0] + 14, 255), min(body_top[1] + 12, 255), min(body_top[2] + 16, 255), 255),
        outline=(*outline_col, 220),
        width=4,
    )

    # 3. Smooth rounded back hair silhouette behind head
    head_r = cw * 0.235
    head_cx = cx
    head_cy = ch * 0.245
    draw.ellipse(
        [head_cx - head_r * 1.13, head_cy - head_r * 1.14, head_cx + head_r * 1.13, head_cy + head_r * 0.94],
        fill=(*hair_dark, 255),
    )

    # Cute subtle ears
    ear_r = head_r * 0.20
    for ex in (head_cx - head_r * 0.96, head_cx + head_r * 0.96):
        draw.ellipse([ex - ear_r, head_cy + 4 - ear_r, ex + ear_r, head_cy + 4 + ear_r], fill=(*skin_shadow, 255), outline=(*outline_col, 160), width=3)

    # 4. Warm expressive face oval
    face_rx = head_r * 0.98
    face_ry = head_r * 0.94
    face_box = [head_cx - face_rx, head_cy - face_ry * 0.92, head_cx + face_rx, head_cy + face_ry]
    draw.ellipse(face_box, fill=(*skin, 255), outline=(*outline_col, 195), width=4)

    # Soft blurred rim-light glow + rosy cheeks STRICTLY CLIPPED to inside the face oval (ZERO spillover!)
    face_mask = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(face_mask).ellipse([face_box[0] + 3, face_box[1] + 3, face_box[2] - 3, face_box[3] - 3], fill=255)
    rim_layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim_layer)
    if rim_light == "blue":
        rd.ellipse([head_cx + face_rx * 0.12, head_cy - face_ry * 0.25, head_cx + face_rx * 1.25, head_cy + face_ry * 1.05], fill=(138, 206, 255, 52))
    elif rim_light == "cyan":
        rd.ellipse([head_cx - face_rx * 0.95, head_cy - face_ry * 0.75, head_cx + face_rx * 0.95, head_cy + face_ry * 0.95], fill=(138, 224, 232, 32))
    else:
        rd.ellipse([head_cx - face_rx * 1.05, head_cy - face_ry * 0.95, head_cx + face_rx * 0.15, head_cy + face_ry * 0.25], fill=(254, 224, 146, 46))
    blush_r = head_r * 0.22
    blush_y = head_cy + face_ry * 0.28
    for bx in (head_cx - face_rx * 0.56, head_cx + face_rx * 0.56):
        rd.ellipse([bx - blush_r, blush_y - blush_r * 0.65, bx + blush_r, blush_y + blush_r * 0.65], fill=(232, 136, 138, 86))
    rim_layer = rim_layer.filter(ImageFilter.GaussianBlur(radius=20))
    # Clip blurred glow cleanly to face oval!
    rim_arr = np.asarray(rim_layer).copy()
    mask_arr = np.asarray(face_mask, dtype=np.float32) / 255.0
    rim_arr[..., 3] = (rim_arr[..., 3].astype(np.float32) * mask_arr).astype(np.uint8)
    img = Image.alpha_composite(img, Image.fromarray(rim_arr, mode="RGBA"))
    draw = ImageDraw.Draw(img)

    # 5. Silky smooth curved hair crown + soft side-swept fringe bangs (ZERO angular corners!)
    hair_crown = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hair_crown)
    # Smooth upper oval cap
    hd.ellipse([head_cx - head_r * 1.12, head_cy - head_r * 1.18, head_cx + head_r * 1.12, head_cy + head_r * 0.52], fill=(*hair_dark, 255))
    # Carve out soft smooth forehead fringe curve using clean mask
    fringe_cut = Image.new("L", (cw, ch), 255)
    fcd = ImageDraw.Draw(fringe_cut)
    forehead_open = [
        (head_cx - head_r * 0.96, head_cy + head_r * 0.60),
        (head_cx - head_r * 0.96, head_cy - head_r * 0.12),
        *_quad_curve((head_cx - head_r * 0.92, head_cy - head_r * 0.24), (head_cx - head_r * 0.52, head_cy - head_r * 0.50), (head_cx - head_r * 0.12, head_cy - head_r * 0.30), steps=14),
        *_quad_curve((head_cx - head_r * 0.12, head_cy - head_r * 0.30), (head_cx + head_r * 0.16, head_cy - head_r * 0.56), (head_cx + head_r * 0.52, head_cy - head_r * 0.32), steps=14),
        *_quad_curve((head_cx + head_r * 0.52, head_cy - head_r * 0.32), (head_cx + head_r * 0.78, head_cy - head_r * 0.44), (head_cx + head_r * 0.94, head_cy - head_r * 0.12), steps=12),
        (head_cx + head_r * 0.96, head_cy + head_r * 0.60),
    ]
    fcd.polygon(forehead_open, fill=0)
    hc_arr = np.asarray(hair_crown).copy()
    hc_arr[..., 3] = np.minimum(hc_arr[..., 3], np.asarray(fringe_cut))
    img = Image.alpha_composite(img, Image.fromarray(hc_arr, mode="RGBA"))
    draw = ImageDraw.Draw(img)
    # Subtle lavender sheen arc on hair crown
    sheen = _quad_curve(
        (head_cx - head_r * 0.52, head_cy - head_r * 0.80),
        (head_cx - head_r * 0.04, head_cy - head_r * 1.00),
        (head_cx + head_r * 0.46, head_cy - head_r * 0.78),
    )
    _draw_smooth_arc_line(draw, sheen, (*hair_hi, 175), max(int(round(head_r * 0.075)), 4))

    # 6. EXPRESSIVE EYES, EYEBROWS & MOUTH (Tailored to each of the 6 emotional moods!)
    eye_dx = face_rx * 0.36
    eye_y = head_cy + face_ry * 0.06
    eye_r = head_r * 0.145
    brow_y = eye_y - eye_r * 1.95
    mouth_y = head_cy + face_ry * 0.48
    sw_face = max(int(round(head_r * 0.075)), 4)

    # Gaze offset per mood
    gaze_x, gaze_y = 0.0, 0.0
    if mood == "sleepy_scroll":
        gaze_x, gaze_y = eye_r * 0.28, eye_r * 0.28
    elif mood == "overwhelmed":
        gaze_x, gaze_y = eye_r * 0.16, -eye_r * 0.10
    elif mood == "inspired_wonder":
        gaze_x, gaze_y = 0.0, -eye_r * 0.28
    elif mood == "deep_focus":
        gaze_x, gaze_y = eye_r * 0.18, 0.0

    # --- EYES ---
    if mood == "protected_calm" or (blink and mood != "peaceful_rest"):
        # Joyful happy closed-arc eyes (^ ^) or natural quick blink
        for sign in (-1, 1):
            ex = head_cx + sign * eye_dx
            curve_dir = -1.0 if mood == "protected_calm" else 0.75
            pts = _quad_curve(
                (ex - eye_r * 1.05, eye_y + (3 if curve_dir < 0 else -2)),
                (ex, eye_y + eye_r * 0.95 * curve_dir),
                (ex + eye_r * 1.05, eye_y + (3 if curve_dir < 0 else -2)),
            )
            _draw_smooth_arc_line(draw, pts, ink_face, sw_face)
    elif mood == "peaceful_rest":
        # Distinct tranquil evening relaxed eyelids (soft downward resting curve u u!)
        for sign in (-1, 1):
            ex = head_cx + sign * eye_dx
            pts = _quad_curve(
                (ex - eye_r * 1.05, eye_y - 3),
                (ex, eye_y + eye_r * 0.85),
                (ex + eye_r * 1.05, eye_y - 3),
            )
            _draw_smooth_arc_line(draw, pts, ink_face, sw_face)
    else:
        for sign in (-1, 1):
            ex = head_cx + sign * eye_dx
            er_x = eye_r * (1.14 if mood == "overwhelmed" else 0.98)
            er_y = eye_r * (1.18 if mood in ("overwhelmed", "inspired_wonder") else 1.08)
            # Dark expressive iris
            draw.ellipse([ex - er_x + gaze_x * 0.5, eye_y - er_y + gaze_y * 0.5, ex + er_x + gaze_x * 0.5, eye_y + er_y + gaze_y * 0.5], fill=ink_face)
            # Bright specular catchlight dot (makes character feel ALIVE!)
            cr = max(eye_r * (0.42 if mood == "inspired_wonder" else 0.34), 3.0)
            draw.ellipse([ex - er_x * 0.36 + gaze_x * 0.5 - cr * 0.5, eye_y - er_y * 0.38 + gaze_y * 0.5 - cr * 0.5, ex - er_x * 0.36 + gaze_x * 0.5 + cr * 0.5, eye_y - er_y * 0.38 + gaze_y * 0.5 + cr * 0.5], fill=(255, 255, 255, 245))
            if mood == "inspired_wonder":
                # Extra tiny secondary sparkle dot!
                draw.ellipse([ex + er_x * 0.24, eye_y + er_y * 0.16, ex + er_x * 0.24 + cr * 0.55, eye_y + er_y * 0.16 + cr * 0.55], fill=(255, 248, 210, 230))
            if mood == "sleepy_scroll":
                # Heavy drooping half-eyelid over top half of eye + subtle under-eye tired tint
                draw.rectangle([ex - er_x * 1.2, eye_y - er_y * 1.3, ex + er_x * 1.2, eye_y - er_y * 0.08], fill=(*skin, 255))
                draw.line([(ex - er_x * 1.1, eye_y - er_y * 0.08), (ex + er_x * 1.1, eye_y - er_y * 0.08)], fill=ink_face, width=sw_face)

    # --- EYEBROWS ---
    for sign in (-1, 1):
        ex = head_cx + sign * eye_dx
        bw = eye_r * 1.15
        if mood == "overwhelmed":
            # Tilted worried eyebrows (inner corners lifted!)
            p0 = (ex - sign * bw, brow_y - eye_r * 0.55)
            p1 = (ex, brow_y - eye_r * 0.15)
            p2 = (ex + sign * bw, brow_y + eye_r * 0.30)
        elif mood == "sleepy_scroll":
            # Drooping flat tired eyebrows
            p0 = (ex - bw, brow_y + eye_r * 0.22)
            p1 = (ex, brow_y + eye_r * 0.10)
            p2 = (ex + bw, brow_y + eye_r * 0.25)
        elif mood in ("inspired_wonder", "deep_focus"):
            # Gently lifted optimistic arches
            p0 = (ex - bw, brow_y - eye_r * 0.05)
            p1 = (ex, brow_y - eye_r * 0.58)
            p2 = (ex + bw, brow_y - eye_r * 0.05)
        else:
            # Calm relaxed soft arches
            p0 = (ex - bw, brow_y + eye_r * 0.05)
            p1 = (ex, brow_y - eye_r * 0.35)
            p2 = (ex + bw, brow_y + eye_r * 0.05)
        _draw_smooth_arc_line(draw, _quad_curve(p0, p1, p2), (*hair_dark, 235), max(sw_face - 1, 3))

    # --- MOUTH ---
    mw = face_rx * 0.26
    if mood == "sleepy_scroll":
        # Small tired slightly downward/flat mouth
        pts = _quad_curve((head_cx - mw * 0.72, mouth_y + 2), (head_cx, mouth_y - 4), (head_cx + mw * 0.72, mouth_y + 3))
        _draw_smooth_arc_line(draw, pts, ink_face, sw_face)
    elif mood == "overwhelmed":
        # Expressive wavy anxious mouth + tiny cyan sweat-drop on temple!
        pts = [
            (head_cx - mw * 0.85, mouth_y + 3),
            (head_cx - mw * 0.35, mouth_y - 7),
            (head_cx + mw * 0.35, mouth_y + 7),
            (head_cx + mw * 0.85, mouth_y - 3),
        ]
        _draw_smooth_arc_line(draw, pts, ink_face, sw_face)
        # Cute subtle anxiety sweat drop upper-left cheek
        sx, sy = head_cx - face_rx * 0.78, head_cy - face_ry * 0.18
        draw.polygon([(sx, sy - 18), (sx - 10, sy + 2), (sx + 10, sy + 2)], fill=(138, 210, 248, 230))
        draw.ellipse([sx - 10, sy - 6, sx + 10, sy + 12], fill=(138, 210, 248, 230))
    elif mood in ("deep_focus", "inspired_wonder"):
        # Warm clear gentle smile
        pts = _quad_curve((head_cx - mw * 0.92, mouth_y - 4), (head_cx, mouth_y + mw * 0.62), (head_cx + mw * 0.92, mouth_y - 4))
        _draw_smooth_arc_line(draw, pts, ink_face, sw_face)
    else:
        # Serene peaceful closed smile
        pts = _quad_curve((head_cx - mw * 0.82, mouth_y - 2), (head_cx, mouth_y + mw * 0.48), (head_cx + mw * 0.82, mouth_y - 2))
        _draw_smooth_arc_line(draw, pts, ink_face, sw_face)

    # 7. Articulated Cozy Sleeves, Hands & Props (Phone or Warm Amber Journal!)
    hand_r = cw * 0.055
    if prop == "phone":
        # Glowing smartphone held up right in front-right with cute rounded hand gripping it!
        pw, ph = cw * 0.155, ch * 0.135
        px = cx + body_half_bot * 0.44
        py = body_top_y + (body_bot_y - body_top_y) * 0.14
        # Arm curving from shoulder to phone
        arm_pts = _quad_curve((cx + body_half_bot * 0.45, body_top_y + 42), (cx + body_half_bot * 0.72, py + ph * 0.75), (px + 10, py + ph * 0.68))
        _draw_smooth_arc_line(draw, arm_pts, (*body_top, 255), int(cw * 0.09))
        draw.rounded_rectangle([px, py, px + pw, py + ph], radius=14, fill=(32, 36, 56, 255), outline=(160, 186, 232, 235), width=4)
        draw.rounded_rectangle([px + 8, py + 10, px + pw - 8, py + ph - 12], radius=7, fill=(176, 228, 255, 255))
        # Cute warm hand holding phone side
        draw.ellipse([px - hand_r * 0.5, py + ph * 0.48, px + hand_r * 1.2, py + ph * 0.48 + hand_r * 1.5], fill=(*skin, 255), outline=(*outline_col, 190), width=3)
    elif prop == "journal":
        # Warm amber notebook tucked calmly under arm with cute resting hand!
        nb_w, nb_h = cw * 0.21, ch * 0.145
        nb_x = cx + body_half_bot * 0.46
        nb_y = body_top_y + (body_bot_y - body_top_y) * 0.34
        draw.rounded_rectangle([nb_x, nb_y, nb_x + nb_w, nb_y + nb_h], radius=12, fill=(214, 154, 62, 255), outline=(146, 98, 32, 235), width=4)
        # Bookmark ribbon detail
        draw.rectangle([nb_x + nb_w * 0.68, nb_y + 4, nb_x + nb_w * 0.78, nb_y + nb_h - 4], fill=(182, 92, 82, 210))
        # Cute warm hand resting on front of journal
        draw.ellipse([nb_x - hand_r * 0.4, nb_y + nb_h * 0.30, nb_x + hand_r * 1.35, nb_y + nb_h * 0.30 + hand_r * 1.45], fill=(*skin, 255), outline=(*outline_col, 190), width=3)

    return _fast_downscale_rgba(img, w, h)


def _pick_character_frame(pair: tuple[Image.Image, Image.Image], t_sec: float, sway_deg: float = 0.0) -> Image.Image:
    """Natural 30fps blink cycle (~every 3.3s for 0.14s) + optional micro expressive head/body tilt."""
    cyc = (t_sec + 1.1) % 3.35
    sprite = pair[1] if (cyc > 3.21) else pair[0]
    if abs(sway_deg) > 0.15:
        return sprite.rotate(sway_deg, resample=Image.Resampling.BILINEAR, expand=False)
    return sprite


# ---------------------------------------------------------------------------
# 4 Distinct Pre-rendered 2x HabitSains Cozy Diorama Sets
# ---------------------------------------------------------------------------

def _build_bedroom_diorama(width: int, height: int, is_evening: bool = False) -> tuple[Image.Image, dict[str, Any]]:
    """Cozy midnight-indigo bedroom diorama (bed, pillow, nightstand, lamp, dawn/moon window, far-away phone)."""
    base = _build_striped_midnight_wall(width, height, floor_frac=0.625)
    ss = 2
    cw, ch = width * ss, height * ss
    layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    floor_y = ch * 0.625

    # Floor & soft oval rug
    d.rectangle([0, floor_y, cw, ch], fill=(16, 12, 28, 255))
    d.line([(0, floor_y), (cw, floor_y)], fill=(48, 39, 76, 220), width=6)
    d.ellipse([cw * 0.08, floor_y + 24, cw * 0.90, floor_y + 150], fill=(32, 25, 54, 210))

    # Arched bedroom window on right (soft lavender dawn glow in morning, calm crescent moon in evening)
    wx0, wx1 = cw * 0.66, cw * 0.88
    wy0, wy1 = ch * 0.16, ch * 0.435
    wr = (wx1 - wx0) / 2.0
    d.pieslice([wx0, wy0, wx1, wy0 + wr * 2], start=180, end=360, fill=(24, 22, 54, 255))
    d.rectangle([wx0, wy0 + wr, wx1, wy1], fill=(24, 22, 54, 255))
    if not is_evening:
        # Soft early-dawn plum/amber band at bottom of window pane
        d.rectangle([wx0 + 14, wy1 - 150, wx1 - 14, wy1 - 10], fill=(66, 52, 92, 210))
        d.rectangle([wx0 + 14, wy1 - 65, wx1 - 14, wy1 - 10], fill=(142, 96, 86, 165))
    # Crescent moon & stars
    mcx, mcy, mr = wx0 + wr * 1.25, wy0 + wr * 0.72, 42 * ss / 1.4
    d.ellipse([mcx - mr, mcy - mr, mcx + mr, mcy + mr], fill=(248, 232, 168, 240))
    d.ellipse([mcx - mr * 0.55, mcy - mr * 1.15, mcx + mr * 1.35, mcy + mr * 0.75], fill=(24, 22, 54, 255))
    for stx, sty in [(wx0 + 115, wy0 + 250), (wx0 + 260, wy0 + 195), (wx0 + 145, wy0 + 440)]:
        d.ellipse([stx - 5, sty - 5, stx + 5, sty + 5], fill=(240, 236, 220, 220))
    # Wooden frame
    fw = 18
    d.arc([wx0, wy0, wx1, wy0 + wr * 2], start=180, end=360, fill=(*WOOD_MID, 255), width=fw)
    d.line([(wx0 + fw // 2, wy0 + wr), (wx0 + fw // 2, wy1)], fill=(*WOOD_MID, 255), width=fw)
    d.line([(wx1 - fw // 2, wy0 + wr), (wx1 - fw // 2, wy1)], fill=(*WOOD_MID, 255), width=fw)
    d.line([(wx0, wy1), (wx1, wy1)], fill=(*WOOD_MID, 255), width=fw)
    d.line([((wx0 + wx1) / 2, wy0 + 10), ((wx0 + wx1) / 2, wy1)], fill=(*WOOD_DARK, 255), width=10)
    d.line([(wx0 + 10, wy0 + (wy1 - wy0) * 0.56), (wx1 - 10, wy0 + (wy1 - wy0) * 0.56)], fill=(*WOOD_DARK, 255), width=10)

    # Cozy minimalist bed (left-center!)
    bx0, bx1 = cw * 0.07, cw * 0.58
    by_mattress = ch * 0.535
    # Wooden headboard
    d.rounded_rectangle([bx0, ch * 0.435, bx0 + 46, floor_y + 4], radius=16, fill=(*WOOD_DARK, 255))
    # Footboard & side frame
    d.rounded_rectangle([bx1 - 32, by_mattress + 18, bx1, floor_y + 4], radius=12, fill=(*WOOD_DARK, 255))
    d.rounded_rectangle([bx0 + 26, by_mattress + 48, bx1 - 12, by_mattress + 112], radius=14, fill=(*WOOD_MID, 255))
    # Plush pillow
    d.rounded_rectangle([bx0 + 52, by_mattress - 46, bx0 + 258, by_mattress + 26], radius=34, fill=(214, 206, 224, 255))
    # Cozy indigo duvet blanket draped across mattress
    d.rounded_rectangle([bx0 + 40, by_mattress - 6, bx1 - 16, by_mattress + 78], radius=28, fill=(84, 68, 134, 255))
    d.rounded_rectangle([bx0 + 215, by_mattress - 10, bx1 - 16, by_mattress + 82], radius=24, fill=(68, 54, 112, 255))

    # Bedside wooden nightstand on far right (under window!)
    nx0, nx1 = cw * 0.69, cw * 0.90
    ny0 = ch * 0.505
    d.rounded_rectangle([nx0, ny0, nx1, floor_y - 16], radius=16, fill=(*WOOD_DARK, 255))
    d.rounded_rectangle([nx0 - 12, ny0 - 8, nx1 + 12, ny0 + 18], radius=10, fill=(*WOOD_MID, 255))
    # Drawer line & tiny gold knob
    d.rounded_rectangle([nx0 + 24, ny0 + 36, nx1 - 24, ny0 + 132], radius=10, fill=(86, 56, 30, 255))
    d.ellipse([(nx0 + nx1) / 2 - 10, ny0 + 74, (nx0 + nx1) / 2 + 10, ny0 + 94], fill=(*GOLD_GLOW, 255))
    # Small warm bedside lamp on nightstand
    lx, ly = (nx0 + nx1) / 2 + 34, ny0 - 8
    d.rectangle([lx - 12, ly - 58, lx + 12, ly], fill=(122, 108, 146, 255))
    d.polygon([(lx - 44, ly - 118), (lx + 44, ly - 118), (lx + 66, ly - 54), (lx - 66, ly - 54)], fill=(208, 144, 66, 255))

    if is_evening:
        # Phone resting peacefully FACE-DOWN far away on nightstand!
        d.rounded_rectangle([nx0 + 26, ny0 - 20, nx0 + 102, ny0 - 6], radius=6, fill=(58, 54, 84, 255), outline=(140, 144, 178, 220), width=3)

    # Hanging wall art above bed
    d.rectangle([cw * 0.25, ch * 0.28, cw * 0.42, ch * 0.37], fill=(52, 42, 82, 255), outline=(*WOOD_MID, 255), width=12)
    d.arc([cw * 0.28, ch * 0.30, cw * 0.39, ch * 0.36], start=180, end=360, fill=(214, 172, 92, 220), width=8)

    down = _fast_downscale_rgba(layer, width, height)
    base = Image.alpha_composite(base, down)
    base = _apply_bottom_velvet_vignette(base, start_frac=0.635)

    # Warm glow around bedside lamp
    gl_r = int(width * (0.28 if is_evening else 0.16))
    _paste_alpha(base, _make_radial_glow(gl_r, GOLD_GLOW, 86 if is_evening else 46), int(lx / ss) - gl_r, int((ly - 72) / ss) - gl_r)

    meta = {
        "floor_y": int(floor_y / ss),
        "bed_seat": (int((bx0 + bx1) * 0.56 / ss), int((by_mattress + 60) / ss)),
    }
    return base, meta


def _build_study_desk_diorama(width: int, height: int, dawn_window: bool = True, laptop_open: bool = False) -> tuple[Image.Image, dict[str, Any]]:
    """Cozy striped midnight-purple HabitSains study room with desk, pendant lamp, pastel books, coffee & journal!"""
    base = _build_striped_midnight_wall(width, height, floor_frac=0.625)
    ss = 2
    cw, ch = width * ss, height * ss
    layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    floor_y = ch * 0.625

    # Floor & oval rug
    d.rectangle([0, floor_y, cw, ch], fill=(16, 12, 28, 255))
    d.line([(0, floor_y), (cw, floor_y)], fill=(48, 39, 76, 220), width=6)
    d.ellipse([cw * 0.08, floor_y + 24, cw * 0.90, floor_y + 150], fill=(34, 26, 56, 200))

    # Arched window on right (warm lavender-gold dawn glow OR starry night!)
    wx0, wx1 = cw * 0.655, cw * 0.875
    wy0, wy1 = ch * 0.145, ch * 0.435
    wr = (wx1 - wx0) / 2.0
    d.pieslice([wx0, wy0, wx1, wy0 + wr * 2], start=180, end=360, fill=(24, 22, 54, 255))
    d.rectangle([wx0, wy0 + wr, wx1, wy1], fill=(24, 22, 54, 255))
    if dawn_window:
        d.rectangle([wx0 + 12, wy1 - 210, wx1 - 12, wy1 - 8], fill=(66, 50, 96, 220))
        d.rectangle([wx0 + 12, wy1 - 115, wx1 - 12, wy1 - 8], fill=(156, 104, 84, 190))
        d.pieslice([wx0 + 68, wy1 - 74, wx1 - 68, wy1 + 74], start=180, end=360, fill=(246, 206, 118, 235))
    else:
        mcx, mcy, mr = wx0 + wr * 1.25, wy0 + wr * 0.72, 42 * ss / 1.4
        d.ellipse([mcx - mr, mcy - mr, mcx + mr, mcy + mr], fill=(248, 232, 168, 255))
        d.ellipse([mcx - mr * 0.55, mcy - mr * 1.15, mcx + mr * 1.35, mcy + mr * 0.75], fill=(24, 22, 54, 255))
    for stx, sty in [(wx0 + 125, wy0 + 230), (wx0 + 275, wy0 + 185), (wx0 + 145, wy0 + 365)]:
        d.ellipse([stx - 5, sty - 5, stx + 5, sty + 5], fill=(240, 236, 220, 215))

    fw = 18
    d.arc([wx0, wy0, wx1, wy0 + wr * 2], start=180, end=360, fill=(*WOOD_MID, 255), width=fw)
    d.line([(wx0 + fw // 2, wy0 + wr), (wx0 + fw // 2, wy1)], fill=(*WOOD_MID, 255), width=fw)
    d.line([(wx1 - fw // 2, wy0 + wr), (wx1 - fw // 2, wy1)], fill=(*WOOD_MID, 255), width=fw)
    d.line([(wx0, wy1), (wx1, wy1)], fill=(*WOOD_MID, 255), width=fw)
    d.line([((wx0 + wx1) / 2, wy0 + 10), ((wx0 + wx1) / 2, wy1)], fill=(*WOOD_DARK, 255), width=10)
    d.line([(wx0 + 10, wy0 + (wy1 - wy0) * 0.56), (wx1 - 10, wy0 + (wy1 - wy0) * 0.56)], fill=(*WOOD_DARK, 255), width=10)

    # Floating wooden bookshelf + pastel books + potted sage plant (left)
    sh_x0, sh_x1, sh_y = cw * 0.055, cw * 0.365, ch * 0.375
    d.rounded_rectangle([sh_x0, sh_y, sh_x1, sh_y + 20], radius=8, fill=(*WOOD_MID, 255))
    for bx, bw, bh, bcol in [
        (sh_x0 + 38, 42, 124, (186, 108, 122)),
        (sh_x0 + 90, 40, 102, (112, 178, 188)),
        (sh_x0 + 140, 42, 118, (226, 186, 94)),
        (sh_x0 + 192, 36, 88, (152, 126, 198)),
    ]:
        d.rounded_rectangle([bx, sh_y - bh, bx + bw, sh_y], radius=6, fill=(*bcol, 255))
    px = sh_x1 - 118
    d.rounded_rectangle([px, sh_y - 68, px + 90, sh_y], radius=14, fill=(182, 134, 58, 255))
    d.polygon([(px + 45, sh_y - 68), (px + 12, sh_y - 156), (px + 42, sh_y - 122)], fill=(102, 168, 124, 255))
    d.polygon([(px + 45, sh_y - 68), (px + 82, sh_y - 168), (px + 50, sh_y - 120)], fill=(122, 186, 138, 255))

    # Minimalist framed golden-sun wall art centered
    fx0, fy0, fx1, fy1 = cw * 0.435, ch * 0.265, cw * 0.568, ch * 0.368
    d.rectangle([fx0, fy0, fx1, fy1], fill=(56, 46, 86, 255), outline=(*WOOD_MID, 255), width=14)
    d.ellipse([fx0 + (fx1 - fx0) * 0.30, fy0 + (fy1 - fy0) * 0.30, fx1 - (fx1 - fx0) * 0.30, fy1 - (fy1 - fy0) * 0.30], fill=(214, 170, 86, 255))

    # Minimalist warm wooden study desk on right-center (replaces empty couch for HabitSains!)
    dx0, dx1 = cw * 0.48, cw * 0.93
    desk_y = ch * 0.532
    # Desk legs
    d.rounded_rectangle([dx0 + 26, desk_y + 20, dx0 + 54, floor_y + 4], radius=8, fill=(*WOOD_DARK, 255))
    d.rounded_rectangle([dx1 - 54, desk_y + 20, dx1 - 26, floor_y + 4], radius=8, fill=(*WOOD_DARK, 255))
    # Desk tabletop + sleek under-drawer
    d.rounded_rectangle([dx0 + 54, desk_y + 22, dx1 - 54, desk_y + 62], radius=8, fill=(78, 52, 32, 255))
    d.rounded_rectangle([dx0, desk_y, dx1, desk_y + 28], radius=12, fill=(*WOOD_MID, 255))

    # Props on desk: open cream journal + pen + ceramic coffee mug (or glowing laptop!)
    coffee_x = dx1 - 155
    if laptop_open:
        # Open laptop casting cool light on desk
        lx0, lx1 = dx0 + 120, dx0 + 440
        d.rounded_rectangle([lx0 + 24, desk_y - 165, lx1 - 24, desk_y - 6], radius=14, fill=(64, 62, 92, 255), outline=(120, 128, 168, 255), width=6)
        d.rounded_rectangle([lx0 + 40, desk_y - 148, lx1 - 40, desk_y - 22], radius=8, fill=(142, 198, 244, 240))
        d.rounded_rectangle([lx0, desk_y - 12, lx1, desk_y + 2], radius=6, fill=(138, 142, 174, 255))
    else:
        # Open cream paper journal + minimalist pen
        jx0, jx1 = dx0 + 120, dx0 + 390
        d.rounded_rectangle([jx0, desk_y - 16, jx1, desk_y + 2], radius=6, fill=(242, 236, 222, 255))
        d.line([((jx0 + jx1) / 2, desk_y - 16), ((jx0 + jx1) / 2, desk_y + 2)], fill=(186, 176, 162, 255), width=4)
        # Small glowing amber desk hourglass / timer next to journal
        d.rounded_rectangle([dx0 + 420, desk_y - 84, dx0 + 482, desk_y], radius=10, fill=(58, 48, 88, 255), outline=(*GOLD_GLOW, 235), width=5)

    # Warm ceramic coffee mug on right side of desk!
    d.rounded_rectangle([coffee_x, desk_y - 74, coffee_x + 76, desk_y + 2], radius=16, fill=(238, 232, 220, 255))
    d.arc([coffee_x + 56, desk_y - 60, coffee_x + 98, desk_y - 16], start=-90, end=90, fill=(238, 232, 220, 255), width=10)

    # Hanging amber pendant lamp (left side)
    lamp_x = cw * 0.295
    lamp_y = ch * 0.215
    d.line([(lamp_x, 0), (lamp_x, lamp_y)], fill=(154, 146, 174, 210), width=6)
    d.polygon([(lamp_x - 56, lamp_y), (lamp_x + 56, lamp_y), (lamp_x + 92, lamp_y + 90), (lamp_x - 92, lamp_y + 90)], fill=(208, 142, 64, 255))
    d.ellipse([lamp_x - 24, lamp_y + 76, lamp_x + 24, lamp_y + 112], fill=(254, 232, 148, 255))

    down = _fast_downscale_rgba(layer, width, height)
    base = Image.alpha_composite(base, down)
    base = _apply_bottom_velvet_vignette(base, start_frac=0.635)

    meta = {
        "lamp_pos": (int(lamp_x / ss), int((lamp_y + 94) / ss)),
        "floor_y": int(floor_y / ss),
        "coffee_pos": (int((coffee_x + 38) / ss), int((desk_y - 78) / ss)),
        "laptop_pos": (int((dx0 + 280) / ss), int((desk_y - 95) / ss)),
    }
    return base, meta


def _build_neural_sky_diorama(width: int, height: int) -> tuple[Image.Image, dict[str, Any]]:
    """Cozy midnight observatory dusk horizon for neural pathways / neuroplasticity & habit protocol scenes."""
    base = _build_striped_midnight_wall(width, height, floor_frac=0.64)
    ss = 2
    cw, ch = width * ss, height * ss
    layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    floor_y = ch * 0.625

    # Soft rolling hills silhouette + calm horizon floor
    d.ellipse([-cw * 0.15, floor_y - 70, cw * 0.58, floor_y + 220], fill=(26, 20, 48, 255))
    d.ellipse([cw * 0.42, floor_y - 90, cw * 1.18, floor_y + 220], fill=(22, 17, 42, 255))
    d.rectangle([0, floor_y, cw, ch], fill=(14, 11, 26, 255))

    down = _fast_downscale_rgba(layer, width, height)
    base = Image.alpha_composite(base, down)
    base = _apply_bottom_velvet_vignette(base, start_frac=0.635)
    return base, {"floor_y": int(floor_y / ss)}


# ---------------------------------------------------------------------------
# Animated Interactive Micro-Sprites (Notification Bubbles, Coffee Steam, Neural Arc)
# ---------------------------------------------------------------------------

def _draw_distraction_badge(img: Image.Image, kind: str, cx: int, cy: int, size: int, alpha: float) -> None:
    """Draw cute minimal floating social/notification icon badges (play, bell, heart, chat)."""
    if alpha <= 0.03 or size < 10:
        return
    pad = 8
    ov = Image.new("RGBA", (size + pad * 2, size + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    colors = {
        "play": ((226, 110, 128), (255, 245, 245)),
        "bell": ((236, 182, 74), (36, 26, 18)),
        "heart": ((224, 124, 152), (255, 245, 248)),
        "chat": ((118, 186, 232), (245, 250, 255)),
    }
    bg_c, fg_c = colors.get(kind, colors["play"])
    d.rounded_rectangle([pad, pad, pad + size, pad + size], radius=size // 3, fill=(*bg_c, int(235 * alpha)))
    mc = pad + size // 2
    r = size // 4
    if kind == "play":
        d.polygon([(mc - r // 2 + 2, mc - r), (mc - r // 2 + 2, mc + r), (mc + r + 2, mc)], fill=(*fg_c, int(250 * alpha)))
    elif kind == "bell":
        d.pieslice([mc - r, mc - r, mc + r, mc + r], start=180, end=360, fill=(*fg_c, int(250 * alpha)))
        d.rectangle([mc - r, mc, mc + r, mc + r // 2], fill=(*fg_c, int(250 * alpha)))
        d.ellipse([mc - 4, mc + r // 2, mc + 4, mc + r], fill=(*fg_c, int(250 * alpha)))
    elif kind == "heart":
        d.ellipse([mc - r, mc - r // 2, mc, mc + r // 2], fill=(*fg_c, int(250 * alpha)))
        d.ellipse([mc, mc - r // 2, mc + r, mc + r // 2], fill=(*fg_c, int(250 * alpha)))
        d.polygon([(mc - r, mc + 2), (mc + r, mc + 2), (mc, mc + r + 2)], fill=(*fg_c, int(250 * alpha)))
    else:
        d.rounded_rectangle([mc - r, mc - r + 2, mc + r, mc + r - 4], radius=6, fill=(*fg_c, int(250 * alpha)))
        d.ellipse([mc - 6, mc - 3, mc - 1, mc + 2], fill=(*bg_c, int(250 * alpha)))
        d.ellipse([mc + 1, mc - 3, mc + 6, mc + 2], fill=(*bg_c, int(250 * alpha)))
    _paste_alpha(img, ov, cx - (size + pad * 2) // 2, cy - (size + pad * 2) // 2)


def _draw_coffee_steam(img: Image.Image, cx: int, base_y: int, t: float) -> None:
    ov = Image.new("RGBA", (110, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for idx, ox in enumerate((-16, 0, 16)):
        pts = []
        for k in range(18):
            u = k / 17.0
            sx = 55 + ox + math.sin(u * 5.0 - t * 2.8 + idx * 1.4) * 8.0
            sy = 112 - u * 88.0
            pts.append((sx, sy))
        a = int(68 + 26 * math.sin(t * 2.0 + idx))
        d.line(pts, fill=(244, 238, 224, a), width=3, joint="curve")
    _paste_alpha(img, ov, cx - 55, base_y - 114)


def _draw_neural_constellation(img: Image.Image, t: float, dur: float, floor_y: int) -> None:
    w, _ = img.size
    nodes = [
        (int(w * 0.14), floor_y - 140),
        (int(w * 0.30), floor_y - 230),
        (int(w * 0.48), floor_y - 185),
        (int(w * 0.68), floor_y - 265),
        (int(w * 0.85), floor_y - 195),
    ]
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    prog = _ease_out_cubic((t - 0.35) / max(dur * 0.55, 2.0))
    total_segs = len(nodes) - 1
    for i in range(total_segs):
        seg_p = _clamp01(prog * total_segs - i)
        if seg_p > 0.01:
            x0, y0 = nodes[i]
            x1, y1 = nodes[i + 1]
            nx, ny = _lerp(x0, x1, seg_p), _lerp(y0, y1, seg_p)
            d.line([(x0, y0), (nx, ny)], fill=(*GOLD_GLOW, 175), width=4)
    for i, (nx, ny) in enumerate(nodes):
        lit = _clamp01(prog * len(nodes) - i + 0.4)
        pulse = 1.0 + 0.18 * math.sin(t * 3.0 + i)
        r = int(round(10 * pulse))
        d.ellipse([nx - r * 2, ny - r * 2, nx + r * 2, ny + r * 2], fill=(*GOLD_GLOW, int(55 * lit)))
        d.ellipse([nx - r, ny - r, nx + r, ny + r], fill=(*GOLD_GLOW, int(245 * lit)))
    img.alpha_composite(ov)


# ---------------------------------------------------------------------------
# Floating Pills, Speech Bubble, Cream Pastel Cards, Dynamic Vector Dual Cards
# ---------------------------------------------------------------------------

def _draw_pill_badge(
    img: Image.Image,
    text: str,
    cy: int,
    alpha: float,
    gold_style: bool = False,
    dots_count: int = 0,
    dots_lit: int = 0,
) -> None:
    if alpha <= 0.02 or not text:
        return
    w, h = img.size
    base_dim = min(w, h)
    font = _find_font("sans", int(round(base_dim * 0.035)))
    tw = float(ImageDraw.Draw(img).textlength(text, font=font))
    pad_x, pad_y = 40, 16
    pw = int(round(tw + pad_x * 2))
    ph = int(round(base_dim * 0.035 + pad_y * 2 + 4))
    px, py = (w - pw) // 2, cy - ph // 2

    ov = Image.new("RGBA", (pw + 24, ph + (64 if dots_count else 24)), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    bdr = GOLD_TEXT if gold_style else (225, 222, 236)
    txt_col = GOLD_TEXT if gold_style else (246, 244, 250)
    od.rounded_rectangle([12, 12, 12 + pw, 12 + ph], radius=ph // 2, fill=(*PILL_BG, int(232 * alpha)), outline=(*bdr, int(220 * alpha)), width=2)
    od.text((12 + pad_x, 12 + pad_y - 2), text, font=font, fill=(*txt_col, int(255 * alpha)))

    if dots_count > 0:
        dot_gap = 58
        start_dx = (pw + 24) / 2.0 - (dots_count - 1) * dot_gap / 2.0
        dot_y = 12 + ph + 32
        for i in range(dots_count):
            dx = start_dx + i * dot_gap
            c = (*GOLD_GLOW, int(245 * alpha)) if i < dots_lit else (115, 102, 134, int(135 * alpha))
            od.ellipse([dx - 10, dot_y - 10, dx + 10, dot_y + 10], fill=c)

    _paste_alpha(img, ov, px - 12, py - 12)


def _draw_speech_bubble(img: Image.Image, text: str, cx: int, bottom_y: int, alpha: float) -> None:
    if alpha <= 0.02:
        return
    w, _ = img.size
    font = _find_font("sans_bold", int(round(w * 0.036)))
    tw = float(ImageDraw.Draw(img).textlength(text, font=font))
    bw = int(round(max(tw + 116, 300)))
    bh, tail = 92, 24
    ov = Image.new("RGBA", (bw + 20, bh + tail + 20), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    fill = (*CREAM_CARD, int(250 * alpha))
    od.rounded_rectangle([10, 10, 10 + bw, 10 + bh], radius=bh // 2, fill=fill)
    od.polygon([(10 + bw // 2 - 18, 10 + bh - 2), (10 + bw // 2 + 18, 10 + bh - 2), (10 + bw // 2, 10 + bh + tail)], fill=fill)
    od.text((10 + (bw - tw) / 2, 10 + (bh - w * 0.036) / 2 - 4), text, font=font, fill=(*CARD_TITLE, int(255 * alpha)))
    _paste_alpha(img, ov, cx - (bw + 20) // 2, bottom_y - bh - tail - 10)


def _draw_pastel_explainer_card(
    img: Image.Image,
    title: str,
    citation: str,
    rows: list[dict[str, str]],
    t_sec: float,
    card_alpha: float,
    row_triggers: list[float],
) -> None:
    if card_alpha <= 0.02:
        return
    w, h = img.size
    is_land = w > h
    cw = int(round(w * (0.58 if is_land else 0.875)))
    num_rows = len(rows)
    header_h = 112 if is_land else 148
    row_h = (118 if num_rows <= 3 else 104) if is_land else (162 if num_rows <= 3 else 138)
    row_gap = 12 if is_land else 18
    pad_x = 24 if is_land else 30
    ch = header_h + num_rows * row_h + max(num_rows - 1, 0) * row_gap + (26 if is_land else 36)

    slide_y = int(round((1.0 - _ease_out_cubic(card_alpha)) * 32))
    cx0 = (w - cw) // 2
    cy0 = int(round(h * (0.065 if is_land else 0.115))) + slide_y

    pad_sh = 30 if is_land else 34
    card_img = _scale_rgba_alpha(_get_cached_card_shadow(cw, ch, pad_sh, radius=28 if is_land else 32), card_alpha).copy()
    cd = ImageDraw.Draw(card_img)
    cd.rounded_rectangle([pad_sh, pad_sh, pad_sh + cw, pad_sh + ch], radius=28 if is_land else 32, fill=(*CREAM_CARD, int(252 * card_alpha)))

    f_title = _find_font("sans_bold", 32 if is_land else 40)
    f_cite = _find_font("sans_bold", 19 if is_land else 23)
    t_up, c_up = title.upper()[:46], citation.upper()[:56]
    tw = float(cd.textlength(t_up, font=f_title))
    cw_txt = float(cd.textlength(c_up, font=f_cite))
    cd.text((pad_sh + (cw - tw) / 2, pad_sh + (22 if is_land else 32)), t_up, font=f_title, fill=(*CARD_TITLE, int(255 * card_alpha)))
    cd.text((pad_sh + (cw - cw_txt) / 2, pad_sh + (64 if is_land else 88)), c_up, font=f_cite, fill=(*CARD_CITE, int(245 * card_alpha)))

    f_main = _find_font("serif_bold", 32 if is_land else 42)
    f_sub = _find_font("serif_italic", 23 if is_land else 29)

    for idx, row in enumerate(rows):
        ry0 = pad_sh + header_h + idx * (row_h + row_gap)
        ry1 = ry0 + row_h
        rx0, rx1 = pad_sh + pad_x, pad_sh + cw - pad_x
        p_fill, p_bar = PASTEL_ROWS[idx % len(PASTEL_ROWS)]

        trig = row_triggers[idx] if idx < len(row_triggers) else (1.2 + idx * 2.5)
        lit = _ease_out_cubic((t_sec - trig) / 0.55)
        if lit > 0.01:
            cd.rounded_rectangle([rx0, ry0, rx1, ry1], radius=16 if is_land else 20, fill=(*p_fill, int(248 * lit * card_alpha)))
        bar_col = _lerp_rgb(_lerp_rgb(CREAM_CARD, p_bar, 0.35), p_bar, lit)
        cd.rounded_rectangle([rx0, ry0 + 6, rx0 + 14, ry1 - 6], radius=7, fill=(*bar_col, int(255 * card_alpha)))

        main_txt, sub_txt = str(row.get("headline", ""))[:42], str(row.get("sub", ""))[:54]
        mw = float(cd.textlength(main_txt, font=f_main))
        main_col = _lerp_rgb(CARD_MUTED, CARD_INK, lit)
        main_y = ry0 + int(round(_lerp(row_h * 0.30, 18 if is_land else 26, lit)))
        cd.text((pad_sh + (cw - mw) / 2 + 6, main_y), main_txt, font=f_main, fill=(*main_col, int(255 * card_alpha)))
        if sub_txt and lit > 0.05:
            sw = float(cd.textlength(sub_txt, font=f_sub))
            cd.text((pad_sh + (cw - sw) / 2 + 6, ry0 + (68 if is_land else 96)), sub_txt, font=f_sub, fill=(*CARD_ITALIC, int(245 * lit * card_alpha)))

    _paste_alpha(img, card_img, cx0 - pad_sh, cy0 - pad_sh)


def _draw_card_vector_icon(d: ImageDraw.ImageDraw, icon_name: str, icx: int, icy: int, accent: tuple[int, int, int], alpha: float) -> None:
    """Draw crisp topic-matched minimalist 2D vector icons inside closing recap cards."""
    a = int(255 * alpha)
    if icon_name == "shield_sun":
        # Golden Morning Shield with radiant sun center!
        pts = [
            (icx, icy - 48),
            (icx + 42, icy - 32),
            (icx + 38, icy + 10),
            (icx, icy + 48),
            (icx - 38, icy + 10),
            (icx - 42, icy - 32),
        ]
        d.polygon(pts, fill=(250, 224, 146, a), outline=(*accent, a))
        d.line(pts + [pts[0]], fill=(138, 92, 26, a), width=7, joint="curve")
        # Inner bright sun circle + 4 crisp rays
        d.ellipse([icx - 16, icy - 18, icx + 16, icy + 14], fill=(*accent, a))
        for ang_deg in range(0, 360, 45):
            ang = math.radians(ang_deg)
            d.line(
                [(icx + 21 * math.cos(ang), icy - 2 + 21 * math.sin(ang)), (icx + 28 * math.cos(ang), icy - 2 + 28 * math.sin(ang))],
                fill=(138, 92, 26, a),
                width=4,
            )
    elif icon_name == "moon_phone_off":
        # Deep Teal Crescent Moon + Tiny Sleeping Phone-Off Icon!
        d.ellipse([icx - 42, icy - 44, icx + 26, icy + 24], fill=(*accent, a))
        d.ellipse([icx - 20, icy - 52, icx + 46, icy + 12], fill=(*CREAM_CARD, a))
        # Cute small muted phone bottom-right with diagonal slash (phone away!)
        px0, py0, px1, py1 = icx + 4, icy - 4, icx + 42, icy + 46
        d.rounded_rectangle([px0, py0, px1, py1], radius=8, fill=(214, 234, 236, a), outline=(36, 98, 108, a), width=5)
        d.line([(px0 - 6, py1 + 2), (px1 + 6, py0 - 2)], fill=(186, 76, 72, a), width=6)
    elif icon_name == "clock_focus":
        d.ellipse([icx - 44, icy - 44, icx + 44, icy + 44], fill=(248, 224, 150, a), outline=(*accent, a), width=7)
        d.line([(icx, icy), (icx, icy - 24)], fill=(38, 30, 58, a), width=7)
        d.line([(icx, icy), (icx + 20, icy + 8)], fill=(38, 30, 58, a), width=6)
    else:
        # Clean brain / focus spark emblem
        d.ellipse([icx - 40, icy - 36, icx + 40, icy + 36], fill=(214, 234, 236, a), outline=(*accent, a), width=7)
        d.ellipse([icx - 14, icy - 14, icx + 14, icy + 14], fill=(*accent, a))


def _draw_closing_dual_cards(
    img: Image.Image,
    left_card: dict[str, str],
    right_card: dict[str, str],
    t_sec: float,
    alpha: float,
) -> None:
    if alpha <= 0.02:
        return
    w, h = img.size
    is_land = w > h
    gap = 36 if is_land else 34
    margin_x = int(round(w * 0.21)) if is_land else 64
    card_w = (w - margin_x * 2 - gap) // 2
    card_h = 285 if is_land else 365
    top_y = int(round(h * (0.20 if is_land else 0.255)))

    specs = [
        (margin_x, left_card, GOLD_ACCENT, 0.35),
        (margin_x + card_w + gap, right_card, TEAL_ACCENT, 0.95),
    ]
    f_head = _find_font("sans_bold", 28 if is_land else 33)
    f_sub = _find_font("serif_italic", 24 if is_land else 29)

    for x0, data, head_col, delay in specs:
        if t_sec < delay:
            continue
        ep = _ease_out_back((t_sec - delay) / 0.55)
        c_alpha = min(_ease_out_cubic((t_sec - delay) / 0.35), alpha)
        dy = int(round((1.0 - min(ep, 1.04)) * 42))

        pad = 24
        ov = _scale_rgba_alpha(_get_cached_card_shadow(card_w, card_h, pad, radius=28), c_alpha).copy()
        d = ImageDraw.Draw(ov)
        d.rounded_rectangle([pad, pad, pad + card_w, pad + card_h], radius=28, fill=(*CREAM_CARD, int(252 * c_alpha)))

        # Colored top strip
        cap_mask = Image.new("L", ov.size, 0)
        ImageDraw.Draw(cap_mask).rounded_rectangle([pad, pad, pad + card_w, pad + card_h], radius=28, fill=255)
        cap_layer = Image.new("RGBA", ov.size, (0, 0, 0, 0))
        ImageDraw.Draw(cap_layer).rectangle([pad, pad, pad + card_w, pad + 18], fill=(*head_col, int(255 * c_alpha)))
        ov.paste(Image.alpha_composite(ov, cap_layer), (0, 0), cap_mask)
        d = ImageDraw.Draw(ov)

        # Dynamic story-matched icon!
        _draw_card_vector_icon(d, str(data.get("icon", "shield_sun")), pad + card_w // 2, pad + (88 if is_land else 110), head_col, c_alpha)

        h_txt, s_txt = str(data.get("title", "")).upper()[:24], str(data.get("sub", ""))[:32]
        hw = float(d.textlength(h_txt, font=f_head))
        sw = float(d.textlength(s_txt, font=f_sub))
        d.text((pad + (card_w - hw) / 2, pad + (162 if is_land else 202)), h_txt, font=f_head, fill=(*head_col, int(255 * c_alpha)))
        d.text((pad + (card_w - sw) / 2, pad + (210 if is_land else 264)), s_txt, font=f_sub, fill=(*CARD_ITALIC, int(245 * c_alpha)))

        _paste_alpha(img, ov, x0 - pad, top_y + dy - pad)


# ---------------------------------------------------------------------------
# Georgia Bold Serif Karaoke Subtitles + Edge TTS Audio
# ---------------------------------------------------------------------------

@dataclass
class WordEvent:
    text: str
    start_sec: float
    end_sec: float


def _chunk_phrases(words: list[WordEvent], max_words: int = 7) -> list[list[WordEvent]]:
    chunks: list[list[WordEvent]] = []
    cur: list[WordEvent] = []
    for w in words:
        cur.append(w)
        ends_p = bool(re.search(r"[\.\!\?,;:]$", w.text))
        if len(cur) >= max_words or (ends_p and len(cur) >= 3):
            chunks.append(cur)
            cur = []
    if cur:
        if chunks and len(cur) <= 2 and len(chunks[-1]) <= 6:
            chunks[-1].extend(cur)
        else:
            chunks.append(cur)
    return chunks


def _draw_serif_karaoke_subtitles(img: Image.Image, t_sec: float, phrases: list[list[WordEvent]], gold_words: set[str]) -> None:
    if not phrases:
        return
    active: list[WordEvent] | None = None
    for idx, ph in enumerate(phrases):
        st = ph[0].start_sec - 0.12
        nxt = phrases[idx + 1][0].start_sec - 0.12 if idx + 1 < len(phrases) else ph[-1].end_sec + 1.5
        if st <= t_sec < nxt:
            active = ph
            break
    if active is None:
        return

    w, h = img.size
    is_land = w > h
    fsize = int(round(h * 0.044)) if is_land else int(round(w * 0.047))
    font = _find_font("serif_bold", fsize)
    d = ImageDraw.Draw(img)
    max_w = w * (0.76 if is_land else 0.84)
    sp_w = float(d.textlength(" ", font=font))

    lines: list[list[WordEvent]] = []
    cur_l: list[WordEvent] = []
    cur_w = 0.0
    for we in active:
        ww = float(d.textlength(we.text, font=font))
        add = ww if not cur_l else sp_w + ww
        if cur_l and cur_w + add > max_w:
            lines.append(cur_l)
            cur_l, cur_w = [we], ww
        else:
            cur_l.append(we)
            cur_w += add
    if cur_l:
        lines.append(cur_l)

    line_h = int(round(fsize * 1.40))
    base_y = int(round(h * (0.805 if is_land else 0.730)))

    for l_i, line_ws in enumerate(lines[:3]):
        widths = [float(d.textlength(we.text, font=font)) for we in line_ws]
        total_lw = sum(widths) + sp_w * max(len(line_ws) - 1, 0)
        x, y = (w - total_lw) / 2.0, base_y + l_i * line_h
        for we, ww in zip(line_ws, widths):
            lit = _ease_out_cubic((t_sec - (we.start_sec - 0.06)) / 0.18) if t_sec >= (we.start_sec - 0.06) else 0.0
            clean = re.sub(r"[^A-Z0-9]", "", we.text.upper())
            target = GOLD_TEXT if clean in gold_words else SUB_WHITE
            col = _lerp_rgb(SUB_DIM, target, lit)
            d.text((x, y + 3), we.text, font=font, fill=(6, 4, 12, 185))
            d.text((x, y), we.text, font=font, fill=(*col, 255))
            x += ww + sp_w


async def _synthesize_edge_audio(text: str, out_mp3: Path, voice: str = "en-US-AndrewMultilingualNeural", rate: str = "-6%") -> tuple[float, list[WordEvent]]:
    import edge_tts

    words: list[WordEvent] = []
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    last_err: Exception | None = None
    for attempt in range(1, 4):
        words = []
        try:
            async def _fetch_once() -> None:
                comm = edge_tts.Communicate(text=text, voice=voice, rate=rate, boundary="WordBoundary")
                with out_mp3.open("wb") as fh:
                    async for ch in comm.stream():
                        if ch.get("type") == "audio":
                            fh.write(ch["data"])
                        elif ch.get("type") == "WordBoundary":
                            wt = str(ch.get("text", "")).strip()
                            if wt:
                                st = float(ch.get("offset", 0)) / 10_000_000.0
                                dur = float(ch.get("duration", 0)) / 10_000_000.0
                                words.append(WordEvent(text=wt, start_sec=st, end_sec=st + max(dur, 0.12)))

            await asyncio.wait_for(_fetch_once(), timeout=25.0)
            if out_mp3.exists() and out_mp3.stat().st_size > 1024:
                last_err = None
                break
        except Exception as exc:
            last_err = exc
            print(f"[cozy-tts] Attempt {attempt}/3 retry ({type(exc).__name__}): {str(exc)[:100]}", flush=True)
            await asyncio.sleep(1.2)
    if last_err is not None and (not out_mp3.exists() or out_mp3.stat().st_size <= 1024):
        raise last_err

    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(out_mp3)],
        capture_output=True, text=True, check=True,
    )
    total_dur = max(float(res.stdout.strip() or 1.0), 1.0)
    src_tokens = [tok for tok in text.strip().split() if tok]
    if words and len(src_tokens) == len(words):
        for w_ev, s_tok in zip(words, src_tokens):
            w_ev.text = s_tok
    elif not words and src_tokens:
        weights = [
            len(re.sub(r"[^A-Za-z0-9]", "", tok)) + 2.5 + (6.0 if tok.endswith((".", "!", "?")) else (3.5 if tok.endswith((",", ";", ":")) else 0.0))
            for tok in src_tokens
        ]
        w_sum = sum(weights) or 1.0
        cur_t, usable = 0.08, max(total_dur - 0.16, 0.5)
        words = []
        for tok, wt in zip(src_tokens, weights):
            d_tok = usable * (wt / w_sum)
            words.append(WordEvent(text=tok, start_sec=cur_t, end_sec=cur_t + d_tok))
            cur_t += d_tok
    return total_dur, words


def _mix_cozy_soundscape(voice_wav: Path, scene_starts: list[float], total_dur: float, out_m4a: Path, work_dir: Path) -> Path:
    chime_wav = work_dir / "_cozy_chime.wav"
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "aevalsrc='(0.55*sin(2*PI*440*t)+0.35*sin(2*PI*659.25*t))*exp(-10*t)':s=44100:d=0.32",
                "-af", "lowpass=f=1600,volume=-23dB",
                "-c:a", "pcm_s16le", str(chime_wav),
            ],
            capture_output=True, check=True,
        )
        fade_out = max(total_dur - 2.2, 0.5)
        pad_expr = (
            "0.24*sin(2*PI*146.83*t)+0.19*sin(2*PI*220.00*t)+0.15*sin(2*PI*277.18*t)"
            "+0.12*sin(2*PI*329.63*t)*(0.78+0.22*sin(2*PI*0.16*t))"
        )
        inputs = ["-i", str(voice_wav), "-f", "lavfi", "-t", f"{total_dur + 0.5:.2f}", "-i", f"aevalsrc='{pad_expr}':s=44100:c=stereo"]
        filters = [f"[1:a]lowpass=f=440,volume=-24dB,afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out:.2f}:d=2.0[pad]"]
        mix = ["[0:a]", "[pad]"]
        nxt = 2
        for idx, st in enumerate(scene_starts[1:8], start=1):
            ms = max(int(round(st * 1000)), 0)
            inputs.extend(["-i", str(chime_wav)])
            filters.append(f"[{nxt}:a]adelay={ms}|{ms}[c{idx}]")
            mix.append(f"[c{idx}]")
            nxt += 1
        filters.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:dropout_transition=2:normalize=0[out]")
        subprocess.run(
            ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]", "-c:a", "aac", "-b:a", "192k", str(out_m4a)],
            capture_output=True, check=True,
        )
        if out_m4a.exists() and out_m4a.stat().st_size > 1024:
            return out_m4a
    except Exception as exc:
        print(f"[cozy-audio] fallback: {exc}", flush=True)
    finally:
        chime_wav.unlink(missing_ok=True)
    return voice_wav


# ---------------------------------------------------------------------------
# Full Story-Matched HabitSains Studio v8.2 Demo Builder
# ---------------------------------------------------------------------------

def build_cozy_diorama_demo(
    scenes: list[dict[str, Any]],
    out_mp4: Path,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    voice: str = "en-US-AndrewMultilingualNeural",
) -> dict[str, Any]:
    work_dir = out_mp4.parent / "_v82_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    print("[v8.3-habitsains] Pre-rendering 6 bespoke dioramas & 6 expressive blinking character moods...", flush=True)
    bed_morning_bg, bed_m_meta = _build_bedroom_diorama(width, height, is_evening=False)
    bed_evening_bg, bed_e_meta = _build_bedroom_diorama(width, height, is_evening=True)
    desk_laptop_bg, desk_l_meta = _build_study_desk_diorama(width, height, dawn_window=False, laptop_open=True)
    desk_calm_bg, desk_c_meta = _build_study_desk_diorama(width, height, dawn_window=True, laptop_open=False)
    neural_sky_bg, neural_meta = _build_neural_sky_diorama(width, height)

    char_h = int(round(height * 0.185))
    char_h_big = int(round(char_h * 1.24))

    def _pair(h_px: int, mood: str, prop: str, rim: str) -> tuple[Image.Image, Image.Image]:
        return (
            _build_expressive_character(h_px, mood=mood, prop=prop, blink=False, rim_light=rim),
            _build_expressive_character(h_px, mood=mood, prop=prop, blink=True, rim_light=rim),
        )

    c_sleepy = _pair(char_h, "sleepy_scroll", "phone", "blue")
    c_overwhelm_big = _pair(char_h_big, "overwhelmed", "phone", "blue")
    c_overwhelm_desk = _pair(char_h, "overwhelmed", "journal", "blue")
    c_protected = _pair(char_h, "protected_calm", "journal", "cyan")
    c_focus = _pair(char_h, "deep_focus", "journal", "warm")
    c_wonder = _pair(char_h, "inspired_wonder", "journal", "warm")
    c_rest = _pair(char_h, "peaceful_rest", "journal", "warm")

    glow_lamp = _make_radial_glow(int(width * 0.40), GOLD_GLOW, 92)
    glow_phone = _make_radial_glow(int(width * 0.24), PHONE_BLUE, 84)
    glow_shield = _make_radial_glow(int(width * 0.24), TEAL_SHIELD, 82)
    rug_glow_soft = Image.new("RGBA", (width, 240), (0, 0, 0, 0))
    ImageDraw.Draw(rug_glow_soft).ellipse([int(width * 0.05), 34, int(width * 0.76), 192], fill=(214, 178, 108, 42))
    rug_glow_soft = rug_glow_soft.filter(ImageFilter.GaussianBlur(radius=20))

    seg_videos: list[Path] = []
    seg_audios: list[Path] = []
    scene_starts: list[float] = []
    cursor = 0.0
    pause_sec = 0.55

    for idx, sc in enumerate(scenes, start=1):
        mp3 = work_dir / f"v_{idx:02d}.mp3"
        dur, words = asyncio.run(_synthesize_edge_audio(sc["narration"], mp3, voice=voice))
        seg_dur = dur + pause_sec
        pad_wav = work_dir / f"v_{idx:02d}.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp3), "-af", f"apad=pad_dur={pause_sec:.2f}", "-t", f"{seg_dur:.3f}", "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(pad_wav)],
            capture_output=True, check=True,
        )
        seg_audios.append(pad_wav)
        scene_starts.append(cursor)
        cursor += seg_dur

        seg_mp4 = work_dir / f"seg_{idx:02d}.mp4"
        stype = sc["scene_type"]
        print(f"[v8.2-habitsains] Rendering scene {idx}/{len(scenes)} ({stype}, {seg_dur:.1f}s @ {fps}fps)...", flush=True)

        phrases = _chunk_phrases(words, max_words=7)
        gold_words = {re.sub(r"[^A-Z0-9]", "", str(w).upper()) for w in (sc.get("gold_words") or [])}
        total_frames = max(int(round(seg_dur * fps)), fps)

        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}", "-r", str(fps), "-i", "pipe:0",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-an",
            str(seg_mp4),
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        assert proc.stdin is not None

        try:
            for f_i in range(total_frames):
                t = f_i / float(fps)
                p = _clamp01(t / max(seg_dur, 0.1))
                bob = int(round(math.sin(t * 2.8) * 5.0))
                env = min(_clamp01(t / 0.35), _clamp01((seg_dur - t) / 0.35))

                # --- SCENE 1: BEDROOM MORNING SCROLL (SLEEPY HALF-LIDDED EYES + PHONE GLOW) ---
                if stype == "bedroom_morning_scroll":
                    frame = bed_morning_bg.copy()
                    bx, by = bed_m_meta["bed_seat"]
                    sp = _pick_character_frame(c_sleepy, t, sway_deg=math.sin(t * 1.6) * 1.4)
                    _paste_alpha(frame, glow_phone, bx + 20 - glow_phone.width // 2, by - sp.height // 2 - glow_phone.height // 2)
                    _paste_alpha(frame, sp, bx - sp.width // 2, by - sp.height + 16 + bob)
                    for n_i, kind in enumerate(("chat", "bell")):
                        cyc = (t * 0.45 + n_i * 0.5) % 1.0
                        ny = int(by - sp.height * 0.72 - cyc * 145)
                        nx = int(bx + 80 + math.sin(cyc * 6.0 + n_i) * 26)
                        na = math.sin(cyc * math.pi)
                        _draw_distraction_badge(frame, kind, nx, ny, 48, na * 0.85)
                    _draw_pill_badge(frame, sc.get("pill", "morning autopilot"), int(height * 0.225), _ease_out_cubic(t / 0.45), gold_style=False)

                # --- SCENE 2: BEDROOM SCROLL FLOOD (OVERWHELMED WIDE EYES + SWEAT DROP + SWARM) ---
                elif stype == "bedroom_scroll_flood":
                    frame = bed_morning_bg.copy()
                    zoom_f = _lerp(1.08, 1.18, p)
                    zw, zh = int(width / zoom_f), int(height / zoom_f)
                    zx0, zy0 = int((width - zw) * 0.36), int((height - zh) * 0.44)
                    frame = _fast_downscale_rgba(frame.crop((zx0, zy0, zx0 + zw, zy0 + zh)), width, height)

                    cx_c, cy_c = int(width * 0.47), int(height * 0.625)
                    sp = _pick_character_frame(c_overwhelm_big, t, sway_deg=math.sin(t * 4.5) * 1.6)
                    _paste_alpha(frame, glow_phone, cx_c + 36 - glow_phone.width // 2, cy_c - sp.height // 2 - glow_phone.height // 2)
                    _paste_alpha(frame, sp, cx_c - sp.width // 2, cy_c - sp.height + bob)

                    swarm = [
                        ("play", -175, 0.00), ("heart", 155, 0.16), ("bell", -85, 0.33),
                        ("chat", 210, 0.50), ("play", 90, 0.66), ("heart", -205, 0.82),
                    ]
                    for kind, dx_off, ph in swarm:
                        cyc = (t * 0.58 + ph) % 1.0
                        ny = int(cy_c - sp.height * 0.62 - cyc * 310)
                        nx = int(cx_c + dx_off * (0.5 + 0.5 * cyc) + math.sin(cyc * 5.0 + ph * 8) * 20)
                        na = math.sin(cyc * math.pi)
                        _draw_distraction_badge(frame, kind, nx, ny, 56, na * 0.92)

                    dots_lit = min(5, 1 + int((t / max(seg_dur * 0.72, 1.0)) * 4))
                    _draw_pill_badge(frame, sc.get("pill", "without realizing"), int(height * 0.185), _ease_out_cubic(t / 0.45), gold_style=True, dots_count=5, dots_lit=dots_lit)

                # --- SCENE 3: DESK COGNITIVE FOG (OVERWHELMED CHARACTER AT LAPTOP + 3-ROW CARD) ---
                elif stype == "desk_cognitive_fog":
                    frame = desk_laptop_bg.copy()
                    fy = desk_l_meta["floor_y"]
                    lap_x, lap_y = desk_l_meta["laptop_pos"]
                    sp = _pick_character_frame(c_overwhelm_desk, t, sway_deg=math.sin(t * 2.6) * 1.2)
                    _paste_alpha(frame, glow_phone, lap_x - glow_phone.width // 2, lap_y - glow_phone.height // 2)
                    _paste_alpha(frame, sp, int(width * 0.33) - sp.width // 2, fy - sp.height + 30 + bob)
                    for n_i, (kind, ox) in enumerate([("play", -60), ("chat", 30), ("bell", 110)]):
                        drift = math.sin(t * 2.0 + n_i * 1.7) * 16
                        _draw_distraction_badge(frame, kind, lap_x + ox, lap_y - 36 + int(drift), 44, 0.45)

                    card_a = min(_ease_out_cubic((t - 0.25) / 0.55), _clamp01((seg_dur - t) / 0.40))
                    _draw_pastel_explainer_card(
                        frame,
                        title=sc["card_title"],
                        citation=sc["card_cite"],
                        rows=sc["card_rows"],
                        t_sec=t,
                        card_alpha=card_a,
                        row_triggers=sc.get("row_triggers", [2.2, 5.8, 9.2]),
                    )

                # --- SCENE 4: FOCUS SHIELD REPEL (SERENE PROTECTED SMILE INSIDE CYAN SHIELD!) ---
                elif stype == "focus_shield_repel":
                    frame = desk_calm_bg.copy()
                    lx, ly = desk_c_meta["lamp_pos"]
                    fy = desk_c_meta["floor_y"]
                    _paste_alpha(frame, glow_lamp, lx - glow_lamp.width // 2, ly - glow_lamp.height // 2 + 40)
                    _paste_alpha(frame, rug_glow_soft, 0, fy - 24)
                    _draw_coffee_steam(frame, *desk_c_meta["coffee_pos"], t)

                    sp = _pick_character_frame(c_protected, t, sway_deg=math.sin(t * 1.4) * 1.0)
                    ch_x = int(width * 0.35)
                    ch_y = fy - sp.height + 30 + bob
                    ring_cx, ring_cy = ch_x, ch_y + sp.height // 2 - 14
                    sh_p = _ease_out_cubic((t - 0.25) / 0.65)
                    shield_r = int(round(196 * sh_p * (1.0 + 0.025 * math.sin(t * 3.4))))

                    if sh_p > 0.01:
                        _paste_alpha(frame, glow_shield, ring_cx - glow_shield.width // 2, ring_cy - glow_shield.height // 2)
                    _paste_alpha(frame, sp, ch_x - sp.width // 2, ch_y)
                    if sh_p > 0.01:
                        ring_ov = Image.new("RGBA", (shield_r * 2 + 40, shield_r * 2 + 40), (0, 0, 0, 0))
                        rc = shield_r + 20
                        ImageDraw.Draw(ring_ov).ellipse([rc - shield_r, rc - shield_r, rc + shield_r, rc + shield_r], outline=(*TEAL_SHIELD, int(235 * sh_p)), width=7)
                        _paste_alpha(frame, ring_ov, ring_cx - rc, ring_cy - rc)

                    projectiles = [
                        ("play", -22.0, 0.00),
                        ("bell", 160.0, 0.28),
                        ("heart", -55.0, 0.56),
                        ("chat", 205.0, 0.78),
                    ]
                    for kind, deg, ph in projectiles:
                        cyc = (t * 0.42 + ph) % 1.0
                        ang = math.radians(deg)
                        if cyc < 0.45:
                            u = cyc / 0.45
                            dist = _lerp(430.0, shield_r + 36.0, _ease_out_cubic(u))
                            ba = _clamp01(u * 2.5)
                        else:
                            u = (cyc - 0.45) / 0.55
                            dist = _lerp(shield_r + 36.0, 500.0, _ease_out_cubic(u))
                            ba = max(0.0, 1.0 - u * 1.15)
                        px = int(ring_cx + dist * math.cos(ang))
                        py = int(ring_cy + dist * math.sin(ang))
                        _draw_distraction_badge(frame, kind, px, py, 52, ba * sh_p)

                    _draw_pill_badge(frame, sc.get("pill", "distraction blocked"), int(height * 0.175), _ease_out_cubic(t / 0.45), gold_style=False)

                # --- SCENE 5: COZY DEEP WORK DESK (BRIGHT ALERT HAPPY FOCUS + STEAMING COFFEE) ---
                elif stype == "cozy_deep_work_desk":
                    frame = desk_calm_bg.copy()
                    lx, ly = desk_c_meta["lamp_pos"]
                    fy = desk_c_meta["floor_y"]
                    _paste_alpha(frame, glow_lamp, lx - glow_lamp.width // 2, ly - glow_lamp.height // 2 + 40)
                    _paste_alpha(frame, rug_glow_soft, 0, fy - 24)
                    _draw_coffee_steam(frame, *desk_c_meta["coffee_pos"], t)

                    sp = _pick_character_frame(c_focus, t, sway_deg=math.sin(t * 1.5) * 1.1)
                    ch_x = int(width * 0.35)
                    ch_y = fy - sp.height + 30 + bob
                    _paste_alpha(frame, sp, ch_x - sp.width // 2, ch_y)
                    _draw_pill_badge(frame, sc.get("pill", "start in stillness"), int(height * 0.175), _ease_out_cubic(t / 0.45), gold_style=True)
                    _draw_speech_bubble(frame, sc.get("speech", "deep focus..."), ch_x + 42, ch_y - 20, _ease_out_cubic((t - 1.0) / 0.45))

                # --- SCENE 6: NEURAL PATHWAY STARS (INSPIRED WONDER GAZING UP + PROTOCOL CARD) ---
                elif stype == "neural_pathway_stars":
                    frame = neural_sky_bg.copy()
                    fy = neural_meta["floor_y"]
                    _draw_neural_constellation(frame, t, seg_dur, fy)
                    sp = _pick_character_frame(c_wonder, t, sway_deg=math.sin(t * 1.4) * 1.2)
                    _paste_alpha(frame, sp, int(width * 0.50) - sp.width // 2, fy - sp.height + 24 + bob)

                    card_a = min(_ease_out_cubic((t - 0.25) / 0.55), _clamp01((seg_dur - t) / 0.40))
                    _draw_pastel_explainer_card(
                        frame,
                        title=sc["card_title"],
                        citation=sc["card_cite"],
                        rows=sc["card_rows"],
                        t_sec=t,
                        card_alpha=card_a,
                        row_triggers=sc.get("row_triggers", [0.9, 5.2]),
                    )

                # --- SCENE 7: BEDROOM EVENING RESET (PEACEFUL REST SMILE + CLOSING DUAL CARDS) ---
                else:
                    frame = bed_evening_bg.copy()
                    fy = bed_e_meta["floor_y"]
                    _paste_alpha(frame, rug_glow_soft, 0, fy - 24)
                    sp = _pick_character_frame(c_rest, t, sway_deg=math.sin(t * 1.2) * 1.0)
                    ch_x = int(width * 0.44)
                    ch_y = fy - sp.height + 30 + bob
                    _paste_alpha(frame, sp, ch_x - sp.width // 2, ch_y)
                    _draw_pill_badge(frame, sc.get("pill", "Two small daily habits"), int(height * 0.205), _ease_out_cubic(t / 0.45), gold_style=True)
                    _draw_closing_dual_cards(frame, sc["left_card"], sc["right_card"], t_sec=t, alpha=env)

                # Signature Georgia Bold Serif Karaoke Subtitles
                _draw_serif_karaoke_subtitles(frame, t, phrases, gold_words)

                rgb_img = frame.convert("RGB")
                if env < 0.998:
                    arr = np.asarray(rgb_img, dtype=np.float32)
                    bg_v = np.array(FLOOR_DARK, dtype=np.float32)
                    arr = bg_v + (arr - bg_v) * env
                    proc.stdin.write(arr.astype(np.uint8).tobytes())
                else:
                    proc.stdin.write(rgb_img.tobytes())

            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", errors="ignore") if proc.stderr else ""
            ret = proc.wait()
            if ret != 0:
                raise RuntimeError(f"FFmpeg v8.2 render failed ({ret}): {err[-300:]}")
        finally:
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()

        seg_videos.append(seg_mp4)

    vlist = work_dir / "v.txt"
    vlist.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in seg_videos), encoding="utf-8")
    merged_v = work_dir / "merged_v.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(vlist), "-c", "copy", str(merged_v)], capture_output=True, check=True)

    alist = work_dir / "a.txt"
    alist.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in seg_audios), encoding="utf-8")
    merged_a = work_dir / "merged_a.wav"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(alist), "-c", "copy", str(merged_a)], capture_output=True, check=True)

    mixed_a = work_dir / "mixed.m4a"
    final_a = _mix_cozy_soundscape(merged_a, scene_starts, cursor, mixed_a, work_dir)

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(merged_v), "-i", str(final_a), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(out_mp4)],
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
        "duration_sec": round(cursor, 2),
        "size_mb": round(out_mp4.stat().st_size / (1024 * 1024), 2),
        "scene_starts": [round(x, 2) for x in scene_starts],
    }


# ---------------------------------------------------------------------------
# Reusable Production Pipeline Adapter (Works for ANY HabitSains Script, 16:9 & 9:16!)
# ---------------------------------------------------------------------------

def _extract_gold_keywords(text: str) -> set[str]:
    power = {
        "FOCUS", "BRAIN", "DOPAMINE", "HABIT", "HABITS", "MINUTES", "MINUTE", "HOURS", "HOUR",
        "ATTENTION", "RESIDUE", "SCROLL", "SCROLLING", "PHONE", "STILLNESS", "CLARITY",
        "PROTECT", "SHIELD", "RESET", "DEEP", "SLEEP", "SCIENCE", "MORNING", "EVENING",
        "AUTOPILOT", "ENERGY", "MEMORY", "PROTOCOL", "NEURONS", "PATHWAYS", "CONSISTENCY",
    }
    found = set()
    for tok in re.findall(r"[A-Za-z0-9]+", text.upper()):
        if tok in power or tok.isdigit():
            found.add(tok)
    return found


def _words_from_scene_audio(scene_audio: Any) -> list[WordEvent]:
    """Convert TrackAudioBundle SceneAudioResult into WordEvent list (works for Gemini TTS & Edge TTS!)."""
    text = str(getattr(scene_audio, "text", "") or "").strip()
    dur = max(float(getattr(scene_audio, "duration_sec", 4.0) or 4.0), 1.0)
    raw_timings = getattr(scene_audio, "word_timings", None) or []

    word_events: list[WordEvent] = []
    for wt in raw_timings:
        if wt.get("type") == "WordBoundary" and str(wt.get("text", "")).strip():
            word_events.append(
                WordEvent(
                    text=str(wt["text"]).strip(),
                    start_sec=float(wt.get("start", 0.0)),
                    end_sec=float(wt.get("end", 0.12)),
                )
            )

    src_tokens = [tok for tok in text.split() if tok]
    if word_events and len(src_tokens) == len(word_events):
        for we, st in zip(word_events, src_tokens):
            we.text = st
        return word_events

    if not src_tokens:
        return []
    weights = [
        len(re.sub(r"[^A-Za-z0-9]", "", tok)) + 2.5 + (6.0 if tok.endswith((".", "!", "?")) else (3.5 if tok.endswith((",", ";", ":")) else 0.0))
        for tok in src_tokens
    ]
    w_sum = sum(weights) or 1.0
    cur_t, usable = 0.08, max(dur - 0.16, 0.5)
    out: list[WordEvent] = []
    for tok, wt in zip(src_tokens, weights):
        dt = usable * (wt / w_sum)
        out.append(WordEvent(text=tok, start_sec=cur_t, end_sec=cur_t + dt))
        cur_t += dt
    return out


def _map_blueprint_scene_to_cozy(scene: dict[str, Any], idx: int, total: int, seg_dur: float) -> dict[str, Any]:
    """Automatically choose the most story-matched Studio v8.3 diorama, mood, cards, and icons."""
    raw = f"{scene.get('section', '')} {scene.get('badge', '')} {scene.get('visual_headline', '')} {scene.get('narration', '')}".lower()
    headline = str(scene.get("visual_headline") or f"Part {idx}").strip()
    callout = str(scene.get("on_screen_callout") or "Science-backed focus & habit protocol").strip()
    bullets = [re.sub(r"^\d+[\.\)]\s*", "", str(b)).strip() for b in (scene.get("bullet_points") or []) if str(b).strip()]

    # Choose diorama type intelligently by story beat & keywords
    explicit = str(scene.get("cozy_scene_type") or "").strip().lower()
    valid = (
        "bedroom_morning_scroll", "bedroom_scroll_flood", "desk_cognitive_fog",
        "focus_shield_repel", "cozy_deep_work_desk", "neural_pathway_stars", "closing_dual_cards",
    )
    if explicit in valid:
        stype = explicit
    elif idx == total and total >= 3:
        stype = "closing_dual_cards"
    elif idx == 1:
        stype = "bedroom_morning_scroll" if any(k in raw for k in ("scroll", "phone", "morning", "wake", "bed", "clip")) else "cozy_deep_work_desk"
    elif any(k in raw for k in ("residue", "mechanism", "study", "research", "science", "23", "dopamine", "trap", "fog")):
        stype = "desk_cognitive_fog"
    elif any(k in raw for k in ("shield", "block", "distract", "noise", "protect")):
        stype = "focus_shield_repel"
    elif any(k in raw for k in ("protocol", "step", "reset", "neuron", "myelin", "pathway", "habit", "66")):
        stype = "neural_pathway_stars"
    elif any(k in raw for k in ("scroll", "autopilot", "feed", "swipe")):
        stype = "bedroom_scroll_flood"
    else:
        cycle = ("bedroom_morning_scroll", "desk_cognitive_fog", "focus_shield_repel", "cozy_deep_work_desk", "neural_pathway_stars")
        stype = cycle[(idx - 1) % len(cycle)]

    # Build clean card rows from bullets / callout
    rows: list[dict[str, str]] = []
    for b in bullets[:3]:
        if ":" in b:
            h_part, s_part = b.split(":", 1)
            rows.append({"headline": h_part.strip()[:38], "sub": s_part.strip()[:52]})
        else:
            rows.append({"headline": b[:38], "sub": callout[:52] if not rows else ""})
    if not rows:
        rows = [
            {"headline": headline[:38], "sub": callout[:52]},
            {"headline": "Protect Deep Focus", "sub": "small repeatable daily shifts"},
        ]

    span = max(seg_dur - 1.8, 2.0)
    triggers = [round(0.8 + (i / float(max(len(rows), 1))) * span * 0.72, 2) for i in range(len(rows))]

    left_card = {
        "title": (rows[0]["headline"][:18] if rows else "MORNING SHIELD"),
        "sub": (rows[0]["sub"][:26] or "protect first quiet hour"),
        "icon": "shield_sun",
    }
    right_card = {
        "title": (rows[1]["headline"][:18] if len(rows) > 1 else "EVENING RESET"),
        "sub": (rows[1]["sub"][:26] or "phone across the room"),
        "icon": "moon_phone_off",
    }

    pill_raw = re.sub(r"^\d+\s*[•:\.\|]\s*", "", str(scene.get("badge") or scene.get("section") or headline)).strip()
    pill = pill_raw[:28].lower()

    return {
        "scene_type": stype,
        "pill": pill,
        "speech": "deep focus...",
        "card_title": headline[:34],
        "card_cite": "HABITSAINS • EVIDENCE-BASED FOCUS",
        "card_rows": rows[:3],
        "row_triggers": triggers,
        "left_card": left_card,
        "right_card": right_card,
        "gold_words": list(_extract_gold_keywords(str(scene.get("narration") or ""))),
    }


def render_cozy_diorama_video_for_pipeline(
    scenes_meta: list[dict[str, Any]],
    audio_bundle: Any,
    out_video_path: Path,
    config: dict[str, Any],
    is_short: bool = False,
) -> Path:
    """Render full Studio v8.3 Cozy Diorama + Expressive Character video directly inside src.video_builder."""
    video_root = config.get("video", {})
    vid_cfg = video_root.get("shorts" if is_short else "youtube_long", {})
    width = int(vid_cfg.get("width", 1080 if is_short else 1920))
    height = int(vid_cfg.get("height", 1920 if is_short else 1080))
    fps = int(vid_cfg.get("fps", 30))
    pause_sec = float(vid_cfg.get("padding_after_audio_sec", 0.30 if is_short else 0.45))

    work_dir = out_video_path.parent / "_cozy_v83_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"[v8.3-cozy] Pre-rendering 6 expressive dioramas ({width}x{height} @ {fps}fps)...", flush=True)
    bed_morning_bg, bed_m_meta = _build_bedroom_diorama(width, height, is_evening=False)
    bed_evening_bg, bed_e_meta = _build_bedroom_diorama(width, height, is_evening=True)
    desk_laptop_bg, desk_l_meta = _build_study_desk_diorama(width, height, dawn_window=False, laptop_open=True)
    desk_calm_bg, desk_c_meta = _build_study_desk_diorama(width, height, dawn_window=True, laptop_open=False)
    neural_sky_bg, neural_meta = _build_neural_sky_diorama(width, height)

    is_land = width > height
    char_h = int(round(height * (0.29 if is_land else 0.185)))
    char_h_big = int(round(char_h * 1.20))

    def _pair(h_px: int, mood: str, prop: str, rim: str) -> tuple[Image.Image, Image.Image]:
        return (
            _build_expressive_character(h_px, mood=mood, prop=prop, blink=False, rim_light=rim),
            _build_expressive_character(h_px, mood=mood, prop=prop, blink=True, rim_light=rim),
        )

    c_sleepy = _pair(char_h, "sleepy_scroll", "phone", "blue")
    c_overwhelm_big = _pair(char_h_big, "overwhelmed", "phone", "blue")
    c_overwhelm_desk = _pair(char_h, "overwhelmed", "journal", "blue")
    c_protected = _pair(char_h, "protected_calm", "journal", "cyan")
    c_focus = _pair(char_h, "deep_focus", "journal", "warm")
    c_wonder = _pair(char_h, "inspired_wonder", "journal", "warm")
    c_rest = _pair(char_h, "peaceful_rest", "journal", "warm")

    glow_base = min(width, height)
    glow_lamp = _make_radial_glow(int(glow_base * 0.40), GOLD_GLOW, 92)
    glow_phone = _make_radial_glow(int(glow_base * 0.24), PHONE_BLUE, 84)
    glow_shield = _make_radial_glow(int(glow_base * 0.24), TEAL_SHIELD, 82)
    rug_glow_soft = Image.new("RGBA", (width, 220), (0, 0, 0, 0))
    ImageDraw.Draw(rug_glow_soft).ellipse([int(width * 0.08), 30, int(width * 0.76), 178], fill=(214, 178, 108, 42))
    rug_glow_soft = rug_glow_soft.filter(ImageFilter.GaussianBlur(radius=20))

    total_scenes = len(audio_bundle.scene_results)
    seg_videos: list[Path] = []
    scene_starts: list[float] = []
    cursor = 0.0

    for idx, scene_audio in enumerate(audio_bundle.scene_results, start=1):
        seg_dur = max(float(scene_audio.duration_sec) + pause_sec, 1.0)
        scene_starts.append(cursor)
        cursor += seg_dur

        s_raw = scenes_meta[idx - 1] if scenes_meta and idx - 1 < len(scenes_meta) else {"visual_headline": f"Part {idx}", "narration": scene_audio.text}
        sc = _map_blueprint_scene_to_cozy(s_raw, idx, total_scenes, seg_dur)
        stype = sc["scene_type"]
        words = _words_from_scene_audio(scene_audio)
        phrases = _chunk_phrases(words, max_words=9 if is_land else 7)
        gold_words = {re.sub(r"[^A-Z0-9]", "", str(w).upper()) for w in sc["gold_words"]}
        total_frames = max(int(round(seg_dur * fps)), fps)
        seg_mp4 = work_dir / f"seg_{idx:02d}.mp4"
        print(f"[v8.3-cozy] Rendering scene {idx}/{total_scenes} ({stype}, {seg_dur:.1f}s @ {fps}fps)...", flush=True)

        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}", "-r", str(fps), "-i", "pipe:0",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-an",
            str(seg_mp4),
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        assert proc.stdin is not None
        try:
            for f_i in range(total_frames):
                t = f_i / float(fps)
                p = _clamp01(t / max(seg_dur, 0.1))
                bob = int(round(math.sin(t * 2.8) * 4.5))
                env = min(_clamp01(t / 0.35), _clamp01((seg_dur - t) / 0.35))

                if stype == "bedroom_morning_scroll":
                    frame = bed_morning_bg.copy()
                    bx, by = bed_m_meta["bed_seat"]
                    sp = _pick_character_frame(c_sleepy, t, sway_deg=math.sin(t * 1.6) * 1.4)
                    _paste_alpha(frame, glow_phone, bx + 20 - glow_phone.width // 2, by - sp.height // 2 - glow_phone.height // 2)
                    _paste_alpha(frame, sp, bx - sp.width // 2, by - sp.height + 16 + bob)
                    for n_i, kind in enumerate(("chat", "bell")):
                        cyc = (t * 0.45 + n_i * 0.5) % 1.0
                        _draw_distraction_badge(frame, kind, int(bx + 80 + math.sin(cyc * 6.0 + n_i) * 24), int(by - sp.height * 0.72 - cyc * 130), 46, math.sin(cyc * math.pi) * 0.85)
                    _draw_pill_badge(frame, sc["pill"], int(height * (0.14 if is_land else 0.225)), _ease_out_cubic(t / 0.45), gold_style=False)

                elif stype == "bedroom_scroll_flood":
                    frame = bed_morning_bg.copy()
                    zoom_f = _lerp(1.06, 1.15, p)
                    zw, zh = int(width / zoom_f), int(height / zoom_f)
                    zx0, zy0 = int((width - zw) * 0.36), int((height - zh) * 0.44)
                    frame = _fast_downscale_rgba(frame.crop((zx0, zy0, zx0 + zw, zy0 + zh)), width, height)
                    cx_c, cy_c = int(width * 0.47), int(height * 0.625)
                    sp = _pick_character_frame(c_overwhelm_big, t, sway_deg=math.sin(t * 4.5) * 1.6)
                    _paste_alpha(frame, glow_phone, cx_c + 34 - glow_phone.width // 2, cy_c - sp.height // 2 - glow_phone.height // 2)
                    _paste_alpha(frame, sp, cx_c - sp.width // 2, cy_c - sp.height + bob)
                    for kind, dx_off, ph in [("play", -165, 0.0), ("heart", 145, 0.2), ("bell", -80, 0.4), ("chat", 190, 0.65)]:
                        cyc = (t * 0.55 + ph) % 1.0
                        _draw_distraction_badge(frame, kind, int(cx_c + dx_off * (0.5 + 0.5 * cyc)), int(cy_c - sp.height * 0.60 - cyc * 240), 52, math.sin(cyc * math.pi) * 0.90)
                    dots_lit = min(5, 1 + int((t / max(seg_dur * 0.72, 1.0)) * 4))
                    _draw_pill_badge(frame, sc["pill"], int(height * (0.12 if is_land else 0.185)), _ease_out_cubic(t / 0.45), gold_style=True, dots_count=5, dots_lit=dots_lit)

                elif stype == "desk_cognitive_fog":
                    frame = desk_laptop_bg.copy()
                    fy = desk_l_meta["floor_y"]
                    lap_x, lap_y = desk_l_meta["laptop_pos"]
                    sp = _pick_character_frame(c_overwhelm_desk, t, sway_deg=math.sin(t * 2.5) * 1.2)
                    _paste_alpha(frame, glow_phone, lap_x - glow_phone.width // 2, lap_y - glow_phone.height // 2)
                    _paste_alpha(frame, sp, int(width * (0.20 if is_land else 0.33)) - sp.width // 2, fy - sp.height + 28 + bob)
                    card_a = min(_ease_out_cubic((t - 0.25) / 0.55), _clamp01((seg_dur - t) / 0.40))
                    _draw_pastel_explainer_card(frame, sc["card_title"], sc["card_cite"], sc["card_rows"], t, card_a, sc["row_triggers"])

                elif stype == "focus_shield_repel":
                    frame = desk_calm_bg.copy()
                    lx, ly = desk_c_meta["lamp_pos"]
                    fy = desk_c_meta["floor_y"]
                    _paste_alpha(frame, glow_lamp, lx - glow_lamp.width // 2, ly - glow_lamp.height // 2 + 35)
                    _paste_alpha(frame, rug_glow_soft, 0, fy - 24)
                    _draw_coffee_steam(frame, *desk_c_meta["coffee_pos"], t)
                    sp = _pick_character_frame(c_protected, t, sway_deg=math.sin(t * 1.4) * 1.0)
                    ch_x = int(width * 0.35)
                    ch_y = fy - sp.height + 28 + bob
                    ring_cx, ring_cy = ch_x, ch_y + sp.height // 2 - 12
                    sh_p = _ease_out_cubic((t - 0.25) / 0.65)
                    shield_r = int(round((176 if is_land else 196) * sh_p * (1.0 + 0.025 * math.sin(t * 3.4))))
                    if sh_p > 0.01:
                        _paste_alpha(frame, glow_shield, ring_cx - glow_shield.width // 2, ring_cy - glow_shield.height // 2)
                    _paste_alpha(frame, sp, ch_x - sp.width // 2, ch_y)
                    if sh_p > 0.01:
                        ring_ov = Image.new("RGBA", (shield_r * 2 + 40, shield_r * 2 + 40), (0, 0, 0, 0))
                        rc = shield_r + 20
                        ImageDraw.Draw(ring_ov).ellipse([rc - shield_r, rc - shield_r, rc + shield_r, rc + shield_r], outline=(*TEAL_SHIELD, int(235 * sh_p)), width=7)
                        _paste_alpha(frame, ring_ov, ring_cx - rc, ring_cy - rc)
                    for kind, deg, ph in [("play", -22.0, 0.0), ("bell", 160.0, 0.28), ("heart", -55.0, 0.56), ("chat", 205.0, 0.78)]:
                        cyc = (t * 0.42 + ph) % 1.0
                        ang = math.radians(deg)
                        if cyc < 0.45:
                            dist = _lerp(420.0, shield_r + 36.0, _ease_out_cubic(cyc / 0.45))
                            ba = _clamp01((cyc / 0.45) * 2.5)
                        else:
                            u = (cyc - 0.45) / 0.55
                            dist = _lerp(shield_r + 36.0, 490.0, _ease_out_cubic(u))
                            ba = max(0.0, 1.0 - u * 1.15)
                        _draw_distraction_badge(frame, kind, int(ring_cx + dist * math.cos(ang)), int(ring_cy + dist * math.sin(ang)), 50, ba * sh_p)
                    _draw_pill_badge(frame, sc["pill"], int(height * (0.12 if is_land else 0.175)), _ease_out_cubic(t / 0.45), gold_style=False)

                elif stype == "cozy_deep_work_desk":
                    frame = desk_calm_bg.copy()
                    lx, ly = desk_c_meta["lamp_pos"]
                    fy = desk_c_meta["floor_y"]
                    _paste_alpha(frame, glow_lamp, lx - glow_lamp.width // 2, ly - glow_lamp.height // 2 + 35)
                    _paste_alpha(frame, rug_glow_soft, 0, fy - 24)
                    _draw_coffee_steam(frame, *desk_c_meta["coffee_pos"], t)
                    sp = _pick_character_frame(c_focus, t, sway_deg=math.sin(t * 1.5) * 1.1)
                    ch_x, ch_y = int(width * 0.35), fy - sp.height + 28 + bob
                    _paste_alpha(frame, sp, ch_x - sp.width // 2, ch_y)
                    _draw_pill_badge(frame, sc["pill"], int(height * (0.12 if is_land else 0.175)), _ease_out_cubic(t / 0.45), gold_style=True)
                    _draw_speech_bubble(frame, sc["speech"], ch_x + 42, ch_y - 18, _ease_out_cubic((t - 1.0) / 0.45))

                elif stype == "neural_pathway_stars":
                    frame = neural_sky_bg.copy()
                    fy = neural_meta["floor_y"]
                    _draw_neural_constellation(frame, t, seg_dur, fy)
                    sp = _pick_character_frame(c_wonder, t, sway_deg=math.sin(t * 1.4) * 1.2)
                    _paste_alpha(frame, sp, int(width * (0.16 if is_land else 0.50)) - sp.width // 2, fy - sp.height + 24 + bob)
                    card_a = min(_ease_out_cubic((t - 0.25) / 0.55), _clamp01((seg_dur - t) / 0.40))
                    _draw_pastel_explainer_card(frame, sc["card_title"], sc["card_cite"], sc["card_rows"], t, card_a, sc["row_triggers"])

                else:
                    frame = bed_evening_bg.copy()
                    fy = bed_e_meta["floor_y"]
                    _paste_alpha(frame, rug_glow_soft, 0, fy - 24)
                    sp = _pick_character_frame(c_rest, t, sway_deg=math.sin(t * 1.2) * 1.0)
                    ch_x = int(width * (0.14 if is_land else 0.44))
                    ch_y = fy - sp.height + 28 + bob
                    _paste_alpha(frame, sp, ch_x - sp.width // 2, ch_y)
                    _draw_pill_badge(frame, sc["pill"], int(height * (0.11 if is_land else 0.205)), _ease_out_cubic(t / 0.45), gold_style=True)
                    _draw_closing_dual_cards(frame, sc["left_card"], sc["right_card"], t_sec=t, alpha=env)

                _draw_serif_karaoke_subtitles(frame, t, phrases, gold_words)
                rgb_img = frame.convert("RGB")
                if env < 0.998:
                    arr = np.asarray(rgb_img, dtype=np.float32)
                    bg_v = np.array(FLOOR_DARK, dtype=np.float32)
                    arr = bg_v + (arr - bg_v) * env
                    proc.stdin.write(arr.astype(np.uint8).tobytes())
                else:
                    proc.stdin.write(rgb_img.tobytes())

            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", errors="ignore") if proc.stderr else ""
            ret = proc.wait()
            if ret != 0:
                raise RuntimeError(f"FFmpeg v8.3 render failed ({ret}): {err[-300:]}")
        finally:
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()

        seg_videos.append(seg_mp4)

    vlist = work_dir / "v.txt"
    vlist.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in seg_videos), encoding="utf-8")
    merged_v = work_dir / "merged_v.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(vlist), "-c", "copy", str(merged_v)], capture_output=True, check=True)

    master_audio = Path(audio_bundle.master_audio_path)
    mixed_a = work_dir / "mixed_cozy.m4a"
    final_a = _mix_cozy_soundscape(master_audio, scene_starts, float(audio_bundle.total_duration_sec), mixed_a, work_dir)

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


HABITSAINS_COZY_DEMO_SCENES: list[dict[str, Any]] = [
    {
        "scene_type": "bedroom_morning_scroll",
        "pill": "morning autopilot",
        "narration": "Most mornings, we grab our phone before our feet even touch the floor. It feels completely harmless.",
        "gold_words": ["PHONE", "HARMLESS"],
    },
    {
        "scene_type": "bedroom_scroll_flood",
        "pill": "without realizing",
        "narration": "We scroll through forty clips on autopilot, without realizing what it quietly does to our brain.",
        "gold_words": ["AUTOPILOT", "BRAIN"],
    },
    {
        "scene_type": "desk_cognitive_fog",
        "narration": "Neuroscientists call this attention residue. Fifteen minutes of scrolling triggers rapid dopamine spikes, leaves static in working memory, and costs twenty-three minutes of deep focus.",
        "gold_words": ["ATTENTION", "RESIDUE", "DOPAMINE", "TWENTYTHREE"],
        "card_title": "ATTENTION RESIDUE",
        "card_cite": "UC IRVINE • COGNITIVE FOCUS STUDY",
        "row_triggers": [2.4, 6.0, 9.2],
        "card_rows": [
            {"headline": "15-Minute Scroll", "sub": "triggers rapid dopamine spikes"},
            {"headline": "Working Memory Static", "sub": "old clips linger behind new tasks"},
            {"headline": "23-Minute Focus Tax", "sub": "time required to reach deep flow"},
        ],
    },
    {
        "scene_type": "focus_shield_repel",
        "pill": "distraction blocked",
        "narration": "When you protect your first quiet hour, mental noise loses its grip, and clarity returns naturally.",
        "gold_words": ["PROTECT", "CLARITY"],
    },
    {
        "scene_type": "cozy_deep_work_desk",
        "pill": "start in stillness",
        "speech": "deep focus...",
        "narration": "Step into your morning desk in quiet stillness. Let your nervous system wake up before the feeds rush in.",
        "gold_words": ["STILLNESS", "FEEDS"],
    },
    {
        "scene_type": "neural_pathway_stars",
        "narration": "First, delay social feeds for sixty minutes to protect peak morning energy. Second, take a two-minute stillness bridge to clear residue before deep work.",
        "gold_words": ["SIXTY", "STILLNESS", "DEEP"],
        "card_title": "THE NEURAL RESET",
        "card_cite": "HABITSAINS • DAILY FOCUS PROTOCOL",
        "row_triggers": [0.9, 5.2],
        "card_rows": [
            {"headline": "Delay Feeds 60 Minutes", "sub": "protect peak morning prefrontal energy"},
            {"headline": "2-Minute Stillness Bridge", "sub": "clear residue before starting deep work"},
        ],
    },
    {
        "scene_type": "closing_dual_cards",
        "pill": "Two small daily habits",
        "narration": "Starting today, keep these two small habits in place. Protect your morning shield, and lock in your evening reset.",
        "gold_words": ["HABITS", "MORNING", "EVENING"],
        "left_card": {"title": "MORNING SHIELD", "sub": "no feeds first hour", "icon": "shield_sun"},
        "right_card": {"title": "EVENING RESET", "sub": "phone across the room", "icon": "moon_phone_off"},
    },
]


if __name__ == "__main__":
    import json

    out_file = Path("output/_v8_cozy_diorama_demo/habitsains_cozy_diorama_demo_9x16.mp4")
    info = build_cozy_diorama_demo(HABITSAINS_COZY_DEMO_SCENES, out_file)
    print("V8.2 DEMO COMPLETE:", json.dumps(info, indent=2))
