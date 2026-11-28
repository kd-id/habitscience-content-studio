"""Studio v13 — High-CTR Curiosity YouTube Thumbnail Engine (1280x720 16:9).

Replaces legacy Pillow flat-box AI-slop thumbnails with bold, scroll-stopping, mobile-readable
YouTube thumbnails engineered specifically to create an irresistible curiosity gap:
  - Massive 2-3 line ultra-bold display typography (94-118px Impact/Arial Black) on the LEFT
    with 1 electric Gold/Amber/Red/Emerald POWER WORD + thick cinematic shadow (zero subtitles!).
  - Dramatic visual story & contrast on the RIGHT (real 2.5D paper-cutout diorama sprites +
    curved red/gold YouTube pointer arrow, blazing 24k Gold Arabic focal word + sunburst rays,
    storm-to-bloom split meter, gleaming needle & glowing pearl drop over ocean, cosmic 4-trap
    radar, or drained red 12% phone chaos vs golden dawn barakah!).
  - 100% HarfBuzz-shaped OFL `AmiriCalligraphy` for Arabic focal words (never broken boxes!).
  - 100% Offline & FREE (Rp 0) on both Windows & GitHub Actions Cloud (~0.5s per thumbnail).
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

from src.html_motion_overlay import find_chrome_executable
from src.islamic_story_acts import resolve_story_acts
from src.islamic_visual_engine import _load_amiri_font_css, _resolve_dalil_payload
from src.paper_craft_motion import _load_kit_data_uris


def _esc(text: Any) -> str:
    return html.escape(str(text or "").strip(), quote=False)


def _extract_focal_arabic_word(arabic: str) -> str:
    """Pick the single most iconic 1-2 word Arabic crest from the verse/hadith for visual drama."""
    raw = [w for w in str(arabic or "").split() if any("\u0621" <= c <= "\u064A" or "\u0671" <= c <= "\u06D3" for c in w)]
    if not raw:
        return "اللَّهُ"
    # Iconic ending word (e.g. الْقُلُوبُ, يُسْرًا, الْجُمُعَةِ, الْبَحْرَ, لَأَزِيدَنَّكُمْ) carries massive visual punch!
    last = raw[-1]
    if len(last) <= 4 and len(raw) >= 2:
        return f"{raw[-2]} {last}"
    return last


def resolve_high_ctr_hook(
    topic: str,
    thumb_meta: dict[str, Any] | None = None,
    dalil: dict[str, Any] | None = None,
    story_acts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive a punchy 2-3 line high-CTR curiosity hook (lines, accent line index, micro badge, right callout)."""
    topic_low = str(topic or "").lower()
    cit_low = str((dalil or {}).get("citation") or "").lower() if dalil else ""
    t_low = f"{topic_low} {cit_low}".strip()

    # Curated ultra-high-CTR curiosity hooks — ordered MOST SPECIFIC first (e.g. al-kahf BEFORE friday!)
    curated: list[tuple[tuple[str, ...], list[str], int, str, str]] = [
        # Secular / brain-science topics checked first so default dalil can NEVER override them
        (("face down", "phone face", "ruins focus"), ["FACE DOWN", "STILL RUINS", "YOUR BRAIN"], 1, "BRAIN TRAP", "12% FOCUS LEFT"),
        (("15 minutes", "scrolling destroys"), ["15 MINUTES", "RUINS", "3 HOURS!"], 1, "SCROLL TRAP", "FOCUS CRASH"),
        (("morning routine", "drains your dopamine"), ["MORNING", "STEALS", "DOPAMINE"], 1, "BEFORE 9 AM", "ENERGY DRAIN"),
        (("90-minute", "ultradian"), ["WORK LESS,", "2X YOUR", "FOCUS!"], 1, "90-MIN RULE", "PEAK BRAIN"),
        (("23-minute", "multitasking"), ["1 SWITCH =", "23 MIN", "LOST!"], 1, "BRAIN COST", "FOCUS KILLER"),
        (("dopamine", "coupling", "attention"), ["WHY YOU", "CAN'T", "FOCUS!"], 1, "BRAIN LAB", "DOPAMINE LOOP"),
        (("video games", "children", "teens"), ["WHAT GAMES", "DO TO KIDS'", "BRAINS"], 2, "BRAIN STUDY", "HIDDEN EFFECT"),
        (("procrastination", "laziness"), ["NOT LAZY.", "JUST", "STUCK."], 2, "BRAIN LOOP", "THE REAL CAUSE"),
        # Islamic curated high-CTR hooks (most specific first!)
        (("al-kahf", "kahf", "6470", "4 modern traps"), ["4 HIDDEN", "TRAPS", "EVERY WEEK"], 1, "SURAH AL-KAHF", "GUARD YOUR MIND"),
        (("13:28", "restless", "remembers allah"), ["STILL LOUD", "INSIDE?"], 1, "QUR'AN 13:28", "18-SEC CALM"),
        (("needle", "ocean", "2577", "small dua"), ["STOP ASKING", "TOO SMALL!"], 1, "HADITH QUDSI", "1 DROP VS OCEAN"),
        (("paralyzed", "feeling stuck", "6369", "worry", "mental weight"), ["FEELING", "STUCK?", "READ THIS"], 1, "BUKHARI 6369", "INSTANT RELIEF"),
        (("angry", "anger", "4782", "sit down"), ["ANGRY?", "SIT DOWN", "RIGHT NOW"], 0, "3-SEC RESET", "99% -> CALM"),
        (("friday", "jumu'ah", "jumuah", "854"), ["WHY FRIDAY", "HITS", "DIFFERENT"], 1, "1400 YRS AGO", "WEEKLY RESET"),
        (("waking up early", "2606", "fajr", "early morning"), ["DON'T MISS", "THIS HOUR!"], 1, "FAJR SECRET", "3X BARAKAH"),
        (("qailulah", "midday", "4431", "nap"), ["2 PM CRASH?", "20-MIN FIX"], 0, "SUNNAH NAP", "BRAIN RECHARGE"),
        (("94:5", "hardship", "ease", "sharh"), ["ONE WORD", "CHANGES", "HARDSHIP"], 0, "QUR'AN 94:5", "WITH NOT AFTER"),
        (("14:7", "shukr", "gratitude"), ["WHY ENOUGH", "FEELS", "EMPTY"], 2, "QUR'AN 14:7", "BRAIN REWIRE"),
        (("2:153", "sabr", "salah", "burnout"), ["5 PAUSES", "STOP", "BURNOUT"], 1, "QUR'AN 2:153", "STRESS RESET"),
        (("99:7", "atom", "tiny good"), ["NOTHING", "IS EVER", "WASTED"], 2, "QUR'AN 99:7", "ATOM'S WEIGHT"),
        (("1/3", "one third", "stomach", "2380"), ["STOP EATING", "PAST 1/3!"], 1, "SUNNAH RULE", "NO BRAIN FOG"),
        (("niyyah", "bukhari 1", "autopilot"), ["3 SECONDS", "BREAKS", "AUTOPILOT"], 0, "BUKHARI #1", "NIYYAH SHIFT"),
        (("smile", "1956", "charity"), ["1 SMILE =", "FREE", "THERAPY"], 1, "TIRMIDHI 1956", "CALMS 2 MINDS"),
        (("monday", "thursday", "fasting", "747"), ["WHY FASTING", "SHARPENS", "YOUR MIND"], 1, "SUNNAH FAST", "CLEAR FOCUS"),
        (("concern you", "2317", "minimalist"), ["DROP THIS,", "GAIN HOURS!"], 0, "FOCUS RULE", "ZERO DRAMA"),
        (("13:11", "inner change"), ["STOP WAITING", "FOR LUCK!"], 1, "QUR'AN 13:11", "INNER SHIFT"),
        (("6018", "speak good", "silent"), ["SAY LESS,", "THINK", "SHARPER"], 2, "BUKHARI 6018", "MENTAL SHIELD"),
        (("comparison", "2963", "social media"), ["SCROLLING", "STEALS", "YOUR JOY"], 1, "MUSLIM 2963", "ENVY CURE"),
        (("65:3", "tawakkul"), ["STOP TRYING", "TO CONTROL", "IT ALL"], 1, "QUR'AN 65:3", "PURE TAWAKKUL"),
        (("3:173", "hasbunallah"), ["4 WORDS", "STOP", "PANIC FAST"], 1, "QUR'AN 3:173", "ANXIETY ANCHOR"),
        (("2:286", "too heavy"), ["YOU CAN", "CARRY", "TODAY"], 1, "QUR'AN 2:286", "HIDDEN STRENGTH"),
        (("25:63", "petty arguments"), ["WALK AWAY", "FROM", "THE NOISE"], 0, "QUR'AN 25:63", "PROTECT PEACE"),
        (("sleep", "isha", "78:9", "bedtime", "6324"), ["STOP LATE", "SCROLLING!"], 1, "NIGHT RESET", "DEEP HEALING"),
        (("istiqamah", "6464", "small daily"), ["WHY BIG", "GOALS FAIL"], 1, "BUKHARI 6464", "1 TINY HABIT"),
        (("sujood", "prostration", "482"), ["WHY SUJOOD", "CALMS", "YOUR BRAIN"], 1, "ISLAMIC SCIENCE", "STRESS DROP"),
        (("wudu", "cool water", "223"), ["30-SEC WUDU", "RESETS", "YOUR MIND"], 1, "ISLAMIC SCIENCE", "CALM REFLEX"),
        (("14 hours", "1894", "sunnah fasting"), ["14H FASTING", "REBUILDS", "YOUR BRAIN"], 1, "ISLAMIC SCIENCE", "BRAIN REPAIR"),
    ]
    for keys, lines, hi_idx, badge, right_tag in curated:
        if any(k in t_low for k in keys):
            return {"lines": lines, "hi_idx": hi_idx, "badge": badge, "right_tag": right_tag}

    # Dynamic fallback from Gemini thumbnail headline or story_acts.hook_kicker
    raw = str((thumb_meta or {}).get("headline") or (story_acts or {}).get("hook_kicker") or topic or "STOP & WATCH").upper()
    clean = re.sub(r"\([^)]*\)", "", raw)
    clean = re.sub(r"[^A-Z0-9'?!&/\-\s]", " ", clean)
    words = [w for w in clean.split() if w][:6]
    if len(words) <= 2:
        lines = words or ["STOP &", "WATCH"]
    elif len(words) <= 4:
        lines = [" ".join(words[:2]), " ".join(words[2:])]
    else:
        lines = [" ".join(words[:2]), " ".join(words[2:4]), " ".join(words[4:6])]
    badge = str((dalil or {}).get("citation") or (thumb_meta or {}).get("badge") or "MUST WATCH").upper()[:18]
    right_tag = str((story_acts or {}).get("stat_badge") or "BRAIN & SUNNAH").upper()[:18]
    return {"lines": lines, "hi_idx": min(1, len(lines) - 1), "badge": badge, "right_tag": right_tag}


