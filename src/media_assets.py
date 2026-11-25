from __future__ import annotations

import os
import random
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from src.config_loader import resolve_font_path


def _hex_to_rgb(hex_color: str, fallback: tuple[int, int, int] = (17, 19, 23)) -> tuple[int, int, int]:
    h = hex_color.strip().lstrip("#")
    if len(h) == 6:
        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except ValueError:
            return fallback
    return fallback


def _load_font(preferred: str | None, size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_path = resolve_font_path(preferred, bold=bold)
    if font_path:
        try:
            return ImageFont.truetype(font_path, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int, max_lines: int = 4) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
            if len(lines) >= max_lines - 1:
                break
    remaining_idx = sum(len(l.split()) for l in lines)
    if len(lines) < max_lines:
        tail_words = words[remaining_idx:]
        tail = " ".join(tail_words)
        while tail:
            bbox = draw.textbbox((0, 0), tail, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                break
            parts = tail.split()
            if len(parts) <= 1:
                tail = tail[:-4] + "..." if len(tail) > 4 else tail
                break
            tail = " ".join(parts[:-1]) + "..."
        if tail:
            lines.append(tail)
    return lines[:max_lines]


def _find_custom_asset(custom_dir: Path | None, stem: str) -> Path | None:
    if not custom_dir or not custom_dir.exists():
        return None
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        cand = custom_dir / f"{stem}{ext}"
        if cand.exists():
            return cand
    return None


def _cover_crop_resize(img: Image.Image, width: int, height: int) -> Image.Image:
    src_ratio = img.width / img.height
    dst_ratio = width / height
    if src_ratio > dst_ratio:
        new_w = int(img.height * dst_ratio)
        left = (img.width - new_w) // 2
        img = img.crop((left, 0, left + new_w, img.height))
    else:
        new_h = int(img.width / dst_ratio)
        top = (img.height - new_h) // 2
        img = img.crop((0, top, img.width, top + new_h))
    return img.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")


def _apply_editorial_scrim(
    img: Image.Image,
    bg_dark: tuple[int, int, int],
    mode: str = "top_bottom",
) -> Image.Image:
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    if mode == "left_fade":
        for x in range(w):
            t = x / max(w - 1, 1)
            alpha = int(215 * max(0.0, 1.0 - t * 1.18) + 22)
            odraw.line([(x, 0), (x, h)], fill=(*bg_dark, min(alpha, 238)))
    elif mode == "top_bottom":
        # Keeps central illustration crystal clear while guaranteeing high-contrast editorial typography at top/bottom
        top_zone = int(h * 0.22)
        bot_zone = int(h * 0.34)
        for y in range(top_zone):
            t = 1.0 - (y / max(top_zone, 1))
            odraw.line([(0, y), (w, y)], fill=(*bg_dark, int(180 * (t**1.3))))
        for y in range(h - bot_zone, h):
            t = (y - (h - bot_zone)) / max(bot_zone, 1)
            odraw.line([(0, y), (w, y)], fill=(*bg_dark, int(230 * (t**1.15))))
    elif mode == "vertical_story":
        # Upper headline zone + subtle bottom caption zone; middle artwork shines cleanly
        top_zone = int(h * 0.34)
        bot_zone = int(h * 0.26)
        for y in range(top_zone):
            t = 1.0 - (y / max(top_zone, 1))
            odraw.line([(0, y), (w, y)], fill=(*bg_dark, int(210 * (t**1.15))))
        for y in range(h - bot_zone, h):
            t = (y - (h - bot_zone)) / max(bot_zone, 1)
            odraw.line([(0, y), (w, y)], fill=(*bg_dark, int(215 * (t**1.1))))
    else:
        overlay = Image.new("RGBA", (w, h), (*bg_dark, 155))

    return Image.alpha_composite(img, overlay)


def _create_charcoal_sketch_canvas(width: int, height: int, branding: dict[str, Any], seed: int = 1) -> Image.Image:
    """Fallback matte dark charcoal notebook surface with subtle hand-drawn chalk accent strokes."""
    bg_dark = _hex_to_rgb(branding.get("bg_dark", "#111317"))
    bg_card = _hex_to_rgb(branding.get("bg_card", "#191C22"))
    primary = _hex_to_rgb(branding.get("primary_color", "#2DD4BF"))
    accent = _hex_to_rgb(branding.get("accent_color", "#F59E0B"))

    base = Image.new("RGBA", (width, height))
    grad = ImageDraw.Draw(base)
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(bg_dark[0] * (1 - t) + bg_card[0] * t)
        g = int(bg_dark[1] * (1 - t) + bg_card[1] * t)
        b = int(bg_dark[2] * (1 - t) + bg_card[2] * t)
        grad.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # Subtle matte dot-grid notebook texture
    dots = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dots)
    step = max(48, width // 28)
    for x in range(step // 2, width, step):
        for y in range(step // 2, height, step):
            dd.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(245, 242, 235, 20))
    base = Image.alpha_composite(base, dots)

    # Minimalist chalk rings accent in periphery
    art = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ad = ImageDraw.Draw(art)
    rng = random.Random(seed * 73)
    cx = int(width * (0.78 if seed % 2 == 0 else 0.24))
    cy = int(height * 0.44)
    for r_mult in (0.14, 0.22, 0.30):
        rad = int(min(width, height) * r_mult)
        col = (*primary, 42) if r_mult != 0.22 else (*accent, 34)
        ad.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), outline=col, width=2)
    for _ in range(14):
        px = rng.randint(int(width * 0.08), int(width * 0.92))
        py = rng.randint(int(height * 0.12), int(height * 0.85))
        ad.ellipse((px - 2, py - 2, px + 2, py + 2), fill=(*primary, 55))
    return Image.alpha_composite(base, art)


def _create_studio_backdrop(
    width: int,
    height: int,
    branding: dict[str, Any],
    accent_shift: int = 0,
    bg_image_path: Path | None = None,
    scrim_mode: str = "top_bottom",
    style: str = "minimalist_ink_sketch",
) -> Image.Image:
    bg_dark = _hex_to_rgb(branding.get("bg_dark", "#111317"))
    if bg_image_path and bg_image_path.exists():
        img = _cover_crop_resize(Image.open(bg_image_path).convert("RGB"), width, height)
        return _apply_editorial_scrim(img, bg_dark=bg_dark, mode=scrim_mode)

    if style == "minimalist_ink_sketch":
        return _create_charcoal_sketch_canvas(width, height, branding, seed=accent_shift + 1)

    bg_card = _hex_to_rgb(branding.get("bg_card", "#141D38"))
    primary = _hex_to_rgb(branding.get("primary_color", "#14B8A6"))
    secondary = _hex_to_rgb(branding.get("secondary_color", "#38BDF8"))
    accent = _hex_to_rgb(branding.get("accent_color", "#F59E0B"))

    base = Image.new("RGBA", (width, height))
    grad_draw = ImageDraw.Draw(base)
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(bg_dark[0] * (1 - t) + bg_card[0] * t)
        g = int(bg_dark[1] * (1 - t) + bg_card[1] * t)
        b = int(bg_dark[2] * (1 - t) + bg_card[2] * t)
        grad_draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    orb_colors = [primary, secondary, accent]
    c1 = orb_colors[accent_shift % len(orb_colors)]
    c2 = orb_colors[(accent_shift + 1) % len(orb_colors)]
    r1 = int(min(width, height) * 0.42)
    r2 = int(min(width, height) * 0.36)
    cx1 = int(width * (0.82 if accent_shift % 2 == 0 else 0.18))
    cy1 = int(height * 0.22)
    cx2 = int(width * (0.16 if accent_shift % 2 == 0 else 0.84))
    cy2 = int(height * 0.78)
    gdraw.ellipse((cx1 - r1, cy1 - r1, cx1 + r1, cy1 + r1), fill=(*c1, 84))
    gdraw.ellipse((cx2 - r2, cy2 - r2, cx2 + r2, cy2 + r2), fill=(*c2, 68))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=int(min(width, height) * 0.14)))
    return Image.alpha_composite(base, glow)


