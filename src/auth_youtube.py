"""One-time local YouTube OAuth login helper for Cloud (GitHub Actions / Docker).

Usage:
    python -m src.auth_youtube

Saves config/youtube_token.json and prints a Base64 string ready to paste into
the GitHub Actions secret `YOUTUBE_TOKEN_JSON` or Docker `.env`.
"""

from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

from src.config_loader import get_project_paths, load_config
from src.publisher import YOUTUBE_SCOPES


def main() -> int:
    paths = get_project_paths()
    load_config(project_root=paths.root)

    secrets_rel = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "config/youtube_client_secret.json")
    token_rel = os.getenv("YOUTUBE_TOKEN_FILE", "config/youtube_token.json")
    secrets_path = (paths.root / secrets_rel) if not Path(secrets_rel).is_absolute() else Path(secrets_rel)
    token_path = (paths.root / token_rel) if not Path(token_rel).is_absolute() else Path(token_rel)

    if not secrets_path.exists():
        print(f"[ERROR] File OAuth Client Secret belum ada di: {secrets_path}")
        print("Langkah:")
        print("  1. Buka Google Cloud Console -> APIs & Services -> Enable 'YouTube Data API v3'.")
        print("  2. Credentials -> Create Credentials -> OAuth client ID -> Application type: Desktop app.")
        print(f"  3. Download file JSON lalu simpan sebagai: {secrets_path}")
        return 1

    from google_auth_oauthlib.flow import InstalledAppFlow

    print("Menyiapkan server login OAuth YouTube lokal...", flush=True)
    flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), YOUTUBE_SCOPES)
    creds = flow.run_local_server(
        host="localhost",
        port=8089,
        open_browser=True,
        authorization_prompt_message="OAUTH_URL: {url}",
        success_message="Login YouTube OAuth berhasil! Anda boleh menutup tab browser ini dan kembali ke Antigravity.",
        access_type="offline",
        prompt="consent",
    )

    token_json = creds.to_json()
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(token_json, encoding="utf-8")

    print(f"\n[OK] Token OAuth tersimpan di: {token_path}")
    if "--no-print-token" not in sys.argv:
        b64 = base64.b64encode(token_json.encode("utf-8")).decode("ascii")
        print("\nUntuk GitHub Actions Secret / Docker Cloud, simpan string berikut sebagai `YOUTUBE_TOKEN_JSON`:")
        print("-" * 72)
        print(b64)
        print("-" * 72)
        print("PERINGATAN: Jangan pernah commit file token atau string ini ke repository publik!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
