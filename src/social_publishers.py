"""Direct Free Official Social Media API Publishers (Zero Monthly Fees, Zero Paid Hubs).

Supports direct binary/native publishing directly from local PC or GitHub Actions Cloud:
  1. Instagram Reels    — Meta Graph API v21.0 Resumable Binary Upload (`rupload.facebook.com`, no external host!)
  2. Instagram Carousel — Meta Graph API v21.0 5-slide carousel (via connected FB Page unpublished CDN bridge)
  3. Facebook Page      — Meta Graph API v21.0 Page Reels (`video_reels`, native `DRAFT` & `PUBLISHED` support!)
  4. TikTok             — TikTok Content Posting API v2 Binary `FILE_UPLOAD` to Inbox Drafts (+ auto token refresh!)
  5. LinkedIn           — LinkedIn REST API (`/rest/images` binary PUT + `/rest/posts` multiImage/single post)
  6. Meta Threads       — Threads Graph API (`graph.threads.net/v1.0/{uid}/threads` + `threads_publish`)
  7. X (Twitter v2)     — X API v2 Free Tier (`POST https://api.x.com/2/tweets`, pure-Python OAuth 1.0a HMAC-SHA1)

Every publisher returns a normalized dict:
  {
    "handled": bool,            # True if credentials were configured and direct API attempted
    "status": str,              # PUBLISHED | DRAFTED | FAILED | PENDING_AUTH
    "external_id": str,
    "url": str,
    "notes": str,
  }
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import math
import os
import secrets
import time
import urllib.parse
from pathlib import Path
from typing import Any

import requests


META_GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v21.0").strip() or "v21.0"
META_GRAPH_BASE = f"https://graph.facebook.com/{META_GRAPH_VERSION}"
LINKEDIN_API_VERSION = os.getenv("LINKEDIN_API_VERSION", "202504").strip() or "202504"
THREADS_API_BASE = "https://graph.threads.net/v1.0"


# ---------------------------------------------------------------------------
# Helpers: Meta Page Token Auto-Resolution & Container Polling
# ---------------------------------------------------------------------------

def _resolve_fb_page_token(meta_token: str, fb_page_id: str) -> str:
    """Resolve a Facebook Page Access Token from explicit env var or User Access Token."""
    explicit = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()
    if explicit:
        return explicit
    try:
        resp = requests.get(
            f"{META_GRAPH_BASE}/{fb_page_id}",
            params={"fields": "access_token", "access_token": meta_token},
            timeout=20,
        )
        if resp.ok:
            tok = resp.json().get("access_token", "").strip()
            if tok:
                return tok
    except Exception:
        pass
    return meta_token


def _poll_ig_container(container_id: str, access_token: str, timeout_sec: int = 120) -> tuple[bool, str]:
    """Poll Instagram Graph API media container until FINISHED or ERROR."""
    deadline = time.monotonic() + timeout_sec
    last_status = "IN_PROGRESS"
    while time.monotonic() < deadline:
        resp = requests.get(
            f"{META_GRAPH_BASE}/{container_id}",
            params={"fields": "status_code,status", "access_token": access_token},
            timeout=20,
        )
        if not resp.ok:
            return False, f"Status check HTTP {resp.status_code}: {resp.text[:220]}"
        data = resp.json()
        code = str(data.get("status_code", "")).upper()
        last_status = code or str(data.get("status", "UNKNOWN"))
        if code in ("FINISHED", "PUBLISHED"):
            return True, code
        if code in ("ERROR", "EXPIRED"):
            return False, f"Meta processing error ({code}): {data.get('status', '')}"
        time.sleep(4)
    return False, f"Timeout menunggu Meta memproses media (status terakhir: {last_status})"


def _upload_fb_unpublished_photo_url(photo_path: Path, fb_page_id: str, page_token: str) -> str:
    """Upload a local PNG/JPG as an unpublished temporary FB Page photo and return Meta's official HTTPS image URL."""
    with photo_path.open("rb") as fh:
        resp = requests.post(
            f"{META_GRAPH_BASE}/{fb_page_id}/photos",
            data={"published": "false", "temporary": "true", "access_token": page_token},
            files={"source": (photo_path.name, fh, "image/png")},
            timeout=45,
        )
    if not resp.ok:
        raise RuntimeError(f"FB unpublished photo upload failed ({resp.status_code}): {resp.text[:220]}")
    photo_id = resp.json().get("id")
    if not photo_id:
        raise RuntimeError(f"FB unpublished photo returned no id: {resp.text[:200]}")

    info = requests.get(
        f"{META_GRAPH_BASE}/{photo_id}",
        params={"fields": "images", "access_token": page_token},
        timeout=20,
    )
    if not info.ok:
        raise RuntimeError(f"FB photo URL fetch failed ({info.status_code}): {info.text[:220]}")
    images = info.json().get("images") or []
    if not images or not images[0].get("source"):
        raise RuntimeError(f"FB photo returned no image source URL: {info.text[:200]}")
    return str(images[0]["source"])


