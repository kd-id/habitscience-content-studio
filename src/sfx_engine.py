"""Procedural Royalty-Free Sound Design Engine (100% Instrument-Free Nature Soundscapes + Legacy Cinema Mode)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _generate_whoosh_wav(out_wav: Path) -> Path:
    """Soft, clean cinema transition whoosh (bandpassed pink-noise swell, 0.42s)."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "anoisesrc=color=pink:sample_rate=44100:duration=0.42",
        "-af", "bandpass=f=480:width_type=h:w=360,afade=t=in:st=0:d=0.16,afade=t=out:st=0.20:d=0.22,volume=-18dB",
        "-c:a", "pcm_s16le",
        str(out_wav),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return out_wav


def _generate_ui_pop_wav(out_wav: Path) -> Path:
    """Crisp, subtle Apple-style UI glass pop (0.09s)."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "aevalsrc='0.7*sin(2*PI*(520+900*t)*t)*exp(-38*t)':s=44100:d=0.09",
        "-af", "lowpass=f=2200,volume=-16dB",
        "-c:a", "pcm_s16le",
        str(out_wav),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return out_wav


def _nature_bed_spec(preset: str, duration_sec: float, vol_db: float) -> tuple[list[str], str]:
    """Build 100% instrument-free natural soundscape (zero musical notes, zero drums, zero synths).

    Presets:
      - dawn_breeze : Soft early-morning Fajr wind & warm air flow
      - gentle_rain : Peaceful distant soft rain ambiance
      - calm_water  : Tranquil flowing stream / gentle ocean tide
    """
    dur = max(duration_sec + 0.5, 2.0)
    fade_out_st = max(duration_sec - 2.0, 0.4)
    p = (preset or "dawn_breeze").lower().strip()

    if p == "gentle_rain":
        inp = ["-f", "lavfi", "-t", f"{dur:.2f}", "-i", "anoisesrc=color=pink:sample_rate=48000"]
        flt = (
            f"highpass=f=260,lowpass=f=2600,aformat=channel_layouts=stereo,"
            f"tremolo=f=0.14:d=0.28,volume={vol_db:.1f}dB,"
            f"afade=t=in:st=0:d=1.4,afade=t=out:st={fade_out_st:.2f}:d=1.8"
        )
        return inp, flt

    if p == "calm_water":
        inp = ["-f", "lavfi", "-t", f"{dur:.2f}", "-i", "anoisesrc=color=brown:sample_rate=48000"]
        flt = (
            f"highpass=f=110,lowpass=f=1250,aformat=channel_layouts=stereo,"
            f"tremolo=f=0.18:d=0.42,volume={vol_db + 1.5:.1f}dB,"
            f"afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_st:.2f}:d=1.8"
        )
        return inp, flt

    # Default: dawn_breeze (airy morning wind, super calm behind spoken narration)
    inp = ["-f", "lavfi", "-t", f"{dur:.2f}", "-i", "anoisesrc=color=pink:sample_rate=48000"]
    flt = (
        f"highpass=f=140,lowpass=f=980,aformat=channel_layouts=stereo,"
        f"tremolo=f=0.11:d=0.38,volume={vol_db + 1.0:.1f}dB,"
        f"afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_st:.2f}:d=1.8"
    )
    return inp, flt


def mix_nature_voice_soundscape(
    master_voice: Path,
    duration_sec: float,
    out_audio: Path,
    config: dict[str, Any],
    preset: str = "dawn_breeze",
    tempo: float = 1.0,
) -> Path:
    """Mix narrator voiceover with 100% instrument-free nature ambiance (48kHz stereo AAC, Meta/YT safe)."""
    video_root = config.get("video", {})
    enable_bgm = bool(video_root.get("ambient_bgm", True))
    vol_db = float(video_root.get("ambient_bgm_volume_db", -27))

    voice_af_parts = ["aformat=sample_rates=48000:channel_layouts=stereo"]
    if tempo and abs(tempo - 1.0) > 0.01:
        clamped = min(max(tempo, 0.8), 1.35)
        voice_af_parts.insert(0, f"atempo={clamped:.4f}")
    voice_af_parts.append("volume=+0.8dB")
    voice_af = ",".join(voice_af_parts)

    if not enable_bgm:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(master_voice),
                "-af", voice_af,
                "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k",
                str(out_audio),
            ],
            capture_output=True, text=True, check=True,
        )
        return out_audio

    try:
        nature_in, nature_flt = _nature_bed_spec(preset=preset, duration_sec=duration_sec, vol_db=vol_db)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(master_voice),
            *nature_in,
            "-filter_complex",
            (
                f"[0:a]{voice_af}[vo];"
                f"[1:a]{nature_flt}[nat];"
                "[vo][nat]amix=inputs=2:duration=first:dropout_transition=2:normalize=0,"
                "alimiter=limit=0.95[out]"
            ),
            "-map", "[out]",
            "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k",
            str(out_audio),
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        if out_audio.exists() and out_audio.stat().st_size > 1024:
            return out_audio
    except Exception as exc:
        print(f"[sfx] Nature soundscape fallback ({type(exc).__name__}): {str(exc)[:140]}", flush=True)

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(master_voice),
            "-af", voice_af,
            "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k",
            str(out_audio),
        ],
        capture_output=True, text=True, check=True,
    )
    return out_audio


def mix_cinema_soundscape(
    master_voice: Path,
    scene_start_times_sec: list[float],
    duration_sec: float,
    out_audio: Path,
    config: dict[str, Any],
    work_dir: Path,
) -> Path:
    """Mix presenter voiceover + subtle ambiance (respects `ambient_bgm_mode: nature_only` for 100% instrument-free audio)."""
    video_root = config.get("video", {})
    bgm_mode = str(video_root.get("ambient_bgm_mode", "nature_only")).lower().strip()
    if bgm_mode == "nature_only":
        preset = str(video_root.get("nature_preset", "dawn_breeze")).strip()
        return mix_nature_voice_soundscape(
            master_voice=master_voice,
            duration_sec=duration_sec,
            out_audio=out_audio,
            config=config,
            preset=preset,
        )

    enable_bgm = bool(video_root.get("ambient_bgm", True))
    enable_sfx = bool(video_root.get("cinema_sfx", True))
    if not enable_bgm and not enable_sfx:
        return master_voice

    vol_db = float(video_root.get("ambient_bgm_volume_db", -26))
    project_root = Path(__file__).resolve().parent.parent
    custom_bgm = project_root / "assets" / "bgm.mp3"
    fade_out_st = max(duration_sec - 2.0, 0.5)

    whoosh_wav = work_dir / "_sfx_whoosh.wav"
    pop_wav = work_dir / "_sfx_pop.wav"

    try:
        inputs: list[str] = ["-i", str(master_voice)]
        filter_parts: list[str] = []
        mix_labels: list[str] = ["[0:a]"]
        next_idx = 1

        if enable_bgm:
            if custom_bgm.exists():
                inputs.extend(["-stream_loop", "-1", "-i", str(custom_bgm)])
                filter_parts.append(
                    f"[{next_idx}:a]atrim=0:{duration_sec:.2f},volume={vol_db}dB,"
                    f"afade=t=in:st=0:d=1.2,afade=t=out:st={fade_out_st:.2f}:d=1.8[bgm]"
                )
            else:
                pad_expr = (
                    "0.28*sin(2*PI*130.81*t)+0.22*sin(2*PI*196.00*t)+0.18*sin(2*PI*246.94*t)"
                    "+0.14*sin(2*PI*293.66*t)+0.10*sin(2*PI*329.63*t)*(0.85+0.15*sin(2*PI*0.18*t))"
                )
                inputs.extend(["-f", "lavfi", "-t", f"{duration_sec + 0.5:.2f}", "-i", f"aevalsrc='{pad_expr}':s=44100:c=stereo"])
                filter_parts.append(
                    f"[{next_idx}:a]lowpass=f=460,volume={vol_db}dB,"
                    f"afade=t=in:st=0:d=1.4,afade=t=out:st={fade_out_st:.2f}:d=1.8[bgm]"
                )
            mix_labels.append("[bgm]")
            next_idx += 1

        if enable_sfx and scene_start_times_sec:
            _generate_whoosh_wav(whoosh_wav)
            _generate_ui_pop_wav(pop_wav)
            for s_i, st_sec in enumerate(scene_start_times_sec[:10]):
                delay_ms = max(int(round(st_sec * 1000)), 0)
                if s_i > 0:
                    inputs.extend(["-i", str(whoosh_wav)])
                    lbl = f"sfxw{s_i}"
                    filter_parts.append(f"[{next_idx}:a]adelay={delay_ms}|{delay_ms}[{lbl}]")
                    mix_labels.append(f"[{lbl}]")
                    next_idx += 1
                pop_ms = delay_ms + 350
                inputs.extend(["-i", str(pop_wav)])
                lbl_p = f"sfxp{s_i}"
                filter_parts.append(f"[{next_idx}:a]adelay={pop_ms}|{pop_ms}[{lbl_p}]")
                mix_labels.append(f"[{lbl_p}]")
                next_idx += 1

        filter_parts.append(
            f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:dropout_transition=2:normalize=0[out]"
        )

        cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filter_parts), "-map", "[out]", "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", str(out_audio)]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        if out_audio.exists() and out_audio.stat().st_size > 1024:
            return out_audio
    except Exception as exc:
        print(f"[sfx] Cinema soundscape fallback ({type(exc).__name__}): {str(exc)[:140]}", flush=True)
    finally:
        whoosh_wav.unlink(missing_ok=True)
        pop_wav.unlink(missing_ok=True)

    return master_voice
