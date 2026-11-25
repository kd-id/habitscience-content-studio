from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from src.config_loader import resolve_font_path


def _hex_to_rgb(hex_color: str, fallback: tuple[int, int, int] = (15, 23, 42)) -> tuple[int, int, int]:
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


def _create_studio_backdrop(
    width: int,
    height: int,
    branding: dict[str, Any],
    accent_shift: int = 0,
    bg_image_path: Path | None = None,
    left_fade_overlay: bool = False,
) -> Image.Image:
    bg_dark = _hex_to_rgb(branding.get("bg_dark", "#0B1020"))
    bg_card = _hex_to_rgb(branding.get("bg_card", "#141D38"))
    primary = _hex_to_rgb(branding.get("primary_color", "#6366F1"))
    secondary = _hex_to_rgb(branding.get("secondary_color", "#0EA5E9"))
    accent = _hex_to_rgb(branding.get("accent_color", "#F59E0B"))

    if bg_image_path and bg_image_path.exists():
        img = Image.open(bg_image_path).convert("RGB")
        # Cover-crop to exact target aspect ratio
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
        img = img.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")
        if left_fade_overlay:
            # Directional gradient: dark left for high-contrast typography, luminous vibrant right for hero art
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            odraw = ImageDraw.Draw(overlay)
            for x in range(width):
                t = x / max(width - 1, 1)
                alpha = int(205 * max(0.0, 1.0 - t * 1.15) + 32)
                odraw.line([(x, 0), (x, height)], fill=(*bg_dark, min(alpha, 235)))
            return Image.alpha_composite(img, overlay)
        # Soft cinematic dark scrim for scene/slide text readability
        overlay = Image.new("RGBA", (width, height), (*bg_dark, 155))
        return Image.alpha_composite(img, overlay)

    # Smooth vertical gradient base
    base = Image.new("RGBA", (width, height))
    grad_draw = ImageDraw.Draw(base)
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(bg_dark[0] * (1 - t) + bg_card[0] * t)
        g = int(bg_dark[1] * (1 - t) + bg_card[1] * t)
        b = int(bg_dark[2] * (1 - t) + bg_card[2] * t)
        grad_draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # Glowing ambient orbs
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
    gdraw.ellipse((cx1 - r1, cy1 - r1, cx1 + r1, cy1 + r1), fill=(*c1, 88))
    gdraw.ellipse((cx2 - r2, cy2 - r2, cx2 + r2, cy2 + r2), fill=(*c2, 72))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=int(min(width, height) * 0.14)))
    base = Image.alpha_composite(base, glow)

    # Subtle architectural grid lines
    grid = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    grid_draw = ImageDraw.Draw(grid)
    step = max(64, width // 20)
    for x in range(0, width, step):
        grid_draw.line([(x, 0), (x, height)], fill=(255, 255, 255, 11), width=1)
    for y in range(0, height, step):
        grid_draw.line([(0, y), (width, y)], fill=(255, 255, 255, 11), width=1)
    return Image.alpha_composite(base, grid)


def _try_gemini_image(prompt: str, aspect_ratio: str, config: dict[str, Any], out_path: Path) -> Path | None:
    if not config.get("ai", {}).get("use_gemini_images", False):
        return None
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        model = config.get("ai", {}).get("image_model", "imagen-3.0-generate-002")
        result = client.models.generate_images(
            model=model,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                output_mime_type="image/png",
            ),
        )
        if result.generated_images:
            img_bytes = result.generated_images[0].image.image_bytes
            img = Image.open(BytesIO(img_bytes))
            img.save(out_path, format="PNG")
            return out_path
    except Exception:
        return None
    return None


