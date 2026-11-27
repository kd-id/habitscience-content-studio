"""Unit tests for Studio v10 Islamic Luminous Visuals, Verified Dalil Bank & Instrument-Free Audio."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.config_loader import load_config
from src.ideation import PILLAR_TOPIC_BANKS, select_topic
from src.islamic_visual_engine import (
    ISLAMIC_VISUAL_MODES,
    _load_amiri_font_css,
    _resolve_dalil_payload,
    build_islamic_visual_html,
)
from src.scriptwriter import generate_content_blueprint
from src.sfx_engine import _nature_bed_spec


class TestIslamicVisualsV10(unittest.TestCase):
    def test_all_30_topics_have_verified_arabic_translit_translation_citation(self) -> None:
        self.assertEqual(
            set(PILLAR_TOPIC_BANKS.keys()),
            {"prophetic_habits", "quran_mental_peace", "sunnah_brain_science"},
        )
        total = 0
        seen_citations: set[str] = set()
        for pillar_id, bank in PILLAR_TOPIC_BANKS.items():
            self.assertEqual(len(bank), 10, f"Pillar {pillar_id} should have 10 curated verified topics")
            for item in bank:
                total += 1
                dalil = item.get("dalil")
                self.assertIsInstance(dalil, dict, f"Missing dalil dict in {item['topic']}")
                assert isinstance(dalil, dict)
                arabic = dalil.get("arabic", "")
                self.assertTrue(any("\u0600" <= ch <= "\u06FF" for ch in arabic), f"Expected Arabic script in {item['topic']}")
                self.assertTrue(len(dalil.get("transliteration", "")) >= 10)
                self.assertTrue(len(dalil.get("translation", "")) >= 15)
                cit = dalil.get("citation", "")
                self.assertTrue(len(cit) >= 8, f"Expected verified citation in {item['topic']}")
                seen_citations.add(cit)
        self.assertEqual(total, 30)
        self.assertGreaterEqual(len(seen_citations), 28)

    def test_amiri_calligraphy_fonts_bundled_and_embeddable(self) -> None:
        css = _load_amiri_font_css()
        self.assertIn("AmiriCalligraphy", css)
        self.assertIn("data:font/ttf;base64,", css)
        self.assertIn("font-weight: 400", css)
        self.assertIn("font-weight: 700", css)

    def test_all_three_v10_modes_build_valid_html_for_9x16_and_16x9(self) -> None:
        sample = PILLAR_TOPIC_BANKS["quran_mental_peace"][0]
        dalil_payload = _resolve_dalil_payload(
            topic_meta={
                "topic": sample["topic"],
                "pillar_label": "Qur'an Wisdom & Mental Peace",
                "channel_handle": "@HabitSains",
                "dalil": sample["dalil"],
            },
            scenes_meta=[],
        )
        payload = {
            "fps": 24,
            "total_dur": 20.0,
            "dalil": dalil_payload,
            "scenes": [{"idx": 0, "start": 0.0, "end": 20.0, "badge": "01 • REFLECT", "headline": "Inner Peace"}],
            "captions": [{"start": 0.2, "end": 3.0, "words": [{"w": "Hearts", "s": 0.2, "e": 0.8}, {"w": "find", "s": 0.8, "e": 1.4}, {"w": "rest.", "s": 1.4, "e": 2.2}]}],
            "rms": [0.4] * 48,
        }
        for mode in ISLAMIC_VISUAL_MODES:
            for w, h in ((720, 1280), (1280, 720)):
                html_doc = build_islamic_visual_html(mode, payload, w, h)
                self.assertIn("window.renderAt", html_doc)
                self.assertIn("AmiriCalligraphy", html_doc)
                self.assertIn("QUR'AN 13:28", html_doc)
                self.assertIn("أَلَا بِذِكْرِ اللَّهِ", html_doc)

    def test_nature_soundscape_contains_zero_musical_oscillators(self) -> None:
        for preset in ("dawn_breeze", "gentle_rain", "calm_water"):
            inp, flt = _nature_bed_spec(preset, duration_sec=30.0, vol_db=-27.0)
            joined = " ".join(inp) + " " + flt
            self.assertIn("anoisesrc=", joined)
            self.assertNotIn("aevalsrc", joined)
            self.assertNotIn("sin(", joined)

    def test_config_routes_three_distinct_v10_modes_and_nature_only_audio(self) -> None:
        cfg = load_config()
        self.assertEqual(cfg["video"].get("ambient_bgm_mode"), "nature_only")
        rot = cfg["content_pillars"]["rotation"]
        self.assertEqual([p["id"] for p in rot], ["prophetic_habits", "quran_mental_peace", "sunnah_brain_science"])
        self.assertEqual([p["visual_style_short"] for p in rot], list(ISLAMIC_VISUAL_MODES))
        self.assertEqual([p["visual_style_long"] for p in rot], list(ISLAMIC_VISUAL_MODES))

    def test_select_topic_and_fallback_blueprint_preserve_verified_dalil(self) -> None:
        cfg = load_config()
        with tempfile.TemporaryDirectory() as tmp:
            hist = Path(tmp) / "history.json"
            hist.write_text("[]", encoding="utf-8")
            idea = select_topic(config=cfg, history_file=hist)
            self.assertIsInstance(idea.dalil, dict)
            assert isinstance(idea.dalil, dict)
            with patch("src.scriptwriter._generate_with_gemini", return_value=(None, "")):
                bp = generate_content_blueprint(idea, cfg)
            self.assertEqual(bp["meta"]["dalil"]["citation"], idea.dalil["citation"])
            self.assertIn(idea.dalil["citation"], bp["youtube_long"]["description"])
            self.assertEqual(len(bp["carousel_social"]["slides"]), 5)


if __name__ == "__main__":
    unittest.main()