def _try_gemini_image(prompt: str, aspect_ratio: str, config: dict[str, Any], out_path: Path) -> Path | None:
    if not config.get("ai", {}).get("use_gemini_images", False):
        return None
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    visual_cfg = config.get("visual", {})
    prefix = str(visual_cfg.get("prompt_prefix", "")).strip()
    full_prompt = f"{prefix} Visual subject ({aspect_ratio} composition): {prompt}".strip() if prefix else prompt

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    primary_img_model = str(config.get("ai", {}).get("image_model", "gemini-3.1-flash-image")).strip()

    # 1. Try Gemini native conversational image models ("Nano Banana" / Flash Image)
    gemini_image_candidates = list(dict.fromkeys([
        m for m in [primary_img_model, "gemini-3.1-flash-image", "gemini-2.5-flash-image"]
        if m and "imagen" not in m.lower()
    ]))
    try:
        for m in client.models.list():
            mname = (getattr(m, "name", "") or "").replace("models/", "")
            if "gemini" in mname.lower() and "image" in mname.lower() and mname not in gemini_image_candidates:
                gemini_image_candidates.append(mname)
    except Exception:
        pass

    for model_name in gemini_image_candidates:
        try:
            cfg_kwargs: dict[str, Any] = {"response_modalities": ["IMAGE"]}
            if hasattr(types, "ImageConfig"):
                cfg_kwargs["image_config"] = types.ImageConfig(aspect_ratio=aspect_ratio)
            resp = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(**cfg_kwargs),
            )
            parts = getattr(resp, "parts", None) or []
            if not parts and getattr(resp, "candidates", None):
                parts = getattr(resp.candidates[0].content, "parts", None) or []
            for part in parts:
                inline = getattr(part, "inline_data", None)
                if inline and getattr(inline, "data", None):
                    img = Image.open(BytesIO(inline.data))
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    img.save(out_path, format="PNG")
                    print(f"[media] Generated AI illustration via {model_name} -> {out_path.name}", flush=True)
                    return out_path
        except Exception as exc:
            print(f"[media] Image model {model_name} failed ({type(exc).__name__}): {str(exc)[:140]}", flush=True)
            continue

    # 2. Fallback to dedicated Imagen models
    imagen_candidates = list(dict.fromkeys([
        m for m in [primary_img_model if "imagen" in primary_img_model.lower() else "", "imagen-4.0-generate-001", "imagen-3.0-generate-002"]
        if m
    ]))
    for model_name in imagen_candidates:
        try:
            result = client.models.generate_images(
                model=model_name,
                prompt=full_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=aspect_ratio,
                    output_mime_type="image/png",
                ),
            )
            if result.generated_images:
                img_bytes = result.generated_images[0].image.image_bytes
                img = Image.open(BytesIO(img_bytes))
                out_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(out_path, format="PNG")
                print(f"[media] Generated Imagen artwork via {model_name} -> {out_path.name}", flush=True)
                return out_path
        except Exception as exc:
            print(f"[media] Imagen model {model_name} failed ({type(exc).__name__}): {str(exc)[:140]}", flush=True)
            continue

    return None


