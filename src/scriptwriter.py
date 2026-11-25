from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_loader import slugify
from src.ideation import TopicIdea


def _build_gemini_prompt(idea: TopicIdea, config: dict[str, Any]) -> str:
    channel = config.get("channel", {})
    lang = channel.get("language", "en")
    if lang == "en":
        return f"""You are a Lead YouTube Creative Director, Charismatic Science Presenter Scriptwriter (think Johnny Harris meets Kurzgesagt and Ali Abdaal), and Multi-Platform Growth Strategist.
Create an original, high-retention Master Content Blueprint in vivid, conversational spoken English that repurposes 1 validated idea across ALL platforms while strictly avoiding robotic or repetitive templates.

Channel Profile:
- Name: {channel.get('name')} ({channel.get('handle')})
- Niche: {channel.get('niche')}
- Target Audience: {channel.get('target_audience')}
- Tone: {channel.get('tone')}
- YouTube CTA: {channel.get('cta_youtube')}
- Social CTA: {channel.get('cta_social')}

Core Idea:
- Topic: {idea.topic}
- Unique Angle: {idea.angle}
- Opening Hook: {idea.hook}
- Keywords: {", ".join(idea.keywords or [])}

Storytelling & Narration Rules (CRITICAL):
- Write as a charismatic human presenter talking directly to ONE viewer ("you"), using rhetorical questions, vivid relatable scenarios, short punchy rhythm changes, and natural pauses.
- NEVER write stiff textbook prose or dry bullet readings.
- Every scene MUST have a completely distinct, vivid, dramatic visual storytelling metaphor in `visual_prompt` (objects, characters, lighting, symbolic environments — strictly NO text/letters).

Return ONLY valid JSON with this exact schema:
{{
  "youtube_long": {{
    "title": "High-CTR curiosity + benefit title (max 68 chars)",
    "alt_titles": ["A/B Alt 1", "A/B Alt 2", "A/B Alt 3"],
    "description": "Engaging YouTube description with story hook, research takeaways, chapter timestamps, CTA, and hashtags",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
    "thumbnail": {{
      "badge": "SHORT BADGE (2-3 words)",
      "headline": "PUNCHY THUMBNAIL TEXT (2-4 words)",
      "subheadline": "Short curiosity subtitle (4-7 words)",
      "visual_prompt": "Dramatic cinematic illustrated storytelling thumbnail concept placed on the RIGHT half, rich volumetric lighting, strictly NO text"
    }},
    "scenes": [
      {{
        "scene_no": 1,
        "section": "HOOK / THE STORY / BRAIN MECHANISM / HIDDEN TRAP / SHIFT 1 / SHIFT 2 / SHIFT 3 / 7-DAY CHALLENGE",
        "visual_headline": "Crisp short editorial title (max 6 words)",
        "bullet_points": ["Point 1", "Point 2", "Point 3"],
        "on_screen_callout": "1-line punchy insight",
        "narration": "Engaging presenter storytelling narration, 2-3 vivid spoken sentences (~12-16 seconds when spoken).",
        "visual_prompt": "Distinct cinematic illustrated storytelling metaphor for this exact beat (Kurzgesagt / Johnny Harris / Aperture art vibe, strictly NO text/letters)"
      }}
    ]
  }},
  "shorts_reels_tiktok": {{
    "title": "Punchy curiosity vertical title",
    "hook_text": "3-second visual hook",
    "caption_yt_shorts": "YouTube Shorts caption + hashtags",
    "caption_tiktok": "TikTok caption + comment trigger + hashtags",
    "caption_ig_reels": "Instagram Reels caption + save/share CTA + hashtags",
    "hashtags": ["#Neuroscience", "#Focus", "#HabitScience", "#DeepWork", "#Productivity"],
    "scenes": [
      {{
        "scene_no": 1,
        "badge": "01 • HOOK",
        "visual_headline": "Short punchy vertical hook (max 5 words)",
        "narration": "Fast, charismatic 1-2 sentence spoken beat (~6-8 seconds).",
        "visual_prompt": "Distinct vertical 9:16 cinematic illustrated storytelling scene (strictly NO text/letters)"
      }}
    ]
  }},
  "carousel_social": {{
    "title": "Carousel title",
    "slides": [
      {{
        "slide_no": 1,
        "badge": "SLIDE 1/5 • COVER",
        "headline": "High-curiosity cover headline",
        "body": "Concise 1-2 sentence insight",
        "highlight": "Key takeaway or metric",
        "visual_prompt": "Dramatic editorial illustration concept for this slide"
      }}
    ],
    "caption_instagram": "Storytelling Instagram carousel caption + save CTA + hashtags",
    "caption_linkedin": "Insightful LinkedIn post with structured bullets + discussion question",
    "thread_x": ["1/5 Hook tweet + 🧵", "2/5 Insight", "3/5 Mechanism", "4/5 Protocol", "5/5 CTA"],
    "post_threads": "Short conversational Threads post",
    "post_facebook": "Engaging Facebook Page post",
    "hashtags": ["#HabitScience", "#Neuroscience", "#Focus", "#DeepWork"]
  }}
}}

Strict beat counts for fast, engaging visual pacing:
- youtube_long.scenes MUST have 8 distinct visual beats (~12-16s each, total ~2 minutes of captivating storytelling).
- shorts_reels_tiktok.scenes MUST have 6 punchy vertical beats (~6-8s each, total ~38-48 seconds, strictly under 58 seconds).
- carousel_social.slides MUST have exactly 5 slides (Cover, 3 Core Science Insights, Actionable CTA).
"""

    lang_label = "Bahasa Indonesia"
    return f"""Kamu adalah Creative Director, YouTube Scriptwriter, dan Social Media Growth Strategist.
Buat Master Content Blueprint lengkap dalam {lang_label} untuk repurpose 1 ide menjadi SEMUA format sekaligus.

Profil Channel:
- Nama: {channel.get('name')} ({channel.get('handle')})
- Niche: {channel.get('niche')}
- Audiens: {channel.get('target_audience')}
- Gaya bahasa: {channel.get('tone')}
- CTA YouTube: {channel.get('cta_youtube')}
- CTA Sosmed: {channel.get('cta_social')}

Ide Utama:
- Topik: {idea.topic}
- Sudut pandang (Angle): {idea.angle}
- Hook awal: {idea.hook}
- Kata kunci: {", ".join(idea.keywords or [])}

Kembalikan HANYA JSON valid dengan struktur persis seperti ini:
{{
  "youtube_long": {{
    "title": "Judul utama SEO + CTR tinggi (max 70 karakter)",
    "alt_titles": ["Alternatif 1", "Alternatif 2", "Alternatif 3"],
    "description": "Deskripsi YouTube lengkap dengan ringkasan, poin penting, CTA, dan hashtag",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
    "thumbnail": {{
      "badge": "LABEL SINGKAT (2-3 kata)",
      "headline": "TEKS THUMBNAIL PUNCHY (3-5 kata)",
      "subheadline": "Subteks pendek (4-7 kata)",
      "visual_prompt": "Prompt visual thumbnail cinematic high contrast"
    }},
    "scenes": [
      {{
        "scene_no": 1,
        "section": "HOOK / INTRO / LANGKAH 1 / LANGKAH 2 / STUDI KASUS / CTA",
        "visual_headline": "Judul singkat di layar (max 8 kata)",
        "bullet_points": ["Poin layar 1", "Poin layar 2", "Poin layar 3"],
        "on_screen_callout": "Highlight singkat 1 baris",
        "narration": "Naskah voiceover natural, mengalir, 2-4 kalimat untuk diucapkan narator.",
        "visual_prompt": "Deskripsi visual untuk scene ini"
      }}
    ]
  }},
  "shorts_reels_tiktok": {{
    "title": "Judul Shorts/Reels/TikTok punchy",
    "hook_text": "Teks hook besar 3 detik pertama",
    "caption_yt_shorts": "Caption khusus YouTube Shorts + hashtag",
    "caption_tiktok": "Caption khusus TikTok + CTA komentar + hashtag",
    "caption_ig_reels": "Caption khusus Instagram Reels + CTA save/share + hashtag",
    "hashtags": ["#AI", "#KontenKreator", "#Automasi", "#YouTubeShorts", "#TipsKonten"],
    "scenes": [
      {{
        "scene_no": 1,
        "badge": "01 HOOK",
        "visual_headline": "Headline vertikal singkat",
        "narration": "Narasi padat & cepat 1-2 kalimat.",
        "visual_prompt": "Deskripsi visual 9:16"
      }}
    ]
  }},
  "carousel_social": {{
    "title": "Judul Carousel",
    "slides": [
      {{
        "slide_no": 1,
        "badge": "SLIDE 1/5 • COVER",
        "headline": "Headline cover menarik perhatian",
        "body": "Penjelasan ringkas dan tajam 1-2 kalimat",
        "highlight": "Takeaway / angka kunci",
        "visual_prompt": "Konsep ilustrasi slide"
      }}
    ],
    "caption_instagram": "Caption Instagram carousel storytelling + CTA save & comment + hashtag",
    "caption_linkedin": "Postingan LinkedIn profesional dengan insight terstruktur + pertanyaan diskusi",
    "thread_x": ["Tweet 1 (Hook + 🧵)", "Tweet 2", "Tweet 3", "Tweet 4", "Tweet 5 (CTA)"],
    "post_threads": "Postingan pendek conversational untuk Threads",
    "post_facebook": "Caption ramah diskusi untuk Facebook Page",
    "hashtags": ["#ContentAutomation", "#AIUntukKreator", "#StrategiKonten", "#Produktivitas"]
  }}
}}

Aturan penting:
- youtube_long.scenes HARUS berisi 5 scene terstruktur (Hook, Masalah & Peluang, Framework 3 Tahap, Eksekusi Praktis, Ringkasan & CTA).
- shorts_reels_tiktok.scenes HARUS berisi 4 scene cepat (Hook, Masalah, Solusi Inti, CTA) dengan total durasi baca ~35-50 detik.
- carousel_social.slides HARUS berisi tepat 5 slide (Cover, 3 Insight Inti, Penutup & CTA).
"""


