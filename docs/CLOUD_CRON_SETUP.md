# Panduan Setup 24/7 Cloud Cron (`cron-job.org` -> GitHub Actions)

Panduan singkat 2 menit untuk memastikan **seluruh produksi harian, bot komentar, dan analitik berjalan 100% tepat waktu 24/7 walau PC mati** (bebas dari delay/skip cron bawaan GitHub).

> Repo `kd-id/habitscience-content-studio` sudah berstatus **Public** (kuota Actions **UNLIMITED gratis**, seluruh API key & token tetap terenkripsi aman di GitHub Secrets), dan sudah dilengkapi **pengaman anti-dobel 90 menit** sehingga `cron-job.org` dan cron cadangan GitHub tidak akan pernah membuat video ganda.

---

## Langkah 1 — Buat GitHub Fine-Grained PAT (30 Detik)
1. Buka: https://github.com/settings/personal-access-tokens/new
2. Isi:
   - **Token name**: `habitsains-cron-trigger`
   - **Expiration**: `No expiration` (atau `1 year`)
   - **Repository access**: pilih **Only select repositories** -> `kd-id/habitscience-content-studio`
   - **Repository permissions** -> **Actions**: ubah ke **`Read and write`** (izin lain biarkan `No access`).
3. Klik **Generate token**, lalu salin token yang muncul (`github_pat_...`).

---

## Langkah 2 — Buat 3 Jadwal di `cron-job.org` (Gratis Selamanya)
Daftar / masuk ke: https://console.cron-job.org/

### Job 1: Produksi & Publikasi Konten (3x Sehari — Prime Time AS)
- **Title**: `HabitSains Production 3x Daily`
- **URL**: `https://api.github.com/repos/kd-id/habitscience-content-studio/actions/workflows/content-automation.yml/dispatches`
- **Execution schedule** (Custom — Timezone `Asia/Jakarta` / WIB):
  - **Hours**: `2, 14, 21`
  - **Minutes**: `17` *(jalan tepat jam 14:17, 21:17, dan 02:17 WIB setiap hari)*
- **Advanced tab**:
  - **Request method**: `POST`
  - **Headers** (tambahkan 3 header):
    - `Authorization`: `Bearer github_pat_ISI_TOKEN_KAMU`
    - `Accept`: `application/vnd.github+json`
    - `User-Agent`: `HabitSains-Cron`
  - **Request body**:
    ```json
    {"ref":"main","inputs":{"publish_mode":"scheduled","visual_style":"hybrid_cozy_3dpov"}}
    ```

### Job 2: Bot Auto-Reply Komentar (Setiap 3 Jam)
- **Title**: `HabitSains Comment Bot`
- **URL**: `https://api.github.com/repos/kd-id/habitscience-content-studio/actions/workflows/comment-autoreply.yml/dispatches`
- **Execution schedule** (Timezone `Asia/Jakarta` / WIB):
  - **Hours**: `0, 3, 6, 9, 12, 15, 18, 21`
  - **Minutes**: `37`
- **Advanced tab**:
  - **Request method**: `POST`
  - **Headers**: sama persis seperti Job 1
  - **Request body**:
    ```json
    {"ref":"main","inputs":{"dry_run":false}}
    ```

### Job 3: Analitik & Optimizer Gaya Visual (1x Sehari)
- **Title**: `HabitSains Daily Analytics`
- **URL**: `https://api.github.com/repos/kd-id/habitscience-content-studio/actions/workflows/analytics-optimizer.yml/dispatches`
- **Execution schedule** (Timezone `Asia/Jakarta` / WIB):
  - **Every day at**: `19:13`
- **Advanced tab**:
  - **Request method**: `POST`
  - **Headers**: sama persis seperti Job 1
  - **Request body**:
    ```json
    {"ref":"main","inputs":{"send_telegram":true}}
    ```

---

## Langkah 3 — Tes 1 Klik
Di `cron-job.org`, klik tombol **Test Run** pada Job 2 (`HabitSains Comment Bot`) -> harus mengembalikan status **`204 No Content`** (artinya GitHub Actions langsung jalan!).
