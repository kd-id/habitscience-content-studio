from __future__ import annotations

import asyncio
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import edge_tts


@dataclass
class SceneAudioResult:
    scene_no: int
    audio_path: str
    duration_sec: float
    text: str
    word_timings: list[dict[str, Any]]


@dataclass
class TrackAudioBundle:
    master_audio_path: str
    srt_path: str
    total_duration_sec: float
    voice: str
    scene_results: list[SceneAudioResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "master_audio_path": self.master_audio_path,
            "srt_path": self.srt_path,
            "total_duration_sec": round(self.total_duration_sec, 3),
            "voice": self.voice,
            "scenes": [asdict(s) for s in self.scene_results],
        }


def probe_duration_sec(media_path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(media_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    try:
        return max(float(res.stdout.strip()), 0.5)
    except ValueError:
        return 3.0


def _format_srt_time(seconds: float) -> str:
    ms_total = max(int(round(seconds * 1000)), 0)
    hours, rem = divmod(ms_total, 3600000)
    minutes, rem = divmod(rem, 60000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


async def _synthesize_single_scene(
    text: str,
    voice: str,
    rate: str,
    pitch: str,
    out_mp3: Path,
) -> list[dict[str, Any]]:
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    timings: list[dict[str, Any]] = []
    with out_mp3.open("wb") as audio_fh:
        async for chunk in communicate.stream():
            ctype = chunk.get("type")
            if ctype == "audio":
                audio_fh.write(chunk["data"])
            elif ctype in ("WordBoundary", "SentenceBoundary"):
                offset_sec = float(chunk.get("offset", 0)) / 10_000_000.0
                dur_sec = float(chunk.get("duration", 0)) / 10_000_000.0
                timings.append({
                    "type": ctype,
                    "text": str(chunk.get("text", "")).strip(),
                    "start": offset_sec,
                    "end": offset_sec + max(dur_sec, 0.12),
                })
    return timings


def _create_fallback_silent_audio(out_mp3: Path, duration_sec: float = 4.0) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=24000:cl=mono",
        "-t",
        f"{duration_sec:.2f}",
        "-q:a",
        "9",
        "-acodec",
        "libmp3lame",
        str(out_mp3),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def _chunk_text_into_captions(text: str, start_offset: float, duration: float, words_per_chunk: int = 6) -> list[tuple[float, float, str]]:
    words = text.split()
    if not words:
        return []
    chunks = [" ".join(words[i : i + words_per_chunk]) for i in range(0, len(words), words_per_chunk)]
    total_chars = max(sum(len(c) for c in chunks), 1)
    cursor = start_offset
    entries: list[tuple[float, float, str]] = []
    for c in chunks:
        seg_dur = max(duration * (len(c) / total_chars), 0.45)
        end_t = min(start_offset + duration, cursor + seg_dur)
        entries.append((cursor, max(end_t, cursor + 0.25), c))
        cursor = end_t
    return entries


def _build_srt_entries(
    scene_results: list[SceneAudioResult],
    pause_sec: float,
    words_per_chunk: int = 6,
) -> list[tuple[float, float, str]]:
    entries: list[tuple[float, float, str]] = []
    cursor = 0.0
    for sr in scene_results:
        word_events = [t for t in sr.word_timings if t.get("type") == "WordBoundary" and t.get("text")]
        if word_events:
            for i in range(0, len(word_events), words_per_chunk):
                group = word_events[i : i + words_per_chunk]
                st = cursor + float(group[0]["start"])
                en = cursor + float(group[-1]["end"])
                caption = " ".join(g["text"] for g in group).strip()
                if caption:
                    entries.append((st, max(en, st + 0.3), caption))
        else:
            entries.extend(_chunk_text_into_captions(sr.text, cursor, sr.duration_sec, words_per_chunk=words_per_chunk))
        cursor += sr.duration_sec + pause_sec
    return entries


def _concat_audio_with_pauses(scene_mp3s: list[Path], out_master: Path, pause_sec: float) -> None:
    if len(scene_mp3s) == 1:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(scene_mp3s[0]),
            "-af",
            f"apad=pad_dur={pause_sec:.2f}",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(out_master),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return

    silence_mp3 = out_master.parent / "_pause_silence.mp3"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=24000:cl=mono",
            "-t",
            f"{pause_sec:.2f}",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(silence_mp3),
        ],
        capture_output=True,
        check=True,
    )

    concat_list = out_master.parent / "_audio_concat.txt"
    lines: list[str] = []
    for idx, mp3 in enumerate(scene_mp3s):
        safe = mp3.resolve().as_posix().replace("'", "'\\''")
        lines.append(f"file '{safe}'")
        if idx < len(scene_mp3s) - 1 or pause_sec > 0:
            safe_sil = silence_mp3.resolve().as_posix().replace("'", "'\\''")
            lines.append(f"file '{safe_sil}'")
    concat_list.write_text("\n".join(lines), encoding="utf-8")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(out_master),
        ],
        capture_output=True,
        check=True,
    )
    silence_mp3.unlink(missing_ok=True)
    concat_list.unlink(missing_ok=True)