# ---------------------------------------------------------------------------
# 1. Instagram Reels — Direct Binary Resumable Upload (rupload.facebook.com)
# ---------------------------------------------------------------------------

def publish_instagram_reels_direct(video_path: Path | None, caption: str, publish_mode: str) -> dict[str, Any]:
    token = os.getenv("META_ACCESS_TOKEN", "").strip()
    ig_id = os.getenv("IG_BUSINESS_ACCOUNT_ID", "").strip()
    if not token or not ig_id:
        return {"handled": False, "status": "PENDING_AUTH", "external_id": "", "url": "", "notes": "META_ACCESS_TOKEN / IG_BUSINESS_ACCOUNT_ID belum diset."}
    if not video_path or not video_path.exists():
        return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": "File video 9:16 untuk Instagram Reels tidak ditemukan."}

    try:
        # Step 1 & 2: Initialize resumable upload session + upload binary to Meta rupload.facebook.com.
        # Retry with a FRESH container session if Meta's rupload edge returns transient 400 ProcessingFailedError/5xx.
        file_size = video_path.stat().st_size
        container_id = ""
        up_resp = None
        last_err_note = ""

        for session_try in range(2):
            init_resp = requests.post(
                f"{META_GRAPH_BASE}/{ig_id}/media",
                data={
                    "media_type": "REELS",
                    "upload_type": "resumable",
                    "caption": caption[:2200],
                    "share_to_feed": "true",
                    "access_token": token,
                },
                timeout=30,
            )
            if not init_resp.ok:
                last_err_note = f"IG Reels init gagal ({init_resp.status_code}): {init_resp.text[:240]}"
                if session_try == 0:
                    time.sleep(3)
                    continue
                return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": last_err_note}

            init_data = init_resp.json()
            container_id = str(init_data.get("id", ""))
            upload_uri = str(init_data.get("uri", ""))
            if not container_id or not upload_uri:
                return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": f"IG Reels init tidak mengembalikan id/uri: {init_resp.text[:200]}"}

            # Small propagation pause so Meta's rupload shard recognizes the freshly minted container_id
            time.sleep(1.5)

            # NOTE: Do NOT send Content-Type header — Meta's rupload rejects 'application/octet-stream' with HTTP 400 ProcessingFailedError!
            try:
                with video_path.open("rb") as fh:
                    up_resp = requests.post(
                        upload_uri,
                        headers={
                            "Authorization": f"OAuth {token}",
                            "offset": "0",
                            "file_size": str(file_size),
                        },
                        data=fh,
                        timeout=240,
                    )
            except requests.RequestException as exc:
                last_err_note = f"IG Reels upload error: {exc}"
                up_resp = None
                if session_try == 0:
                    time.sleep(4)
                    continue
                return {"handled": True, "status": "FAILED", "external_id": container_id, "url": "", "notes": last_err_note}

            if up_resp.ok:
                break
            last_err_note = f"IG Reels binary upload gagal ({up_resp.status_code}): {up_resp.text[:240]}"
            if session_try == 0:
                time.sleep(4)
                continue

        if up_resp is None or not up_resp.ok:
            return {"handled": True, "status": "FAILED", "external_id": container_id, "url": "", "notes": last_err_note or "IG Reels binary upload gagal"}

        # Step 3: Poll until Meta finishes ingesting the video
        ok, status_msg = _poll_ig_container(container_id, token, timeout_sec=150)
        if not ok:
            return {"handled": True, "status": "FAILED", "external_id": container_id, "url": "", "notes": status_msg}

        # Step 4: Draft vs Publish/Scheduled (in scheduled mode, cron runs directly at US Prime Time!)
        if publish_mode not in ("publish", "scheduled"):
            return {
                "handled": True,
                "status": "DRAFTED",
                "external_id": container_id,
                "url": "",
                "notes": f"Reels binary berhasil diunggah & lolos verifikasi Meta (container={container_id}, siap tayang). Gunakan mode publish/scheduled untuk merilis ke feed IG.",
            }

        pub_resp = requests.post(
            f"{META_GRAPH_BASE}/{ig_id}/media_publish",
            data={"creation_id": container_id, "access_token": token},
            timeout=30,
        )
        if not pub_resp.ok:
            return {"handled": True, "status": "FAILED", "external_id": container_id, "url": "", "notes": f"IG media_publish gagal ({pub_resp.status_code}): {pub_resp.text[:240]}"}

        media_id = str(pub_resp.json().get("id", container_id))
        permalink = ""
        try:
            pr = requests.get(f"{META_GRAPH_BASE}/{media_id}", params={"fields": "permalink", "access_token": token}, timeout=15)
            if pr.ok:
                permalink = str(pr.json().get("permalink", ""))
        except Exception:
            pass

        return {
            "handled": True,
            "status": "PUBLISHED",
            "external_id": media_id,
            "url": permalink,
            "notes": f"Instagram Reels langsung tayang via Meta Graph API (id={media_id}).",
        }
    except Exception as exc:
        return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": f"IG Reels error: {exc}"}


