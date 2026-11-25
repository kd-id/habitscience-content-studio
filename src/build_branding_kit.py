"""Compose pixel-exact YouTube Channel Customization assets for HabitScience Lab."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.config_loader import resolve_font_path


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    fp = resolve_font_path("bahnschrift.ttf" if bold else "segoeui.ttf", bold=bold)
    return ImageFont.truetype(fp, size=size) if fp else ImageFont.load_default()


def build_kit(logo_src: Path, banner_bg_src: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Profile Picture / Logo (1024x1024 PNG)
    logo_img = Image.open(logo_src).convert("RGB")
    side = min(logo_img.width, logo_img.height)
    left = (logo_img.width - side) // 2
    top = (logo_img.height - side) // 2
    logo_sq = logo_img.crop((left, top, left + side, top + side)).resize((1024, 1024), Image.Resampling.LANCZOS)
    logo_sq.save(out_dir / "youtube_logo_1024x1024.png", format="PNG")

    # 2. Video Subscribe Watermark (150x150 transparent circular PNG)
    wm_size = 150
    wm_base = logo_sq.resize((wm_size, wm_size), Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", (wm_size, wm_size), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.ellipse((4, 4, wm_size - 4, wm_size - 4), fill=225)
    wm_out = Image.new("RGBA", (wm_size, wm_size), (0, 0, 0, 0))
    wm_out.paste(wm_base, (0, 0), mask)
    wdraw = ImageDraw.Draw(wm_out, "RGBA")
    wdraw.ellipse((4, 4, wm_size - 4, wm_size - 4), outline=(45, 212, 191, 220), width=3)
    wm_out.save(out_dir / "youtube_watermark_150x150.png", format="PNG")

    # 3. YouTube Channel Banner (2560x1440 PNG, typography locked inside 1546x423 safe zone)
    bw, bh = 2560, 1440
    bg = Image.open(banner_bg_src).convert("RGB")
    src_r = bg.width / bg.height
    dst_r = bw / bh
    if src_r > dst_r:
        nw = int(bg.height * dst_r)
        bg = bg.crop(((bg.width - nw) // 2, 0, (bg.width + nw) // 2, bg.height))
    else:
        nh = int(bg.width / dst_r)
        bg = bg.crop((0, (bg.height - nh) // 2, bg.width, (bg.height + nh) // 2))
    banner = bg.resize((bw, bh), Image.Resampling.LANCZOS).convert("RGBA")

    # Subtle radial darkening behind central safe area so white typography pops cleanly
    scrim = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(scrim)
    sdraw.rounded_rectangle((560, 520, 2000, 920), radius=48, fill=(17, 19, 23, 170))
    banner = Image.alpha_composite(banner, scrim)
    draw = ImageDraw.Draw(banner, "RGBA")

    # Safe zone center = (1280, 720), box = x:[507..2053], y:[508..931]
    f_eyebrow = _font(32, bold=True)
    f_title = _font(118, bold=True)
    f_sub = _font(44, bold=False)
    f_tag = _font(30, bold=True)

    eyebrow = "NEUROSCIENCE  •  FOCUS  •  HABITS"
    eb = draw.textbbox((0, 0), eyebrow, font=f_eyebrow)
    draw.text(((bw - (eb[2] - eb[0])) // 2, 548), eyebrow, font=f_eyebrow, fill=(45, 212, 191, 255))

    title = "HABITSAINS"
    tb = draw.textbbox((0, 0), title, font=f_title)
    tx = (bw - (tb[2] - tb[0])) // 2
    draw.text((tx + 4, 608), title, font=f_title, fill=(0, 0, 0, 195))
    draw.text((tx, 604), title, font=f_title, fill=(245, 242, 235, 255))

    # Subtle amber highlighter bar centered under title
    draw.rounded_rectangle((bw // 2 - 140, 742, bw // 2 + 140, 750), radius=4, fill=(245, 158, 11, 255))

    sub = "Rewire Your Focus. Backed by Neuroscience."
    sb = draw.textbbox((0, 0), sub, font=f_sub)
    draw.text(((bw - (sb[2] - sb[0])) // 2, 774), sub, font=f_sub, fill=(184, 181, 173, 255))

    tag = "@HabitSains   •   NEW PROTOCOLS EVERY WEEK"
    gb = draw.textbbox((0, 0), tag, font=f_tag)
    draw.text(((bw - (gb[2] - gb[0])) // 2, 850), tag, font=f_tag, fill=(245, 242, 235, 190))

    banner.convert("RGB").save(out_dir / "youtube_banner_2560x1440.png", format="PNG")
    print("YouTube Branding Kit built cleanly in:", out_dir)


if __name__ == "__main__":
    build_kit(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