def _resolve_thumb_theme(blueprint: dict[str, Any], config: dict[str, Any] | None = None) -> str:
    meta = blueprint.get("meta") if isinstance(blueprint.get("meta"), dict) else {}
    pillar = str(meta.get("pillar") or "").strip().lower()
    if pillar in (
        "minute_wisdom_dua",
        "prophetic_habits",
        "sunnah_paper_story",
        "quran_mental_peace",
        "sunnah_particle_map",
        "hadith_cinematic_story",
        "islamic_science_qa_pov",
    ):
        return pillar
    style_map = {
        "islamic_nature_transform": "minute_wisdom_dua",
        "islamic_luminous_sky": "prophetic_habits",
        "islamic_paper_craft": "sunnah_paper_story",
        "islamic_gold_visualizer": "quran_mental_peace",
        "islamic_particle_map": "sunnah_particle_map",
        "islamic_cinematic_metaphor": "hadith_cinematic_story",
        "pov_3d_toon": "islamic_science_qa_pov",
    }
    for k in ("visual_style_short", "visual_style_long"):
        v = str(meta.get(k) or "").strip().lower()
        if v in style_map:
            return style_map[v]
    # Infer from topic/dalil when updating legacy YouTube videos
    low = f"{meta.get('topic', '')} {(meta.get('dalil') or {}).get('citation', '')}".lower()
    if any(k in low for k in ("13:28", "94:5", "14:7", "2:153", "99:7", "surah ar-ra'd", "dhikr")):
        return "quran_mental_peace"
    if any(k in low for k in ("friday", "jumu'ah", "jumuah", "niyyah", "smile", "fasting")):
        return "sunnah_paper_story"
    if any(k in low for k in ("needle", "ocean", "tawakkul", "hasbunallah", "2:286", "25:63")):
        return "hadith_cinematic_story"
    if any(k in low for k in ("al-kahf", "kahf", "1/3", "stomach", "comparison", "13:11")):
        return "sunnah_particle_map"
    if any(k in low for k in ("angry", "anger", "stuck", "paralyzed", "worry", "dua", "6369")):
        return "minute_wisdom_dua"
    if any(k in low for k in ("fajr", "qailulah", "sleep", "isha", "istiqamah", "barakah")):
        return "prophetic_habits"
    return "secular_brain"


