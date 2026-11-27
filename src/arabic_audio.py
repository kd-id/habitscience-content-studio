"""Authentic Arabic Voiceover & Real Qur'an Qari Tilawah Engine (100% Free).

Routing rules (strict Islamic Adab):
  1. Qur'an Verses (`QUR'AN S:A` or `QUR'AN S:A1-A2`):
     - Fetches REAL uncut Qari recitation from EveryAyah.com CDN (default: Syaikh Mishary Rashid Alafasy,
       `Alafasy_128kbps`) with persistent local caching under `assets/cache/quran_audio/`.
     - NEVER cuts or speeds up a Qari mid-verse!
     - On YouTube Long (16:9): always uses the full uncut real Qari Ayah recitation.
     - On Shorts (9:16, <=58s budget): uses the full uncut real Qari recitation whenever the complete Ayah
       is <= `max_qari_short_sec` (default 20.0s, covering 8+ of our core verses including 13:28, 14:7,
       94:5-6, 78:9-10, 65:3, 2:153, 25:63, 99:7). For extra-long verses (>20s such as 2:286 or 13:11),
       Shorts gracefully recites ONLY the exact displayed Arabic clause via calm Saudi Arabic neural voice
       (`ar-SA-HamedNeural`) rather than truncating a Qari mid-sentence.
  2. Authentic Hadith & Prophetic Duas (`SAHIH AL-BUKHARI`, `SAHIH MUSLIM`, `SUNAN ...`, `JAMI' ...`):
     - Uses native Saudi Arabic male neural voice (`ar-SA-HamedNeural`, gentle `-8%` pace) reading full
       harakat/tashkeel cleanly and clearly.
"""

from __future__ import annotations

import asyncio
import re
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import edge_tts

from src.voiceover import probe_duration_sec

EVERYAYAH_BASE = "https://everyayah.com/data"
DEFAULT_QARI_ID = "Alafasy_128kbps"
DEFAULT_QARI_LABEL = "Mishary Rashid Alafasy"
DEFAULT_ARABIC_TTS_VOICE = "ar-SA-HamedNeural"


@dataclass
class ArabicRecitationResult:
    audio_path: Path
    duration_sec: float
    source: str
    reciter_label: str
    is_real_qari: bool


def parse_quran_citation(citation: str) -> tuple[int, int, int] | None:
    """Parse citations like `QUR'AN 13:28`, `QUR'AN 94:5-6`, or `SURAH AR-RA'D 13:28`."""
    raw = (citation or "").strip().upper()
    if "QUR" not in raw and "SURAH" not in raw:
        return None
    m = re.search(r"(\d{1,3})\s*:\s*(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?", raw)
    if not m:
        return None
    surah = int(m.group(1))
    a1 = int(m.group(2))
    a2 = int(m.group(3) or a1)
    if not (1 <= surah <= 114 and 1 <= a1 <= 286 and a1 <= a2 <= 286):
        return None
    return surah, a1, a2


