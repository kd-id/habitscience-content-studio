from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.config_loader import get_project_paths, load_config, slugify
from src.ideation import select_topic
from src.media_assets import (
    generate_carousel_slides,
    generate_long_scene_images,
    generate_short_scene_images,
    generate_youtube_thumbnail,
)
from src.publisher import publish_all_platforms, send_report_notification
from src.reporter import generate_publish_report
from src.scriptwriter import generate_content_blueprint
from src.video_builder import build_video_from_scenes
from src.voiceover import generate_voiceover_bundle


WIB = timezone(timedelta(hours=7))


def _write_social_captions_md(blueprint: dict[str, Any], out_file: Path) -> None:
    carousel = blueprint.get("carousel_social", {})
    shorts = blueprint.get("shorts_reels_tiktok", {})
    lines = [
        f"# Copywriting Semua Platform — {blueprint['meta']['topic']}",
        "",
        "## Instagram Carousel",
        carousel.get("caption_instagram", ""),
        "",
        "## LinkedIn",
        carousel.get("caption_linkedin", ""),
        "",
        "## X (Thread)",
        *[f"{i}. {t}" for i, t in enumerate(carousel.get("thread_x", []), start=1)],
        "",
        "## Threads",
        carousel.get("post_threads", ""),
        "",
        "## Facebook",
        carousel.get("post_facebook", ""),
        "",
        "## TikTok",
        shorts.get("caption_tiktok", ""),
        "",
        "## Instagram Reels",
        shorts.get("caption_ig_reels", ""),
        "",
        "## YouTube Shorts",
        shorts.get("caption_yt_shorts", ""),
    ]
    out_file.write_text("\n".join(lines), encoding="utf-8")


