"""Multi-Platform Natural Human-Style Comment Auto-Reply Bot (YouTube, IG, FB, Threads).

Key features:
  - Mirrors the exact language, slang, and vibe of every commenter (casual English slang,
    Indo tongkrongan/gaul, polite/formal Bahasa Indonesia, etc.) — ZERO robotic AI clichés!
  - Automatically skips spam/bot links, own channel/page comments, and already-replied IDs.
  - Tallies interactive [A] vs [B] votes from viewer comments so you immediately know which
    branch wins for Part 2!
  - Protects daily YouTube API upload quota (strict daily YouTube reply cap configurable in YAML).
  - Sends a crisp summary + live A/B vote scoreboard to Telegram (@Ars_Id_bot).

Usage:
  python -m src.comment_bot             # Live auto-reply across all connected platforms
  python -m src.comment_bot --dry-run   # Preview replies & A/B vote tally without posting
"""

from __future__ import annotations

import argparse
import html
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from src.config_loader import get_project_paths, load_config
from src.publisher import _get_youtube_service
from src.social_publishers import META_GRAPH_BASE, THREADS_API_BASE, _resolve_fb_page_token


# ---------------------------------------------------------------------------
# Spam Filter, A/B Vote Detector & Natural Human Reply Engine (Zero AI Slop!)
# ---------------------------------------------------------------------------

SPAM_PATTERNS = re.compile(
    r"(https?://|www\.|t\.me/|wa\.me/|whatsapp\s*\+?\d|crypto|forex|binary\s*option|"
    r"dm\s+me\s+for\s+promo|check\s+my\s+profile|sub\s*4\s*sub|subscribe\s+back|slot\s*gacor|judol)",
    re.IGNORECASE,
)

AI_CLICHE_PREFIXES = (
    "great question!",
    "great point!",
    "fantastic point!",
    "thanks for sharing!",
    "thank you for sharing!",
    "thank you for your comment!",
    "absolutely!",
    "i completely agree!",
    "that's a great insight!",
    "pertanyaan yang sangat bagus!",
    "terima kasih atas komentarnya!",
    "terima kasih sudah berbagi!",
)


def is_spam_comment(text: str) -> bool:
    clean = (text or "").strip()
    if not clean:
        return True
    if SPAM_PATTERNS.search(clean):
        return True
    return False


def detect_ab_vote(text: str) -> str | None:
    """Detect whether a viewer voted Option A or Option B in an interactive POV video."""
    t = (text or "").strip()
    if not t:
        return None
    low = t.lower()
    # Standalone 'A' / 'B' or phrases like "option A", "pilih B", "gw A", "definitely B", "team A"
    if re.fullmatch(r"[\[\(]?a[\]\)\!\.\?\s]*", low):
        return "A"
    if re.fullmatch(r"[\[\(]?b[\]\)\!\.\?\s]*", low):
        return "B"
    has_a = bool(re.search(r"\b(option\s*a|pilih\s*a|tim\s*a|team\s*a|vote\s*a|definitely\s*a|gw\s*a|gue\s*a|aku\s*a|saya\s*a|jawab\s*a|a\s+all\s+day|a\s+lah|a\s+sih|a\s+bang|a\s+bro)\b", low))
    has_b = bool(re.search(r"\b(option\s*b|pilih\s*b|tim\s*b|team\s*b|vote\s*b|definitely\s*b|gw\s*b|gue\s*b|aku\s*b|saya\s*b|jawab\s*b|b\s+all\s+day|b\s+lah|b\s+sih|b\s+bang|b\s+bro)\b", low))
    if has_a and not has_b:
        return "A"
    if has_b and not has_a:
        return "B"
    return None