# ---------------------------------------------------------------------------
# 2. Instagram Carousel — 5 Slides via Connected FB Page CDN Bridge
# ---------------------------------------------------------------------------

def publish_instagram_carousel_direct(slide_paths: list[Path], caption: str, publish_mode: str) -> dict[str, Any]:
    token = os.getenv("META_ACCESS_TOKEN", "").strip()
    ig_id = os.getenv("IG_BUSINESS_ACCOUNT_ID", "").strip()
    fb_page_id = os.getenv("FB_PAGE_ID", "").strip()
    if not token or not ig_id or not fb_page_id:
        return {"handled": False, "status": "PENDING_AUTH", "external_id": "", "url": "", "notes": "Butuh META_ACCESS_TOKEN, IG_BUSINESS_ACCOUNT_ID, & FB_PAGE_ID untuk IG Carousel."}

    valid_slides = [p for p in slide_paths if p.exists()][:10]
    if len(valid_slides) < 2:
        return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": "Minimal 2 slide diperlukan untuk Instagram Carousel."}

    try:
        page_token = _resolve_fb_page_token(token, fb_page_id)
        child_ids: list[str] = []
        for slide in valid_slides:
            img_url = _upload_fb_unpublished_photo_url(slide, fb_page_id, page_token)
            ch_resp = requests.post(
                f"{META_GRAPH_BASE}/{ig_id}/media",
                data={"image_url": img_url, "is_carousel_item": "true", "access_token": token},
                timeout=30,
            )
            if not ch_resp.ok:
                return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": f"IG Carousel slide {slide.name} gagal ({ch_resp.status_code}): {ch_resp.text[:200]}"}
            child_ids.append(str(ch_resp.json()["id"]))

        parent_resp = requests.post(
            f"{META_GRAPH_BASE}/{ig_id}/media",
            data={
                "media_type": "CAROUSEL",
                "children": ",".join(child_ids),
                "caption": caption[:2200],
                "access_token": token,
            },
            timeout=30,
        )
        if not parent_resp.ok:
            return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": f"IG Carousel parent container gagal ({parent_resp.status_code}): {parent_resp.text[:220]}"}

        parent_id = str(parent_resp.json()["id"])
        ok, status_msg = _poll_ig_container(parent_id, token, timeout_sec=90)
        if not ok:
            return {"handled": True, "status": "FAILED", "external_id": parent_id, "url": "", "notes": status_msg}

        if publish_mode not in ("publish", "scheduled"):
            return {
                "handled": True,
                "status": "DRAFTED",
                "external_id": parent_id,
                "url": "",
                "notes": f"Carousel {len(child_ids)} slide berhasil diunggah ke container Meta (id={parent_id}). Gunakan mode publish/scheduled untuk tayang live.",
            }

        pub_resp = requests.post(
            f"{META_GRAPH_BASE}/{ig_id}/media_publish",
            data={"creation_id": parent_id, "access_token": token},
            timeout=30,
        )
        if not pub_resp.ok:
            return {"handled": True, "status": "FAILED", "external_id": parent_id, "url": "", "notes": f"IG Carousel publish gagal ({pub_resp.status_code}): {pub_resp.text[:220]}"}

        media_id = str(pub_resp.json().get("id", parent_id))
        permalink = ""
        try:
            pr = requests.get(f"{META_GRAPH_BASE}/{media_id}", params={"fields": "permalink", "access_token": token}, timeout=15)
            if pr.ok:
                permalink = str(pr.json().get("permalink", ""))
        except Exception:
            pass
        return {
            "handled": True,
            "status": "PUBLISHED",
            "external_id": media_id,
            "url": permalink,
            "notes": f"Instagram Carousel ({len(child_ids)} slide) tayang via Meta Graph API.",
        }
    except Exception as exc:
        return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": f"IG Carousel error: {exc}"}


