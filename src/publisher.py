from __future__ import annotations

import base64
import html
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from src.scheduler_state import (
    allocate_youtube_schedule_slots,
    compute_facebook_prime_schedule_ts,
    save_schedule_state,
)
from src.social_publishers import (
    publish_facebook_reel_direct,
    publish_instagram_carousel_direct,
    publish_instagram_reels_direct,
    publish_linkedin_direct,
    publish_tiktok_direct,
    publish_x_and_threads_direct,
)


YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def _decode_json_env(raw_val: str) -> dict[str, Any] | None:
    text = raw_val.strip()
    if not text:
        return None
    if text.startswith("{"):
        return json.loads(text)
    # Also allow Base64-encoded JSON (common in CI/CD secrets)
    decoded = base64.b64decode(text).decode("utf-8")
    return json.loads(decoded)


def _get_youtube_service(project_root: Path):
    secrets_rel = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "config/youtube_client_secret.json")
    token_rel = os.getenv("YOUTUBE_TOKEN_FILE", "config/youtube_token.json")
    secrets_path = (project_root / secrets_rel) if not Path(secrets_rel).is_absolute() else Path(secrets_rel)
    token_path = (project_root / token_rel) if not Path(token_rel).is_absolute() else Path(token_rel)

    env_token_raw = os.getenv("YOUTUBE_TOKEN_JSON", "").strip()
    env_secret_raw = os.getenv("YOUTUBE_CLIENT_SECRET_JSON", "").strip()

    if not env_token_raw and not secrets_path.exists() and not token_path.exists():
        return None, (
            f"Kredensial OAuth YouTube belum ditemukan di {secrets_path} "
            "atau env YOUTUBE_TOKEN_JSON (untuk mode cloud)."
        )

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if env_token_raw:
        token_info = _decode_json_env(env_token_raw)
        if token_info:
            # Pass scopes=None so existing youtube.upload-only tokens keep working seamlessly until re-auth
            creds = Credentials.from_authorized_user_info(token_info)
    elif token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path))

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            if not env_token_raw:
                token_path.parent.mkdir(parents=True, exist_ok=True)
                token_path.write_text(creds.to_json(), encoding="utf-8")
        else:
            is_headless = bool(os.getenv("CI") or os.getenv("GITHUB_ACTIONS") or os.getenv("HEADLESS_CLOUD"))
            if is_headless:
                return None, (
                    "Mode cloud/headless tidak dapat membuka browser login OAuth. "
                    "Jalankan `python -m src.auth_youtube` sekali di PC lokal, lalu simpan hasilnya ke secret YOUTUBE_TOKEN_JSON."
                )
            if env_secret_raw and not secrets_path.exists():
                secrets_path.parent.mkdir(parents=True, exist_ok=True)
                secrets_path.write_text(json.dumps(_decode_json_env(env_secret_raw)), encoding="utf-8")
            if not secrets_path.exists():
                return None, f"File client secret tidak ditemukan: {secrets_path}"
            flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), YOUTUBE_SCOPES)
            creds = flow.run_local_server(port=0)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json(), encoding="utf-8")

    service = build("youtube", "v3", credentials=creds)
    return service, ""


def _upload_youtube_video(
    service: Any,
    video_path: Path,
    title: str,
    description: str,
    tags: list[str],
    category_id: str,
    privacy_status: str,
    made_for_kids: bool,
    thumbnail_path: Path | None = None,
    publish_at: str | None = None,
) -> dict[str, Any]:
    from googleapiclient.http import MediaFileUpload

    status_obj: dict[str, Any] = {
        "privacyStatus": "private" if publish_at else privacy_status,
        "selfDeclaredMadeForKids": made_for_kids,
    }
    if publish_at:
        status_obj["publishAt"] = publish_at

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:25],
            "categoryId": str(category_id),
        },
        "status": status_obj,
    }
    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    request = service.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()

    video_id = response["id"]
    thumb_uploaded = False
    thumb_note = ""
    if thumbnail_path and thumbnail_path.exists():
        try:
            service.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/png"),
            ).execute()
            thumb_uploaded = True
        except Exception as exc:
            thumb_uploaded = False
            thumb_note = f" (thumbnail dilewati — pastikan verifikasi nomor HP di YouTube Studio: {type(exc).__name__})"

    return {
        "video_id": video_id,
        "studio_url": f"https://studio.youtube.com/video/{video_id}/edit",
        "watch_url": f"https://youtu.be/{video_id}",
        "privacy_status": privacy_status,
        "thumbnail_uploaded": thumb_uploaded,
        "thumb_note": thumb_note,
    }


