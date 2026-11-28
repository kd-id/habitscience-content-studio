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
                "islamic_science_qa_pov",
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
        self.assertEqual(total, 35)
        self.assertGreaterEqual(len(seen_citations), 32)

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
                "islamic_science_qa_pov",
            ],
        )
        self.assertEqual([p["visual_style_short"] for p in rot], list(ISLAMIC_VISUAL_MODES) + ["pov_3d_toon"])
        self.assertEqual([p["visual_style_long"] for p in rot][:6], list(ISLAMIC_VISUAL_MODES))
        self.assertEqual(rot[6]["visual_style_short"], "pov_3d_toon")

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

            # 1) Short complete Qur'an Ayah (<=20s) uses real uncut Mishary Alafasy Qari + word timings!
            fake_segs = [{"i": 0, "s": 0.1, "e": 0.9}, {"i": 1, "s": 0.9, "e": 1.8}]
            with patch("src.arabic_audio.fetch_everyayah_quran_wav", return_value=(fake_qari, 15.5)), \
                 patch("src.arabic_audio.fetch_quran_word_timings", return_value=fake_segs):
                res = resolve_dalil_arabic_audio(
                    PILLAR_TOPIC_BANKS["quran_mental_peace"][2]["dalil"], wdir, cfg, is_short=True
                )
                assert res is not None
                self.assertTrue(res.is_real_qari)
                self.assertIn("everyayah:", res.source)
                self.assertEqual(len(res.word_timings), 2)

            # 2) Curated Qur'an excerpt (is_excerpt=True, e.g., 2:286) routes straight to ar-SA-HamedNeural so displayed words match spoken audio 100%!
            with patch("src.arabic_audio.fetch_everyayah_quran_wav") as mock_everyayah, \
                 patch("src.arabic_audio.synthesize_arabic_tts_wav", return_value=(fake_tts, 4.2)):
                res = resolve_dalil_arabic_audio(
                    PILLAR_TOPIC_BANKS["hadith_cinematic_story"][3]["dalil"], wdir, cfg, is_short=True
                )
                assert res is not None
                self.assertFalse(res.is_real_qari)
                self.assertIn("ar-SA-HamedNeural", res.source)
                mock_everyayah.assert_not_called()

            # 3) Hadith / Prophetic Dua routes cleanly to Saudi Arabic TTS (ar-SA-HamedNeural)
            with patch("src.arabic_audio.synthesize_arabic_tts_wav", return_value=(fake_tts, 3.8)):
                res = resolve_dalil_arabic_audio(
                    PILLAR_TOPIC_BANKS["prophetic_habits"][1]["dalil"], wdir, cfg, is_short=True
                )
                assert res is not None
                self.assertFalse(res.is_real_qari)
                self.assertIn("ar-SA-HamedNeural", res.source)

    def test_v12_complete_verses_papercraft_kit_and_exact_word_sync(self) -> None:
        # 1) Verify all 11 studio-lit 2.5D Paper-Cutout transparent PNG sprites exist in assets/papercraft_kit/
        kit_dir = Path(__file__).resolve().parent.parent / "assets" / "papercraft_kit"
        expected_sprites = {
            "presenter_point.png", "presenter_scroll.png", "presenter_dua.png",
            "sunburst_3d.png", "calendar_3d.png", "plaque_islamic.png",
            "open_book_3d.png", "cloud_3d.png", "dome_medallion_3d.png",
            "garden_arch_fg.png", "sunrise_hills_fg.png",
        }
        present = {p.name for p in kit_dir.glob("*.png")}
        self.assertTrue(expected_sprites.issubset(present), f"Missing sprites: {expected_sprites - present}")

        # 2) Complete Qur'an verses (13:28, 14:7, 2:153, 25:63) have full Ayah Arabic matching EveryAyah 1:1
        by_cit = {
            item["dalil"]["citation"]: item["dalil"]
            for bank in PILLAR_TOPIC_BANKS.values()
            for item in bank
        }
        self.assertIn("الَّذِينَ آمَنُوا", by_cit["QUR'AN 13:28"]["arabic"])
        self.assertIn("أَلَا بِذِكْرِ اللَّهِ", by_cit["QUR'AN 13:28"]["arabic"])
        self.assertIn("وَإِذْ تَأَذَّنَ", by_cit["QUR'AN 14:7"]["arabic"])
        self.assertIn("يَـٰٓأَيُّهَا", by_cit["QUR'AN 2:153"]["arabic"])
        self.assertIn("قَالُوا سَلَامًا", by_cit["QUR'AN 25:63"]["arabic"])
        for ex_cit in ("QUR'AN 13:11", "QUR'AN 65:3", "QUR'AN 3:173", "QUR'AN 2:286"):
            self.assertTrue(by_cit[ex_cit].get("is_excerpt"), f"Expected is_excerpt=True on {ex_cit}")

        # 3) All 6 modes wire exact millisecond Arabic word karaoke (`buildArabicKaraokeHTML` + `updateArabicKaraokeAt`)
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
            for w, h in ((720, 1280), (1280, 720)):
                html = build_islamic_visual_html(mode, payload, w, h)
                self.assertIn("buildArabicKaraokeHTML", html, f"{mode} missing buildArabicKaraokeHTML")
                self.assertIn("updateArabicKaraokeAt", html, f"{mode} missing updateArabicKaraokeAt")
                self.assertIn("springOut", html, f"{mode} missing springOut true-motion curve")
                if mode == "islamic_paper_craft":
                    self.assertIn("sunburst_3d", html)
                    self.assertIn("window._assetsReady", html)

    def test_v125_six_pillar_human_editorial_carousels_and_amiri_rtl(self) -> None:
        from src.islamic_carousel_engine import CAROUSEL_THEMES, build_islamic_carousel_html

        cfg = load_config()
        seen_themes: set[str] = set()
        for pillar_id, bank in PILLAR_TOPIC_BANKS.items():
            sample = bank[0]
            bp = {
                "meta": {
                    "topic": sample["topic"],
                    "angle": sample["angle"],
                    "hook": sample["hook"],
                    "pillar": pillar_id,
                    "channel_handle": "@HabitSains",
                    "dalil": sample["dalil"],
                },
                "carousel_social": {
                    "slides": [
                        {"slide_no": 1, "badge": "COVER", "headline": sample["topic"], "body": sample["hook"], "highlight": ""},
                        {"slide_no": 2, "badge": "SOURCE", "headline": "Verified Wisdom", "body": "Reflect slowly on these words.", "highlight": sample["dalil"]["citation"]},
                        {"slide_no": 3, "badge": "SCIENCE", "headline": "How It Calms Your Brain", "body": "Quiet Prophetic rhythm lowers mental noise.", "highlight": ""},
                        {"slide_no": 4, "badge": "PRACTICE", "headline": "Try This Today", "body": "1) Pause for one breath. 2) Whisper Dhikr. 3) Keep it daily.", "highlight": "Consistency beats intensity."},
                        {"slide_no": 5, "badge": "KEEPSAKE", "headline": "Hold On To Peace", "body": "Save this reminder for a busy day.", "highlight": "Save & share"},
                    ]
                },
            }
            html_doc, theme_id = build_islamic_carousel_html(bp, cfg)
            seen_themes.add(theme_id)
            self.assertIn("AmiriCalligraphy", html_doc)
            self.assertIn("direction: rtl", html_doc)
            self.assertIn(sample["dalil"]["arabic"], html_doc)
            self.assertIn(sample["dalil"]["citation"], html_doc)
            for s_idx in range(1, 6):
                self.assertIn(f'id="slide_0{s_idx}"', html_doc)
            if pillar_id == "sunnah_paper_story":
                self.assertIn("data:image/png;base64,", html_doc)
        self.assertEqual(len(seen_themes), 7)
        self.assertEqual(set(CAROUSEL_THEMES.keys()), set(PILLAR_TOPIC_BANKS.keys()))

    def test_v13_high_ctr_thumbnails_and_zero_internal_act_hook_debug_labels(self) -> None:
        from src.islamic_thumbnail_engine import build_high_ctr_thumbnail_html

        cfg = load_config()
        # 1) All 6 video engines must NEVER leak internal 'ACT 1', '1. HOOK', '1. THE HOOK', or 'ACT ${act.num}' onto screen
        sample = PILLAR_TOPIC_BANKS["quran_mental_peace"][0]
        dalil_p = _resolve_dalil_payload(
            topic_meta={"topic": sample["topic"], "pillar_label": "Qur'an Peace", "channel_handle": "@HabitSains", "dalil": sample["dalil"]},
            scenes_meta=[],
        )
        payload = {
            "fps": 24, "total_dur": 30.0, "dalil": dalil_p,
            "scenes": [{"idx": 0, "start": 0.0, "end": 30.0, "badge": "REFLECT", "headline": "Quiet Mind"}],
            "captions": [], "rms": [0.3] * 24,
        }
        forbidden_ui = ("ACT 1 •", "ACT 2 •", "ACT 3 •", "ACT 4 •", "1. HOOK", "1. THE HOOK", "2. VERIFIED DALIL", "ACT ${act.num}")
        for mode in ISLAMIC_VISUAL_MODES:
            html_doc = build_islamic_visual_html(mode, payload, 720, 1280)
            for bad in forbidden_ui:
                self.assertNotIn(bad, html_doc, f"Internal script label '{bad}' leaked into {mode}")

        # 2) High-CTR Thumbnail engine covers all 6 Islamic pillars + secular fallback
        seen_t: set[str] = set()
        for pid, bank in PILLAR_TOPIC_BANKS.items():
            item = bank[0]
            bp = {"meta": {"topic": item["topic"], "pillar": pid, "dalil": item["dalil"]}, "youtube_long": {"thumbnail": {}}}
            t_html, t_theme = build_high_ctr_thumbnail_html(bp, cfg)
            seen_t.add(t_theme)
            self.assertIn("1280px", t_html)
            self.assertIn("AmiriCalligraphy", t_html)
        self.assertEqual(len(seen_t), 7)

    def test_v135_topic_specific_carousel_assets_vary_across_titles_and_pillars(self) -> None:
        from src.islamic_carousel_engine import build_islamic_carousel_html, resolve_carousel_asset_kit

        # 1) All 11 new topic-specific 3D paper-cutout sprites exist in assets/papercraft_kit/
        kit_dir = Path(__file__).resolve().parent.parent / "assets" / "papercraft_kit"
        new_sprites = {
            "ocean_needle_3d.png", "lantern_heart_3d.png", "storm_to_bloom_3d.png",
            "compass_arch_3d.png", "fajr_mosque_3d.png", "crescent_window_3d.png",
            "water_pitcher_3d.png", "balance_scale_3d.png", "hourglass_focus_3d.png",
            "growing_sapling_3d.png", "brain_bloom_3d.png",
        }
        present = {p.name for p in kit_dir.glob("*.png")}
        self.assertTrue(new_sprites.issubset(present), f"Missing v13.5 sprites: {new_sprites - present}")

        # 2) Across the 6 flagship pillar posts (bank[0]), ALL 6 Slide 1 hero props MUST be 100% distinct!
        cfg = load_config()
        flagship_s1_props: set[str] = set()
        seen_s2_frames: set[str] = set()
        seen_s4_fgs: set[str] = set()
        for pillar_id, bank in PILLAR_TOPIC_BANKS.items():
            # Also verify titles WITHIN the same pillar get multiple distinct Slide 1 assets!
            pillar_s1_props: set[str] = set()
            for idx, item in enumerate(bank):
                bp = {
                    "meta": {"topic": item["topic"], "angle": item["angle"], "hook": item["hook"], "pillar": pillar_id, "keywords": item["keywords"], "dalil": item["dalil"]},
                    "carousel_social": {"slides": [{"slide_no": i, "headline": item["topic"], "body": item["hook"]} for i in range(1, 6)]},
                }
                acts = resolve_story_acts(bp["meta"], scenes_meta=[])
                plan = resolve_carousel_asset_kit(bp, pillar_id, item["dalil"], acts)
                pillar_s1_props.add(plan["slide1_prop"])
                # Never duplicate Slide 1 prop onto Slide 3 or Slide 5 inside the same carousel!
                self.assertNotEqual(plan["slide1_prop"], plan["slide3_prop"], f"Duplicate S1/S3 prop on {item['topic']}")
                self.assertNotEqual(plan["slide1_prop"], plan["slide5_prop"], f"Duplicate S1/S5 prop on {item['topic']}")
                if idx == 0:
                    flagship_s1_props.add(plan["slide1_prop"])
                    seen_s2_frames.add(plan["slide2_frame"])
                    seen_s4_fgs.add(plan["slide4_fg"])
                    html_doc, _ = build_islamic_carousel_html(bp, cfg)
                    self.assertIn(f'data-prop="{plan["slide1_prop"]}"', html_doc)
                    self.assertIn(f'data-frame="{plan["slide2_frame"]}"', html_doc)
                    self.assertIn(f'data-fg="{plan["slide4_fg"]}"', html_doc)
            self.assertGreaterEqual(len(pillar_s1_props), 4, f"Pillar {pillar_id} reused too many Slide 1 assets: {pillar_s1_props}")

        self.assertEqual(len(flagship_s1_props), 7, f"Expected 7 distinct flagship Slide 1 props, got {flagship_s1_props}")
        self.assertEqual(len(seen_s2_frames), 3, f"Expected all 3 Arabic calligraphy frames used, got {seen_s2_frames}")
        self.assertGreaterEqual(len(seen_s4_fgs), 3, f"Expected >=3 distinct Slide 4 foregrounds, got {seen_s4_fgs}")

    def test_v14_edge_tts_word_boundary_sync_and_pillar7_3d_pov_schedule(self) -> None:
        import inspect
        from src import voiceover

        src_edge = inspect.getsource(voiceover._synthesize_single_scene_edge)
        self.assertIn('boundary="WordBoundary"', src_edge)

        # Verify Pillar #7 3D POV Q&A script builds cleanly for Islamic Science topics
        from src.scriptwriter import build_topic_matched_pov_3d_episode
        ep = build_topic_matched_pov_3d_episode(
            topic="Why Does Prostration (Sujood) Instantly Lower Mental Stress?",
            pillar="islamic_science_qa_pov",
        )
        self.assertEqual(len(ep["dialogue"]), 8)
        self.assertEqual(ep["dialogue"][0]["beat"], "intro")
        self.assertIn("ISLAMIC SCIENCE", ep["props"]["series_eyebrow"])

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