def _strip_json_fences(raw_text: str) -> str:
    txt = (raw_text or "").strip()
    if txt.startswith("```"):
        lines = txt.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        txt = "\n".join(lines).strip()
    return txt


def _generate_with_gemini(idea: TopicIdea, config: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[scriptwriter] GEMINI_API_KEY not set; using local fallback.", flush=True)
        return None, ""

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    ai_cfg = config.get("ai", {})
    primary_model = str(ai_cfg.get("text_model", "gemini-3.8-flash")).strip()
    candidate_models = list(dict.fromkeys([primary_model, "gemini-3.8-flash", "gemini-3.0-flash", "gemini-2.5-flash"]))
    prompt = _build_gemini_prompt(idea, config)
    temp = float(ai_cfg.get("temperature", 0.7))

    def _try_model(model_name: str) -> dict[str, Any] | None:
        resp = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=temp,
            ),
        )
        cleaned = _strip_json_fences(resp.text or "")
        parsed = json.loads(cleaned)
        if all(k in parsed for k in ("youtube_long", "shorts_reels_tiktok", "carousel_social")):
            return parsed
        print(f"[scriptwriter] Gemini model {model_name} returned incomplete keys: {list(parsed.keys())}", flush=True)
        return None

    for model_name in candidate_models:
        try:
            parsed = _try_model(model_name)
            if parsed is not None:
                print(f"[scriptwriter] Gemini API succeeded with model: {model_name}", flush=True)
                return parsed, model_name
        except Exception as exc:
            print(f"[scriptwriter] Gemini model {model_name} failed ({type(exc).__name__}): {exc}", flush=True)
            continue

    # Auto-discover latest available Gemini Flash model if hardcoded names ever deprecate
    try:
        discovered = []
        for m in client.models.list():
            mname = getattr(m, "name", "") or ""
            methods = getattr(m, "supported_actions", None) or getattr(m, "supported_generation_methods", None) or []
            if "gemini" in mname.lower() and "flash" in mname.lower() and (not methods or any("generateContent" in str(a) for a in methods)):
                discovered.append(mname.replace("models/", ""))
        for model_name in reversed(discovered[-4:]):
            if model_name in candidate_models:
                continue
            try:
                parsed = _try_model(model_name)
                if parsed is not None:
                    print(f"[scriptwriter] Gemini API succeeded with auto-discovered model: {model_name}", flush=True)
                    return parsed, model_name
            except Exception as exc:
                print(f"[scriptwriter] Auto-discovered model {model_name} failed ({type(exc).__name__}): {exc}", flush=True)
    except Exception as exc:
        print(f"[scriptwriter] Model discovery failed: {exc}", flush=True)

    return None, ""


