"""Studio v12.5 — Human-Editorial Instagram & LinkedIn Carousel Engine (5 Slides, 1080x1350 4:5).

Replaces legacy dark-box Pillow AI-slop cards with 6 genuinely handcrafted, magazine-grade
human-editorial carousel designs locked 1-to-1 to the 6 HabitSains Pillars & Format Packages:
  1. `minute_wisdom_dua`      (`islamic_nature_transform`)   -> Botanical Meadow Journal (warm cotton paper)
  2. `prophetic_habits`       (`islamic_luminous_sky`)       -> Fajr Editorial Horizon (pearl ivory + dawn watercolor)
  3. `sunnah_paper_story`     (`islamic_paper_craft`)        -> Handmade 2.5D Paper-Cutout Zine (real 11 PNG sprites!)
  4. `quran_mental_peace`     (`islamic_gold_visualizer`)    -> Mushaf Obsidian & 24k Gold Foil Edition
  5. `sunnah_particle_map`    (`islamic_particle_map`)       -> Celestial Astrolabe Folio
  6. `hadith_cinematic_story` (`islamic_cinematic_metaphor`) -> Kinfolk Coastal Fine-Art Essay

Key guarantees:
  - 100% HarfBuzz-shaped RTL Arabic calligraphy via embedded OFL Amiri (`Amiri-Regular.ttf` / `Amiri-Bold.ttf`)
    so every Arabic letter & full harakat renders like a printed Mushaf (zero boxes / disconnected glyphs!).
  - 5 distinct editorial compositions per carousel (Cover -> Sacred Text Spread -> Visual Mind-Science
    Diagram -> Pocket Field-Notes Checklist -> Shareable Keepsake Bookmark Card).
  - 100% Offline & FREE (Rp 0) on both Windows and GitHub Actions Ubuntu Cloud (~1.5s for all 5 PNGs).
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

# Strictly locked 1-to-1 Anti-Rancu Carousel Themes per Pillar / Visual Style
CAROUSEL_THEMES: dict[str, dict[str, Any]] = {
    "minute_wisdom_dua": {
        "theme_id": "botanical_journal",
        "edition_label": "BOTANICAL FIELD JOURNAL",
        "dark": False,
        "bg": "#F6F1E6",
        "bg_alt": "#EFE8D8",
        "card_bg": "#FCF9F2",
        "card_soft": "#E9EFE6",
        "ink": "#183327",
        "muted": "#516559",
        "accent": "#B55D3C",
        "accent_soft": "rgba(181, 93, 60, 0.14)",
        "good": "#256847",
        "rule": "rgba(24, 51, 39, 0.18)",
        "ar_color": "#183327",
        "quote_bg": "#EEF3EA",
        "serif": "'Georgia', 'Palatino Linotype', 'Book Antiqua', serif",
        "sans": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
    },
    "prophetic_habits": {
        "theme_id": "fajr_horizon",
        "edition_label": "PROPHETIC HABITS EDITORIAL",
        "dark": False,
        "bg": "#FAF7F0",
        "bg_alt": "#F1EADF",
        "card_bg": "#FFFFFF",
        "card_soft": "#F4EFE4",
        "ink": "#16243A",
        "muted": "#526075",
        "accent": "#B47B2B",
        "accent_soft": "rgba(180, 123, 43, 0.14)",
        "good": "#1E6E5C",
        "rule": "rgba(22, 36, 58, 0.16)",
        "ar_color": "#16243A",
        "quote_bg": "#F6EFE2",
        "serif": "'Georgia', 'Palatino Linotype', serif",
        "sans": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
    },
    "sunnah_paper_story": {
        "theme_id": "papercraft_zine",
        "edition_label": "SUNNAH PAPER-CRAFT EDITION",
        "dark": False,
        "bg": "#B1D5E0",
        "bg_alt": "#9EC7D4",
        "card_bg": "#FAF6EA",
        "card_soft": "#F1EBDA",
        "ink": "#1D3146",
        "muted": "#465C71",
        "accent": "#C48A2D",
        "accent_soft": "rgba(196, 138, 45, 0.18)",
        "good": "#0F6B50",
        "rule": "rgba(29, 49, 70, 0.18)",
        "ar_color": "#1D3146",
        "quote_bg": "#FAF6EA",
        "serif": "'Georgia', 'Trebuchet MS', serif",
        "sans": "'Segoe UI', 'Trebuchet MS', Arial, sans-serif",
    },
    "quran_mental_peace": {
        "theme_id": "mushaf_obsidian",
        "edition_label": "QUR'AN REFLECTION FOLIO",
        "dark": True,
        "bg": "#0A0A0E",
        "bg_alt": "#121218",
        "card_bg": "#111117",
        "card_soft": "#17161E",
        "ink": "#F6F0E4",
        "muted": "#B6AE9E",
        "accent": "#DFBD6D",
        "accent_soft": "rgba(223, 189, 109, 0.14)",
        "good": "#84C5A3",
        "rule": "rgba(223, 189, 109, 0.28)",
        "ar_color": "#F7DF9A",
        "quote_bg": "#121118",
        "serif": "'Georgia', 'Times New Roman', serif",
        "sans": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
    },
    "sunnah_particle_map": {
        "theme_id": "astrolabe_folio",
        "edition_label": "MIND & SUNNAH ATLAS",
        "dark": True,
        "bg": "#0C1425",
        "bg_alt": "#111C33",
        "card_bg": "#121D34",
        "card_soft": "#172540",
        "ink": "#F4EFE6",
        "muted": "#A3B4CC",
        "accent": "#E4C475",
        "accent_soft": "rgba(228, 196, 117, 0.14)",
        "good": "#67C8B5",
        "rule": "rgba(228, 196, 117, 0.24)",
        "ar_color": "#F5D98E",
        "quote_bg": "#101B30",
        "serif": "'Georgia', 'Palatino Linotype', serif",
        "sans": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
    },
    "hadith_cinematic_story": {
        "theme_id": "kinfolk_essay",
        "edition_label": "REFLECTIVE ESSAY SERIES",
        "dark": False,
        "bg": "#EFEAE0",
        "bg_alt": "#E5DDD0",
        "card_bg": "#F9F6F0",
        "card_soft": "#E9E2D5",
        "ink": "#1F252C",
        "muted": "#58626E",
        "accent": "#9E6A33",
        "accent_soft": "rgba(158, 106, 51, 0.14)",
        "good": "#2E6A62",
        "rule": "rgba(31, 37, 44, 0.18)",
        "ar_color": "#1F252C",
        "quote_bg": "#F7F3EB",
        "serif": "'Georgia', 'Times New Roman', serif",
        "sans": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
    },
}

_STYLE_TO_PILLAR: dict[str, str] = {
    "islamic_nature_transform": "minute_wisdom_dua",
    "islamic_luminous_sky": "prophetic_habits",
    "islamic_paper_craft": "sunnah_paper_story",
    "islamic_gold_visualizer": "quran_mental_peace",
    "islamic_particle_map": "sunnah_particle_map",
    "islamic_cinematic_metaphor": "hadith_cinematic_story",
}


def resolve_carousel_theme(blueprint: dict[str, Any], config: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
    """Resolve the locked Anti-Rancu carousel editorial theme from pillar or visual_style."""
    meta = blueprint.get("meta") if isinstance(blueprint.get("meta"), dict) else {}
    pillar = str(meta.get("pillar") or "").strip().lower()
    if pillar in CAROUSEL_THEMES:
        return pillar, CAROUSEL_THEMES[pillar]
    for key in ("visual_style_short", "visual_style_long"):
        st = str(meta.get(key) or "").strip().lower()
        if st in _STYLE_TO_PILLAR:
            p = _STYLE_TO_PILLAR[st]
            return p, CAROUSEL_THEMES[p]
    if config:
        eng = str((config.get("video") or {}).get("engine_mode") or "").strip().lower()
        if eng in _STYLE_TO_PILLAR:
            p = _STYLE_TO_PILLAR[eng]
            return p, CAROUSEL_THEMES[p]
    return "prophetic_habits", CAROUSEL_THEMES["prophetic_habits"]


def _esc(text: Any) -> str:
    return html.escape(str(text or "").strip(), quote=False)


def _clean_editorial_badge(raw: str, fallback: str) -> str:
    """Strip robotic AI-slop prefixes like 'SLIDE 1/5 • COVER' into refined editorial labels."""
    s = re.sub(r"^\s*SLIDE\s*\d+\s*/\s*\d+\s*[•·:\-—]*\s*", "", str(raw or ""), flags=re.IGNORECASE).strip()
    if not s or s.upper() in ("COVER", "CTA", "ACTION", "HOOK"):
        return fallback
    return s.upper()[:34]


def _extract_practice_steps(slide_body: str, slide_highlight: str, story_acts: dict[str, Any]) -> list[tuple[str, str]]:
    """Turn Slide 4 body text into 3 crisp, scannable human pocket-journal steps."""
    raw = str(slide_body or "").strip()
    # Try explicit numbered steps: "1) ... 2) ... 3) ..."
    numbered = re.split(r"(?:^|\s)\d+[\)\.\-]\s+", raw)
    numbered = [p.strip(" .;—-") for p in numbered if len(p.strip()) >= 8]
    if len(numbered) >= 2:
        items = numbered[:3]
    else:
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", raw) if len(s.strip()) >= 8]
        items = sents[:3]

    defaults = [
        f"Pause for one quiet breath before reacting — shift into {story_acts.get('after_label', 'calm Sunnah rhythm').lower()}.",
        f"Anchor your heart with {story_acts.get('core_lesson', 'one sincere tiny habit today')}",
        "Keep it small enough to repeat effortlessly every single day without burnout.",
    ]
    while len(items) < 3:
        items.append(defaults[len(items)])

    labels = ["PAUSE", "ANCHOR", "REPEAT"]
    return [(labels[i], items[i]) for i in range(3)]


def _theme_cover_art_svg(theme_id: str, th: dict[str, Any], dalil: dict[str, Any], kit: dict[str, str]) -> str:
    """Bespoke art-directed visual centerpiece for Slide 1 (Cover) — distinct for every pillar!"""
    if theme_id == "papercraft_zine" and kit:
        sun = kit.get("sunburst_3d", "")
        cal = kit.get("calendar_3d", "")
        prs = kit.get("presenter_point", "")
        cld = kit.get("cloud_3d", "")
        return f"""
        <div class="paper-hero">
          <img class="p-cloud c1" src="{cld}" alt="">
          <img class="p-cloud c2" src="{cld}" alt="">
          <img class="p-sun" src="{sun}" alt="">
          <img class="p-cal" src="{cal}" alt="">
          <img class="p-pres" src="{prs}" alt="">
        </div>"""

    if theme_id == "botanical_journal":
        return f"""
        <svg class="hero-svg" viewBox="0 0 880 340" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="botSky" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#E7EFE6"/>
              <stop offset="100%" stop-color="#F6F1E6"/>
            </linearGradient>
          </defs>
          <rect x="0" y="0" width="880" height="340" rx="22" fill="url(#botSky)" stroke="{th['rule']}" stroke-width="1.5"/>
          <!-- Minimal watercolor hills -->
          <path d="M0 278 Q220 218 440 256 T880 238 L880 340 L0 340 Z" fill="#C9DEC7" opacity="0.72"/>
          <path d="M0 302 Q290 258 580 284 T880 274 L880 340 L0 340 Z" fill="#9EC19E" opacity="0.58"/>
          <!-- Sunlit droplet & concentric water ripples -->
          <circle cx="440" cy="118" r="54" fill="#B55D3C" opacity="0.14"/>
          <path d="M440 74 C458 104 460 124 440 140 C420 124 422 104 440 74 Z" fill="#256847" opacity="0.88"/>
          <ellipse cx="440" cy="212" rx="115" ry="18" fill="none" stroke="#256847" stroke-width="1.6" opacity="0.34"/>
          <ellipse cx="440" cy="212" rx="68" ry="10" fill="none" stroke="#256847" stroke-width="1.8" opacity="0.55"/>
          <!-- Hand-drawn olive branches framing left & right -->
          <g stroke="#183327" stroke-width="2" fill="none" opacity="0.62">
            <path d="M72 290 C105 220 135 165 186 112"/>
            <ellipse cx="122" cy="206" rx="18" ry="7" transform="rotate(-38 122 206)" fill="#9EC19E"/>
            <ellipse cx="152" cy="162" rx="17" ry="6.5" transform="rotate(-24 152 162)" fill="#9EC19E"/>
            <ellipse cx="104" cy="170" rx="16" ry="6" transform="rotate(28 104 170)" fill="#C9DEC7"/>
            <path d="M808 290 C775 220 745 165 694 112"/>
            <ellipse cx="758" cy="206" rx="18" ry="7" transform="rotate(38 758 206)" fill="#9EC19E"/>
            <ellipse cx="728" cy="162" rx="17" ry="6.5" transform="rotate(24 728 162)" fill="#9EC19E"/>
            <ellipse cx="776" cy="170" rx="16" ry="6" transform="rotate(-28 776 170)" fill="#C9DEC7"/>
          </g>
          <circle cx="192" cy="108" r="6" fill="#B55D3C" opacity="0.72"/>
          <circle cx="688" cy="108" r="6" fill="#B55D3C" opacity="0.72"/>
        </svg>"""

    if theme_id == "fajr_horizon":
        return f"""
        <svg class="hero-svg" viewBox="0 0 880 340" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="fajrG" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#1C2E4A"/>
              <stop offset="48%" stop-color="#58547A"/>
              <stop offset="82%" stop-color="#DDA273"/>
              <stop offset="100%" stop-color="#F6DEC0"/>
            </linearGradient>
          </defs>
          <rect x="0" y="0" width="880" height="340" rx="22" fill="url(#fajrG)"/>
          <!-- Soft rising dawn sun glow & crescent -->
          <circle cx="440" cy="222" r="105" fill="#FDE8B8" opacity="0.30"/>
          <circle cx="440" cy="222" r="52" fill="#FFF3D2" opacity="0.78"/>
          <circle cx="696" cy="78" r="18" fill="#FCECC0" opacity="0.92"/>
          <circle cx="705" cy="72" r="15" fill="#233352"/>
          <!-- Delicate stars -->
          <g fill="#FFF9E6" opacity="0.75">
            <circle cx="140" cy="64" r="2.2"/><circle cx="230" cy="96" r="1.6"/>
            <circle cx="310" cy="52" r="2.0"/><circle cx="560" cy="70" r="1.8"/>
            <circle cx="775" cy="112" r="2.1"/>
          </g>
          <!-- Editorial mosque silhouette & mirror reflection -->
          <path d="M0 264 Q220 248 440 256 T880 260 L880 272 L0 272 Z" fill="#142038"/>
          <rect x="366" y="218" width="148" height="48" fill="#142038"/>
          <path d="M392 218 C390 174 420 150 440 136 C460 150 490 174 488 218 Z" fill="#142038"/>
          <rect x="438.5" y="118" width="3" height="20" fill="#142038"/>
          <rect x="328" y="156" width="13" height="110" fill="#142038"/>
          <polygon points="328,156 334.5,130 341,156" fill="#142038"/>
          <rect x="539" y="156" width="13" height="110" fill="#142038"/>
          <polygon points="539,156 545.5,130 552,156" fill="#142038"/>
          <!-- Calm water reflection lines -->
          <rect x="0" y="272" width="880" height="68" fill="#1E2C47" opacity="0.88"/>
          <g stroke="#F8D89B" stroke-width="2" opacity="0.45">
            <line x1="360" y1="290" x2="520" y2="290"/>
            <line x1="390" y1="306" x2="490" y2="306"/>
            <line x1="412" y1="322" x2="468" y2="322"/>
          </g>
        </svg>"""

    if theme_id == "mushaf_obsidian":
        bnum = _esc(dalil.get("badge_num") or "AYAH")
        blbl = _esc(dalil.get("badge_label") or "AYAH")
        sar = _esc(dalil.get("surah_ar") or "")
        return f"""
        <div class="mushaf-emblem">
          <svg viewBox="0 0 880 340" xmlns="http://www.w3.org/2000/svg" class="hero-svg">
            <defs>
              <radialGradient id="gAura" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#DFBD6D" stop-opacity="0.22"/>
                <stop offset="65%" stop-color="#DFBD6D" stop-opacity="0.04"/>
                <stop offset="100%" stop-color="#0A0A0E" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <rect x="0" y="0" width="880" height="340" fill="url(#gAura)"/>
            <!-- Delicate Rub el Hizb octagonal filigree -->
            <g transform="translate(440,170)" fill="none" stroke="#DFBD6D">
              <circle r="138" stroke-opacity="0.20" stroke-width="1"/>
              <circle r="118" stroke-opacity="0.42" stroke-width="1.2"/>
              <rect x="-86" y="-86" width="172" height="172" stroke-opacity="0.34" stroke-width="1.2"/>
              <rect x="-86" y="-86" width="172" height="172" transform="rotate(45)" stroke-opacity="0.34" stroke-width="1.2"/>
              <circle r="76" fill="#0B0B10" stroke="#DFBD6D" stroke-width="1.8" stroke-opacity="0.82"/>
              <circle r="67" stroke="#DFBD6D" stroke-width="0.9" stroke-opacity="0.38"/>
              <line x1="-290" y1="0" x2="-155" y2="0" stroke-opacity="0.34" stroke-width="1"/>
              <line x1="155" y1="0" x2="290" y2="0" stroke-opacity="0.34" stroke-width="1"/>
              <circle cx="-155" cy="0" r="3" fill="#DFBD6D" opacity="0.65"/>
              <circle cx="155" cy="0" r="3" fill="#DFBD6D" opacity="0.65"/>
            </g>
          </svg>
          <div class="mushaf-badge-txt">
            <div class="mb-num">{bnum}</div>
            <div class="mb-lbl">{blbl}</div>
          </div>
          <div class="mushaf-surah-ar">{sar}</div>
        </div>"""

    if theme_id == "astrolabe_folio":
        return f"""
        <svg class="hero-svg" viewBox="0 0 880 340" xmlns="http://www.w3.org/2000/svg">
          <rect x="0" y="0" width="880" height="340" rx="20" fill="#101B30" stroke="rgba(228,196,117,0.22)" stroke-width="1.2"/>
          <g transform="translate(440,170)" fill="none" stroke="#E4C475">
            <circle r="132" stroke-opacity="0.16" stroke-dasharray="4 6" stroke-width="1.2"/>
            <circle r="96" stroke-opacity="0.34" stroke-width="1.2"/>
            <circle r="54" stroke-opacity="0.22" stroke-width="1"/>
            <ellipse rx="150" ry="54" transform="rotate(-18)" stroke="#67C8B5" stroke-opacity="0.34" stroke-width="1.2"/>
            <ellipse rx="150" ry="54" transform="rotate(18)" stroke="#E4C475" stroke-opacity="0.28" stroke-width="1.2"/>
            <line x1="-220" y1="0" x2="220" y2="0" stroke-opacity="0.16" stroke-width="1"/>
            <line x1="0" y1="-150" x2="0" y2="150" stroke-opacity="0.16" stroke-width="1"/>
            <!-- Crescent center -->
            <path d="M-6 -26 A28 28 0 1 0 -6 26 A21 21 0 1 1 -6 -26 Z" fill="#E4C475" opacity="0.92"/>
            <!-- 4 Cardinal Constellation Nodes -->
            <circle cx="0" cy="-96" r="5" fill="#E4C475"/><circle cx="96" cy="0" r="5" fill="#67C8B5"/>
            <circle cx="0" cy="96" r="5" fill="#E4C475"/><circle cx="-96" cy="0" r="5" fill="#67C8B5"/>
            <circle cx="-132" cy="-54" r="3" fill="#FFF7DE" opacity="0.8"/>
            <circle cx="144" cy="-48" r="2.5" fill="#FFF7DE" opacity="0.7"/>
            <circle cx="118" cy="76" r="3" fill="#67C8B5" opacity="0.8"/>
            <circle cx="-126" cy="68" r="2.5" fill="#E4C475" opacity="0.8"/>
          </g>
        </svg>"""

    # Default / Pillar 6: Kinfolk Coastal Fine-Art Essay (Atmospheric Ocean & Golden Needle Drop Plate!)
    return f"""
    <svg class="hero-svg" viewBox="0 0 880 340" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="kSky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#3E4959"/>
          <stop offset="56%" stop-color="#C9B79B"/>
          <stop offset="100%" stop-color="#F6DFAC"/>
        </linearGradient>
        <linearGradient id="kSea" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#79A3AB"/>
          <stop offset="55%" stop-color="#3F6E7D"/>
          <stop offset="100%" stop-color="#1E3D4C"/>
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="880" height="340" rx="6" fill="#F9F6F0" stroke="#D5CCBC" stroke-width="2"/>
      <g clip-path="inset(14px round 2px)">
        <rect x="14" y="14" width="852" height="148" fill="url(#kSky)"/>
        <rect x="14" y="162" width="852" height="164" fill="url(#kSea)"/>
        <g stroke="#FCEFC7" stroke-opacity="0.34" stroke-width="2">
          <line x1="120" y1="186" x2="760" y2="186"/>
          <line x1="170" y1="210" x2="710" y2="210"/>
          <line x1="210" y1="238" x2="670" y2="238"/>
          <line x1="260" y1="270" x2="620" y2="270"/>
        </g>
        <!-- Concentric sunlit ripple + gleaming silver needle & pearl drop -->
        <ellipse cx="440" cy="236" rx="124" ry="20" fill="none" stroke="#FFF6D6" stroke-width="1.6" opacity="0.52"/>
        <ellipse cx="440" cy="236" rx="68" ry="11" fill="none" stroke="#FFF6D6" stroke-width="2" opacity="0.78"/>
        <polygon points="434,14 446,14 443,152 440,178 437,152" fill="#FFFFFF" opacity="0.95"/>
        <circle cx="440" cy="202" r="24" fill="#FFF4CC" opacity="0.36"/>
        <path d="M440 186 C449 198 449 208 440 212 C431 208 431 198 440 186 Z" fill="#FFFDF7"/>
      </g>
    </svg>"""


def _science_diagram_svg(story_acts: dict[str, Any], th: dict[str, Any]) -> str:
    """Crisp editorial infographic SVG for Slide 3 (Mind Science) — zero AI-slop empty gap!"""
    kind = str(story_acts.get("explainer_visual") or "brain_wave_calm")
    before_lbl = _esc(story_acts.get("before_label") or "NOISY AUTOPILOT")
    after_lbl = _esc(story_acts.get("after_label") or "CALM SUNNAH RHYTHM")
    stat_lbl = _esc(story_acts.get("stat_badge") or "CALM CLARITY RESTORED")
    ink = th["ink"]
    muted = th["muted"]
    acc = th["accent"]
    good = th["good"]
    warn = "#C94A38" if not th["dark"] else "#F28472"
    card_bg = th["card_soft"]
    rule = th["rule"]

    if kind == "one_third_pie":
        visual_inner = f"""
          <g transform="translate(210,115)">
            <circle r="72" fill="none" stroke="{rule}" stroke-width="26"/>
            <circle r="72" fill="none" stroke="{acc}" stroke-width="26" stroke-dasharray="151 302" transform="rotate(-90)"/>
            <circle r="72" fill="none" stroke="#4F96B8" stroke-width="26" stroke-dasharray="151 302" transform="rotate(30)"/>
            <circle r="72" fill="none" stroke="{good}" stroke-width="26" stroke-dasharray="151 302" transform="rotate(150)"/>
            <text x="0" y="7" text-anchor="middle" fill="{ink}" font-family="Georgia, serif" font-size="24" font-weight="700">1/3</text>
          </g>
          <g transform="translate(360,64)" font-family="Segoe UI, sans-serif" font-size="20" font-weight="700" fill="{ink}">
            <circle cx="0" cy="0" r="8" fill="{acc}"/><text x="24" y="7">ONE THIRD FOR FOOD</text>
            <circle cx="0" cy="52" r="8" fill="#4F96B8"/><text x="24" y="59">ONE THIRD FOR WATER</text>
            <circle cx="0" cy="104" r="8" fill="{good}"/><text x="24" y="111">ONE THIRD FOR BREATH</text>
          </g>"""
    elif kind == "focus_battery_charge":
        visual_inner = f"""
          <text x="48" y="48" fill="{muted}" font-family="Segoe UI, sans-serif" font-size="16" font-weight="700" letter-spacing="2">BEFORE: {before_lbl[:34]}</text>
          <rect x="48" y="62" width="760" height="28" rx="14" fill="{rule}"/>
          <rect x="48" y="62" width="215" height="28" rx="14" fill="{warn}" opacity="0.88"/>
          <text x="795" y="83" text-anchor="end" fill="{warn}" font-family="Georgia, serif" font-size="22" font-weight="700">28%</text>

          <text x="48" y="138" fill="{good}" font-family="Segoe UI, sans-serif" font-size="16" font-weight="700" letter-spacing="2">AFTER: {after_lbl[:36]}</text>
          <rect x="48" y="152" width="760" height="32" rx="16" fill="{rule}"/>
          <rect x="48" y="152" width="690" height="32" rx="16" fill="{good}" opacity="0.92"/>
          <text x="795" y="176" text-anchor="end" fill="{good}" font-family="Georgia, serif" font-size="24" font-weight="700">94%</text>"""
    elif kind == "four_pillar_map":
        visual_inner = f"""
          <g transform="translate(428,112)" font-family="Segoe UI, sans-serif" font-weight="700" font-size="17">
            <circle r="76" fill="none" stroke="{rule}" stroke-width="2" stroke-dasharray="5 5"/>
            <line x1="-180" y1="0" x2="180" y2="0" stroke="{rule}" stroke-width="1.5"/>
            <line x1="0" y1="-82" x2="0" y2="82" stroke="{rule}" stroke-width="1.5"/>
            <rect x="-78" y="-102" width="156" height="36" rx="18" fill="{acc}"/><text x="0" y="-78" text-anchor="middle" fill="#101520">FAITH</text>
            <rect x="112" y="-18" width="156" height="36" rx="18" fill="{good}"/><text x="190" y="6" text-anchor="middle" fill="#101520">WEALTH</text>
            <rect x="-88" y="66" width="176" height="36" rx="18" fill="{acc}"/><text x="0" y="90" text-anchor="middle" fill="#101520">KNOWLEDGE</text>
            <rect x="-268" y="-18" width="156" height="36" rx="18" fill="{good}"/><text x="-190" y="6" text-anchor="middle" fill="#101520">POWER</text>
          </g>"""
    else:
        # Smooth editorial transition wave: jagged noisy stress -> serene calm wave!
        visual_inner = f"""
          <line x1="48" y1="112" x2="808" y2="112" stroke="{rule}" stroke-width="1.4" stroke-dasharray="4 6"/>
          <!-- Left: jagged stress wave -->
          <path d="M48 112 L76 68 L104 156 L132 58 L160 162 L188 70 L216 150 L244 82 L272 142 L300 94 L328 128 L356 104"
                fill="none" stroke="{warn}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
          <!-- Right: smooth calm cosine wave -->
          <path d="M356 104 C410 72 465 144 530 112 C595 80 650 142 715 112 C755 94 785 112 808 112"
                fill="none" stroke="{good}" stroke-width="4.5" stroke-linecap="round"/>
          <circle cx="356" cy="104" r="6" fill="{acc}"/>
          <text x="48" y="38" fill="{warn}" font-family="Segoe UI, sans-serif" font-size="14.5" font-weight="800" letter-spacing="1.2">✕  {before_lbl[:34]}</text>
          <text x="808" y="38" text-anchor="end" fill="{good}" font-family="Segoe UI, sans-serif" font-size="14.5" font-weight="800" letter-spacing="1.2">✓  {after_lbl[:34]}</text>"""

    return f"""
    <div class="science-plate">
      <svg viewBox="0 0 856 226" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;">
        <rect x="0" y="0" width="856" height="226" rx="16" fill="{card_bg}" stroke="{rule}" stroke-width="1.5"/>
        {visual_inner}
      </svg>
      <div class="science-caption">{stat_lbl}</div>
    </div>"""


def _build_carousel_deck_html(
    blueprint: dict[str, Any],
    config: dict[str, Any],
    pillar_id: str,
    th: dict[str, Any],
) -> str:
    """Build a single HTML document containing all 5 handcrafted 1080x1350 editorial slides."""
    font_css = _load_amiri_font_css()
    meta = blueprint.get("meta") if isinstance(blueprint.get("meta"), dict) else {}
    carousel = blueprint.get("carousel_social") if isinstance(blueprint.get("carousel_social"), dict) else {}
    raw_slides = carousel.get("slides") if isinstance(carousel.get("slides"), list) else []
    scenes_meta = (blueprint.get("shorts_reels_tiktok") or {}).get("scenes") or []

    dalil = _resolve_dalil_payload(topic_meta=meta, scenes_meta=scenes_meta)
    story_acts = resolve_story_acts(topic_meta=meta, scenes_meta=scenes_meta)
    handle = _esc(
        (config.get("branding") or {}).get("watermark_text")
        or meta.get("channel_handle")
        or "@HabitSains"
    )
    theme_id = th["theme_id"]
    kit = _load_kit_data_uris() if theme_id == "papercraft_zine" else {}

    def get_s(i: int) -> dict[str, Any]:
        return raw_slides[i] if i < len(raw_slides) and isinstance(raw_slides[i], dict) else {}

    s1, s2, s3, s4, s5 = get_s(0), get_s(1), get_s(2), get_s(3), get_s(4)

    # Slide 1 Copy (Cover)
    s1_head = _esc(s1.get("headline") or meta.get("topic") or "Prophetic Wisdom for a Calm Mind")
    s1_body = _esc(s1.get("body") or meta.get("hook") or meta.get("angle") or "")
    s1_tag = _esc(th["edition_label"])

    # Slide 2 Copy (Sacred Text Spread — ALWAYS shows verified full-harakat Amiri Arabic!)
    ar_text = _esc(dalil["arabic"])
    ar_word_count = len([w for w in dalil["arabic"].split() if any("\u0621" <= c <= "\u064A" or "\u0671" <= c <= "\u06D3" for c in w)])
    ar_font_px = 44 if ar_word_count >= 10 else (52 if ar_word_count >= 7 else 58)
    tr_text = _esc(dalil["transliteration"])
    en_trans = _esc(dalil["translation"])
    citation = _esc(dalil["citation"])
    surah_ar = _esc(dalil["surah_ar"])
    s2_note = _esc(s2.get("body") or "")
    s2_label = _esc(_clean_editorial_badge(s2.get("badge", ""), "THE SACRED SOURCE"))

    # Slide 3 Copy (Mind Science + Visual Diagram)
    s3_label = _esc(_clean_editorial_badge(s3.get("badge", ""), "EVERYDAY MIND SCIENCE"))
    s3_head = _esc(s3.get("headline") or "What Happens Inside Your Mind")
    s3_body = _esc(s3.get("body") or "Quiet, intentional Prophetic rhythm interrupts racing stress loops and restores steady mental clarity.")
    s3_diagram = _science_diagram_svg(story_acts, th)

    # Slide 4 Copy (Field Notes / 3-Step Practice)
    s4_label = _esc(_clean_editorial_badge(s4.get("badge", ""), "TODAY'S POCKET PRACTICE"))
    s4_head = _esc(s4.get("headline") or "How to Live This Today")
    steps = _extract_practice_steps(str(s4.get("body") or ""), str(s4.get("highlight") or ""), story_acts)
    s4_note = _esc(s4.get("highlight") or story_acts.get("stat_badge") or "Small sincere steps outlast sudden bursts.")
    steps_html = "".join(
        f"""
        <div class="step-row">
          <div class="step-num">0{i + 1}</div>
          <div class="step-copy">
            <div class="step-tag">{_esc(lbl)}</div>
            <div class="step-txt">{_esc(txt)}</div>
          </div>
        </div>"""
        for i, (lbl, txt) in enumerate(steps)
    )

    # Slide 5 Copy (Keepsake Bookmark Card)
    core_lesson = _esc(story_acts.get("core_lesson") or s5.get("headline") or dalil["translation"])
    s5_sub = _esc(s5.get("body") or "Bookmark this reminder for a noisy day, and send it to someone who could use a breath of peace.")

    # Optional Paper-Craft 2.5D sprites for Slides 2, 3, 5 when Pillar 3 (`sunnah_paper_story`)!
    is_paper = theme_id == "papercraft_zine" and bool(kit)
    paper_s2_art = (
        f'<img class="p-s2-scroll" src="{kit["presenter_scroll"]}" alt="">'
        f'<img class="p-s2-sun" src="{kit["sunburst_3d"]}" alt="">'
        if is_paper else ""
    )
    paper_s3_art = (
        f'<img class="p-s3-book" src="{kit["open_book_3d"]}" alt="">'
        if is_paper else ""
    )
    paper_s5_art = (
        f'<div class="paper-dome-wrap">'
        f'<img class="p-dome-bg" src="{kit["dome_medallion_3d"]}" alt="">'
        f'<img class="p-dome-dua" src="{kit["presenter_dua"]}" alt="">'
        f'<div class="p-dome-inner">'
        f'  <div class="keepsake-allah">اللَّهُ</div>'
        f'  <div class="p-dome-lesson">{core_lesson}</div>'
        f'  <div class="p-dome-cit">{citation}</div>'
        f'</div></div>'
        if is_paper else ""
    )

    # Fine paper-grain SVG data URI (subtle tactile texture, zero heavy blur!)
    grain_opacity = "0.045" if not th["dark"] else "0.06"
    s1_cover_art = _theme_cover_art_svg(theme_id, th, dalil, kit)

    # Subtle SVG bookmark icon for Slide 5
    bookmark_svg = f'<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{th["accent"]}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>'

    # Slide 5 body (Paper-craft uses Dome Medallion + Presenter Dua; others use museum keepsake card)
    if is_paper:
        slide5_center = f"""
        {paper_s5_art}
        <p class="keepsake-sub" style="margin-top:26px;">{s5_sub}</p>"""
    else:
        slide5_center = f"""
        <div class="keepsake-card">
          <div class="keepsake-orn">✦ &nbsp; {surah_ar} &nbsp; ✦</div>
          <div class="keepsake-allah">اللَّهُ</div>
          <div class="keepsake-quote">“{core_lesson}”</div>
          <div class="keepsake-rule"></div>
          <div class="keepsake-cit">{citation}</div>
        </div>
        <p class="keepsake-sub">{s5_sub}</p>"""

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  {font_css}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #000;
    font-family: {th['sans']};
    color: {th['ink']};
    -webkit-font-smoothing: antialiased;
  }}

  .slide {{
    position: relative;
    width: 1080px;
    height: 1350px;
    overflow: hidden;
    background: {th['bg']};
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 68px 88px 62px 88px;
  }}

  /* Tactile subtle paper grain overlay (zero AI neon gradients!) */
  .slide::before {{
    content: "";
    position: absolute; inset: 0; pointer-events: none; z-index: 1;
    background-image: radial-gradient({th['ink']} 0.75px, transparent 0.75px);
    background-size: 18px 18px;
    opacity: {grain_opacity};
  }}

  /* Editorial archival inset border (thin, quiet, printed-book feel) */
  .frame-border {{
    position: absolute; inset: 34px; pointer-events: none; z-index: 2;
    border: 1.5px solid {th['rule']};
    border-radius: {'6px' if theme_id == 'kinfolk_essay' else ('18px' if theme_id == 'papercraft_zine' else '10px')};
  }}
  {'.frame-border::after { content: ""; position: absolute; inset: 8px; border: 1px solid rgba(223,189,109,0.16); border-radius: 6px; }' if theme_id == 'mushaf_obsidian' else ''}

  .masthead, .main-body, .colophon {{
    position: relative; z-index: 4;
  }}

  .masthead {{
    display: flex; align-items: center; justify-content: space-between;
    padding-bottom: 22px;
    border-bottom: 1.5px solid {th['rule']};
    font-size: 17px; font-weight: 700; letter-spacing: 3.2px;
    text-transform: uppercase; color: {th['muted']};
  }}
  .masthead .folio {{
    font-family: {th['serif']}; font-style: italic; font-weight: 700;
    letter-spacing: 1.6px; color: {th['accent']};
  }}

  .colophon {{
    display: flex; align-items: center; justify-content: space-between;
    padding-top: 22px;
    border-top: 1.5px solid {th['rule']};
    font-size: 18px; font-weight: 600; color: {th['muted']};
  }}
  .colophon .handle {{
    font-family: {th['serif']}; font-weight: 700; letter-spacing: 0.6px; color: {th['ink']};
  }}
  .colophon .swipe {{
    display: inline-flex; align-items: center; gap: 10px;
    font-size: 16px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase;
    color: {th['accent']};
  }}
  .pips {{
    display: inline-flex; align-items: center; gap: 9px;
  }}
  .pip {{
    width: 8px; height: 8px; border-radius: 50%;
    background: {th['rule']};
  }}
  .pip.on {{
    width: 24px; border-radius: 99px; background: {th['accent']};
  }}

  /* ===== SLIDE 1: EDITORIAL COVER ===== */
  .cover-wrap {{
    flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 36px;
    padding: 24px 0;
  }}
  .hero-svg {{
    width: 100%; height: auto; display: block;
    filter: drop-shadow(0 12px 24px rgba(15, 25, 38, {'0.35' if th['dark'] else '0.09'}));
  }}
  .mushaf-emblem {{ position: relative; width: 100%; height: 340px; }}
  .mushaf-badge-txt {{
    position: absolute; inset: 0; display: flex; flex-direction: column;
    align-items: center; justify-content: center; text-align: center;
  }}
  .mb-num {{
    font-family: {th['serif']}; font-size: 50px; font-weight: 700; color: #F5D98E; line-height: 1.05;
  }}
  .mb-lbl {{
    font-size: 14px; font-weight: 700; letter-spacing: 3.5px; color: #B6AE9E; margin-top: 6px;
  }}
  .mushaf-surah-ar {{
    position: absolute; bottom: 8px; left: 0; right: 0; text-align: center;
    font-family: 'AmiriCalligraphy', 'Amiri', serif; direction: rtl;
    font-size: 30px; color: rgba(223, 189, 109, 0.85);
  }}
  .kicker {{
    font-size: 16px; font-weight: 800; letter-spacing: 3.4px;
    text-transform: uppercase; color: {th['accent']};
  }}
  .cover-title {{
    font-family: {th['serif']}; font-size: 62px; font-weight: 700;
    line-height: 1.13; letter-spacing: -0.5px; color: {th['ink']};
  }}
  .cover-lead {{
    font-family: {th['serif']}; font-size: 29px; line-height: 1.48;
    color: {th['muted']}; max-width: 860px;
  }}

  /* Paper-craft real 2.5D sprite hero for Pillar 3 */
  .paper-hero {{
    position: relative; width: 100%; height: 390px;
    background: linear-gradient(180deg, rgba(255,253,245,0.22), rgba(255,253,245,0.04));
    border-radius: 22px; overflow: hidden;
    border: 2px solid rgba(250, 246, 234, 0.55);
  }}
  .paper-hero img {{ position: absolute; filter: drop-shadow(8px 14px 16px rgba(18, 36, 52, 0.28)); }}
  .p-sun {{ width: 250px; top: -28px; right: 16px; }}
  .p-cal {{ width: 260px; bottom: 18px; right: 120px; }}
  .p-pres {{ height: 320px; bottom: 0; left: 105px; }}
  .p-cloud.c1 {{ width: 140px; top: 36px; left: 32px; opacity: 0.92; }}
  .p-cloud.c2 {{ width: 120px; top: 82px; left: 340px; opacity: 0.86; }}

  /* ===== SLIDE 2: SACRED ARABIC CALLIGRAPHY SPREAD ===== */
  .dalil-wrap {{
    flex: 1; display: flex; flex-direction: column; justify-content: center;
    align-items: center; text-align: center; gap: 28px; padding: 14px 0;
  }}
  .dalil-plate {{
    position: relative; width: 100%;
    background: {th['card_bg']};
    border: 1.8px solid {th['rule']};
    border-radius: {'24px' if theme_id == 'papercraft_zine' else '14px'};
    padding: 58px 56px 48px 56px;
    box-shadow: {'8px 18px 34px rgba(18,36,52,0.18)' if theme_id == 'papercraft_zine' else ('0 18px 44px rgba(0,0,0,0.45)' if th['dark'] else '0 14px 36px rgba(24,36,48,0.07)')};
  }}
  .dalil-surah {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; unicode-bidi: embed;
    font-size: 30px; font-weight: 700; color: {th['accent']};
    margin-bottom: 18px;
  }}
  .dalil-arabic {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; unicode-bidi: embed;
    font-size: {ar_font_px}px; font-weight: 700; line-height: 1.72;
    color: {th['ar_color']};
    margin-bottom: 24px;
  }}
  .dalil-rule {{
    width: 110px; height: 2px; background: {th['accent']};
    margin: 0 auto 24px auto; opacity: 0.72;
  }}
  .dalil-translit {{
    font-family: {th['serif']}; font-style: italic;
    font-size: 24px; line-height: 1.45; color: {th['accent']};
    margin-bottom: 20px;
  }}
  .dalil-en {{
    font-family: {th['serif']}; font-size: 30px; line-height: 1.44;
    color: {th['ink']}; margin-bottom: 28px;
  }}
  .dalil-cit {{
    display: inline-block;
    padding: 7px 22px; border-radius: 999px;
    background: {th['accent_soft']};
    border: 1px solid {th['rule']};
    font-size: 16px; font-weight: 800; letter-spacing: 2.8px;
    color: {th['accent']}; text-transform: uppercase;
  }}
  .dalil-foot-note {{
    font-family: {th['serif']}; font-size: 25px; line-height: 1.48;
    color: {th['muted']}; max-width: 820px;
  }}
  .p-s2-scroll {{ position: absolute; height: 210px; bottom: -16px; left: -12px; opacity: 0.94; filter: drop-shadow(6px 10px 14px rgba(18,36,52,0.24)); }}
  .p-s2-sun {{ position: absolute; width: 145px; top: -36px; right: -24px; opacity: 0.88; filter: drop-shadow(6px 10px 14px rgba(18,36,52,0.22)); }}

  /* ===== SLIDE 3: MIND SCIENCE EDITORIAL INFOGRAPHIC ===== */
  .sci-wrap {{
    flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 30px;
  }}
  .sec-title {{
    font-family: {th['serif']}; font-size: 54px; font-weight: 700;
    line-height: 1.15; color: {th['ink']};
  }}
  .sec-body {{
    font-family: {th['serif']}; font-size: 29px; line-height: 1.50;
    color: {th['muted']};
  }}
  .science-plate {{
    background: {th['card_bg']};
    border: 1.5px solid {th['rule']};
    border-radius: 20px; padding: 26px;
    box-shadow: {'6px 14px 28px rgba(18,36,52,0.16)' if theme_id == 'papercraft_zine' else ('0 14px 36px rgba(0,0,0,0.38)' if th['dark'] else '0 10px 28px rgba(24,36,48,0.06)')};
  }}
  .science-caption {{
    margin-top: 16px; text-align: center;
    font-size: 16px; font-weight: 800; letter-spacing: 2.8px;
    text-transform: uppercase; color: {th['accent']};
  }}
  .p-s3-book {{
    width: 310px; align-self: center; margin-top: -8px;
    filter: drop-shadow(6px 14px 16px rgba(18,36,52,0.26));
  }}

  /* ===== SLIDE 4: POCKET FIELD NOTES CHECKLIST ===== */
  .notes-wrap {{
    flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 28px;
  }}
  .steps-card {{
    background: {th['card_bg']};
    border: 1.5px solid {th['rule']};
    border-radius: 20px;
    padding: 14px 42px;
    box-shadow: {'6px 14px 28px rgba(18,36,52,0.16)' if theme_id == 'papercraft_zine' else ('0 14px 34px rgba(0,0,0,0.36)' if th['dark'] else '0 10px 28px rgba(24,36,48,0.06)')};
  }}
  .step-row {{
    display: flex; align-items: flex-start; gap: 28px;
    padding: 28px 0;
    border-bottom: 1.2px solid {th['rule']};
  }}
  .step-row:last-child {{ border-bottom: none; }}
  .step-num {{
    font-family: {th['serif']}; font-size: 46px; font-weight: 700; font-style: italic;
    line-height: 1.0; color: {th['accent']}; min-width: 64px;
  }}
  .step-tag {{
    font-size: 14px; font-weight: 800; letter-spacing: 2.6px; color: {th['good']};
    margin-bottom: 6px;
  }}
  .step-txt {{
    font-family: {th['serif']}; font-size: 27px; line-height: 1.42; color: {th['ink']};
  }}
  .margin-pull {{
    border-left: 4px solid {th['accent']};
    padding: 14px 26px;
    background: {th['quote_bg']};
    border-radius: 0 12px 12px 0;
    font-family: {th['serif']}; font-style: italic; font-size: 25px; line-height: 1.42;
    color: {th['ink']};
  }}

  /* ===== SLIDE 5: KEEPSAKE BOOKMARK CARD ===== */
  .keepsake-wrap {{
    flex: 1; display: flex; flex-direction: column; justify-content: center;
    align-items: center; text-align: center; gap: 34px;
  }}
  .keepsake-card {{
    width: 100%;
    background: {th['card_bg']};
    border: 1.8px solid {th['rule']};
    border-radius: 18px;
    padding: 68px 64px;
    box-shadow: {'0 20px 46px rgba(0,0,0,0.48)' if th['dark'] else '0 14px 36px rgba(24,36,48,0.08)'};
  }}
  .keepsake-orn {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    font-size: 26px; color: {th['accent']}; margin-bottom: 14px;
  }}
  .keepsake-allah {{
    font-family: 'AmiriCalligraphy', 'Amiri', serif;
    direction: rtl; font-size: 86px; font-weight: 700; line-height: 1.15;
    color: {th['ar_color']}; margin-bottom: 18px;
  }}
  .keepsake-quote {{
    font-family: {th['serif']}; font-size: 46px; font-weight: 700;
    line-height: 1.26; color: {th['ink']}; margin-bottom: 30px;
  }}
  .keepsake-rule {{
    width: 92px; height: 2px; background: {th['accent']}; margin: 0 auto 22px auto;
  }}
  .keepsake-cit {{
    font-size: 16px; font-weight: 800; letter-spacing: 3px; color: {th['accent']};
    text-transform: uppercase;
  }}
  .keepsake-sub {{
    font-family: {th['serif']}; font-size: 26px; line-height: 1.48;
    color: {th['muted']}; max-width: 780px;
  }}
  .bookmark-cta {{
    display: inline-flex; align-items: center; gap: 12px;
    padding: 12px 26px; border-radius: 999px;
    border: 1.5px solid {th['rule']}; background: {th['card_bg']};
    font-size: 17px; font-weight: 700; letter-spacing: 1.4px; color: {th['ink']};
  }}

  /* Paper-craft Slide 5 Dome Medallion + Dua Presenter */
  .paper-dome-wrap {{
    position: relative; width: 100%; height: 640px;
    display: flex; align-items: center; justify-content: center;
  }}
  .p-dome-bg {{
    width: 580px; position: absolute; left: 48px; top: 8px;
    filter: drop-shadow(10px 20px 26px rgba(18, 36, 52, 0.28));
  }}
  .p-dome-dua {{
    height: 410px; position: absolute; right: 20px; bottom: 8px;
    filter: drop-shadow(8px 16px 20px rgba(18, 36, 52, 0.28));
  }}
  .p-dome-inner {{
    position: absolute; left: 168px; top: 164px; width: 340px; height: 332px;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    text-align: center; padding: 14px 18px;
  }}
  .p-dome-lesson {{
    font-family: {th['serif']}; font-size: 25px; font-weight: 700; line-height: 1.30;
    color: #1D3146; margin: 8px 0 12px 0;
  }}
  .p-dome-cit {{
    font-size: 13px; font-weight: 800; letter-spacing: 2.2px; color: #B47D22;
    text-transform: uppercase;
  }}
</style>
</head>
<body>

<!-- ==================== SLIDE 1: EDITORIAL COVER ==================== -->
<section class="slide" id="slide_01">
  <div class="frame-border"></div>
  <header class="masthead">
    <span>{s1_tag}</span>
    <span class="folio">01 / 05</span>
  </header>
  <main class="main-body cover-wrap">
    {s1_cover_art}
    <div style="display:flex;flex-direction:column;gap:20px;">
      <div class="kicker">✦ &nbsp; {citation}</div>
      <h1 class="cover-title">{s1_head}</h1>
      <p class="cover-lead">{s1_body}</p>
    </div>
  </main>
  <footer class="colophon">
    <span class="handle">{handle}</span>
    <span class="swipe">Swipe to reflect &nbsp;→</span>
  </footer>
</section>

<!-- ==================== SLIDE 2: SACRED ARABIC SPREAD ==================== -->
<section class="slide" id="slide_02">
  <div class="frame-border"></div>
  <header class="masthead">
    <span>{s2_label}</span>
    <span class="folio">02 / 05</span>
  </header>
  <main class="main-body dalil-wrap">
    <div class="dalil-plate">
      {paper_s2_art}
      <div class="dalil-surah">{surah_ar}</div>
      <div class="dalil-arabic">{ar_text}</div>
      <div class="dalil-rule"></div>
      <div class="dalil-translit">{tr_text}</div>
      <div class="dalil-en">“{en_trans}”</div>
      <div class="dalil-cit">✦ &nbsp; {citation} &nbsp; ✦</div>
    </div>
    {f'<p class="dalil-foot-note">{s2_note}</p>' if s2_note else ''}
  </main>
  <footer class="colophon">
    <span class="handle">{handle}</span>
    <span class="pips"><span class="pip"></span><span class="pip on"></span><span class="pip"></span><span class="pip"></span><span class="pip"></span></span>
  </footer>
</section>

<!-- ==================== SLIDE 3: MIND SCIENCE INFOGRAPHIC ==================== -->
<section class="slide" id="slide_03">
  <div class="frame-border"></div>
  <header class="masthead">
    <span>{s3_label}</span>
    <span class="folio">03 / 05</span>
  </header>
  <main class="main-body sci-wrap">
    <div class="kicker">HOW IT RESETS YOUR MIND</div>
    <h2 class="sec-title">{s3_head}</h2>
    <p class="sec-body">{s3_body}</p>
    {s3_diagram}
    {paper_s3_art}
  </main>
  <footer class="colophon">
    <span class="handle">{handle}</span>
    <span class="pips"><span class="pip"></span><span class="pip"></span><span class="pip on"></span><span class="pip"></span><span class="pip"></span></span>
  </footer>
</section>

<!-- ==================== SLIDE 4: POCKET FIELD NOTES ==================== -->
<section class="slide" id="slide_04">
  <div class="frame-border"></div>
  <header class="masthead">
    <span>{s4_label}</span>
    <span class="folio">04 / 05</span>
  </header>
  <main class="main-body notes-wrap">
    <div class="kicker">3 QUIET STEPS FOR TODAY</div>
    <h2 class="sec-title">{s4_head}</h2>
    <div class="steps-card">
      {steps_html}
    </div>
    <div class="margin-pull">“{s4_note}”</div>
  </main>
  <footer class="colophon">
    <span class="handle">{handle}</span>
    <span class="pips"><span class="pip"></span><span class="pip"></span><span class="pip"></span><span class="pip on"></span><span class="pip"></span></span>
  </footer>
</section>

<!-- ==================== SLIDE 5: KEEPSAKE BOOKMARK CARD ==================== -->
<section class="slide" id="slide_05">
  <div class="frame-border"></div>
  <header class="masthead">
    <span>KEEPSAKE REMINDER</span>
    <span class="folio">05 / 05</span>
  </header>
  <main class="main-body keepsake-wrap">
    {slide5_center}
    <div class="bookmark-cta">{bookmark_svg} <span>Save for a noisy day &amp; share the peace</span></div>
  </main>
  <footer class="colophon">
    <span class="handle">{handle}</span>
    <span class="pips"><span class="pip"></span><span class="pip"></span><span class="pip"></span><span class="pip"></span><span class="pip on"></span></span>
  </footer>
</section>

</body>
</html>"""