def _looks_indonesian(text: str) -> bool:
    low = f" {(text or '').lower()} "
    indo_hits = (
        " gw ", " gue ", " gua ", " aku ", " saya ", " kamu ", " lu ", " lo ",
        " bang ", " bro ", " kak ", " min ", " wkwk", " haha", " anjir", " njir",
        " banget", " bgt", " sih ", " lah ", " dong ", " nih ", " yang ", " yg ",
        " gak ", " ga ", " nggak ", " tidak ", " pilih ", " bagus ", " keren ",
        " mantap", " terima kasih", " makasih", " relate ", " parah ", " jujur ",
        " bener", " benar", " tidur ", " fokus ", " hp ", " otak ",
    )
    return any(tok in low for tok in indo_hits)


def _looks_casual_slang_id(text: str) -> bool:
    low = f" {(text or '').lower()} "
    slang = (" gw ", " gue ", " gua ", " lu ", " lo ", " wkwk", " anjir", " njir", " bgt", " banget", " bang ", " lah ", " sih ", " gak ", " ga ", " dong", " parah", " boncos", " gabut")
    return any(tok in low for tok in slang)


def _sanitize_human_reply(reply: str) -> str:
    """Strip quotes, hashtags, em-dashes, and robotic AI openings so replies feel 100% typed by hand."""
    r = (reply or "").strip().strip('"').strip("'").strip()
    r = re.sub(r"\s*#\w+", "", r).strip()
    r = r.replace("—", " - ").replace("–", " - ")
    r = re.sub(r"\s+", " ", r).strip()
    low = r.lower()
    for bad in AI_CLICHE_PREFIXES:
        if low.startswith(bad):
            r = r[len(bad):].lstrip(" ,.-!")
            break
    # Keep concise like a real creator replying on mobile
    if len(r) > 190:
        cut = r[:185].rsplit(" ", 1)[0].rstrip(",;:")
        r = cut + ("." if not cut.endswith((".", "!", "?")) else "")
    return r


def _fallback_human_reply(comment_text: str, vote: str | None) -> str:
    """Natural, non-robotic fallback replies if Gemini API is unavailable."""
    is_id = _looks_indonesian(comment_text)
    slang_id = _looks_casual_slang_id(comment_text)

    if vote == "A":
        if is_id and slang_id:
            return random.choice([
                "nah cakep, amanin dulu fokusnya biar gak kejebak scroll wkwk. tungguin part 2 ya!",
                "pilihan aman bang, otak langsung lega tuh. cek efeknya di part 2 nanti 👀",
                "gokil disiplin amat milih A 😂 liat nanti hasilnya di part 2!",
            ])
        if is_id:
            return random.choice([
                "Pilihan tepat kak, fokus pagi langsung terjaga. Tunggu lanjutannya di Part 2 ya!",
                "Setuju banget pilih A, efeknya kerasa sampai sore. Part 2 segera tayang ya.",
            ])
        return random.choice([
            "smart call fr, your future self at 3pm is thanking you already. part 2 soon 👀",
            "locked in on A! let's see if it holds up in part 2",
            "solid discipline picking A ngl, wait till you see what happens next",
        ])

    if vote == "B":
        if is_id and slang_id:
            return random.choice([
                "wkwk jujur amat bang 😭 liat aja nasib fokusnya jam 3 sore di part 2 nanti",
                "relate parah sih, emang godaan 2 menit paling bahaya 😂 tungguin part 2!",
                "berani banget milih B wkwk, siap-siap liat efek dopaminnya di part 2 👀",
            ])
        if is_id:
            return random.choice([
                "Jujur banget kak 😅 lihat efeknya ke fokus di Part 2 nanti ya!",
                "Memang paling susah nolak godaan B ya kak, tunggu kelanjutannya di Part 2!",
            ])
        return random.choice([
            "lol respect the honesty 💀 wait till you see what happens at 3pm in part 2",
            "brave choice picking B 😅 your dopamine meter is sweating already",
            "honestly half of us do B on autopilot lol, part 2 is gonna expose us",
        ])

    if is_id and slang_id:
        return random.choice([
            "wkwk bener banget sih, sering kejadian tanpa sadar kan 😅",
            "nah iya parah, emang jebakan kecil gitu yg paling ngaruh ke fokus!",
            "setuju bang, makanya kudu diakalin dari awal sebelum kebablasan 😂",
        ])
    if is_id:
        return random.choice([
            "Makasih banyak kak sudah mampir, semoga langsung kerasa bedanya pas dicoba ya!",
            "Betul banget kak, kebiasaan kecil kayak gini efeknya lumayan gede ke fokus harian.",
        ])
    return random.choice([
        "fr it's wild how fast autopilot kicks in when you're not watching 😅",
        "appreciate you watching! let me know if you try it out this week",
        "spot on, those tiny morning habits make a massive difference by afternoon",
    ])


