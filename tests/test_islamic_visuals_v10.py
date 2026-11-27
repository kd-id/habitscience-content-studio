"""Unit tests for Studio v10 Islamic Luminous Visuals, Verified Dalil Bank & Instrument-Free Audio."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.arabic_audio import parse_quran_citation, resolve_dalil_arabic_audio
from src.config_loader import load_config
from src.ideation import PILLAR_TOPIC_BANKS, select_topic
from src.islamic_story_acts import resolve_story_acts
from src.islamic_visual_engine import (
    ISLAMIC_VISUAL_MODES,
    _load_amiri_font_css,
    _resolve_dalil_payload,
    build_islamic_visual_html,
)
from src.scriptwriter import ISLAMIC_FORMAT_PROFILES, _build_gemini_prompt, generate_content_blueprint
from src.sfx_engine import _nature_bed_spec


class TestIslamicVisualsV10(unittest.TestCase):
    def test_all_30_topics_have_verified_arabic_translit_translation_citation(self) -> None:
        self.assertEqual(
            set(PILLAR_TOPIC_BANKS.keys()),
            {
                "minute_wisdom_dua",
                "prophetic_habits",
                "sunnah_paper_story",
                "quran_mental_peace",
                "sunnah_particle_map",
                "hadith_cinematic_story",
            },
        )
        total = 0
        seen_citations: set[str] = set()
        for pillar_id, bank in PILLAR_TOPIC_BANKS.items():
            self.assertEqual(len(bank), 5, f"Pillar {pillar_id} should have 5 curated verified topics")
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

    def test_config_routes_six_distinct_v10_modes_and_nature_only_audio(self) -> None:
        cfg = load_config()
        self.assertEqual(cfg["video"].get("ambient_bgm_mode"), "nature_only")
        rot = cfg["content_pillars"]["rotation"]
        self.assertEqual(
            [p["id"] for p in rot],
            [
                "minute_wisdom_dua",
                "prophetic_habits",
                "sunnah_paper_story",
                "quran_mental_peace",
                "sunnah_particle_map",
                "hadith_cinematic_story",
            ],
        )
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

    def test_anti_rancu_isolated_format_prompts_never_mix_styles_or_legacy_pov(self) -> None:
        from src.ideation import TopicIdea

        cfg = load_config()
        self.assertEqual(
            set(ISLAMIC_FORMAT_PROFILES.keys()),
            {
                "minute_wisdom_dua",
                "prophetic_habits",
                "sunnah_paper_story",
                "quran_mental_peace",
                "sunnah_particle_map",
                "hadith_cinematic_story",
            },
        )
        for pillar_id, prof in ISLAMIC_FORMAT_PROFILES.items():
            sample = PILLAR_TOPIC_BANKS[pillar_id][0]
            idea = TopicIdea(
                topic=sample["topic"],
                angle=sample["angle"],
                hook=sample["hook"],
                source="test",
                pillar=pillar_id,
                pillar_label=prof["format_name"],
                dalil=sample["dalil"],
            )
            prompt = _build_gemini_prompt(idea, cfg)
            self.assertIn(prof["visual_style"], prompt)
            self.assertIn(prof["nature_audio"], prompt)
            self.assertIn(sample["dalil"]["citation"], prompt)
            # Strictly isolated: zero legacy POV clutter AND zero competing format visual modes!
            self.assertNotIn("pov_3d_episode", prompt)
            for other_id, other_prof in ISLAMIC_FORMAT_PROFILES.items():
                if other_id != pillar_id:
                    self.assertNotIn(other_prof["visual_style"], prompt)

    def test_quran_citation_parser_and_uncut_qari_adab_routing(self) -> None:
        self.assertEqual(parse_quran_citation("QUR'AN 13:28"), (13, 28, 28))
        self.assertEqual(parse_quran_citation("QUR'AN 94:5-6"), (94, 5, 6))
        self.assertEqual(parse_quran_citation("QUR'AN 78:9-10"), (78, 9, 10))
        self.assertIsNone(parse_quran_citation("SAHIH AL-BUKHARI 6464"))
        self.assertIsNone(parse_quran_citation("SUNAN ABI DAWUD 2606"))

        cfg = load_config()
        with tempfile.TemporaryDirectory() as tmp:
            wdir = Path(tmp)
            fake_qari = wdir / "q.wav"
            fake_qari.write_bytes(b"RIFF" + b"\x00" * 64)
            fake_tts = wdir / "t.wav"
            fake_tts.write_bytes(b"RIFF" + b"\x00" * 64)

            # 1) Short Qur'an Ayah (<=20s) uses real uncut Mishary Alafasy Qari!
            with patch("src.arabic_audio.fetch_everyayah_quran_wav", return_value=(fake_qari, 15.5)):
                res = resolve_dalil_arabic_audio(
                    PILLAR_TOPIC_BANKS["quran_mental_peace"][2]["dalil"], wdir, cfg, is_short=True
                )
                assert res is not None
                self.assertTrue(res.is_real_qari)
                self.assertIn("everyayah:", res.source)

            # 2) Ultra-long Qur'an Ayah (>20s) on Short NEVER chops Qari mid-verse -> routes to Saudi Arabic TTS!
            fake_qari.write_bytes(b"RIFF" + b"\x00" * 64)
            with patch("src.arabic_audio.fetch_everyayah_quran_wav", return_value=(fake_qari, 53.0)), \
                 patch("src.arabic_audio.synthesize_arabic_tts_wav", return_value=(fake_tts, 4.2)):
                res = resolve_dalil_arabic_audio(
                    PILLAR_TOPIC_BANKS["hadith_cinematic_story"][3]["dalil"], wdir, cfg, is_short=True
                )
                assert res is not None
                self.assertFalse(res.is_real_qari)
                self.assertIn("ar-SA-HamedNeural", res.source)

            # 3) Hadith / Prophetic Dua routes cleanly to Saudi Arabic TTS (ar-SA-HamedNeural)
            with patch("src.arabic_audio.synthesize_arabic_tts_wav", return_value=(fake_tts, 3.8)):
                res = resolve_dalil_arabic_audio(
                    PILLAR_TOPIC_BANKS["prophetic_habits"][1]["dalil"], wdir, cfg, is_short=True
                )
                assert res is not None
                self.assertFalse(res.is_real_qari)
                self.assertIn("ar-SA-HamedNeural", res.source)

    def test_four_act_storytelling_staging_across_all_30_topics_and_6_modes(self) -> None:
        # Every single curated topic must resolve a valid 4-Act visual plan
        valid_hooks = {"phone_chaos", "anger_heat", "heavy_wall", "rushing_calendar", "comparison_scroll", "needle_ocean", "racing_mind"}
        valid_explainers = {"brain_wave_calm", "focus_battery_charge", "one_third_pie", "posture_cool_down", "four_pillar_map", "before_after_cards"}
        for pillar_id, bank in PILLAR_TOPIC_BANKS.items():
            for item in bank:
                acts = resolve_story_acts(
                    {"topic": item["topic"], "angle": item["angle"], "dalil": item["dalil"]},
                    scenes_meta=[],
                )
                self.assertIn(acts["hook_visual"], valid_hooks, f"Bad hook_visual for {item['topic']}")
                self.assertIn(acts["explainer_visual"], valid_explainers, f"Bad explainer_visual for {item['topic']}")
                self.assertTrue(len(acts["core_lesson"]) >= 16, f"Core lesson too short for {item['topic']}")
                self.assertTrue(len(acts["stat_badge"]) >= 8)

        # Every one of the 6 visual templates must wire the 4-Act visual engine & stage toggles
        sample = PILLAR_TOPIC_BANKS["quran_mental_peace"][0]
        dalil_payload = _resolve_dalil_payload(
            topic_meta={"topic": sample["topic"], "pillar_label": "Qur'an Peace", "channel_handle": "@HabitSains", "dalil": sample["dalil"]},
            scenes_meta=[],
        )
        payload = {
            "fps": 24,
            "total_dur": 30.0,
            "dalil": dalil_payload,
            "scenes": [{"idx": 0, "start": 0.0, "end": 30.0, "badge": "01 • HOOK", "headline": "Quiet Mind"}],
            "captions": [],
            "rms": [0.3] * 24,
        }
        for mode in ISLAMIC_VISUAL_MODES:
            html = build_islamic_visual_html(mode, payload, 720, 1280)
            self.assertIn("computeFourActTiming", html, f"{mode} missing computeFourActTiming")
            self.assertIn("getCurrentAct", html, f"{mode} missing getCurrentAct")
            self.assertIn("drawAct1HookVisual", html, f"{mode} missing drawAct1HookVisual")
            self.assertIn("drawAct3ExplainerVisual", html, f"{mode} missing drawAct3ExplainerVisual")
            self.assertIn("THE LESSON", html.upper(), f"{mode} missing Act 4 Core Lesson card")


if __name__ == "__main__":
    unittest.main()