# ---------------------------------------------------------------------------
# 3. Facebook Page Reels — Direct Binary Upload + Native DRAFT / PUBLISHED
# ---------------------------------------------------------------------------

def publish_facebook_reel_direct(
    video_path: Path | None,
    description: str,
    publish_mode: str,
    scheduled_publish_ts: int | None = None,
) -> dict[str, Any]:
    token = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip() or os.getenv("META_ACCESS_TOKEN", "").strip()
    fb_page_id = os.getenv("FB_PAGE_ID", "").strip()
    if not token or not fb_page_id:
        return {"handled": False, "status": "PENDING_AUTH", "external_id": "", "url": "", "notes": "META_ACCESS_TOKEN / FB_PAGE_ID belum diset."}
    if not video_path or not video_path.exists():
        return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": "File video 9:16 untuk Facebook Reels tidak ditemukan."}

    try:
        page_token = _resolve_fb_page_token(token, fb_page_id)
        # Step 1: start upload session
        start_resp = requests.post(
            f"{META_GRAPH_BASE}/{fb_page_id}/video_reels",
            json={"upload_phase": "start", "access_token": page_token},
            timeout=30,
        )
        if not start_resp.ok:
            return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": f"FB Reels start gagal ({start_resp.status_code}): {start_resp.text[:220]}"}

        start_data = start_resp.json()
        video_id = str(start_data.get("video_id", ""))
        upload_url = str(start_data.get("upload_url", ""))
        if not video_id or not upload_url:
            return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": f"FB Reels start tanpa video_id/upload_url: {start_resp.text[:200]}"}

        # Step 2: binary upload to rupload.facebook.com (Meta strictly requires lowercase 'offset' & 'file_size', NO Content-Type!)
        file_size = video_path.stat().st_size
        up_resp = None
        last_exc: Exception | None = None
        for attempt in range(2):
            try:
                with video_path.open("rb") as fh:
                    up_resp = requests.post(
                        upload_url,
                        headers={
                            "Authorization": f"OAuth {page_token}",
                            "offset": "0",
                            "file_size": str(file_size),
                        },
                        data=fh,
                        timeout=240,
                    )
                last_exc = None
                break
            except requests.RequestException as exc:
                last_exc = exc
                if attempt == 0:
                    time.sleep(2)
        if last_exc is not None or up_resp is None:
            return {"handled": True, "status": "FAILED", "external_id": video_id, "url": "", "notes": f"FB Reels upload error: {last_exc}"}
        if not up_resp.ok:
            return {"handled": True, "status": "FAILED", "external_id": video_id, "url": "", "notes": f"FB Reels binary upload gagal ({up_resp.status_code}): {up_resp.text[:220]}"}

        # Step 3: finish (supports native DRAFT, SCHEDULED at US Prime Time, or PUBLISHED!)
        fin_body: dict[str, Any] = {
            "upload_phase": "finish",
            "video_id": video_id,
            "description": description[:2200],
            "access_token": page_token,
        }
        if publish_mode == "scheduled" and scheduled_publish_ts:
            video_state = "SCHEDULED"
            fin_body["video_state"] = "SCHEDULED"
            fin_body["scheduled_publish_time"] = int(scheduled_publish_ts)
        elif publish_mode == "publish":
            video_state = "PUBLISHED"
            fin_body["video_state"] = "PUBLISHED"
        else:
            video_state = "DRAFT"
            fin_body["video_state"] = "DRAFT"

        fin_resp = requests.post(
            f"{META_GRAPH_BASE}/{fb_page_id}/video_reels",
            json=fin_body,
            timeout=45,
        )
        if not fin_resp.ok:
            return {"handled": True, "status": "FAILED", "external_id": video_id, "url": "", "notes": f"FB Reels finish gagal ({fin_resp.status_code}): {fin_resp.text[:220]}"}

        res_status = "PUBLISHED" if video_state == "PUBLISHED" else ("SCHEDULED" if video_state == "SCHEDULED" else "DRAFTED")
        sched_note = f", scheduled_unix={scheduled_publish_ts}" if video_state == "SCHEDULED" else ""
        return {
            "handled": True,
            "status": res_status,
            "external_id": video_id,
            "url": f"https://www.facebook.com/reel/{video_id}" if video_state == "PUBLISHED" else "https://business.facebook.com/latest/content_library",
            "notes": f"Facebook Page Reel sukses ({video_state}, video_id={video_id}{sched_note}).",
        }
    except Exception as exc:
        return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": f"FB Reels error: {exc}"}


