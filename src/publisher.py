from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


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
            creds = Credentials.from_authorized_user_info(token_info, YOUTUBE_SCOPES)
    elif token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), YOUTUBE_SCOPES)

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
) -> dict[str, Any]:
    from googleapiclient.http import MediaFileUpload

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:25],
            "categoryId": str(category_id),
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": made_for_kids,
        },
    }
    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    request = service.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()

    video_id = response["id"]
    thumb_uploaded = False
    if thumbnail_path and thumbnail_path.exists():
        try:
            service.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/png"),
            ).execute()
            thumb_uploaded = True
        except Exception:
            thumb_uploaded = False

    return {
        "video_id": video_id,
        "studio_url": f"https://studio.youtube.com/video/{video_id}/edit",
        "watch_url": f"https://youtu.be/{video_id}",
        "privacy_status": privacy_status,
        "thumbnail_uploaded": thumb_uploaded,
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
      - 'draft': uploads YouTube as private draft & sends status='draft' to social webhook/connectors.
      - 'publish': uploads YouTube as public & sends status='publish' to social webhook/connectors.
    """
    mode = publish_mode.lower().strip()
    if mode not in ("dry-run", "draft", "publish"):
        mode = "draft"

    platforms_cfg = config.get("platforms", {})
    yt_long_meta = blueprint.get("youtube_long", {})
    shorts_meta = blueprint.get("shorts_reels_tiktok", {})
    carousel_meta = blueprint.get("carousel_social", {})

    results: list[dict[str, Any]] = []
    youtube_service = None
    youtube_auth_err = ""

    if mode in ("draft", "publish") and (
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
                "notes": "Simulasi sukses. File video, subtitle, dan thumbnail siap diupload sebagai draft/publish.",
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
                )
                results.append({
                    "platform": "YouTube Long (16:9)",
                    "format": "Video 1920x1080 + Thumbnail",
                    "mode": mode,
                    "status": "PUBLISHED" if mode == "publish" else "DRAFTED",
                    "title": yt_long_meta.get("title", ""),
                    "target_privacy": privacy,
                    "external_id": up["video_id"],
                    "url": up["studio_url"] if mode == "draft" else up["watch_url"],
                    "notes": f"Upload sukses (privacy={privacy}, thumbnail={up['thumbnail_uploaded']}).",
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
                )
                results.append({
                    "platform": "YouTube Shorts (9:16)",
                    "format": "Video 1080x1920",
                    "mode": mode,
                    "status": "PUBLISHED" if mode == "publish" else "DRAFTED",
                    "title": short_title,
                    "target_privacy": privacy,
                    "external_id": up["video_id"],
                    "url": up["studio_url"] if mode == "draft" else up["watch_url"],
                    "notes": f"Upload Shorts sukses (privacy={privacy}).",
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

    # 3. Social Media Bundle Payload (Instagram Reels, Instagram Carousel, TikTok, LinkedIn, X/Threads, Facebook)
    social_targets = [
        ("instagram_reels", "Instagram Reels", "Video 1080x1920", shorts_meta.get("caption_ig_reels", ""), assets.get("shorts_reels_tiktok", {}).get("video_path", "")),
        ("tiktok", "TikTok", "Video 1080x1920", shorts_meta.get("caption_tiktok", ""), assets.get("shorts_reels_tiktok", {}).get("video_path", "")),
        ("instagram_carousel", "Instagram Carousel", "5 Slides 1080x1350", carousel_meta.get("caption_instagram", ""), assets.get("carousel_social", {}).get("slide_paths", [])),
        ("linkedin", "LinkedIn", "Carousel / Post", carousel_meta.get("caption_linkedin", ""), assets.get("carousel_social", {}).get("slide_paths", [])),
        ("x_threads", "X & Threads", "Thread 5 Posts + Threads", "\n\n".join(carousel_meta.get("thread_x", [])), assets.get("carousel_social", {}).get("slide_paths", [])[:1]),
        ("facebook", "Facebook Page", "Post + Carousel/Video", carousel_meta.get("post_facebook", ""), assets.get("carousel_social", {}).get("slide_paths", [])[:1]),
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

    webhook_ok = False
    webhook_msg = ""
    webhook_resp: dict[str, Any] = {}
    if mode in ("draft", "publish") and active_social:
        webhook_ok, webhook_msg, webhook_resp = _dispatch_social_webhook(webhook_payload)

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
                "notes": f"Payload siap di {payload_file.name}. Aktifkan PUBLISH_WEBHOOK_URL (Zapier/n8n) untuk auto-draft/publish.",
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
                "notes": f"Terkirim via webhook ({webhook_msg}).",
            })
        else:
            results.append({
                "platform": label,
                "format": fmt,
                "mode": mode,
                "status": "READY_FOR_CONNECTOR",
                "title": preview,
                "target_privacy": mode,
                "external_id": "",
                "url": "",
                "notes": f"{webhook_msg}. Payload tersimpan di {payload_file.name}.",
            })

    summary = {
        "publish_mode": mode,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "payload_snapshot": str(payload_file),
        "results": results,
        "counts": {
            "total": len(results),
            "published": sum(1 for r in results if r["status"] == "PUBLISHED"),
            "drafted": sum(1 for r in results if r["status"] == "DRAFTED"),
            "dry_run_ready": sum(1 for r in results if r["status"] == "DRY_RUN_READY"),
            "pending_setup": sum(1 for r in results if r["status"] in ("PENDING_AUTH", "READY_FOR_CONNECTOR")),
            "failed": sum(1 for r in results if r["status"] == "FAILED"),
        },
    }

    (run_dir / "publish_results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def send_report_notification(report_summary: dict[str, Any], report_md_path: Path) -> bool:
    url = os.getenv("REPORT_NOTIFICATION_WEBHOOK_URL", "").strip()
    if not url:
        return False
    counts = report_summary.get("publishing", {}).get("counts", {})
    msg = (
        f"**Content Automation Studio — Laporan Produksi**\n"
        f"- Topik: {report_summary.get('topic')}\n"
        f"- Mode: `{report_summary.get('publish_mode')}`\n"
        f"- Status Platform: Published={counts.get('published', 0)}, Drafted={counts.get('drafted', 0)}, "
        f"Dry-Run={counts.get('dry_run_ready', 0)}, Pending Setup={counts.get('pending_setup', 0)}\n"
        f"- File Laporan: `{report_md_path}`"
    )
    try:
        resp = requests.post(url, json={"content": msg, "text": msg}, timeout=12)
        return 200 <= resp.status_code < 300
    except Exception:
        return False
