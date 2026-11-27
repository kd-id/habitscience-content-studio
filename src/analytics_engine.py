"""Closed-Loop Multi-Platform Analytics, Sequel Ideator & Visual Style Optimizer.

Monitors live performance across ALL connected platforms:
  - YouTube (@HabitSains)     : views, likes, comments, Long vs Shorts, privacy/scheduled status (~3 API units!)
  - Instagram (@kha_zaki94)   : plays/views, reach, saves, likes, comments
  - Facebook Page (OST Anime) : video views, likes, comments
  - Meta Threads (@kha_zaki94): views, likes, replies

What it outputs (`output/analytics_insights.json`) & feeds back into the daily pipeline:
  1. Top most-watched videos across all platforms (so you immediately see winners!).
  2. Visual Style Leaderboard (`pov_3d_toon` v9 vs `cozy_diorama` v8.3 vs `minimal_line_story` v7
     vs `cinema_broll_html` v6) attributed directly via `output/history.json`.
  3. Ready-to-produce Part 2 / sequel follow-up topics extending your #1 most-watched videos
     (including live A/B vote results from `output/replied_comments.json`!).
  4. Epsilon-Greedy Visual Style Selector (80% best-performing style, 20% challenger style test
     to automatically discover & adopt whichever visual format gets the highest views!).
  5. Daily Performance & Growth Digest sent directly to Telegram (@Ars_Id_bot).

Usage:
  python -m src.analytics_engine            # Live pull, analyze, save insights & send Telegram digest
  python -m src.analytics_engine --no-notify
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from src.config_loader import get_project_paths, load_config, slugify
from src.publisher import _get_youtube_service
from src.social_publishers import META_GRAPH_BASE, THREADS_API_BASE, _resolve_fb_page_token


WIB = timezone(timedelta(hours=7))

CANDIDATE_SHORT_STYLES = [
    "islamic_luminous_sky",
    "islamic_gold_visualizer",
    "islamic_particle_map",
    "pov_3d_toon",
    "cozy_diorama",
    "minimal_line_story",
    "cinema_broll_html",
]
CANDIDATE_LONG_STYLES = [
    "islamic_luminous_sky",
    "islamic_gold_visualizer",
    "islamic_particle_map",
    "cozy_diorama",
    "minimal_line_story",
    "cinema_broll_html",
]


def _parse_iso_duration_sec(iso_dur: str) -> int:
    m = re.match(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$", iso_dur or "")
    if not m:
        return 0
    return int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + int(m.group(3) or 0)


def _engagement_score(views: int, likes: int, comments: int, saves: int = 0) -> float:
    """Weighted virality score rewarding both reach (views) and deep interaction (comments/saves)."""
    return round(float(views) + likes * 6.0 + comments * 18.0 + saves * 15.0, 2)


# ---------------------------------------------------------------------------
# 1. Live Multi-Platform Metric Fetchers (Zero Paid APIs, Minimal Quota!)
# ---------------------------------------------------------------------------

def _fetch_youtube_metrics(project_root: Path, max_videos: int = 25) -> tuple[list[dict[str, Any]], str]:
    service, err = _get_youtube_service(project_root)
    if not service:
        return [], err or "YouTube OAuth belum terhubung."

    try:
        ch = service.channels().list(part="contentDetails,statistics", mine=True).execute()
        items = ch.get("items") or []
        if not items:
            return [], "Channel YouTube tidak ditemukan."
        uploads_pl = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

        pl = service.playlistItems().list(part="contentDetails", playlistId=uploads_pl, maxResults=max_videos).execute()
        vid_ids = [it["contentDetails"]["videoId"] for it in (pl.get("items") or []) if (it.get("contentDetails") or {}).get("videoId")]
        if not vid_ids:
            return [], "Belum ada video di channel YouTube."

        v_resp = service.videos().list(
            part="snippet,statistics,contentDetails,status",
            id=",".join(vid_ids[:50]),
        ).execute()

        rows: list[dict[str, Any]] = []
        for v in v_resp.get("items") or []:
            sn = v.get("snippet") or {}
            st = v.get("statistics") or {}
            cd = v.get("contentDetails") or {}
            stat = v.get("status") or {}
            dur = _parse_iso_duration_sec(cd.get("duration", ""))
            is_short = dur <= 62 or "#shorts" in str(sn.get("title", "")).lower()
            views = int(st.get("viewCount") or 0)
            likes = int(st.get("likeCount") or 0)
            comments = int(st.get("commentCount") or 0)
            privacy = str(stat.get("privacyStatus", "unknown"))
            publish_at = str(stat.get("publishAt", ""))
            rows.append({
                "platform": "YouTube Shorts" if is_short else "YouTube Long",
                "format": "short" if is_short else "long",
                "id": v["id"],
                "title": str(sn.get("title", "")),
                "url": f"https://youtu.be/{v['id']}" if privacy == "public" else f"https://studio.youtube.com/video/{v['id']}/edit",
                "privacy": "scheduled" if (privacy == "private" and publish_at) else privacy,
                "publish_at": publish_at,
                "published_at": str(sn.get("publishedAt", "")),
                "views": views,
                "likes": likes,
                "comments": comments,
                "saves": 0,
                "score": _engagement_score(views, likes, comments),
            })
        return rows, "OK"
    except Exception as exc:
        return [], f"YouTube analytics error: {exc}"


def _fetch_instagram_metrics(limit: int = 15) -> tuple[list[dict[str, Any]], str]:
    tok = os.getenv("META_ACCESS_TOKEN", "").strip()
    ig_id = os.getenv("IG_BUSINESS_ACCOUNT_ID", "").strip()
    if not tok or not ig_id:
        return [], "META_ACCESS_TOKEN / IG_BUSINESS_ACCOUNT_ID belum diset."
    try:
        med = requests.get(
            f"{META_GRAPH_BASE}/{ig_id}/media",
            params={"fields": "id,caption,media_type,permalink,like_count,comments_count,timestamp", "limit": limit, "access_token": tok},
            timeout=20,
        )
        if not med.ok:
            return [], f"IG media fetch HTTP {med.status_code}"

        rows: list[dict[str, Any]] = []
        for m in med.json().get("data") or []:
            mid = str(m.get("id", ""))
            mtype = str(m.get("media_type", "IMAGE")).upper()
            likes = int(m.get("like_count") or 0)
            comments = int(m.get("comments_count") or 0)
            views, saves = 0, 0

            # Best-effort insights fetch (plays/views & saved)
            metrics_q = "views,reach,saved" if mtype in ("VIDEO", "REELS") else "reach,saved"
            ins = requests.get(
                f"{META_GRAPH_BASE}/{mid}/insights",
                params={"metric": metrics_q, "access_token": tok},
                timeout=15,
            )
            if not ins.ok and mtype in ("VIDEO", "REELS"):
                ins = requests.get(
                    f"{META_GRAPH_BASE}/{mid}/insights",
                    params={"metric": "plays,reach,saved", "access_token": tok},
                    timeout=15,
                )
            if ins.ok:
                for metric in ins.json().get("data") or []:
                    name = str(metric.get("name", ""))
                    vals = metric.get("values") or []
                    val = int(vals[0].get("value") or 0) if vals else 0
                    if name in ("views", "plays"):
                        views = max(views, val)
                    elif name == "reach" and views == 0:
                        views = val
                    elif name == "saved":
                        saves = val

            cap = str(m.get("caption") or "Instagram Post").splitlines()[0][:85]
            rows.append({
                "platform": "Instagram Reels" if mtype in ("VIDEO", "REELS") else "Instagram Carousel",
                "format": "short" if mtype in ("VIDEO", "REELS") else "carousel",
                "id": mid,
                "title": cap,
                "url": str(m.get("permalink", "")),
                "privacy": "public",
                "publish_at": "",
                "published_at": str(m.get("timestamp", "")),
                "views": views,
                "likes": likes,
                "comments": comments,
                "saves": saves,
                "score": _engagement_score(views, likes, comments, saves),
            })
        return rows, "OK"
    except Exception as exc:
        return [], f"IG analytics error: {exc}"


def _fetch_facebook_metrics(limit: int = 12) -> tuple[list[dict[str, Any]], str]:
    tok = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip() or os.getenv("META_ACCESS_TOKEN", "").strip()
    fb_id = os.getenv("FB_PAGE_ID", "").strip()
    if not tok or not fb_id:
        return [], "FB_PAGE_ID belum diset."
    try:
        page_tok = _resolve_fb_page_token(tok, fb_id)
        resp = requests.get(
            f"{META_GRAPH_BASE}/{fb_id}/videos",
            params={"fields": "id,title,description,views,permalink_url,created_time,likes.summary(true),comments.summary(true)", "limit": limit, "access_token": page_tok},
            timeout=20,
        )
        if not resp.ok:
            return [], f"FB videos HTTP {resp.status_code}"
        rows: list[dict[str, Any]] = []
        for v in resp.json().get("data") or []:
            views = int(v.get("views") or 0)
            likes = int(((v.get("likes") or {}).get("summary") or {}).get("total_count") or 0)
            comments = int(((v.get("comments") or {}).get("summary") or {}).get("total_count") or 0)
            title = str(v.get("title") or v.get("description") or "Facebook Reel").splitlines()[0][:85]
            purl = str(v.get("permalink_url") or "")
            if purl.startswith("/"):
                purl = f"https://www.facebook.com{purl}"
            rows.append({
                "platform": "Facebook Page Reels",
                "format": "short",
                "id": str(v.get("id", "")),
                "title": title,
                "url": purl,
                "privacy": "public",
                "publish_at": "",
                "published_at": str(v.get("created_time", "")),
                "views": views,
                "likes": likes,
                "comments": comments,
                "saves": 0,
                "score": _engagement_score(views, likes, comments),
            })
        return rows, "OK"
    except Exception as exc:
        return [], f"FB analytics error: {exc}"


def _fetch_threads_metrics(limit: int = 12) -> tuple[list[dict[str, Any]], str]:
    tok = os.getenv("THREADS_ACCESS_TOKEN", "").strip()
    uid = os.getenv("THREADS_USER_ID", "").strip()
    if not tok or not uid:
        return [], "THREADS_ACCESS_TOKEN belum diset."
    try:
        resp = requests.get(
            f"{THREADS_API_BASE}/{uid}/threads",
            params={"fields": "id,text,permalink,timestamp", "limit": limit, "access_token": tok},
            timeout=20,
        )
        if not resp.ok:
            return [], f"Threads list HTTP {resp.status_code}"
        rows: list[dict[str, Any]] = []
        for p in resp.json().get("data") or []:
            tid = str(p.get("id", ""))
            views, likes, replies = 0, 0, 0
            ins = requests.get(
                f"{THREADS_API_BASE}/{tid}/insights",
                params={"metric": "views,likes,replies", "access_token": tok},
                timeout=15,
            )
            if ins.ok:
                for m in ins.json().get("data") or []:
                    nm = str(m.get("name", ""))
                    vals = m.get("values") or []
                    v = int(vals[0].get("value") or 0) if vals else 0
                    if nm == "views":
                        views = v
                    elif nm == "likes":
                        likes = v
                    elif nm == "replies":
                        replies = v
            rows.append({
                "platform": "Threads",
                "format": "text",
                "id": tid,
                "title": str(p.get("text") or "Threads Post").splitlines()[0][:85],
                "url": str(p.get("permalink", "")),
                "privacy": "public",
                "publish_at": "",
                "published_at": str(p.get("timestamp", "")),
                "views": views,
                "likes": likes,
                "comments": replies,
                "saves": 0,
                "score": _engagement_score(views, likes, replies),
            })
        return rows, "OK"
    except Exception as exc:
        return [], f"Threads analytics error: {exc}"


def _fetch_account_growth_stats(project_root: Path) -> dict[str, int]:
    """Fetch lightweight channel/account follower & subscriber counters across YouTube, IG & FB."""
    stats: dict[str, int] = {
        "yt_subscribers": 0,
        "yt_channel_views": 0,
        "ig_followers": 0,
        "fb_followers": 0,
    }
    try:
        service, _ = _get_youtube_service(project_root)
        if service:
            ch = service.channels().list(part="statistics", mine=True).execute()
            items = ch.get("items") or []
            if items:
                st = items[0].get("statistics") or {}
                stats["yt_subscribers"] = int(st.get("subscriberCount") or 0)
                stats["yt_channel_views"] = int(st.get("viewCount") or 0)
    except Exception:
        pass

    meta_tok = os.getenv("META_ACCESS_TOKEN", "").strip()
    ig_id = os.getenv("IG_BUSINESS_ACCOUNT_ID", "").strip()
    if meta_tok and ig_id:
        try:
            r = requests.get(
                f"{META_GRAPH_BASE}/{ig_id}",
                params={"fields": "followers_count", "access_token": meta_tok},
                timeout=15,
            )
            if r.ok:
                stats["ig_followers"] = int(r.json().get("followers_count") or 0)
        except Exception:
            pass

    fb_tok = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip() or meta_tok
    fb_id = os.getenv("FB_PAGE_ID", "").strip()
    if fb_tok and fb_id:
        try:
            ptok = _resolve_fb_page_token(fb_tok, fb_id)
            r = requests.get(
                f"{META_GRAPH_BASE}/{fb_id}",
                params={"fields": "followers_count,fan_count", "access_token": ptok},
                timeout=15,
            )
            if r.ok:
                d = r.json()
                stats["fb_followers"] = int(d.get("followers_count") or d.get("fan_count") or 0)
        except Exception:
            pass

    return stats


def compute_pillar_leaderboard(videos: list[dict[str, Any]], history: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Attribute live public video views back to the 3 rotating content pillars."""
    id_to_pillar: dict[str, str] = {}
    for rec in history:
        pil = str(rec.get("pillar_label") or rec.get("pillar") or "").strip()
        if not pil:
            continue
        for eid in (rec.get("external_ids") or {}).values():
            if not eid:
                continue
            clean_id = str(eid).split(":", 1)[-1] if ":" in str(eid) else str(eid)
            id_to_pillar[str(eid)] = pil
            id_to_pillar[clean_id] = pil

    buckets: dict[str, list[dict[str, Any]]] = {}
    for v in videos:
        if v.get("privacy") != "public":
            continue
        pil = id_to_pillar.get(str(v.get("id", "")))
        if not pil:
            continue
        v["pillar"] = pil
        buckets.setdefault(pil, []).append(v)

    board: dict[str, dict[str, Any]] = {}
    for pil, items in buckets.items():
        cnt = len(items)
        board[pil] = {
            "videos": cnt,
            "total_views": sum(x["views"] for x in items),
            "avg_views": round(sum(x["views"] for x in items) / cnt, 1),
            "avg_score": round(sum(x["score"] for x in items) / cnt, 1),
        }
    return board


