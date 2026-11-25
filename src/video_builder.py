from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from src.broll_fetcher import fetch_broll_sequence, fetch_pexels_broll_clip
from src.html_motion_overlay import HtmlOverlayRenderer
from src.motion_engine import render_motion_scene_segment
from src.sfx_engine import mix_cinema_soundscape
from src.vector_2d_engine import render_flat_vector_scene_segment
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


def _build_graded_broll_clip(
    raw_clip: Path,
    clip_dur: float,
    width: int,
    height: int,
    fps: int,
    out_mp4: Path,
    fade_in: bool = False,
    fade_out: bool = False,
) -> Path:
    """Scale, crop, apply fast SIMD Netflix/Aperture dark teal-amber cinema grade."""
    filters = [
        f"scale={width}:{height}:force_original_aspect_ratio=increase:flags=fast_bilinear",
        f"crop={width}:{height}",
        "eq=brightness=-0.11:contrast=1.15:saturation=0.80",
        "colorchannelmixer=rr=0.96:gg=1.01:bb=1.06",
    ]
    if fade_in:
        filters.append("fade=t=in:st=0:d=0.28")
    if fade_out:
        st_out = max(clip_dur - 0.28, 0.15)
        filters.append(f"fade=t=out:st={st_out:.2f}:d=0.28")
    filters.append("format=yuv420p")

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", str(raw_clip),
        "-t", f"{clip_dur:.3f}",
        "-vf", ",".join(filters),
        "-r", str(fps),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22", "-pix_fmt", "yuv420p", "-an",
        str(out_mp4),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return out_mp4


def _build_fast_cut_broll_bed(
    raw_clips: list[Path],
    seg_dur: float,
    width: int,
    height: int,
    fps: int,
    work_dir: Path,
    seg_idx: int,
    cut_interval_sec: float = 4.5,
) -> Path:
    """Assemble fast 4-5s dynamic cinema B-roll cuts for one narration scene."""
    num_cuts = max(1, min(len(raw_clips), int(round(seg_dur / max(cut_interval_sec, 2.5)))))
    sub_dur = seg_dur / float(num_cuts)
    out_bed = work_dir / f"bed_{seg_idx:02d}.mp4"

    if num_cuts == 1:
        return _build_graded_broll_clip(raw_clips[0], seg_dur, width, height, fps, out_bed, fade_in=True, fade_out=True)

    sub_files: list[Path] = []
    for c_i in range(num_cuts):
        sub_out = work_dir / f"bed_{seg_idx:02d}_cut_{c_i:02d}.mp4"
        _build_graded_broll_clip(
            raw_clips[c_i % len(raw_clips)],
            sub_dur,
            width,
            height,
            fps,
            sub_out,
            fade_in=(c_i == 0),
            fade_out=(c_i == num_cuts - 1),
        )
        sub_files.append(sub_out)

    concat_f = work_dir / f"bed_{seg_idx:02d}_concat.txt"
    concat_f.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in sub_files), encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_f), "-c", "copy", str(out_bed)],
        capture_output=True, text=True, check=True,
    )
    for p in sub_files:
        p.unlink(missing_ok=True)
    concat_f.unlink(missing_ok=True)
    return out_bed


