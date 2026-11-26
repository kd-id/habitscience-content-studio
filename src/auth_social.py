"""Interactive Free Direct Social API Connection Checker & Token Helper.

Usage:
  python -m src.auth_social --check              # Verify ALL configured Direct API tokens
  python -m src.auth_social --discover-meta      # Auto-find FB_PAGE_ID & IG_BUSINESS_ACCOUNT_ID from META_ACCESS_TOKEN
  python -m src.auth_social --exchange-meta      # Exchange short-lived META_ACCESS_TOKEN into a 60-day token
  python -m src.auth_social --discover-linkedin  # Auto-find LINKEDIN_AUTHOR_URN from LINKEDIN_ACCESS_TOKEN
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

from src.social_publishers import META_GRAPH_BASE, THREADS_API_BASE, _resolve_tiktok_access_token


def check_all_connections(project_root: Path) -> dict[str, str]:
    load_dotenv(project_root / ".env")
    report: dict[str, str] = {}

    # 1. YouTube
    yt_tok = os.getenv("YOUTUBE_TOKEN_JSON", "").strip()
    yt_file = project_root / os.getenv("YOUTUBE_TOKEN_FILE", "config/youtube_token.json")
    report["YouTube (Long & Shorts)"] = "CONNECTED" if (yt_tok or yt_file.exists()) else "NOT_SET"

    # 2. Meta (Instagram + Facebook)
    meta_tok = os.getenv("META_ACCESS_TOKEN", "").strip()
    ig_id = os.getenv("IG_BUSINESS_ACCOUNT_ID", "").strip()
    fb_id = os.getenv("FB_PAGE_ID", "").strip()
    if meta_tok:
        try:
            r = requests.get(f"{META_GRAPH_BASE}/me", params={"fields": "id,name", "access_token": meta_tok}, timeout=15)
            if r.ok:
                me = r.json()
                report["Instagram (Reels & Carousel)"] = f"CONNECTED (user={me.get('name')}, ig_id={ig_id or 'MISSING'})"
                report["Facebook Page Reels"] = f"CONNECTED (page_id={fb_id or 'MISSING'})"
            else:
                report["Instagram (Reels & Carousel)"] = f"TOKEN_ERROR ({r.status_code})"
                report["Facebook Page Reels"] = f"TOKEN_ERROR ({r.status_code})"
        except Exception as exc:
            report["Instagram (Reels & Carousel)"] = f"ERROR ({exc})"
            report["Facebook Page Reels"] = f"ERROR ({exc})"
    else:
        report["Instagram (Reels & Carousel)"] = "NOT_SET (META_ACCESS_TOKEN + IG_BUSINESS_ACCOUNT_ID)"
        report["Facebook Page Reels"] = "NOT_SET (META_ACCESS_TOKEN + FB_PAGE_ID)"

    # 3. TikTok
    tt_tok, tt_err = _resolve_tiktok_access_token()
    report["TikTok (Inbox Drafts)"] = "CONNECTED" if tt_tok else f"NOT_SET ({tt_err})"

    # 4. LinkedIn
    li_tok = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
    li_urn = os.getenv("LINKEDIN_AUTHOR_URN", "").strip()
    if li_tok:
        try:
            r = requests.get("https://api.linkedin.com/v2/userinfo", headers={"Authorization": f"Bearer {li_tok}"}, timeout=15)
            if r.ok:
                sub = r.json().get("sub", "")
                report["LinkedIn"] = f"CONNECTED (urn={li_urn or f'urn:li:person:{sub}'})"
            else:
                report["LinkedIn"] = f"TOKEN_ERROR ({r.status_code})"
        except Exception as exc:
            report["LinkedIn"] = f"ERROR ({exc})"
    else:
        report["LinkedIn"] = "NOT_SET (LINKEDIN_ACCESS_TOKEN + LINKEDIN_AUTHOR_URN)"

    # 5. Threads
    th_tok = os.getenv("THREADS_ACCESS_TOKEN", "").strip()
    th_uid = os.getenv("THREADS_USER_ID", "").strip()
    if th_tok and th_uid:
        try:
            r = requests.get(f"{THREADS_API_BASE}/{th_uid}", params={"fields": "id,username", "access_token": th_tok}, timeout=15)
            report["Meta Threads"] = f"CONNECTED (@{r.json().get('username')})" if r.ok else f"TOKEN_ERROR ({r.status_code})"
        except Exception as exc:
            report["Meta Threads"] = f"ERROR ({exc})"
    else:
        report["Meta Threads"] = "NOT_SET (THREADS_ACCESS_TOKEN + THREADS_USER_ID)"

    # 6. X (Twitter)
    has_x = all(os.getenv(k, "").strip() for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"))
    report["X (Twitter v2)"] = "CONFIGURED (OAuth 1.0a keys present)" if has_x else "NOT_SET (X_API_KEY..X_ACCESS_SECRET)"

    return report


def discover_meta_ids(project_root: Path) -> None:
    load_dotenv(project_root / ".env")
    tok = os.getenv("META_ACCESS_TOKEN", "").strip()
    if not tok:
        raise SystemExit("Set META_ACCESS_TOKEN di .env terlebih dahulu.")
    resp = requests.get(
        f"{META_GRAPH_BASE}/me/accounts",
        params={"fields": "id,name,access_token,instagram_business_account{id,username}", "access_token": tok},
        timeout=20,
    )
    resp.raise_for_status()
    pages = resp.json().get("data", [])
    if not pages:
        print("Tidak ada Facebook Page yang terhubung ke token ini.")
        return
    for p in pages:
        ig = p.get("instagram_business_account") or {}
        print(f"\nFacebook Page : {p.get('name')}")
        print(f"  FB_PAGE_ID              = {p.get('id')}")
        print(f"  IG_BUSINESS_ACCOUNT_ID  = {ig.get('id', '(belum terhubung ke IG Business)')} (@{ig.get('username', '-')})")


def exchange_meta_long_lived(project_root: Path) -> None:
    load_dotenv(project_root / ".env")
    tok = os.getenv("META_ACCESS_TOKEN", "").strip()
    app_id = os.getenv("META_APP_ID", "").strip()
    app_secret = os.getenv("META_APP_SECRET", "").strip()
    if not (tok and app_id and app_secret):
        raise SystemExit("Butuh META_ACCESS_TOKEN, META_APP_ID, dan META_APP_SECRET di .env untuk menukar ke 60-day token.")
    resp = requests.get(
        f"{META_GRAPH_BASE}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": tok,
        },
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    print("60-Day Long-Lived META_ACCESS_TOKEN berhasil dibuat:")
    print(json.dumps({"expires_in_days": round(data.get("expires_in", 0) / 86400, 1), "access_token": data.get("access_token")}, indent=2))


def discover_linkedin_urn(project_root: Path) -> None:
    load_dotenv(project_root / ".env")
    tok = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
    if not tok:
        raise SystemExit("Set LINKEDIN_ACCESS_TOKEN di .env terlebih dahulu.")
    resp = requests.get("https://api.linkedin.com/v2/userinfo", headers={"Authorization": f"Bearer {tok}"}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    print(f"LINKEDIN_AUTHOR_URN = urn:li:person:{data.get('sub')}")
    print(f"Name                = {data.get('name')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Direct Free Social API Auth Helper & Validator")
    parser.add_argument("--check", action="store_true", help="Periksa status semua token Direct API")
    parser.add_argument("--discover-meta", action="store_true", help="Temukan FB_PAGE_ID & IG_BUSINESS_ACCOUNT_ID otomatis")
    parser.add_argument("--exchange-meta", action="store_true", help="Tukar Meta token menjadi 60-day long-lived token")
    parser.add_argument("--discover-linkedin", action="store_true", help="Temukan LINKEDIN_AUTHOR_URN otomatis")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parent.parent
    if args.discover_meta:
        discover_meta_ids(root)
    elif args.exchange_meta:
        exchange_meta_long_lived(root)
    elif args.discover_linkedin:
        discover_linkedin_urn(root)
    else:
        res = check_all_connections(root)
        print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