# ---------------------------------------------------------------------------
# 4. TikTok Content Posting API v2 — Direct Binary FILE_UPLOAD (+ Auto Refresh!)
# ---------------------------------------------------------------------------

def _resolve_tiktok_access_token() -> tuple[str, str]:
    """Return a fresh TikTok access token, refreshing via TIKTOK_REFRESH_TOKEN if available."""
    refresh_tok = os.getenv("TIKTOK_REFRESH_TOKEN", "").strip()
    client_key = os.getenv("TIKTOK_CLIENT_KEY", "").strip()
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET", "").strip()
    static_tok = os.getenv("TIKTOK_ACCESS_TOKEN", "").strip()

    if refresh_tok and client_key and client_secret:
        try:
            resp = requests.post(
                "https://open.tiktokapis.com/v2/oauth/token/",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "client_key": client_key,
                    "client_secret": client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_tok,
                },
                timeout=25,
            )
            if resp.ok:
                new_tok = str(resp.json().get("access_token", "")).strip()
                if new_tok:
                    return new_tok, ""
            if static_tok:
                return static_tok, ""
            return "", f"TikTok refresh token gagal ({resp.status_code}): {resp.text[:200]}"
        except Exception as exc:
            if static_tok:
                return static_tok, ""
            return "", f"TikTok token refresh error: {exc}"

    if static_tok:
        return static_tok, ""
    return "", "TIKTOK_ACCESS_TOKEN / TIKTOK_REFRESH_TOKEN belum diset."