def _draw_pill(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int, int],
    text_color: tuple[int, int, int, int],
    pad_x: int = 24,
    pad_y: int = 10,
) -> tuple[int, int, int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x0, y0 = xy
    x1 = x0 + tw + pad_x * 2
    y1 = y0 + th + pad_y * 2
    draw.rounded_rectangle((x0, y0, x1, y1), radius=(y1 - y0) // 2, fill=fill)
    draw.text((x0 + pad_x, y0 + pad_y - bbox[1]), text, font=font, fill=text_color)
    return (x0, y0, x1, y1)


def generate_youtube_thumbnail(
    blueprint: dict[str, Any],
    config: dict[str, Any],
    out_path: Path,
    custom_bg: Path | None = None,
) -> Path:
    branding = config.get("branding", {})
    style = config.get("visual", {}).get("style", "minimalist_ink_sketch")
    thumb = blueprint.get("youtube_long", {}).get("thumbnail", {})
    w, h = 1280, 720

    if not custom_bg:
        ai_raw = out_path.parent / "_ai_thumb_bg.png"
        thumb_prompt = (
            f"{thumb.get('visual_prompt', blueprint['meta']['topic'])}. "
            "Place the primary hand-drawn focal illustration cleanly on the RIGHT half of the 16:9 canvas, "
            "keeping the LEFT half clean matte dark charcoal negative space."
        )
        custom_bg = _try_gemini_image(thumb_prompt, "16:9", config, ai_raw)

    canvas = _create_studio_backdrop(
        w, h, branding, accent_shift=0, bg_image_path=custom_bg, scrim_mode="left_fade", style=style
    )
    draw = ImageDraw.Draw(canvas, "RGBA")

    primary = _hex_to_rgb(branding.get("primary_color", "#2DD4BF"))
    accent = _hex_to_rgb(branding.get("accent_color", "#F59E0B"))
    text_primary = _hex_to_rgb(branding.get("text_primary", "#F5F2EB"))
    text_muted = _hex_to_rgb(branding.get("text_muted", "#B8B5AD"))

    # Subtle editorial frame & chalk accent vertical line
    draw.rounded_rectangle((28, 28, w - 28, h - 28), radius=24, outline=(*primary, 130), width=3)
    draw.rounded_rectangle((74, 118, 86, h - 118), radius=6, fill=(*accent, 255))

    f_badge = _load_font(branding.get("font_bold"), 28, bold=True)
    f_head = _load_font(branding.get("font_bold"), 86 if custom_bg else 92, bold=True)
    f_sub = _load_font(branding.get("font_regular"), 36, bold=False)
    f_brand = _load_font(branding.get("font_bold"), 26, bold=True)

    text_max_w = int(w * 0.54) if custom_bg else (w - 220)

    badge_text = str(thumb.get("badge") or "HABITSCIENCE LAB").upper()
    _draw_pill(draw, (118, 106), badge_text, f_badge, fill=(*accent, 255), text_color=(17, 19, 23, 255), pad_x=24, pad_y=10)

    headline = str(thumb.get("headline") or blueprint["meta"]["topic"]).upper()
    head_lines = _wrap_text(draw, headline, f_head, max_width=text_max_w, max_lines=3)
    y_cursor = 204
    for line in head_lines:
        draw.text((122, y_cursor + 4), line, font=f_head, fill=(0, 0, 0, 210))
        draw.text((118, y_cursor), line, font=f_head, fill=(*text_primary, 255))
        y_cursor += 94

    # Hand-drawn style highlighter underline
    draw.rounded_rectangle((118, y_cursor + 4, 340, y_cursor + 12), radius=4, fill=(*primary, 255))
    y_cursor += 32

    sub = str(thumb.get("subheadline") or blueprint.get("youtube_long", {}).get("title", ""))
    sub_lines = _wrap_text(draw, sub, f_sub, max_width=text_max_w, max_lines=2)
    for line in sub_lines:
        draw.text((118, y_cursor), line, font=f_sub, fill=(*text_muted, 255))
        y_cursor += 48

    watermark = str(branding.get("watermark_text") or blueprint["meta"].get("channel_handle", "@habitsciencelab"))
    wm_bbox = draw.textbbox((0, 0), watermark, font=f_brand)
    wm_w = wm_bbox[2] - wm_bbox[0]
    _draw_pill(
        draw,
        (w - wm_w - 102, h - 102),
        watermark,
        f_brand,
        fill=(17, 19, 23, 215),
        text_color=(*text_primary, 255),
        pad_x=20,
        pad_y=9,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, format="PNG")
    return out_path


def generate_long_scene_images(
    blueprint: dict[str, Any],
    config: dict[str, Any],
    scenes_dir: Path,
    custom_assets_dir: Path | None = None,
) -> list[Path]:
    branding = config.get("branding", {})
    visual_cfg = config.get("visual", {})
    style = visual_cfg.get("style", "minimalist_ink_sketch")
    cinematic_full_bleed = bool(visual_cfg.get("cinematic_full_bleed", True))
    vid_cfg = config.get("video", {}).get("youtube_long", {})
    w = int(vid_cfg.get("width", 1920))
    h = int(vid_cfg.get("height", 1080))
    scenes = blueprint.get("youtube_long", {}).get("scenes", [])
    total = max(len(scenes), 1)

    primary = _hex_to_rgb(branding.get("primary_color", "#2DD4BF"))
    accent = _hex_to_rgb(branding.get("accent_color", "#F59E0B"))
    text_primary = _hex_to_rgb(branding.get("text_primary", "#F5F2EB"))
    text_muted = _hex_to_rgb(branding.get("text_muted", "#B8B5AD"))

    f_section = _load_font(branding.get("font_bold"), 28, bold=True)
    f_head = _load_font(branding.get("font_bold"), 64, bold=True)
    f_sub = _load_font(branding.get("font_regular"), 34, bold=False)
    f_meta = _load_font(branding.get("font_bold"), 26, bold=True)

    scenes_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for idx, scene in enumerate(scenes, start=1):
        bg_override = _find_custom_asset(custom_assets_dir, f"long_scene_{idx}")
        if not bg_override:
            ai_bg = scenes_dir / f"_ai_long_{idx:02d}.png"
            bg_override = _try_gemini_image(scene.get("visual_prompt", scene.get("visual_headline", "")), "16:9", config, ai_bg)

        # Full-bleed documentary layout: let bespoke editorial artwork fill the center cleanly!
        use_cinematic = cinematic_full_bleed and (bg_override is not None or style == "minimalist_ink_sketch")
        canvas = _create_studio_backdrop(
            w, h, branding, accent_shift=idx, bg_image_path=bg_override, scrim_mode="top_bottom", style=style
        )
        draw = ImageDraw.Draw(canvas, "RGBA")

        # Whisper-thin top progress line
        draw.rectangle((0, 0, w, 6), fill=(255, 255, 255, 25))
        draw.rectangle((0, 0, int(w * (idx / total)), 6), fill=(*primary, 255))

        # Minimal top chapter indicator & watermark
        section = f"{idx:02d}/{total:02d}  •  {str(scene.get('section', f'PART {idx}')).upper()}"
        _draw_pill(draw, (72, 46), section, f_section, fill=(17, 19, 23, 195), text_color=(*primary, 255), pad_x=22, pad_y=10)

        watermark = str(branding.get("watermark_text") or blueprint["meta"].get("channel_handle", "@habitsciencelab"))
        wm_box = draw.textbbox((0, 0), watermark, font=f_meta)
        draw.text((w - 72 - (wm_box[2] - wm_box[0]), 54), watermark, font=f_meta, fill=(*text_muted, 200))

        headline = str(scene.get("visual_headline") or blueprint["meta"]["topic"])
        callout = str(scene.get("on_screen_callout") or "").strip()

        if use_cinematic and bg_override is not None:
            # Clean editorial lower-third ONLY (artwork stays 100% unobstructed in center!)
            y_base = 735
            h_lines = _wrap_text(draw, headline, f_head, max_width=w - 220, max_lines=1)
            c_lines = _wrap_text(draw, callout, f_sub, max_width=w - 220, max_lines=1) if callout else []
            max_tw = 0
            for line in h_lines:
                b = draw.textbbox((0, 0), line, font=f_head)
                max_tw = max(max_tw, b[2] - b[0])
            for cl in c_lines:
                b = draw.textbbox((0, 0), cl, font=f_sub)
                max_tw = max(max_tw, b[2] - b[0])
            box_h = 136 if c_lines else 92
            draw.rounded_rectangle(
                (56, y_base - 18, min(140 + max_tw, w - 56), y_base - 18 + box_h),
                radius=18,
                fill=(17, 19, 23, 210),
            )
            draw.rounded_rectangle((74, y_base - 4, 84, y_base - 4 + (box_h - 28)), radius=5, fill=(*accent, 255))
            for line in h_lines:
                draw.text((108, y_base + 2), line, font=f_head, fill=(0, 0, 0, 210))
                draw.text((105, y_base), line, font=f_head, fill=(*text_primary, 255))
            for cl in c_lines:
                draw.text((106, y_base + 74), cl, font=f_sub, fill=(*text_muted, 250))
        else:
            # Clean minimalist editorial visual-note layout (no heavy PowerPoint box!)
            h_lines = _wrap_text(draw, headline, _load_font(branding.get("font_bold"), 76, bold=True), max_width=w - 200, max_lines=2)
            y = 178
            for line in h_lines:
                draw.text((96, y), line, font=_load_font(branding.get("font_bold"), 76, bold=True), fill=(*text_primary, 255))
                y += 88
            draw.rounded_rectangle((96, y + 10, 280, y + 18), radius=4, fill=(*accent, 255))
            y += 58

            f_bullet = _load_font(branding.get("font_regular"), 42, bold=False)
            for bullet in (scene.get("bullet_points") or [])[:3]:
                clean_b = str(bullet).lstrip("0123456789.-) ").strip()
                draw.ellipse((100, y + 16, 118, y + 34), fill=(*primary, 255))
                b_lines = _wrap_text(draw, clean_b, f_bullet, max_width=w - 260, max_lines=2)
                for bl in b_lines:
                    draw.text((146, y), bl, font=f_bullet, fill=(*text_primary, 238))
                    y += 56
                y += 22

            if callout:
                draw.text((96, 804), f"—  {callout}", font=f_sub, fill=(*accent, 255))

        out_file = scenes_dir / f"scene_{idx:02d}.png"
        canvas.convert("RGB").save(out_file, format="PNG")
        generated.append(out_file)

    return generated


def generate_short_scene_images(
    blueprint: dict[str, Any],
    config: dict[str, Any],
    scenes_dir: Path,
    custom_assets_dir: Path | None = None,
) -> list[Path]:
    branding = config.get("branding", {})
    visual_cfg = config.get("visual", {})
    style = visual_cfg.get("style", "minimalist_ink_sketch")
    vid_cfg = config.get("video", {}).get("shorts", {})
    w = int(vid_cfg.get("width", 1080))
    h = int(vid_cfg.get("height", 1920))
    scenes = blueprint.get("shorts_reels_tiktok", {}).get("scenes", [])
    total = max(len(scenes), 1)

    primary = _hex_to_rgb(branding.get("primary_color", "#2DD4BF"))
    accent = _hex_to_rgb(branding.get("accent_color", "#F59E0B"))
    text_primary = _hex_to_rgb(branding.get("text_primary", "#F5F2EB"))
    text_muted = _hex_to_rgb(branding.get("text_muted", "#B8B5AD"))

    f_badge = _load_font(branding.get("font_bold"), 34, bold=True)
    f_head = _load_font(branding.get("font_bold"), 78, bold=True)
    f_brand = _load_font(branding.get("font_bold"), 30, bold=True)

    scenes_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for idx, scene in enumerate(scenes, start=1):
        bg_override = _find_custom_asset(custom_assets_dir, f"short_scene_{idx}")
        if not bg_override:
            ai_bg = scenes_dir / f"_ai_short_{idx:02d}.png"
            bg_override = _try_gemini_image(scene.get("visual_prompt", scene.get("visual_headline", "")), "9:16", config, ai_bg)

        canvas = _create_studio_backdrop(
            w, h, branding, accent_shift=idx + 2, bg_image_path=bg_override, scrim_mode="vertical_story", style=style
        )
        draw = ImageDraw.Draw(canvas, "RGBA")

        # Clean minimalist story progress segments at top
        seg_gap = 12
        margin = 64
        seg_w = (w - margin * 2 - seg_gap * (total - 1)) // total
        for s_i in range(total):
            x0 = margin + s_i * (seg_w + seg_gap)
            color = (*primary, 255) if s_i < idx else (255, 255, 255, 45)
            draw.rounded_rectangle((x0, 112, x0 + seg_w, 122), radius=5, fill=color)

        handle = str(branding.get("watermark_text") or blueprint["meta"].get("channel_handle", "@habitsciencelab"))
        hb = draw.textbbox((0, 0), handle, font=f_brand)
        draw.text(((w - (hb[2] - hb[0])) // 2, 152), handle, font=f_brand, fill=(*text_muted, 215))

        # Crisp floating upper headline (NO heavy card blocking the vertical illustration!)
        badge = str(scene.get("badge") or f"0{idx}").upper()
        bb = draw.textbbox((0, 0), badge, font=f_badge)
        pill_w = (bb[2] - bb[0]) + 48
        _draw_pill(
            draw,
            ((w - pill_w) // 2, 232),
            badge,
            f_badge,
            fill=(*accent, 255),
            text_color=(17, 19, 23, 255),
            pad_x=24,
            pad_y=11,
        )

        headline = str(scene.get("visual_headline") or blueprint["meta"]["topic"])
        h_lines = _wrap_text(draw, headline, f_head, max_width=w - 140, max_lines=3)
        y = 330
        for line in h_lines:
            lb = draw.textbbox((0, 0), line, font=f_head)
            lx = (w - (lb[2] - lb[0])) // 2
            draw.text((lx + 4, y + 4), line, font=f_head, fill=(0, 0, 0, 215))
            draw.text((lx, y), line, font=f_head, fill=(*text_primary, 255))
            y += 92

        out_file = scenes_dir / f"short_scene_{idx:02d}.png"
        canvas.convert("RGB").save(out_file, format="PNG")
        generated.append(out_file)

    return generated


def generate_carousel_slides(
    blueprint: dict[str, Any],
    config: dict[str, Any],
    carousel_dir: Path,
    custom_assets_dir: Path | None = None,
) -> list[Path]:
    branding = config.get("branding", {})
    style = config.get("visual", {}).get("style", "minimalist_ink_sketch")
    w, h = 1080, 1350
    slides = blueprint.get("carousel_social", {}).get("slides", [])
    total = max(len(slides), 1)

    primary = _hex_to_rgb(branding.get("primary_color", "#2DD4BF"))
    accent = _hex_to_rgb(branding.get("accent_color", "#F59E0B"))
    text_primary = _hex_to_rgb(branding.get("text_primary", "#F5F2EB"))
    text_muted = _hex_to_rgb(branding.get("text_muted", "#B8B5AD"))

    f_badge = _load_font(branding.get("font_bold"), 28, bold=True)
    f_head = _load_font(branding.get("font_bold"), 74, bold=True)
    f_body = _load_font(branding.get("font_regular"), 42, bold=False)
    f_high = _load_font(branding.get("font_bold"), 34, bold=True)
    f_footer = _load_font(branding.get("font_bold"), 28, bold=True)

    carousel_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for idx, slide in enumerate(slides, start=1):
        bg_override = _find_custom_asset(custom_assets_dir, f"carousel_slide_{idx}")
        if not bg_override and idx == 1:
            ai_cov = carousel_dir / "_ai_carousel_cover.png"
            bg_override = _try_gemini_image(slide.get("visual_prompt", blueprint["meta"]["topic"]), "3:4", config, ai_cov)

        canvas = _create_studio_backdrop(
            w, h, branding, accent_shift=idx, bg_image_path=bg_override, scrim_mode="full", style=style
        )
        draw = ImageDraw.Draw(canvas, "RGBA")

        # Editorial hairline border
        draw.rounded_rectangle((48, 48, w - 48, h - 48), radius=28, outline=(245, 242, 235, 55), width=2)

        badge = str(slide.get("badge") or f"SLIDE {idx}/{total}").upper()
        _draw_pill(draw, (96, 104), badge, f_badge, fill=(*primary, 255), text_color=(17, 19, 23, 255), pad_x=22, pad_y=10)

        draw.rounded_rectangle((96, 194, 216, 204), radius=5, fill=(*accent, 255))

        headline = str(slide.get("headline") or blueprint["meta"]["topic"])
        h_lines = _wrap_text(draw, headline, f_head, max_width=w - 192, max_lines=4)
        y = 248
        for line in h_lines:
            draw.text((96, y), line, font=f_head, fill=(*text_primary, 255))
            y += 88

        body = str(slide.get("body") or "")
        b_lines = _wrap_text(draw, body, f_body, max_width=w - 192, max_lines=6)
        y += 32
        for line in b_lines:
            draw.text((96, y), line, font=f_body, fill=(*text_muted, 245))
            y += 58

        highlight = str(slide.get("highlight") or "").strip()
        if highlight:
            box_y0 = h - 328
            box_y1 = h - 188
            draw.rounded_rectangle(
                (96, box_y0, w - 96, box_y1),
                radius=20,
                fill=(25, 28, 34, 255),
                outline=(*accent, 255),
                width=3,
            )
            hl_lines = _wrap_text(draw, highlight, f_high, max_width=w - 252, max_lines=2)
            hy = box_y0 + 34
            for hl in hl_lines:
                draw.text((126, hy), hl, font=f_high, fill=(252, 211, 77, 255))
                hy += 44

        handle = str(branding.get("watermark_text") or blueprint["meta"].get("channel_handle", "@habitsciencelab"))
        draw.text((96, h - 126), handle, font=f_footer, fill=(*text_muted, 210))

        dot_r = 7
        dot_gap = 24
        start_x = w - 96 - (total * dot_gap)
        for d_i in range(total):
            cx = start_x + d_i * dot_gap
            cy = h - 110
            color = (*accent, 255) if (d_i + 1) == idx else (245, 242, 235, 70)
            draw.ellipse((cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r), fill=color)

        out_file = carousel_dir / f"slide_{idx:02d}.png"
        canvas.convert("RGB").save(out_file, format="PNG")
        generated.append(out_file)

    return generated