def compute_growth_deltas(
    prev_insights: dict[str, Any],
    studio_public_rows: list[dict[str, Any]],
    account_stats: dict[str, int],
) -> dict[str, Any]:
    """Compare current views & audience counters against the previous snapshot to detect rising videos."""
    prev_views_map = prev_insights.get("video_views_snapshot") or {}
    prev_acct = prev_insights.get("account_stats") or {}
    has_prev = bool(prev_insights.get("updated_at_wib"))

    rising: list[dict[str, Any]] = []
    cur_views_map: dict[str, int] = {}
    for v in studio_public_rows:
        vid = str(v.get("id", ""))
        cur_v = int(v.get("views") or 0)
        cur_views_map[vid] = cur_v
        if has_prev and vid:
            prev_v = int(prev_views_map.get(vid, 0))
            dv = cur_v - prev_v
            if dv > 0:
                rising.append({
                    "id": vid,
                    "title": str(v.get("title", "")),
                    "platform": str(v.get("platform", "")),
                    "url": str(v.get("url", "")),
                    "views": cur_v,
                    "delta_views": dv,
                    "likes": int(v.get("likes") or 0),
                    "comments": int(v.get("comments") or 0),
                })

    rising.sort(key=lambda x: (x["delta_views"], x["views"]), reverse=True)
    cur_total_views = sum(cur_views_map.values())
    prev_total_views = int(prev_insights.get("total_views_all_platforms", cur_total_views)) if has_prev else cur_total_views

    def _d(key: str) -> int:
        if not has_prev or key not in prev_acct:
            return 0
        return int(account_stats.get(key, 0)) - int(prev_acct.get(key, 0))

    return {
        "has_previous_snapshot": has_prev,
        "delta_total_views": cur_total_views - prev_total_views,
        "delta_yt_subs": _d("yt_subscribers"),
        "delta_ig_followers": _d("ig_followers"),
        "delta_fb_followers": _d("fb_followers"),
        "rising_videos": rising[:5],
        "video_views_snapshot": cur_views_map,
    }