def _dispatch_social_webhook(payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    url = os.getenv("PUBLISH_WEBHOOK_URL", "").strip()
    if not url:
        return False, "PUBLISH_WEBHOOK_URL (Zapier/n8n/Make) belum diatur di .env", {}

    headers = {"Content-Type": "application/json"}
    secret = os.getenv("PUBLISH_WEBHOOK_SECRET", "").strip()
    if secret:
        headers["Authorization"] = f"Bearer {secret}"

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=25)
        ok = 200 <= resp.status_code < 300
        try:
            resp_json = resp.json()
        except ValueError:
            resp_json = {"raw_text": resp.text[:400]}
        msg = f"HTTP {resp.status_code}" if ok else f"Webhook error HTTP {resp.status_code}: {resp.text[:200]}"
        return ok, msg, resp_json
    except Exception as exc:
        return False, f"Gagal mengirim webhook: {exc}", {}


def publish_all_platforms(
    blueprint: dict[str, Any],
    assets: dict[str, Any],
    run_dir: Path,
    config: dict[str, Any],
    project_root: Path,
    publish_mode: str = "draft",
) -> dict[str, Any]:
    """
    Execute multi-platform publishing according to publish_mode:
      - 'dry-run': validates assets & builds full payload snapshots without calling external APIs.
      - 'draft': uploads YouTube as private draft & keeps social media in draft/container mode.
      - 'scheduled': YouTube Long & Shorts upload immediately and auto-queue onto distinct consecutive
        dates at US Prime Time via `publishAt` (`output/schedule_state.json`); Facebook Reels schedules
        natively at US Prime Time; Instagram Reels/Carousel & Threads publish live at the US Prime Time run.
      - 'publish': uploads YouTube & all connected platforms immediately as public.
    """
    mode = publish_mode.lower().strip()
    if mode not in ("dry-run", "draft", "scheduled", "publish"):
        mode = "draft"

    platforms_cfg = config.get("platforms", {})
    yt_long_meta = blueprint.get("youtube_long", {})
    shorts_meta = blueprint.get("shorts_reels_tiktok", {})
    carousel_meta = blueprint.get("carousel_social", {})

    results: list[dict[str, Any]] = []
    youtube_service = None
    youtube_auth_err = ""

    # Prepare distinct-date YouTube US Prime Time schedule slots when mode == 'scheduled'
    schedule_state_file = project_root / "output" / "schedule_state.json"
    yt_long_publish_at: str | None = None
    yt_shorts_publish_at: str | None = None
    pending_sched_state: dict[str, Any] | None = None
    yt_any_scheduled = False
    fb_sched_ts: int | None = None

    if mode == "scheduled":
        yt_long_publish_at, yt_shorts_publish_at, pending_sched_state = allocate_youtube_schedule_slots(
            schedule_state_file, config=config
        )
        prime_hrs = tuple(config.get("publishing", {}).get("schedule", {}).get("us_prime_hours_utc", [14, 17, 21]))
        fb_sched_ts = compute_facebook_prime_schedule_ts(prime_hours_utc=prime_hrs)

    if mode in ("draft", "scheduled", "publish") and (
        platforms_cfg.get("youtube_long", {}).get("enabled", True)
        or platforms_cfg.get("youtube_shorts", {}).get("enabled", True)
    ):
        try:
            youtube_service, youtube_auth_err = _get_youtube_service(project_root)
        except Exception as exc:
            youtube_service, youtube_auth_err = None, str(exc)

    # 1. YouTube Long (16:9)
    if platforms_cfg.get("youtube_long", {}).get("enabled", True):
        yt_cfg = platforms_cfg["youtube_long"]
        video_path = Path(assets["youtube_long"]["video_path"]) if assets.get("youtube_long", {}).get("video_path") else None
        thumb_path = Path(assets["youtube_long"]["thumbnail_path"]) if assets.get("youtube_long", {}).get("thumbnail_path") else None
        privacy = yt_cfg.get("publish_privacy", "public") if mode == "publish" else yt_cfg.get("draft_privacy", "private")

        if mode == "dry-run":
            results.append({
                "platform": "YouTube Long (16:9)",
                "format": "Video 1920x1080 + Thumbnail",
                "mode": mode,
                "status": "DRY_RUN_READY",
                "title": yt_long_meta.get("title", ""),
                "target_privacy": privacy,
                "external_id": "",
                "url": "",
                "notes": "Simulasi sukses. File video, subtitle, dan thumbnail siap diupload sebagai draft/scheduled/publish.",
            })
        elif youtube_service and video_path and video_path.exists():
            try:
                up = _upload_youtube_video(
                    service=youtube_service,
                    video_path=video_path,
                    title=yt_long_meta.get("title", blueprint["meta"]["topic"]),
                    description=yt_long_meta.get("description", ""),
                    tags=yt_long_meta.get("tags", []),
                    category_id=str(yt_cfg.get("category_id", "28")),
                    privacy_status=privacy,
                    made_for_kids=bool(yt_cfg.get("made_for_kids", False)),
                    thumbnail_path=thumb_path,
                    publish_at=yt_long_publish_at,
                )
                if mode == "scheduled" and yt_long_publish_at:
                    yt_any_scheduled = True
                res_st = "SCHEDULED" if (mode == "scheduled" and yt_long_publish_at) else ("PUBLISHED" if mode == "publish" else "DRAFTED")
                sched_txt = f", publishAt={yt_long_publish_at}" if yt_long_publish_at else ""
                results.append({
                    "platform": "YouTube Long (16:9)",
                    "format": "Video 1920x1080 + Thumbnail",
                    "mode": mode,
                    "status": res_st,
                    "title": yt_long_meta.get("title", ""),
                    "target_privacy": "scheduled" if yt_long_publish_at else privacy,
                    "external_id": up["video_id"],
                    "url": up["watch_url"] if mode == "publish" else up["studio_url"],
                    "notes": f"Upload sukses (privacy={privacy}{sched_txt}, thumbnail={up['thumbnail_uploaded']}){up.get('thumb_note', '')}.",
                })
            except Exception as exc:
                results.append({
                    "platform": "YouTube Long (16:9)",
                    "format": "Video 1920x1080 + Thumbnail",
                    "mode": mode,
                    "status": "FAILED",
                    "title": yt_long_meta.get("title", ""),
                    "target_privacy": privacy,
                    "external_id": "",
                    "url": "",
                    "notes": f"Upload gagal: {exc}",
                })
        else:
            results.append({
                "platform": "YouTube Long (16:9)",
                "format": "Video 1920x1080 + Thumbnail",
                "mode": mode,
                "status": "PENDING_AUTH",
                "title": yt_long_meta.get("title", ""),
                "target_privacy": privacy,
                "external_id": "",
                "url": "",
                "notes": youtube_auth_err or "Video file belum tersedia atau OAuth YouTube belum dihubungkan.",
            })

    # 2. YouTube Shorts (9:16)
    if platforms_cfg.get("youtube_shorts", {}).get("enabled", True):
        sh_cfg = platforms_cfg["youtube_shorts"]
        short_video = Path(assets["shorts_reels_tiktok"]["video_path"]) if assets.get("shorts_reels_tiktok", {}).get("video_path") else None
        privacy = sh_cfg.get("publish_privacy", "public") if mode == "publish" else sh_cfg.get("draft_privacy", "private")
        short_title = shorts_meta.get("title", blueprint["meta"]["topic"])
        if "#Shorts" not in short_title:
            short_title = f"{short_title[:88]} #Shorts"

        if mode == "dry-run":
            results.append({
                "platform": "YouTube Shorts (9:16)",
                "format": "Video 1080x1920",
                "mode": mode,
                "status": "DRY_RUN_READY",
                "title": short_title,
                "target_privacy": privacy,
                "external_id": "",
                "url": "",
                "notes": "Simulasi sukses. Video vertikal 9:16 + subtitle sinkron siap diupload.",
            })
        elif youtube_service and short_video and short_video.exists():
            try:
                up = _upload_youtube_video(
                    service=youtube_service,
                    video_path=short_video,
                    title=short_title,
                    description=shorts_meta.get("caption_yt_shorts", ""),
                    tags=[h.lstrip("#") for h in shorts_meta.get("hashtags", [])],
                    category_id=str(sh_cfg.get("category_id", "28")),
                    privacy_status=privacy,
                    made_for_kids=bool(sh_cfg.get("made_for_kids", False)),
                    publish_at=yt_shorts_publish_at,
                )
                if mode == "scheduled" and yt_shorts_publish_at:
                    yt_any_scheduled = True
                res_st = "SCHEDULED" if (mode == "scheduled" and yt_shorts_publish_at) else ("PUBLISHED" if mode == "publish" else "DRAFTED")
                sched_txt = f", publishAt={yt_shorts_publish_at}" if yt_shorts_publish_at else ""
                results.append({
                    "platform": "YouTube Shorts (9:16)",
                    "format": "Video 1080x1920",
                    "mode": mode,
                    "status": res_st,
                    "title": short_title,
                    "target_privacy": "scheduled" if yt_shorts_publish_at else privacy,
                    "external_id": up["video_id"],
                    "url": up["watch_url"] if mode == "publish" else up["studio_url"],
                    "notes": f"Upload Shorts sukses (privacy={privacy}{sched_txt}).",
                })
            except Exception as exc:
                results.append({
                    "platform": "YouTube Shorts (9:16)",
                    "format": "Video 1080x1920",
                    "mode": mode,
                    "status": "FAILED",
                    "title": short_title,
                    "target_privacy": privacy,
                    "external_id": "",
                    "url": "",
                    "notes": f"Upload Shorts gagal: {exc}",
                })
        else:
            results.append({
                "platform": "YouTube Shorts (9:16)",
                "format": "Video 1080x1920",
                "mode": mode,
                "status": "PENDING_AUTH",
                "title": short_title,
                "target_privacy": privacy,
                "external_id": "",
                "url": "",
                "notes": youtube_auth_err or "OAuth YouTube belum dihubungkan.",
            })

    # Persist advanced YouTube schedule date ONLY when at least one YouTube upload succeeded!
    if yt_any_scheduled and pending_sched_state is not None:
        save_schedule_state(schedule_state_file, pending_sched_state)

    # 3. Direct Free Official APIs (Instagram Reels/Carousel, TikTok, Facebook Reels, LinkedIn, X/Threads)
    #    with automatic fallback to PUBLISH_WEBHOOK_URL for any platform without direct credentials.
    short_vid_str = assets.get("shorts_reels_tiktok", {}).get("video_path", "")
    short_vid_path = Path(short_vid_str) if short_vid_str else None
    slide_strs = assets.get("carousel_social", {}).get("slide_paths", [])
    slide_paths = [Path(s) for s in slide_strs]

    social_targets = [
        ("instagram_reels", "Instagram Reels", "Video 1080x1920", shorts_meta.get("caption_ig_reels", ""), short_vid_str),
        ("tiktok", "TikTok", "Video 1080x1920", shorts_meta.get("caption_tiktok", ""), short_vid_str),
        ("instagram_carousel", "Instagram Carousel", "5 Slides 1080x1350", carousel_meta.get("caption_instagram", ""), slide_strs),
        ("linkedin", "LinkedIn", "Carousel / Post", carousel_meta.get("caption_linkedin", ""), slide_strs),
        ("x_threads", "X & Threads", "Thread 5 Posts + Threads", "\n\n".join(carousel_meta.get("thread_x", [])), slide_strs[:1]),
        ("facebook", "Facebook Page Reels", "Reel 1080x1920", carousel_meta.get("post_facebook", "") or shorts_meta.get("caption_ig_reels", ""), short_vid_str),
    ]

    webhook_payload = {
        "event": "content_automation_publish",
        "publish_mode": mode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "topic": blueprint["meta"]["topic"],
        "channel": blueprint["meta"].get("channel_name"),
        "targets": [],
    }

    active_social: list[tuple[str, str, str, str, Any]] = []
    for key, label, fmt, caption, media_ref in social_targets:
        if platforms_cfg.get(key, {}).get("enabled", True):
            active_social.append((key, label, fmt, caption, media_ref))
            webhook_payload["targets"].append({
                "platform_key": key,
                "platform_name": label,
                "format": fmt,
                "status": "draft" if mode != "publish" else "publish",
                "caption": caption,
                "hashtags": carousel_meta.get("hashtags", []),
                "media": media_ref,
            })

    payload_file = run_dir / "social_publish_payload.json"
    if config.get("publishing", {}).get("save_payload_snapshots", True):
        payload_file.write_text(json.dumps(webhook_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Attempt Direct Free API first for each enabled platform (when mode in draft/publish)
    direct_results: dict[str, dict[str, Any]] = {}
    fallback_targets: list[tuple[str, str, str, str, Any]] = []

    for item in active_social:
        key, label, fmt, caption, _ = item
        if mode == "dry-run":
            fallback_targets.append(item)
            continue

        adapter = str(platforms_cfg.get(key, {}).get("adapter", "direct")).lower().strip()
        if adapter == "webhook":
            fallback_targets.append(item)
            continue

        if key == "instagram_reels":
            d_res = publish_instagram_reels_direct(short_vid_path, caption, mode)
        elif key == "tiktok":
            d_res = publish_tiktok_direct(short_vid_path, caption, mode)
        elif key == "instagram_carousel":
            d_res = publish_instagram_carousel_direct(slide_paths, caption, mode)
        elif key == "linkedin":
            d_res = publish_linkedin_direct(slide_paths, caption, mode)
        elif key == "x_threads":
            d_res = publish_x_and_threads_direct(carousel_meta.get("thread_x", []), carousel_meta.get("post_threads", ""), mode)
        elif key == "facebook":
            d_res = publish_facebook_reel_direct(short_vid_path, caption, mode, scheduled_publish_ts=fb_sched_ts)
        else:
            d_res = {"handled": False}

        if d_res.get("handled"):
            direct_results[key] = d_res
        else:
            direct_results[key] = d_res
            fallback_targets.append(item)

    # Dispatch optional webhook ONLY for platforms not already handled by Direct API
    webhook_ok = False
    webhook_msg = ""
    webhook_resp: dict[str, Any] = {}
    if mode in ("draft", "scheduled", "publish") and fallback_targets and os.getenv("PUBLISH_WEBHOOK_URL", "").strip():
        fb_keys = {k for k, *_ in fallback_targets}
        fb_payload = {**webhook_payload, "targets": [t for t in webhook_payload["targets"] if t["platform_key"] in fb_keys]}
        webhook_ok, webhook_msg, webhook_resp = _dispatch_social_webhook(fb_payload)

    for key, label, fmt, caption, _ in active_social:
        preview = (caption.splitlines()[0] if caption else blueprint["meta"]["topic"])[:75]
        if mode == "dry-run":
            results.append({
                "platform": label,
                "format": fmt,
                "mode": mode,
                "status": "DRY_RUN_READY",
                "title": preview,
                "target_privacy": "draft",
                "external_id": "",
                "url": "",
                "notes": f"Simulasi sukses. Direct API & payload siap di {payload_file.name}.",
            })
        elif key in direct_results and direct_results[key].get("handled"):
            dr = direct_results[key]
            results.append({
                "platform": label,
                "format": fmt,
                "mode": mode,
                "status": dr["status"],
                "title": preview,
                "target_privacy": mode,
                "external_id": dr.get("external_id", ""),
                "url": dr.get("url", ""),
                "notes": dr.get("notes", ""),
            })
        elif webhook_ok:
            results.append({
                "platform": label,
                "format": fmt,
                "mode": mode,
                "status": "PUBLISHED" if mode == "publish" else "DRAFTED",
                "title": preview,
                "target_privacy": mode,
                "external_id": str(webhook_resp.get("id", webhook_resp.get("request_id", ""))),
                "url": str(webhook_resp.get("url", "")),
                "notes": f"Terkirim via webhook fallback ({webhook_msg}).",
            })
        else:
            missing_hint = direct_results.get(key, {}).get("notes", "") or webhook_msg or "Token Direct API belum diset."
            results.append({
                "platform": label,
                "format": fmt,
                "mode": mode,
                "status": "PENDING_AUTH",
                "title": preview,
                "target_privacy": mode,
                "external_id": "",
                "url": "",
                "notes": f"{missing_hint} (Lihat docs/DIRECT_SOCIAL_API_SETUP.md; payload tersimpan di {payload_file.name}).",
            })

    summary = {
        "publish_mode": mode,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "payload_snapshot": str(payload_file),
        "results": results,
        "counts": {
            "total": len(results),
            "published": sum(1 for r in results if r["status"] == "PUBLISHED"),
            "scheduled": sum(1 for r in results if r["status"] == "SCHEDULED"),
            "drafted": sum(1 for r in results if r["status"] == "DRAFTED"),
            "dry_run_ready": sum(1 for r in results if r["status"] == "DRY_RUN_READY"),
            "pending_setup": sum(1 for r in results if r["status"] in ("PENDING_AUTH", "READY_FOR_CONNECTOR")),
            "failed": sum(1 for r in results if r["status"] == "FAILED"),
        },
    }

    (run_dir / "publish_results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _format_telegram_report_html(report_summary: dict[str, Any]) -> str:
    """Format an executive, clickable HTML Telegram report for every pipeline run."""
    pub = report_summary.get("publishing") or {}
    counts = pub.get("counts") or {}
    results = pub.get("results") or []
    topic = html.escape(str(report_summary.get("topic", "Unknown Topic")))
    mode = html.escape(str(report_summary.get("publish_mode", "scheduled")))
    qa_ok = bool(report_summary.get("qa_passed_all", False))
    elapsed = report_summary.get("elapsed_sec")
    dur_txt = f"{round(float(elapsed) / 60.0, 1)} menit" if elapsed else "-"

    status_icon = {
        "PUBLISHED": "✅",
        "SCHEDULED": "🗓",
        "DRAFTED": "📝",
        "DRY_RUN_READY": "🧪",
        "PENDING_AUTH": "⏸",
        "READY_FOR_CONNECTOR": "⏸",
        "FAILED": "❌",
    }

    lines = [
        "<b>🎬 HabitSains Studio — Laporan Produksi</b>",
        f"📌 <b>Topik:</b> {topic}",
        f"⚙️ <b>Mode:</b> <code>{mode}</code> | <b>QA:</b> {'✅ LOLOS' if qa_ok else '⚠️ CEK'} | ⏱ {dur_txt}",
        (
            f"📊 <b>Ringkasan:</b> "
            f"Published={counts.get('published', 0)}, "
            f"Scheduled={counts.get('scheduled', 0)}, "
            f"Drafted={counts.get('drafted', 0)}, "
            f"Failed={counts.get('failed', 0)}"
        ),
        "",
        "<b>📡 Status Distribusi Platform:</b>",
    ]
    for r in results:
        st = str(r.get("status", ""))
        if st in ("PENDING_AUTH", "READY_FOR_CONNECTOR"):
            continue
        icon = status_icon.get(st, "•")
        plat = html.escape(str(r.get("platform", "")))
        url = str(r.get("url", "")).strip()
        note = html.escape(str(r.get("notes", ""))[:130])
        if url:
            lines.append(f'{icon} <b>{plat}</b> — <code>{st}</code> (<a href="{html.escape(url)}">Buka</a>)\n    <i>{note}</i>')
        else:
            lines.append(f"{icon} <b>{plat}</b> — <code>{st}</code>\n    <i>{note}</i>")

    gh_run_id = os.getenv("GITHUB_RUN_ID", "").strip()
    gh_repo = os.getenv("GITHUB_REPOSITORY", "").strip()
    if gh_run_id and gh_repo:
        run_url = f"https://github.com/{gh_repo}/actions/runs/{gh_run_id}"
        lines.append(f'\n🔗 <a href="{run_url}">Buka Detail &amp; Artifact di GitHub Actions</a>')

    return "\n".join(lines)[:4000]


def send_report_notification(report_summary: dict[str, Any], report_md_path: Path) -> bool:
    sent_any = False

    # 1. Telegram Bot API (Gratis, resmi, langsung ke HP dengan link clickable!)
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if tg_token and tg_chat:
        try:
            tg_msg = _format_telegram_report_html(report_summary)
            resp = requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                json={
                    "chat_id": tg_chat,
                    "text": tg_msg,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=15,
            )
            if 200 <= resp.status_code < 300:
                sent_any = True
        except Exception:
            pass

    # 2. Optional Discord / Slack / Generic Webhook
    url = os.getenv("REPORT_NOTIFICATION_WEBHOOK_URL", "").strip()
    if url:
        counts = report_summary.get("publishing", {}).get("counts", {})
        msg = (
            f"**Content Automation Studio — Laporan Produksi**\n"
            f"- Topik: {report_summary.get('topic')}\n"
            f"- Mode: `{report_summary.get('publish_mode')}`\n"
            f"- Status Platform: Published={counts.get('published', 0)}, Scheduled={counts.get('scheduled', 0)}, "
            f"Drafted={counts.get('drafted', 0)}, Failed={counts.get('failed', 0)}\n"
            f"- File Laporan: `{report_md_path}`"
        )
        try:
            resp = requests.post(url, json={"content": msg, "text": msg}, timeout=12)
            if 200 <= resp.status_code < 300:
                sent_any = True
        except Exception:
            pass

    return sent_any
