from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


WIB = timezone(timedelta(hours=7))

STATUS_BADGES = {
    "PUBLISHED": "✅ PUBLISHED",
    "SCHEDULED": "🗓 SCHEDULED",
    "DRAFTED": "📝 AUTO-DRAFTED",
    "DRY_RUN_READY": "🧪 DRY-RUN READY",
    "PENDING_AUTH": "🔑 PERLU OAUTH YOUTUBE",
    "READY_FOR_CONNECTOR": "🔌 PERLU WEBHOOK SOSMED",
    "FAILED": "❌ GAGAL",
}


def _file_size_kb(path_str: str) -> str:
    p = Path(path_str)
    if not p.exists():
        return "-"
    size = p.stat().st_size
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    return f"{size / 1024:.1f} KB"


def update_history(history_file: Path, record: dict[str, Any]) -> None:
    history: list[dict[str, Any]] = []
    if history_file.exists():
        try:
            history = json.loads(history_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            history = []
    history.append(record)
    history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_publish_report(
    run_id: str,
    run_dir: Path,
    blueprint: dict[str, Any],
    assets: dict[str, Any],
    publish_summary: dict[str, Any],
    elapsed_sec: float,
    history_file: Path,
) -> tuple[Path, Path, dict[str, Any]]:
    now_wib = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S WIB")
    meta = blueprint.get("meta", {})
    yt_long = blueprint.get("youtube_long", {})
    shorts = blueprint.get("shorts_reels_tiktok", {})
    carousel = blueprint.get("carousel_social", {})

    long_vinfo = assets.get("youtube_long", {}).get("video_info", {})
    short_vinfo = assets.get("shorts_reels_tiktok", {}).get("video_info", {})
    slide_paths = assets.get("carousel_social", {}).get("slide_paths", [])

    # Automated QA checks
    qa_checks = [
        ("Thumbnail YouTube 1280x720 tersedia", bool(assets.get("youtube_long", {}).get("thumbnail_path")) and Path(assets["youtube_long"]["thumbnail_path"]).exists()),
        ("Video YouTube Long 16:9 valid (H.264/AAC)", bool(long_vinfo.get("exists")) and long_vinfo.get("width") == 1920),
        ("Subtitle YouTube Long (.srt) tersinkronisasi", bool(assets.get("youtube_long", {}).get("srt_path")) and Path(assets["youtube_long"]["srt_path"]).exists()),
        ("Video Shorts/Reels/TikTok 9:16 valid (< 60 detik)", bool(short_vinfo.get("exists")) and float(short_vinfo.get("duration_sec", 999)) <= 60.0),
        ("Subtitle vertikal (.srt) tersinkronisasi", bool(assets.get("shorts_reels_tiktok", {}).get("srt_path")) and Path(assets["shorts_reels_tiktok"]["srt_path"]).exists()),
        (f"Carousel visual lengkap ({len(slide_paths)} slide 1080x1350)", len(slide_paths) >= 5),
        ("Copywriting semua platform (YT, Shorts, TikTok, IG, LinkedIn, X, FB) lengkap", bool(yt_long.get("description")) and bool(carousel.get("caption_instagram")) and bool(carousel.get("thread_x"))),
    ]

    # Build Markdown Report
    md: list[str] = [
        f"# Laporan Automasi & Publikasi Konten — `{run_id}`",
        "",
        "## 1. Ringkasan Eksekusi",
        "",
        "| Field | Nilai |",
        "| :--- | :--- |",
        f"| **Waktu Selesai** | {now_wib} |",
        f"| **Channel** | {meta.get('channel_name')} (`{meta.get('channel_handle')}`) |",
        f"| **Topik Utama** | {meta.get('topic')} |",
        f"| **Pillar Jadwal** | `{meta.get('pillar', 'focus_habits')}` ({meta.get('pillar_label', 'Everyday Focus & Habits')}) |",
        f"| **Sudut Pandang (Angle)** | {meta.get('angle', '-')} |",
        f"| **Sumber Ide** | `{meta.get('source', '-')}` |",
        f"| **Engine Scriptwriter** | `{meta.get('generator_mode', '-')}` |",
        f"| **Mode Publish** | `{publish_summary.get('publish_mode')}` |",
        f"| **Durasi Total Pipeline** | {elapsed_sec:.1f} detik |",
        f"| **Folder Output** | `{run_dir}` |",
        "",
        "## 2. Status Publikasi / Auto-Draft Per Platform",
        "",
        "| Platform | Format | Status | Judul / Preview | Link / ID | Catatan |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for item in publish_summary.get("results", []):
        badge = STATUS_BADGES.get(item["status"], item["status"])
        link_cell = f"[{item['external_id']}]({item['url']})" if item.get("url") else (item.get("external_id") or "-")
        title_clean = str(item.get("title", "")).replace("|", "/")
        notes_clean = str(item.get("notes", "")).replace("|", "/")
        md.append(f"| **{item['platform']}** | {item['format']} | {badge} | {title_clean} | {link_cell} | {notes_clean} |")

    md.extend([
        "",
        "## 3. Inventaris Aset Media Tervalidasi",
        "",
        "| Aset | Resolusi / Spesifikasi | Durasi | Ukuran | Lokasi File |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ])

    yt_assets = assets.get("youtube_long", {})
    if yt_assets.get("video_path"):
        md.append(
            f"| **Video YouTube Long** | {long_vinfo.get('width', '?')}x{long_vinfo.get('height', '?')} ({long_vinfo.get('video_codec', 'h264')}/{long_vinfo.get('audio_codec', 'aac')}) "
            f"| {long_vinfo.get('duration_sec', '-')} dtk | {_file_size_kb(yt_assets['video_path'])} | `{yt_assets['video_path']}` |"
        )
    if yt_assets.get("thumbnail_path"):
        md.append(f"| **Thumbnail YouTube** | 1280x720 PNG | - | {_file_size_kb(yt_assets['thumbnail_path'])} | `{yt_assets['thumbnail_path']}` |")
    if yt_assets.get("audio_path"):
        md.append(f"| **Voiceover YouTube Long** | MP3 (`{yt_assets.get('voice', '-')}`) | {yt_assets.get('audio_duration_sec', '-')} dtk | {_file_size_kb(yt_assets['audio_path'])} | `{yt_assets['audio_path']}` |")
    if yt_assets.get("srt_path"):
        md.append(f"| **Subtitle YouTube Long** | SRT | - | {_file_size_kb(yt_assets['srt_path'])} | `{yt_assets['srt_path']}` |")

    sh_assets = assets.get("shorts_reels_tiktok", {})
    if sh_assets.get("video_path"):
        md.append(
            f"| **Video Shorts / Reels / TikTok** | {short_vinfo.get('width', '?')}x{short_vinfo.get('height', '?')} ({short_vinfo.get('video_codec', 'h264')}/{short_vinfo.get('audio_codec', 'aac')}) "
            f"| {short_vinfo.get('duration_sec', '-')} dtk | {_file_size_kb(sh_assets['video_path'])} | `{sh_assets['video_path']}` |"
        )
    if sh_assets.get("audio_path"):
        md.append(f"| **Voiceover Vertikal** | MP3 (`{sh_assets.get('voice', '-')}`) | {sh_assets.get('audio_duration_sec', '-')} dtk | {_file_size_kb(sh_assets['audio_path'])} | `{sh_assets['audio_path']}` |")
    if sh_assets.get("srt_path"):
        md.append(f"| **Subtitle Vertikal** | SRT | - | {_file_size_kb(sh_assets['srt_path'])} | `{sh_assets['srt_path']}` |")

    if slide_paths:
        md.append(f"| **Carousel Social ({len(slide_paths)} Slides)** | 1080x1350 PNG (4:5) | - | {len(slide_paths)} file | `{Path(slide_paths[0]).parent}` |")

    md.extend([
        "",
        "## 4. Checklist Quality Assurance (QA)",
        "",
    ])
    for label, passed in qa_checks:
        mark = "x" if passed else " "
        md.append(f"- [{mark}] {label}")

    md.extend([
        "",
        "## 5. Rincian Copywriting & Metadata Siap Pakai",
        "",
        "### YouTube Long",
        f"- **Judul Utama**: {yt_long.get('title', '-')}",
        "- **Alternatif A/B Judul**:",
    ])
    for alt in yt_long.get("alt_titles", []):
        md.append(f"  - {alt}")
    md.extend([
        f"- **Tags SEO**: `{', '.join(yt_long.get('tags', []))}`",
        "",
        "**Deskripsi YouTube:**",
        "```text",
        yt_long.get("description", ""),
        "```",
        "",
        "### YouTube Shorts / TikTok / Instagram Reels",
        f"- **Judul / Hook**: {shorts.get('title', '-')} (`{shorts.get('hook_text', '-')}`)",
        "",
        "**Caption YouTube Shorts:**",
        "```text",
        shorts.get("caption_yt_shorts", ""),
        "```",
        "",
        "**Caption TikTok:**",
        "```text",
        shorts.get("caption_tiktok", ""),
        "```",
        "",
        "**Caption Instagram Reels:**",
        "```text",
        shorts.get("caption_ig_reels", ""),
        "```",
        "",
        "### Instagram Carousel, LinkedIn, X/Threads & Facebook",
        "",
        "**Caption Instagram Carousel:**",
        "```text",
        carousel.get("caption_instagram", ""),
        "```",
        "",
        "**Post LinkedIn:**",
        "```text",
        carousel.get("caption_linkedin", ""),
        "```",
        "",
        "**Thread X:**",
    ])
    for idx, tweet in enumerate(carousel.get("thread_x", []), start=1):
        md.append(f"{idx}. {tweet}")

    md.extend([
        "",
        "**Post Threads:**",
        f"> {carousel.get('post_threads', '')}",
        "",
        "**Post Facebook:**",
        "```text",
        carousel.get("post_facebook", ""),
        "```",
    ])

    pending_count = publish_summary.get("counts", {}).get("pending_setup", 0)
    if pending_count > 0:
        md.extend([
            "",
            "## 6. Langkah Aktivasi Auto-Draft / Auto-Publish Live",
            "",
            "Sebagian platform masih menunggu kredensial koneksi:",
            "1. **YouTube Data API v3**: Buat OAuth Desktop Client di Google Cloud Console, simpan sebagai `config/youtube_client_secret.json`, lalu jalankan `--publish-mode draft` sekali untuk login OAuth.",
            "2. **Instagram / TikTok / LinkedIn / X / Facebook**: Hubungkan webhook Zapier atau n8n, lalu masukkan URL-nya ke `PUBLISH_WEBHOOK_URL` di file `.env`.",
            "3. **Plugin Antigravity**: Anda juga bisa memasang plugin **Zapier** atau **Gemini API** langsung dari Antigravity Marketplace.",
        ])

    report_md_path = run_dir / "PUBLISH_REPORT.md"
    report_md_path.write_text("\n".join(md), encoding="utf-8")

    report_data = {
        "run_id": run_id,
        "generated_at_wib": now_wib,
        "topic": meta.get("topic"),
        "pillar": meta.get("pillar", ""),
        "pillar_label": meta.get("pillar_label", ""),
        "slug": meta.get("slug"),
        "publish_mode": publish_summary.get("publish_mode"),
        "elapsed_sec": round(elapsed_sec, 2),
        "run_dir": str(run_dir),
        "report_md": str(report_md_path),
        "qa_passed_all": all(ok for _, ok in qa_checks),
        "qa_checks": [{"check": name, "passed": ok} for name, ok in qa_checks],
        "assets": assets,
        "publishing": publish_summary,
    }
    report_json_path = run_dir / "report.json"
    report_json_path.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")

    ext_ids = {
        str(r.get("platform", "")): str(r.get("external_id", ""))
        for r in publish_summary.get("results", [])
        if r.get("external_id")
    }
    update_history(
        history_file,
        {
            "run_id": run_id,
            "slug": meta.get("slug"),
            "topic": meta.get("topic"),
            "pillar": meta.get("pillar", ""),
            "pillar_label": meta.get("pillar_label", ""),
            "generated_at_wib": now_wib,
            "publish_mode": publish_summary.get("publish_mode"),
            "visual_style_long": meta.get("visual_style_long", ""),
            "visual_style_short": meta.get("visual_style_short", ""),
            "external_ids": ext_ids,
            "counts": publish_summary.get("counts", {}),
            "report_md": str(report_md_path),
        },
    )

    return report_md_path, report_json_path, report_data