# ---------------------------------------------------------------------------
# 2. Visual Style Attribution, Leaderboard & Epsilon-Greedy Optimizer
# ---------------------------------------------------------------------------

def compute_style_leaderboard(videos: list[dict[str, Any]], history: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Attribute live video views/engagement back to the exact visual style recorded in history.json."""
    id_to_style: dict[str, tuple[str, str]] = {}  # ext_id -> (format, style)
    for rec in history:
        ext = rec.get("external_ids") or {}
        st_long = str(rec.get("visual_style_long") or "")
        st_short = str(rec.get("visual_style_short") or "")
        for plat_name, ext_id in ext.items():
            if not ext_id:
                continue
            low_p = plat_name.lower()
            if "long" in low_p and st_long:
                id_to_style[str(ext_id)] = ("long", st_long)
            elif any(k in low_p for k in ("short", "reel", "facebook", "tiktok")) and st_short:
                id_to_style[str(ext_id)] = ("short", st_short)

    buckets: dict[str, dict[str, list[dict[str, Any]]]] = {"short": {}, "long": {}}
    for v in videos:
        if v.get("privacy") != "public":
            continue
        vid_id = str(v.get("id", ""))
        matched = id_to_style.get(vid_id)
        if not matched:
            continue
        fmt, style = matched
        v["visual_style"] = style
        buckets[fmt].setdefault(style, []).append(v)

    board: dict[str, dict[str, Any]] = {"short": {}, "long": {}}
    for fmt in ("short", "long"):
        for style, items in buckets[fmt].items():
            cnt = len(items)
            avg_views = round(sum(x["views"] for x in items) / cnt, 1)
            avg_score = round(sum(x["score"] for x in items) / cnt, 1)
            board[fmt][style] = {
                "videos": cnt,
                "total_views": sum(x["views"] for x in items),
                "avg_views": avg_views,
                "avg_score": avg_score,
            }
    return board


def choose_next_visual_styles(
    insights_file: Path,
    history_count: int,
    config: dict[str, Any],
) -> tuple[str, str, str]:
    """Select (long_style, short_style, reason) using Epsilon-Greedy exploitation + exploration.

    - 80% of runs (Exploit): uses the highest-performing proven visual style from real view analytics
      (defaults to `cozy_diorama` for 16:9 Long and `pov_3d_toon` for 9:16 Shorts).
    - 20% of runs (Explore — every Nth run): automatically experiments with a challenger visual style
      (e.g. `minimal_line_story` v7 or `cinema_broll_html` v6) so the channel continuously tests
      viral formats and shifts automatically to whichever gets more views!
    """
    vid_cfg = config.get("video", {})
    explore_every = max(int(vid_cfg.get("style_explore_every_n_runs", 5)), 3)

    best_long = "cozy_diorama"
    best_short = "pov_3d_toon"
    board: dict[str, dict[str, Any]] = {}

    if insights_file.exists():
        try:
            ins = json.loads(insights_file.read_text(encoding="utf-8"))
            board = ins.get("style_leaderboard") or {}
            # Crown a data-backed winner only when it has >= 2 published videos & > 0 views
            s_ranked = [
                (st, m) for st, m in (board.get("short") or {}).items()
                if m.get("videos", 0) >= 2 and m.get("total_views", 0) > 0
            ]
            if s_ranked:
                s_ranked.sort(key=lambda x: (x[1]["avg_score"], x[1]["avg_views"]), reverse=True)
                best_short = s_ranked[0][0]

            l_ranked = [
                (st, m) for st, m in (board.get("long") or {}).items()
                if m.get("videos", 0) >= 2 and m.get("total_views", 0) > 0
            ]
            if l_ranked:
                l_ranked.sort(key=lambda x: (x[1]["avg_score"], x[1]["avg_views"]), reverse=True)
                best_long = l_ranked[0][0]
        except (json.JSONDecodeError, OSError):
            pass

    # Every Nth run, test a challenger Shorts visual style (and Long challenger half as often)
    if history_count > 0 and (history_count % explore_every == 0):
        challengers_short = [s for s in CANDIDATE_SHORT_STYLES if s != best_short]
        pick_idx = (history_count // explore_every) % len(challengers_short)
        test_short = challengers_short[pick_idx]
        return best_long, test_short, f"explore_challenger_short:{test_short}"

    return best_long, best_short, f"exploit_best(long={best_long},short={best_short})"


# ---------------------------------------------------------------------------
# 3. Gemini AI Sequel & Winning-Pattern Strategist
# ---------------------------------------------------------------------------

def _generate_sequel_insights_with_gemini(
    top_videos: list[dict[str, Any]],
    vote_tally: dict[str, Any],
    style_board: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Analyze top performing videos + A/B votes to propose Part 2 sequels & winning hooks."""
    default_out = {
        "winning_patterns": [
            "Specific time-based morning/afternoon dopamine traps (e.g. 7 AM, 2 PM crash)",
            "Concrete brain metrics (-40% focus, 23-minute attention residue)",
            "Interactive A/B survival choice cliffhangers driving Part 2 anticipation",
        ],
        "recommended_sequels": [],
    }
    if not top_videos:
        return default_out

    # Deterministic fallback sequels from the #1 and #2 most-watched videos
    fallback_sequels: list[dict[str, Any]] = []
    for v in top_videos[:2]:
        base_title = re.sub(r"\s*#Shorts\b", "", str(v.get("title", "")), flags=re.IGNORECASE).strip()
        if base_title:
            fallback_sequels.append({
                "topic": f"Part 2: {base_title[:58]} — What Happens Next in Your Brain",
                "angle": f"Direct sequel expanding on our top-performing video ({v.get('views', 0)} views on {v.get('platform')}) with deeper neuroscience + 3-step fix",
                "hook": f"Everyone loved our breakdown on {base_title[:45]}—here is Part 2 showing what happens inside your brain next.",
                "source_video_id": v.get("id", ""),
                "source_views": v.get("views", 0),
                "keywords": [w for w in slugify(base_title).split("-") if len(w) > 2][:5] + ["part 2", "neuroscience"],
            })
    default_out["recommended_sequels"] = fallback_sequels

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return default_out

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        model = config.get("ai", {}).get("text_model", "gemini-3.8-flash")
        prompt = f"""You are a YouTube & Short-Form Viral Growth Strategist for @HabitSains (English science-backed focus, dopamine, habits & neuroscience channel).

Here are the channel's TOP PERFORMING published videos right now:
{json.dumps(top_videos[:6], ensure_ascii=False, indent=2)}

Audience A/B interactive vote tallies (if any):
{json.dumps(vote_tally, ensure_ascii=False)}

Visual style leaderboard:
{json.dumps(style_board, ensure_ascii=False)}

Task:
1. Extract 3 concise `winning_patterns` explaining WHY the top videos got the most views/engagement.
2. Propose 3 high-CTR `recommended_sequels` (Part 2 / deeper follow-ups / viral spin-offs directly building on the #1–#2 most-watched topics and any winning A/B vote!). Every topic MUST be in vivid natural English.

Return ONLY valid JSON:
{{
  "winning_patterns": ["pattern 1", "pattern 2", "pattern 3"],
  "recommended_sequels": [
    {{
      "topic": "Specific Part 2 / sequel title (max 70 chars)",
      "angle": "Why viewers of the winning video will click immediately",
      "hook": "1-sentence 3-second viral opening hook",
      "keywords": ["kw1", "kw2", "kw3", "kw4"]
    }}
  ]
}}"""
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.7, response_mime_type="application/json"),
        )
        parsed = json.loads((resp.text or "").strip())
        if isinstance(parsed.get("recommended_sequels"), list) and parsed["recommended_sequels"]:
            return {
                "winning_patterns": [str(x) for x in (parsed.get("winning_patterns") or default_out["winning_patterns"])][:4],
                "recommended_sequels": parsed["recommended_sequels"][:3],
            }
    except Exception:
        pass
    return default_out


