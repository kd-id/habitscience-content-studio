"""Interactive Free Direct Social API Connection Checker & Token Helper.

Usage:
  python -m src.auth_social --check              # Verify ALL configured Direct API tokens
  python -m src.auth_social --discover-meta      # Auto-find FB_PAGE_ID & IG_BUSINESS_ACCOUNT_ID from META_ACCESS_TOKEN
  python -m src.auth_social --exchange-meta      # Exchange short-lived META_ACCESS_TOKEN into a 60-day token
  python -m src.auth_social --discover-linkedin  # Auto-find LINKEDIN_AUTHOR_URN from LINKEDIN_ACCESS_TOKEN
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
import re
import secrets
import sys
import urllib.parse
import webbrowser
from pathlib import Path

import requests
from dotenv import dotenv_values, load_dotenv

from src.social_publishers import META_GRAPH_BASE, THREADS_API_BASE, _resolve_tiktok_access_token


def _upsert_env_file(env_path: Path, updates: dict[str, str]) -> None:
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    done: set[str] = set()
    out: list[str] = []
    for ln in lines:
        m = re.match(r"^([A-Za-z0-9_]+)\s*=", ln)
        if m and m.group(1) in updates:
            k = m.group(1)
            out.append(f"{k}={updates[k]}")
            done.add(k)
        else:
            out.append(ln)
    for k, v in updates.items():
        if k not in done:
            out.append(f"{k}={v}")
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def _load_merged_env(project_root: Path) -> None:
    """Load root .env and also fallback to config/.env if user saved keys there."""
    cfg_env = project_root / "config" / ".env"
    if cfg_env.exists():
        for k, v in dotenv_values(cfg_env).items():
            if k and (v or "").strip() and not os.getenv(k, "").strip():
                os.environ[k] = str(v).strip()
    load_dotenv(project_root / ".env", override=False)


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


def discover_threads_id(project_root: Path) -> None:
    _load_merged_env(project_root)
    tok = os.getenv("THREADS_ACCESS_TOKEN", "").strip()
    if not tok:
        raise SystemExit("Set THREADS_ACCESS_TOKEN di .env (atau config/.env) terlebih dahulu.")
    resp = requests.get(f"{THREADS_API_BASE}/me", params={"fields": "id,username,name", "access_token": tok}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    uid = str(data.get("id", "")).strip()
    uname = str(data.get("username", "")).strip()
    # Optional 60-day long-lived exchange if THREADS_APP_SECRET is provided
    th_secret = os.getenv("THREADS_APP_SECRET", "").strip() or os.getenv("META_APP_SECRET", "").strip()
    final_tok = tok
    if th_secret:
        ex = requests.get(
            f"{THREADS_API_BASE}/access_token",
            params={"grant_type": "th_exchange_token", "client_secret": th_secret, "access_token": tok},
            timeout=15,
        )
        if ex.ok and ex.json().get("access_token"):
            final_tok = str(ex.json()["access_token"]).strip()
            print(f"Threads token diperpanjang ({round(ex.json().get('expires_in', 0) / 86400, 1)} hari).")
    _upsert_env_file(project_root / ".env", {"THREADS_ACCESS_TOKEN": final_tok, "THREADS_USER_ID": uid})
    print(f"THREADS_USER_ID = {uid} (@{uname}) — tersimpan ke .env!")


def auth_tiktok_oauth(project_root: Path, port: int = 8765) -> None:
    """Interactive browser OAuth2 PKCE flow for TikTok Content Posting API (auto-saves 365-day refresh token!)."""
    _load_merged_env(project_root)
    client_key = os.getenv("TIKTOK_CLIENT_KEY", "").strip()
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET", "").strip()
    if not (client_key and client_secret):
        raise SystemExit("Isi TIKTOK_CLIENT_KEY dan TIKTOK_CLIENT_SECRET di .env (atau config/.env) terlebih dahulu.")

    redirect_uri = f"http://localhost:{port}/callback"
    state = secrets.token_urlsafe(16)
    code_verifier = secrets.token_urlsafe(48)
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")

    auth_params = urllib.parse.urlencode({
        "client_key": client_key,
        "scope": "user.info.basic,video.upload",
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })
    auth_url = f"https://www.tiktok.com/v2/auth/authorize/?{auth_params}"
    captured: dict[str, str] = {}

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            if "code" in qs:
                captured["code"] = qs["code"][0]
                captured["state"] = (qs.get("state") or [""])[0]
                body = b"<h2>TikTok berhasil terhubung! Anda boleh menutup tab ini.</h2>"
                self.send_response(200)
            else:
                captured["error"] = (qs.get("error_description") or qs.get("error") or ["unknown"])[0]
                body = f"<h2>TikTok OAuth gagal: {captured['error']}</h2>".encode("utf-8")
                self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:  # noqa: A002
            pass

    server = http.server.HTTPServer(("127.0.0.1", port), _Handler)
    print(f"Membuka browser untuk login & otorisasi TikTok (redirect: {redirect_uri})...", flush=True)
    webbrowser.open(auth_url)
    server.handle_request()
    server.server_close()

    if "code" not in captured:
        raise SystemExit(f"Otorisasi TikTok dibatalkan/gagal: {captured.get('error', 'no code')}")

    tok_resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "code": captured["code"],
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        },
        timeout=25,
    )
    tok_resp.raise_for_status()
    tok_data = tok_resp.json()
    acc = str(tok_data.get("access_token", "")).strip()
    ref = str(tok_data.get("refresh_token", "")).strip()
    if not acc:
        raise SystemExit(f"TikTok token exchange gagal: {tok_data}")
    updates = {"TIKTOK_CLIENT_KEY": client_key, "TIKTOK_CLIENT_SECRET": client_secret, "TIKTOK_ACCESS_TOKEN": acc}
    if ref:
        updates["TIKTOK_REFRESH_TOKEN"] = ref
    _upsert_env_file(project_root / ".env", updates)
    print("TikTok OAuth BERHASIL! TIKTOK_ACCESS_TOKEN & TIKTOK_REFRESH_TOKEN (365 hari) tersimpan ke .env!")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Direct Free Social API Auth Helper & Validator")
    parser.add_argument("--check", action="store_true", help="Periksa status semua token Direct API")
    parser.add_argument("--discover-meta", action="store_true", help="Temukan FB_PAGE_ID & IG_BUSINESS_ACCOUNT_ID otomatis")
    parser.add_argument("--exchange-meta", action="store_true", help="Tukar Meta token menjadi 60-day long-lived token")
    parser.add_argument("--discover-threads", action="store_true", help="Temukan THREADS_USER_ID & perpanjang token Threads 60 hari")
    parser.add_argument("--auth-tiktok", action="store_true", help="Login OAuth TikTok via browser lokal (otomatis simpan refresh token 365 hari)")
    parser.add_argument("--discover-linkedin", action="store_true", help="Temukan LINKEDIN_AUTHOR_URN otomatis")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parent.parent
    if args.discover_meta:
        discover_meta_ids(root)
    elif args.exchange_meta:
        exchange_meta_long_lived(root)
    elif args.discover_threads:
        discover_threads_id(root)
    elif args.auth_tiktok:
        auth_tiktok_oauth(root)
    elif args.discover_linkedin:
        discover_linkedin_urn(root)
    else:
        res = check_all_connections(root)
        print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