def build_islamic_carousel_html(blueprint: dict[str, Any], config: dict[str, Any]) -> tuple[str, str]:
    """Return `(html_document, theme_id)` for unit testing and Chromium rendering."""
    pillar_id, th = resolve_carousel_theme(blueprint, config)
    return _build_carousel_deck_html(blueprint, config, pillar_id=pillar_id, th=th), th["theme_id"]


def render_islamic_editorial_carousel(
    blueprint: dict[str, Any],
    config: dict[str, Any],
    carousel_dir: Path,
) -> list[Path]:
    """Render all 5 human-editorial 1080x1350 PNG slides via Headless Chromium + Amiri HarfBuzz RTL."""
    from playwright.sync_api import sync_playwright

    carousel_dir.mkdir(parents=True, exist_ok=True)
    html_doc, theme_id = build_islamic_carousel_html(blueprint, config)
    chrome = find_chrome_executable()
    launch_kw: dict[str, Any] = {
        "headless": True,
        "args": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"],
    }
    if chrome:
        launch_kw["executable_path"] = chrome

    generated: list[Path] = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(**launch_kw)
        page = br.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1.0)
        page.set_content(html_doc, wait_until="load")
        page.evaluate("() => document.fonts.ready")
        # Wait for all embedded sprite <img> elements to decode cleanly
        page.evaluate(
            """() => Promise.all(Array.from(document.images).map(im =>
                im.complete ? Promise.resolve() : new Promise(r => { im.onload = r; im.onerror = r; })
            ))"""
        )
        try:
            for idx in range(1, 6):
                out_file = carousel_dir / f"slide_{idx:02d}.png"
                loc = page.locator(f"#slide_{idx:02d}")
                loc.screenshot(path=str(out_file), type="png")
                generated.append(out_file)
        finally:
            br.close()

    print(
        f"[carousel] Rendered 5 human-editorial slides (1080x1350, theme={theme_id}, Amiri RTL HarfBuzz) -> {carousel_dir.name}",
        flush=True,
    )
    return generated
