from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import wave
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
    engine: str = "edge_tts"


@dataclass
class TrackAudioBundle:
    master_audio_path: str
    srt_path: str
    total_duration_sec: float
    voice: str
    scene_results: list[SceneAudioResult]
    provider: str = "edge_tts"

    def to_dict(self) -> dict[str, Any]:
        return {
            "master_audio_path": self.master_audio_path,
            "srt_path": self.srt_path,
            "total_duration_sec": round(self.total_duration_sec, 3),
            "voice": self.voice,
            "provider": self.provider,
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


def _write_audio_bytes_to_mp3(raw_bytes: bytes, mime_type: str, out_mp3: Path) -> None:
    tmp_raw = out_mp3.with_suffix(".tmp_audio")
    mime_low = (mime_type or "").lower()

    if raw_bytes[:4] == b"RIFF" or "wav" in mime_low:
        tmp_raw = out_mp3.with_suffix(".wav")
        tmp_raw.write_bytes(raw_bytes)
    elif raw_bytes[:3] == b"ID3" or raw_bytes[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2") or "mpeg" in mime_low or "mp3" in mime_low:
        out_mp3.write_bytes(raw_bytes)
        return
    else:
        # Raw Linear PCM from Gemini TTS (typically audio/L16;codec=pcm;rate=24000)
        rate_match = re.search(r"rate=(\d+)", mime_low)
        sample_rate = int(rate_match.group(1)) if rate_match else 24000
        tmp_raw = out_mp3.with_suffix(".wav")
        with wave.open(str(tmp_raw), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(raw_bytes)

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(tmp_raw),
                "-c:a",
                "libmp3lame",
                "-b:a",
                "192k",
                str(out_mp3),
            ],
            capture_output=True,
            check=True,
        )
    finally:
        tmp_raw.unlink(missing_ok=True)


def _discover_gemini_tts_models(client: Any, primary_model: str) -> list[str]:
    base = [
        primary_model,
        "gemini-3.8-flash-tts",
        "gemini-3.8-flash-lite-tts",
        "gemini-2.5-flash-preview-tts",
    ]
    candidates = [m for m in dict.fromkeys(base) if m]
    try:
        discovered = []
        for m in client.models.list():
            mname = (getattr(m, "name", "") or "").replace("models/", "")
            if "tts" in mname.lower() and "gemini" in mname.lower():
                discovered.append(mname)
        for mname in reversed(discovered):
            if mname not in candidates:
                candidates.append(mname)
    except Exception:
        pass
    return candidates


def _synthesize_scene_gemini_tts(
    text: str,
    style_prompt: str,
    voice_name: str,
    tts_models: list[str],
    out_mp3: Path,
) -> tuple[bool, str]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return False, ""

    from google import genai
    from google.genai import types

    prompt_content = f"{style_prompt.strip()}\n\n{text.strip()}" if style_prompt.strip() else text.strip()

    for api_ver in ("v1beta", None):
        client = genai.Client(api_key=api_key, http_options={"api_version": api_ver}) if api_ver else genai.Client(api_key=api_key)
        for model_name in tts_models:
            try:
                cfg = types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name,
                            )
                        )
                    ),
                )
                resp = client.models.generate_content(
                    model=model_name,
                    contents=prompt_content,
                    config=cfg,
                )
                candidates = getattr(resp, "candidates", None) or []
                for cand in candidates:
                    content = getattr(cand, "content", None)
                    parts = getattr(content, "parts", None) or []
                    for part in parts:
                        inline = getattr(part, "inline_data", None)
                        if inline and getattr(inline, "data", None):
                            _write_audio_bytes_to_mp3(
                                raw_bytes=inline.data,
                                mime_type=getattr(inline, "mime_type", "") or "",
                                out_mp3=out_mp3,
                            )
                            if out_mp3.exists() and out_mp3.stat().st_size > 512:
                                return True, model_name
            except Exception as exc:
                print(
                    f"[voiceover] Gemini TTS {model_name} (api={api_ver or 'default'}) failed "
                    f"({type(exc).__name__}): {str(exc)[:180]}",
                    flush=True,
                )
                continue
    return False, ""


async def _synthesize_single_scene_edge(
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


def _concat_audio_with_pauses(scene_mp3s: list[Path], out_master: Path, pause_sec: float, loudnorm: bool = True) -> None:
    af_filter = "loudnorm=I=-16:TP=-1.5:LRA=11" if loudnorm else None

    if len(scene_mp3s) == 1:
        filters = [f"apad=pad_dur={pause_sec:.2f}"]
        if af_filter:
            filters.append(af_filter)
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(scene_mp3s[0]),
            "-af",
            ",".join(filters),
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

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list),
    ]
    if af_filter:
        cmd.extend(["-af", af_filter])
    cmd.extend(["-c:a", "libmp3lame", "-b:a", "192k", str(out_master)])

    subprocess.run(cmd, capture_output=True, check=True)
    silence_mp3.unlink(missing_ok=True)
    concat_list.unlink(missing_ok=True)