def _truncate_words(text: str, max_len: int) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_len:
        return clean
    clipped = clean[: max_len - 1].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return (clipped or clean[: max_len - 3]) + "..."


def _build_english_fallback(idea: TopicIdea, config: dict[str, Any]) -> dict[str, Any]:
    channel = config.get("channel", {})
    topic = idea.topic
    cta_yt = channel.get("cta_youtube", "Subscribe for science-backed focus and habit protocols every week.")
    cta_soc = channel.get("cta_social", "Save this post and comment 'PROTOCOL' for the checklist.")
    short_title = _truncate_words(topic, 58)
    short_sub = _truncate_words(topic, 48)
    keywords = idea.keywords or ["neuroscience", "focus", "habits", "deep work", "productivity"]
    hashtags_list = [f"#{slugify(k, 22).replace('-', '')}" for k in keywords[:4] if slugify(k, 22)]
    for tag in ("#Neuroscience", "#Focus", "#HabitScience"):
        if tag not in hashtags_list:
            hashtags_list.append(tag)

    return {
        "youtube_long": {
            "title": f"{short_title} (Science Explained)",
            "alt_titles": [
                f"The Neuroscience Behind {short_sub}",
                f"{short_title} — The 3-Step Protocol",
                f"Why Most People Miss This: {short_sub}",
            ],
            "description": (
                f"{idea.hook}\n\n"
                f"In this episode of {channel.get('name', 'HabitScience Lab')}, we break down {topic} through a practical, science-backed lens for {channel.get('target_audience', 'ambitious learners')}.\n\n"
                "Chapters:\n"
                "00:00 The Core Problem\n"
                "00:18 Part 1: The Brain Mechanism\n"
                "00:38 Part 2: The Hidden Trap\n"
                "00:58 Part 3: The 3-Step Lab Protocol\n"
                "01:18 Your 7-Day Experiment\n\n"
                f"{cta_yt}\n\n"
                + " ".join(hashtags_list)
            ),
            "tags": list(dict.fromkeys(keywords + ["neuroscience of focus", "habit science", "deep work", "brain performance"])),
            "thumbnail": {
                "badge": "NEUROSCIENCE LAB",
                "headline": _truncate_words(topic, 26).upper(),
                "subheadline": short_sub,
                "visual_prompt": f"Dark editorial neuroscience illustration about {topic}, glowing teal neural geometry, amber highlight",
            },
            "scenes": [
                {
                    "scene_no": 1,
                    "section": "HOOK",
                    "visual_headline": short_sub,
                    "bullet_points": [
                        "Why willpower alone keeps failing",
                        "What cognitive neuroscience actually shows",
                        "A 3-step protocol you can test today",
                    ],
                    "on_screen_callout": "Work with your brain's biology instead of fighting it",
                    "narration": f"{idea.hook} In the next two minutes, we break down the brain mechanism behind {topic} and the practical three-step protocol to fix it.",
                    "visual_prompt": f"Minimalist dark editorial neuroscience intro visual about {topic}",
                },
                {
                    "scene_no": 2,
                    "section": "PART 1 • THE BRAIN MECHANISM",
                    "visual_headline": "What Happens Inside Your Brain",
                    "bullet_points": [
                        "Prefrontal cortex fatigue under constant switching",
                        "Neurochemical rhythms govern peak alertness",
                        "Attention recovers only in protected blocks",
                    ],
                    "on_screen_callout": "Your nervous system runs in measurable biological cycles",
                    "narration": f"When you examine {topic} through behavioral neuroscience, a clear pattern emerges. Your prefrontal cortex has a finite daily bandwidth for deep analytical work, and ignoring biological rhythms quietly drains your focus.",
                    "visual_prompt": "Glowing teal neural wave cycles on midnight navy grid",
                },
                {
                    "scene_no": 3,
                    "section": "PART 2 • THE HIDDEN TRAP",
                    "visual_headline": "Why Standard Advice Backfires",
                    "bullet_points": [
                        "Pushing harder increases mental friction",
                        "High-novelty breaks disrupt cognitive recovery",
                        "Unstructured schedules invite constant drift",
                    ],
                    "on_screen_callout": "Effort without recovery design leads straight to burnout",
                    "narration": "Most productivity advice tells you to grind longer with brute discipline. Yet without managing stimulation and deliberate recovery, longer hours produce lower quality thinking and faster mental exhaustion.",
                    "visual_prompt": "Dark contrast chart of erratic fatigue spikes versus steady rhythmic flow",
                },
                {
                    "scene_no": 4,
                    "section": "PART 3 • 3-STEP PROTOCOL",
                    "visual_headline": "The 3-Step HabitScience Protocol",
                    "bullet_points": [
                        "Protect one distraction-free morning deep block",
                        "Use deliberate low-stimulation recovery intervals",
                        "Remove physical friction triggers before starting",
                    ],
                    "on_screen_callout": "Design your environment so deep focus becomes the default",
                    "narration": "Apply three concrete shifts starting tomorrow. Protect one uninterrupted morning focus block, take true low-stimulation breaks between sessions, and remove visual phone triggers before you sit down.",
                    "visual_prompt": "Three luminous concentric teal lenses focusing warm light into clarity",
                },
                {
                    "scene_no": 5,
                    "section": "7-DAY EXPERIMENT",
                    "visual_headline": "Run the 7-Day Lab Challenge",
                    "bullet_points": [
                        "Test one protected session daily for 7 days",
                        "Log energy and clarity scores each afternoon",
                        "Keep the exact routine that works for you",
                    ],
                    "on_screen_callout": "Small repeatable protocols compound into lasting focus",
                    "narration": f"Treat this week as a personal seven-day lab experiment and track how your clarity shifts by day four. {cta_yt}",
                    "visual_prompt": "Clean calm 7-day progress nodes glowing in teal and amber",
                },
            ],
        },
        "shorts_reels_tiktok": {
            "title": _truncate_words(topic, 56),
            "hook_text": "STOP FIGHTING YOUR BRAIN BIOLOGY",
            "caption_yt_shorts": f"{idea.hook} Full breakdown on {channel.get('name', 'HabitScience Lab')}! {' '.join(hashtags_list[:4])} #Shorts",
            "caption_tiktok": f"Most people approach {topic} backward. Here is the 3-step neuroscience protocol! {cta_soc} {' '.join(hashtags_list[:5])}",
            "caption_ig_reels": f"Save this for your next deep-work block! {idea.hook} {cta_soc} {' '.join(hashtags_list[:5])}",
            "hashtags": hashtags_list,
            "scenes": [
                {
                    "scene_no": 1,
                    "badge": "01 • HOOK",
                    "visual_headline": _truncate_words(topic, 34),
                    "narration": f"{idea.hook}",
                    "visual_prompt": "Vertical dark editorial neuroscience hook graphic",
                },
                {
                    "scene_no": 2,
                    "badge": "02 • SCIENCE",
                    "visual_headline": "Focus Runs in Biological Cycles",
                    "narration": "Your brain cannot sustain peak output nonstop—ignoring cognitive cycles multiplies mental friction and destroys clarity.",
                    "visual_prompt": "Vertical glowing teal brain rhythm waveform",
                },
                {
                    "scene_no": 3,
                    "badge": "03 • PROTOCOL",
                    "visual_headline": "Protect. Recover. Repeat.",
                    "narration": "Protect one morning deep-work block, take genuine screen-free recovery breaks, and remove distractions before you start.",
                    "visual_prompt": "Vertical luminous teal triad protocol visual",
                },
                {
                    "scene_no": 4,
                    "badge": "04 • 7-DAY TEST",
                    "visual_headline": "Try It for 7 Days",
                    "narration": f"Test this protocol for seven days and feel the difference in your energy. {cta_soc}",
                    "visual_prompt": "Vertical calm summary CTA graphic",
                },
            ],
        },
        "carousel_social": {
            "title": short_title,
            "slides": [
                {
                    "slide_no": 1,
                    "badge": "SLIDE 1/5 • COVER",
                    "headline": short_title,
                    "body": "Stop fighting your brain with brute willpower. Use science-backed rhythms to unlock deeper clarity.",
                    "highlight": "Swipe for the 3-step neuroscience protocol ->",
                    "visual_prompt": "Editorial dark teal neuroscience cover",
                },
                {
                    "slide_no": 2,
                    "badge": "SLIDE 2/5 • MECHANISM",
                    "headline": "Your Brain Runs in Cycles",
                    "body": "Peak cognitive performance rises and dips in measurable biological waves rather than flat linear hours.",
                    "highlight": "Aligning with biology beats forcing longer hours",
                    "visual_prompt": "Minimalist neural cycle card",
                },
                {
                    "slide_no": 3,
                    "badge": "SLIDE 3/5 • THE TRAP",
                    "headline": "Fake Breaks Drain Recovery",
                    "body": "Switching from work straight to rapid feeds keeps working memory overloaded instead of restoring attention.",
                    "highlight": "Low-stimulation pauses actually reset focus",
                    "visual_prompt": "Contrast recovery infographic card",
                },
                {
                    "slide_no": 4,
                    "badge": "SLIDE 4/5 • PROTOCOL",
                    "headline": "The 3-Step Focus Reset",
                    "body": "1) Guard one morning deep block. 2) Take 10-15 min screen-free recovery. 3) Keep your phone out of sight.",
                    "highlight": "Environment beats willpower every time",
                    "visual_prompt": "Clean 3-step teal protocol visual",
                },
                {
                    "slide_no": 5,
                    "badge": "SLIDE 5/5 • ACTION",
                    "headline": "Run the 7-Day Lab Test",
                    "body": "Track one protected deep-work session each morning for seven days and measure how fast mental friction fades.",
                    "highlight": cta_soc,
                    "visual_prompt": "Calm 7-day CTA summary slide",
                },
            ],
            "caption_instagram": f"Working longer hours rarely produces better thinking.\n\nSwipe through this 5-slide neuroscience breakdown of {topic} and the 3-step protocol you can test this week.\n\n{cta_soc}\n\n{' '.join(hashtags_list)}",
            "caption_linkedin": f"Most high performers don't need more hours—they need better biological alignment.\n\nHere is a 3-step framework from {topic}:\n• Protect one uninterrupted morning deep-work block\n• Replace scroll breaks with genuine low-stimulation recovery\n• Remove phone friction triggers before starting complex work\n\nWhich shift makes the biggest difference in your workday?\n\n{' '.join(hashtags_list)}",
            "thread_x": [
                f"1/5 Most people approach {topic} backward—and burn out before noon.\n\nHere is the neuroscience breakdown + 3-step protocol 🧵",
                "2/5 Your prefrontal cortex operates in measurable biological cycles, not flat 8-hour blocks.",
                "3/5 Scrolling during breaks feels relaxing, yet floods working memory with attention residue instead of letting focus recover.",
                "4/5 The 3-Step Reset:\n• One protected morning deep block\n• Screen-free recovery intervals\n• Phone in another room",
                f"5/5 Test this for 7 days and track your clarity by Day 4. Follow {channel.get('handle', '@habitsciencelab')} for weekly science-backed protocols.",
            ],
            "post_threads": f"Science-backed reminder on {topic}: you don't need harsher discipline—you need protected deep blocks paired with genuine screen-free recovery.",
            "post_facebook": f"Ever feel exhausted after working all day yet struggle to finish your most important task?\n\nExplore our science-backed breakdown of {topic} and test the 3-step HabitScience protocol over the next 7 days.\n\n{cta_soc}\n{' '.join(hashtags_list)}",
            "hashtags": hashtags_list,
        },
    }


