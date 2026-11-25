# Panduan Menjalankan Content Automation Studio di Cloud (Tanpa PC Menyala)

Anda punya **2 pilihan cloud** yang sudah siap pakai di proyek ini:

| Opsi | Biaya | Cocok Untuk | Cara Kerja |
| :--- | :--- | :--- | :--- |
| **Opsi 1: GitHub Actions** | **Gratis** (2.000 menit/bln di repo private, unlimited di repo public) | Paling praktis, tanpa beli/urus server | Jalan otomatis sesuai jadwal cron, laporan muncul di GitHub Summary + bisa download video/carousel dari Artifacts |
| **Opsi 2: Docker + VPS / Railway / Coolify** | Mulai ~Rp50rb–Rp100rb/bln (atau Oracle Cloud Free Tier) | Kontrol penuh 24/7, penyimpanan file lokal permanen | Container `scheduler` bangun tiap jam jadwal WIB dan menjalankan pipeline otomatis |

---

## Persiapan Awal (Cukup 1 Kali di PC Lokal Anda)

### Langkah A: Sesuaikan Niche & Brand Channel
Edit `config/channel_config.yaml` (nama channel, handle, niche, warna brand, suara TTS, dan platform aktif).

### Langkah B: Siapkan Kredensial API yang Dibutuhkan di Cloud
1. **Gemini API Key (Sangat Disarankan untuk Mode Cloud)**:
   - Di cloud tidak ada chat Antigravity interaktif, jadi gunakan `GEMINI_API_KEY` gratis/berbayar dari [Google AI Studio](https://aistudio.google.com/apikey) agar script, judul SEO, dan repurpose tetap tajam & relevan dengan tren terbaru.
2. **YouTube Auto-Draft / Auto-Publish (Opsional — 1x Login di PC Lokal)**:
   - Buat OAuth Desktop Client di Google Cloud Console (enable **YouTube Data API v3**), download ke `config/youtube_client_secret.json`.
   - Jalankan sekali di PC lokal Anda:
     ```powershell
     cd "C:\Users\Administrator\.gemini\antigravity\scratch\content-automation-studio"
     python -m src.auth_youtube
     ```
   - Browser akan terbuka untuk izin channel YouTube. Setelah selesai, skrip akan mencetak string Base64 **`YOUTUBE_TOKEN_JSON`** — salin string ini untuk dimasukkan ke Secret GitHub / `.env` Docker.
3. **Auto-Draft / Auto-Publish Sosmed Lain (Instagram, TikTok, LinkedIn, X, Facebook)**:
   - Buat Webhook di **Zapier** atau **n8n** (terima POST JSON dari pipeline -> arahkan ke aksi upload/draft tiap sosmed), lalu catat URL-nya sebagai `PUBLISH_WEBHOOK_URL`.
4. **Notifikasi Laporan ke HP (Opsional)**:
   - Buat Incoming Webhook di **Discord** atau **Slack**, lalu simpan sebagai `REPORT_NOTIFICATION_WEBHOOK_URL`.

---

## Opsi 1: Deploy di GitHub Actions (Gratis & Paling Cepat)

File workflow sudah disiapkan di `.github/workflows/content-automation.yml`.

### Step 1 — Buat Repository Private di GitHub
1. Buka https://github.com/new dan buat repository **Private** baru (misal: `content-automation-studio`).
2. Push proyek lokal Anda ke repo tersebut (`.gitignore` sudah melindungi `.env`, token YouTube, dan file video besar):
   ```powershell
   cd "C:\Users\Administrator\.gemini\antigravity\scratch\content-automation-studio"
   git init
   git branch -M main
   git add .
   git commit -m "feat: initial Content Automation Studio cloud setup"
   git remote add origin https://github.com/<USERNAME_ANDA>/content-automation-studio.git
   git push -u origin main
   ```

### Step 2 — Masukkan GitHub Secrets
Buka repository Anda di GitHub -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**, lalu tambahkan sesuai kebutuhan:
- `GEMINI_API_KEY` *(wajib agar script & ide AI tajam di cloud)*
- `YOUTUBE_TOKEN_JSON` *(hasil Base64 dari `python -m src.auth_youtube`)*
- `PUBLISH_WEBHOOK_URL` *(URL webhook Zapier / n8n untuk IG, TikTok, LinkedIn, X, FB)*
- `PUBLISH_WEBHOOK_SECRET` *(opsional)*
- `REPORT_NOTIFICATION_WEBHOOK_URL` *(opsional, webhook Discord/Slack)*

### Step 3 — Uji Coba 1 Klik dari Browser / HP
1. Buka tab **Actions** -> pilih **Content Automation Studio (Cloud Pipeline)**.
2. Klik **Run workflow**:
   - `topic`: kosongkan untuk riset tren otomatis, atau isi topik tertentu.
   - `publish_mode`: pilih **`dry-run`** dulu untuk tes pertama, lalu **`draft`** untuk produksi aman.
3. Tunggu ~2 menit sampai centang hijau.
4. Buka run tersebut:
   - **Summary** langsung menampilkan seluruh **`PUBLISH_REPORT.md`** (tabel status 8 platform, checklist QA, dan semua caption).
   - **Artifacts** berisi paket zip lengkap (`video_16x9.mp4`, `video_9x16.mp4`, `thumbnail.png`, 5 slide carousel, subtitle `.srt`, dan `PUBLISH_REPORT.md`) yang bisa diunduh kapan saja selama 14 hari.
   - `output/history.json` otomatis di-commit balik ke repo agar topik besok tidak pernah duplikat.

### Step 4 — Atur Jadwal Cron Otomatis
Edit `.github/workflows/content-automation.yml` pada bagian `schedule` (GitHub Actions menggunakan zona waktu **UTC**, selisih -7 jam dari WIB):
- **Setiap hari jam 08:00 WIB**: `cron: "0 1 * * *"` *(default aktif)*
- **Senin, Rabu, Jumat jam 08:00 WIB**: `cron: "0 1 * * 1,3,5"`
- **Setiap hari jam 19:00 WIB**: `cron: "0 12 * * *"`

> Setelah push, GitHub akan menjalankan produksi & auto-draft otomatis meski PC Anda mati total!

---

## Opsi 2: Deploy dengan Docker (VPS / Coolify / Railway / Render)

File sudah disiapkan di `Dockerfile`, `docker-compose.yml`, dan `src/cloud_scheduler.py`.

### Step 1 — Salin Proyek ke VPS & Buat File `.env`
```bash
git clone https://github.com/<USERNAME_ANDA>/content-automation-studio.git
cd content-automation-studio
cp .env.example .env
nano .env
```
Isi `GEMINI_API_KEY`, `YOUTUBE_TOKEN_JSON`, `PUBLISH_WEBHOOK_URL`, serta jadwal di `.env`:
```env
SCHEDULE_TZ=Asia/Jakarta
SCHEDULE_TIME_WIB=08:00
SCHEDULE_DAYS=mon,wed,fri
PUBLISH_MODE=draft
RUN_ON_STARTUP=false
```

### Step 2 — Uji Coba 1x Run On-Demand di Docker
```bash
docker compose build
docker compose run --rm studio --topic "Tips Automasi Konten AI" --publish-mode dry-run
```
Hasil video, carousel, dan `PUBLISH_REPORT.md` akan langsung muncul di folder `./output/` pada server Anda.

### Step 3 — Nyalakan Mode Cloud Scheduler 24/7
```bash
docker compose --profile scheduler up -d --build
```
Pantau log real-time kapan saja:
```bash
docker compose --profile scheduler logs -f
```
Container ini memakai `restart: unless-stopped`, sehingga walaupun VPS restart atau PC lokal Anda mati, pipeline akan tetap bangun otomatis sesuai `SCHEDULE_TIME_WIB` dan mengirim hasil + laporan ke YouTube/sosmed/notifikasi Anda!