async def _generate_track_async(
    scenes: list[dict[str, Any]],
    out_dir: Path,
    voice: str,
    rate: str,
    pitch: str,
    pause_sec: float,
    words_per_chunk: int,
) -> TrackAudioBundle:
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_parts_dir = out_dir / "audio_parts"
    audio_parts_dir.mkdir(parents=True, exist_ok=True)

    scene_results: list[SceneAudioResult] = []
    scene_files: list[Path] = []

    for idx, scene in enumerate(scenes, start=1):
        narration = str(scene.get("narration") or "").strip() or f"Bagian {idx}."
        part_mp3 = audio_parts_dir / f"scene_{idx:02d}.mp3"
        timings: list[dict[str, Any]] = []
        try:
            timings = await _synthesize_single_scene(narration, voice, rate, pitch, part_mp3)
            if not part_mp3.exists() or part_mp3.stat().st_size < 256:
                raise RuntimeError("Empty TTS output")
        except Exception:
            est_dur = max(len(narration.split()) / 2.4, 3.0)
            _create_fallback_silent_audio(part_mp3, duration_sec=est_dur)

        dur = probe_duration_sec(part_mp3)
        scene_files.append(part_mp3)
        scene_results.append(
            SceneAudioResult(
                scene_no=idx,
                audio_path=str(part_mp3),
                duration_sec=round(dur, 3),
                text=narration,
                word_timings=timings,
            )
        )

    master_mp3 = out_dir / "voiceover.mp3"
    _concat_audio_with_pauses(scene_files, master_mp3, pause_sec=pause_sec)
    total_dur = probe_duration_sec(master_mp3)

    srt_entries = _build_srt_entries(scene_results, pause_sec=pause_sec, words_per_chunk=words_per_chunk)
    srt_lines: list[str] = []
    for idx, (st, en, text) in enumerate(srt_entries, start=1):
        srt_lines.append(f"{idx}\n{_format_srt_time(st)} --> {_format_srt_time(en)}\n{text}\n")

    srt_path = out_dir / "subtitles.srt"
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")

    # Save timing manifest for debugging/reuse
    manifest = out_dir / "audio_manifest.json"
    bundle = TrackAudioBundle(
        master_audio_path=str(master_mp3),
        srt_path=str(srt_path),
        total_duration_sec=total_dur,
        voice=voice,
        scene_results=scene_results,
    )
    manifest.write_text(json.dumps(bundle.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return bundle


def generate_voiceover_bundle(
    scenes: list[dict[str, Any]],
    out_dir: Path,
    config: dict[str, Any],
    is_short: bool = False,
) -> TrackAudioBundle:
    vo_cfg = config.get("voiceover", {})
    vid_cfg = config.get("video", {}).get("shorts" if is_short else "youtube_long", {})
    voice = vo_cfg.get("voice_shorts" if is_short else "voice_long", "id-ID-ArdiNeural")
    rate = vo_cfg.get("rate_shorts" if is_short else "rate_long", "+5%")
    pitch = vo_cfg.get("pitch", "+0Hz")
    pause_sec = float(vid_cfg.get("padding_after_audio_sec", 0.4 if is_short else 0.6))
    words_per_chunk = 4 if is_short else 7

    return asyncio.run(
        _generate_track_async(
            scenes=scenes,
            out_dir=out_dir,
            voice=voice,
            rate=rate,
            pitch=pitch,
            pause_sec=pause_sec,
            words_per_chunk=words_per_chunk,
        )
    )