def _build_structured_fallback(idea: TopicIdea, config: dict[str, Any]) -> dict[str, Any]:
    if config.get("channel", {}).get("language", "en") == "en":
        return _build_english_fallback(idea, config)
    channel = config.get("channel", {})
    topic = idea.topic
    cta_yt = channel.get("cta_youtube", "Subscribe untuk strategi automasi konten lainnya!")
    cta_soc = channel.get("cta_social", "Simpan postingan ini dan bagikan ke tim kreator kamu.")
    niche = channel.get("niche", "AI & Produktivitas")
    short_title = _truncate_words(topic, 58)
    short_sub = _truncate_words(topic, 48)
    keywords = idea.keywords or ["automasi", "ai", "konten", "youtube", "sosmed"]
    hashtags_list = [f"#{slugify(k, 22).replace('-', '')}" for k in keywords[:5] if slugify(k, 22)]
    if "#YouTube" not in hashtags_list:
        hashtags_list.append("#YouTube")
    if "#ContentAutomation" not in hashtags_list:
        hashtags_list.append("#ContentAutomation")

    return {
        "youtube_long": {
            "title": f"{short_title} (Panduan Lengkap)",
            "alt_titles": [
                f"Blueprint Lengkap: {short_title}",
                f"{short_title} — 1 Ide Jadi Semua Format Konten!",
                f"Workflow {short_sub} yang Hemat 10 Jam/Minggu",
            ],
            "description": (
                f"{idea.hook}\n\n"
                f"Di video ini kita membedah tuntas tentang {topic} dengan pendekatan {idea.angle}. "
                f"Cocok untuk {channel.get('target_audience', 'kreator konten')}.\n\n"
                "Yang akan kamu pelajari:\n"
                "00:00 Hook & Kenapa Ini Penting Sekarang\n"
                "00:12 Masalah Utama Produksi Konten Manual\n"
                "00:25 Sistem 4 Tahap Dari Ide Sampai Publish\n"
                "00:40 Cara Repurpose 1 Ide ke YouTube, Shorts, Reels & Carousel\n"
                "00:55 Checklist Eksekusi & Langkah Berikutnya\n\n"
                f"{cta_yt}\n\n"
                + " ".join(hashtags_list)
            ),
            "tags": list(dict.fromkeys(keywords + ["automasi konten", "youtube automation", "repurpose konten", "ai kreator"])),
            "thumbnail": {
                "badge": "BLUEPRINT 2026",
                "headline": "1 IDE JADI SEMUA KONTEN",
                "subheadline": short_sub,
                "visual_prompt": f"High-contrast YouTube studio thumbnail about {topic}, glowing workflow nodes, bold futuristic typography, dark navy and indigo palette with amber accent",
            },
            "scenes": [
                {
                    "scene_no": 1,
                    "section": "HOOK",
                    "visual_headline": "1 Ide -> Semua Platform Otomatis",
                    "bullet_points": [
                        "Riset tren harian otomatis",
                        "Video panjang + Shorts + Carousel",
                        "Auto-draft lengkap dengan laporan",
                    ],
                    "on_screen_callout": "Hemat 80% waktu produksi konten mingguan",
                    "narration": (
                        f"{idea.hook} Bayangkan cukup memasukkan satu topik tentang {topic}, "
                        "lalu sistem langsung menyiapkan naskah, voiceover, video panjang, video pendek, dan carousel siap publish."
                    ),
                    "visual_prompt": f"Dynamic studio intro graphic highlighting {topic}",
                },
                {
                    "scene_no": 2,
                    "section": "MASALAH UTAMA",
                    "visual_headline": "Kenapa Kreator Cepat Burnout?",
                    "bullet_points": [
                        "Riset ide memakan waktu berjam-jam",
                        "Nulis ulang caption untuk tiap platform",
                        "Editing berulang tanpa standar template",
                    ],
                    "on_screen_callout": "Fokus strategi, biarkan sistem mengerjakan repetisi",
                    "narration": (
                        "Tantangan terbesar kreator saat ini bukan kekurangan ide, melainkan proses eksekusi yang berulang. "
                        "Mulai dari riset tren, menulis script, mengisi suara, sampai menyesuaikan ukuran video untuk YouTube, TikTok, dan Instagram."
                    ),
                    "visual_prompt": "Clean dark infographic comparing manual workflow vs automated content studio",
                },
                {
                    "scene_no": 3,
                    "section": "ARSITEKTUR PIPELINE",
                    "visual_headline": "4 Tahap Sistem Otomasi Konten",
                    "bullet_points": [
                        "1. Riset Tren & Anti-Duplikat Topik",
                        "2. Master Script + Repurpose Multi-Format",
                        "3. Render Visual, Voiceover & Subtitle",
                        "4. Auto-Draft & Laporan Publikasi",
                    ],
                    "on_screen_callout": "Modular, konsisten, dan bisa jalan terjadwal",
                    "narration": (
                        f"Dengan sistem modular untuk niche {niche}, setiap produksi dimulai dari riset tren otomatis. "
                        "Setelah itu AI merangkai master script, mengubahnya menjadi format vertikal dan carousel, lalu merender audio dan video secara otomatis."
                    ),
                    "visual_prompt": "4-step glowing pipeline architecture diagram in indigo and cyan",
                },
                {
                    "scene_no": 4,
                    "section": "REPURPOSE CERDAS",
                    "visual_headline": "Satu Riset, Enam Kanal Aktif",
                    "bullet_points": [
                        "YouTube 16:9 + Thumbnail CTR tinggi",
                        "Shorts, Reels, TikTok 9:16 + Subtitle",
                        "Carousel IG, LinkedIn & Thread X",
                    ],
                    "on_screen_callout": "Distribusi maksimal tanpa kerja dua kali",
                    "narration": (
                        "Kunci pertumbuhan channel modern adalah distribusi konsisten. "
                        "Satu riset mendalam langsung dipecah menjadi video YouTube 16 banding 9, klip vertikal 9 banding 16 dengan subtitle sinkron, serta carousel 5 slide beserta caption khusus tiap platform."
                    ),
                    "visual_prompt": "Multi-platform distribution hub graphic showing YouTube, Shorts, Reels, TikTok, Instagram, LinkedIn",
                },
                {
                    "scene_no": 5,
                    "section": "AUTO-DRAFT & CTA",
                    "visual_headline": "Aman dengan Auto-Draft & Laporan",
                    "bullet_points": [
                        "Upload otomatis sebagai Draft / Private",
                        "Review cepat lewat laporan detail",
                        "Publish 1 klik atau jadwalkan otomatis",
                    ],
                    "on_screen_callout": "Kontrol penuh kualitas tetap di tangan kamu",
                    "narration": (
                        "Supaya tetap aman dan berkualitas tinggi, pipeline mengirim konten sebagai auto-draft lengkap dengan laporan detail file, durasi, dan status tiap platform. "
                        f"{cta_yt}"
                    ),
                    "visual_prompt": "Clean dashboard summary screen with green verification badges and publish CTA",
                },
            ],
        },
        "shorts_reels_tiktok": {
            "title": _truncate_words(f"Blueprint: {topic}", 54),
            "hook_text": "1 IDE = 6 KONTEN OTOMATIS!",
            "caption_yt_shorts": f"{idea.hook}\nTonton video lengkapnya di channel kami! {' '.join(hashtags_list[:4])} #Shorts",
            "caption_tiktok": f"Masih bikin konten satu per satu? Coba sistem {topic} ini! Tulis 'AUTOMASI' di komentar kalau mau workflow-nya. {' '.join(hashtags_list[:5])} #TikTokEdukasi",
            "caption_ig_reels": f"Save Reels ini dulu! Begini cara ubah 1 ide soal {topic} jadi video panjang, Reels, dan Carousel sekaligus. {cta_soc} {' '.join(hashtags_list[:5])}",
            "hashtags": hashtags_list,
            "scenes": [
                {
                    "scene_no": 1,
                    "badge": "01 • HOOK",
                    "visual_headline": "1 Ide Jadi 6 Konten Otomatis!",
                    "narration": f"Stop bikin konten sosmed satu per satu! Begini cara kerja sistem {topic} dari ide sampai siap publish.",
                    "visual_prompt": "Bold vertical 9:16 hook card with electric indigo glow",
                },
                {
                    "scene_no": 2,
                    "badge": "02 • RISET & SCRIPT",
                    "visual_headline": "AI Riset Tren & Tulis Script",
                    "narration": "Pertama, sistem mencari tren terbaru, membuat naskah video panjang, lalu otomatis memecahnya jadi script Shorts, Reels, TikTok, dan Carousel.",
                    "visual_prompt": "Vertical dark graphic showing AI script and repurpose engine",
                },
                {
                    "scene_no": 3,
                    "badge": "03 • RENDER OTOMATIS",
                    "visual_headline": "Voiceover, Subtitle & Video Jadi",
                    "narration": "Kedua, voiceover natural, subtitle sinkron, thumbnail, dan video vertikal langsung dirender rapi tanpa edit manual dari nol.",
                    "visual_prompt": "Vertical video rendering progress visual with waveform and captions",
                },
                {
                    "scene_no": 4,
                    "badge": "04 • AUTO-DRAFT",
                    "visual_headline": "Masuk Draft + Laporan Lengkap",
                    "narration": f"Terakhir, semua aset masuk auto-draft lengkap dengan laporan status tiap platform. {cta_soc}",
                    "visual_prompt": "Vertical summary screen with publish checkmarks and CTA",
                },
            ],
        },
        "carousel_social": {
            "title": f"Blueprint: {short_title}",
            "slides": [
                {
                    "slide_no": 1,
                    "badge": "SLIDE 1/5 • COVER",
                    "headline": short_title,
                    "body": "Ubah 1 ide menjadi YouTube Long, Shorts, Reels, TikTok, dan Carousel secara otomatis.",
                    "highlight": "Geser untuk lihat alur lengkapnya ->",
                    "visual_prompt": "Modern bold editorial cover slide dark theme",
                },
                {
                    "slide_no": 2,
                    "badge": "SLIDE 2/5 • RISET IDE",
                    "headline": "Mulai dari Tren yang Tervalidasi",
                    "body": "Ambil topik harian dari RSS & tren niche, lalu saring otomatis memakai riwayat konten agar tidak pernah mengulang topik.",
                    "highlight": "Zero blank-page syndrome setiap minggu",
                    "visual_prompt": "Minimalist card showing trend radar and topic filter",
                },
                {
                    "slide_no": 3,
                    "badge": "SLIDE 3/5 • REPURPOSE",
                    "headline": "1 Master Blueprint, Multi-Platform",
                    "body": "Dari satu naskah utama, pecah otomatis jadi struktur YouTube 16:9, klip vertikal 9:16, 5 slide carousel, thread X, dan post LinkedIn.",
                    "highlight": "Konsisten di semua kanal tanpa burnout",
                    "visual_prompt": "Content repurpose matrix graphic",
                },
                {
                    "slide_no": 4,
                    "badge": "SLIDE 4/5 • PRODUKSI",
                    "headline": "Render Media Lokal & Hemat Biaya",
                    "body": "Gabungkan neural TTS, subtitle sinkron otomatis, template visual brand, dan FFmpeg untuk hasil video tajam siap upload.",
                    "highlight": "Cepat, terukur, dan mudah dikustomisasi",
                    "visual_prompt": "Media production stack diagram",
                },
                {
                    "slide_no": 5,
                    "badge": "SLIDE 5/5 • PUBLISH",
                    "headline": "Auto-Draft + Laporan Detail",
                    "body": "Kirim otomatis sebagai draft ke YouTube & sosmed, lalu terima laporan lengkap berisi checklist QA, link draft, dan ringkasan aset.",
                    "highlight": cta_soc,
                    "visual_prompt": "Clean summary checklist CTA slide",
                },
            ],
            "caption_instagram": (
                f"Capek produksi konten berulang untuk tiap platform? 🚀\n\n"
                f"Geser carousel ini untuk melihat sistem lengkap {topic} — mulai dari riset ide, penulisan script, render video 16:9 & 9:16, sampai auto-draft dengan laporan detail.\n\n"
                f"💡 Poin kunci:\n"
                f"1. Riset tren otomatis & anti-duplikat\n"
                f"2. 1 topik direpurpose ke 6+ format\n"
                f"3. Auto-draft dulu supaya kualitas tetap terjaga\n\n"
                f"{cta_soc}\n\n"
                + " ".join(hashtags_list)
            ),
            "caption_linkedin": (
                f"Banyak tim konten gagal konsisten bukan karena kurang ide, tapi karena bottleneck di proses produksi & distribusi.\n\n"
                f"Hari ini saya merangkum arsitektur untuk {topic}:\n"
                f"• Stage 1: Trend discovery berbasis niche & history deduplication\n"
                f"• Stage 2: Master scriptwriting + automatic multi-format repurposing\n"
                f"• Stage 3: Automated voiceover, synced subtitles, thumbnail, carousel, dan render 16:9 + 9:16\n"
                f"• Stage 4: Safe auto-draft publishing + executive publish report\n\n"
                f"Hasilnya: 1 ide tervalidasi langsung menjadi aset siap tayang di YouTube, Shorts, Reels, TikTok, Instagram, LinkedIn, dan X.\n\n"
                f"Bagian mana dari workflow konten Anda yang saat ini paling menyita waktu? Diskusi di komentar 👇\n\n"
                + " ".join(hashtags_list)
            ),
            "thread_x": [
                f"1/5 Masih bikin konten YouTube, TikTok, Reels & IG secara terpisah? Ini blueprint {topic} yang mengubah 1 ide jadi semua format otomatis 🧵👇",
                "2/5 Mulai dari riset tren otomatis sesuai niche + cek history.json supaya topik selalu segar dan tidak pernah dobel.",
                "3/5 Buat 1 Master Blueprint JSON: langsung menghasilkan script YouTube 16:9, klip pendek 9:16, 5 slide carousel, plus caption beda-beda tiap platform.",
                "4/5 Produksi aset otomatis: neural voiceover + subtitle .SRT sinkron + thumbnail & carousel branded + render FFmpeg 16:9 & 9:16.",
                f"5/5 Terakhir, upload otomatis ke mode Draft (YouTube Private + Social Webhook) dan terima PUBLISH_REPORT.md lengkap. {cta_soc}",
            ],
            "post_threads": (
                f"Baru saja menerapkan sistem {topic}: cukup 1 ide, langsung keluar video YouTube 16:9, Shorts/Reels/TikTok 9:16, 5 slide carousel, caption semua platform, plus auto-draft & laporan detail. "
                "Menurut kalian tahap mana yang paling wajib diotomatisasi duluan?"
            ),
            "post_facebook": (
                f"Ingin jadwal upload YouTube dan media sosial tetap konsisten tanpa kehabisan waktu?\n\n"
                f"Di paket konten kali ini kita bahas {topic} — alur kerja lengkap dari riset ide, naskah, voiceover, render video, hingga auto-draft dan laporan publikasi.\n\n"
                f"{cta_soc}\n" + " ".join(hashtags_list)
            ),
            "hashtags": hashtags_list,
        },
    }


