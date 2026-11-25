from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from src.voiceover import TrackAudioBundle


def probe_video_info(video_path: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration,size:stream=codec_type,codec_name,width,height",
        "-of",
        "json",
        str(video_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    info: dict[str, Any] = {
        "path": str(video_path),
        "exists": video_path.exists(),
        "size_mb": round(video_path.stat().st_size / (1024 * 1024), 2) if video_path.exists() else 0.0,
    }
    try:
        parsed = json.loads(res.stdout)
        fmt = parsed.get("format", {})
        info["duration_sec"] = round(float(fmt.get("duration", 0.0)), 2)
        for st in parsed.get("streams", []):
            if st.get("codec_type") == "video":
                info["width"] = st.get("width")
                info["height"] = st.get("height")
                info["video_codec"] = st.get("codec_name")
            elif st.get("codec_type") == "audio":
                info["audio_codec"] = st.get("codec_name")
    except Exception:
        pass
    return info


def _prepare_mixed_audio(
    master_voice: Path,
    duration_sec: float,
    out_audio: Path,
    config: dict[str, Any],
) -> Path:
    """Optionally blend a very subtle, calm royalty-free ambient pad behind the presenter voice."""
    video_root = config.get("video", {})
    if not video_root.get("ambient_bgm", False):
        return master_voice

    vol_db = float(video_root.get("ambient_bgm_volume_db", -27))
    project_root = Path(__file__).resolve().parent.parent
    custom_bgm = project_root / "assets" / "bgm.mp3"
    fade_out_st = max(duration_sec - 2.0, 0.5)

    try:
        if custom_bgm.exists():
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(master_voice),
                "-stream_loop",
                "-1",
                "-i",
                str(custom_bgm),
                "-filter_complex",
                f"[1:a]atrim=0:{duration_sec:.2f},volume={vol_db}dB,afade=t=in:st=0:d=1.2,afade=t=out:st={fade_out_st:.2f}:d=1.8[bgm];"
                "[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[out]",
                "-map",
                "[out]",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                str(out_audio),
            ]
        else:
            # Synthesize a warm, subtle low-passed Cmaj9 ambient pad (100% original, zero copyright risk)
            pad_expr = (
                "0.30*sin(2*PI*130.81*t)+0.22*sin(2*PI*196.00*t)+0.18*sin(2*PI*246.94*t)"
                "+0.14*sin(2*PI*293.66*t)+0.10*sin(2*PI*329.63*t)*(0.85+0.15*sin(2*PI*0.18*t))"
            )
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(master_voice),
                "-f",
                "lavfi",
                "-t",
                f"{duration_sec + 0.5:.2f}",
                "-i",
                f"aevalsrc='{pad_expr}':s=44100:c=stereo",
                "-filter_complex",
                f"[1:a]lowpass=f=480,volume={vol_db}dB,afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_st:.2f}:d=1.8[bgm];"
                "[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[out]",
                "-map",
                "[out]",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                str(out_audio),
            ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        if out_audio.exists() and out_audio.stat().st_size > 1024:
            return out_audio
    except Exception:
        pass
    return master_voice


def build_video_from_scenes(
    scene_images: list[Path],
    audio_bundle: TrackAudioBundle,
    out_video_path: Path,
    config: dict[str, Any],
    is_short: bool = False,
) -> dict[str, Any]:
    video_root = config.get("video", {})
    vid_cfg = video_root.get("shorts" if is_short else "youtube_long", {})
    width = int(vid_cfg.get("width", 1080 if is_short else 1920))
    height = int(vid_cfg.get("height", 1920 if is_short else 1080))
    fps = int(vid_cfg.get("fps", 30))
    burn_subs = bool(vid_cfg.get("burn_subtitles", True))
    pause_sec = float(vid_cfg.get("padding_after_audio_sec", 0.35 if is_short else 0.55))
    ken_burns = bool(video_root.get("ken_burns_motion", True))

    out_dir = out_video_path.parent
    segments_dir = out_dir / "_segments"
    segments_dir.mkdir(parents=True, exist_ok=True)

    segment_paths: list[Path] = []
    for idx, (img_path, scene_audio) in enumerate(zip(scene_images, audio_bundle.scene_results), start=1):
        seg_dur = max(scene_audio.duration_sec + pause_sec, 1.0)
        total_frames = max(int(round(seg_dur * fps)), fps)
        seg_out = segments_dir / f"seg_{idx:02d}.mp4"
        fade_out_start = max(seg_dur - 0.35, 0.2)

        if ken_burns:
            # Smooth documentary Ken Burns motion (alternating subtle zoom-in and zoom-out, zero jitter)
            zoom_span = 0.065
            step = zoom_span / max(total_frames, 1)
            if idx % 2 == 1:
                z_expr = f"min(1.0+{step:.6f}*on,1.07)"
            else:
                z_expr = f"max(1.065-{step:.6f}*on,1.0)"
            up_w = int(width * 1.25)
            up_h = int(height * 1.25)
            vf = (
                f"scale={up_w}:{up_h}:force_original_aspect_ratio=increase,"
                f"crop={up_w}:{up_h},"
                f"zoompan=z='{z_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={width}x{height}:fps={fps},"
                f"fade=t=in:st=0:d=0.35,"
                f"fade=t=out:st={fade_out_start:.2f}:d=0.35,"
                "format=yuv420p"
            )
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(img_path),
                "-vf",
                vf,
                "-t",
                f"{seg_dur:.3f}",
                "-r",
                str(fps),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                "-pix_fmt",
                "yuv420p",
                "-an",
                str(seg_out),
            ]
        else:
            vf = (
                f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},"
                f"fade=t=in:st=0:d=0.30,"
                f"fade=t=out:st={fade_out_start:.2f}:d=0.30,"
                "format=yuv420p"
            )
            cmd = [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-t",
                f"{seg_dur:.3f}",
                "-i",
                str(img_path),
                "-vf",
                vf,
                "-r",
                str(fps),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                "-pix_fmt",
                "yuv420p",
                "-an",
                str(seg_out),
            ]

        subprocess.run(cmd, capture_output=True, text=True, check=True)
        segment_paths.append(seg_out)

    concat_txt = segments_dir / "concat_video.txt"
    concat_lines = [f"file '{p.resolve().as_posix()}'" for p in segment_paths]
    concat_txt.write_text("\n".join(concat_lines), encoding="utf-8")

    merged_silent = segments_dir / "merged_silent.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_txt),
            "-c",
            "copy",
            str(merged_silent),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    srt_file = Path(audio_bundle.srt_path)
    ass_file = Path(audio_bundle.ass_path) if getattr(audio_bundle, "ass_path", "") else None
    master_audio = Path(audio_bundle.master_audio_path)
    mixed_audio_path = segments_dir / "mixed_audio.m4a"
    final_audio = _prepare_mixed_audio(master_audio, audio_bundle.total_duration_sec, mixed_audio_path, config)

    use_ass = (
        bool(video_root.get("animated_ass_subtitles", True))
        and ass_file is not None
        and ass_file.exists()
        and ass_file.stat().st_size > 0
    )

    if burn_subs and use_ass and ass_file is not None:
        cmd_final = [
            "ffmpeg",
            "-y",
            "-i",
            str(merged_silent),
            "-i",
            str(final_audio),
            "-vf",
            f"ass={ass_file.name}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(out_video_path.name),
        ]
        subprocess.run(cmd_final, cwd=str(out_dir), capture_output=True, text=True, check=True)
    elif burn_subs and srt_file.exists() and srt_file.stat().st_size > 0:
        if is_short:
            style = (
                "FontName=Arial,FontSize=16,Bold=1,PrimaryColour=&H00EBF2F5,"
                "OutlineColour=&H00171311,BorderStyle=1,Outline=2.4,Shadow=1.2,"
                "Alignment=2,MarginV=88,MarginL=26,MarginR=26"
            )
        else:
            style = (
                "FontName=Arial,FontSize=17,Bold=1,PrimaryColour=&H00EBF2F5,"
                "OutlineColour=&H00171311,BorderStyle=1,Outline=2.2,Shadow=1.2,"
                "Alignment=2,MarginV=24,MarginL=44,MarginR=44"
            )
        cmd_final = [
            "ffmpeg",
            "-y",
            "-i",
            str(merged_silent),
            "-i",
            str(final_audio),
            "-vf",
            f"subtitles={srt_file.name}:force_style='{style}'",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(out_video_path.name),
        ]
        subprocess.run(cmd_final, cwd=str(out_dir), capture_output=True, text=True, check=True)
    else:
        cmd_final = [
            "ffmpeg",
            "-y",
            "-i",
            str(merged_silent),
            "-i",
            str(final_audio),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(out_video_path),
        ]
        subprocess.run(cmd_final, capture_output=True, text=True, check=True)

    for p in segment_paths:
        p.unlink(missing_ok=True)
    merged_silent.unlink(missing_ok=True)
    mixed_audio_path.unlink(missing_ok=True)
    concat_txt.unlink(missing_ok=True)
    try:
        segments_dir.rmdir()
    except OSError:
        pass

    return probe_video_info(out_video_path)