# ---------------------------------------------------------------------------
# 4. Telegram Daily Performance & Style Digest
# ---------------------------------------------------------------------------

def _fmt_delta(val: int) -> str:
    if val > 0:
        return f" (+{val:,})"
    if val < 0:
        return f" ({val:,})"
    return ""


def _send_telegram_analytics_digest(insights: dict[str, Any]) -> bool:
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not tg_token or not tg_chat:
        return False

    top_pub = insights.get("top_videos") or []
    rising = insights.get("rising_videos") or []
    drafts_cnt = int(insights.get("scheduled_or_draft_count", 0))
    pub_cnt = int(insights.get("public_video_count", 0))
    total_views = int(insights.get("total_views_all_platforms", 0))
    growth = insights.get("growth_deltas") or {}
    acct = insights.get("account_stats") or {}
    board_short = (insights.get("style_leaderboard") or {}).get("short") or {}
    pillar_board = insights.get("pillar_leaderboard") or {}
    sequels = insights.get("recommended_sequels") or []
    next_plan = insights.get("next_style_plan") or {}
    interaction = insights.get("interaction_summary") or {}
    sys_health = insights.get("system_health") or {}

    dv_txt = _fmt_delta(int(growth.get("delta_total_views", 0)))
    lines = [
        "<b>📈 HabitSains — Laporan Perkembangan Channel</b>",
        (
            f"👁 Total Views Konten: <b>{total_views:,}{dv_txt}</b>\n"
            f"📺 Publik: <b>{pub_cnt}</b> | 🗓 Antrean/Draft: <b>{drafts_cnt}</b> | 🎬 Total Episode: <b>{int(sys_health.get('total_episodes', 0))}</b>"
        ),
        (
            f"👥 <b>Audiens:</b> "
            f"YT Subs <b>{int(acct.get('yt_subscribers', 0)):,}{_fmt_delta(int(growth.get('delta_yt_subs', 0)))}</b> • "
            f"IG <b>{int(acct.get('ig_followers', 0)):,}{_fmt_delta(int(growth.get('delta_ig_followers', 0)))}</b> • "
            f"FB <b>{int(acct.get('fb_followers', 0)):,}{_fmt_delta(int(growth.get('delta_fb_followers', 0)))}</b>"
        ),
        "",
    ]

    if rising:
        lines.append("<b>🚀 Video Sedang Naik Daun (Penonton Baru!):</b>")
        for r in rising[:3]:
            t = html.escape(str(r.get("title", ""))[:56])
            plat = html.escape(str(r.get("platform", "")))
            url = str(r.get("url", ""))
            link = f'<a href="{html.escape(url)}">{t}</a>' if url else t
            lines.append(
                f"• {link}\n"
                f"   <i>{plat} • 🔥 <b>+{int(r.get('delta_views', 0)):,} views baru</b> (Total {int(r.get('views', 0)):,} • 👍 {r.get('likes', 0)} • 💬 {r.get('comments', 0)})</i>"
            )
        lines.append("")

    if top_pub:
        lines.append("<b>🏆 Top Video Paling Banyak Ditonton:</b>")
        for idx, v in enumerate(top_pub[:4], start=1):
            t = html.escape(str(v.get("title", ""))[:58])
            plat = html.escape(str(v.get("platform", "")))
            st_tag = f" [{v['visual_style']}]" if v.get("visual_style") else ""
            url = str(v.get("url", ""))
            link = f'<a href="{html.escape(url)}">{t}</a>' if url else t
            saves_txt = f" • 🔖 {v.get('saves', 0)}" if v.get("saves") else ""
            lines.append(
                f"{idx}. {link}\n"
                f"   <i>{plat}{html.escape(st_tag)} • 👁 {v.get('views', 0):,} • 👍 {v.get('likes', 0)} • 💬 {v.get('comments', 0)}{saves_txt}</i>"
            )
    else:
        lines.append("<i>Belum ada video publik dengan views (video baru masih di antrean jadwal — data views akan masuk otomatis begitu tayang!).</i>")

    if pillar_board:
        lines.append("\n<b>🧭 Performa Pillar Topik:</b>")
        for pil_name, m in sorted(pillar_board.items(), key=lambda x: x[1].get("avg_score", 0), reverse=True):
            lines.append(f"• {html.escape(pil_name)}: rata-rata <b>{m['avg_views']}</b> views ({m['videos']} konten)")

    if board_short:
        lines.append("\n<b>🎨 Performa Gaya Visual (9:16):</b>")
        for st_name, m in sorted(board_short.items(), key=lambda x: x[1].get("avg_score", 0), reverse=True):
            lines.append(f"• <code>{html.escape(st_name)}</code>: rata-rata <b>{m['avg_views']}</b> views ({m['videos']} video)")

    total_replied = int(interaction.get("total_comments_replied", 0))
    vote_summary = interaction.get("top_votes") or []
    if total_replied > 0 or vote_summary:
        lines.append(f"\n<b>💬 Interaksi &amp; Vote Penonton:</b> Bot membalas <b>{total_replied}</b> komentar")
        for vs in vote_summary[:2]:
            lines.append(f"• {html.escape(str(vs))}")

    if next_plan:
        lines.append(
            f"\n🧪 <b>Strategi Episode Berikutnya:</b> Long=<code>{html.escape(str(next_plan.get('long_style', 'cozy_diorama')))}</code> | "
            f"Shorts=<code>{html.escape(str(next_plan.get('short_style', 'pov_3d_toon')))}</code>"
        )

    if sequels:
        lines.append("\n<b>🔥 Ide Lanjutan Part 2 (Dari Video Teramai):</b>")
        for s in sequels[:2]:
            lines.append(f"• {html.escape(str(s.get('topic', ''))[:80])}")

    next_yt = str(sys_health.get("next_youtube_date") or "")
    p_errs = [f"{k}: {v}" for k, v in (insights.get("platform_status") or {}).items() if v != "OK"]
    footer_bits: list[str] = []
    if next_yt:
        footer_bits.append(f"🗓 Slot YT berikut: <code>{html.escape(next_yt)}</code>")
    if p_errs:
        footer_bits.append(f"⚠️ Cek API: {html.escape('; '.join(p_errs[:2]))}")
    else:
        footer_bits.append("✅ Koneksi 4 Platform: Normal")
    if footer_bits:
        lines.append("\n" + " | ".join(footer_bits))

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{tg_token}/sendMessage",
            json={"chat_id": tg_chat, "text": "\n".join(lines)[:4000], "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=15,
        )
        return 200 <= resp.status_code < 300
    except Exception:
        return False


