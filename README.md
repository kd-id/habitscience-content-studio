# Content Automation Studio (Antigravity Edition)

Sistem automasi konten end-to-end untuk **YouTube Long (16:9)**, **YouTube Shorts / TikTok / Instagram Reels (9:16)**, **Instagram & LinkedIn Carousel (5 slide 4:5)**, serta **Thread X, Threads, dan Facebook** — mulai dari riset ide, penulisan naskah & repurpose, produksi voiceover + subtitle sinkron, desain visual & render video HD FFmpeg, hingga **auto-draft / auto-publish lengkap dengan laporan detail (`PUBLISH_REPORT.md`)**.

## Arsitektur Pipeline

1. **Riset Tren & Anti-Duplikat (`src/ideation.py`)** — Mengambil tren Google News RSS / custom RSS / riset web Antigravity dan memeriksa `output/history.json` agar topik selalu segar.
2. **Master Script & Repurpose Engine (`src/scriptwriter.py`)** — Mengubah 1 topik menjadi:
   - Script YouTube Panjang (5 scene, judul SEO + 3 alternatif A/B, deskripsi ber-chapter, tags, konsep thumbnail).
   - Script Video Vertikal 9:16 (4 scene punchy < 60 detik + caption khusus YT Shorts, TikTok, IG Reels).
   - Paket Carousel 5 Slide + caption Instagram, LinkedIn, Thread X (5 tweet), Threads, dan Facebook.
3. **Visual Studio (`src/media_assets.py`)** — Merender Thumbnail YouTube (`1280x720`), slide scene `1920x1080` & `1080x1920`, dan 5 slide carousel `1080x1350`. Mendukung background AI opsional dari **Antigravity `image-generator`** maupun **Gemini Imagen**.
4. **Neural Voiceover & Synced Subtitles (`src/voiceover.py`)** — Menggunakan `edge-tts` (suara natural bahasa Indonesia/Inggris) per scene + membuat `subtitles.srt` yang 100% sinkron dengan durasi audio nyata.
5. **FFmpeg HD Video Builder (`src/video_builder.py`)** — Menggabungkan visual, transisi fade, audio AAC 192kbps, dan burned-in subtitles menjadi `video_16x9.mp4` dan `video_9x16.mp4` (`H.264 + yuv420p + faststart`).
6. **Auto-Draft / Auto-Publish (`src/publisher.py`)** —
   - **YouTube Data API v3**: Upload langsung YouTube Long + Thumbnail & YouTube Shorts sebagai `private` (mode `draft`) atau `public` (mode `publish`).
   - **Social Webhook (Zapier / n8n / Make)**: Mengirim payload JSON lengkap untuk Instagram, TikTok, LinkedIn, X/Threads, dan Facebook.
7. **Executive Publish Report (`src/reporter.py`)** — Membuat `PUBLISH_REPORT.md` & `report.json` berisi tabel status tiap platform, link draft/publish, inventaris ukuran/resolusi/durasi media, checklist QA otomatis, serta seluruh copywriting siap pakai.

## Cara Menjalankan

### A. Lewat Antigravity (Paling Praktis — On-Demand)
Cukup ketik di chat Antigravity (Skill `content-automation-studio` sudah terpasang global):
- *"Buatkan paket konten lengkap tentang [topik] dan jalankan auto-draft"*
- *"Riset tren AI hari ini lalu produksi konten YouTube + sosmed lengkap dengan laporan"*

### B. Lewat Multi-Agent Parallel Workflow (`run_workflow`)
Gunakan script `workflows/content_pipeline_workflow.py` agar 3 spesialis writer (YouTube Long, Shorts/TikTok/Reels, Carousel/Social) bekerja paralel lalu merender & melaporkan hasil secara otomatis.

### C. Lewat CLI Langsung
```powershell
cd "C:\Users\Administrator\.gemini\antigravity\scratch\content-automation-studio"

# 1. Uji coba aman (Dry-Run penuh + render video + laporan)
python -m src.pipeline --topic "Cara Automasi Konten YouTube Pakai AI" --publish-mode dry-run

# 2. Produksi otomatis dari tren hari ini -> Auto-Draft
python -m src.pipeline --publish-mode draft

# 3. Gunakan blueprint JSON hasil riset Antigravity -> Auto-Draft
python -m src.pipeline --brief "output\_agent_brief.json" --publish-mode draft

# 4. Publish langsung ke publik (hanya jika kredensial & QA sudah siap)
python -m src.pipeline --topic "Topik Anda" --publish-mode publish
```

## Konfigurasi Brand & Kredensial

1. Edit `config/channel_config.yaml` untuk menyesuaikan **nama channel, handle, niche, warna brand, suara TTS (`id-ID-ArdiNeural` / `id-ID-GadisNeural`), dan platform aktif**.
2. Salin `.env.example` menjadi `.env`:
   - **YouTube Auto-Draft/Publish**: Simpan file OAuth Desktop Client dari Google Cloud Console di `config/youtube_client_secret.json`.
   - **Instagram, TikTok, LinkedIn, X, Facebook**: Isi `PUBLISH_WEBHOOK_URL` dengan URL webhook **Zapier** atau **n8n** (atau pasang plugin Zapier langsung di Antigravity Marketplace).
   - **Gemini API Headless (Opsional)**: Isi `GEMINI_API_KEY` jika ingin menjalankan mode CLI mandiri tanpa Antigravity agent.
   - **Notifikasi Laporan (Opsional)**: Isi `REPORT_NOTIFICATION_WEBHOOK_URL` (Discord/Slack) agar ringkasan laporan langsung masuk notifikasi.