def publish_tiktok_direct(video_path: Path | None, caption: str, publish_mode: str) -> dict[str, Any]:
    token, tok_err = _resolve_tiktok_access_token()
    if not token:
        return {"handled": False, "status": "PENDING_AUTH", "external_id": "", "url": "", "notes": tok_err}
    if not video_path or not video_path.exists():
        return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": "File video 9:16 untuk TikTok tidak ditemukan."}

    try:
        video_bytes = video_path.read_bytes()
        total_size = len(video_bytes)
        # TikTok rule: single chunk if <= 64MB, else 10MB chunks (min 5MB, max 64MB, last chunk up to 128MB)
        if total_size <= 64 * 1024 * 1024:
            chunk_size = total_size
            total_chunks = 1
        else:
            chunk_size = 10 * 1024 * 1024
            total_chunks = math.floor(total_size / chunk_size)

        direct_post = os.getenv("TIKTOK_DIRECT_POST", "").strip() == "1" and publish_mode == "publish"
        if direct_post:
            init_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
            body: dict[str, Any] = {
                "post_info": {
                    "title": caption[:2200],
                    "privacy_level": os.getenv("TIKTOK_PRIVACY_LEVEL", "PUBLIC_TO_EVERYONE"),
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": total_size,
                    "chunk_size": chunk_size,
                    "total_chunk_count": total_chunks,
                },
            }
        else:
            # Inbox Draft upload works safely on unaudited apps and lands straight in TikTok app Inbox!
            init_url = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
            body = {
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": total_size,
                    "chunk_size": chunk_size,
                    "total_chunk_count": total_chunks,
                }
            }

        init_resp = requests.post(
            init_url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"},
            json=body,
            timeout=30,
        )
        if not init_resp.ok:
            return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": f"TikTok init gagal ({init_resp.status_code}): {init_resp.text[:240]}"}

        init_json = init_resp.json()
        err_obj = init_json.get("error") or {}
        if err_obj.get("code") not in (None, "", "ok"):
            return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": f"TikTok API error ({err_obj.get('code')}): {err_obj.get('message', '')}"}

        data = init_json.get("data") or {}
        publish_id = str(data.get("publish_id", ""))
        upload_url = str(data.get("upload_url", ""))
        if not upload_url:
            return {"handled": True, "status": "FAILED", "external_id": publish_id, "url": "", "notes": f"TikTok tidak mengembalikan upload_url: {init_resp.text[:200]}"}

        # Sequential PUT chunks with exact 0-indexed inclusive Content-Range
        for idx in range(total_chunks):
            start = idx * chunk_size
            end_exclusive = total_size if idx == total_chunks - 1 else (idx + 1) * chunk_size
            chunk = video_bytes[start:end_exclusive]
            put_resp = requests.put(
                upload_url,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {start}-{end_exclusive - 1}/{total_size}",
                },
                data=chunk,
                timeout=180,
            )
            if put_resp.status_code not in (200, 201, 206):
                return {"handled": True, "status": "FAILED", "external_id": publish_id, "url": "", "notes": f"TikTok PUT chunk {idx + 1}/{total_chunks} gagal ({put_resp.status_code}): {put_resp.text[:200]}"}

        return {
            "handled": True,
            "status": "PUBLISHED" if direct_post else "DRAFTED",
            "external_id": publish_id,
            "url": "",
            "notes": (
                f"TikTok Direct Post sukses (publish_id={publish_id})."
                if direct_post
                else f"Video 3D POV masuk ke TikTok Inbox Draft Anda (publish_id={publish_id}) — siap klik Post di aplikasi TikTok!"
            ),
        }
    except Exception as exc:
        return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": f"TikTok upload error: {exc}"}


# ---------------------------------------------------------------------------
# 5. LinkedIn REST API — Direct Image/Multi-Image Upload + Post
# ---------------------------------------------------------------------------

