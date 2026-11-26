from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_loader import slugify


DEFAULT_CONTENT_PILLARS: list[dict[str, str]] = [
    {
        "id": "focus_habits",
        "label": "Everyday Focus & Habits",
        "description": "Simple everyday phone habits, focus tricks, and beating procrastination without academic jargon.",
    },
    {
        "id": "everyday_science",
        "label": "Fun Everyday Science",
        "description": "Light, surprising everyday brain & body facts (coffee crash, tired after 8h sleep, shower ideas, fake breaks, naps, stress).",
    },
    {
        "id": "pov_survival",
        "label": "3D POV Brain Challenge",
        "description": "Thrilling First-Person 3D POV countdown/survival challenges (@you.have.72hours vibe) with urgent [A]/[B] decisions.",
    },
]

# 30 crystal-clear, everyday plain-English topics split across 3 non-colliding rotating pillars
PILLAR_TOPIC_BANKS: dict[str, list[dict[str, Any]]] = {
    "focus_habits": [
        {
            "topic": "Why Checking Your Phone at 7 AM Ruins Your Focus All Day",
            "angle": "Simple everyday breakdown of how morning scrolling drains your focus fuel before work even starts",
            "hook": "Ever pick up your phone for two minutes in bed—and suddenly feel lazy for the rest of the day?",
            "keywords": ["morning phone", "focus", "dopamine", "habits", "deep work"],
        },
        {
            "topic": "You're Not Lazy: Why Starting a Simple Task Feels So Hard",
            "angle": "Why your brain avoids boring tasks and the tiny 5-minute trick that breaks the freeze instantly",
            "hook": "Staring at one easy task for an hour does not mean you are lazy—your brain is playing a trick on you.",
            "keywords": ["procrastination", "motivation", "habits", "focus", "5 minute rule"],
        },
        {
            "topic": "Why Checking Just One Text Costs You 23 Minutes of Focus",
            "angle": "How one quick 10-second notification leaves mental fog behind and kills your momentum",
            "hook": "Think a ten-second text reply is harmless? Science says it steals twenty-three minutes from your brain.",
            "keywords": ["notifications", "multitasking", "focus", "23 minute rule", "phone"],
        },
        {
            "topic": "The 5-Minute Trick That Makes Boring Tasks Feel Easy",
            "angle": "How lowering the starting bar fools your brain into enjoying work you were dreading",
            "hook": "Wait until you feel motivated and you will wait all day—here is the 5-minute trick that works every time.",
            "keywords": ["5 minute trick", "boring tasks", "habits", "productivity", "focus"],
        },
        {
            "topic": "Why You Keep Opening Apps Without Even Realizing It",
            "angle": "How autopilot phone habits hijack your hand in half a second and how to break the loop",
            "hook": "Ever close an app on your phone... and immediately tap the exact same app two seconds later?",
            "keywords": ["phone addiction", "scrolling", "autopilot", "habits", "focus"],
        },
        {
            "topic": "How One Messy Desk Secretly Drains Your Energy Every Hour",
            "angle": "Why visual clutter forces your brain to work overtime even when you think you are ignoring it",
            "hook": "Your messy desk is quietly burning your focus battery—even when you are only looking at your laptop.",
            "keywords": ["messy desk", "clutter", "focus", "deep work", "habits"],
        },
        {
            "topic": "Why To-Do Lists Make You Procrastinate More (And What Works)",
            "angle": "Why giant task lists trigger overwhelm and how picking just 1 priority unlocks instant action",
            "hook": "Writing a 15-item to-do list feels productive—until your brain freezes and does zero of them.",
            "keywords": ["to do list", "procrastination", "focus", "habits", "productivity"],
        },
        {
            "topic": "How to Reset a Fried Brain in Just 10 Quiet Minutes",
            "angle": "Why staring at a ceiling beats scrolling when your head feels foggy mid-afternoon",
            "hook": "When your brain feels completely fried at 3 PM, scrolling makes it worse—try this 10-minute reset instead.",
            "keywords": ["brain fog", "focus reset", "rest", "energy", "habits"],
        },
        {
            "topic": "Why You Can't Stop Scrolling Even When You're Completely Bored",
            "angle": "The slot-machine trick inside every feed that keeps your thumb swiping long past fun",
            "hook": "You aren't even enjoying the videos anymore—so why can't your thumb stop swiping up?",
            "keywords": ["doomscrolling", "dopamine", "phone habit", "focus", "self control"],
        },
        {
            "topic": "The One Nighttime Habit That Makes Tomorrow Twice as Easy",
            "angle": "How charging your phone outside the bedroom fixes both sleep quality and morning focus in one move",
            "hook": "Move one tiny object ten feet away tonight—and tomorrow morning will feel completely different.",
            "keywords": ["night habit", "sleep", "morning focus", "phone", "routine"],
        },
    ],
    "everyday_science": [
        {
            "topic": "Why Drinking Coffee Right After Waking Up Makes You Crash at 2 PM",
            "angle": "The simple timing mistake that blocks your natural wake-up signal and triggers an afternoon wall",
            "hook": "Drinking coffee the second you wake up is the exact reason you hit a brick wall at 2 PM.",
            "keywords": ["coffee", "caffeine crash", "energy", "morning", "everyday science"],
        },
        {
            "topic": "Why You Still Feel Exhausted Even After Sleeping 8 Hours",
            "angle": "How late-night bright screens and racing thoughts steal deep recovery sleep even when you stay in bed 8 hours",
            "hook": "You slept a full eight hours—so why do you wake up feeling like you barely closed your eyes?",
            "keywords": ["sleep", "tired", "energy", "brain science", "night phone"],
        },
        {
            "topic": "Why Scrolling on Your Break Makes Your Brain MORE Tired",
            "angle": "Why fast short videos flood your tired mind with noise instead of letting your energy recharge",
            "hook": "Taking a five-minute break on your phone feels relaxing—so why do you come back twice as exhausted?",
            "keywords": ["breaks", "scrolling", "brain fatigue", "energy", "everyday science"],
        },
        {
            "topic": "Why Your Best Ideas Always Hit You in the Shower",
            "angle": "What happens in your brain the second you stop staring at screens and let your mind wander freely",
            "hook": "You stared at your laptop for two hours with zero ideas—then solved everything in a five-minute shower.",
            "keywords": ["shower thoughts", "creativity", "boredom", "brain", "everyday science"],
        },
        {
            "topic": "Why 20-Minute Naps Refresh You—But 45-Minute Naps Ruin Your Day",
            "angle": "The simple sleep-stage timer that explains why a long afternoon nap leaves you groggy and confused",
            "hook": "Ever wake up from an afternoon nap not even knowing what year it is? Here is why that happens.",
            "keywords": ["power nap", "sleep", "energy", "afternoon", "everyday science"],
        },
        {
            "topic": "Why Listening to Songs With Lyrics Slows Down Your Reading",
            "angle": "Why your brain's language center can't read hard text and process sung words at the same time",
            "hook": "Reading the same paragraph four times with your favorite playlist on? Your brain is fighting the lyrics.",
            "keywords": ["study music", "lyrics", "focus", "reading", "everyday science"],
        },
        {
            "topic": "Why Walking Into a Room Makes You Instantly Forget Why You Went There",
            "angle": "The surprising doorway effect where your brain clears old tabs the moment you cross into a new space",
            "hook": "You walked into the kitchen for one thing—and stood there completely blank. Your doorway did that.",
            "keywords": ["doorway effect", "memory", "brain facts", "everyday science", "mind"],
        },
        {
            "topic": "Why Stress Makes You Crave Junk Food Late at Night",
            "angle": "How a tired, stressed brain hunts for fast sugar and cheap comfort the moment willpower runs dry",
            "hook": "Eating healthy all day—then raiding the kitchen at 11 PM? It's your stressed brain begging for quick fuel.",
            "keywords": ["stress", "cravings", "late night", "habits", "everyday science"],
        },
        {
            "topic": "Why Time Feels Faster Every Year as You Get Older",
            "angle": "How repeating the exact same daily routine makes your brain compress entire weeks into a blur",
            "hook": "Remember when summer vacation felt endless? Here is the simple brain reason years fly by now.",
            "keywords": ["time perception", "memory", "routine", "brain facts", "everyday science"],
        },
        {
            "topic": "Why Staying Up Just 1 Hour Later Makes You Cranky All Tomorrow",
            "angle": "How losing that final hour of sleep strips away your patience and turns tiny annoyances into big stress",
            "hook": "Going to bed just one hour late doesn't just make you sleepy—it turns your mood switch upside down.",
            "keywords": ["sleep loss", "mood", "stress", "bedtime", "everyday science"],
        },
    ],
    "pov_survival": [
        {
            "topic": "72 Hours Without Your Phone: What Happens to Your Brain on Hour 1",
            "angle": "First-Person 3D POV countdown challenge—can you survive the very first hour without tapping your glowing screen?",
            "hook": "The 72-hour no-phone challenge just started—and your hand is already reaching for the screen on minute five.",
            "keywords": ["72 hours", "no phone challenge", "pov", "dopamine detox", "focus"],
        },
        {
            "topic": "You Have 6 Hours to Finish Everything—One Phone Tap Resets the Clock",
            "angle": "High-stakes First-Person 3D POV focus countdown where 3 urgent pings try to wreck your deadline",
            "hook": "Six hours left on the clock. Zero words written. And your phone just lit up with three urgent pings.",
            "keywords": ["6 hour challenge", "deadline", "pov", "focus game", "distraction"],
        },
        {
            "topic": "Survive 24 Hours With Zero Screens: Why Most People Quit at Hour 3",
            "angle": "First-Person 3D POV survival episode showing the exact boredom trap that breaks almost everyone at hour 3",
            "hook": "Hour three with zero screens—and your brain is literally panicking from the silence. Do you cave in?",
            "keywords": ["24 hours no screen", "digital detox", "pov", "boredom", "challenge"],
        },
        {
            "topic": "Midnight Trap: One More Short Video Costs You Tomorrow's Entire Day",
            "angle": "First-Person 3D POV 11:42 PM survival showdown between sleep recovery and the autoplay trap",
            "hook": "It's 11:42 PM. You promised yourself just one more video—and your alarm goes off in seven hours.",
            "keywords": ["midnight scroll", "sleep trap", "pov", "night routine", "challenge"],
        },
        {
            "topic": "You Wake Up With Only 4 Hours of Brain Battery Left Today",
            "angle": "First-Person 3D POV energy-bar survival game where every tiny distraction drains 15% of your day's fuel",
            "hook": "Imagine seeing your brain's real battery bar when you wake up—and watching one scroll drop it to 40 percent.",
            "keywords": ["brain battery", "focus bar", "pov", "energy", "challenge"],
        },
        {
            "topic": "The 90-Minute Focus Challenge: Can You Ignore Every Ping Until the Timer Hits Zero?",
            "angle": "First-Person 3D POV distraction gauntlet testing whether you lock in or fold on the final alert",
            "hook": "Ninety minutes. One big goal on your desk. Three loud alerts trying to break you—what would you do?",
            "keywords": ["90 minute challenge", "deep focus", "pov", "notifications", "self control"],
        },
        {
            "topic": "Locked in Your Room With 1 Big Task and 19 Notifications: What Would You Do?",
            "angle": "First-Person 3D POV decision thriller turning everyday procrastination into an interactive A/B survival choice",
            "hook": "One big project on the left. Nineteen glowing alerts on the right. Your brain only has fuel for one.",
            "keywords": ["pov decision", "procrastination", "focus trap", "a or b", "challenge"],
        },
        {
            "topic": "The 2 PM Energy Crash Survival Test: Coffee vs a 10-Minute Offline Reset",
            "angle": "First-Person 3D POV afternoon crash crisis where the wrong choice wrecks your sleep tonight",
            "hook": "2:14 PM. Your eyes feel heavy and work is still half-finished. Pick the wrong fix and tonight is ruined.",
            "keywords": ["2 pm crash", "coffee vs rest", "pov", "energy", "challenge"],
        },
        {
            "topic": "No Coffee, No Music, No Phone for One Morning: Hour-by-Hour Brain Test",
            "angle": "First-Person 3D POV morning reset challenge showing how quickly quiet focus returns when noise stops",
            "hook": "Zero coffee. Zero music. Zero phone until 9 AM. Watch what happens to your brain in the first hour.",
            "keywords": ["morning challenge", "dopamine reset", "pov", "quiet morning", "focus"],
        },
        {
            "topic": "Your Focus Drops 10% Every Time You Switch Tabs—Can You Survive Work Today?",
            "angle": "First-Person 3D POV multitasking survival countdown as pings try to drain your focus bar to zero",
            "hook": "Every single tab switch drops your focus bar ten percent—and your inbox just exploded.",
            "keywords": ["tab switching", "multitasking", "pov", "focus bar", "challenge"],
        },
    ],
}