async def _generate_track_async(
    scenes: list[dict[str, Any]],
    out_dir: Path,
    config: dict[str, Any],
    is_short: bool,
) -> TrackAudioBundle:
    vo_cfg = config.get("voiceover", {})
    vid_cfg = config.get("video", {}).get("shorts" if is_short else "youtube_long", {})
    desired_provider = str(vo_cfg.get("provider", "gemini_tts")).lower().strip()
    loudnorm = bool(vo_cfg.get("loudnorm", True))

    edge_voice = vo_cfg.get("voice_shorts" if is_short else "voice_long", "en-US-BrianNeural")
    edge_rate = vo_cfg.get("rate_shorts" if is_short else "rate_long", "+0%")
    edge_pitch = vo_cfg.get("pitch", "+0Hz")
    pause_sec = float(vid_cfg.get("padding_after_audio_sec", 0.35 if is_short else 0.55))
    words_per_chunk = 4 if is_short else 7

    gemini_voice = vo_cfg.get("gemini_voice_shorts" if is_short else "gemini_voice_long", "Charon")
    gemini_style = vo_cfg.get("style_prompt_shorts" if is_short else "style_prompt_long", "")
    gemini_primary_model = str(vo_cfg.get("gemini_tts_model", "gemini-3.8-flash-tts"))

    gemini_models: list[str] = []
    use_gemini = desired_provider == "gemini_tts" and bool(os.getenv("GEMINI_API_KEY", "").strip())
    if use_gemini:
        try:
            from google import genai

            c = genai.Client(api_key=os.getenv("GEMINI_API_KEY", "").strip(), http_options={"api_version": "v1beta"})
            gemini_models = _discover_gemini_tts_models(c, gemini_primary_model)
        except Exception:
            gemini_models = [gemini_primary_model, "gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts"]

    out_dir.mkdir(parents=True, exist_ok=True)
    audio_parts_dir = out_dir / "audio_parts"
    audio_parts_dir.mkdir(parents=True, exist_ok=True)

    scene_results: list[SceneAudioResult] = []
    scene_files: list[Path] = []
    used_engine_label = f"edge_tts:{edge_voice}"
    active_gemini_model: str | None = None

    for idx, scene in enumerate(scenes, start=1):
        narration = str(scene.get("narration") or "").strip() or f"Part {idx}."
        part_mp3 = audio_parts_dir / f"scene_{idx:02d}.mp3"
        timings: list[dict[str, Any]] = []
        engine_used = "edge_tts"

        if use_gemini and gemini_models:
            ordered = ([active_gemini_model] + [m for m in gemini_models if m != active_gemini_model]) if active_gemini_model else gemini_models
            ok, used_model = _synthesize_scene_gemini_tts(
                text=narration,
                style_prompt=gemini_style,
                voice_name=gemini_voice,
                tts_models=ordered,
                out_mp3=part_mp3,
            )
            if ok:
                active_gemini_model = used_model
                engine_used = f"gemini_tts:{used_model}:{gemini_voice}"
                used_engine_label = engine_used
                if idx == 1:
                    print(f"[voiceover] Gemini TTS active ({used_model}, voice={gemini_voice})", flush=True)
            else:
                # If scene 1 failed across all Gemini TTS models, disable further pointless retries in this track
                if idx == 1:
                    print("[voiceover] Gemini TTS unavailable; falling back to Edge TTS.", flush=True)
                    use_gemini = False

        if engine_used == "edge_tts":
            try:
                timings = await _synthesize_single_scene_edge(narration, edge_voice, edge_rate, edge_pitch, part_mp3)
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
                engine=engine_used,
            )
        )

    master_mp3 = out_dir / "voiceover.mp3"
    _concat_audio_with_pauses(scene_files, master_mp3, pause_sec=pause_sec, loudnorm=loudnorm)
    total_dur = probe_duration_sec(master_mp3)

    srt_entries = _build_srt_entries(scene_results, pause_sec=pause_sec, words_per_chunk=words_per_chunk)
    srt_lines: list[str] = []
    for idx, (st, en, text) in enumerate(srt_entries, start=1):
        srt_lines.append(f"{idx}\n{_format_srt_time(st)} --> {_format_srt_time(en)}\n{text}\n")

    srt_path = out_dir / "subtitles.srt"
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")

    display_voice = f"{gemini_voice} ({active_gemini_model})" if active_gemini_model else edge_voice
    provider_label = "gemini_tts" if active_gemini_model else "edge_tts"

    manifest = out_dir / "audio_manifest.json"
    bundle = TrackAudioBundle(
        master_audio_path=str(master_mp3),
        srt_path=str(srt_path),
        total_duration_sec=total_dur,
        voice=display_voice,
        scene_results=scene_results,
        provider=provider_label,
    )
    manifest.write_text(json.dumps(bundle.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return bundle


def generate_voiceover_bundle(
    scenes: list[dict[str, Any]],
    out_dir: Path,
    config: dict[str, Any],
    is_short: bool = False,
) -> TrackAudioBundle:
    return asyncio.run(
        _generate_track_async(
            scenes=scenes,
            out_dir=out_dir,
            config=config,
            is_short=is_short,
        )
    )