def run_pipeline(
    topic: str | None = None,
    angle: str | None = None,
    brief_path: Path | None = None,
    custom_assets_dir: Path | None = None,
    config_path: Path | None = None,
    publish_mode: str | None = None,
    visual_style: str | None = None,
    skip_video: bool = False,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    paths = get_project_paths()
    config = load_config(config_path=config_path, project_root=paths.root)
    if visual_style:
        config.setdefault("video", {})["engine_mode"] = visual_style
    effective_mode = publish_mode or config.get("publishing", {}).get("default_mode", "draft")

    print("[1/7] Riset & pemilihan topik...", flush=True)
    idea = select_topic(config=config, history_file=paths.history_file, manual_topic=topic, manual_angle=angle)

    print(f"[2/7] Menyusun Master Script & Repurpose multi-format untuk: {idea.topic}", flush=True)
    blueprint = generate_content_blueprint(idea=idea, config=config, brief_override_path=brief_path)

    stamp = datetime.now(WIB).strftime("%Y-%m-%d_%H%M%S")
    run_slug = slugify(blueprint["meta"]["topic"], max_length=36)
    run_id = f"{stamp}_{run_slug}"
    run_dir = paths.output_dir / run_id
    yt_long_dir = run_dir / "youtube_long"
    shorts_dir = run_dir / "shorts_reels_tiktok"
    carousel_dir = run_dir / "carousel_social"
    for d in (yt_long_dir, shorts_dir, carousel_dir):
        d.mkdir(parents=True, exist_ok=True)

    (run_dir / "brief_and_scripts.json").write_text(json.dumps(blueprint, ensure_ascii=False, indent=2), encoding="utf-8")
    (yt_long_dir / "metadata.json").write_text(json.dumps(blueprint.get("youtube_long", {}), ensure_ascii=False, indent=2), encoding="utf-8")
    (shorts_dir / "metadata.json").write_text(json.dumps(blueprint.get("shorts_reels_tiktok", {}), ensure_ascii=False, indent=2), encoding="utf-8")
    (carousel_dir / "metadata.json").write_text(json.dumps(blueprint.get("carousel_social", {}), ensure_ascii=False, indent=2), encoding="utf-8")
    _write_social_captions_md(blueprint, carousel_dir / "captions_all_platforms.md")

    print("[3/7] Membuat aset visual (Thumbnail 16:9, Scene 16:9 & 9:16, Carousel 5 slide 4:5)...", flush=True)
    thumb_bg = None
    if custom_assets_dir and custom_assets_dir.exists():
        for ext in (".png", ".jpg", ".jpeg", ".webp"):
            cand = custom_assets_dir / f"thumbnail_bg{ext}"
            if cand.exists():
                thumb_bg = cand
                break
    thumb_path = generate_youtube_thumbnail(blueprint, config, yt_long_dir / "thumbnail.png", custom_bg=thumb_bg)
    long_scene_imgs = generate_long_scene_images(blueprint, config, yt_long_dir / "scenes", custom_assets_dir=custom_assets_dir)
    short_scene_imgs = generate_short_scene_images(blueprint, config, shorts_dir / "scenes", custom_assets_dir=custom_assets_dir)
    carousel_slides = generate_carousel_slides(blueprint, config, carousel_dir, custom_assets_dir=custom_assets_dir)

    print("[4/7] Memproduksi neural voiceover (Edge TTS) & subtitle .SRT sinkron...", flush=True)
    long_audio = generate_voiceover_bundle(blueprint["youtube_long"]["scenes"], yt_long_dir, config, is_short=False)
    short_audio = generate_voiceover_bundle(blueprint["shorts_reels_tiktok"]["scenes"], shorts_dir, config, is_short=True)

    long_video_info: dict[str, Any] = {}
    short_video_info: dict[str, Any] = {}
    long_video_path = yt_long_dir / "video_16x9.mp4"
    short_video_path = shorts_dir / "video_9x16.mp4"

    if not skip_video:
        print("[5/7] Merender True Motion Video 30fps YouTube Long (16:9) & Shorts/Reels/TikTok (9:16)...", flush=True)
        long_video_info = build_video_from_scenes(
            long_scene_imgs,
            long_audio,
            long_video_path,
            config,
            is_short=False,
            scenes_meta=blueprint["youtube_long"]["scenes"],
        )
        short_video_info = build_video_from_scenes(
            short_scene_imgs,
            short_audio,
            short_video_path,
            config,
            is_short=True,
            scenes_meta=blueprint["shorts_reels_tiktok"]["scenes"],
        )
    else:
        print("[5/7] Melewati render video (--skip-video aktif).", flush=True)

    assets: dict[str, Any] = {
        "youtube_long": {
            "thumbnail_path": str(thumb_path),
            "scene_images": [str(p) for p in long_scene_imgs],
            "audio_path": long_audio.master_audio_path,
            "audio_duration_sec": round(long_audio.total_duration_sec, 2),
            "voice": long_audio.voice,
            "srt_path": long_audio.srt_path,
            "video_path": str(long_video_path) if long_video_path.exists() else "",
            "video_info": long_video_info,
        },
        "shorts_reels_tiktok": {
            "scene_images": [str(p) for p in short_scene_imgs],
            "audio_path": short_audio.master_audio_path,
            "audio_duration_sec": round(short_audio.total_duration_sec, 2),
            "voice": short_audio.voice,
            "srt_path": short_audio.srt_path,
            "video_path": str(short_video_path) if short_video_path.exists() else "",
            "video_info": short_video_info,
        },
        "carousel_social": {
            "slide_paths": [str(p) for p in carousel_slides],
            "captions_md": str(carousel_dir / "captions_all_platforms.md"),
        },
    }

    print(f"[6/7] Menjalankan publisher multi-platform (mode={effective_mode})...", flush=True)
    publish_summary = publish_all_platforms(
        blueprint=blueprint,
        assets=assets,
        run_dir=run_dir,
        config=config,
        project_root=paths.root,
        publish_mode=effective_mode,
    )

    elapsed = time.perf_counter() - t0
    print("[7/7] Membuat laporan detail PUBLISH_REPORT.md & report.json...", flush=True)
    report_md, report_json, report_data = generate_publish_report(
        run_id=run_id,
        run_dir=run_dir,
        blueprint=blueprint,
        assets=assets,
        publish_summary=publish_summary,
        elapsed_sec=elapsed,
        history_file=paths.history_file,
    )
    notified = send_report_notification(report_data, report_md)
    report_data["notification_sent"] = notified

    print("\n=== PIPELINE SELESAI ===", flush=True)
    print(json.dumps({
        "run_id": run_id,
        "topic": blueprint["meta"]["topic"],
        "publish_mode": effective_mode,
        "qa_passed_all": report_data["qa_passed_all"],
        "counts": publish_summary["counts"],
        "report_md": str(report_md),
        "run_dir": str(run_dir),
    }, ensure_ascii=False, indent=2), flush=True)

    return report_data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Content Automation Studio — End-to-End Pipeline")
    parser.add_argument("--topic", type=str, default=None, help="Topik konten manual (kosongkan untuk riset tren otomatis)")
    parser.add_argument("--angle", type=str, default=None, help="Sudut pandang / angle konten")
    parser.add_argument("--brief", type=str, default=None, help="Path ke file JSON blueprint buatan Antigravity/manual")
    parser.add_argument("--custom-assets", type=str, default=None, help="Folder gambar custom (thumbnail_bg.png, long_scene_1.png, dll.)")
    parser.add_argument("--config", type=str, default=None, help="Path ke file channel_config.yaml")
    parser.add_argument(
        "--publish-mode",
        type=str,
        choices=["dry-run", "draft", "publish"],
        default=None,
        help="Mode publikasi: dry-run (simulasi), draft (auto-draft aman), publish (langsung publik)",
    )
    parser.add_argument(
        "--visual-style",
        type=str,
        choices=["cozy_diorama", "minimal_line_story", "cinema_broll_html", "flat_vector_2d", "motion_hybrid", "ken_burns_images"],
        default=None,
        help="Override gaya visual video (default dari config/channel_config.yaml)",
    )
    parser.add_argument("--skip-video", action="store_true", help="Lewati tahap render MP4 FFmpeg")
    args = parser.parse_args(argv)

    run_pipeline(
        topic=args.topic,
        angle=args.angle,
        brief_path=Path(args.brief).resolve() if args.brief else None,
        custom_assets_dir=Path(args.custom_assets).resolve() if args.custom_assets else None,
        config_path=Path(args.config).resolve() if args.config else None,
        publish_mode=args.publish_mode,
        visual_style=args.visual_style,
        skip_video=args.skip_video,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
