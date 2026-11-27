from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_loader import slugify
from src.ideation import TopicIdea


# Strictly isolated 6 Format Packages (Anti-Rancu): 1 Pillar = 1 Script Rhythm = 1 Visual Engine = 1 Nature Audio
ISLAMIC_FORMAT_PROFILES: dict[str, dict[str, Any]] = {
    "minute_wisdom_dua": {
        "format_name": "Format 1: Minute Wisdom Transform (Ref #1 — Fire -> Rain -> Blooming Meadow)",
        "visual_style": "islamic_nature_transform",
        "nature_audio": "gentle_rain",
        "rhythm_rules": (
            "- Tone: Gentle, deeply comforting emotional reset—starts with heaviness, worry, or anger, then washes it clean into serene hope.\n"
            "- Visual context: Hexagonal dark ember earth & flames extinguishing with steam -> falling blue teardrop into meadow pool -> sunlit wildflowers & fruit/blossom trees + 1/7..7/7 dots + Amiri Arabic calligraphy.\n"
            "- Headline rule: Keep every `visual_headline` <= 5 words.\n"
            "- Shorts 5-beat arc (75-100 English words so Saudi Arabic Dua VO + calm English lands ~38-48s): 01 THE HEAT (name the worry/anger) -> 02 THE DUA (reflect on the verified Prophetic Dua recited right after Scene 1) -> 03 COOLING SCIENCE (how calming the body/mind extinguishes stress) -> 04 DAILY RESET (1 gentle habit) -> 05 BLOOM (save & share peace)."
        ),
        "long_sections": "THE HEAT / VERIFIED PROPHETIC DUA / CALMING THE STORM / EVERYDAY MIND SCIENCE / DAILY SHIFT 1 / DAILY SHIFT 2 / STEADY PEACE / CLOSING",
        "short_badge_example": "01 • CALM THE STORM",
    },
    "prophetic_habits": {
        "format_name": "Format 2: Luminous Prayer Sky (Ref #2 — 5-Prayer Sky + Mosque Water Reflection)",
        "visual_style": "islamic_luminous_sky",
        "nature_audio": "dawn_breeze",
        "rhythm_rules": (
            "- Tone: Warm, reassuring, practical step-by-step Prophetic habit coaching.\n"
            "- Visual context: Shifting 5-prayer sky (Fajr -> Dhuhr -> Asr -> Maghrib -> Isha) with mosque & palm silhouette reflected in calm water, showing the verified Amiri Arabic calligraphy card + glowing step dots.\n"
            "- Headline rule: Keep every `visual_headline` <= 5 words so it fits cleanly above the Arabic calligraphy card.\n"
            "- Shorts 5-6 beat arc (80-105 English words so Arabic VO + calm English lands ~40-50s): 01 REFLECT (everyday struggle) -> 02 THE SUNNAH (exact verified Hadith/Dua) -> 03 MIND SCIENCE (why it helps your brain) -> 04 STEP 1 (tiny easy start) -> 05 SHARE PEACE (soft save/share CTA)."
        ),
        "long_sections": "REFLECT / THE MODERN STRUGGLE / THE VERIFIED SUNNAH / EVERYDAY BRAIN SCIENCE / STEP 1 / STEP 2 / GENTLE CONSISTENCY / CLOSING",
        "short_badge_example": "01 • REFLECT",
    },
    "sunnah_paper_story": {
        "format_name": "Format 3: Paper-Cutout 3D Craft (Ref #3 — Pastel Sky Diorama & Faceless Narrator)",
        "visual_style": "islamic_paper_craft",
        "nature_audio": "dawn_breeze",
        "rhythm_rules": (
            "- Tone: Friendly, bright, crisp visual explainer—feels like a warm storybook lesson anyone from teen to adult enjoys sharing.\n"
            "- Visual context: Pastel sky-blue 3D layered paper-cutout diorama with curling wall calendar, open 3D paper book, layered emerald paper hills, Islamic arch medallion, and a respectful faceless minimalist presenter in navy kurta.\n"
            "- Headline rule: Keep every `visual_headline` bold and <= 4 words (renders as crisp cutout display text at top).\n"
            "- Shorts 5-beat arc (80-105 English words so Arabic VO + bright calm English lands ~40-50s): 01 HOOK (relatable everyday question) -> 02 SUNNAH LESSON (verified Hadith meaning) -> 03 BRAIN BENEFIT (why science confirms this daily habit) -> 04 TRY TODAY (simple memorable action) -> 05 SHARE BARAKAH (warm closing)."
        ),
        "long_sections": "OPENING STORY / VERIFIED HADITH / WHY IT MATTERS / BRAIN & HABIT SCIENCE / PRACTICAL STEP 1 / PRACTICAL STEP 2 / WEEKLY RHYTHM / CLOSING",
        "short_badge_example": "01 • STORY",
    },
    "quran_mental_peace": {
        "format_name": "Format 4: Obsidian & Gold Visualizer (Ref #4 — Luxury 24k Gold Sunburst + Real Qari)",
        "visual_style": "islamic_gold_visualizer",
        "nature_audio": "gentle_rain",
        "rhythm_rules": (
            "- Tone: Deeply serene, intimate, unhurried late-night reflection—every sentence feels like a calm breath of peace.\n"
            "- Visual context: Pitch-black obsidian canvas with a glowing 24k gold voice-reactive radial sunburst visualizer and word-by-word gold Arabic & English karaoke. Real uncut Syaikh Mishary Alafasy Qur'an tilawah plays automatically right after Scene 1!\n"
            "- Headline rule: Keep every `visual_headline` <= 5 words because it displays inside a sleek bottom gold insight pill.\n"
            "- Shorts 4-5 beat arc (65-85 English words total so uncut real Qari tilawah + calm English lands cleanly ~42-53s): 01 QUIET PAIN (short 1-sentence hook before Qari recites) -> 02 DEEP MEANING (gentle nuance right after tilawah) -> 03 CALM SCIENCE (how it settles stress/overthinking) -> 04 PEACE (warm save reminder)."
        ),
        "long_sections": "QUIET PAIN / THE AYAH / SUBTLE MEANING / CALM MIND SCIENCE / HIDDEN NOISE / DAILY ANCHOR / LIVING THE VERSE / CLOSING PEACE",
        "short_badge_example": "01 • QUIET PAIN",
    },
    "sunnah_particle_map": {
        "format_name": "Format 5: Cosmic Particle Map (Ref #5 — Al-Kahfi Morphing Particle Constellations)",
        "visual_style": "islamic_particle_map",
        "nature_audio": "calm_water",
        "rhythm_rules": (
            "- Tone: Structured, illuminating wisdom mapping—breaks timeless Prophetic frameworks into crystal-clear mental landmarks.\n"
            "- Visual context: Mood-shifting cosmic canvas where 380+ luminous particles morph across symbolic shapes (crescent, cave arch, 1/3 balance rings, brain waves, circular 4-node summary map) above centered white-outlined subtitles and 4 milestone pills (REFLECT / SUNNAH / SCIENCE / HABIT).\n"
            "- Headline rule: Keep every `visual_headline` punchy and <= 5 words (renders in bold uppercase at the top).\n"
            "- Shorts 5-beat arc (85-110 English words so Arabic VO + calm English lands ~42-52s): 01 FRAMEWORK HOOK (curiosity question) -> 02 VERIFIED HADITH (clear meaning) -> 03 THE SCIENCE (everyday brain/body reason) -> 04 MODERN TRAP (contrast with noisy modern habit) -> 05 DAILY SHIFT (memorable rule + save CTA)."
        ),
        "long_sections": "THE FRAMEWORK / THE VERIFIED SOURCE / BRAIN & BODY SCIENCE / THE MODERN TRAP / KEY INSIGHT 1 / KEY INSIGHT 2 / DAILY SHIFT / CLOSING",
        "short_badge_example": "01 • FRAMEWORK",
    },
    "hadith_cinematic_story": {
        "format_name": "Format 6: Cinematic Visual Metaphor (Ref #6 — Ocean Needle, Twilight Plains & Sunset)",
        "visual_style": "islamic_cinematic_metaphor",
        "nature_audio": "calm_water",
        "rhythm_rules": (
            "- Tone: Deeply reflective, cinematic storytelling—short poetic spoken lines that paint vivid visual metaphors (needle in the ocean, endless plain, quiet surrender at sunset).\n"
            "- Visual context: Full-bleed atmospheric scenes shifting beat-by-beat (luminous needle + glowing drop over sunlit ocean -> midnight ocean vista -> infinite twilight plain -> mirror water ripple -> warm rose-gold sunset clouds) with crisp centered white-outlined conversational subtitles.\n"
            "- Headline rule: Keep every `visual_headline` <= 5 words.\n"
            "- Shorts 5-beat arc (80-105 English words so Arabic VO + reflective English lands ~40-50s): 01 THE IMAGE (vivid opening metaphor) -> 02 THE MEANING (what the authentic Hadith/Ayah teaches) -> 03 MIND SHIFT (moving from scarcity/fear to calm trust) -> 04 QUIET COURAGE (practical heart shift today) -> 05 SURRENDER (warm closing reminder)."
        ),
        "long_sections": "THE METAPHOR / AUTHENTIC SOURCE / SEEING CLEARLY / MINDSET SCIENCE / LETTING GO / QUIET COURAGE / DAILY REFLECTION / CLOSING",
        "short_badge_example": "01 • METAPHOR",
    },
}