def _composite_overlay_onto_broll(broll_mp4: Path, overlay_mov: Path, out_mp4: Path, fps: int) -> Path:
    """Alpha-composite transparent HTML5 Frosted-Glass Vox/Bento overlay onto real cinema B-roll."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(broll_mp4),
        "-i", str(overlay_mov),
        "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1:format=auto[v]",
        "-map", "[v]",
        "-r", str(fps),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21", "-pix_fmt", "yuv420p", "-an",
        str(out_mp4),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return out_mp4


def build_video_from_scenes(
    scene_images: list[Path],
    audio_bundle: TrackAudioBundle,
    out_video_path: Path,
    config: dict[str, Any],
    is_short: bool = False,
    scenes_meta: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    video_root = config.get("video", {})
    vid_cfg = video_root.get("shorts" if is_short else "youtube_long", {})
    width = int(vid_cfg.get("width", 1080 if is_short else 1920))
    height = int(vid_cfg.get("height", 1920 if is_short else 1080))
    fps = int(vid_cfg.get("fps", 30))
    burn_subs = bool(vid_cfg.get("burn_subtitles", True))
    pause_sec = float(vid_cfg.get("padding_after_audio_sec", 0.30 if is_short else 0.45))
    ken_burns = bool(video_root.get("ken_burns_motion", True))
    cut_interval = float(video_root.get("broll_cut_interval_sec", 4.5))
    # Supported Studio video engines:
    #   "cinema_broll_html" (v6 flagship): Real HD/4K B-Roll fast 4-5s cuts + HTML5 Frosted-Glass Vox/Bento Overlays + SFX
    #   "flat_vector_2d"    (v5): Kurzgesagt / TED-Ed 30fps Flat Vector 2D Explainer
    #   "motion_hybrid"     (v4): Programmatic Motion Graphics + Pexels B-Roll
    #   "motion_graphics"   (v4): Pure Programmatic Motion Graphics
    #   "ken_burns_images"  (v3): Full-bleed AI illustrations + Ken Burns
    video_mode = str(video_root.get("engine_mode", "cinema_broll_html")).lower().strip()
    handle = str(config.get("branding", {}).get("watermark_text", "@HabitSains"))

    out_dir = out_video_path.parent
    segments_dir = out_dir / "_segments"
    segments_dir.mkdir(parents=True, exist_ok=True)

    total_scenes = len(audio_bundle.scene_results)
    used_broll_keys: set[str] = set()
    segment_paths: list[Path] = []
    scene_start_times: list[float] = []
    cursor_sec = 0.0

    html_renderer: HtmlOverlayRenderer | None = None
    if video_mode == "cinema_broll_html":
        try:
            html_renderer = HtmlOverlayRenderer(width=width, height=height)
        except Exception as exc:
            print(f"[video] Headless Chrome overlay init failed ({type(exc).__name__}): {exc}; falling back.", flush=True)
            html_renderer = None

    try:
        for idx, scene_audio in enumerate(audio_bundle.scene_results, start=1):
            seg_dur = max(scene_audio.duration_sec + pause_sec, 1.0)
            scene_start_times.append(cursor_sec)
            cursor_sec += seg_dur

            seg_out = segments_dir / f"seg_{idx:02d}.mp4"
            s_meta = (
                scenes_meta[idx - 1]
                if scenes_meta and idx - 1 < len(scenes_meta)
                else {"visual_headline": f"Part {idx}", "narration": scene_audio.text}
            )
            rendered = False

            # --- STUDIO v6 FLAGSHIP: REAL HD CINEMA B-ROLL (FAST 5s CUTS) + HTML5 FROSTED-GLASS OVERLAY ---
            if video_mode == "cinema_broll_html":
                desired_cuts = max(1, min(3, int(round(seg_dur / max(cut_interval, 3.5)))))
                raw_clips = fetch_broll_sequence(s_meta, num_clips=desired_cuts, is_short=is_short, used_keys=used_broll_keys)
                if raw_clips:
                    bed_mp4 = _build_fast_cut_broll_bed(raw_clips, seg_dur, width, height, fps, segments_dir, idx, cut_interval_sec=cut_interval)
                    if html_renderer is not None:
                        ov_mov = segments_dir / f"overlay_{idx:02d}.mov"
                        try:
                            _, ov_style = html_renderer.render_overlay_mov(
                                scene=s_meta,
                                scene_idx=idx,
                                total_scenes=total_scenes,
                                duration_sec=seg_dur,
                                out_mov=ov_mov,
                                handle=handle,
                                is_short=is_short,
                                overlay_fps=16,
                            )
                            print(f"[video] Composited Cinema B-Roll ({len(raw_clips)} cuts) + HTML5 '{ov_style}' overlay ({idx}/{total_scenes})", flush=True)
                            _composite_overlay_onto_broll(bed_mp4, ov_mov, seg_out, fps=fps)
                            ov_mov.unlink(missing_ok=True)
                            bed_mp4.unlink(missing_ok=True)
                            rendered = True
                        except Exception as exc:
                            print(f"[video] HTML5 overlay render failed on scene {idx}: {exc}; using clean cinema B-roll.", flush=True)
                            ov_mov.unlink(missing_ok=True)
                            bed_mp4.replace(seg_out)
                            rendered = True
                    else:
                        bed_mp4.replace(seg_out)
                        rendered = True

            # --- STUDIO v5: FLAT VECTOR 2D KURZGESAGT ---
            if not rendered and video_mode == "flat_vector_2d":
                print(f"[video] Rendering Flat Vector 2D Explainer (30fps) segment {idx}/{total_scenes} ({'9:16' if is_short else '16:9'})...", flush=True)
                render_flat_vector_scene_segment(
                    scene=s_meta, scene_idx=idx, total_scenes=total_scenes,
                    duration_sec=seg_dur, width=width, height=height, fps=fps,
                    out_mp4=seg_out, config=config, is_short=is_short,
                )
                rendered = True

            # --- STUDIO v4: MOTION GRAPHICS + B-ROLL HYBRID ---
            if not rendered and video_mode in ("motion_hybrid", "motion_graphics", "cinema_broll_html"):
                print(f"[video] Rendering 30fps motion graphics fallback segment {idx}/{total_scenes}...", flush=True)
                render_motion_scene_segment(
                    scene=s_meta, scene_idx=idx, total_scenes=total_scenes,
                    duration_sec=seg_dur, width=width, height=height, fps=fps,
                    out_mp4=seg_out, config=config, is_short=is_short,
                )
                rendered = True

            # --- STUDIO v3: ILLUSTRATED KEN BURNS ---
            if not rendered:
                img_path = scene_images[min(idx - 1, len(scene_images) - 1)]
                total_frames = max(int(round(seg_dur * fps)), fps)
                fade_out_start = max(seg_dur - 0.35, 0.2)
                if ken_burns:
                    step = 0.065 / max(total_frames, 1)
                    z_expr = f"min(1.0+{step:.6f}*on,1.07)" if idx % 2 == 1 else f"max(1.065-{step:.6f}*on,1.0)"
                    up_w, up_h = int(width * 1.25), int(height * 1.25)
                    vf = (
                        f"scale={up_w}:{up_h}:force_original_aspect_ratio=increase,crop={up_w}:{up_h},"
                        f"zoompan=z='{z_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={width}x{height}:fps={fps},"
                        f"fade=t=in:st=0:d=0.35,fade=t=out:st={fade_out_start:.2f}:d=0.35,format=yuv420p"
                    )
                    cmd = ["ffmpeg", "-y", "-i", str(img_path), "-vf", vf, "-t", f"{seg_dur:.3f}", "-r", str(fps), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", str(seg_out)]
                else:
                    vf = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fade=t=in:st=0:d=0.30,fade=t=out:st={fade_out_start:.2f}:d=0.30,format=yuv420p"
                    cmd = ["ffmpeg", "-y", "-loop", "1", "-t", f"{seg_dur:.3f}", "-i", str(img_path), "-vf", vf, "-r", str(fps), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", str(seg_out)]
                subprocess.run(cmd, capture_output=True, text=True, check=True)

            segment_paths.append(seg_out)
    finally:
        if html_renderer is not None:
            html_renderer.close()

    concat_txt = segments_dir / "concat_video.txt"
    concat_txt.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in segment_paths), encoding="utf-8")

    merged_silent = segments_dir / "merged_silent.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(merged_silent)],
        capture_output=True, text=True, check=True,
    )

    srt_file = Path(audio_bundle.srt_path)
    ass_file = Path(audio_bundle.ass_path) if getattr(audio_bundle, "ass_path", "") else None
    master_audio = Path(audio_bundle.master_audio_path)
    mixed_audio_path = segments_dir / "mixed_audio.m4a"
    final_audio = mix_cinema_soundscape(
        master_voice=master_audio,
        scene_start_times_sec=scene_start_times,
        duration_sec=audio_bundle.total_duration_sec,
        out_audio=mixed_audio_path,
        config=config,
        work_dir=segments_dir,
    )

    use_ass = (
        bool(video_root.get("animated_ass_subtitles", True))
        and ass_file is not None
        and ass_file.exists()
        and ass_file.stat().st_size > 0
    )

    if burn_subs and use_ass and ass_file is not None:
        cmd_final = [
            "ffmpeg", "-y", "-i", str(merged_silent), "-i", str(final_audio),
            "-vf", f"ass={ass_file.name}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest",
            str(out_video_path.name),
        ]
        subprocess.run(cmd_final, cwd=str(out_dir), capture_output=True, text=True, check=True)
    elif burn_subs and srt_file.exists() and srt_file.stat().st_size > 0:
        style = (
            "FontName=Arial,FontSize=16,Bold=1,PrimaryColour=&H00EBF2F5,OutlineColour=&H00171311,BorderStyle=1,Outline=2.4,Shadow=1.2,Alignment=2,MarginV=88,MarginL=26,MarginR=26"
            if is_short
            else "FontName=Arial,FontSize=17,Bold=1,PrimaryColour=&H00EBF2F5,OutlineColour=&H00171311,BorderStyle=1,Outline=2.2,Shadow=1.2,Alignment=2,MarginV=24,MarginL=44,MarginR=44"
        )
        cmd_final = [
            "ffmpeg", "-y", "-i", str(merged_silent), "-i", str(final_audio),
            "-vf", f"subtitles={srt_file.name}:force_style='{style}'",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest",
            str(out_video_path.name),
        ]
        subprocess.run(cmd_final, cwd=str(out_dir), capture_output=True, text=True, check=True)
    else:
        cmd_final = [
            "ffmpeg", "-y", "-i", str(merged_silent), "-i", str(final_audio),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest",
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