def run_analytics_optimizer(notify_telegram: bool = True) -> dict[str, Any]:
    paths = get_project_paths()
    load_dotenv(paths.root / ".env", override=False)
    config = load_config(project_root=paths.root)

    history: list[dict[str, Any]] = []
    if paths.history_file.exists():
        try:
            history = json.loads(paths.history_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            history = []

    vote_tally: dict[str, Any] = {}
    total_replied_comments = 0
    rep_file = paths.root / "output" / "replied_comments.json"
    if rep_file.exists():
        try:
            rep_data = json.loads(rep_file.read_text(encoding="utf-8"))
            vote_tally = rep_data.get("vote_tally") or {}
            total_replied_comments = len(rep_data.get("replied_ids") or {})
        except (json.JSONDecodeError, OSError):
            vote_tally = {}

    insights_file = paths.root / "output" / "analytics_insights.json"
    prev_insights: dict[str, Any] = {}
    if insights_file.exists():
        try:
            prev_insights = json.loads(insights_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            prev_insights = {}

    next_yt_date = ""
    sched_file = paths.root / "output" / "schedule_state.json"
    if sched_file.exists():
        try:
            next_yt_date = str(json.loads(sched_file.read_text(encoding="utf-8")).get("next_youtube_date", ""))
        except (json.JSONDecodeError, OSError):
            next_yt_date = ""

    account_stats = _fetch_account_growth_stats(paths.root)
    yt_rows, yt_st = _fetch_youtube_metrics(paths.root)
    ig_rows, ig_st = _fetch_instagram_metrics()
    fb_rows, fb_st = _fetch_facebook_metrics()
    th_rows, th_st = _fetch_threads_metrics()

    all_rows = yt_rows + ig_rows + fb_rows + th_rows
    # Identify videos belonging strictly to HabitSains / this automation studio (so unrelated old posts on
    # shared FB/IG accounts never trigger off-niche Part 2 sequels!)
    known_studio_ids: set[str] = set()
    for rec in history:
        for eid in (rec.get("external_ids") or {}).values():
            if not eid:
                continue
            s_eid = str(eid)
            known_studio_ids.add(s_eid)
            if ":" in s_eid:
                known_studio_ids.add(s_eid.split(":", 1)[-1])
    for r in all_rows:
        r["is_studio_video"] = (
            str(r.get("id", "")) in known_studio_ids
            or r.get("platform") in ("YouTube Long", "YouTube Shorts")
            or "habitsains" in str(r.get("title", "")).lower()
            or "habitscience" in str(r.get("title", "")).lower()
        )

    public_rows = [r for r in all_rows if r.get("privacy") == "public"]
    studio_public_rows = [r for r in public_rows if r.get("is_studio_video")]
    draft_or_sched = [r for r in all_rows if r.get("privacy") != "public"]

    style_board = compute_style_leaderboard(all_rows, history)
    pillar_board = compute_pillar_leaderboard(studio_public_rows, history)
    growth = compute_growth_deltas(prev_insights, studio_public_rows, account_stats)
    top_videos = sorted(studio_public_rows, key=lambda r: (r["score"], r["views"]), reverse=True)[:10]
    ai_insights = _generate_sequel_insights_with_gemini(top_videos, vote_tally, style_board, config)

    top_vote_lines: list[str] = []
    for k, v in list(vote_tally.items())[:3]:
        if isinstance(v, dict):
            top_vote_lines.append(f"{k[:40]}: A={v.get('A', 0)} vs B={v.get('B', 0)}")

    # Pre-save style_leaderboard so choose_next_visual_styles sees fresh leaderboard
    prelim = {
        "updated_at_wib": datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S WIB"),
        "platform_status": {"youtube": yt_st, "instagram": ig_st, "facebook": fb_st, "threads": th_st},
        "account_stats": account_stats,
        "growth_deltas": {
            "has_previous_snapshot": growth["has_previous_snapshot"],
            "delta_total_views": growth["delta_total_views"],
            "delta_yt_subs": growth["delta_yt_subs"],
            "delta_ig_followers": growth["delta_ig_followers"],
            "delta_fb_followers": growth["delta_fb_followers"],
        },
        "rising_videos": growth["rising_videos"],
        "video_views_snapshot": growth["video_views_snapshot"],
        "public_video_count": len(studio_public_rows),
        "scheduled_or_draft_count": len(draft_or_sched),
        "total_views_all_platforms": sum(r["views"] for r in studio_public_rows),
        "top_videos": top_videos,
        "scheduled_queue": draft_or_sched[:10],
        "style_leaderboard": style_board,
        "pillar_leaderboard": pillar_board,
        "interaction_summary": {
            "total_comments_replied": total_replied_comments,
            "top_votes": top_vote_lines,
        },
        "system_health": {
            "total_episodes": len(history),
            "next_youtube_date": next_yt_date,
        },
        "winning_patterns": ai_insights["winning_patterns"],
        "recommended_sequels": ai_insights["recommended_sequels"],
        "vote_tally": vote_tally,
    }
    insights_file.parent.mkdir(parents=True, exist_ok=True)
    insights_file.write_text(json.dumps(prelim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    next_l, next_s, reason = choose_next_visual_styles(insights_file, len(history), config)
    prelim["next_style_plan"] = {"long_style": next_l, "short_style": next_s, "reason": reason}
    insights_file.write_text(json.dumps(prelim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if notify_telegram:
        prelim["telegram_sent"] = _send_telegram_analytics_digest(prelim)

    print(json.dumps({
        "updated_at_wib": prelim["updated_at_wib"],
        "platform_status": prelim["platform_status"],
        "public_video_count": prelim["public_video_count"],
        "scheduled_or_draft_count": prelim["scheduled_or_draft_count"],
        "total_views_all_platforms": prelim["total_views_all_platforms"],
        "top_3": [{"platform": v["platform"], "title": v["title"][:50], "views": v["views"]} for v in top_videos[:3]],
        "next_style_plan": prelim["next_style_plan"],
        "recommended_sequels": [s.get("topic") for s in prelim["recommended_sequels"]],
    }, ensure_ascii=False, indent=2))
    return prelim


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Multi-Platform Analytics, Sequel Planner & Visual Style Optimizer")
    parser.add_argument("--no-notify", action="store_true", help="Lewati pengiriman laporan ke Telegram")
    args = parser.parse_args(argv)
    run_analytics_optimizer(notify_telegram=not args.no_notify)
    return 0


if __name__ == "__main__":
    sys.exit(main())
