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


@dataclass
class TopicIdea:
    topic: str
    angle: str
    hook: str
    source: str
    source_url: str = ""
    keywords: list[str] | None = None
    discovered_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["keywords"] = self.keywords or []
        data["discovered_at"] = self.discovered_at or datetime.now(timezone.utc).isoformat()
        return data


def load_history(history_file: Path) -> list[dict[str, Any]]:
    if not history_file.exists():
        return []
    try:
        return json.loads(history_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


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
                # Strip trailing publisher name from Google News title ("Headline - Source")
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
    winning_patterns: list[str] | None = None,
) -> TopicIdea | None:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or not candidates:
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
        if lang == "en":
            prompt = (
                f"You are the Lead Content Strategist for '{channel.get('name')}' "
                f"(niche: {channel.get('niche')}, audience: {channel.get('target_audience')}, language: English).\n"
                f"Select 1 high-CTR, original science-backed topic angle from the trend candidates below, avoiding previously used slugs ({sorted(list(used_slugs))[:15]})."
                f"{pat_txt}\n"
                f"Candidates:\n{json.dumps(candidates[:12], ensure_ascii=False, indent=2)}\n\n"
                "Return valid JSON with keys: topic, angle, hook, source_url, keywords (array of 5 strings)."
            )
        else:
            prompt = (
                f"Kamu adalah Content Strategist untuk channel '{channel.get('name')}' "
                f"(niche: {channel.get('niche')}, audiens: {channel.get('target_audience')}, bahasa: {lang}).\n"
                f"Pilih 1 topik paling potensial viral dan actionable dari daftar tren berikut, hindari topik yang sudah dipakai ({sorted(list(used_slugs))[:15]}).\n"
                f"Kandidat tren:\n{json.dumps(candidates[:12], ensure_ascii=False, indent=2)}\n\n"
                "Kembalikan JSON valid dengan keys: topic, angle, hook, source_url, keywords (array 5 string)."
            )
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.6,
            ),
        )
        data = json.loads(resp.text)
        return TopicIdea(
            topic=str(data.get("topic") or candidates[0]["title"]).strip(),
            angle=str(data.get("angle") or "Panduan praktis langkah demi langkah").strip(),
            hook=str(data.get("hook") or "Kebanyakan kreator masih melakukan ini secara manual—padahal bisa otomatis!").strip(),
            source="google_news_rss+gemini",
            source_url=str(data.get("source_url") or candidates[0].get("url", "")),
            keywords=[str(k) for k in (data.get("keywords") or [])][:8],
            discovered_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception:
        return None


def select_topic(
    config: dict[str, Any],
    history_file: Path,
    manual_topic: str | None = None,
    manual_angle: str | None = None,
) -> TopicIdea:
    now_iso = datetime.now(timezone.utc).isoformat()
    channel = config.get("channel", {})
    niche = channel.get("niche", "AI & Produktivitas")

    lang = channel.get("language", "en")
    if manual_topic and manual_topic.strip():
        clean_topic = manual_topic.strip()
        if lang == "en":
            return TopicIdea(
                topic=clean_topic,
                angle=(manual_angle or f"Science-backed breakdown and actionable 3-step protocol for {channel.get('target_audience', 'knowledge workers')}").strip(),
                hook=f"Most people misunderstand {clean_topic}—and it quietly drains hours of focus every single week.",
                source="manual_input",
                keywords=[w for w in slugify(clean_topic).split("-") if len(w) > 2][:6] + ["neuroscience", "focus"],
                discovered_at=now_iso,
            )
        return TopicIdea(
            topic=clean_topic,
            angle=(manual_angle or f"Blueprint praktis dan strategi eksekusi cepat untuk {channel.get('target_audience', 'kreator')}").strip(),
            hook=f"Masih menghabiskan berjam-jam untuk satu konten? Begini cara kerja {clean_topic} dari ide sampai siap publish!",
            source="manual_input",
            keywords=[w for w in slugify(clean_topic).split("-") if len(w) > 2][:6] + ["automasi", "konten"],
            discovered_at=now_iso,
        )

    history = load_history(history_file)
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
                    keywords=[str(k) for k in (seq.get("keywords") or ["part 2", "neuroscience", "focus"])][:8],
                    discovered_at=now_iso,
                )

    candidates = discover_trending_candidates(config)
    fresh = [c for c in candidates if slugify(c["title"]) not in used_slugs]
    pool = fresh or candidates

    gemini_pick = _rank_topic_with_gemini(
        pool, config, used_slugs, winning_patterns=insights.get("winning_patterns")
    )
    if gemini_pick:
        return gemini_pick

    if pool:
        top = pool[0]
        if lang == "en":
            return TopicIdea(
                topic=top["title"],
                angle=f"Science-backed breakdown and actionable protocol for {niche}",
                hook=f"New research just sparked debate on {top['title']} — and here is what it actually means for your brain.",
                source="google_news_rss",
                source_url=top.get("url", ""),
                keywords=[w for w in slugify(top["title"]).split("-") if len(w) > 2][:6] + ["neuroscience", "focus"],
                discovered_at=now_iso,
            )
        return TopicIdea(
            topic=top["title"],
            angle=f"Analisis tren & cara praktik langsung untuk niche {niche}",
            hook=f"Tren ini sedang ramai dibahas: {top['title']} — dan ini dampaknya buat kreator hari ini!",
            source="google_news_rss",
            source_url=top.get("url", ""),
            keywords=[w for w in slugify(top["title"]).split("-") if len(w) > 2][:6],
            discovered_at=now_iso,
        )

    # Evergreen offline fallback
    if lang == "en":
        fallback_topics = [
            "Why Checking Your Phone at 7 AM Cuts Deep Focus by 40% for 6 Hours",
            "Attention Residue: The Hidden 23-Minute Tax Behind Every Quick Notification",
            "The 5-Minute Neural Activation Rule to Beat Procrastination Automatically",
        ]
        chosen = next((t for t in fallback_topics if slugify(t) not in used_slugs), fallback_topics[0])
        return TopicIdea(
            topic=chosen,
            angle="Evidence-based neuroscience breakdown with a practical 3-step daily protocol",
            hook=f"Most people blame willpower—when the real bottleneck behind {chosen} is basic brain chemistry.",
            source="evergreen_fallback",
            keywords=["neuroscience", "focus", "dopamine", "deep work", "habits"],
            discovered_at=now_iso,
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
    )