def _right_visual_html(theme: str, dalil: dict[str, Any], hook: dict[str, Any], kit: dict[str, str]) -> tuple[str, dict[str, str]]:
    """Return `(right_focal_html, palette_vars)` for ultra-high-CTR YouTube composition."""
    ar_word = _esc(_extract_focal_arabic_word(dalil.get("arabic", "")))
    rtag = _esc(hook["right_tag"])

    if theme == "sunnah_paper_story" and kit:
        pal = {
            "bg": "linear-gradient(125deg, #0D2036 0%, #173C58 46%, #7BB8CA 100%)",
            "hi": "#FFD84D",
            "badge_bg": "#E11D48",
            "badge_fg": "#FFFFFF",
            "glow": "rgba(255, 216, 77, 0.34)",
        }
        vis = f"""
        <div class="right-stage">
          <img class="t-sun" src="{kit['sunburst_3d']}" alt="">
          <img class="t-book" src="{kit['open_book_3d']}" alt="">
          <img class="t-pres" src="{kit['presenter_point']}" alt="">
          <div class="t-metric-orb">
            <div class="tm-num">95%</div>
            <div class="tm-lbl">RESET</div>
          </div>
          <svg class="t-arrow" viewBox="0 0 220 140"><path d="M12 110 Q90 24 188 46" fill="none" stroke="#FF3B30" stroke-width="14" stroke-linecap="round"/><polygon points="182,18 214,52 170,74" fill="#FF3B30"/></svg>
          <div class="r-chip">{rtag}</div>
        </div>"""
        return vis, pal

    if theme == "quran_mental_peace":
        pal = {
            "bg": "radial-gradient(circle at 74% 50%, #3A2A0B 0%, #140F06 42%, #050507 82%)",
            "hi": "#FFD659",
            "badge_bg": "#D99B26",
            "badge_fg": "#070709",
            "glow": "rgba(255, 214, 89, 0.42)",
        }
        bnum = _esc(dalil.get("badge_num") or "13:28")
        vis = f"""
        <div class="right-stage">
          <svg class="t-svg-full" viewBox="0 0 640 720" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <radialGradient id="qSun" cx="54%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#FFE484" stop-opacity="0.92"/>
                <stop offset="32%" stop-color="#D99B26" stop-opacity="0.38"/>
                <stop offset="100%" stop-color="#050507" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <circle cx="345" cy="360" r="320" fill="url(#qSun)"/>
            <g transform="translate(345,360)" stroke="#F4C95D" fill="none">
              <circle r="245" stroke-width="2" stroke-opacity="0.38" stroke-dasharray="10 10"/>
              <rect x="-175" y="-175" width="350" height="350" stroke-width="2.5" stroke-opacity="0.45"/>
              <rect x="-175" y="-175" width="350" height="350" transform="rotate(45)" stroke-width="2.5" stroke-opacity="0.45"/>
              <circle r="158" fill="#08080C" stroke="#FFD659" stroke-width="5"/>
              <circle r="142" stroke="#FFD659" stroke-width="1.5" stroke-opacity="0.5"/>
            </g>
          </svg>
          <div class="q-focal-ar">{ar_word}</div>
          <div class="q-focal-num">AYAH {bnum}</div>
          <svg class="t-arrow" style="left:-26px;top:410px;" viewBox="0 0 220 140"><path d="M12 108 Q96 36 184 44" fill="none" stroke="#FFD659" stroke-width="13" stroke-linecap="round"/><polygon points="178,18 212,48 172,72" fill="#FFD659"/></svg>
        </div>"""
        return vis, pal

    if theme == "hadith_cinematic_story":
        pal = {
            "bg": "linear-gradient(115deg, #071220 0%, #102A42 46%, #2C5E74 100%)",
            "hi": "#FFE066",
            "badge_bg": "#F59E0B",
            "badge_fg": "#08121E",
            "glow": "rgba(255, 224, 102, 0.38)",
        }
        vis = f"""
        <div class="right-stage">
          <svg class="t-svg-full" viewBox="0 0 640 720" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="ocSky" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#1E2C42"/><stop offset="60%" stop-color="#C8A97E"/><stop offset="100%" stop-color="#FFE699"/>
              </linearGradient>
              <linearGradient id="ocSea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#5AA2AE"/><stop offset="55%" stop-color="#225B70"/><stop offset="100%" stop-color="#091C2B"/>
              </linearGradient>
              <radialGradient id="dropG" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#FFFFFF" stop-opacity="1"/><stop offset="35%" stop-color="#FFE588" stop-opacity="0.72"/><stop offset="100%" stop-color="#FFE588" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <rect x="20" y="24" width="596" height="672" rx="28" fill="#0A1A28" stroke="#FFE066" stroke-width="4" stroke-opacity="0.55"/>
            <g clip-path="inset(28px 24px 28px 24px round 24px)">
              <rect x="24" y="24" width="588" height="290" fill="url(#ocSky)"/>
              <rect x="24" y="314" width="588" height="380" fill="url(#ocSea)"/>
              <ellipse cx="330" cy="510" rx="235" ry="42" fill="none" stroke="#FFF4C2" stroke-width="3.5" opacity="0.55"/>
              <ellipse cx="330" cy="510" rx="145" ry="26" fill="none" stroke="#FFF4C2" stroke-width="4.5" opacity="0.82"/>
              <ellipse cx="330" cy="510" rx="68" ry="12" fill="none" stroke="#FFFFFF" stroke-width="5" opacity="0.95"/>
              <!-- Giant gleaming metallic silver needle -->
              <polygon points="306,24 354,24 344,295 330,368 316,295" fill="#F8FAFC"/>
              <polygon points="330,24 354,24 344,295 330,368" fill="#CBD5E1" opacity="0.65"/>
              <!-- Blinding luminous pearl droplet -->
              <circle cx="330" cy="435" r="115" fill="url(#dropG)"/>
              <path d="M330 384 C362 426 360 462 330 472 C300 462 298 426 330 384 Z" fill="#FFFFFF"/>
            </g>
          </svg>
          <svg class="t-arrow" style="left:-34px;top:375px;" viewBox="0 0 220 140"><path d="M12 104 Q94 42 186 58" fill="none" stroke="#FF3B30" stroke-width="14" stroke-linecap="round"/><polygon points="178,30 214,62 172,84" fill="#FF3B30"/></svg>
          <div class="r-chip" style="background:#FF3B30;color:#FFF;">{rtag}</div>
        </div>"""
        return vis, pal

    if theme == "minute_wisdom_dua":
        pal = {
            "bg": "linear-gradient(120deg, #1E0707 0%, #3A0E0C 38%, #0C2B22 100%)",
            "hi": "#FF5A36",
            "badge_bg": "#10B981",
            "badge_fg": "#051912",
            "glow": "rgba(255, 90, 54, 0.42)",
        }
        vis = f"""
        <div class="right-stage">
          <svg class="t-svg-full" viewBox="0 0 640 720" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <radialGradient id="redHeat" cx="35%" cy="42%" r="48%">
                <stop offset="0%" stop-color="#FF4D2E" stop-opacity="0.88"/><stop offset="100%" stop-color="#1E0707" stop-opacity="0"/>
              </radialGradient>
              <radialGradient id="grnCalm" cx="72%" cy="56%" r="50%">
                <stop offset="0%" stop-color="#34D399" stop-opacity="0.82"/><stop offset="100%" stop-color="#0C2B22" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <circle cx="210" cy="300" r="240" fill="url(#redHeat)"/>
            <circle cx="445" cy="410" r="250" fill="url(#grnCalm)"/>
            <!-- Left: Red Overwhelmed Stress Gauge -->
            <rect x="44" y="136" width="235" height="390" rx="28" fill="rgba(28,8,8,0.88)" stroke="#FF4D2E" stroke-width="5"/>
            <text x="162" y="196" text-anchor="middle" fill="#FF8A75" font-family="Arial Black, sans-serif" font-size="24">STRESS</text>
            <circle cx="162" cy="330" r="78" fill="none" stroke="rgba(255,77,46,0.28)" stroke-width="18"/>
            <circle cx="162" cy="330" r="78" fill="none" stroke="#FF4D2E" stroke-width="18" stroke-dasharray="430 490" transform="rotate(-90 162 330)"/>
            <text x="162" y="346" text-anchor="middle" fill="#FFFFFF" font-family="Arial Black, sans-serif" font-size="48">99%</text>
            <text x="162" y="476" text-anchor="middle" fill="#FF6B52" font-family="Segoe UI, sans-serif" font-weight="900" font-size="22">OVERLOADED</text>
            <!-- Right: Emerald Peaceful Reset -->
            <rect x="348" y="136" width="250" height="390" rx="28" fill="rgba(8,36,28,0.92)" stroke="#34D399" stroke-width="5"/>
            <text x="473" y="196" text-anchor="middle" fill="#6EE7B7" font-family="Arial Black, sans-serif" font-size="24">SUNNAH</text>
            <path d="M473 246 C512 308 514 348 473 376 C432 348 434 308 473 246 Z" fill="#34D399"/>
            <ellipse cx="473" cy="396" rx="74" ry="14" fill="none" stroke="#A7F3D0" stroke-width="3.5" opacity="0.8"/>
            <text x="473" y="476" text-anchor="middle" fill="#FFFFFF" font-family="Arial Black, sans-serif" font-size="26">INSTANT CALM</text>
            <!-- Bold Golden Transition Arrow -->
            <path d="M254 332 L360 332" stroke="#FFD84D" stroke-width="16" stroke-linecap="round"/>
            <polygon points="346,296 392,332 346,368" fill="#FFD84D"/>
          </svg>
          <div class="r-chip" style="background:#34D399;color:#052016;">{rtag}</div>
        </div>"""
        return vis, pal

    if theme == "sunnah_particle_map":
        pal = {
            "bg": "radial-gradient(circle at 72% 48%, #1C2E66 0%, #0A1128 52%, #050814 100%)",
            "hi": "#38BDF8",
            "badge_bg": "#F4C95D",
            "badge_fg": "#070C1A",
            "glow": "rgba(56, 189, 248, 0.38)",
        }
        vis = f"""
        <div class="right-stage">
          <svg class="t-svg-full" viewBox="0 0 640 720" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <radialGradient id="cGlow" cx="52%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#38BDF8" stop-opacity="0.52"/><stop offset="55%" stop-color="#F4C95D" stop-opacity="0.16"/><stop offset="100%" stop-color="#050814" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <circle cx="330" cy="360" r="300" fill="url(#cGlow)"/>
            <g transform="translate(330,350)" fill="none">
              <circle r="210" stroke="#38BDF8" stroke-width="3" stroke-opacity="0.45" stroke-dasharray="8 8"/>
              <circle r="140" stroke="#F4C95D" stroke-width="4" stroke-opacity="0.82"/>
              <line x1="-220" y1="0" x2="220" y2="0" stroke="#38BDF8" stroke-width="2" stroke-opacity="0.45"/>
              <line x1="0" y1="-220" x2="0" y2="220" stroke="#38BDF8" stroke-width="2" stroke-opacity="0.45"/>
              <!-- Glowing 4-Node Shield Pills -->
              <rect x="-86" y="-235" width="172" height="52" rx="26" fill="#FF3B30"/><text x="0" y="-201" text-anchor="middle" fill="#FFF" font-family="Arial Black, sans-serif" font-size="22">TRAP #1</text>
              <rect x="128" y="-26" width="172" height="52" rx="26" fill="#F4C95D"/><text x="214" y="8" text-anchor="middle" fill="#070C1A" font-family="Arial Black, sans-serif" font-size="22">TRAP #2</text>
              <rect x="-86" y="182" width="172" height="52" rx="26" fill="#38BDF8"/><text x="0" y="216" text-anchor="middle" fill="#070C1A" font-family="Arial Black, sans-serif" font-size="22">TRAP #3</text>
              <rect x="-295" y="-26" width="172" height="52" rx="26" fill="#34D399"/><text x="-209" y="8" text-anchor="middle" fill="#070C1A" font-family="Arial Black, sans-serif" font-size="22">TRAP #4</text>
              <circle r="76" fill="#0B132B" stroke="#F4C95D" stroke-width="4"/>
              <text x="0" y="16" text-anchor="middle" fill="#F4C95D" font-family="Arial Black, sans-serif" font-size="56">?</text>
            </g>
          </svg>
          <div class="r-chip" style="background:#38BDF8;color:#050B18;">{rtag}</div>
        </div>"""
        return vis, pal

    if theme == "prophetic_habits":
        pal = {
            "bg": "linear-gradient(125deg, #0A1328 0%, #1F2D54 45%, #B86D3B 100%)",
            "hi": "#FFD452",
            "badge_bg": "#FFD452",
            "badge_fg": "#0A1328",
            "glow": "rgba(255, 212, 82, 0.42)",
        }
        vis = f"""
        <div class="right-stage">
          <svg class="t-svg-full" viewBox="0 0 640 720" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <radialGradient id="dSun" cx="55%" cy="56%" r="52%">
                <stop offset="0%" stop-color="#FFF5C4" stop-opacity="0.98"/><stop offset="42%" stop-color="#F59E0B" stop-opacity="0.52"/><stop offset="100%" stop-color="#0A1328" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <circle cx="350" cy="400" r="300" fill="url(#dSun)"/>
            <circle cx="350" cy="395" r="120" fill="#FFF2B8" opacity="0.94"/>
            <!-- Crisp Dramatic Mosque Skyline Silhouette -->
            <path d="M24 550 Q180 515 350 532 T620 540 L620 690 L24 690 Z" fill="#070E20"/>
            <rect x="220" y="445" width="260" height="105" fill="#070E20"/>
            <path d="M266 445 C262 365 314 316 350 288 C386 316 438 365 434 445 Z" fill="#070E20"/>
            <rect x="164" y="328" width="24" height="220" fill="#070E20"/>
            <polygon points="164,328 176,272 188,328" fill="#070E20"/>
            <rect x="512" y="328" width="24" height="220" fill="#070E20"/>
            <polygon points="512,328 524,272 536,328" fill="#070E20"/>
            <!-- High-CTR Glowing Focus Battery Badge -->
            <rect x="210" y="102" width="286" height="96" rx="22" fill="rgba(7,14,32,0.88)" stroke="#34D399" stroke-width="4.5"/>
            <rect x="228" y="122" width="224" height="56" rx="12" fill="#10B981"/>
            <text x="340" y="162" text-anchor="middle" fill="#FFFFFF" font-family="Arial Black, sans-serif" font-size="36">98% CLEAR</text>
          </svg>
          <div class="r-chip" style="background:#FFD452;color:#0A1328;">{rtag}</div>
        </div>"""
        return vis, pal

    if theme == "islamic_science_qa_pov" and kit:
        pal = {
            "bg": "radial-gradient(circle at 74% 50%, #0E3A5C 0%, #091B30 46%, #040B16 100%)",
            "hi": "#38BDF8",
            "badge_bg": "#38BDF8",
            "badge_fg": "#040B16",
            "glow": "rgba(56, 189, 248, 0.44)",
        }
        brain_uri = kit.get("brain_bloom_3d") or kit.get("sunburst_3d") or ""
        vis = f"""
        <div class="right-stage">
          <svg class="t-svg-full" viewBox="0 0 640 720" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <radialGradient id="sciGlow" cx="55%" cy="48%" r="50%">
                <stop offset="0%" stop-color="#38BDF8" stop-opacity="0.62"/><stop offset="100%" stop-color="#040B16" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <circle cx="345" cy="345" r="285" fill="url(#sciGlow)"/>
            <circle cx="345" cy="345" r="215" fill="none" stroke="#38BDF8" stroke-width="3" stroke-dasharray="14 10" opacity="0.65"/>
            <circle cx="345" cy="345" r="255" fill="none" stroke="#FFD659" stroke-width="2" stroke-dasharray="8 14" opacity="0.50"/>
          </svg>
          <img style="position:absolute;right:58px;top:92px;width:470px;filter:drop-shadow(0 18px 34px rgba(0,0,0,0.65));" src="{brain_uri}" alt="">
          <div style="position:absolute;right:48px;top:64px;padding:12px 24px;border-radius:16px;background:#FFD659;color:#040B16;font-family:'Arial Black',sans-serif;font-size:32px;box-shadow:0 10px 24px rgba(0,0,0,0.5);">3D POV Q&amp;A</div>
          <svg class="t-arrow" style="left:-34px;top:375px;" viewBox="0 0 220 140"><path d="M12 108 Q96 36 184 44" fill="none" stroke="#FFD659" stroke-width="14" stroke-linecap="round"/><polygon points="178,18 212,48 172,72" fill="#FFD659"/></svg>
          <div class="r-chip" style="background:#38BDF8;color:#040B16;">{rtag}</div>
        </div>"""
        return vis, pal

    # Secular Brain-Science High-CTR Thumbnail (for existing HabitSains psychology Long videos!)
    pal = {
        "bg": "radial-gradient(circle at 75% 50%, #3D0C14 0%, #160A14 44%, #080A12 100%)",
        "hi": "#FF3B30",
        "badge_bg": "#FFD43B",
        "badge_fg": "#0A0C14",
        "glow": "rgba(255, 59, 48, 0.44)",
    }
    vis = f"""
    <div class="right-stage">
      <svg class="t-svg-full" viewBox="0 0 640 720" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <radialGradient id="bRed" cx="54%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#FF3B30" stop-opacity="0.72"/><stop offset="100%" stop-color="#080A12" stop-opacity="0"/>
          </radialGradient>
        </defs>
        <circle cx="345" cy="360" r="290" fill="url(#bRed)"/>
        <!-- Dramatic Glowing Phone + Draining 12% Focus Meter -->
        <rect x="220" y="110" width="250" height="475" rx="38" fill="#0F172A" stroke="#FF3B30" stroke-width="7"/>
        <rect x="242" y="142" width="206" height="408" rx="22" fill="#1E293B"/>
        <rect x="260" y="176" width="170" height="52" rx="14" fill="#EF4444"/>
        <rect x="260" y="246" width="170" height="52" rx="14" fill="#F59E0B"/>
        <rect x="260" y="316" width="170" height="52" rx="14" fill="#EF4444"/>
        <!-- Giant Red Alert Bubbles -->
        <circle cx="456" cy="146" r="46" fill="#FF3B30" stroke="#FFF" stroke-width="5"/>
        <text x="456" y="162" text-anchor="middle" fill="#FFF" font-family="Arial Black, sans-serif" font-size="38">99+</text>
        <circle cx="194" cy="285" r="40" fill="#FFD43B" stroke="#080A12" stroke-width="5"/>
        <text x="194" y="302" text-anchor="middle" fill="#080A12" font-family="Arial Black, sans-serif" font-size="48">!</text>
        <!-- Crashing Battery Bar -->
        <rect x="256" y="438" width="178" height="72" rx="14" fill="#090D18" stroke="#FF3B30" stroke-width="4"/>
        <rect x="266" y="448" width="38" height="52" rx="8" fill="#FF3B30"/>
        <text x="366" y="486" text-anchor="middle" fill="#FF6B6B" font-family="Arial Black, sans-serif" font-size="32">12%</text>
      </svg>
      <svg class="t-arrow" style="left:-36px;top:385px;" viewBox="0 0 220 140"><path d="M12 108 Q96 36 184 44" fill="none" stroke="#FFD43B" stroke-width="14" stroke-linecap="round"/><polygon points="178,18 212,48 172,72" fill="#FFD43B"/></svg>
      <div class="r-chip" style="background:#FF3B30;color:#FFF;">{rtag}</div>
    </div>"""
    return vis, pal