def generate_human_reply(
    comment_text: str,
    post_context: str,
    platform: str,
    config: dict[str, Any],
    vote: str | None = None,
) -> str:
    """Generate a short, natural, human-sounding reply mirroring the commenter's exact language & slang."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return _fallback_human_reply(comment_text, vote)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        model = config.get("ai", {}).get("text_model", "gemini-3.8-flash")
        vote_hint = f"The commenter voted for Option {vote} on our interactive A/B decision video." if vote else "Normal viewer comment."

        prompt = f"""You are the real human creator behind @HabitSains replying to a viewer comment from your phone on {platform}.

Video / Post topic: {post_context[:260]}
Viewer comment: "{comment_text[:320]}"
Context: {vote_hint}

STRICT STYLE RULES (CRITICAL — DO NOT SOUND LIKE AI!):
1. MIRROR THE EXACT LANGUAGE & VIBE of the viewer's comment:
   - If they use Indonesian slang/tongkrongan ("gw/lu/wkwk/anjir/bang/bgt/sih"), reply in natural casual Indonesian tongkrongan (e.g. "wkwk jujur amat bang 😂 liat aja efeknya di part 2 nanti").
   - If they use polite/formal Indonesian ("terima kasih/kak/sangat bermanfaat"), reply warmly in polite natural Indonesian.
   - If they use casual English / Gen-Z slang ("bro/fr/lol/cooked/ngl"), reply in relaxed casual English creator banter (lowercase is totally fine!).
   - If they use standard English or another language (Spanish, Malay, etc.), reply naturally in that exact same language & tone.
   - If the comment is ONLY a single letter "A" or "B", reply in casual English matching the @HabitSains global audience.