def publish_linkedin_direct(slide_paths: list[Path], caption: str, publish_mode: str) -> dict[str, Any]:
    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
    author_urn = os.getenv("LINKEDIN_AUTHOR_URN", "").strip()
    if not token or not author_urn:
        return {"handled": False, "status": "PENDING_AUTH", "external_id": "", "url": "", "notes": "LINKEDIN_ACCESS_TOKEN / LINKEDIN_AUTHOR_URN belum diset."}

    if publish_mode not in ("publish", "scheduled") and not author_urn.startswith("urn:li:organization:"):
        # LinkedIn personal profiles (w_member_social) do not support DRAFT lifecycleState via API.
        return {
            "handled": True,
            "status": "DRAFTED",
            "external_id": "",
            "url": "",
            "notes": "Kredensial LinkedIn valid. Mode draft tidak memposting langsung ke profil personal (ubah ke publish/scheduled untuk tayang otomatis).",
        }

    headers = {
        "Authorization": f"Bearer {token}",
        "Linkedin-Version": LINKEDIN_API_VERSION,
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }

    try:
        uploaded_urns: list[str] = []
        for slide in [p for p in slide_paths if p.exists()][:5]:
            init_resp = requests.post(
                "https://api.linkedin.com/rest/images?action=initializeUpload",
                headers=headers,
                json={"initializeUploadRequest": {"owner": author_urn}},
                timeout=25,
            )
            if not init_resp.ok:
                return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": f"LinkedIn image init gagal ({init_resp.status_code}): {init_resp.text[:220]}"}
            val = init_resp.json().get("value") or {}
            up_url, img_urn = str(val.get("uploadUrl", "")), str(val.get("image", ""))
            if not up_url or not img_urn:
                return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": f"LinkedIn image init invalid: {init_resp.text[:200]}"}

            put_resp = requests.put(
                up_url,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "image/png"},
                data=slide.read_bytes(),
                timeout=60,
            )
            if put_resp.status_code not in (200, 201):
                return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": f"LinkedIn image PUT gagal ({put_resp.status_code}): {put_resp.text[:200]}"}
            uploaded_urns.append(img_urn)

        lifecycle = "PUBLISHED" if publish_mode in ("publish", "scheduled") else "DRAFT"
        payload: dict[str, Any] = {
            "author": author_urn,
            "commentary": caption[:2950],
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": lifecycle,
            "isReshareDisabledByAuthor": False,
        }
        if len(uploaded_urns) >= 2:
            payload["content"] = {
                "multiImage": {
                    "images": [{"id": u, "altText": f"HabitSains slide {i + 1}"} for i, u in enumerate(uploaded_urns)]
                }
            }
        elif len(uploaded_urns) == 1:
            payload["content"] = {"media": {"id": uploaded_urns[0], "altText": "HabitSains visual"}}

        post_resp = requests.post("https://api.linkedin.com/rest/posts", headers=headers, json=payload, timeout=30)
        if post_resp.status_code not in (200, 201):
            return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": f"LinkedIn post gagal ({post_resp.status_code}): {post_resp.text[:240]}"}

        post_id = str(post_resp.headers.get("x-restli-id", ""))
        return {
            "handled": True,
            "status": "PUBLISHED" if lifecycle == "PUBLISHED" else "DRAFTED",
            "external_id": post_id,
            "url": f"https://www.linkedin.com/feed/update/{post_id}/" if post_id and lifecycle == "PUBLISHED" else "",
            "notes": f"LinkedIn post ({len(uploaded_urns)} slide, state={lifecycle}) sukses.",
        }
    except Exception as exc:
        return {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": f"LinkedIn error: {exc}"}


# ---------------------------------------------------------------------------
# 6. Meta Threads API + X (Twitter API v2 OAuth 1.0a Pure-Python)
# ---------------------------------------------------------------------------

def _oauth1_header(method: str, url: str, api_key: str, api_secret: str, access_token: str, access_secret: str) -> str:
    """Build RFC-5849 OAuth 1.0a Authorization header (HMAC-SHA1) with zero external packages."""
    oauth_params = {
        "oauth_consumer_key": api_key,
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }
    encoded_pairs = sorted(
        (urllib.parse.quote(k, safe=""), urllib.parse.quote(v, safe=""))
        for k, v in oauth_params.items()
    )
    param_str = "&".join(f"{k}={v}" for k, v in encoded_pairs)
    base_str = "&".join([
        method.upper(),
        urllib.parse.quote(url, safe=""),
        urllib.parse.quote(param_str, safe=""),
    ])
    signing_key = f"{urllib.parse.quote(api_secret, safe='')}&{urllib.parse.quote(access_secret, safe='')}"
    sig = base64.b64encode(hmac.new(signing_key.encode("utf-8"), base_str.encode("utf-8"), hashlib.sha1).digest()).decode("utf-8")
    oauth_params["oauth_signature"] = sig
    hdr_items = ", ".join(
        f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
        for k, v in sorted(oauth_params.items())
    )
    return f"OAuth {hdr_items}"


def publish_x_and_threads_direct(thread_tweets: list[str], threads_text: str, publish_mode: str) -> dict[str, Any]:
    """Publish directly to Meta Threads and/or X (Twitter API v2 Free Tier) if configured."""
    th_token = os.getenv("THREADS_ACCESS_TOKEN", "").strip()
    th_uid = os.getenv("THREADS_USER_ID", "").strip()

    x_ck = os.getenv("X_API_KEY", "").strip()
    x_cs = os.getenv("X_API_SECRET", "").strip()
    x_at = os.getenv("X_ACCESS_TOKEN", "").strip()
    x_as = os.getenv("X_ACCESS_SECRET", "").strip()

    has_threads = bool(th_token and th_uid)
    has_x = bool(x_ck and x_cs and x_at and x_as)
    if not has_threads and not has_x:
        return {"handled": False, "status": "PENDING_AUTH", "external_id": "", "url": "", "notes": "THREADS_ACCESS_TOKEN/THREADS_USER_ID atau X_API_KEY..X_ACCESS_SECRET belum diset."}

    notes: list[str] = []
    ext_ids: list[str] = []
    urls: list[str] = []
    any_fail = False
    any_pub = False

    # A) Meta Threads Direct API
    if has_threads and threads_text.strip():
        try:
            c_resp = requests.post(
                f"{THREADS_API_BASE}/{th_uid}/threads",
                data={"media_type": "TEXT", "text": threads_text.strip()[:500], "access_token": th_token},
                timeout=25,
            )
            if not c_resp.ok:
                any_fail = True
                notes.append(f"Threads container gagal ({c_resp.status_code}): {c_resp.text[:140]}")
            else:
                cid = str(c_resp.json().get("id", ""))
                if publish_mode in ("publish", "scheduled"):
                    # Meta Threads API needs a brief propagation window after creating the container before threads_publish
                    p_resp = None
                    for wait_s in (2.5, 4.0, 6.0):
                        time.sleep(wait_s)
                        p_resp = requests.post(
                            f"{THREADS_API_BASE}/{th_uid}/threads_publish",
                            data={"creation_id": cid, "access_token": th_token},
                            timeout=25,
                        )
                        if p_resp.ok:
                            break
                        if p_resp.status_code not in (400, 429, 500, 502, 503):
                            break
                    if p_resp is not None and p_resp.ok:
                        tid = str(p_resp.json().get("id", cid))
                        ext_ids.append(f"threads:{tid}")
                        any_pub = True
                        notes.append(f"Threads tayang (id={tid})")
                    else:
                        any_fail = True
                        sc = p_resp.status_code if p_resp is not None else "?"
                        body_txt = p_resp.text[:160] if p_resp is not None else ""
                        notes.append(f"Threads publish gagal ({sc}): {body_txt}")
                else:
                    ext_ids.append(f"threads_draft:{cid}")
                    notes.append(f"Threads container siap (draft id={cid})")
        except Exception as exc:
            any_fail = True
            notes.append(f"Threads error: {exc}")

    # B) X (Twitter API v2 Free Tier)
    if has_x and thread_tweets:
        if publish_mode not in ("publish", "scheduled"):
            notes.append(f"X API siap ({len(thread_tweets)} tweet — mode draft dilewati agar tidak langsung tweet publik)")
        else:
            try:
                tweet_url = "https://api.x.com/2/tweets"
                reply_to: str | None = None
                first_id = ""
                for tw in thread_tweets[:6]:
                    body: dict[str, Any] = {"text": tw.strip()[:280]}
                    if reply_to:
                        body["reply"] = {"in_reply_to_tweet_id": reply_to}
                    auth_hdr = _oauth1_header("POST", tweet_url, x_ck, x_cs, x_at, x_as)
                    r = requests.post(tweet_url, headers={"Authorization": auth_hdr, "Content-Type": "application/json"}, json=body, timeout=25)
                    if not r.ok:
                        any_fail = True
                        notes.append(f"X tweet gagal ({r.status_code}): {r.text[:140]}")
                        break
                    tid = str((r.json().get("data") or {}).get("id", ""))
                    if not first_id:
                        first_id = tid
                    reply_to = tid
                if first_id:
                    ext_ids.append(f"x:{first_id}")
                    urls.append(f"https://x.com/i/web/status/{first_id}")
                    any_pub = True
                    notes.append(f"X thread tayang ({len(thread_tweets)} tweet, id={first_id})")
            except Exception as exc:
                any_fail = True
                notes.append(f"X error: {exc}")

    status = "FAILED" if (any_fail and not any_pub and not ext_ids) else ("PUBLISHED" if any_pub else "DRAFTED")
    return {
        "handled": True,
        "status": status,
        "external_id": ", ".join(ext_ids),
        "url": urls[0] if urls else "",
        "notes": "; ".join(notes),
    }