def _normalize_clip_to_wav(src_audio: Path, out_wav: Path, target_lufs: float = -15.5) -> Path:
    """Normalize recitation loudness gently to 48kHz stereo PCM WAV without altering pitch or speed."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src_audio),
            "-af", f"loudnorm=I={target_lufs:.1f}:TP=-1.5:LRA=11,aformat=sample_rates=48000:channel_layouts=stereo",
            "-c:a", "pcm_s16le",
            str(out_wav),
        ],
        capture_output=True, text=True, check=True,
    )
    return out_wav


def fetch_everyayah_quran_wav(
    surah: int,
    ayah_start: int,
    ayah_end: int,
    work_dir: Path,
    qari_id: str = DEFAULT_QARI_ID,
    cache_dir: Path | None = None,
) -> tuple[Path, float]:
    """Download (with local cache) and normalize complete uncut Ayah recitation(s) from EveryAyah.com."""
    root = Path(__file__).resolve().parent.parent
    cdir = cache_dir or (root / "assets" / "cache" / "quran_audio" / qari_id)
    cdir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    mp3_parts: list[Path] = []
    for ayah in range(ayah_start, ayah_end + 1):
        code = f"{surah:03d}{ayah:03d}"
        cached = cdir / f"{code}.mp3"
        if not cached.exists() or cached.stat().st_size < 4096:
            url = f"{EVERYAYAH_BASE}/{qari_id}/{code}.mp3"
            req = urllib.request.Request(url, headers={"User-Agent": "HabitSainsStudio/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            if len(data) < 4096:
                raise RuntimeError(f"EveryAyah returned unexpectedly tiny audio for {code}")
            cached.write_bytes(data)
        mp3_parts.append(cached)

    out_wav = work_dir / f"qari_{surah:03d}_{ayah_start:03d}_{ayah_end:03d}.wav"
    if len(mp3_parts) == 1:
        _normalize_clip_to_wav(mp3_parts[0], out_wav, target_lufs=-15.5)
    else:
        concat_txt = work_dir / f"_qari_concat_{surah:03d}.txt"
        concat_txt.write_text(
            "\n".join(f"file '{p.resolve().as_posix()}'" for p in mp3_parts),
            encoding="utf-8",
        )
        merged = work_dir / f"_qari_merged_{surah:03d}.mp3"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(merged)],
            capture_output=True, text=True, check=True,
        )
        _normalize_clip_to_wav(merged, out_wav, target_lufs=-15.5)
        concat_txt.unlink(missing_ok=True)
        merged.unlink(missing_ok=True)

    return out_wav, probe_duration_sec(out_wav)


async def _synth_arabic_edge_async(text: str, out_mp3: Path, voice: str, rate: str) -> None:
    comm = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await comm.save(str(out_mp3))


def synthesize_arabic_tts_wav(
    arabic_text: str,
    work_dir: Path,
    voice: str = DEFAULT_ARABIC_TTS_VOICE,
    rate: str = "-8%",
) -> tuple[Path, float]:
    """Synthesize calm native Saudi Arabic neural voice reading full-harakat Dua/Hadith cleanly."""
    clean = (arabic_text or "").replace("۝", "، ").replace("ۚ", "، ").strip()
    if not clean:
        raise ValueError("Empty Arabic text for recitation")
    work_dir.mkdir(parents=True, exist_ok=True)
    raw_mp3 = work_dir / "_arabic_tts_raw.mp3"
    out_wav = work_dir / "arabic_tts_norm.wav"
    asyncio.run(_synth_arabic_edge_async(clean, raw_mp3, voice=voice, rate=rate))
    if not raw_mp3.exists() or raw_mp3.stat().st_size < 1024:
        raise RuntimeError("Arabic Edge TTS returned empty audio")
    _normalize_clip_to_wav(raw_mp3, out_wav, target_lufs=-15.8)
    raw_mp3.unlink(missing_ok=True)
    return out_wav, probe_duration_sec(out_wav)


def resolve_dalil_arabic_audio(
    dalil: dict[str, Any],
    work_dir: Path,
    config: dict[str, Any],
    is_short: bool = False,
) -> ArabicRecitationResult | None:
    """Resolve the best authentic Arabic recitation clip for this verified dalil.

    - Qur'an verses -> Real uncut Mishary Rashid Alafasy tilawah via EveryAyah.com
      (falls back to Saudi Arabic TTS on Shorts ONLY when the full Ayah > 20s so a Qari is never cut mid-verse).
    - Hadith / Prophetic Duas -> Native Saudi Arabic male neural voice (`ar-SA-HamedNeural`).
    """
    vo_cfg = config.get("voiceover", {})
    if not bool(vo_cfg.get("arabic_recitation", True)):
        return None

    arabic_text = str(dalil.get("arabic") or "").strip()
    citation = str(dalil.get("citation") or "").strip()
    if not arabic_text:
        return None

    qari_id = str(vo_cfg.get("quran_reciter", DEFAULT_QARI_ID)).strip() or DEFAULT_QARI_ID
    qari_label = str(vo_cfg.get("quran_reciter_label", DEFAULT_QARI_LABEL)).strip() or DEFAULT_QARI_LABEL
    ar_voice = str(vo_cfg.get("arabic_tts_voice", DEFAULT_ARABIC_TTS_VOICE)).strip() or DEFAULT_ARABIC_TTS_VOICE
    ar_rate = str(vo_cfg.get("arabic_tts_rate", "-8%")).strip() or "-8%"
    max_qari_short_sec = float(vo_cfg.get("max_qari_short_sec", 20.0))

    parsed_q = parse_quran_citation(citation)
    if parsed_q is not None:
        surah, a1, a2 = parsed_q
        try:
            q_wav, q_dur = fetch_everyayah_quran_wav(surah, a1, a2, work_dir=work_dir, qari_id=qari_id)
            if (not is_short) or (q_dur <= max_qari_short_sec):
                print(
                    f"[arabic-vo] Real Qari tilawah loaded: {citation} ({qari_label}, {q_dur:.1f}s, uncut)",
                    flush=True,
                )
                return ArabicRecitationResult(
                    audio_path=q_wav,
                    duration_sec=round(q_dur, 3),
                    source=f"everyayah:{qari_id}",
                    reciter_label=qari_label,
                    is_real_qari=True,
                )
            print(
                f"[arabic-vo] Complete Ayah {citation} is {q_dur:.1f}s (> {max_qari_short_sec:.0f}s Shorts cap); "
                f"keeping Qari uncut for Long and using calm {ar_voice} for the displayed Short excerpt.",
                flush=True,
            )
            q_wav.unlink(missing_ok=True)
        except Exception as exc:
            print(f"[arabic-vo] EveryAyah fetch skipped ({type(exc).__name__}): {str(exc)[:120]}; falling back to {ar_voice}.", flush=True)

    # Hadith, Prophetic Dua, or extra-long Short excerpt -> calm native Saudi Arabic neural voice
    try:
        t_wav, t_dur = synthesize_arabic_tts_wav(arabic_text, work_dir=work_dir, voice=ar_voice, rate=ar_rate)
        print(f"[arabic-vo] Saudi Arabic recitation ready: {citation} ({ar_voice}, {t_dur:.1f}s)", flush=True)
        return ArabicRecitationResult(
            audio_path=t_wav,
            duration_sec=round(t_dur, 3),
            source=f"edge_tts:{ar_voice}",
            reciter_label="Arabic Recitation",
            is_real_qari=False,
        )
    except Exception as exc:
        print(f"[arabic-vo] Arabic TTS unavailable ({type(exc).__name__}): {str(exc)[:120]}; continuing English-only.", flush=True)
        return None