2. SOUND 100% HUMAN TYPING WITH THUMBS ON A PHONE:
   - Strictly 1 to 2 VERY SHORT sentences (max 20 words total!).
   - NEVER start with AI clichés like "Great question!", "Thanks for sharing!", "Absolutely!", "That's a fantastic point!", "Pertanyaan yang bagus!", or "Terima kasih atas komentarnya!".
   - NEVER use em-dashes (—), bullet points, quotation marks, or hashtags (#).
   - Use at most 1 natural emoji (or zero).
   - If they voted A or B, playfully react to their pick and tease Part 2 without sounding salesy.

Output ONLY the raw reply text, nothing else."""

        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.92, max_output_tokens=80),
        )
        raw = _sanitize_human_reply(resp.text or "")
        if len(raw) >= 4:
            return raw
    except Exception:
        pass
    return _fallback_human_reply(comment_text, vote)


# ---------------------------------------------------------------------------
# Persistent Reply State + Daily YouTube Quota Guard (`output/replied_comments.json`)
# ---------------------------------------------------------------------------

def _load_reply_state(state_file: Path) -> dict[str, Any]:
    if not state_file.exists():
        return {"replied_ids": {}, "vote_tally": {}, "yt_daily_counts": {}}
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        data.setdefault("replied_ids", {})
        data.setdefault("vote_tally", {})
        data.setdefault("yt_daily_counts", {})
        return data
    except (json.JSONDecodeError, OSError):
        return {"replied_ids": {}, "vote_tally": {}, "yt_daily_counts": {}}


def _save_reply_state(state_file: Path, state: dict[str, Any]) -> None:
    # Keep state compact (retain last 2,000 replied IDs & last 30 days of YT daily counts)
    rep = state.get("replied_ids", {})
    if len(rep) > 2000:
        keys = list(rep.keys())[-2000:]
        state["replied_ids"] = {k: rep[k] for k in keys}
    yt_d = state.get("yt_daily_counts", {})
    if len(yt_d) > 30:
        keys = sorted(yt_d.keys())[-30:]
        state["yt_daily_counts"] = {k: yt_d[k] for k in keys}
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _record_vote(state: dict[str, Any], content_key: str, vote: str | None) -> None:
    if vote not in ("A", "B"):
        return
    vt = state.setdefault("vote_tally", {}).setdefault(content_key, {"A": 0, "B": 0})
    vt[vote] = int(vt.get(vote, 0)) + 1


# ---------------------------------------------------------------------------
# Platform Scanners & Repliers (YouTube, Instagram, Facebook, Threads)
# ---------------------------------------------------------------------------

def _process_youtube_comments(
    project_root: Path,
    config: dict[str, Any],
    state: dict[str, Any],
    max_replies: int,
    dry_run: bool,
) -> dict[str, Any]:
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily_cap = int(config.get("comment_bot", {}).get("youtube_daily_reply_cap", 4))
    used_today = int(state.get("yt_daily_counts", {}).get(today_utc, 0))
    allowed = max(0, min(max_replies, daily_cap - used_today))
    if allowed <= 0:
        return {"platform": "YouTube", "status": "QUOTA_GUARD", "replied": [], "notes": f"Batas aman harian YouTube ({daily_cap}/hari) tercapai agar kuota upload video tetap aman."}

    service, err = _get_youtube_service(project_root)
    if not service:
        return {"platform": "YouTube", "status": "PENDING_AUTH", "replied": [], "notes": err}

    replied: list[dict[str, str]] = []
    try:
        ch_resp = service.channels().list(part="id,contentDetails", mine=True).execute()
        items = ch_resp.get("items") or []
        if not items:
            return {"platform": "YouTube", "status": "SKIPPED", "replied": [], "notes": "Channel YouTube tidak ditemukan."}
        my_channel_id = items[0]["id"]
        uploads_pl = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

        pl_resp = service.playlistItems().list(part="snippet", playlistId=uploads_pl, maxResults=8).execute()
        videos = pl_resp.get("items") or []

        for v in videos:
            if len(replied) >= allowed:
                break
            sn = v.get("snippet") or {}
            vid_id = (sn.get("resourceId") or {}).get("videoId", "")
            vid_title = sn.get("title", "HabitSains video")
            if not vid_id:
                continue
            try:
                th_resp = service.commentThreads().list(
                    part="snippet,replies", videoId=vid_id, maxResults=15, order="time", textFormat="plainText"
                ).execute()
            except Exception as exc:
                msg = str(exc)
                if "commentsDisabled" in msg or "forbidden" in msg.lower():
                    continue
                if "insufficient" in msg.lower() or "scope" in msg.lower() or "403" in msg:
                    return {
                        "platform": "YouTube",
                        "status": "NEEDS_SCOPE",
                        "replied": replied,
                        "notes": "Token YouTube butuh scope youtube.force-ssl — jalankan `python -m src.auth_youtube` 1x lalu update secret YOUTUBE_TOKEN_JSON.",
                    }
                continue

            for th in th_resp.get("items") or []:
                if len(replied) >= allowed:
                    break
                cid = th["id"]
                key = f"yt:{cid}"
                if key in state["replied_ids"]:
                    continue
                top = (th.get("snippet") or {}).get("topLevelComment", {}).get("snippet", {})
                author_ch = (top.get("authorChannelId") or {}).get("value", "")
                if author_ch == my_channel_id:
                    continue
                # Skip if we already replied manually on YouTube Studio
                existing_replies = (th.get("replies") or {}).get("comments") or []
                if any((r.get("snippet", {}).get("authorChannelId") or {}).get("value") == my_channel_id for r in existing_replies):
                    state["replied_ids"][key] = "manual_already_replied"
                    continue
                text = str(top.get("textDisplay") or top.get("textOriginal") or "").strip()
                if is_spam_comment(text):
                    continue

                vote = detect_ab_vote(text)
                reply_txt = generate_human_reply(text, vid_title, "YouTube", config, vote=vote)
                if not dry_run:
                    service.comments().insert(
                        part="snippet",
                        body={"snippet": {"parentId": cid, "textOriginal": reply_txt}},
                    ).execute()
                    state["replied_ids"][key] = datetime.now(timezone.utc).isoformat()
                    state["yt_daily_counts"][today_utc] = int(state["yt_daily_counts"].get(today_utc, 0)) + 1
                    _record_vote(state, f"yt:{vid_id} ({vid_title[:32]})", vote)
                    time.sleep(1.5)
                replied.append({"author": top.get("authorDisplayName", "viewer"), "comment": text, "reply": reply_txt, "vote": vote or ""})
        return {"platform": "YouTube", "status": "OK", "replied": replied, "notes": f"{len(replied)} komentar dibalas."}
    except Exception as exc:
        msg = str(exc)
        if "insufficient" in msg.lower() or "scope" in msg.lower() or "403" in msg:
            return {"platform": "YouTube", "status": "NEEDS_SCOPE", "replied": replied, "notes": "Butuh re-auth YouTube dengan scope youtube.force-ssl (`python -m src.auth_youtube`)."}
        return {"platform": "YouTube", "status": "FAILED", "replied": replied, "notes": f"YouTube error: {msg[:200]}"}


def _process_instagram_comments(
    config: dict[str, Any],
    state: dict[str, Any],
    max_replies: int,
    dry_run: bool,
) -> dict[str, Any]:
    tok = os.getenv("META_ACCESS_TOKEN", "").strip()
    ig_id = os.getenv("IG_BUSINESS_ACCOUNT_ID", "").strip()
    if not tok or not ig_id:
        return {"platform": "Instagram", "status": "PENDING_AUTH", "replied": [], "notes": "META_ACCESS_TOKEN / IG_BUSINESS_ACCOUNT_ID belum diset."}

    replied: list[dict[str, str]] = []
    try:
        me = requests.get(f"{META_GRAPH_BASE}/{ig_id}", params={"fields": "username", "access_token": tok}, timeout=15)
        my_user = (me.json().get("username") or "").lower() if me.ok else ""

        med = requests.get(f"{META_GRAPH_BASE}/{ig_id}/media", params={"fields": "id,caption,permalink", "limit": 8, "access_token": tok}, timeout=20)
        if not med.ok:
            return {"platform": "Instagram", "status": "FAILED", "replied": [], "notes": f"IG media fetch ({med.status_code}): {med.text[:160]}"}

        for m in med.json().get("data") or []:
            if len(replied) >= max_replies:
                break
            mid = m["id"]
            cap = str(m.get("caption") or "HabitSains Reel")
            cm = requests.get(
                f"{META_GRAPH_BASE}/{mid}/comments",
                params={"fields": "id,text,username,replies{username}", "limit": 15, "access_token": tok},
                timeout=20,
            )
            if not cm.ok:
                if cm.status_code in (400, 403) and ("permission" in cm.text.lower() or "instagram_manage_comments" in cm.text.lower()):
                    return {"platform": "Instagram", "status": "NEEDS_SCOPE", "replied": replied, "notes": "Tambah izin instagram_manage_comments di Meta Graph API Explorer."}
                continue

            for c in cm.json().get("data") or []:
                if len(replied) >= max_replies:
                    break
                cid = str(c.get("id", ""))
                key = f"ig:{cid}"
                if not cid or key in state["replied_ids"]:
                    continue
                user = str(c.get("username") or "")
                if my_user and user.lower() == my_user:
                    continue
                existing = (c.get("replies") or {}).get("data") or []
                if my_user and any(str(x.get("username", "")).lower() == my_user for x in existing):
                    state["replied_ids"][key] = "manual_already_replied"
                    continue
                text = str(c.get("text") or "").strip()
                if is_spam_comment(text):
                    continue

                vote = detect_ab_vote(text)
                reply_txt = generate_human_reply(text, cap, "Instagram", config, vote=vote)
                if not dry_run:
                    rp = requests.post(
                        f"{META_GRAPH_BASE}/{cid}/replies",
                        data={"message": reply_txt, "access_token": tok},
                        timeout=20,
                    )
                    if not rp.ok:
                        if rp.status_code in (400, 403) and "permission" in rp.text.lower():
                            return {"platform": "Instagram", "status": "NEEDS_SCOPE", "replied": replied, "notes": "Butuh izin instagram_manage_comments di token Meta."}
                        continue
                    state["replied_ids"][key] = datetime.now(timezone.utc).isoformat()
                    _record_vote(state, f"ig:{mid}", vote)
                    time.sleep(1.5)
                replied.append({"author": f"@{user}" if user else "viewer", "comment": text, "reply": reply_txt, "vote": vote or ""})

        return {"platform": "Instagram", "status": "OK", "replied": replied, "notes": f"{len(replied)} komentar dibalas."}
    except Exception as exc:
        return {"platform": "Instagram", "status": "FAILED", "replied": replied, "notes": f"IG error: {exc}"}


def _process_facebook_comments(
    config: dict[str, Any],
    state: dict[str, Any],
    max_replies: int,
    dry_run: bool,
) -> dict[str, Any]:
    tok = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip() or os.getenv("META_ACCESS_TOKEN", "").strip()
    fb_id = os.getenv("FB_PAGE_ID", "").strip()
    if not tok or not fb_id:
        return {"platform": "Facebook Page", "status": "PENDING_AUTH", "replied": [], "notes": "FB_PAGE_ID / META_ACCESS_TOKEN belum diset."}

    replied: list[dict[str, str]] = []
    try:
        page_tok = _resolve_fb_page_token(tok, fb_id)
        posts_resp = requests.get(
            f"{META_GRAPH_BASE}/{fb_id}/posts",
            params={"fields": "id,message", "limit": 8, "access_token": page_tok},
            timeout=20,
        )
        post_items = (posts_resp.json().get("data") or []) if posts_resp.ok else []

        for p in post_items:
            if len(replied) >= max_replies:
                break
            pid = p["id"]
            msg_ctx = str(p.get("message") or "HabitSains Facebook Post")
            cm = requests.get(
                f"{META_GRAPH_BASE}/{pid}/comments",
                params={"fields": "id,message,from,comments{from}", "limit": 15, "access_token": page_tok},
                timeout=20,
            )
            if not cm.ok:
                continue

            for c in cm.json().get("data") or []:
                if len(replied) >= max_replies:
                    break
                cid = str(c.get("id", ""))
                key = f"fb:{cid}"
                if not cid or key in state["replied_ids"]:
                    continue
                author = c.get("from") or {}
                if str(author.get("id", "")) == fb_id:
                    continue
                existing = (c.get("comments") or {}).get("data") or []
                if any(str((x.get("from") or {}).get("id", "")) == fb_id for x in existing):
                    state["replied_ids"][key] = "manual_already_replied"
                    continue
                text = str(c.get("message") or "").strip()
                if is_spam_comment(text):
                    continue

                vote = detect_ab_vote(text)
                reply_txt = generate_human_reply(text, msg_ctx, "Facebook", config, vote=vote)
                if not dry_run:
                    rp = requests.post(
                        f"{META_GRAPH_BASE}/{cid}/comments",
                        data={"message": reply_txt, "access_token": page_tok},
                        timeout=20,
                    )
                    if not rp.ok:
                        if rp.status_code in (400, 403) and "permission" in rp.text.lower():
                            return {"platform": "Facebook Page", "status": "NEEDS_SCOPE", "replied": replied, "notes": "Butuh izin pages_manage_engagement di token Meta."}
                        continue
                    state["replied_ids"][key] = datetime.now(timezone.utc).isoformat()
                    _record_vote(state, f"fb:{pid}", vote)
                    time.sleep(1.5)
                replied.append({"author": author.get("name", "viewer"), "comment": text, "reply": reply_txt, "vote": vote or ""})

        return {"platform": "Facebook Page", "status": "OK", "replied": replied, "notes": f"{len(replied)} komentar dibalas."}
    except Exception as exc:
        return {"platform": "Facebook Page", "status": "FAILED", "replied": replied, "notes": f"FB error: {exc}"}


def _process_threads_comments(
    config: dict[str, Any],
    state: dict[str, Any],
    max_replies: int,
    dry_run: bool,
) -> dict[str, Any]:
    tok = os.getenv("THREADS_ACCESS_TOKEN", "").strip()
    uid = os.getenv("THREADS_USER_ID", "").strip()
    if not tok or not uid:
        return {"platform": "Threads", "status": "PENDING_AUTH", "replied": [], "notes": "THREADS_ACCESS_TOKEN / THREADS_USER_ID belum diset."}

    replied: list[dict[str, str]] = []
    try:
        me = requests.get(f"{THREADS_API_BASE}/me", params={"fields": "username", "access_token": tok}, timeout=15)
        my_user = (me.json().get("username") or "").lower() if me.ok else ""

        posts = requests.get(
            f"{THREADS_API_BASE}/{uid}/threads",
            params={"fields": "id,text", "limit": 8, "access_token": tok},
            timeout=20,
        )
        if not posts.ok:
            return {"platform": "Threads", "status": "FAILED", "replied": [], "notes": f"Threads list ({posts.status_code}): {posts.text[:160]}"}

        for p in posts.json().get("data") or []:
            if len(replied) >= max_replies:
                break
            tid = str(p.get("id", ""))
            ctx = str(p.get("text") or "HabitSains Threads")
            reps = requests.get(
                f"{THREADS_API_BASE}/{tid}/replies",
                params={"fields": "id,text,username,has_replies", "access_token": tok},
                timeout=20,
            )
            if not reps.ok:
                if reps.status_code in (400, 403):
                    return {"platform": "Threads", "status": "NEEDS_SCOPE", "replied": replied, "notes": "Aktifkan izin threads_read_replies & threads_manage_replies di App Threads."}
                continue

            for c in reps.json().get("data") or []:
                if len(replied) >= max_replies:
                    break
                cid = str(c.get("id", ""))
                key = f"th:{cid}"
                if not cid or key in state["replied_ids"]:
                    continue
                user = str(c.get("username") or "")
                if my_user and user.lower() == my_user:
                    continue
                text = str(c.get("text") or "").strip()
                if is_spam_comment(text):
                    continue

                vote = detect_ab_vote(text)
                reply_txt = generate_human_reply(text, ctx, "Threads", config, vote=vote)
                if not dry_run:
                    cr = requests.post(
                        f"{THREADS_API_BASE}/{uid}/threads",
                        data={"media_type": "TEXT", "text": reply_txt[:500], "reply_to_id": cid, "access_token": tok},
                        timeout=20,
                    )
                    if not cr.ok:
                        continue
                    pub = requests.post(
                        f"{THREADS_API_BASE}/{uid}/threads_publish",
                        data={"creation_id": cr.json()["id"], "access_token": tok},
                        timeout=20,
                    )
                    if not pub.ok:
                        continue
                    state["replied_ids"][key] = datetime.now(timezone.utc).isoformat()
                    _record_vote(state, f"th:{tid}", vote)
                    time.sleep(1.5)
                replied.append({"author": f"@{user}" if user else "viewer", "comment": text, "reply": reply_txt, "vote": vote or ""})

        return {"platform": "Threads", "status": "OK", "replied": replied, "notes": f"{len(replied)} komentar dibalas."}
    except Exception as exc:
        return {"platform": "Threads", "status": "FAILED", "replied": replied, "notes": f"Threads error: {exc}"}


def _notify_telegram_replies(platform_results: list[dict[str, Any]], state: dict[str, Any], dry_run: bool) -> None:
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not tg_token or not tg_chat:
        return

    total_replied = sum(len(r.get("replied") or []) for r in platform_results)
    needs_attention = [r for r in platform_results if r.get("status") in ("NEEDS_SCOPE", "FAILED")]
    if total_replied == 0 and not needs_attention:
        return  # Stay quiet when there are zero new comments — zero notification spam!

    lines = [
        f"<b>💬 HabitSains Comment Bot {'(DRY-RUN)' if dry_run else ''}</b>",
        f"Total dibalas: <b>{total_replied}</b> komentar",
        "",
    ]
    for r in platform_results:
        reps = r.get("replied") or []
        if reps:
            lines.append(f"<b>{html.escape(r['platform'])} ({len(reps)}):</b>")
            for item in reps[:4]:
                v_badge = f" [Vote {item['vote']}]" if item.get("vote") else ""
                lines.append(
                    f"• <i>{html.escape(item['author'])}{v_badge}:</i> \"{html.escape(item['comment'][:70])}\"\n"
                    f"  ↳ {html.escape(item['reply'])}"
                )
        elif r.get("status") in ("NEEDS_SCOPE", "FAILED"):
            lines.append(f"⚠️ <b>{html.escape(r['platform'])}:</b> {html.escape(r.get('notes', ''))}")

    # Include top A/B vote tallies if any!
    tallies = [(k, v) for k, v in (state.get("vote_tally") or {}).items() if (v.get("A", 0) + v.get("B", 0)) > 0]
    if tallies:
        lines.append("\n<b>🗳 Skor Voting A vs B (Untuk Part 2):</b>")
        for k, v in tallies[-3:]:
            lines.append(f"• {html.escape(k)}: <b>A={v.get('A', 0)}</b> vs <b>B={v.get('B', 0)}</b>")

    try:
        requests.post(
            f"https://api.telegram.org/bot{tg_token}/sendMessage",
            json={"chat_id": tg_chat, "text": "\n".join(lines)[:4000], "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=15,
        )
    except Exception:
        pass


def run_comment_bot(dry_run: bool = False, max_per_platform: int = 6) -> dict[str, Any]:
    paths = get_project_paths()
    load_dotenv(paths.root / ".env", override=False)
    config = load_config(project_root=paths.root)
    state_file = paths.root / "output" / "replied_comments.json"
    state = _load_reply_state(state_file)

    bot_cfg = config.get("comment_bot", {})
    cap = int(bot_cfg.get("max_replies_per_platform_per_run", max_per_platform))

    results = [
        _process_youtube_comments(paths.root, config, state, max_replies=cap, dry_run=dry_run),
        _process_instagram_comments(config, state, max_replies=cap, dry_run=dry_run),
        _process_facebook_comments(config, state, max_replies=cap, dry_run=dry_run),
        _process_threads_comments(config, state, max_replies=cap, dry_run=dry_run),
    ]

    if not dry_run:
        _save_reply_state(state_file, state)
    _notify_telegram_replies(results, state, dry_run=dry_run)

    summary = {
        "dry_run": dry_run,
        "total_replied": sum(len(r.get("replied") or []) for r in results),
        "platforms": results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Multi-Platform Natural Human-Style Comment Auto-Reply Bot")
    parser.add_argument("--dry-run", action="store_true", help="Simulasi tanpa benar-benar mengirim balasan")
    parser.add_argument("--max-per-platform", type=int, default=6, help="Maksimal balasan per platform per run")
    args = parser.parse_args(argv)
    run_comment_bot(dry_run=args.dry_run, max_per_platform=args.max_per_platform)
    return 0


if __name__ == "__main__":
    sys.exit(main())