def generate_content_blueprint(
    idea: TopicIdea,
    config: dict[str, Any],
    brief_override_path: Path | None = None,
) -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    if brief_override_path and brief_override_path.exists():
        loaded = json.loads(brief_override_path.read_text(encoding="utf-8"))
        loaded.setdefault("meta", {})
        loaded["meta"].setdefault("topic", idea.topic)
        loaded["meta"].setdefault("slug", slugify(loaded["meta"]["topic"]))
        loaded["meta"].setdefault("generated_at", now_iso)
        loaded["meta"]["generator_mode"] = "external_brief_json"
        return loaded

    gemini_result, used_model = _generate_with_gemini(idea, config)
    if gemini_result is not None:
        blueprint = gemini_result
        mode = f"gemini_api:{used_model}"
    else:
        blueprint = _build_structured_fallback(idea, config)
        mode = "structured_local_template"

    blueprint["meta"] = {
        "topic": idea.topic,
        "angle": idea.angle,
        "hook": idea.hook,
        "source": idea.source,
        "source_url": idea.source_url,
        "keywords": idea.keywords or [],
        "slug": slugify(idea.topic),
        "channel_name": config.get("channel", {}).get("name", "Creator Studio"),
        "channel_handle": config.get("channel", {}).get("handle", "@creator"),
        "language": config.get("channel", {}).get("language", "id"),
        "generated_at": now_iso,
        "generator_mode": mode,
    }
    return blueprint
