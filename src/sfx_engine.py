"""Procedural Royalty-Free Cinema Sound Design Engine (Whoosh Transitions + UI Pop + Ambient Score)."""

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


def mix_cinema_soundscape(
    master_voice: Path,
    scene_start_times_sec: list[float],
    duration_sec: float,
    out_audio: Path,
    config: dict[str, Any],
    work_dir: Path,
) -> Path:
    """Mix presenter voiceover + subtle warm ambient score + cinema whoosh/pop SFX at exact cut points."""
    video_root = config.get("video", {})
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
            # Limit SFX events cleanly so FFmpeg filter graph stays lean & snappy
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

        cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filter_parts), "-map", "[out]", "-c:a", "aac", "-b:a", "192k", str(out_audio)]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        if out_audio.exists() and out_audio.stat().st_size > 1024:
            return out_audio
    except Exception as exc:
        print(f"[sfx] Cinema soundscape fallback ({type(exc).__name__}): {str(exc)[:140]}", flush=True)
    finally:
        whoosh_wav.unlink(missing_ok=True)
        pop_wav.unlink(missing_ok=True)

    return master_voice