def _draw_pill(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int, int],
    text_color: tuple[int, int, int, int],
    pad_x: int = 24,
    pad_y: int = 12,
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
    thumb = blueprint.get("youtube_long", {}).get("thumbnail", {})
    w, h = 1280, 720

    if not custom_bg:
        ai_raw = out_path.parent / "_ai_thumb_bg.png"
        custom_bg = _try_gemini_image(thumb.get("visual_prompt", ""), "16:9", config, ai_raw)

    canvas = _create_studio_backdrop(w, h, branding, accent_shift=0, bg_image_path=custom_bg, left_fade_overlay=bool(custom_bg))
    draw = ImageDraw.Draw(canvas, "RGBA")

    primary = _hex_to_rgb(branding.get("primary_color", "#6366F1"))
    accent = _hex_to_rgb(branding.get("accent_color", "#F59E0B"))
    text_primary = _hex_to_rgb(branding.get("text_primary", "#F8FAFC"))
    text_muted = _hex_to_rgb(branding.get("text_muted", "#CBD5E1"))

    # Accent frame border & left indicator bar
    draw.rounded_rectangle((28, 28, w - 28, h - 28), radius=28, outline=(*primary, 160), width=4)
    draw.rounded_rectangle((72, 110, 88, h - 110), radius=8, fill=(*accent, 255))

    f_badge = _load_font(branding.get("font_bold"), 30, bold=True)
    f_head = _load_font(branding.get("font_bold"), 86 if custom_bg else 92, bold=True)
    f_sub = _load_font(branding.get("font_regular"), 38 if custom_bg else 40, bold=False)
    f_brand = _load_font(branding.get("font_bold"), 28, bold=True)

    text_max_w = int(w * 0.56) if custom_bg else (w - 220)

    badge_text = str(thumb.get("badge") or "STRATEGI AI").upper()
    _draw_pill(draw, (124, 98), badge_text, f_badge, fill=(*accent, 255), text_color=(11, 16, 32, 255), pad_x=26, pad_y=12)

    headline = str(thumb.get("headline") or blueprint["meta"]["topic"]).upper()
    head_lines = _wrap_text(draw, headline, f_head, max_width=text_max_w, max_lines=3)
    y_cursor = 205
    for line in head_lines:
        draw.text((128, y_cursor + 5), line, font=f_head, fill=(0, 0, 0, 200))
        draw.text((124, y_cursor), line, font=f_head, fill=(*text_primary, 255))
        y_cursor += 96 if custom_bg else 104

    sub = str(thumb.get("subheadline") or blueprint.get("youtube_long", {}).get("title", ""))
    sub_lines = _wrap_text(draw, sub, f_sub, max_width=text_max_w, max_lines=2)
    y_cursor += 14
    for line in sub_lines:
        draw.text((124, y_cursor), line, font=f_sub, fill=(*text_muted, 255))
        y_cursor += 52

    # Bottom right watermark pill
    watermark = str(branding.get("watermark_text") or blueprint["meta"].get("channel_handle", "@creator"))
    wm_bbox = draw.textbbox((0, 0), watermark, font=f_brand)
    wm_w = wm_bbox[2] - wm_bbox[0]
    _draw_pill(
        draw,
        (w - wm_w - 110, h - 108),
        watermark,
        f_brand,
        fill=(15, 23, 42, 205),
        text_color=(*text_primary, 255),
        pad_x=22,
        pad_y=10,
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
    vid_cfg = config.get("video", {}).get("youtube_long", {})
    w = int(vid_cfg.get("width", 1920))
    h = int(vid_cfg.get("height", 1080))
    scenes = blueprint.get("youtube_long", {}).get("scenes", [])
    total = max(len(scenes), 1)

    primary = _hex_to_rgb(branding.get("primary_color", "#6366F1"))
    secondary = _hex_to_rgb(branding.get("secondary_color", "#0EA5E9"))
    accent = _hex_to_rgb(branding.get("accent_color", "#F59E0B"))
    text_primary = _hex_to_rgb(branding.get("text_primary", "#F8FAFC"))
    text_muted = _hex_to_rgb(branding.get("text_muted", "#CBD5E1"))

    f_section = _load_font(branding.get("font_bold"), 34, bold=True)
    f_head = _load_font(branding.get("font_bold"), 78, bold=True)
    f_bullet = _load_font(branding.get("font_regular"), 42, bold=False)
    f_callout = _load_font(branding.get("font_bold"), 34, bold=True)
    f_meta = _load_font(branding.get("font_bold"), 28, bold=True)

    scenes_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for idx, scene in enumerate(scenes, start=1):
        bg_override = _find_custom_asset(custom_assets_dir, f"long_scene_{idx}")
        if not bg_override:
            ai_bg = scenes_dir / f"_ai_long_{idx:02d}.png"
            bg_override = _try_gemini_image(scene.get("visual_prompt", ""), "16:9", config, ai_bg)

        canvas = _create_studio_backdrop(w, h, branding, accent_shift=idx, bg_image_path=bg_override)
        draw = ImageDraw.Draw(canvas, "RGBA")

        # Top progress bar
        bar_margin = 96
        bar_w = w - bar_margin * 2
        draw.rounded_rectangle((bar_margin, 44, bar_margin + bar_w, 54), radius=5, fill=(255, 255, 255, 36))
        progress_w = int(bar_w * (idx / total))
        draw.rounded_rectangle((bar_margin, 44, bar_margin + progress_w, 54), radius=5, fill=(*accent, 255))

        # Section badge & scene counter
        section = f"{idx:02d}/{total:02d} • {str(scene.get('section', f'SCENE {idx}')).upper()}"
        _draw_pill(draw, (96, 86), section, f_section, fill=(*primary, 230), text_color=(255, 255, 255, 255), pad_x=28, pad_y=12)

        watermark = str(branding.get("watermark_text") or blueprint["meta"].get("channel_handle", "@creator"))
        wm_box = draw.textbbox((0, 0), watermark, font=f_meta)
        draw.text((w - 96 - (wm_box[2] - wm_box[0]), 98), watermark, font=f_meta, fill=(*text_muted, 210))

        # Main headline
        headline = str(scene.get("visual_headline") or blueprint["meta"]["topic"])
        h_lines = _wrap_text(draw, headline, f_head, max_width=w - 192, max_lines=2)
        y = 186
        for line in h_lines:
            draw.text((98, y + 4), line, font=f_head, fill=(0, 0, 0, 140))
            draw.text((96, y), line, font=f_head, fill=(*text_primary, 255))
            y += 92

        # Glassmorphism content card (kept above bottom subtitle safe area y < 860)
        card_top = max(y + 24, 370)
        card_bottom = 780
        draw.rounded_rectangle(
            (96, card_top, w - 96, card_bottom),
            radius=28,
            fill=(15, 23, 42, 188),
            outline=(255, 255, 255, 42),
            width=2,
        )

        bullets = scene.get("bullet_points") or []
        by = card_top + 44
        for b_idx, bullet in enumerate(bullets[:4], start=1):
            # Number dot
            dot_x, dot_y = 148, by + 4
            draw.ellipse((dot_x, dot_y, dot_x + 42, dot_y + 42), fill=(*secondary, 235))
            num_txt = str(b_idx)
            nb = draw.textbbox((0, 0), num_txt, font=f_meta)
            draw.text((dot_x + (42 - (nb[2] - nb[0])) // 2, dot_y + 4), num_txt, font=f_meta, fill=(11, 16, 32, 255))

            b_lines = _wrap_text(draw, str(bullet), f_bullet, max_width=w - 340, max_lines=2)
            for bl in b_lines:
                draw.text((216, by), bl, font=f_bullet, fill=(*text_primary, 245))
                by += 54
            by += 18
            if by > card_bottom - 65:
                break

        # On-screen callout pill right below card (still safely above bottom subtitle band)
        callout = str(scene.get("on_screen_callout") or "").strip()
        if callout:
            _draw_pill(
                draw,
                (96, 804),
                f"KEY TAKEAWAY: {callout}",
                f_callout,
                fill=(*accent, 235),
                text_color=(11, 16, 32, 255),
                pad_x=28,
                pad_y=12,
            )

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
    vid_cfg = config.get("video", {}).get("shorts", {})
    w = int(vid_cfg.get("width", 1080))
    h = int(vid_cfg.get("height", 1920))
    scenes = blueprint.get("shorts_reels_tiktok", {}).get("scenes", [])
    total = max(len(scenes), 1)

    primary = _hex_to_rgb(branding.get("primary_color", "#6366F1"))
    accent = _hex_to_rgb(branding.get("accent_color", "#F59E0B"))
    text_primary = _hex_to_rgb(branding.get("text_primary", "#F8FAFC"))
    text_muted = _hex_to_rgb(branding.get("text_muted", "#CBD5E1"))

    f_badge = _load_font(branding.get("font_bold"), 38, bold=True)
    f_head = _load_font(branding.get("font_bold"), 86, bold=True)
    f_sub = _load_font(branding.get("font_regular"), 42, bold=False)
    f_brand = _load_font(branding.get("font_bold"), 34, bold=True)

    scenes_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for idx, scene in enumerate(scenes, start=1):
        bg_override = _find_custom_asset(custom_assets_dir, f"short_scene_{idx}")
        if not bg_override:
            ai_bg = scenes_dir / f"_ai_short_{idx:02d}.png"
            bg_override = _try_gemini_image(scene.get("visual_prompt", ""), "9:16", config, ai_bg)

        canvas = _create_studio_backdrop(w, h, branding, accent_shift=idx + 2, bg_image_path=bg_override)
        draw = ImageDraw.Draw(canvas, "RGBA")

        # Top segmented story bar (respecting mobile notch safe area)
        seg_gap = 14
        margin = 72
        seg_w = (w - margin * 2 - seg_gap * (total - 1)) // total
        for s_i in range(total):
            x0 = margin + s_i * (seg_w + seg_gap)
            color = (*accent, 255) if s_i < idx else (255, 255, 255, 50)
            draw.rounded_rectangle((x0, 120, x0 + seg_w, 134), radius=7, fill=color)

        # Channel handle at top
        handle = str(branding.get("watermark_text") or blueprint["meta"].get("channel_handle", "@creator"))
        hb = draw.textbbox((0, 0), handle, font=f_brand)
        draw.text(((w - (hb[2] - hb[0])) // 2, 168), handle, font=f_brand, fill=(*text_muted, 225))

        # Center glass card positioned in upper-middle safe zone (leaving bottom 35% clean for subtitles + TikTok/Reels UI)
        card_x0, card_y0, card_x1, card_y1 = 72, 310, w - 72, 1140
        draw.rounded_rectangle(
            (card_x0, card_y0, card_x1, card_y1),
            radius=36,
            fill=(11, 16, 32, 195),
            outline=(*primary, 180),
            width=3,
        )

        # Badge centered
        badge = str(scene.get("badge") or f"0{idx}").upper()
        bb = draw.textbbox((0, 0), badge, font=f_badge)
        pill_w = (bb[2] - bb[0]) + 56
        _draw_pill(
            draw,
            ((w - pill_w) // 2, card_y0 + 58),
            badge,
            f_badge,
            fill=(*accent, 255),
            text_color=(11, 16, 32, 255),
            pad_x=28,
            pad_y=14,
        )

        # Bold centered headline
        headline = str(scene.get("visual_headline") or blueprint["meta"]["topic"])
        h_lines = _wrap_text(draw, headline, f_head, max_width=w - 220, max_lines=4)
        y = card_y0 + 185
        for line in h_lines:
            lb = draw.textbbox((0, 0), line, font=f_head)
            lx = (w - (lb[2] - lb[0])) // 2
            draw.text((lx + 4, y + 4), line, font=f_head, fill=(0, 0, 0, 160))
            draw.text((lx, y), line, font=f_head, fill=(*text_primary, 255))
            y += 104

        # Supporting short preview line inside card
        narration_preview = str(scene.get("narration") or "")
        if len(narration_preview) > 110:
            narration_preview = narration_preview[:107].rsplit(" ", 1)[0] + "..."
        s_lines = _wrap_text(draw, narration_preview, f_sub, max_width=w - 240, max_lines=3)
        y = max(y + 34, card_y1 - 240)
        for line in s_lines:
            lb = draw.textbbox((0, 0), line, font=f_sub)
            lx = (w - (lb[2] - lb[0])) // 2
            draw.text((lx, y), line, font=f_sub, fill=(*text_muted, 235))
            y += 56

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
    w, h = 1080, 1350  # 4:5 Instagram & LinkedIn optimal portrait ratio
    slides = blueprint.get("carousel_social", {}).get("slides", [])
    total = max(len(slides), 1)

    primary = _hex_to_rgb(branding.get("primary_color", "#6366F1"))
    accent = _hex_to_rgb(branding.get("accent_color", "#F59E0B"))
    text_primary = _hex_to_rgb(branding.get("text_primary", "#F8FAFC"))
    text_muted = _hex_to_rgb(branding.get("text_muted", "#CBD5E1"))

    f_badge = _load_font(branding.get("font_bold"), 30, bold=True)
    f_head = _load_font(branding.get("font_bold"), 76, bold=True)
    f_body = _load_font(branding.get("font_regular"), 42, bold=False)
    f_high = _load_font(branding.get("font_bold"), 34, bold=True)
    f_footer = _load_font(branding.get("font_bold"), 28, bold=True)

    carousel_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for idx, slide in enumerate(slides, start=1):
        bg_override = _find_custom_asset(custom_assets_dir, f"carousel_slide_{idx}")

        canvas = _create_studio_backdrop(w, h, branding, accent_shift=idx, bg_image_path=bg_override)
        draw = ImageDraw.Draw(canvas, "RGBA")

        # Frame card
        draw.rounded_rectangle(
            (56, 56, w - 56, h - 56),
            radius=36,
            fill=(12, 18, 36, 170),
            outline=(255, 255, 255, 42),
            width=2,
        )

        # Top badge
        badge = str(slide.get("badge") or f"SLIDE {idx}/{total}").upper()
        _draw_pill(draw, (108, 114), badge, f_badge, fill=(*primary, 235), text_color=(255, 255, 255, 255), pad_x=24, pad_y=12)

        # Accent divider line
        draw.rounded_rectangle((108, 210, 228, 222), radius=6, fill=(*accent, 255))

        # Headline
        headline = str(slide.get("headline") or blueprint["meta"]["topic"])
        h_lines = _wrap_text(draw, headline, f_head, max_width=w - 216, max_lines=4)
        y = 264
        for line in h_lines:
            draw.text((108, y), line, font=f_head, fill=(*text_primary, 255))
            y += 90

        # Body text
        body = str(slide.get("body") or "")
        b_lines = _wrap_text(draw, body, f_body, max_width=w - 216, max_lines=6)
        y += 32
        for line in b_lines:
            draw.text((108, y), line, font=f_body, fill=(*text_muted, 245))
            y += 58

        # Highlight callout box
        highlight = str(slide.get("highlight") or "").strip()
        if highlight:
            box_y0 = h - 340
            box_y1 = h - 196
            draw.rounded_rectangle(
                (108, box_y0, w - 108, box_y1),
                radius=24,
                fill=(24, 34, 64, 255),
                outline=(*accent, 255),
                width=3,
            )
            hl_lines = _wrap_text(draw, highlight, f_high, max_width=w - 276, max_lines=2)
            hy = box_y0 + 36
            for hl in hl_lines:
                draw.text((138, hy), hl, font=f_high, fill=(252, 211, 77, 255))
                hy += 46

        # Footer: handle on left, pagination dots on right
        handle = str(branding.get("watermark_text") or blueprint["meta"].get("channel_handle", "@creator"))
        draw.text((108, h - 134), handle, font=f_footer, fill=(*text_muted, 210))

        dot_r = 8
        dot_gap = 26
        start_x = w - 108 - (total * dot_gap)
        for d_i in range(total):
            cx = start_x + d_i * dot_gap
            cy = h - 118
            color = (*accent, 255) if (d_i + 1) == idx else (255, 255, 255, 70)
            draw.ellipse((cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r), fill=color)

        out_file = carousel_dir / f"slide_{idx:02d}.png"
        canvas.convert("RGB").save(out_file, format="PNG")
        generated.append(out_file)

    return generated
