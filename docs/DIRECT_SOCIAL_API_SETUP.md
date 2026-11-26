# Panduan Aktivasi Direct Social API Gratis (Tanpa Biaya Bulanan)

`src/social_publishers.py` kini sudah mendukung **direct binary upload resmi & 100% gratis** ke semua platform sosial media langsung dari PC lokal maupun GitHub Actions Cloud (tanpa butuh Zapier/Make berbayar atau hosting pihak ketiga).

> **Catatan**: Anda **tidak wajib** mengaktifkan semua sekaligus. Cukup pasang secret untuk platform yang memang ingin Anda jalankan — platform lain otomatis ditandai `PENDING_AUTH` tanpa mengganggu pipeline.

---

## 1. Instagram Reels, Instagram Carousel, & Facebook Page Reels (Meta Graph API — Gratis)

**Syarat akun**:
1. Ubah akun Instagram Anda ke **Professional (Business / Creator)** di menu *Settings → Account type*.
2. Hubungkan akun Instagram tersebut ke **1 Facebook Page** milik Anda (*Meta Business Suite*).

**Langkah ambil token (3 menit)**:
1. Buka [Meta for Developers](https://developers.facebook.com/apps/) → **Create App** → pilih **Business**.
2. Tambahkan produk **Facebook Login for Business** & **Instagram**.
3. Buka [Graph API Explorer](https://developers.facebook.com/tools/explorer/), pilih App Anda, lalu centang izin:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
4. Klik **Generate Access Token**, salin ke `.env` sebagai `META_ACCESS_TOKEN`.
5. Jalankan helper otomatis kami untuk menemukan `FB_PAGE_ID` & `IG_BUSINESS_ACCOUNT_ID`, serta menukar token menjadi **60 hari**:
   ```powershell
   python -m src.auth_social --discover-meta
   python -m src.auth_social --exchange-meta
   ```
6. Simpan ke GitHub Secrets:
   - `META_ACCESS_TOKEN`
   - `IG_BUSINESS_ACCOUNT_ID`
   - `FB_PAGE_ID`

> **Perilaku Mode**:
> - **Facebook Reels**: mode `draft` membuat **Draft asli di Meta Business Suite**; mode `publish` langsung tayang publik.
> - **Instagram Reels & Carousel**: mode `draft` mengunggah binary & memverifikasi container Meta tanpa merilis ke feed; mode `publish` langsung tayang ke Reels/Feed IG.

---

## 2. TikTok (Content Posting API v2 — Gratis, Masuk TikTok Inbox Draft)

1. Buka [TikTok for Developers](https://developers.tiktok.com/) → buat App → aktifkan **Content Posting API** (scope `video.upload`).
2. Dapatkan `access_token` dan `refresh_token` (berlaku 365 hari) dari OAuth TikTok.
3. Simpan ke GitHub Secrets:
   - `TIKTOK_CLIENT_KEY`
   - `TIKTOK_CLIENT_SECRET`
   - `TIKTOK_REFRESH_TOKEN` *(otomatis me-refresh access token setiap hari di GitHub Actions!)*
   - *(Opsional jika uji coba cepat)* `TIKTOK_ACCESS_TOKEN`

> **Keunggulan Inbox Draft**: Video 9:16 3D POV langsung diunggah secara binary ke **Inbox aplikasi TikTok** Anda — aman dari flag spam dan tidak perlu menunggu *app audit* panjang untuk mulai dipakai.

---

## 3. LinkedIn (REST Posts API — Gratis)

1. Buka [LinkedIn Developers](https://www.linkedin.com/developers/apps) → buat App → aktifkan produk **Share on LinkedIn** & **Sign In with LinkedIn using OpenID Connect** (scope `w_member_social`, `openid`, `profile`).
2. Generate OAuth Access Token di tab **Auth → OAuth 2.0 tools**.
3. Temukan `LINKEDIN_AUTHOR_URN` otomatis dengan:
   ```powershell
   python -m src.auth_social --discover-linkedin
   ```
4. Simpan ke GitHub Secrets:
   - `LINKEDIN_ACCESS_TOKEN`
   - `LINKEDIN_AUTHOR_URN`

---

## 4. Meta Threads & X / Twitter v2 (Gratis)

- **Meta Threads**: di Meta App yang sama, aktifkan produk **Threads API** (`threads_basic`, `threads_content_publish`), lalu simpan `THREADS_ACCESS_TOKEN` & `THREADS_USER_ID` ke GitHub Secrets.
- **X (Twitter v2 Free Tier)**: buat Project di [X Developer Portal](https://developer.x.com/) dengan izin **Read and Write**, lalu simpan 4 kunci OAuth 1.0a ke GitHub Secrets:
  - `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_SECRET`

---

## Cek Status Semua Koneksi Sekaligus

Kapan saja Anda menambahkan token di `.env`, jalankan:
```powershell
python -m src.auth_social --check
```
Atau langsung simpan secret ke GitHub Cloud dari terminal:
```powershell
gh secret set META_ACCESS_TOKEN
gh secret set IG_BUSINESS_ACCOUNT_ID
gh secret set FB_PAGE_ID
gh secret set TIKTOK_REFRESH_TOKEN
```