def build_high_ctr_thumbnail_html(blueprint: dict[str, Any], config: dict[str, Any]) -> tuple[str, str]:
    """Build 1280x720 high-CTR curiosity YouTube thumbnail HTML document + resolved theme key."""
    font_css = _load_amiri_font_css()
    meta = blueprint.get("meta") if isinstance(blueprint.get("meta"), dict) else {}
    thumb_meta = (blueprint.get("youtube_long") or {}).get("thumbnail") or {}
    scenes_meta = (blueprint.get("youtube_long") or {}).get("scenes") or []

    has_real_dalil = isinstance(meta.get("dalil"), dict) and bool((meta.get("dalil") or {}).get("arabic"))
    dalil = _resolve_dalil_payload(topic_meta=meta, scenes_meta=scenes_meta) if has_real_dalil else {}
    story_acts = resolve_story_acts(topic_meta=meta, scenes_meta=scenes_meta)
    theme = _resolve_thumb_theme(blueprint, config)
    hook = resolve_high_ctr_hook(
        topic=str(meta.get("topic") or ""),
        thumb_meta=thumb_meta,
        dalil=dalil if has_real_dalil else None,
        story_acts=story_acts,
    )
    kit = _load_kit_data_uris() if theme == "sunnah_paper_story" else {}
    right_html, pal = _right_visual_html(theme, dalil, hook, kit)

    lines = hook["lines"]
    hi_idx = hook["hi_idx"]
    max_len = max((len(ln) for ln in lines), default=8)
    if max_len >= 11:
        font_px = 82 if len(lines) >= 3 else 86
    elif max_len >= 9:
        font_px = 92 if len(lines) >= 3 else 100
    else:
        font_px = 104 if len(lines) >= 3 else 116
    lines_html = "".join(
        f'<div class="hl-line{" hi" if i == hi_idx else ""}">{_esc(ln)}</div>'
        for i, ln in enumerate(lines)
    )

    doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  {font_css}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: 1280px; height: 720px; overflow: hidden;
    background: #06080E;
    font-family: 'Arial Black', 'Segoe UI', Impact, sans-serif;
  }}
  .thumb {{
    position: relative; width: 1280px; height: 720px; overflow: hidden;
    background: {pal['bg']};
    display: flex; align-items: stretch;
  }}
  /* Subtle cinema vignette so giant left hook text pops with 100% contrast even at 168px mobile feed! */
  .thumb::before {{
    content: ""; position: absolute; inset: 0; z-index: 2; pointer-events: none;
    background: linear-gradient(90deg, rgba(4,7,14,0.84) 0%, rgba(4,7,14,0.62) 45%, rgba(4,7,14,0.08) 76%, rgba(4,7,14,0.22) 100%);
  }}
  .left-col {{
    position: relative; z-index: 6; width: 655px;
    padding: 58px 24px 58px 66px;
    display: flex; flex-direction: column; justify-content: center; gap: 22px;
  }}
  .micro-badge {{
    display: inline-block; align-self: flex-start;
    padding: 10px 24px; border-radius: 10px;
    background: {pal['badge_bg']}; color: {pal['badge_fg']};
    font-family: 'Segoe UI', 'Arial Black', sans-serif;
    font-size: 26px; font-weight: 900; letter-spacing: 2.6px; text-transform: uppercase;
    box-shadow: 0 10px 26px rgba(0,0,0,0.48);
  }}
  .hl-stack {{
    display: flex; flex-direction: column; gap: 2px;
  }}
  .hl-line {{
    font-family: 'Arial Black', Impact, 'Segoe UI', sans-serif;
    font-size: {font_px}px; font-weight: 900; line-height: 1.02;
    letter-spacing: -1.5px; text-transform: uppercase;
    white-space: nowrap;
    color: #FFFFFF;
    -webkit-text-stroke: 4px rgba(5, 8, 16, 0.85);
    paint-order: stroke fill;
    text-shadow: 0 10px 28px rgba(0, 0, 0, 0.85), 0 4px 0 rgba(0, 0, 0, 0.92);
  }}
  .hl-line.hi {{
    color: {pal['hi']};
    text-shadow: 0 0 36px {pal['glow']}, 0 10px 28px rgba(0, 0, 0, 0.90), 0 4px 0 rgba(0, 0, 0, 0.95);
  }}

  .right-stage {{
    position: relative; z-index: 4; flex: 1; height: 720px;
  }}
  .t-svg-full {{
    position: absolute; inset: 0; width: 100%; height: 100%;
  }}
  .q-focal-ar {{
    position: absolute; left: 26px; right: 0; top: 242px; text-align: center;
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; unicode-bidi: embed;
    font-size: 98px; font-weight: 700; color: #FFE484;
    text-shadow: 0 0 38px rgba(255, 214, 89, 0.88), 0 6px 18px rgba(0, 0, 0, 0.92);
  }}
  .q-focal-num {{
    position: absolute; left: 26px; right: 0; top: 432px; text-align: center;
    font-family: 'Segoe UI', sans-serif; font-size: 24px; font-weight: 900;
    letter-spacing: 5px; color: #F4C95D;
  }}

  /* Paper-craft 2.5D sprites on Right Stage */
  .t-sun {{
    position: absolute; width: 410px; right: 16px; top: 18px;
    filter: drop-shadow(0 16px 28px rgba(0,0,0,0.45));
  }}
  .t-book {{
    position: absolute; width: 520px; right: -10px; bottom: 20px;
    filter: drop-shadow(0 18px 28px rgba(0,0,0,0.48));
  }}
  .t-pres {{
    position: absolute; height: 470px; left: 10px; bottom: 0; z-index: 7;
    filter: drop-shadow(10px 16px 24px rgba(0,0,0,0.52));
  }}
  .t-metric-orb {{
    position: absolute; right: 126px; top: 128px; width: 190px; height: 190px;
    border-radius: 50%; background: #FAF6EA;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    box-shadow: 0 12px 32px rgba(0,0,0,0.38);
  }}
  .tm-num {{ font-size: 62px; font-weight: 900; color: #162B42; line-height: 1; }}
  .tm-lbl {{ font-size: 20px; font-weight: 900; letter-spacing: 2.5px; color: #C48329; margin-top: 4px; }}

  .t-arrow {{
    position: absolute; left: -32px; top: 182px; width: 215px; height: 135px; z-index: 9;
    filter: drop-shadow(0 8px 14px rgba(0,0,0,0.65));
  }}
  .r-chip {{
    position: absolute; right: 34px; bottom: 28px; z-index: 9;
    padding: 10px 22px; border-radius: 10px;
    background: #FFD84D; color: #0A1424;
    font-family: 'Segoe UI', 'Arial Black', sans-serif;
    font-size: 22px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase;
    box-shadow: 0 10px 26px rgba(0,0,0,0.55);
  }}
</style>
</head>
<body>
<div class="thumb">
  <div class="left-col">
    <div class="micro-badge">{_esc(hook['badge'])}</div>
    <div class="hl-stack">{lines_html}</div>
  </div>
  {right_html}
</div>
</body>
</html>"""
    return doc, theme


def render_high_ctr_youtube_thumbnail(
    blueprint: dict[str, Any],
    config: dict[str, Any],
    out_path: Path,
) -> Path:
    """Render a crisp 1280x720 high-CTR YouTube thumbnail PNG via Headless Chromium."""
    from playwright.sync_api import sync_playwright

    html_doc, theme = build_high_ctr_thumbnail_html(blueprint, config)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome_executable()
    launch_kw: dict[str, Any] = {
        "headless": True,
        "args": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"],
    }
    if chrome:
        launch_kw["executable_path"] = chrome

    with sync_playwright() as pw:
        br = pw.chromium.launch(**launch_kw)
        page = br.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1.0)
        page.set_content(html_doc, wait_until="load")
        page.evaluate("() => document.fonts.ready")
        page.evaluate(
            """() => Promise.all(Array.from(document.images).map(im =>
                im.complete ? Promise.resolve() : new Promise(r => { im.onload = r; im.onerror = r; })
            ))"""
        )
        page.screenshot(path=str(out_path), type="png")
        br.close()

    print(f"[thumbnail] Rendered Studio v13 High-CTR Thumbnail (1280x720, theme={theme}) -> {out_path.name}", flush=True)
    return out_path