_ACADEMIC_JARGON_MARKERS: tuple[str, ...] = (
    "coupling",
    "correlates",
    "modulates",
    "modulation",
    "striatal",
    "cortical",
    "prefrontal",
    "dopaminergic",
    "fmri",
    "eeg",
    "meta-analysis",
    "longitudinal",
    "randomized",
    "cohort",
    "pathophysiology",
    "neurogenesis",
    "synaptic",
    "hippocampal",
    "adolescents",
    "children and teens",
    "attention-related networks",
    "executive function",
    "cognitive load",
    "et al",
    "study finds",
    "researchers find",
    "journal of",
)


def _looks_academic_jargon(title: str) -> bool:
    low = (title or "").lower()
    if not low.strip():
        return True
    if any(m in low for m in _ACADEMIC_JARGON_MARKERS):
        return True
    # Reject overly dense/long news headlines (> 85 chars)
    if len(title.strip()) > 85:
        return True
    return False


@dataclass
class TopicIdea:
    topic: str
    angle: str
    hook: str
    source: str
    source_url: str = ""
    keywords: list[str] | None = None
    discovered_at: str = ""
    pillar: str = "focus_habits"
    pillar_label: str = "Everyday Focus & Habits"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["keywords"] = self.keywords or []
        data["discovered_at"] = data["discovered_at"] or datetime.now(timezone.utc).isoformat()
        return data


