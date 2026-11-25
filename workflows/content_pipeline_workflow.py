"""Antigravity Multi-Agent Content Automation Workflow (`run_workflow`).

Orchestrates specialized agents in parallel:
  1. Trend Strategist -> researches fresh non-duplicate topic
  2. Parallel Specialist Writers -> YouTube Long, Short-form Vertical, Social Carousel/Copy
  3. Production Engineer -> merges blueprint JSON and runs local TTS/Visual/FFmpeg/Auto-Draft pipeline
  4. QA Reviewer -> verifies report.json and summarizes results

Run via Antigravity `run_workflow` tool with:
  ScriptPath="C:/Users/Administrator/.gemini/antigravity/scratch/content-automation-studio/workflows/content_pipeline_workflow.py"
  Args={"topic": "", "publish_mode": "draft"}
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\Administrator\.gemini\antigravity\scratch\content-automation-studio")
requested_topic = (args or {}).get("topic", "").strip()
publish_mode = (args or {}).get("publish_mode", "draft").strip() or "draft"

phase("1. Trend Research & Ideation")
idea = await agent(
    f"""Baca konfigurasi channel di {PROJECT_ROOT / 'config' / 'channel_config.yaml'} dan riwayat di {PROJECT_ROOT / 'output' / 'history.json'} (jika ada).
{'Gunakan topik yang diminta user: ' + requested_topic if requested_topic else 'Cari 1 tren terbaru yang relevan dengan niche channel via search_web dan belum pernah dipakai di history.json.'}
Kembalikan JSON berisi: topic, angle, hook, source, keywords (array 5-7 string), channel_name, channel_handle, language.""",
    schema={
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "angle": {"type": "string"},
            "hook": {"type": "string"},
            "source": {"type": "string"},
            "keywords": {"type": "array", "items": {"type": "string"}},
            "channel_name": {"type": "string"},
            "channel_handle": {"type": "string"},
            "language": {"type": "string"},
        },
        "required": ["topic", "angle", "hook", "keywords"],
    },
    role="Trend Strategist",
)
log(f"Selected topic: {idea['topic']}")

phase("2. Parallel Multi-Format Scripting & Repurposing")

yt_long_task = {
    "key": "youtube_long",
    "role": "YouTube Long Scriptwriter",
    "prompt": f"""Tulis paket script YouTube Panjang (16:9) dalam bahasa {idea.get('language', 'id')} untuk topik:
{json.dumps(idea, ensure_ascii=False)}
Wajib 5 scene terstruktur (Hook, Masalah, Framework, Praktik, CTA). Kembalikan JSON sesuai schema.""",
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "alt_titles": {"type": "array", "items": {"type": "string"}},
            "description": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "thumbnail": {
                "type": "object",
                "properties": {
                    "badge": {"type": "string"},
                    "headline": {"type": "string"},
                    "subheadline": {"type": "string"},
                    "visual_prompt": {"type": "string"},
                },
                "required": ["badge", "headline", "subheadline", "visual_prompt"],
            },
            "scenes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "scene_no": {"type": "integer"},
                        "section": {"type": "string"},
                        "visual_headline": {"type": "string"},
                        "bullet_points": {"type": "array", "items": {"type": "string"}},
                        "on_screen_callout": {"type": "string"},
                        "narration": {"type": "string"},
                        "visual_prompt": {"type": "string"},
                    },
                    "required": ["scene_no", "section", "visual_headline", "bullet_points", "narration"],
                },
            },
        },
        "required": ["title", "alt_titles", "description", "tags", "thumbnail", "scenes"],
    },
}

shorts_task = {
    "key": "shorts_reels_tiktok",
    "role": "Short-Form Viral Writer",
    "prompt": f"""Repurpose topik berikut menjadi script video pendek vertikal 9:16 (< 50 detik total baca, tepat 4 scene cepat) untuk YouTube Shorts, TikTok, dan Instagram Reels:
{json.dumps(idea, ensure_ascii=False)}
Kembalikan JSON sesuai schema.""",
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "hook_text": {"type": "string"},
            "caption_yt_shorts": {"type": "string"},
            "caption_tiktok": {"type": "string"},
            "caption_ig_reels": {"type": "string"},
            "hashtags": {"type": "array", "items": {"type": "string"}},
            "scenes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "scene_no": {"type": "integer"},
                        "badge": {"type": "string"},
                        "visual_headline": {"type": "string"},
                        "narration": {"type": "string"},
                        "visual_prompt": {"type": "string"},
                    },
                    "required": ["scene_no", "badge", "visual_headline", "narration"],
                },
            },
        },
        "required": ["title", "hook_text", "caption_yt_shorts", "caption_tiktok", "caption_ig_reels", "hashtags", "scenes"],
    },
}

carousel_task = {
    "key": "carousel_social",
    "role": "Social Carousel & Copy Strategist",
    "prompt": f"""Repurpose topik berikut menjadi paket Carousel 5 slide + copywriting Instagram, LinkedIn, Thread X (5 tweet), Threads, dan Facebook:
{json.dumps(idea, ensure_ascii=False)}
Kembalikan JSON sesuai schema.""",
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "slides": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "slide_no": {"type": "integer"},
                        "badge": {"type": "string"},
                        "headline": {"type": "string"},
                        "body": {"type": "string"},
                        "highlight": {"type": "string"},
                        "visual_prompt": {"type": "string"},
                    },
                    "required": ["slide_no", "badge", "headline", "body", "highlight"],
                },
            },
            "caption_instagram": {"type": "string"},
            "caption_linkedin": {"type": "string"},
            "thread_x": {"type": "array", "items": {"type": "string"}},
            "post_threads": {"type": "string"},
            "post_facebook": {"type": "string"},
            "hashtags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["title", "slides", "caption_instagram", "caption_linkedin", "thread_x", "post_threads", "post_facebook", "hashtags"],
    },
}

results = await parallel(
    [yt_long_task, shorts_task, carousel_task],
    lambda t: agent(t["prompt"], schema=t["schema"], role=t["role"]),
)

blueprint = {
    "meta": idea,
    "youtube_long": results[0],
    "shorts_reels_tiktok": results[1],
    "carousel_social": results[2],
}

brief_file = PROJECT_ROOT / "output" / "_workflow_brief.json"
brief_file.parent.mkdir(parents=True, exist_ok=True)
brief_file.write_text(json.dumps(blueprint, ensure_ascii=False, indent=2), encoding="utf-8")
log(f"Merged multi-agent blueprint saved to {brief_file}")

phase("3. Render Media, Auto-Draft & Publish Report")
final_report = await agent(
    f"""Jalankan pipeline produksi di {PROJECT_ROOT} dengan perintah:
python -m src.pipeline --brief "{brief_file}" --publish-mode {publish_mode}
Setelah selesai, baca PUBLISH_REPORT.md yang dihasilkan dan kembalikan ringkasan eksekutif beserta path laporan.""",
    schema={
        "type": "object",
        "properties": {
            "run_id": {"type": "string"},
            "report_md": {"type": "string"},
            "qa_passed_all": {"type": "boolean"},
            "summary": {"type": "string"},
        },
        "required": ["run_id", "report_md", "qa_passed_all", "summary"],
    },
    role="Production & Publish Engineer",
)

log(f"Completed run {final_report['run_id']} | QA Passed: {final_report['qa_passed_all']}")
print(json.dumps(final_report, ensure_ascii=False, indent=2))
