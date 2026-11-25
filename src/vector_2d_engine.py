"""Studio v5 — Flat Vector 2D Explainer Animation Engine (Kurzgesagt / TED-Ed style, True 30fps).

Uses 2x-supersampled Pillow vector sprite layers + Gaussian glows + smooth NumPy/OpenCV
real-time compositing piped straight into FFmpeg H.264. 100% free locally and on GitHub Actions.

Five distinct animated 2D vector storytelling scenes:
  1. vector_desk_brain    : Cozy indigo room, blinking/typing character at glowing laptop,
                            coral vector brain overhead with meshing rotating teal gears,
                            floating amber notification bubbles drifting toward starry window.
  2. vector_brain_factory : Stylized vector brain silhouette with glowing neural tracks,
                            racing cyan/gold energy orbs, and rotating interlocking gears.
  3. vector_dopamine_lab  : Vibrant flat-vector science gauges & animated dual area wave
                            (coral-amber spike & crash vs calm rising teal flow) + rising bubbles.
  4. vector_path_bridge   : Geometric twilight canyon where 3 luminous teal stepping-stone
                            protocol arches build sequentially while a glowing traveler advances.
  5. vector_sunrise_growth: Twilight-to-dawn horizon with rising golden sun, blooming geometric
                            teal/gold tree canopy, drifting clouds, and 7 lighting milestone orbs.
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
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from src.config_loader import resolve_font_path


# Kurzgesagt-inspired rich flat-vector palette (RGB)
COL_INDIGO_DARK = (18, 19, 56)
COL_INDIGO_MID = (29, 32, 82)
COL_INDIGO_LIGHT = (46, 51, 114)
COL_TEAL = (45, 212, 191)
COL_CYAN = (56, 189, 248)
COL_CORAL = (255, 118, 102)
COL_PEACH = (255, 174, 138)
COL_MAGENTA = (186, 62, 128)
COL_AMBER = (251, 191, 36)
COL_ORANGE = (249, 115, 22)
COL_WHITE = (248, 250, 252)
COL_LAVENDER = (199, 210, 254)
COL_SKIN = (252, 194, 152)
COL_SKIN_SHADE = (232, 158, 118)
COL_HAIR = (26, 30, 82)
COL_DESK = (58, 176, 174)
COL_DESK_DARK = (32, 112, 126)


def _ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def _ease_out_back(t: float) -> float:
    t = max(0.0, min(1.0, t))
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * ((t - 1.0) ** 3) + c1 * ((t - 1.0) ** 2)


def _load_font(preferred: str | None, size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    fp = resolve_font_path(preferred, bold=bold)
    if fp:
        try:
            return ImageFont.truetype(fp, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def _pil_to_np(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("RGBA"), dtype=np.uint8)


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
    sub = sprite_rgba[sy0:sy1, sx0:sx1]
    a = (sub[:, :, 3:4].astype(np.float32) / 255.0) * float(alpha_mult)
    dst = frame_rgb[y0:y1, x0:x1].astype(np.float32)
    src = sub[:, :, :3].astype(np.float32)
    frame_rgb[y0:y1, x0:x1] = np.clip(src * a + dst * (1.0 - a), 0, 255).astype(np.uint8)


def _rotate_rgba(sprite_rgba: np.ndarray, angle_deg: float) -> np.ndarray:
    h, w = sprite_rgba.shape[:2]
    mat = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), angle_deg, 1.0)
    return cv2.warpAffine(sprite_rgba, mat, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


def _scale_rgba(sprite_rgba: np.ndarray, scale: float) -> np.ndarray:
    if abs(scale - 1.0) < 0.005:
        return sprite_rgba
    h, w = sprite_rgba.shape[:2]
    nw, nh = max(2, int(round(w * scale))), max(2, int(round(h * scale)))
    return cv2.resize(sprite_rgba, (nw, nh), interpolation=cv2.INTER_LINEAR)


def _make_glow_circle(radius: int, color: tuple[int, int, int], max_alpha: int = 110) -> np.ndarray:
    size = radius * 2
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    dist = np.hypot(xx - radius, yy - radius) / max(float(radius), 1.0)
    falloff = np.clip(1.0 - dist, 0.0, 1.0) ** 2.1
    out = np.zeros((size, size, 4), dtype=np.uint8)
    out[:, :, 0] = color[0]
    out[:, :, 1] = color[1]
    out[:, :, 2] = color[2]
    out[:, :, 3] = np.clip(falloff * max_alpha, 0, 255).astype(np.uint8)
    return out


def _make_gear_sprite(radius: int, teeth: int, color: tuple[int, int, int], inner_color: tuple[int, int, int]) -> np.ndarray:
    """Crisp 2x supersampled flat-vector toothed gear sprite."""
    ss = 2
    r = radius * ss
    pad = int(r * 0.42)
    size = (r + pad) * 2
    cx = cy = size // 2
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    pts: list[tuple[float, float]] = []
    outer_r = r * 1.0
    root_r = r * 0.78
    step = math.tau / teeth
    for i in range(teeth):
        a0 = i * step
        a1 = a0 + step * 0.20
        a2 = a0 + step * 0.48
        a3 = a0 + step * 0.68
        pts.extend([
            (cx + math.cos(a0) * root_r, cy + math.sin(a0) * root_r),
            (cx + math.cos(a1) * outer_r, cy + math.sin(a1) * outer_r),
            (cx + math.cos(a2) * outer_r, cy + math.sin(a2) * outer_r),
            (cx + math.cos(a3) * root_r, cy + math.sin(a3) * root_r),
        ])
    d.polygon(pts, fill=(*color, 255))
    inner_r = int(r * 0.50)
    d.ellipse((cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r), fill=(*inner_color, 255))
    hole_r = int(r * 0.25)
    d.ellipse((cx - hole_r, cy - hole_r, cx + hole_r, cy + hole_r), fill=(0, 0, 0, 0))

    img = img.resize((size // ss, size // ss), Image.Resampling.LANCZOS)
    return _pil_to_np(img)


def _make_brain_sprite(scale: float = 1.0) -> np.ndarray:
    """Kurzgesagt-style layered coral-peach-magenta flat-vector brain silhouette."""
    ss = 2
    w, h = int(420 * scale * ss), int(320 * scale * ss)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w // 2, int(h * 0.48)

    # Outer coral-peach cloud lobes forming iconic Kurzgesagt brain silhouette
    lobes = [
        (-118, -18, 72), (-90, -76, 68), (-22, -92, 74), (54, -84, 72),
        (114, -38, 68), (124, 24, 62), (76, 62, 58), (6, 60, 62),
        (-68, 56, 60), (-118, 28, 56),
    ]
    # Soft magenta drop-lobe shadow
    for lx, ly, lr in lobes:
        x, y, r = cx + int(lx * scale * ss), cy + int((ly + 14) * scale * ss), int(lr * scale * ss)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(*COL_MAGENTA, 255))
    # Brain stem
    stem_pts = [
        (cx - int(18 * scale * ss), cy + int(70 * scale * ss)),
        (cx + int(22 * scale * ss), cy + int(70 * scale * ss)),
        (cx + int(10 * scale * ss), cy + int(136 * scale * ss)),
        (cx - int(22 * scale * ss), cy + int(128 * scale * ss)),
    ]
    d.polygon(stem_pts, fill=(*COL_MAGENTA, 255))

    # Warm peach top rim highlights (solid opaque pastel for crisp Kurzgesagt flat-vector look)
    for lx, ly, lr in [(-90, -76, 56), (-22, -92, 62), (54, -84, 58), (114, -38, 52)]:
        x, y, r = cx + int(lx * scale * ss), cy + int((ly - 6) * scale * ss), int(lr * scale * ss)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 162, 134, 255))

    # Main bright coral lobes layered cleanly below rim
    for lx, ly, lr in lobes:
        x, y, r = cx + int(lx * scale * ss), cy + int((ly + 4) * scale * ss), int(lr * scale * ss)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(*COL_CORAL, 255))

    # Inner deep plum cavity (gives crisp contrast behind rotating teal gears!)
    inner_w, inner_h = int(146 * scale * ss), int(94 * scale * ss)
    d.ellipse((cx - inner_w, cy - inner_h, cx + inner_w, cy + inner_h), fill=(72, 22, 88, 255))
    inner_w2, inner_h2 = int(130 * scale * ss), int(78 * scale * ss)
    d.ellipse((cx - inner_w2, cy - inner_h2, cx + inner_w2, cy + inner_h2), fill=(44, 18, 74, 255))

    img = img.resize((w // ss, h // ss), Image.Resampling.LANCZOS)
    return _pil_to_np(img)


def _make_notif_bubble(kind: str, scale: float = 1.0) -> np.ndarray:
    """Warm amber/orange rounded speech-bubble notification with vector icon."""
    ss = 2
    w, h = int(112 * scale * ss), int(104 * scale * ss)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bg = COL_AMBER if kind != "alert" else (255, 148, 72)
    fg = (124, 45, 18)

    pad = int(10 * scale * ss)
    box_b = int(76 * scale * ss)
    d.rounded_rectangle((pad, pad, w - pad, box_b), radius=int(18 * scale * ss), fill=(*bg, 255))
    # Speech tail
    d.polygon([
        (int(34 * scale * ss), box_b - 2),
        (int(52 * scale * ss), box_b - 2),
        (int(30 * scale * ss), int(94 * scale * ss)),
    ], fill=(*bg, 255))

    cx, cy = w // 2, (pad + box_b) // 2
    s = scale * ss
    if kind == "bell":
        d.pieslice((cx - int(15 * s), cy - int(16 * s), cx + int(15 * s), cy + int(14 * s)), 180, 360, fill=(*fg, 255))
        d.rectangle((cx - int(15 * s), cy - int(2 * s), cx + int(15 * s), cy + int(10 * s)), fill=(*fg, 255))
        d.rounded_rectangle((cx - int(20 * s), cy + int(8 * s), cx + int(20 * s), cy + int(14 * s)), radius=int(3 * s), fill=(*fg, 255))
        d.ellipse((cx - int(5 * s), cy + int(13 * s), cx + int(5 * s), cy + int(21 * s)), fill=(*fg, 255))
    elif kind == "chat":
        for dy, lw in [(-10, 22), (0, 26), (10, 16)]:
            d.rounded_rectangle((cx - int(22 * s), cy + int((dy - 3) * s), cx - int(22 * s) + int(lw * 1.7 * s), cy + int((dy + 3) * s)), radius=int(3 * s), fill=(*fg, 255))
    else:
        # Checkmark
        pts = [(cx - int(16 * s), cy + int(1 * s)), (cx - int(4 * s), cy + int(13 * s)), (cx + int(18 * s), cy - int(12 * s))]
        d.line(pts, fill=(*fg, 255), width=max(4, int(7 * s)), joint="curve")

    img = img.resize((w // ss, h // ss), Image.Resampling.LANCZOS)
    return _pil_to_np(img)


def _make_character_sprites(scale: float = 1.0) -> dict[str, np.ndarray]:
    """Friendly Kurzgesagt/TED-Ed minimalist vector character (body + head open/blink + desk/laptop)."""
    ss = 2
    s = scale * ss

    # 1. Body + chair torso
    bw, bh = int(340 * s), int(300 * s)
    body = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    db = ImageDraw.Draw(body)
    # Chair back
    db.rounded_rectangle((int(34 * s), int(56 * s), int(106 * s), int(288 * s)), radius=int(24 * s), fill=(62, 54, 118, 255))
    # Sweater torso (layered teal shading)
    db.rounded_rectangle((int(76 * s), int(76 * s), int(238 * s), int(292 * s)), radius=int(72 * s), fill=(36, 118, 134, 255))
    db.rounded_rectangle((int(92 * s), int(76 * s), int(222 * s), int(292 * s)), radius=int(64 * s), fill=(48, 152, 164, 255))
    # Neck
    db.rounded_rectangle((int(142 * s), int(46 * s), int(184 * s), int(104 * s)), radius=int(16 * s), fill=(*COL_SKIN_SHADE, 255))
    # Forearm reaching forward to laptop
    db.rounded_rectangle((int(156 * s), int(196 * s), int(288 * s), int(252 * s)), radius=int(26 * s), fill=(58, 178, 184, 255))
    db.ellipse((int(260 * s), int(204 * s), int(306 * s), int(248 * s)), fill=(*COL_SKIN, 255))
    body_np = _pil_to_np(body.resize((bw // ss, bh // ss), Image.Resampling.LANCZOS))

    # 2. Head (eyes open & eyes blinking)
    def _build_head(blink: bool) -> np.ndarray:
        hw, hh = int(190 * s), int(196 * s)
        himg = Image.new("RGBA", (hw, hh), (0, 0, 0, 0))
        dh = ImageDraw.Draw(himg)
        # Ear
        dh.ellipse((int(30 * s), int(84 * s), int(62 * s), int(118 * s)), fill=(*COL_SKIN_SHADE, 255))
        # Face rounded oval
        dh.rounded_rectangle((int(44 * s), int(38 * s), int(156 * s), int(166 * s)), radius=int(50 * s), fill=(*COL_SKIN, 255))
        # Stylized flat-vector hair sweep
        dh.pieslice((int(34 * s), int(14 * s), int(164 * s), int(126 * s)), 175, 360, fill=(*COL_HAIR, 255))
        dh.rounded_rectangle((int(34 * s), int(46 * s), int(72 * s), int(106 * s)), radius=int(18 * s), fill=(*COL_HAIR, 255))
        dh.ellipse((int(88 * s), int(14 * s), int(166 * s), int(78 * s)), fill=(*COL_HAIR, 255))
        # Subtle soft rosy cheek (solid warm blush pastel)
        dh.ellipse((int(76 * s), int(108 * s), int(96 * s), int(121 * s)), fill=(248, 152, 138, 255))
        # Eyes
        if blink:
            dh.arc((int(88 * s), int(90 * s), int(106 * s), int(104 * s)), 10, 170, fill=(*COL_HAIR, 255), width=max(2, int(4 * s)))
            dh.arc((int(124 * s), int(90 * s), int(142 * s), int(104 * s)), 10, 170, fill=(*COL_HAIR, 255), width=max(2, int(4 * s)))
        else:
            dh.ellipse((int(91 * s), int(88 * s), int(103 * s), int(104 * s)), fill=(*COL_HAIR, 255))
            dh.ellipse((int(127 * s), int(88 * s), int(139 * s), int(104 * s)), fill=(*COL_HAIR, 255))
        # Friendly calm smile
        dh.arc((int(100 * s), int(114 * s), int(130 * s), int(136 * s)), 15, 165, fill=(140, 62, 52, 255), width=max(2, int(4 * s)))
        return _pil_to_np(himg.resize((hw // ss, hh // ss), Image.Resampling.LANCZOS))

    # 3. Laptop + potted succulent plant
    lw, lh = int(340 * s), int(170 * s)
    lap = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lap)
    # Laptop screen angled
    dl.polygon([(int(34 * s), int(144 * s)), (int(66 * s), int(38 * s)), (int(210 * s), int(38 * s)), (int(180 * s), int(144 * s))], fill=(62, 74, 146, 255))
    dl.polygon([(int(46 * s), int(136 * s)), (int(74 * s), int(48 * s)), (int(198 * s), int(48 * s)), (int(172 * s), int(136 * s))], fill=(76, 94, 174, 255))
    # Glowing teal logo dot on laptop back
    dl.ellipse((int(114 * s), int(82 * s), int(138 * s), int(106 * s)), fill=(*COL_TEAL, 255))
    # Base
    dl.rounded_rectangle((int(16 * s), int(138 * s), int(218 * s), int(156 * s)), radius=int(8 * s), fill=(116, 134, 198, 255))
    # Potted plant on right
    px = int(272 * s)
    dl.polygon([(px - int(22 * s), int(110 * s)), (px + int(22 * s), int(110 * s)), (px + int(16 * s), int(156 * s)), (px - int(16 * s), int(156 * s))], fill=(46, 136, 146, 255))
    for dx, dy, rx, ry, col in [(-12, 86, 14, 24, COL_TEAL), (0, 74, 14, 30, (34, 197, 168)), (14, 88, 13, 22, COL_TEAL)]:
        dl.ellipse((px + int((dx - rx) * s), int((dy - ry) * s), px + int((dx + rx) * s), int((dy + ry) * s)), fill=(*col, 255))
    lap_np = _pil_to_np(lap.resize((lw // ss, lh // ss), Image.Resampling.LANCZOS))

    return {
        "body": body_np,
        "head_open": _build_head(False),
        "head_blink": _build_head(True),
        "laptop_plant": lap_np,
    }


def _make_cloud_sprite(w_px: int, h_px: int, color: tuple[int, int, int], alpha: int = 190) -> np.ndarray:
    img = Image.new("RGBA", (w_px, h_px), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = h_px // 2
    d.rounded_rectangle((r // 2, h_px // 2, w_px - r // 2, h_px), radius=r // 2, fill=(*color, alpha))
    for fx, fy, fr in [(0.26, 0.55, 0.36), (0.48, 0.42, 0.46), (0.72, 0.56, 0.34)]:
        cx, cy, rad = int(w_px * fx), int(h_px * fy), int(h_px * fr)
        d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=(*color, alpha))
    return _pil_to_np(img)


def _make_text_sprite(
    text: str,
    font: ImageFont.ImageFont,
    color: tuple[int, int, int],
    max_width: int,
    max_lines: int = 2,
    align: str = "left",
) -> np.ndarray:
    dummy = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(dummy)
    words = text.split()
    lines: list[str] = []
    if words:
        cur = words[0]
        for w in words[1:]:
            cand = f"{cur} {w}"
            bb = d.textbbox((0, 0), cand, font=font)
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
            bb = d.textbbox((0, 0), tail, font=font)
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

    boxes = [d.textbbox((0, 0), l, font=font) for l in lines]
    widths = [b[2] - b[0] for b in boxes]
    heights = [b[3] - b[1] for b in boxes]
    base_h = max(heights) if heights else 24
    step_y = int(base_h * 1.18)
    pad = 10
    sw = max(widths) + pad * 2
    sh = step_y * (len(lines) - 1) + base_h + pad * 2 + 6
    img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    idraw = ImageDraw.Draw(img)
    y = pad
    for line, lw, bb in zip(lines, widths, boxes):
        x = (sw - lw) // 2 if align == "center" else (sw - pad - lw if align == "right" else pad)
        idraw.text((x + 3, y + 3 - bb[1]), line, font=font, fill=(10, 10, 32, 195))
        idraw.text((x, y - bb[1]), line, font=font, fill=(*color, 255))
        y += step_y
    return _pil_to_np(img)


def _make_pill_sprite(text: str, font: ImageFont.ImageFont, bg: tuple[int, int, int], fg: tuple[int, int, int]) -> np.ndarray:
    dummy = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(dummy)
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    px, py = 22, 9
    w, h = tw + px * 2 + 4, th + py * 2 + 4
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    idraw = ImageDraw.Draw(img)
    idraw.rounded_rectangle((2, 2, w - 2, h - 2), radius=(h - 4) // 2, fill=(*bg, 240))
    idraw.text((px + 2, py + 2 - bb[1]), text, font=font, fill=(*fg, 255))
    return _pil_to_np(img)


def _pick_vector_scene_type(scene: dict[str, Any], idx: int) -> str:
    explicit = str(scene.get("vector_scene") or "").strip().lower()
    valid = ("vector_desk_brain", "vector_brain_factory", "vector_dopamine_lab", "vector_path_bridge", "vector_sunrise_growth")
    if explicit in valid:
        return explicit
    header = f"{scene.get('section', '')} {scene.get('visual_headline', '')}".lower()
    if idx == 1:
        return "vector_desk_brain"
    if any(k in header for k in ("7-day", "challenge", "experiment", "sunrise", "habit lab")):
        return "vector_sunrise_growth"
    if any(k in header for k in ("protocol", "step", "reset", "bridge", "shield", "automaticity", "fix")):
        return "vector_path_bridge"
    if any(k in header for k in ("dopamine", "boring", "trap", "spike", "crash", "dip", "missing")):
        return "vector_dopamine_lab"
    if any(k in header for k in ("mechanism", "residue", "neuron", "neural", "highway", "brain", "data", "science")):
        return "vector_brain_factory"
    return valid[(idx - 1) % len(valid)]


def _extract_steps(scene: dict[str, Any]) -> list[str]:
    bullets = [str(b).lstrip("0123456789.-) ").strip() for b in (scene.get("bullet_points") or []) if str(b).strip()]
    if len(bullets) >= 3:
        return bullets[:3]
    callout = str(scene.get("on_screen_callout") or "").strip()
    if "," in callout and len(callout.split(",")) >= 3:
        return [p.strip().capitalize() for p in callout.split(",")[:3]]
    return ["Anchor Cue", "Shrink Start", "Repeat Calmly"]


def _make_indigo_backdrop(w: int, h: int, top_col: tuple[int, int, int], bot_col: tuple[int, int, int]) -> np.ndarray:
    y = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    c0 = np.array(top_col, dtype=np.float32)[None, None, :]
    c1 = np.array(bot_col, dtype=np.float32)[None, None, :]
    col_strip = np.clip(c0 * (1.0 - y) + c1 * y, 0, 255).astype(np.uint8)
    return np.ascontiguousarray(np.repeat(col_strip, w, axis=1))


def render_flat_vector_scene_segment(
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
    """Render a true 30fps Kurzgesagt / TED-Ed Flat Vector 2D Explainer MP4 segment."""
    branding = config.get("branding", {})
    handle = str(branding.get("watermark_text", "@HabitSains"))
    scene_type = _pick_vector_scene_type(scene, scene_idx)
    total_frames = max(int(round(duration_sec * fps)), fps)
    rng = random.Random(scene_idx * 431 + (29 if is_short else 7))

    f_badge = _load_font(branding.get("font_bold"), 28 if is_short else 24, bold=True)
    f_head = _load_font(branding.get("font_bold"), 64 if is_short else 56, bold=True)
    f_meta = _load_font(branding.get("font_bold"), 26 if is_short else 22, bold=True)
    f_step = _load_font(branding.get("font_bold"), 30 if is_short else 28, bold=True)

    sec_label = str(scene.get("badge") or scene.get("section") or f"PART {scene_idx}").upper()
    if not is_short:
        sec_label = f"{scene_idx:02d}/{total_scenes:02d}  •  {sec_label}"
    badge_sp = _make_pill_sprite(sec_label, f_badge, bg=COL_TEAL, fg=COL_INDIGO_DARK)
    handle_sp = _make_text_sprite(handle, f_meta, COL_LAVENDER, max_width=360, max_lines=1, align="right")
    headline = str(scene.get("visual_headline") or "HabitSains")
    head_sp = _make_text_sprite(headline, f_head, COL_WHITE, max_width=int(width * (0.86 if is_short else 0.56)), max_lines=2, align="center" if is_short else "left")

    # Shared Kurzgesagt vector sprites
    scale_base = 0.86 if is_short else 1.0
    brain_sp = _make_brain_sprite(scale=1.02 * scale_base)
    gear_big = _make_gear_sprite(int(50 * scale_base), 10, COL_TEAL, (20, 128, 128))
    gear_med = _make_gear_sprite(int(36 * scale_base), 8, COL_CYAN, (24, 108, 152))
    gear_sm = _make_gear_sprite(int(26 * scale_base), 7, COL_AMBER, (176, 108, 22))
    teal_glow_lg = _make_glow_circle(int(260 * scale_base), COL_TEAL, max_alpha=95)
    amber_glow_md = _make_glow_circle(int(180 * scale_base), COL_AMBER, max_alpha=88)
    char_sprites = _make_character_sprites(scale=0.92 * scale_base)
    notifs = [
        (_make_notif_bubble("bell", 0.85 * scale_base), 0.0),
        (_make_notif_bubble("chat", 0.82 * scale_base), 1.3),
        (_make_notif_bubble("bell", 0.78 * scale_base), 2.6),
        (_make_notif_bubble("check", 0.80 * scale_base), 3.9),
        (_make_notif_bubble("check", 0.75 * scale_base), 5.1),
    ]
    cloud_sp_1 = _make_cloud_sprite(int(240 * scale_base), int(84 * scale_base), (56, 86, 148), alpha=185)
    cloud_sp_2 = _make_cloud_sprite(int(180 * scale_base), int(64 * scale_base), (44, 68, 126), alpha=165)

    # Precompute static scene backdrop & pre-scaled sprites outside the 30fps loop for maximum speed
    if scene_type == "vector_sunrise_growth":
        base_bg = _make_indigo_backdrop(width, height, (22, 24, 72), (56, 44, 96))
    else:
        base_bg = _make_indigo_backdrop(width, height, COL_INDIGO_DARK, COL_INDIGO_MID)

    big_brain_sp = _scale_rgba(brain_sp, 1.50 if not is_short else 1.22)
    gear_big_lg = _scale_rgba(gear_big, 1.32)
    gear_med_lg = _scale_rgba(gear_med, 1.32)
    gear_sm_lg = _scale_rgba(gear_sm, 1.32)

    win_rect = (
        (int(width * 0.60), int(height * 0.14), int(width * 0.94), int(height * 0.70))
        if not is_short
        else (int(width * 0.52), int(height * 0.24), int(width * 0.94), int(height * 0.56))
    )
    if scene_type == "vector_desk_brain":
        wx0, wy0, wx1, wy1 = win_rect
        beam = np.zeros_like(base_bg)
        b_pts = np.array([[wx0, wy0 + 20], [wx0, wy1], [int(width * 0.22), height], [int(width * 0.18), int(height * 0.62)]], dtype=np.int32)
        cv2.fillPoly(beam, [b_pts], (38, 66, 118))
        cv2.addWeighted(beam, 0.22, base_bg, 1.0, 0, base_bg)
    stars = [
        (rng.randint(int(width * 0.05), int(width * 0.95)), rng.randint(int(height * 0.08), int(height * 0.75)), rng.randint(2, 5), rng.uniform(0, math.tau))
        for _ in range(42)
    ]

    # Step badges for vector_path_bridge
    bridge_steps = _extract_steps(scene)
    bridge_sprites = [
        _make_pill_sprite(f"{i+1}. {st[:24]}", f_step, bg=COL_INDIGO_LIGHT, fg=COL_WHITE)
        for i, st in enumerate(bridge_steps)
    ]

    # Pipe raw RGB24 straight to FFmpeg
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}", "-r", str(fps), "-i", "pipe:0",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an",
        str(out_mp4),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    fade_frames = max(int(fps * 0.35), 1)

    try:
        for f_idx in range(total_frames):
            t = f_idx / float(fps)
            prog = f_idx / float(max(total_frames - 1, 1))
            frame = base_bg.copy()

            # ------------------------------------------------------------------
            # SCENE 1: KURZGESAGT DESK + BLINKING CHARACTER + ROTATING BRAIN GEARS + WINDOW
            # ------------------------------------------------------------------
            if scene_type == "vector_desk_brain":
                wx0, wy0, wx1, wy1 = win_rect
                # Night sky window interior
                cv2.rectangle(frame, (wx0, wy0), (wx1, wy1), (14, 24, 68), -1)
                # Twinkling stars inside window
                for sx, sy, sr, sph in stars:
                    if wx0 + 12 < sx < wx1 - 12 and wy0 + 12 < sy < wy1 - 12:
                        tw = 0.55 + 0.45 * math.sin(t * 2.8 + sph)
                        col = tuple(int(c * tw) for c in (COL_AMBER if sr > 3 else COL_TEAL))
                        cv2.circle(frame, (sx, sy), sr, col, -1, lineType=cv2.LINE_AA)
                # Crescent moon
                mx, my = wx1 - int((wx1 - wx0) * 0.22), wy0 + int((wy1 - wy0) * 0.24)
                mr = int(34 * scale_base)
                cv2.circle(frame, (mx, my), mr, (254, 240, 138), -1, lineType=cv2.LINE_AA)
                cv2.circle(frame, (mx - int(mr * 0.38), my - int(mr * 0.14)), int(mr * 0.88), (14, 24, 68), -1, lineType=cv2.LINE_AA)
                # Slowly drifting clouds clipped to window
                c_shift = int((t * 18) % max((wx1 - wx0), 1))
                c_win_y = wy1 - cloud_sp_1.shape[0] - 8
                win_roi = frame[wy0:wy1, wx0:wx1]
                _blit_rgba(win_roi, cloud_sp_2, (c_shift - 60) % (wx1 - wx0) - 40, (wy1 - wy0) - cloud_sp_2.shape[0] - 46, 0.85)
                _blit_rgba(win_roi, cloud_sp_1, ((wx1 - wx0) - c_shift) - 80, (wy1 - wy0) - cloud_sp_1.shape[0] - 6, 0.92)
                # Window geometric mullions & sill
                cv2.rectangle(frame, (wx0, wy0), (wx1, wy1), (42, 64, 128), 12)
                mid_wx = (wx0 + wx1) // 2 + int((wx1 - wx0) * 0.08)
                cv2.line(frame, (mid_wx, wy0), (mid_wx, wy1), (42, 64, 128), 10)
                cv2.rectangle(frame, (wx0 - 14, wy1 - 6), (wx1 + 14, wy1 + 12), (62, 86, 152), -1)

                # Coordinates for desk, character, and floating brain
                desk_y = int(height * (0.76 if not is_short else 0.72))
                char_x = int(width * (0.14 if not is_short else 0.10))
                char_y = desk_y - int(char_sprites["body"].shape[0] * 0.82)
                bob = int(math.sin(t * 2.4) * 5)

                # Glowing teal halo behind brain
                brain_cx = int(width * (0.31 if not is_short else 0.34))
                brain_cy = int(height * (0.33 if not is_short else 0.42)) + int(math.sin(t * 1.9) * 8)
                _blit_rgba(frame, teal_glow_lg, brain_cx - teal_glow_lg.shape[1] // 2, brain_cy - teal_glow_lg.shape[0] // 2, 0.95)
                _blit_rgba(frame, brain_sp, brain_cx - brain_sp.shape[1] // 2, brain_cy - brain_sp.shape[0] // 2, 1.0)

                # 3 Meshing Rotating Teal/Cyan/Amber Gears inside the brain!
                ang = t * 52.0
                g1 = _rotate_rgba(gear_big, ang)
                g2 = _rotate_rgba(gear_med, -ang * 1.35 + 14)
                g3 = _rotate_rgba(gear_sm, ang * 1.65)
                _blit_rgba(frame, g1, brain_cx + int(22 * scale_base) - g1.shape[1] // 2, brain_cy - int(4 * scale_base) - g1.shape[0] // 2)
                _blit_rgba(frame, g2, brain_cx - int(48 * scale_base) - g2.shape[1] // 2, brain_cy - int(18 * scale_base) - g2.shape[0] // 2)
                _blit_rgba(frame, g3, brain_cx - int(32 * scale_base) - g3.shape[1] // 2, brain_cy + int(36 * scale_base) - g3.shape[0] // 2)

                # Floating amber notification bubbles drifting smoothly upward & right
                for idx_n, (nsp, phase) in enumerate(notifs):
                    nx_base = int(width * (0.46 + (idx_n % 2) * 0.08 if not is_short else 0.62 + (idx_n % 2) * 0.14))
                    ny_base = int(height * (0.18 + idx_n * 0.11 if not is_short else 0.28 + idx_n * 0.08))
                    nx = nx_base + int(math.sin(t * 1.6 + phase) * 14 + prog * 26)
                    ny = ny_base + int(math.cos(t * 2.1 + phase) * 12 - prog * 18)
                    _blit_rgba(frame, nsp, nx, ny, 0.96)

                # Character body + gentle head nod + periodic natural eye blink!
                is_blinking = (t % 3.6) > 3.44
                _blit_rgba(frame, char_sprites["body"], char_x, char_y + bob // 2)
                head_sp_cur = char_sprites["head_blink"] if is_blinking else char_sprites["head_open"]
                _blit_rgba(frame, head_sp_cur, char_x + int(68 * scale_base), char_y - int(84 * scale_base) + bob)

                # Laptop glow + laptop & plant
                lap_x = char_x + int(225 * scale_base)
                lap_y = desk_y - char_sprites["laptop_plant"].shape[0] + int(10 * scale_base)
                _blit_rgba(frame, teal_glow_lg, lap_x - 60, lap_y - 80, 0.38 + 0.08 * math.sin(t * 3.0))
                _blit_rgba(frame, char_sprites["laptop_plant"], lap_x, lap_y)

                # Clean flat-vector teal desk surface & legs
                desk_l = int(width * 0.07)
                desk_r = int(width * (0.64 if not is_short else 0.93))
                cv2.rectangle(frame, (desk_l + 36, desk_y + 18), (desk_l + 62, height), COL_DESK_DARK, -1)
                cv2.rectangle(frame, (desk_r - 62, desk_y + 18), (desk_r - 36, height), COL_DESK_DARK, -1)
                cv2.rectangle(frame, (desk_l, desk_y), (desk_r, desk_y + 22), COL_DESK, -1)
                cv2.rectangle(frame, (desk_l, desk_y + 16), (desk_r, desk_y + 24), COL_DESK_DARK, -1)

            # ------------------------------------------------------------------
            # SCENE 2: BRAIN FACTORY (LARGE VECTOR BRAIN + RACING NEURAL ORBS + GEARS)
            # ------------------------------------------------------------------
            elif scene_type == "vector_brain_factory":
                for sx, sy, sr, sph in stars:
                    tw = 0.5 + 0.5 * math.sin(t * 2.5 + sph)
                    cv2.circle(frame, (sx, sy), sr, tuple(int(c * tw) for c in COL_LAVENDER), -1, lineType=cv2.LINE_AA)
                cx, cy = width // 2, int(height * (0.55 if not is_short else 0.52))
                _blit_rgba(frame, teal_glow_lg, cx - teal_glow_lg.shape[1] // 2, cy - teal_glow_lg.shape[0] // 2, 1.0)
                _blit_rgba(frame, amber_glow_md, cx - amber_glow_md.shape[1] // 2, cy - amber_glow_md.shape[0] // 2, 0.7)

                # Radiating flat-vector neural highway beams with racing orbs
                for k in range(8):
                    ang_r = math.radians(k * 45 + 15)
                    r_in = int(170 * scale_base)
                    r_out = int((460 if not is_short else 340) * scale_base)
                    p0 = (int(cx + math.cos(ang_r) * r_in), int(cy + math.sin(ang_r) * r_in))
                    p1 = (int(cx + math.cos(ang_r) * r_out), int(cy + math.sin(ang_r) * r_out))
                    cv2.line(frame, p0, p1, (48, 88, 138), 6, lineType=cv2.LINE_AA)
                    u = (t * 0.75 + k * 0.19) % 1.0
                    ox = int(p0[0] + (p1[0] - p0[0]) * u)
                    oy = int(p0[1] + (p1[1] - p0[1]) * u)
                    col_orb = COL_AMBER if k % 2 == 0 else COL_TEAL
                    cv2.circle(frame, (ox, oy), 13, col_orb, -1, lineType=cv2.LINE_AA)
                    cv2.circle(frame, (ox, oy), 5, COL_WHITE, -1, lineType=cv2.LINE_AA)

                _blit_rgba(frame, big_brain_sp, cx - big_brain_sp.shape[1] // 2, cy - big_brain_sp.shape[0] // 2)
                ang = t * 60.0
                g1 = _rotate_rgba(gear_big_lg, ang)
                g2 = _rotate_rgba(gear_med_lg, -ang * 1.35 + 10)
                g3 = _rotate_rgba(gear_sm_lg, ang * 1.6)
                _blit_rgba(frame, g1, cx + int(36 * scale_base) - g1.shape[1] // 2, cy - g1.shape[0] // 2)
                _blit_rgba(frame, g2, cx - int(66 * scale_base) - g2.shape[1] // 2, cy - int(22 * scale_base) - g2.shape[0] // 2)
                _blit_rgba(frame, g3, cx - int(44 * scale_base) - g3.shape[1] // 2, cy + int(52 * scale_base) - g3.shape[0] // 2)

            # ------------------------------------------------------------------
            # SCENE 3: DOPAMINE LAB (COLOR-FILLED VECTOR AREA WAVE + ANIMATED GAUGES)
            # ------------------------------------------------------------------
            elif scene_type == "vector_dopamine_lab":
                for sx, sy, sr, sph in stars[:25]:
                    tw = 0.45 + 0.55 * math.sin(t * 2.2 + sph)
                    cv2.circle(frame, (sx, sy), sr, tuple(int(c * tw) for c in COL_TEAL), -1, lineType=cv2.LINE_AA)
                gx0, gx1 = int(width * 0.09), int(width * 0.91)
                gy_base = int(height * (0.76 if not is_short else 0.70))
                gy_mid = int(height * (0.55 if not is_short else 0.52))
                amp_y = int(height * (0.15 if not is_short else 0.11))

                # Flat-vector rounded dark dashboard card behind graph
                cv2.rectangle(frame, (gx0 - 24, gy_mid - amp_y - 44), (gx1 + 24, gy_base + 24), (24, 28, 74), -1)
                cv2.rectangle(frame, (gx0 - 24, gy_mid - amp_y - 44), (gx1 + 24, gy_base + 24), (62, 74, 146), 3)
                cv2.line(frame, (gx0, gy_mid), (gx1, gy_mid), (76, 92, 156), 2, lineType=cv2.LINE_AA)

                steps_n = max(2, int(150 * _ease_out_cubic(min(prog / 0.80, 1.0))))
                pts_coral: list[tuple[int, int]] = []
                pts_teal: list[tuple[int, int]] = []
                for k in range(steps_n):
                    u = k / 149.0
                    x = int(gx0 + (gx1 - gx0) * u)
                    y_c = int(gy_mid - (math.sin(u * 17.0 + t * 1.8) * (1.0 - 0.5 * u) - 0.35 * max(0.0, u - 0.35)) * amp_y * 0.88)
                    y_t = int(gy_mid - (math.sin(u * 6.5 - t * 1.5) * 0.34 + 0.24 * u) * amp_y)
                    pts_coral.append((x, y_c))
                    pts_teal.append((x, y_t))

                if len(pts_teal) >= 2:
                    gy_top = gy_mid - amp_y - 44
                    roi = frame[gy_top:gy_base + 1, gx0:gx1 + 1]
                    shifted_poly = np.array([(0, gy_base - gy_top)] + [(px - gx0, py - gy_top) for px, py in pts_teal] + [(pts_teal[-1][0] - gx0, gy_base - gy_top)], dtype=np.int32)
                    layer = roi.copy()
                    cv2.fillPoly(layer, [shifted_poly], COL_TEAL)
                    cv2.addWeighted(layer, 0.22, roi, 0.78, 0, roi)
                    cv2.polylines(frame, [np.array(pts_teal, dtype=np.int32)], False, COL_TEAL, 7, lineType=cv2.LINE_AA)
                    cv2.circle(frame, pts_teal[-1], 13, COL_TEAL, -1, lineType=cv2.LINE_AA)
                    cv2.circle(frame, pts_teal[-1], 5, COL_WHITE, -1, lineType=cv2.LINE_AA)
                if len(pts_coral) >= 2:
                    cv2.polylines(frame, [np.array(pts_coral, dtype=np.int32)], False, COL_CORAL, 6, lineType=cv2.LINE_AA)
                    cv2.circle(frame, pts_coral[-1], 12, COL_AMBER, -1, lineType=cv2.LINE_AA)
                    cv2.circle(frame, pts_coral[-1], 5, COL_WHITE, -1, lineType=cv2.LINE_AA)

            # ------------------------------------------------------------------
            # SCENE 4: PROTOCOL BRIDGE (STEPPING-STONE ARCHES BUILDING LIVE)
            # ------------------------------------------------------------------
            elif scene_type == "vector_path_bridge":
                for sx, sy, sr, sph in stars:
                    tw = 0.45 + 0.55 * math.sin(t * 2.4 + sph)
                    cv2.circle(frame, (sx, sy), sr, tuple(int(c * tw) for c in COL_AMBER), -1, lineType=cv2.LINE_AA)

                # Geometric twilight canyon cliffs on left & right
                horizon_y = int(height * (0.72 if not is_short else 0.68))
                left_cliff = np.array([[0, horizon_y - 30], [int(width * 0.20), horizon_y], [int(width * 0.14), height], [0, height]], dtype=np.int32)
                right_cliff = np.array([[int(width * 0.80), horizon_y], [width, horizon_y - 50], [width, height], [int(width * 0.86), height]], dtype=np.int32)
                cv2.fillPoly(frame, [left_cliff], (34, 38, 96))
                cv2.fillPoly(frame, [right_cliff], (34, 38, 96))

                # Glowing sunrise orb rising behind right cliff
                sun_x, sun_y = int(width * 0.86), int(horizon_y - 90 - prog * 35)
                _blit_rgba(frame, amber_glow_md, sun_x - amber_glow_md.shape[1] // 2, sun_y - amber_glow_md.shape[0] // 2, 0.9)
                cv2.circle(frame, (sun_x, sun_y), int(56 * scale_base), COL_AMBER, -1, lineType=cv2.LINE_AA)

                # 3 luminous stepping-stone arches rising into place sequentially
                stone_centers: list[tuple[int, int]] = []
                for s_i in range(3):
                    appear = s_i * 0.24 + 0.05
                    sp_p = _ease_out_back(min(max((prog - appear) / 0.18, 0.0), 1.0)) if prog >= appear else 0.0
                    sx = int(width * (0.28 + s_i * 0.22))
                    sy = int(horizon_y - 26 - s_i * (22 if not is_short else 34) + (1.0 - min(sp_p, 1.0)) * 120)
                    stone_centers.append((sx, sy))
                    if sp_p > 0.02:
                        pw = int((185 if not is_short else 160) * scale_base)
                        ph = int(34 * scale_base)
                        col_s = COL_TEAL if s_i < 2 else COL_AMBER
                        cv2.rectangle(frame, (sx - pw // 2, sy), (sx + pw // 2, sy + ph), col_s, -1)
                        cv2.rectangle(frame, (sx - pw // 2, sy + ph - 8), (sx + pw // 2, sy + ph), COL_DESK_DARK, -1)
                        # Floating step pill above arch
                        bsp = bridge_sprites[s_i]
                        _blit_rgba(frame, bsp, sx - bsp.shape[1] // 2, sy - bsp.shape[0] - 18, min(sp_p, 1.0))

                # Glowing traveler orb hopping cleanly across built arches!
                if stone_centers:
                    hop_u = min(max((prog - 0.12) / 0.72, 0.0), 1.0)
                    seg_f = hop_u * 2.0
                    idx_a = min(int(seg_f), 1)
                    local_u = seg_f - idx_a
                    pa, pb = stone_centers[idx_a], stone_centers[idx_a + 1]
                    tx = int(pa[0] + (pb[0] - pa[0]) * local_u)
                    ty = int(pa[1] + (pb[1] - pa[1]) * local_u - math.sin(local_u * math.pi) * 90 - 26)
                    cv2.circle(frame, (tx, ty), 20, COL_CORAL, -1, lineType=cv2.LINE_AA)
                    cv2.circle(frame, (tx, ty), 9, COL_WHITE, -1, lineType=cv2.LINE_AA)

            # ------------------------------------------------------------------
            # SCENE 5: SUNRISE GROWTH (RISING SUN + BLOOMING GEOMETRIC TREE + 7 ORBS)
            # ------------------------------------------------------------------
            else:
                # Drifting twilight clouds
                c_off = int(t * 24)
                _blit_rgba(frame, cloud_sp_1, (int(width * 0.10) + c_off) % (width + 200) - 180, int(height * 0.22), 0.75)
                _blit_rgba(frame, cloud_sp_2, (int(width * 0.65) - c_off) % (width + 200) - 180, int(height * 0.28), 0.7)

                cx = width // 2
                ground_y = int(height * (0.76 if not is_short else 0.72))
                sun_y = int(ground_y - 60 - _ease_out_cubic(prog) * (150 if not is_short else 130))
                _blit_rgba(frame, amber_glow_md, cx - amber_glow_md.shape[1] // 2, sun_y - amber_glow_md.shape[0] // 2, 1.0)
                cv2.circle(frame, (cx, sun_y), int(108 * scale_base), COL_AMBER, -1, lineType=cv2.LINE_AA)
                cv2.circle(frame, (cx, sun_y), int(84 * scale_base), (254, 240, 138), -1, lineType=cv2.LINE_AA)

                # Rolling geometric hills
                cv2.ellipse(frame, (int(width * 0.28), ground_y + 110), (int(width * 0.55), 180), 0, 180, 360, (34, 42, 98), -1)
                cv2.ellipse(frame, (int(width * 0.74), ground_y + 125), (int(width * 0.55), 190), 0, 180, 360, (24, 32, 78), -1)
                cv2.rectangle(frame, (0, ground_y + 50), (width, height), (20, 26, 66), -1)

                # Blooming stylized geometric tree growing smoothly from ground!
                grow = _ease_out_cubic(min(prog / 0.55, 1.0))
                trunk_h = int(170 * scale_base * grow)
                cv2.line(frame, (cx, ground_y + 40), (cx, ground_y + 40 - trunk_h), COL_PEACH, max(4, int(14 * scale_base)), lineType=cv2.LINE_AA)
                if grow > 0.35:
                    bloom = _ease_out_back(min((grow - 0.35) / 0.65, 1.0))
                    top_y = ground_y + 40 - trunk_h
                    for dx, dy, rad, col in [
                        (0, -48, 66, COL_TEAL), (-54, -12, 48, (32, 184, 168)),
                        (54, -12, 48, (32, 184, 168)), (-28, -68, 42, COL_CYAN), (30, -64, 40, COL_AMBER),
                    ]:
                        r = max(2, int(rad * scale_base * bloom))
                        cv2.circle(frame, (cx + int(dx * scale_base), top_y + int(dy * scale_base)), r, col, -1, lineType=cv2.LINE_AA)

                # 7 glowing milestone orbs arching overhead
                lit = min(7, 1 + int(prog * 7.5))
                arc_r = int((290 if not is_short else 250) * scale_base)
                for d_i in range(7):
                    th = math.radians(-155 + d_i * (130 / 6.0))
                    ox = int(cx + math.cos(th) * arc_r)
                    oy = int(ground_y - 120 + math.sin(th) * arc_r)
                    active = d_i < lit
                    cv2.circle(frame, (ox, oy), 16 if active else 9, COL_AMBER if active else (68, 78, 134), -1, lineType=cv2.LINE_AA)
                    if active:
                        cv2.circle(frame, (ox, oy), 7, COL_WHITE, -1, lineType=cv2.LINE_AA)

            # ------------------------------------------------------------------
            # OVERLAY: TOP PROGRESS LINE + BADGE + HEADLINE + WATERMARK
            # ------------------------------------------------------------------
            bar_h = 6 if not is_short else 8
            cv2.rectangle(frame, (0, 0), (width, bar_h), (28, 32, 78), -1)
            global_p = ((scene_idx - 1) + prog) / float(max(total_scenes, 1))
            cv2.rectangle(frame, (0, 0), (int(width * global_p), bar_h), COL_TEAL, -1)

            in_a = _ease_out_cubic(min(t / 0.45, 1.0))
            in_dy = int((1.0 - in_a) * 20)
            if is_short:
                _blit_rgba(frame, handle_sp, (width - handle_sp.shape[1]) // 2, 86, 0.85)
                _blit_rgba(frame, badge_sp, (width - badge_sp.shape[1]) // 2, 148 + in_dy, in_a)
                _blit_rgba(frame, head_sp, (width - head_sp.shape[1]) // 2, 224 + in_dy, in_a)
            else:
                _blit_rgba(frame, badge_sp, 64, 38 + in_dy, in_a)
                _blit_rgba(frame, head_sp, 64, 102 + in_dy, in_a)
                _blit_rgba(frame, handle_sp, width - 64 - handle_sp.shape[1], 44, 0.85)

            # Smooth fade in/out
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
            raise RuntimeError(f"FFmpeg Flat Vector 2D render failed (code {ret}): {stderr_out[-400:]}")
    finally:
        if proc.stdin and not proc.stdin.closed:
            proc.stdin.close()

    return out_mp4