def _build_gemini_prompt(idea: TopicIdea, config: dict[str, Any]) -> str:
    channel = config.get("channel", {})
    lang = channel.get("language", "en")
    if lang == "en":
        pillar_id = getattr(idea, "pillar", "prophetic_habits") or "prophetic_habits"
        pillar_label = getattr(idea, "pillar_label", "Prophetic Habits & Daily Sunnah") or "Prophetic Habits & Daily Sunnah"
        dalil = getattr(idea, "dalil", None) or {}
        dalil_block = ""
        if isinstance(dalil, dict) and dalil.get("citation"):
            dalil_block = (
                "\nVERIFIED AUTHENTIC ISLAMIC SOURCE (LOCKED — USE THIS EXACT SOURCE & NEVER INVENT OTHER VERSE/HADITH NUMBERS):\n"
                f"- Arabic: {dalil.get('arabic', '')}\n"
                f"- Transliteration: {dalil.get('transliteration', '')}\n"
                f"- Translation: {dalil.get('translation', '')}\n"
                f"- Verified Citation: {dalil.get('citation', '')}\n"
            )

        # ANTI-RANCU ISOLATION: Studio v10 Islamic formats get a pure, dedicated prompt with ZERO legacy POV bloat!
        if pillar_id in ISLAMIC_FORMAT_PROFILES:
            prof = ISLAMIC_FORMAT_PROFILES[pillar_id]
            return f"""You are a Master Reflective Islamic Wisdom & Everyday Brain Science Storyteller for '{channel.get('name')}' ({channel.get('handle')}).
You are authoring EXCLUSIVELY for ONE locked Format Package—do NOT mix styles from any other format.

LOCKED FORMAT PACKAGE:
- Format: {prof['format_name']}
- Pillar: {pillar_label} ({pillar_id})
- Locked Visual Engine: {prof['visual_style']}
- Locked Audio Ambiance: {prof['nature_audio']} (100% instrument-free nature soundscape + calm narrator voice)
- Audience: {channel.get('target_audience')}
- YouTube CTA: {channel.get('cta_youtube')}
- Social CTA: {channel.get('cta_social')}

CORE IDEA:
- Topic: {idea.topic}
- Unique Angle: {idea.angle}
- Opening Hook: {idea.hook}
- Keywords: {", ".join(idea.keywords or [])}
{dalil_block}
LOCKED FORMAT RHYTHM & STRUCTURE:
{prof['rhythm_rules']}

ISLAMIC ACCURACY, ADAB & PLAIN-ENGLISH RULES (NON-NEGOTIABLE):
1. ZERO FABRICATION: NEVER guess or invent Qur'an verse numbers or Hadith numbers. Anchor strictly to the Verified Citation above.
2. ADAB & RESPECT: Speak of Allah and Prophet Muhammad (peace be upon him) with sincere reverence and calm warmth. In EVERY `visual_prompt`, strictly forbid depicting Prophets, sacred figures, or human faces—use luminous mosque silhouettes, twilight skies, water reflections, starlight, Islamic geometry, rain, meadows, or glowing symbolic light instead.
3. PLAIN EVERYDAY ENGLISH (GRADE 6-7 CLARITY): Warm, soulful, short spoken sentences—ZERO textbook jargon! STRICTLY FORBIDDEN words anywhere in titles or narration: "prefrontal cortex", "amygdala", "coupling", "neural correlates", "cognitive load", "memory consolidation", "executive function", "ultradian", "melatonin", "cortical", "bandwidth".

Return ONLY valid JSON with this exact schema:
{{
  "youtube_long": {{
    "title": "Soulful high-CTR curiosity + wisdom title (max 68 chars)",
    "alt_titles": ["A/B Alt 1", "A/B Alt 2", "A/B Alt 3"],
    "description": "Warm YouTube description with reflective hook, verified citation, everyday science takeaways, chapter timestamps, CTA, and hashtags",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
    "thumbnail": {{
      "badge": "SHORT BADGE (2-3 words)",
      "headline": "PUNCHY THUMBNAIL TEXT (2-4 words)",
      "subheadline": "Short reflective subtitle (4-7 words)",
      "visual_prompt": "Serene luminous Islamic architectural/nature editorial illustration (strictly NO prophets, NO faces, NO text)"
    }},
    "scenes": [
      {{
        "scene_no": 1,
        "section": "{prof['long_sections']}",
        "visual_headline": "Crisp short title (max 5 words)",
        "bullet_points": ["Point 1", "Point 2", "Point 3"],
        "on_screen_callout": "1-line calm insight",
        "narration": "Calm, warm, thoughtful storytelling narration, 2-3 clear spoken sentences (~12-16 seconds when spoken).",
        "visual_prompt": "Serene luminous Islamic landscape or symbolic light illustration (strictly NO prophets, NO faces, NO text)"
      }}
    ]
  }},
  "shorts_reels_tiktok": {{
    "title": "Reflective curiosity vertical title",
    "hook_text": "3-second calm visual hook",
    "caption_yt_shorts": "YouTube Shorts caption with verified citation + hashtags",
    "caption_tiktok": "TikTok caption with gentle reflection question + hashtags",
    "caption_ig_reels": "Instagram Reels caption with verified citation + save/share CTA + hashtags",
    "hashtags": ["#IslamicReminders", "#Sunnah", "#QuranWisdom", "#HabitSains", "#MentalPeace"],
    "scenes": [
      {{
        "scene_no": 1,
        "badge": "{prof['short_badge_example']}",
        "visual_headline": "Crisp short vertical headline (max 5 words)",
        "narration": "Warm, calm, clear 1-2 sentence spoken beat (~6-8 seconds).",
        "visual_prompt": "Serene vertical 9:16 luminous Islamic sky/geometry/nature visual (strictly NO prophets, NO faces, NO text)"
      }}
    ]
  }},
  "carousel_social": {{
    "title": "Carousel title",
    "slides": [
      {{
        "slide_no": 1,
        "badge": "SLIDE 1/5 • COVER",
        "headline": "Soulful reflective cover headline",
        "body": "Concise 1-2 sentence insight",
        "highlight": "Key takeaway or verified citation",
        "visual_prompt": "Serene luminous Islamic twilight/geometric art for this slide (strictly NO prophets, NO faces, NO text)"
      }}
    ],
    "caption_instagram": "Warm reflective Instagram carousel caption with verified citation + save/share CTA + hashtags",
    "caption_linkedin": "Thoughtful LinkedIn reflection connecting timeless Prophetic wisdom with everyday focus science + gentle question",
    "thread_x": ["1/5 Reflective hook + 🧵", "2/5 Authentic wisdom & citation", "3/5 Everyday mind science", "4/5 One gentle daily habit", "5/5 Save/share CTA"],
    "post_threads": "Short warm reflective Threads post with verified wisdom",
    "post_facebook": "Engaging warm Facebook Page post with verified citation & question",
    "hashtags": ["#IslamicReminders", "#Sunnah", "#QuranWisdom", "#HabitSains", "#PeaceOfMind"]
  }}
}}

Strict beat counts:
- youtube_long.scenes MUST have 8 distinct calm visual beats (~12-16s each, total ~2 minutes).
- shorts_reels_tiktok.scenes MUST have 6 crisp vertical beats (~6-8s each, strictly under 55 seconds total).
- carousel_social.slides MUST have exactly 5 slides (Cover, Verified Source/Citation, Everyday Mind Science, Gentle Daily Step, Save/Share CTA).
"""

        # Legacy secular POV/Science prompt path (ONLY used when explicitly invoking legacy pillars!)
        pillar_hint = {
            "pov_survival": "Style focus: Thrilling First-Person 3D POV countdown/survival brain challenge.",
            "everyday_science": "Style focus: Fun, surprising everyday brain/body science.",
            "focus_habits": "Style focus: Relatable everyday phone/focus/procrastination struggle + 1 super-simple habit trick.",
        }.get(pillar_id, "Style focus: Super-simple everyday brain & habit storytelling.")
        return f"""You are a Viral YouTube & Reels Storyteller for '{channel.get('name')}' ({channel.get('handle')}).
Create an original Master Content Blueprint in super-simple everyday spoken English (Grade 6-7 clarity, zero academic jargon).

Channel Profile:
- Scheduled Pillar: {pillar_label} ({pillar_id}) — {pillar_hint}
- Audience: {channel.get('target_audience')}
- Tone: {channel.get('tone')}
- YouTube CTA: {channel.get('cta_youtube')}
- Social CTA: {channel.get('cta_social')}

Core Idea:
- Topic: {idea.topic}
- Unique Angle: {idea.angle}
- Opening Hook: {idea.hook}
- Keywords: {", ".join(idea.keywords or [])}

Return ONLY valid JSON with keys: youtube_long (8 scenes), shorts_reels_tiktok (6 scenes + pov_3d_episode), carousel_social (5 slides).
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


REQUIRED_POV_BEATS: tuple[str, ...] = (
    "intro",
    "trap",
    "explain",
    "timer_react",
    "scan",
    "desk",
    "agree",
    "ping",
)
_BEAT_SPEAKERS: dict[str, str] = {
    "intro": "pov",
    "trap": "partner",
    "explain": "partner",
    "timer_react": "pov",
    "scan": "partner",
    "desk": "partner",
    "agree": "pov",
    "ping": "partner",
}
_BADGE_COLORS: tuple[str, ...] = (
    "#E11D48",
    "#F59E0B",
    "#3B82F6",
    "#EC4899",
    "#8B5CF6",
    "#F43F5E",
)


def _clamp_prop(val: Any, max_len: int, fallback: str) -> str:
    raw = " ".join(str(val or "").split()).strip()
    if not raw:
        raw = fallback
    if len(raw) <= max_len:
        return raw
    clipped = raw[:max_len].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return clipped if len(clipped) >= max(4, max_len // 2) else raw[:max_len].rstrip()


def _extract_series_title(topic: str) -> str:
    clean = re.sub(r"\([^)]*\)", "", topic or "")
    clean = re.sub(r"[^A-Za-z0-9\s\-]", " ", clean)
    stop = {
        "why", "how", "the", "your", "what", "does", "do", "is", "are", "of", "to", "in", "for",
        "and", "a", "an", "on", "supports", "support", "affects", "affect", "causes", "cause",
        "makes", "make", "helps", "help", "shows", "show", "secretly", "actually", "really",
        "related", "behind", "about", "into", "with", "from",
    }
    words = [w for w in clean.split() if w]
    key_words = [w for w in words if w.lower() not in stop]
    chosen = (key_words[:3] if len(key_words) >= 2 else words[:3]) or ["FOCUS", "TRAP"]
    title = " ".join(chosen).upper()
    if len(title) > 20:
        title = " ".join(chosen[:2]).upper()[:20].strip()
    return title or "THE FOCUS TRAP"


def _extract_spoken_topic(topic: str) -> str:
    clean = re.sub(r"\([^)]*\)", "", topic or "").strip().rstrip("?!.")
    if ":" in clean:
        left, right = [p.strip() for p in clean.split(":", 1)]
        clean = left if 2 <= len(left.split()) <= 6 else right
    words = clean.split()
    if len(words) > 7:
        clean = " ".join(words[:7])
    return clean or "deep focus"


_VALID_SCENE_ENVS: tuple[str, ...] = (
    "sunrise_bedroom",
    "midnight_study",
    "sunny_cafe_desk",
    "survival_bunker",
    "focus_lab",
)
_VALID_ACTION_PATTERNS: tuple[str, ...] = (
    "nightstand_to_desk",
    "desk_face_down",
    "partner_first_confrontation",
    "coffee_window_pan",
)
_VALID_HERO_PROPS: tuple[str, ...] = (
    "alarm_phone",
    "face_down_phone",
    "coffee_mug",
    "hazard_beacon",
)


def _pick_3d_world_and_action(topic: str, low_blob: str, pillar: str = "") -> tuple[str, str, str]:
    """Select distinct (scene_env, action_pattern, hero_prop) tailored to THIS episode's exact topic & action."""
    if pillar == "pov_survival" or any(k in low_blob for k in ("72 hour", "24 hour", "survive", "challenge", "resets the clock", "locked in", "brain battery", "zero screen", "no phone")):
        return "survival_bunker", "partner_first_confrontation", "hazard_beacon"
    if any(k in low_blob for k in ("coffee", "caffeine")):
        return "sunny_cafe_desk", "coffee_window_pan", "coffee_mug"
    if any(k in low_blob for k in ("face down", "arm's reach", "arm reach", "nearby", "desk", "messy", "clutter", "to-do", "to do", "procrastin", "boring", "lazy")):
        return "midnight_study", "desk_face_down", "face_down_phone"
    if any(k in low_blob for k in ("multitask", "switch", "23-minute", "23 min", "text", "tab", "interrupt", "notification", "lyrics", "reading")):
        return "focus_lab", "desk_face_down", "face_down_phone"
    if any(k in low_blob for k in ("sleep", "insomnia", "bedtime", "midnight", "night", "exhausted", "8 hours", "1 hour later")):
        return "midnight_study", "nightstand_to_desk", "alarm_phone"
    if any(k in low_blob for k in ("morning", "7 am", "7:00", "wake", "sunlight", "alarm")):
        return "sunrise_bedroom", "nightstand_to_desk", "alarm_phone"
    if any(k in low_blob for k in ("shower", "nap", "break", "fried", "tired", "reset", "rest", "doorway")):
        return "sunny_cafe_desk", "partner_first_confrontation", "coffee_mug"

    # Deterministic per-title variety hash so even general topics vary world & camera blocking!
    h = sum(ord(ch) * (i + 1) for i, ch in enumerate((topic or "focus").lower()))
    env = _VALID_SCENE_ENVS[h % len(_VALID_SCENE_ENVS)]
    act = _VALID_ACTION_PATTERNS[(h // 3) % len(_VALID_ACTION_PATTERNS)]
    prop = {
        "sunrise_bedroom": "alarm_phone",
        "midnight_study": "face_down_phone" if act == "desk_face_down" else "alarm_phone",
        "sunny_cafe_desk": "coffee_mug",
        "survival_bunker": "hazard_beacon",
        "focus_lab": "face_down_phone",
    }[env]
    return env, act, prop


def build_topic_matched_pov_3d_episode(
    topic: str,
    angle: str = "",
    hook: str = "",
    scenes_meta: list[dict[str, Any]] | None = None,
    config: dict[str, Any] | None = None,
    pillar: str = "",
) -> dict[str, Any]:
    """Synthesize a plain-English, zero-jargon, beat-locked 8-line 2-speaker 3D POV script & 3D props.

    Designed for instant Grade 6-7 comprehension across ALL 3 rotating pillars:
      - focus_habits: everyday phone, procrastination, distraction & motivation fixes
      - everyday_science: surprising daily brain facts (coffee crash, tired after 8h sleep, shower ideas, naps, lyrics)
      - pov_survival: thrilling @you.have.72hours countdown brain-survival challenges
    """
    cfg = config or {}
    handle = str(cfg.get("branding", {}).get("watermark_text", "@HabitSains"))
    scenes = scenes_meta or []
    blob = " ".join(
        [
            topic or "",
            angle or "",
            hook or "",
            *[f"{s.get('visual_headline', '')} {s.get('on_screen_callout', '')} {s.get('narration', '')}" for s in scenes],
        ]
    )
    low = blob.lower()
    series_title = _extract_series_title(topic)
    spoken_topic = _extract_spoken_topic(topic)
    clean_laptop_title = (
        spoken_topic
        if len(spoken_topic) <= 26
        else _clamp_prop(f"{series_title.title()} Goal", 26, "Today's Big Goal")
    )
    end_sub_line = f"Part 2 reveals what happens next • {handle}"

    stat_match = re.search(r"(\d{1,3}\s?%|\d{1,2}\s?(?:min|minutes|hours|hrs))", blob, re.IGNORECASE)
    extracted_num = ""
    if stat_match:
        extracted_num = stat_match.group(1).upper().replace("MINUTES", "MIN").replace("HOURS", "HRS").strip()

    is_survival = (
        pillar == "pov_survival"
        or any(k in low for k in ("72 hour", "24 hour", "survive", "challenge", "resets the clock", "locked in", "brain battery", "zero screen", "no phone"))
    )

    if is_survival:
        is_night = any(k in low for k in ("midnight", "11:42", "sleep", "night", "tomorrow"))
        loc_main = "YOUR BEDROOM • 11:42 PM" if is_night else "CHALLENGE • HOUR 1"
        phone_time = "11:42" if is_night else "01:00"
        stat_str = extracted_num if extracted_num else "1 TAP = FAIL"
        props = {
            "loc_main": loc_main,
            "loc_sub": f"{handle} • Part 1",
            "series_eyebrow": "3D POV CHALLENGE",
            "series_title": series_title,
            "timer_label": "SURVIVAL CLOCK",
            "phone_time": phone_time,
            "phone_norm_hdr": "CHALLENGE ACTIVE",
            "phone_norm_cards": [
                ["#E11D48", "RULE #1", "Do NOT touch your phone"],
                ["#F59E0B", "BRAIN BATTERY", "Drops every time you peek"],
                ["#3B82F6", "NEW MESSAGES", "14 people just texted you"],
            ],
            "phone_cta_norm": "TAP TO QUIT",
            "phone_urgent_hdr": "3 FINAL TEMPTATIONS!",
            "phone_urgent_cards": [
                ["#E11D48", "URGENT TEXT", "Open this right now?!"],
                ["#F59E0B", "VIRAL VIDEO", "Everyone is watching it"],
                ["#E11D48", "GROUP CHAT", "99+ unread messages!"],
            ],
            "phone_cta_urgent": "GIVE IN NOW",
            "swarm_badges": ["QUIT?", "TAP!", "99+", "PING!", "FAIL", "TRAP"],
            "scan_title": "BRAIN BATTERY SCAN",
            "scan_stat": _clamp_prop(stat_str, 14, "1 TAP = FAIL"),
            "scan_sub": "MOST PEOPLE QUIT FAST",
            "scan_left_lbl": "1 QUICK PEEK",
            "scan_right_lbl": "FOCUS AT 0%",
            "scan_footer": "CHALLENGE: AT RISK",
            "laptop_hdr": "MISSION • FINISH TODAY",
            "laptop_due": "TIME RUNNING OUT",
            "laptop_title": clean_laptop_title,
            "laptop_status": "|  (Stay locked in to win)",
            "laptop_callout": "IGNORE THE PHONE = YOU WIN",
            "end_top": "PART 1 • YOU DECIDE",
            "option_a": "IGNORE ALL 3 ALERTS & SURVIVE THE CLOCK",
            "option_b": "PEEK FOR 5 SECONDS & FAIL THE CHALLENGE",
            "end_sub": end_sub_line,
        }
        dialogue = [
            {"beat": "intro", "speaker": "pov", "text": "Okay... the timer just started. One quick peek at my phone can't really ruin the whole challenge, right?"},
            {"beat": "trap", "speaker": "partner", "text": "STOP! Pull your hand back! One tap on that glowing screen resets your entire focus clock!"},
            {"beat": "explain", "speaker": "partner", "text": "Here is the rule. Every time you cave in to a quick ping, your brain craves ten more—and your focus battery tanks almost instantly."},
            {"beat": "timer_react", "speaker": "pov", "text": "Wait... so even a five-second peek really wipes out my battery?!"},
            {"beat": "scan", "speaker": "partner", "text": "Look at this scan. Most people fold right here in the first hour because boredom feels scary for five minutes."},
            {"beat": "desk", "speaker": "partner", "text": "Look at your desk. Survive just ten quiet minutes on your real goal, and the urge to check your phone drops fast."},
            {"beat": "agree", "speaker": "pov", "text": "Alright, hands off the phone. I'm surviving this clock."},
            {"beat": "ping", "speaker": "partner", "text": "Uh-oh—three loud alerts just hit at once! Your hand is already reaching back toward the screen!"},
        ]
    elif any(k in low for k in ("coffee", "caffeine")):
        props = {
            "loc_main": "YOUR BEDROOM • 7:01 AM",
            "loc_sub": f"{handle} • Part 1",
            "series_eyebrow": "EVERYDAY SCIENCE",
            "series_title": series_title,
            "timer_label": "ENERGY CLOCK",
            "phone_time": "7:01",
            "phone_norm_hdr": "MORNING ROUTINE",
            "phone_norm_cards": [
                ["#F59E0B", "7:01 AM COFFEE", "Feels great right now..."],
                ["#E11D48", "2:00 PM WALL", "Massive energy crash later"],
                ["#3B82F6", "SLEEPY SIGNAL", "Only paused, not gone"],
            ],
            "phone_cta_norm": "DRINK NOW",
            "phone_urgent_hdr": "2 PM CRASH ALERT!",
            "phone_urgent_cards": [
                ["#E11D48", "EYES HEAVY", "Coffee just wore off!"],
                ["#F59E0B", "CUP #2?", "Ruins your sleep tonight"],
                ["#E11D48", "BRAIN FOG", "Can't focus on work"],
            ],
            "phone_cta_urgent": "MORE COFFEE",
            "swarm_badges": ["CRASH", "TIRED", "2 PM!", "FOG", "TRAP", "LOW"],
            "scan_title": "DAILY ENERGY SCAN",
            "scan_stat": "2 PM CRASH",
            "scan_sub": "SLEEPY SIGNAL FLOODS BACK",
            "scan_left_lbl": "7 AM COFFEE",
            "scan_right_lbl": "2 PM WALL",
            "scan_footer": "WAIT 60-90 MIN AFTER WAKING",
            "laptop_hdr": "AFTERNOON • BIG TASK",
            "laptop_due": "DUE 5:00 PM",
            "laptop_title": clean_laptop_title,
            "laptop_status": "|  (Hard to think at 2 PM)",
            "laptop_callout": "WATER FIRST -> COFFEE LATER",
            "end_top": "PART 1 • YOU DECIDE",
            "option_a": "DRINK WATER FIRST & WAIT 60 MIN FOR COFFEE",
            "option_b": "CHUG COFFEE AT 7 AM & CRASH AT 2 PM",
            "end_sub": end_sub_line,
        }
        dialogue = [
            {"beat": "intro", "speaker": "pov", "text": "Seven AM already... I feel half asleep. Let me grab coffee right now before I even wake up."},
            {"beat": "trap", "speaker": "partner", "text": "STOP! Don't drink coffee the second you open your eyes! That's why you crash hard at two PM!"},
            {"beat": "explain", "speaker": "partner", "text": "Here is why. Coffee doesn't actually erase tiredness—it just hits pause on your brain's sleepy chemical. Drink it too early, and all that tiredness piles up behind a dam."},
            {"beat": "timer_react", "speaker": "pov", "text": "Wait... so my morning cup is what causes my two PM wall?!"},
            {"beat": "scan", "speaker": "partner", "text": "Look at this scan. The moment that early caffeine wears off, the dam breaks and your energy drops off a cliff."},
            {"beat": "desk", "speaker": "partner", "text": "Look at the work waiting on your desk. Drink water first, get light in your eyes, and wait an hour for coffee so your energy stays smooth."},
            {"beat": "agree", "speaker": "pov", "text": "Okay, water first... I'll wait an hour for coffee."},
            {"beat": "ping", "speaker": "partner", "text": "Three morning alerts just hit and your brain is begging for instant caffeine—can you really hold out?"},
        ]
    elif any(k in low for k in ("shower", "nap", "lyrics", "music", "doorway", "walking into a room", "time feels faster", "junk food", "crave")):
        is_shower = "shower" in low
        is_nap = "nap" in low
        is_lyrics = "lyrics" in low or "music" in low
        is_door = "doorway" in low or "walking into a room" in low
        props = {
            "loc_main": "YOUR DESK • 2:14 PM",
            "loc_sub": f"{handle} • Part 1",
            "series_eyebrow": "EVERYDAY SCIENCE",
            "series_title": series_title,
            "timer_label": "BRAIN MODE",
            "phone_time": "2:14",
            "phone_norm_hdr": "WHY DOES THIS HAPPEN?",
            "phone_norm_cards": [
                ["#3B82F6", "NONSTOP NOISE", "Crowds your thinking space"],
                ["#F59E0B", "ZERO QUIET", "Blocks sudden great ideas"],
                ["#E11D48", "BRAIN OVERLOAD", "Makes simple things blurry"],
            ],
            "phone_cta_norm": "KEEP SCROLLING",
            "phone_urgent_hdr": "3 NOISE TRAPS!",
            "phone_urgent_cards": [
                ["#E11D48", "LOUD FEED", "Kills quiet thinking"],
                ["#F59E0B", "NEW VIDEO", "Fills every silent gap"],
                ["#E11D48", "PING ALERT", "Breaks your train of thought"],
            ],
            "phone_cta_urgent": "TAP NOISE",
            "swarm_badges": ["NOISE", "FOG", "PING!", "BUSY", "LOST", "TRAP"],
            "scan_title": "EVERYDAY BRAIN SCAN",
            "scan_stat": "20 MIN MAX" if is_nap else ("NO LYRICS" if is_lyrics else "QUIET = IDEAS"),
            "scan_sub": "WHY YOUR BRAIN ACTS WEIRD",
            "scan_left_lbl": "OVERLOADED",
            "scan_right_lbl": "CRYSTAL CLEAR",
            "scan_footer": "GIVE YOUR BRAIN ROOM TO BREATHE",
            "laptop_hdr": "SMART HABIT • TRY TODAY",
            "laptop_due": "SIMPLE FIX",
            "laptop_title": clean_laptop_title,
            "laptop_status": "|  (Works the very first day)",
            "laptop_callout": "LESS NOISE = SHARPER BRAIN",
            "end_top": "PART 1 • YOU DECIDE",
            "option_a": "TRY THIS SIMPLE BRAIN FIX TODAY",
            "option_b": "KEEP DOING IT THE OLD TIRED WAY",
            "end_sub": end_sub_line,
        }
        if is_shower:
            explain = "Your brain only connects creative dots when you stop feeding it nonstop noise. In the shower, there's no phone—so your hidden ideas finally pop up."
            scan_line = "Look at this scan. Staring at a screen locks your brain in tunnel vision, while five quiet minutes spark twice as many fresh ideas."
            desk_line = "Look at that stuck task on your desk. Step away for five silent minutes without your phone, and watch the answer hit you."
        elif is_nap:
            explain = "After twenty minutes, your brain drops into super-deep sleep. Wake up in the middle of that at forty-five minutes, and you feel drunk and groggy for hours."
            scan_line = "Look at this scan. A twenty-minute nap refreshes your energy cleanly—while a forty-five minute nap leaves you in heavy brain fog."
            desk_line = "Look at your desk. Set a strict twenty-minute alarm before you lie down so you wake up sharp instead of wrecked."
        elif is_lyrics:
            explain = "Your brain uses the exact same reading zone to process sung words. So when lyrics play, your brain has to keep switching back and forth."
            scan_line = "Look at this scan. Songs with lyrics cut reading speed sharply—forcing you to re-read the exact same sentence three times."
            desk_line = "Look at that work on your desk. Switch to instrumental music or quiet beats and watch how much faster you finish."
        elif is_door:
            explain = "Every time you walk through a doorway, your brain treats the new room like a brand-new chapter—and quietly closes the mental tab from the last room."
            scan_line = "Look at this scan. Crossing a doorway clears short-term memory on purpose so your brain can focus on the new space."
            desk_line = "Look at your desk. Say the one thing you need out loud before standing up, and your brain won't wipe it at the door."
        else:
            explain = f"It feels random, right? With {spoken_topic.lower()}, your brain is just taking a shortcut to save energy—and constant phone noise makes it ten times worse."
            scan_line = "Look at this scan. When your mind is flooded with alerts and stress, clear thinking drops fast and autopilot takes over."
            desk_line = "Look over at your desk. Give yourself ten minutes of calm focus without your phone and notice how fast your head clears."
        dialogue = [
            {"beat": "intro", "speaker": "pov", "text": "Wait a second... why does my brain always do this to me? Let me scroll my phone while I think."},
            {"beat": "trap", "speaker": "partner", "text": "STOP! Put that phone down! Your brain isn't broken—there's a crazy simple reason this happens!"},
            {"beat": "explain", "speaker": "partner", "text": explain},
            {"beat": "timer_react", "speaker": "pov", "text": "No way... THAT is actually why that keeps happening to me?!"},
            {"beat": "scan", "speaker": "partner", "text": scan_line},
            {"beat": "desk", "speaker": "partner", "text": desk_line},
            {"beat": "agree", "speaker": "pov", "text": "Whoa, that actually makes total sense. I'll try it now."},
            {"beat": "ping", "speaker": "partner", "text": "Too late—three notifications just buzzed! Your hand is already reaching right back for the screen!"},
        ]
    elif any(k in low for k in ("sleep", "insomnia", "bedtime", "midnight", "night", "exhausted", "8 hours", "1 hour later")):
        props = {
            "loc_main": "YOUR BEDROOM • 11:42 PM",
            "loc_sub": f"{handle} • Part 1",
            "series_eyebrow": "EVERYDAY SCIENCE",
            "series_title": series_title,
            "timer_label": "SLEEP BATTERY",
            "phone_time": "11:42",
            "phone_norm_hdr": "LATE-NIGHT LOOP",
            "phone_norm_cards": [
                ["#E11D48", "ONE MORE VIDEO", "Tricks brain into daytime"],
                ["#3B82F6", "LATE CHATS", "Keeps your mind racing"],
                ["#F59E0B", "LIGHT SLEEP", "Wake up tired after 8 hrs"],
            ],
            "phone_cta_norm": "WATCH 1 MORE",
            "phone_urgent_hdr": "3 MIDNIGHT TRAPS!",
            "phone_urgent_cards": [
                ["#E11D48", "NEXT EPISODE", "Just 10 minutes more?"],
                ["#F59E0B", "FRIEND TAGGED", "Tap before sleeping"],
                ["#E11D48", "LATE PING", "Steals deep recharge"],
            ],
            "phone_cta_urgent": "OPEN SCREEN",
            "swarm_badges": ["AWAKE", "TIRED", "1 AM!", "PING!", "LATE", "FOG"],
            "scan_title": "DEEP SLEEP SCAN",
            "scan_stat": extracted_num if "%" in extracted_num else "-35% ENERGY",
            "scan_sub": "8 HOURS IN BED, STILL TIRED",
            "scan_left_lbl": "11:42 PM PHONE",
            "scan_right_lbl": "GROGGY MORNING",
            "scan_footer": "DEEP RECHARGE: BLOCKED",
            "laptop_hdr": "TOMORROW • BIG DAY",
            "laptop_due": "STARTS 9 AM",
            "laptop_title": clean_laptop_title,
            "laptop_status": "|  (Needs a rested brain)",
            "laptop_callout": "PHONE OUTSIDE = REAL ENERGY",
            "end_top": "PART 1 • YOU DECIDE",
            "option_a": "CHARGE PHONE OUTSIDE & SLEEP DEEPLY",
            "option_b": '"JUST ONE MORE VIDEO" UNTIL 1:00 AM',
            "end_sub": end_sub_line,
        }
        dialogue = [
            {"beat": "intro", "speaker": "pov", "text": "Eleven forty-two already... I should sleep, let me just watch one short video first."},
            {"beat": "trap", "speaker": "partner", "text": "STOP! Put that glowing screen down! That's why you wake up tired even after eight hours!"},
            {"beat": "explain", "speaker": "partner", "text": "Here is why. Bright late-night videos tell your brain it's still daytime, shutting off your sleep chemical so you stay stuck in light, shallow sleep."},
            {"beat": "timer_react", "speaker": "pov", "text": "Wait... ten minutes on my phone ruins my sleep quality all night?!"},
            {"beat": "scan", "speaker": "partner", "text": "Look at this scan. Late scrolling cuts deep recharge sharply—leaving you foggy and cranky all next afternoon."},
            {"beat": "desk", "speaker": "partner", "text": "Look at the work waiting on your desk for tomorrow. Charge your phone outside the bedroom tonight so your brain actually recharges."},
            {"beat": "agree", "speaker": "pov", "text": "Okay, fair point... lights out, phone stays away."},
            {"beat": "ping", "speaker": "partner", "text": "Hear those three midnight pings? One tap right now and you'll still be scrolling at one AM!"},
        ]
    elif any(k in low for k in ("morning", "7 am", "7:00", "wake", "sunlight", "alarm")):
        props = {
            "loc_main": "YOUR BEDROOM • 7:01 AM",
            "loc_sub": f"{handle} • Part 1",
            "series_eyebrow": "HABITSAINS POV",
            "series_title": series_title,
            "timer_label": "FOCUS WINDOW",
            "phone_time": "7:01",
            "phone_norm_hdr": "19 NOTIFICATIONS",
            "phone_norm_cards": [
                ["#E11D48", "SOCIAL FEED", "14 new likes & comments"],
                ["#3B82F6", "MESSAGES", "3 unread group chats"],
                ["#F59E0B", "SHORT VIDEOS", "Just 2 minutes? Tap now"],
            ],
            "phone_cta_norm": "SWIPE TO SCROLL",
            "phone_urgent_hdr": "3 URGENT ALERTS!",
            "phone_urgent_cards": [
                ["#E11D48", "BOSS • URGENT", "Can you reply right now?!"],
                ["#F59E0B", "VIRAL REEL", "You were tagged in 4 posts"],
                ["#E11D48", "BREAKING NEWS", "Tap to see what happened"],
            ],
            "phone_cta_urgent": "OPEN NOW",
            "swarm_badges": ["99+", "PING!", "MSG", "LIVE", "LIKE", "TRAP"],
            "scan_title": "MORNING FOCUS SCAN",
            "scan_stat": extracted_num if "%" in extracted_num else "-40% FOCUS",
            "scan_sub": "BRAIN FOG FOR 6 HOURS",
            "scan_left_lbl": "7:01 AM SCROLL",
            "scan_right_lbl": "3:00 PM FOG",
            "scan_footer": "FOCUS FUEL: BURNED EARLY",
            "laptop_hdr": "TODAY • BIG PRIORITY",
            "laptop_due": "DUE 5:00 PM",
            "laptop_title": clean_laptop_title,
            "laptop_status": "|  (0 words written...)",
            "laptop_callout": "PROTECT YOUR FIRST 30 MINUTES",
            "end_top": "PART 1 • YOU DECIDE",
            "option_a": "LEAVE PHONE AWAY FOR THE FIRST 30 MINUTES",
            "option_b": '"JUST TWO MINUTES" OF BED SCROLLING',
            "end_sub": end_sub_line,
        }
        dialogue = [
            {"beat": "intro", "speaker": "pov", "text": "Ugh... seven AM already. Let me just check my phone for two minutes before getting up."},
            {"beat": "trap", "speaker": "partner", "text": "STOP! Don't touch that screen! You're walking straight into the seven AM focus trap!"},
            {"beat": "explain", "speaker": "partner", "text": "Listen closely. You wake up with fresh focus fuel. One bed-scroll burns it on fake excitement—making normal work feel painfully boring all day."},
            {"beat": "timer_react", "speaker": "pov", "text": "Wait... six whole hours ruined from just two minutes in bed?!"},
            {"beat": "scan", "speaker": "partner", "text": "Look at this scan. Your focus drops forty percent right after morning scrolling, and brain fog hangs on till afternoon."},
            {"beat": "desk", "speaker": "partner", "text": "Look at that work on your desk. Keep the phone away for your first thirty minutes so your brain stays sharp."},
            {"beat": "agree", "speaker": "pov", "text": "Okay, okay... I won't check it yet."},
            {"beat": "ping", "speaker": "partner", "text": "There it goes—three loud alerts hitting at once! Your hand is already reaching back for it!"},
        ]
    elif any(k in low for k in ("multitask", "switch", "23-minute", "23 min", "text", "interrupt", "notification", "tab")):
        props = {
            "loc_main": "YOUR DESK • 2:14 PM",
            "loc_sub": f"{handle} • Part 1",
            "series_eyebrow": "HABITSAINS POV",
            "series_title": series_title,
            "timer_label": "FOCUS CLOCK",
            "phone_time": "2:14",
            "phone_norm_hdr": "1 TEXT = 23 MIN LOST",
            "phone_norm_cards": [
                ["#3B82F6", "QUICK TEXT", "Takes 10 sec, costs 23 min"],
                ["#F59E0B", "NEW EMAIL", "Pulls mind off your work"],
                ["#E11D48", "APP PING", "Resets your whole flow"],
            ],
            "phone_cta_norm": "PEEK 10 SECS",
            "phone_urgent_hdr": "3 DISTRACTION PINGS!",
            "phone_urgent_cards": [
                ["#E11D48", "TEAM CHAT", "Quick question right now"],
                ["#F59E0B", "INBOX +4", "Urgent? Or just noise?"],
                ["#E11D48", "APP ALERT", "1 glance = 23 min lost"],
            ],
            "phone_cta_urgent": "CHECK NOW",
            "swarm_badges": ["23 MIN", "PING!", "TEXT", "TAB+", "NOISE", "LOST"],
            "scan_title": "FOCUS LOSS SCAN",
            "scan_stat": "23 MIN LOST",
            "scan_sub": "FROM ONE 10-SEC CHECK",
            "scan_left_lbl": "10 SEC TEXT",
            "scan_right_lbl": "23 MIN GONE",
            "scan_footer": "BRAIN STUCK ON OLD MESSAGE",
            "laptop_hdr": "ONE TASK • ZERO PINGS",
            "laptop_due": "DUE 5:00 PM",
            "laptop_title": clean_laptop_title,
            "laptop_status": "|  (1 tab open, phone silent)",
            "laptop_callout": "ONE TASK AT A TIME = 2X FASTER",
            "end_top": "PART 1 • YOU DECIDE",
            "option_a": "AIRPLANE MODE & FINISH THIS ONE TASK",
            "option_b": "PEEK AT 1 TEXT & LOSE 23 MINUTES",
            "end_sub": end_sub_line,
        }
        dialogue = [
            {"beat": "intro", "speaker": "pov", "text": "Ooh, my phone lit up. Let me reply for ten seconds, then jump right back to work."},
            {"beat": "trap", "speaker": "partner", "text": "STOP! Don't touch that text! A ten-second glance is way more expensive than you think!"},
            {"beat": "explain", "speaker": "partner", "text": "Here is why. Your brain can't really multitask. Even after you put the phone down, half your mind stays stuck on that text while you try to work."},
            {"beat": "timer_react", "speaker": "pov", "text": "Wait... ten seconds really costs how much of my focus time?!"},
            {"beat": "scan", "speaker": "partner", "text": "Look at this scan. Studies show it takes twenty-three full minutes to get back into deep flow after one tiny interruption."},
            {"beat": "desk", "speaker": "partner", "text": "Look at that work on your desk. Put your phone on airplane mode until this one task is finished."},
            {"beat": "agree", "speaker": "pov", "text": "Got it... airplane mode on. One task only."},
            {"beat": "ping", "speaker": "partner", "text": "Uh-oh—three loud pings just lit up your phone! Your hand is already reaching to take a peek!"},
        ]
    elif any(k in low for k in ("procrastin", "boring", "lazy", "laziness", "to-do", "to do", "starting", "start", "messy desk", "clutter")):
        props = {
            "loc_main": "YOUR DESK • 2:14 PM",
            "loc_sub": f"{handle} • Part 1",
            "series_eyebrow": "HABITSAINS POV",
            "series_title": series_title,
            "timer_label": "ACTION WINDOW",
            "phone_time": "2:14",
            "phone_norm_hdr": "WHY YOU CAN'T START",
            "phone_norm_cards": [
                ["#E11D48", "EASY ESCAPE", "Hides task stress fast"],
                ["#F59E0B", "SCROLL FEED", "Feels good, breeds guilt"],
                ["#3B82F6", "DO IT LATER", "Makes starting 2x harder"],
            ],
            "phone_cta_norm": "AVOID WORK",
            "phone_urgent_hdr": "3 ESCAPE BAITS!",
            "phone_urgent_cards": [
                ["#E11D48", "NEW VIDEO", "Instant mood relief!"],
                ["#F59E0B", "GROUP MEME", "Just laugh for 1 min"],
                ["#E11D48", "EASY SCROLL", "Put off work again"],
            ],
            "phone_cta_urgent": "ESCAPE NOW",
            "swarm_badges": ["LATER", "AVOID", "SCROLL", "STRESS", "GUILT", "TRAP"],
            "scan_title": "BRAIN ALARM SCAN",
            "scan_stat": "NOT LAZY!",
            "scan_sub": "BRAIN TREATS WORK AS STRESS",
            "scan_left_lbl": "BIG TASK",
            "scan_right_lbl": "PHONE ESCAPE",
            "scan_footer": "START TINY TO CALM YOUR BRAIN",
            "laptop_hdr": "5-MINUTE START TRICK",
            "laptop_due": "DUE TODAY",
            "laptop_title": clean_laptop_title,
            "laptop_status": "|  (Just do 5 ugly minutes)",
            "laptop_callout": "5 MINUTES BREAKS THE FREEZE",
            "end_top": "PART 1 • YOU DECIDE",
            "option_a": "DO JUST 5 EASY MINUTES ON THE DESK NOW",
            "option_b": "SCROLL FOR RELIEF & FEEL GUILTY LATER",
            "end_sub": end_sub_line,
        }
        dialogue = [
            {"beat": "intro", "speaker": "pov", "text": "I know I need to start this... I just don't feel motivated at all. Maybe a quick phone break first."},
            {"beat": "trap", "speaker": "partner", "text": "STOP! Drop that phone! You're not lazy—your brain is trying to escape stress!"},
            {"beat": "explain", "speaker": "partner", "text": "Here is what's happening. When a task feels big or boring, your brain's alarm button fires—and pushes you toward your phone for quick comfort."},
            {"beat": "timer_react", "speaker": "pov", "text": "Wait... so putting work off isn't laziness—my brain just wants quick relief?!"},
            {"beat": "scan", "speaker": "partner", "text": "Look at this scan. Every avoidance scroll feels good for two minutes, then piles on stress and makes starting twice as hard."},
            {"beat": "desk", "speaker": "partner", "text": "Look at that laptop on your desk. Tell yourself you'll only do five tiny, ugly minutes—once you start, the freeze vanishes."},
            {"beat": "agree", "speaker": "pov", "text": "Okay... just five tiny minutes. No phone."},
            {"beat": "ping", "speaker": "partner", "text": "Three notifications just buzzed right on cue! Your brain is begging your hand to escape again!"},
        ]
    elif any(k in low for k in ("break", "fried", "tired", "burnout", "fatigue", "reset", "rest", "energy")):
        props = {
            "loc_main": "YOUR DESK • 2:14 PM",
            "loc_sub": f"{handle} • Part 1",
            "series_eyebrow": "EVERYDAY SCIENCE",
            "series_title": series_title,
            "timer_label": "ENERGY BATTERY",
            "phone_time": "2:14",
            "phone_norm_hdr": "FAKE BREAK TRAP",
            "phone_norm_cards": [
                ["#E11D48", "SCROLL BREAK", "Drains battery even more"],
                ["#F59E0B", "FAST VIDEOS", "Zero real mental rest"],
                ["#3B82F6", "MORE NOISE", "Triggers 3 PM brain fog"],
            ],
            "phone_cta_norm": "FAKE REST",
            "phone_urgent_hdr": "3 BATTERY DRAINS!",
            "phone_urgent_cards": [
                ["#E11D48", "RAPID CLIPS", "Overloads tired brain"],
                ["#F59E0B", "NEW ALERTS", "Stops your recharge"],
                ["#E11D48", "ENDLESS FEED", "Leaves you more tired"],
            ],
            "phone_cta_urgent": "DRAIN NOW",
            "swarm_badges": ["TIRED", "CRASH", "NOISE", "DRAIN", "FOG", "LOW"],
            "scan_title": "BRAIN BATTERY SCAN",
            "scan_stat": "0% RECHARGE",
            "scan_sub": "SCROLLING IS NOT REST",
            "scan_left_lbl": "PHONE BREAK",
            "scan_right_lbl": "STILL TIRED",
            "scan_footer": "REAL REST = NO SCREENS",
            "laptop_hdr": "10-MINUTE BRAIN RESET",
            "laptop_due": "SIMPLE FIX",
            "laptop_title": clean_laptop_title,
            "laptop_status": "|  (Step away for 10 quiet min)",
            "laptop_callout": "QUIET EYES = FAST RECHARGE",
            "end_top": "PART 1 • YOU DECIDE",
            "option_a": "TAKE 10 QUIET MINUTES WITH ZERO SCREENS",
            "option_b": "SCROLL YOUR PHONE & COME BACK MORE TIRED",
            "end_sub": end_sub_line,
        }
        dialogue = [
            {"beat": "intro", "speaker": "pov", "text": "Ugh, my head feels totally fried. Let me take a quick five-minute break on my phone."},
            {"beat": "trap", "speaker": "partner", "text": "STOP! Put that phone down! Scrolling on your break actually makes your brain MORE tired!"},
            {"beat": "explain", "speaker": "partner", "text": "Think about it. Fast videos force your tired brain to process hundreds of flashing clips in minutes—so your battery never actually recharges."},
            {"beat": "timer_react", "speaker": "pov", "text": "Wait... so my phone breaks aren't resting my brain at all?!"},
            {"beat": "scan", "speaker": "partner", "text": "Look at this scan. Screen breaks give you zero real recharge, which is why you come back feeling even heavier."},
            {"beat": "desk", "speaker": "partner", "text": "Look back at your desk. Walk away from every screen for ten quiet minutes, and watch your energy snap right back."},
            {"beat": "agree", "speaker": "pov", "text": "Alright... ten quiet minutes off-screen first."},
            {"beat": "ping", "speaker": "partner", "text": "Hear those three buzzes? Your tired brain is already pulling your hand right back to the phone!"},
        ]
    else:
        # Universal 100% plain-English everyday focus & phone trap (zero academic jargon!)
        stat_str = extracted_num if extracted_num else "-40% FOCUS"
        props = {
            "loc_main": "YOUR DESK • 2:14 PM",
            "loc_sub": f"{handle} • Part 1",
            "series_eyebrow": "HABITSAINS POV",
            "series_title": series_title,
            "timer_label": "FOCUS BATTERY",
            "phone_time": "2:14",
            "phone_norm_hdr": "14 FOCUS TRAPS",
            "phone_norm_cards": [
                ["#E11D48", "SHORT CLIPS", "Burns your focus fuel"],
                ["#3B82F6", "GROUP CHAT", "12 unread pings waiting"],
                ["#F59E0B", "SOCIAL FEED", "Makes real work feel dull"],
            ],
            "phone_cta_norm": "CHECK QUICKLY",
            "phone_urgent_hdr": "3 FOCUS TRAPS!",
            "phone_urgent_cards": [
                ["#E11D48", "VIRAL CLIP", "Instant fake excitement"],
                ["#F59E0B", "NEW REPLY", "Pulls you off track"],
                ["#E11D48", "TRENDING NOW", "Just 60 seconds?"],
            ],
            "phone_cta_urgent": "TAP NOW",
            "swarm_badges": ["SPIKE", "DRIFT", "PING!", "NOISE", "TRAP", "FOG"],
            "scan_title": "FOCUS BATTERY SCAN",
            "scan_stat": _clamp_prop(stat_str, 14, "-40% FOCUS"),
            "scan_sub": "EASY SCROLL -> REAL FOG",
            "scan_left_lbl": "QUICK SCROLL",
            "scan_right_lbl": "BRAIN FOG",
            "scan_footer": "FOCUS FUEL: DRAINED FAST",
            "laptop_hdr": "TODAY • BIG GOAL",
            "laptop_due": "DUE 5:00 PM",
            "laptop_title": clean_laptop_title,
            "laptop_status": "|  (Ready for clean focus)",
            "laptop_callout": "PHONE OUT OF SIGHT = EASY FOCUS",
            "end_top": "PART 1 • YOU DECIDE",
            "option_a": "PUT PHONE IN ANOTHER ROOM & LOCK IN",
            "option_b": "TAP ONE ALERT & LOSE YOUR WHOLE HOUR",
            "end_sub": end_sub_line,
        }
        dialogue = [
            {"beat": "intro", "speaker": "pov", "text": "Two fourteen already... my focus is slipping. Maybe one quick scroll will wake my brain up."},
            {"beat": "trap", "speaker": "partner", "text": "STOP! Drop that phone! That two-minute scroll is the exact reason you can't focus!"},
            {"beat": "explain", "speaker": "partner", "text": "Here is the simple truth. Your brain runs on natural focus fuel. Fast feeds burn it on fake excitement—making real work feel ten times harder."},
            {"beat": "timer_react", "speaker": "pov", "text": "Wait... one tiny check really drains my whole focus battery?!"},
            {"beat": "scan", "speaker": "partner", "text": "Look at this scan. Right after a quick scroll, your focus drops forty percent and leaves your head stuck in fog."},
            {"beat": "desk", "speaker": "partner", "text": "Look over at your desk. Put your phone in another room for thirty minutes—once it's out of sight, focus comes back fast."},
            {"beat": "agree", "speaker": "pov", "text": "Okay, phone stays out of sight. Locking in now."},
            {"beat": "ping", "speaker": "partner", "text": "Hear those three alerts hitting at once? Your hand is already reaching straight back for the phone!"},
        ]

    scene_env, action_pattern, hero_prop = _pick_3d_world_and_action(topic, low, pillar)
    props["scene_env"] = scene_env
    props["action_pattern"] = action_pattern
    props["hero_prop"] = hero_prop
    return {"props": props, "dialogue": dialogue}


def normalize_pov_3d_episode(
    raw_ep: dict[str, Any] | None,
    topic: str,
    angle: str = "",
    hook: str = "",
    scenes_meta: list[dict[str, Any]] | None = None,
    config: dict[str, Any] | None = None,
    pillar: str = "",
) -> dict[str, Any]:
    """Validate & length-clamp a Gemini or fallback pov_3d_episode so 3D props and 8 beats NEVER break."""
    base = build_topic_matched_pov_3d_episode(
        topic=topic, angle=angle, hook=hook, scenes_meta=scenes_meta, config=config, pillar=pillar
    )
    if not isinstance(raw_ep, dict):
        return base

    base_props = base["props"]
    raw_props = raw_ep.get("props") if isinstance(raw_ep.get("props"), dict) else {}
    str_limits = {
        "loc_main": 26,
        "loc_sub": 26,
        "series_eyebrow": 20,
        "series_title": 22,
        "timer_label": 18,
        "phone_time": 6,
        "phone_norm_hdr": 20,
        "phone_cta_norm": 16,
        "phone_urgent_hdr": 20,
        "phone_cta_urgent": 16,
        "scan_title": 24,
        "scan_stat": 15,
        "scan_sub": 25,
        "scan_left_lbl": 16,
        "scan_right_lbl": 16,
        "scan_footer": 26,
        "laptop_hdr": 24,
        "laptop_due": 14,
        "laptop_title": 28,
        "laptop_status": 30,
        "laptop_callout": 32,
        "end_top": 24,
        "option_a": 48,
        "option_b": 48,
        "end_sub": 48,
    }
    clean_props: dict[str, Any] = {}
    for k, lim in str_limits.items():
        clean_props[k] = _clamp_prop(raw_props.get(k), lim, str(base_props[k]))

    raw_env = str(raw_props.get("scene_env") or "").strip().lower()
    clean_props["scene_env"] = raw_env if raw_env in _VALID_SCENE_ENVS else str(base_props.get("scene_env", "sunrise_bedroom"))
    raw_act = str(raw_props.get("action_pattern") or "").strip().lower()
    clean_props["action_pattern"] = raw_act if raw_act in _VALID_ACTION_PATTERNS else str(base_props.get("action_pattern", "nightstand_to_desk"))
    raw_hp = str(raw_props.get("hero_prop") or "").strip().lower()
    clean_props["hero_prop"] = raw_hp if raw_hp in _VALID_HERO_PROPS else str(base_props.get("hero_prop", "alarm_phone"))

    # Sanitize 3-row phone notification card arrays
    for card_key in ("phone_norm_cards", "phone_urgent_cards"):
        raw_cards = raw_props.get(card_key)
        fallback_cards = base_props[card_key]
        out_cards: list[list[str]] = []
        if isinstance(raw_cards, list):
            for idx in range(3):
                item = raw_cards[idx] if idx < len(raw_cards) else fallback_cards[idx]
                fb = fallback_cards[idx]
                if isinstance(item, (list, tuple)) and len(item) >= 3:
                    col = str(item[0]).strip()
                    if not re.match(r"^#[0-9A-Fa-f]{6}$", col):
                        col = fb[0]
                    out_cards.append([col, _clamp_prop(item[1], 16, fb[1]), _clamp_prop(item[2], 26, fb[2])])
                else:
                    out_cards.append(list(fb))
        clean_props[card_key] = out_cards if len(out_cards) == 3 else [list(c) for c in fallback_cards]

    # Sanitize 6 floating 3D badge labels
    raw_badges = raw_props.get("swarm_badges")
    fb_badges = base_props["swarm_badges"]
    out_badges: list[str] = []
    if isinstance(raw_badges, list):
        for idx in range(6):
            raw_b = raw_badges[idx] if idx < len(raw_badges) else fb_badges[idx]
            if isinstance(raw_b, (list, tuple)) and len(raw_b) >= 2:
                raw_b = raw_b[1]
            out_badges.append(_clamp_prop(raw_b, 7, fb_badges[idx]).upper())
    clean_props["swarm_badges"] = out_badges if len(out_badges) == 6 else list(fb_badges)

    # Validate & align all 8 required beats in exact visual choreography order
    raw_dlg = raw_ep.get("dialogue")
    by_beat: dict[str, dict[str, str]] = {}
    if isinstance(raw_dlg, list):
        for item in raw_dlg:
            if not isinstance(item, dict):
                continue
            b = str(item.get("beat", "")).strip().lower()
            txt = " ".join(str(item.get("text", "")).split()).strip()
            if b in _BEAT_SPEAKERS and len(txt) >= 6:
                # Cap individual line length at 28 words so total runtime stays snappy (< 58s)
                words = txt.split()
                if len(words) > 28:
                    txt = " ".join(words[:28]).rstrip(" ,;:-") + "."
                by_beat[b] = {
                    "beat": b,
                    "speaker": _BEAT_SPEAKERS[b],
                    "text": txt,
                }

    base_by_beat = {d["beat"]: d for d in base["dialogue"]}
    clean_dialogue = [by_beat.get(b, base_by_beat[b]) for b in REQUIRED_POV_BEATS]

    return {"props": clean_props, "dialogue": clean_dialogue}


def _build_english_fallback(idea: TopicIdea, config: dict[str, Any]) -> dict[str, Any]:
    channel = config.get("channel", {})
    topic = idea.topic
    cta_yt = channel.get("cta_youtube", "Subscribe to HabitSains for daily Prophetic habits, Qur'an peace, and calm focus science.")
    cta_soc = channel.get("cta_social", "Save this Sunnah reminder for your week and share it with someone who needs calm today.")
    short_title = _truncate_words(topic, 58)
    short_sub = _truncate_words(topic, 48)
    dalil = getattr(idea, "dalil", None) if isinstance(getattr(idea, "dalil", None), dict) else None
    keywords = idea.keywords or ["sunnah", "quran", "prophetic habits", "mental peace", "brain science"]
    hashtags_list = [f"#{slugify(k, 22).replace('-', '')}" for k in keywords[:4] if slugify(k, 22)]
    for tag in ("#IslamicReminders", "#Sunnah", "#HabitSains"):
        if tag not in hashtags_list:
            hashtags_list.append(tag)

    if dalil:
        citation = str(dalil.get("citation") or "AUTHENTIC SUNNAH")
        translation = str(dalil.get("translation") or "")
        translit = str(dalil.get("transliteration") or "")
        pillar_lbl = getattr(idea, "pillar_label", "Prophetic Wisdom & Science")
        return {
            "youtube_long": {
                "title": _truncate_words(topic, 68),
                "alt_titles": [
                    f"{short_title} ({citation})",
                    f"Why This Sunnah Calms Your Mind: {short_sub}",
                    f"{short_title} — Prophetic Wisdom & Brain Science",
                ],
                "description": (
                    f"{idea.hook}\n\n"
                    f"Authentic Reference ({citation}):\n"
                    f"\"{translation}\"\n"
                    f"({translit})\n\n"
                    f"In this calm reflection on {channel.get('name', 'HabitSains')}, we explore {topic}—connecting timeless Islamic wisdom with simple everyday brain and habit science.\n\n"
                    f"{cta_yt}\n\n"
                    + " ".join(hashtags_list)
                ),
                "tags": list(dict.fromkeys(keywords + ["islamic habits", "sunnah", "quran wisdom", "mental peace", "habit science"])),
                "thumbnail": {
                    "badge": _truncate_words(pillar_lbl, 20).upper(),
                    "headline": _truncate_words(topic, 26).upper(),
                    "subheadline": citation,
                    "visual_prompt": f"Luminous serene Islamic twilight mosque dome reflected in calm water with soft antique gold glow, representing {topic}, strictly NO prophets, NO faces, NO text",
                },
                "scenes": [
                    {
                        "scene_no": 1,
                        "section": "REFLECT",
                        "visual_headline": short_sub,
                        "bullet_points": ["A quiet modern struggle", "Timeless Prophetic guidance", "One gentle shift for today"],
                        "on_screen_callout": citation,
                        "narration": f"{idea.hook} Take a quiet breath for a moment and reflect on how timeless Islamic wisdom speaks directly to what our minds struggle with today.",
                        "visual_prompt": "Serene twilight sky transitioning over calm water and distant mosque silhouette, strictly NO faces, NO text",
                    },
                    {
                        "scene_no": 2,
                        "section": "THE WISDOM",
                        "visual_headline": f"Verified Guidance: {citation}",
                        "bullet_points": [citation, translit[:60], "Timeless clarity for the heart"],
                        "on_screen_callout": translation[:72],
                        "narration": f"In {citation}, we are gently reminded: {translation} Pause and let the calm weight of those words settle inside your heart.",
                        "visual_prompt": "Antique gold geometric starlight radiating softly in obsidian night sky, strictly NO faces, NO text",
                    },
                    {
                        "scene_no": 3,
                        "section": "THE SCIENCE",
                        "visual_headline": "Why Your Brain Responds to Peace",
                        "bullet_points": ["Lowers racing stress loops", "Restores clear steady focus", "Builds lasting calm habits"],
                        "on_screen_callout": idea.angle[:72],
                        "narration": f"What is remarkable is how everyday brain and habit science echoes this exact rhythm. {idea.angle}. When your daily routine aligns with peace instead of constant noise, your energy stops burning out.",
                        "visual_prompt": "Luminous glowing particles forming calm balanced waves over deep indigo sky, strictly NO faces, NO text",
                    },
                    {
                        "scene_no": 4,
                        "section": "THE HIDDEN NOISE",
                        "visual_headline": "What Quietly Steals Your Calm",
                        "bullet_points": ["Nonstop rushing and alerts", "Harsh all-or-nothing pressure", "Forgetting to pause and breathe"],
                        "on_screen_callout": "Peace starts when you step off autopilot",
                        "narration": "Modern life pushes us to rush nonstop, compare ourselves to strangers, and expect instant results. That constant pressure leaves both the heart and the mind exhausted before evening even arrives.",
                        "visual_prompt": "Gentle rain falling onto dark earth turning into peaceful rippling water, strictly NO faces, NO text",
                    },
                    {
                        "scene_no": 5,
                        "section": "TODAY'S PRACTICE",
                        "visual_headline": "One Gentle Step to Start Today",
                        "bullet_points": ["Begin with one quiet minute", "Anchor your intention sincerely", "Repeat calmly every single day"],
                        "on_screen_callout": "Small sincere consistency beats rare intensity",
                        "narration": "You do not need to overhaul your entire life overnight. Choose one small, sincere moment today to practice this wisdom calmly, and let steady daily repetition reshape your peace of mind.",
                        "visual_prompt": "Soft golden dawn sunrise rising over lush peaceful meadow, strictly NO faces, NO text",
                    },
                    {
                        "scene_no": 6,
                        "section": "CLOSING",
                        "visual_headline": "Carry This Peace Forward",
                        "bullet_points": ["Save for hard days", "Practice calmly this week", "Share the reminder"],
                        "on_screen_callout": cta_soc[:72],
                        "narration": f"May this reminder bring clarity to your mind and quiet peace to your heart today. {cta_yt}",
                        "visual_prompt": "Tranquil starry crescent moon glowing gently over calm reflective horizon, strictly NO faces, NO text",
                    },
                ],
            },
            "shorts_reels_tiktok": {
                "title": _truncate_words(topic, 56),
                "hook_text": _truncate_words(topic, 40).upper(),
                "caption_yt_shorts": f"{idea.hook}\nReference: {citation}\n{cta_soc} {' '.join(hashtags_list[:4])} #Shorts",
                "caption_tiktok": f"{idea.hook}\nSource: {citation} — {cta_soc} {' '.join(hashtags_list[:5])}",
                "caption_ig_reels": f"{idea.hook}\n\n\"{translation}\"\n— {citation}\n\n{cta_soc}\n\n{' '.join(hashtags_list[:5])}",
                "hashtags": hashtags_list,
                "scenes": [
                    {
                        "scene_no": 1,
                        "badge": "01 • REFLECT",
                        "visual_headline": _truncate_words(topic, 36),
                        "narration": f"{idea.hook}",
                        "visual_prompt": "Vertical serene twilight sky and crescent over calm water, strictly NO faces, NO text",
                    },
                    {
                        "scene_no": 2,
                        "badge": "02 • WISDOM",
                        "visual_headline": citation,
                        "narration": f"In {citation}, we are reminded: {translation}",
                        "visual_prompt": "Vertical luminous antique gold starlight on dark obsidian backdrop, strictly NO faces, NO text",
                    },
                    {
                        "scene_no": 3,
                        "badge": "03 • CALM MIND",
                        "visual_headline": "Why Your Mind Needs This",
                        "narration": f"{idea.angle}. When you slow down and honor this simple rhythm, racing thoughts settle and real clarity returns.",
                        "visual_prompt": "Vertical golden particles flowing into peaceful concentric ripples, strictly NO faces, NO text",
                    },
                    {
                        "scene_no": 4,
                        "badge": "04 • PRACTICE",
                        "visual_headline": "One Small Step Today",
                        "narration": "Start small and sincere today. Even one quiet minute practiced with steady consistency slowly transforms your heart and focus.",
                        "visual_prompt": "Vertical gentle sunrise over peaceful green meadow, strictly NO faces, NO text",
                    },
                    {
                        "scene_no": 5,
                        "badge": "05 • SHARE PEACE",
                        "visual_headline": "Save & Share This Reminder",
                        "narration": f"{cta_soc}",
                        "visual_prompt": "Vertical starry night sky reflecting softly in tranquil pool, strictly NO faces, NO text",
                    },
                ],
                "pov_3d_episode": build_topic_matched_pov_3d_episode(
                    topic=topic,
                    angle=idea.angle,
                    hook=idea.hook,
                    scenes_meta=None,
                    config=config,
                    pillar=getattr(idea, "pillar", ""),
                ),
            },
            "carousel_social": {
                "title": short_title,
                "slides": [
                    {
                        "slide_no": 1,
                        "badge": "SLIDE 1/5 • COVER",
                        "headline": short_title,
                        "body": idea.hook,
                        "highlight": f"Verified Source: {citation} ->",
                        "visual_prompt": "Luminous midnight and antique gold Islamic architectural cover, strictly NO faces, NO text",
                    },
                    {
                        "slide_no": 2,
                        "badge": "SLIDE 2/5 • VERIFIED SOURCE",
                        "headline": citation,
                        "body": f"\"{translation}\"",
                        "highlight": translit[:72],
                        "visual_prompt": "Minimalist antique gold Islamic geometry on deep indigo, strictly NO faces, NO text",
                    },
                    {
                        "slide_no": 3,
                        "badge": "SLIDE 3/5 • MIND SCIENCE",
                        "headline": "Why Everyday Science Agrees",
                        "body": f"{idea.angle}. Quiet, steady habits protect your mental battery far better than nonstop rushing.",
                        "highlight": "Inner calm unlocks sharper daily clarity",
                        "visual_prompt": "Glowing peaceful waves and starlight on deep night sky, strictly NO faces, NO text",
                    },
                    {
                        "slide_no": 4,
                        "badge": "SLIDE 4/5 • DAILY STEP",
                        "headline": "How to Practice Gently Today",
                        "body": "Pause for one calm minute, renew your intention sincerely, and keep the habit small enough to repeat every day.",
                        "highlight": "Small consistent steps change everything",
                        "visual_prompt": "Soft golden dawn horizon over calm water, strictly NO faces, NO text",
                    },
                    {
                        "slide_no": 5,
                        "badge": "SLIDE 5/5 • REMINDER",
                        "headline": "Save & Share the Peace",
                        "body": "Keep this reminder close on heavy days and share it with a friend who needs a moment of calm.",
                        "highlight": cta_soc,
                        "visual_prompt": "Serene crescent moon above tranquil meadow, strictly NO faces, NO text",
                    },
                ],
                "caption_instagram": f"{idea.hook}\n\n\"{translation}\"\n— {citation}\n\nSwipe through to see how this timeless Islamic guidance aligns with everyday mind & habit science.\n\n{cta_soc}\n\n{' '.join(hashtags_list)}",
                "caption_linkedin": f"{idea.hook}\n\nTimeless reminder ({citation}): \"{translation}\"\n\nWhy this matters for daily clarity: {idea.angle}.\n\nWhich small calm habit anchors your workday the most?\n\n{' '.join(hashtags_list)}",
                "thread_x": [
                    f"1/5 {idea.hook} 🧵",
                    f"2/5 Verified reminder ({citation}): \"{translation}\"",
                    f"3/5 Why your mind responds so deeply: {idea.angle}.",
                    "4/5 Start small today: one quiet minute, sincere intention, gentle daily consistency.",
                    f"5/5 {cta_soc}",
                ],
                "post_threads": f"{idea.hook}\n\n\"{translation}\" ({citation})\n\nSmall calm habits practiced sincerely change far more than frantic rushing.",
                "post_facebook": f"{idea.hook}\n\n\"{translation}\"\n— {citation}\n\n{idea.angle}.\n\n{cta_soc}\n{' '.join(hashtags_list)}",
                "hashtags": hashtags_list,
            },
        }

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
                        "Why forcing yourself keeps failing",
                        "The simple reason your brain does this",
                        "3 easy habits you can try today",
                    ],
                    "on_screen_callout": "Work with your brain instead of fighting it",
                    "narration": f"{idea.hook} In the next two minutes, let's break down what is actually going on inside your head—and three dead-simple habits that fix it fast.",
                    "visual_prompt": f"Warm cozy editorial illustration about {topic}",
                },
                {
                    "scene_no": 2,
                    "section": "PART 1 • WHY IT HAPPENS",
                    "visual_headline": "What Actually Happens in Your Head",
                    "bullet_points": [
                        "Your focus battery runs out faster than you think",
                        "Quick phone hits burn your best energy early",
                        "Quiet breaks recharge your mind way faster",
                    ],
                    "on_screen_callout": "Your brain runs like a battery, not a nonstop machine",
                    "narration": f"Here is the simple truth behind {topic}. Your brain wakes up with a fresh focus battery every day—and tiny hidden habits quietly drain it before you even start your real work.",
                    "visual_prompt": "Glowing teal brain battery meter draining under phone alerts",
                },
                {
                    "scene_no": 3,
                    "section": "PART 2 • THE HIDDEN TRAP",
                    "visual_headline": "Why Common Advice Backfires",
                    "bullet_points": [
                        "Working longer hours creates heavier brain fog",
                        "Scrolling on breaks doesn't actually rest your mind",
                        "Keeping your phone nearby steals focus on autopilot",
                    ],
                    "on_screen_callout": "Pushing harder with an empty battery only makes you slower",
                    "narration": "Most advice just tells you to try harder and force more discipline. But when you take fake breaks on your phone and keep switching tabs, longer hours just leave you more exhausted.",
                    "visual_prompt": "Contrast graphic showing messy tangled focus vs calm steady clarity",
                },
                {
                    "scene_no": 4,
                    "section": "PART 3 • 3 SIMPLE FIXES",
                    "visual_headline": "3 Easy Shifts to Try Today",
                    "bullet_points": [
                        "Keep your phone in another room for 30 minutes",
                        "Take 10-minute breaks with zero screens",
                        "Start any scary task with just 5 ugly minutes",
                    ],
                    "on_screen_callout": "Make the right habit easier than the distraction",
                    "narration": "Try three tiny changes starting today. Put your phone in another room while you work, take real screen-free breaks, and shrink any hard task down to five easy minutes.",
                    "visual_prompt": "Three clean glowing steps leading from phone clutter to calm workspace",
                },
                {
                    "scene_no": 5,
                    "section": "7-DAY CHALLENGE",
                    "visual_headline": "Try the 7-Day Reset",
                    "bullet_points": [
                        "Test just one clean focus block each day",
                        "Notice how much lighter afternoons feel by Day 4",
                        "Keep the simple routine that works best for you",
                    ],
                    "on_screen_callout": "Tiny daily tweaks beat willpower every single time",
                    "narration": f"Test this for just seven days and notice how much clearer your head feels by day four. {cta_yt}",
                    "visual_prompt": "Calm 7-day progress trail glowing in warm amber and teal",
                },
            ],
        },
        "shorts_reels_tiktok": {
            "title": _truncate_words(topic, 56),
            "hook_text": "YOUR BRAIN ISN'T LAZY—HERE'S WHY",
            "caption_yt_shorts": f"{idea.hook} Watch the full breakdown on {channel.get('name', 'HabitSains')}! {' '.join(hashtags_list[:4])} #Shorts",
            "caption_tiktok": f"{idea.hook} Comment A or B below! {cta_soc} {' '.join(hashtags_list[:5])}",
            "caption_ig_reels": f"Save this for when you can't focus! {idea.hook} {cta_soc} {' '.join(hashtags_list[:5])}",
            "hashtags": hashtags_list,
            "scenes": [
                {
                    "scene_no": 1,
                    "badge": "01 • HOOK",
                    "visual_headline": _truncate_words(topic, 34),
                    "narration": f"{idea.hook}",
                    "visual_prompt": "Vertical bold everyday brain habit hook visual",
                },
                {
                    "scene_no": 2,
                    "badge": "02 • WHY",
                    "visual_headline": "Your Focus Runs Like a Battery",
                    "narration": "Quick phone checks and fake breaks drain your focus fuel early—making normal work feel way harder than it should.",
                    "visual_prompt": "Vertical glowing brain battery meter graphic",
                },
                {
                    "scene_no": 3,
                    "badge": "03 • THE FIX",
                    "visual_headline": "Phone Away. 5 Min Start.",
                    "narration": "Put your phone in another room, take real screen-free breaks, and start with just five tiny minutes.",
                    "visual_prompt": "Vertical clean 3-step habit graphic",
                },
                {
                    "scene_no": 4,
                    "badge": "04 • TRY IT",
                    "visual_headline": "Test This Today",
                    "narration": f"Try this one tiny shift today and feel the difference right away. {cta_soc}",
                    "visual_prompt": "Vertical calm summary CTA graphic",
                },
            ],
            "pov_3d_episode": build_topic_matched_pov_3d_episode(
                topic=topic,
                angle=idea.angle,
                hook=idea.hook,
                scenes_meta=None,
                config=config,
                pillar=getattr(idea, "pillar", ""),
            ),
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
        if config.get("channel", {}).get("language", "en") == "en" and isinstance(loaded.get("shorts_reels_tiktok"), dict):
            shorts_block = loaded["shorts_reels_tiktok"]
            shorts_block["pov_3d_episode"] = normalize_pov_3d_episode(
                shorts_block.get("pov_3d_episode"),
                topic=str(loaded["meta"].get("topic") or idea.topic),
                angle=str(loaded["meta"].get("angle") or idea.angle),
                hook=str(loaded["meta"].get("hook") or idea.hook),
                scenes_meta=shorts_block.get("scenes"),
                config=config,
                pillar=str(loaded["meta"].get("pillar") or getattr(idea, "pillar", "")),
            )
        return loaded

    gemini_result, used_model = _generate_with_gemini(idea, config)
    if gemini_result is not None:
        blueprint = gemini_result
        mode = f"gemini_api:{used_model}"
    else:
        blueprint = _build_structured_fallback(idea, config)
        mode = "structured_local_template"

    active_pillar = getattr(idea, "pillar", "")
    if (
        config.get("channel", {}).get("language", "en") == "en"
        and active_pillar not in ISLAMIC_FORMAT_PROFILES
        and isinstance(blueprint.get("shorts_reels_tiktok"), dict)
    ):
        shorts_block = blueprint["shorts_reels_tiktok"]
        shorts_block["pov_3d_episode"] = normalize_pov_3d_episode(
            shorts_block.get("pov_3d_episode"),
            topic=idea.topic,
            angle=idea.angle,
            hook=idea.hook,
            scenes_meta=shorts_block.get("scenes"),
            config=config,
            pillar=active_pillar,
        )

    blueprint["meta"] = {
        "topic": idea.topic,
        "pillar": getattr(idea, "pillar", "prophetic_habits"),
        "pillar_label": getattr(idea, "pillar_label", "Prophetic Habits & Daily Sunnah"),
        "dalil": dict(idea.dalil) if isinstance(getattr(idea, "dalil", None), dict) else None,
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