def load_history(history_file: Path) -> list[dict[str, Any]]:
    if not history_file.exists():
        return []
    try:
        return json.loads(history_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def select_next_pillar(history: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, str]:
    """Rotate deterministically across the 3 content pillars so consecutive runs never collide."""
    configured = (config.get("content_pillars") or {}).get("rotation")
    pillars = configured if isinstance(configured, list) and configured else DEFAULT_CONTENT_PILLARS
    valid = [p for p in pillars if isinstance(p, dict) and p.get("id")]
    if not valid:
        valid = DEFAULT_CONTENT_PILLARS

    # Look at the most recent run's pillar first so we strictly advance to the NEXT pillar
    if history:
        last_pillar = str(history[-1].get("pillar") or "").strip()
        ids = [str(p["id"]) for p in valid]
        if last_pillar in ids:
            nxt_idx = (ids.index(last_pillar) + 1) % len(valid)
            return valid[nxt_idx]

    return valid[len(history) % len(valid)]


def _fetch_google_news_rss(query: str, hl: str = "id", gl: str = "ID", ceid: str = "ID:id", limit: int = 5) -> list[dict[str, str]]:
    encoded = urllib.parse.quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl={hl}&gl={gl}&ceid={ceid}"
    req = urllib.request.Request(url, headers={"User-Agent": "ContentAutomationStudio/1.0"})
    items: list[dict[str, str]] = []
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            xml_bytes = resp.read()
        root = ET.fromstring(xml_bytes)
        for item in root.findall(".//item")[:limit]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
            if title:
                clean_title = title.rsplit(" - ", 1)[0].strip() if " - " in title else title
                items.append({
                    "title": clean_title,
                    "raw_title": title,
                    "url": link,
                    "published": pub_date,
                    "query": query,
                })
    except Exception:
        return []
    return items


def discover_trending_candidates(config: dict[str, Any], limit_per_query: int = 4) -> list[dict[str, str]]:
    trends_cfg = config.get("trends", {})
    queries = trends_cfg.get("queries") or [config.get("channel", {}).get("niche", "AI produktivitas")]
    hl = trends_cfg.get("locale_hl", "id")
    gl = trends_cfg.get("locale_gl", "ID")
    ceid = trends_cfg.get("locale_ceid", "ID:id")

    seen_slugs: set[str] = set()
    candidates: list[dict[str, str]] = []
    for query in queries:
        for item in _fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query):
            s = slugify(item["title"])
            if s not in seen_slugs:
                seen_slugs.add(s)
                candidates.append(item)

    for feed_url in trends_cfg.get("custom_rss_feeds") or []:
        try:
            req = urllib.request.Request(feed_url, headers={"User-Agent": "ContentAutomationStudio/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                root = ET.fromstring(resp.read())
            for item in root.findall(".//item")[:limit_per_query]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if title:
                    s = slugify(title)
                    if s not in seen_slugs:
                        seen_slugs.add(s)
                        candidates.append({"title": title, "raw_title": title, "url": link, "published": "", "query": feed_url})
        except Exception:
            continue

    return candidates


def _load_analytics_insights(history_file: Path) -> dict[str, Any]:
    ins_file = history_file.parent / "analytics_insights.json"
    if not ins_file.exists():
        return {}
    try:
        return json.loads(ins_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _rank_topic_with_gemini(
    candidates: list[dict[str, str]],
    config: dict[str, Any],
    used_slugs: set[str],
    pillar: dict[str, str],
    winning_patterns: list[str] | None = None,
) -> TopicIdea | None:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        channel = config.get("channel", {})
        model = config.get("ai", {}).get("text_model", "gemini-3.8-flash")
        pat_txt = (
            f"\nProven high-view patterns from our channel analytics (prioritize matching these!):\n- "
            + "\n- ".join(winning_patterns[:4])
            + "\n"
            if winning_patterns
            else ""
        )

        lang = channel.get("language", "en")
        pillar_id = pillar.get("id", "focus_habits")
        pillar_label = pillar.get("label", "Everyday Focus & Habits")
        pillar_desc = pillar.get("description", "")

        if lang == "en":
            prompt = (
                f"You are the Viral Content Strategist for '{channel.get('name')}' (audience: everyday viewers worldwide, language: super-simple conversational English).\n"
                f"TODAY'S SCHEDULED CONTENT PILLAR (MUST MATCH THIS PILLAR SO DAILY VIDEOS NEVER COLLIDE):\n"
                f"- Pillar ID: {pillar_id} ({pillar_label})\n"
                f"- Pillar Goal: {pillar_desc}\n\n"
                "PLAIN-ENGLISH CLARITY RULES (CRITICAL — ZERO JARGON):\n"
                "1. NEVER copy an academic study title verbatim (e.g. NEVER write 'Dopamine Supports Coupling of Attention-Related Networks' or 'fMRI reveals...').\n"
                "2. Rewrite or invent 1 crystal-clear, bingeable everyday topic a 14-year-old IMMEDIATELY understands in 2 seconds (max 68 chars).\n"
                "   - Good examples for focus_habits: 'Why Checking Your Phone at 7 AM Ruins Your Focus All Day', 'You Are Not Lazy: Why Starting Simple Tasks Feels Hard'\n"
                "   - Good examples for everyday_science: 'Why Coffee Right After Waking Up Makes You Crash at 2 PM', 'Why You Still Feel Tired After Sleeping 8 Hours'\n"
                "   - Good examples for pov_survival: '72 Hours Without Your Phone: Hour 1 Brain Test', 'You Have 6 Hours Left—One Phone Tap Resets the Clock'\n"
                "3. Strictly FORBID jargon words: coupling, prefrontal, correlates, modulates, cortical, striatal, cognitive load, executive function, adolescents.\n"
                f"4. Avoid previously used slugs: {sorted(list(used_slugs))[:18]}\n"
                f"{pat_txt}\n"
                f"Optional inspiration news headlines (ONLY use if you rewrite into plain everyday English matching pillar '{pillar_id}'):\n"
                f"{json.dumps(candidates[:10], ensure_ascii=False, indent=2)}\n\n"
                "Return valid JSON with keys: topic, angle, hook, source_url, keywords (array of 5 simple strings)."
            )
        else:
            prompt = (
                f"Kamu adalah Content Strategist untuk channel '{channel.get('name')}' "
                f"(niche: {channel.get('niche')}, audiens: {channel.get('target_audience')}, bahasa: {lang}).\n"
                f"Pilih 1 topik paling potensial viral dan gampang dipahami dari daftar tren berikut, hindari topik yang sudah dipakai ({sorted(list(used_slugs))[:15]}).\n"
                f"Kandidat tren:\n{json.dumps(candidates[:12], ensure_ascii=False, indent=2)}\n\n"
                "Kembalikan JSON valid dengan keys: topic, angle, hook, source_url, keywords (array 5 string)."
            )
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.65,
            ),
        )
        data = json.loads(resp.text)
        picked_topic = str(data.get("topic") or "").strip()
        if not picked_topic or (lang == "en" and _looks_academic_jargon(picked_topic)):
            print(f"[ideation] Rejected overly academic/empty Gemini topic: {picked_topic!r}; using curated pillar bank.", flush=True)
            return None
        if slugify(picked_topic) in used_slugs:
            print(f"[ideation] Rejected duplicate Gemini topic: {picked_topic!r}; using curated pillar bank.", flush=True)
            return None
        return TopicIdea(
            topic=picked_topic,
            angle=str(data.get("angle") or f"Super-simple everyday breakdown for {pillar_label}").strip(),
            hook=str(data.get("hook") or f"Ever wonder why this happens to your brain? Let's break down {picked_topic}.").strip(),
            source=f"gemini_pillar:{pillar_id}",
            source_url=str(data.get("source_url") or ""),
            keywords=[str(k) for k in (data.get("keywords") or [])][:8],
            discovered_at=datetime.now(timezone.utc).isoformat(),
            pillar=pillar_id,
            pillar_label=pillar_label,
        )
    except Exception:
        return None


def _pick_from_pillar_bank(
    pillar: dict[str, str],
    used_slugs: set[str],
    now_iso: str,
) -> TopicIdea:
    pillar_id = pillar.get("id", "focus_habits")
    pillar_label = pillar.get("label", "Everyday Focus & Habits")
    bank = PILLAR_TOPIC_BANKS.get(pillar_id) or PILLAR_TOPIC_BANKS["focus_habits"]
    chosen = next((item for item in bank if slugify(item["topic"]) not in used_slugs), None)
    if chosen is None:
        # Try any unused topic across other banks before wrapping around
        for alt_bank in PILLAR_TOPIC_BANKS.values():
            chosen = next((item for item in alt_bank if slugify(item["topic"]) not in used_slugs), None)
            if chosen is not None:
                break
    if chosen is None:
        chosen = bank[len(used_slugs) % len(bank)]

    return TopicIdea(
        topic=str(chosen["topic"]),
        angle=str(chosen["angle"]),
        hook=str(chosen["hook"]),
        source=f"curated_pillar:{pillar_id}",
        source_url="",
        keywords=list(chosen.get("keywords") or ["focus", "habits", "brain"]),
        discovered_at=now_iso,
        pillar=pillar_id,
        pillar_label=pillar_label,
    )


def select_topic(
    config: dict[str, Any],
    history_file: Path,
    manual_topic: str | None = None,
    manual_angle: str | None = None,
) -> TopicIdea:
    now_iso = datetime.now(timezone.utc).isoformat()
    channel = config.get("channel", {})
    niche = channel.get("niche", "AI & Produktivitas")
    history = load_history(history_file)
    pillar = select_next_pillar(history, config)
    pillar_id = pillar["id"]
    pillar_label = pillar["label"]

    lang = channel.get("language", "en")
    if manual_topic and manual_topic.strip():
        clean_topic = manual_topic.strip()
        if lang == "en":
            return TopicIdea(
                topic=clean_topic,
                angle=(manual_angle or f"Super-simple everyday breakdown anyone can understand and apply today").strip(),
                hook=f"Ever feel stuck on this? Here is the simple truth behind {clean_topic}.",
                source="manual_input",
                keywords=[w for w in slugify(clean_topic).split("-") if len(w) > 2][:6] + ["habits", "focus"],
                discovered_at=now_iso,
                pillar=pillar_id,
                pillar_label=pillar_label,
            )
        return TopicIdea(
            topic=clean_topic,
            angle=(manual_angle or f"Blueprint praktis dan strategi eksekusi cepat untuk {channel.get('target_audience', 'kreator')}").strip(),
            hook=f"Masih menghabiskan berjam-jam untuk satu konten? Begini cara kerja {clean_topic} dari ide sampai siap publish!",
            source="manual_input",
            keywords=[w for w in slugify(clean_topic).split("-") if len(w) > 2][:6] + ["automasi", "konten"],
            discovered_at=now_iso,
            pillar=pillar_id,
            pillar_label=pillar_label,
        )

    used_slugs = {item.get("slug", "") for item in history}
    insights = _load_analytics_insights(history_file)

    # Closed-Loop Sequel Engine: every 3rd run, automatically produce a Part 2 / sequel
    # directly extending our #1 most-watched video (once real views exist)!
    sequels = insights.get("recommended_sequels") or []
    if len(history) > 0 and (len(history) % 3 == 0) and int(insights.get("total_views_all_platforms", 0)) > 0:
        for seq in sequels:
            seq_topic = str(seq.get("topic") or "").strip()
            if seq_topic and slugify(seq_topic) not in used_slugs:
                return TopicIdea(
                    topic=seq_topic,
                    angle=str(seq.get("angle") or f"Direct Part 2 sequel expanding our most-watched {niche} episode").strip(),
                    hook=str(seq.get("hook") or f"Because so many of you watched Part 1, here is what happens next: {seq_topic}").strip(),
                    source="analytics_sequel",
                    source_url="",
                    keywords=[str(k) for k in (seq.get("keywords") or ["part 2", "focus", "habits"])][:8],
                    discovered_at=now_iso,
                    pillar=pillar_id,
                    pillar_label=pillar_label,
                )

    candidates = discover_trending_candidates(config)
    fresh = [c for c in candidates if slugify(c["title"]) not in used_slugs]
    pool = fresh or candidates

    gemini_pick = _rank_topic_with_gemini(
        pool,
        config,
        used_slugs,
        pillar=pillar,
        winning_patterns=insights.get("winning_patterns"),
    )
    if gemini_pick:
        return gemini_pick

    # For English HabitSains: NEVER dump raw academic Google News titles straight into a video!
    # Always select a crisp, zero-jargon, everyday topic from the active rotating pillar bank.
    if lang == "en":
        return _pick_from_pillar_bank(pillar, used_slugs, now_iso)

    if pool:
        top = pool[0]
        return TopicIdea(
            topic=top["title"],
            angle=f"Analisis tren & cara praktik langsung untuk niche {niche}",
            hook=f"Tren ini sedang ramai dibahas: {top['title']} — dan ini dampaknya buat kreator hari ini!",
            source="google_news_rss",
            source_url=top.get("url", ""),
            keywords=[w for w in slugify(top["title"]).split("-") if len(w) > 2][:6],
            discovered_at=now_iso,
            pillar=pillar_id,
            pillar_label=pillar_label,
        )

    fallback_topics = [
        "Cara Membangun Pabrik Konten AI Otomatis untuk YouTube dan Sosmed",
        "Strategi Repurpose 1 Ide Konten Menjadi 7 Format Siap Publish",
        "Workflow AI Harian Kreator: Dari Riset Tren Sampai Auto-Draft dalam 10 Menit",
    ]
    chosen = next((t for t in fallback_topics if slugify(t) not in used_slugs), fallback_topics[0])
    return TopicIdea(
        topic=chosen,
        angle="Framework end-to-end yang langsung bisa dipraktikkan kreator hari ini",
        hook=f"Satu topik bisa berubah jadi video panjang, Shorts, Reels, TikTok, dan Carousel sekaligus—ini caranya!",
        source="evergreen_fallback",
        keywords=["automasi konten", "youtube ai", "repurpose konten", "sosial media", "produktivitas"],
        discovered_at=now_iso,
        pillar=pillar_id,
        pillar_label=pillar_label,
    )
