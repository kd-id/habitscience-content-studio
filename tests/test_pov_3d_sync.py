"""Unit tests for 3-Pillar Rotation, Zero-Jargon Ideation, and Story-Synced Studio v9 3D POV."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.config_loader import slugify
from src.habitsains_3d_pov_engine import _schedule_pov_dialogue_events
from src.ideation import PILLAR_TOPIC_BANKS, _looks_academic_jargon, select_next_pillar, select_topic
from src.scriptwriter import (
    REQUIRED_POV_BEATS,
    build_topic_matched_pov_3d_episode,
    normalize_pov_3d_episode,
)

BANNED_JARGON = (
    "prefrontal cortex",
    "amygdala",
    "melatonin",
    "memory consolidation",
    "attention residue",
    "ultradian",
    "neural correlates",
    "coupling",
)


class TestPov3DSyncAndPillars(unittest.TestCase):
    def test_academic_jargon_filter_blocks_dense_paper_titles(self) -> None:
        self.assertTrue(_looks_academic_jargon("Dopamine Supports Coupling of Attention-Related Networks"))
        self.assertTrue(_looks_academic_jargon("How do video games affect brain development in children and teens?"))
        self.assertTrue(_looks_academic_jargon("fMRI Study Finds Cortical Modulation Under Cognitive Load"))
        self.assertFalse(_looks_academic_jargon("Why Drinking Coffee Right After Waking Up Makes You Crash at 2 PM"))
        self.assertFalse(_looks_academic_jargon("72 Hours Without Your Phone: What Happens to Your Brain on Hour 1"))

    def test_three_pillar_rotation_never_collides_back_to_back(self) -> None:
        cfg = {"channel": {"language": "en", "niche": "HabitSains"}}
        with tempfile.TemporaryDirectory() as tmp:
            hist_file = Path(tmp) / "history.json"
            history: list[dict[str, str]] = []
            seen_pillars: list[str] = []
            seen_topics: set[str] = set()

            with patch("src.ideation.discover_trending_candidates", return_value=[]), \
                 patch("src.ideation._rank_topic_with_gemini", return_value=None):
                for _ in range(6):
                    hist_file.write_text(json.dumps(history), encoding="utf-8")
                    idea = select_topic(config=cfg, history_file=hist_file)
                    seen_pillars.append(idea.pillar)
                    self.assertNotIn(idea.topic, seen_topics)
                    seen_topics.add(idea.topic)
                    self.assertFalse(_looks_academic_jargon(idea.topic))
                    history.append({"slug": slugify(idea.topic), "pillar": idea.pillar})

            # Exact non-colliding rotation across 2 full daily cycles (6 runs)
            self.assertEqual(
                seen_pillars,
                ["focus_habits", "everyday_science", "pov_survival", "focus_habits", "everyday_science", "pov_survival"],
            )

    def test_zero_jargon_plain_english_across_all_three_pillars(self) -> None:
        cfg = {"branding": {"watermark_text": "@HabitSains"}}
        for pillar_id, bank in PILLAR_TOPIC_BANKS.items():
            for item in bank:
                ep = build_topic_matched_pov_3d_episode(
                    topic=item["topic"],
                    angle=item["angle"],
                    hook=item["hook"],
                    config=cfg,
                    pillar=pillar_id,
                )
                props = ep["props"]
                dlg = ep["dialogue"]
                self.assertEqual([d["beat"] for d in dlg], list(REQUIRED_POV_BEATS))
                self.assertEqual(len(props["phone_norm_cards"]), 3)
                self.assertEqual(len(props["phone_urgent_cards"]), 3)
                self.assertEqual(len(props["swarm_badges"]), 6)

                full_text = " ".join(
                    [d["text"] for d in dlg]
                    + [str(v) for v in props.values() if isinstance(v, str)]
                ).lower()
                for bad in BANNED_JARGON:
                    self.assertNotIn(bad, full_text, f"Found academic jargon {bad!r} in pillar={pillar_id} topic={item['topic']!r}")

    def test_normalization_clamps_verbose_gemini_output(self) -> None:
        dirty = {
            "props": {
                "series_title": "THIS IS AN EXTREMELY LONG SERIES TITLE THAT WOULD OVERFLOW THE BANNER",
                "phone_norm_cards": [["invalid-color", "VERY LONG CARD TITLE HERE", "Extremely long subtitle that should be clamped cleanly"]],
                "swarm_badges": ["SUPERLONGWORD", "OK"],
            },
            "dialogue": [
                {"beat": "intro", "speaker": "partner", "text": " ".join(["word"] * 45)},
                {"beat": "scan", "speaker": "partner", "text": "Look at this scan showing your energy drops forty percent."},
            ],
        }
        norm = normalize_pov_3d_episode(dirty, topic="Why Coffee Right After Waking Up Makes You Crash at 2 PM", pillar="everyday_science")
        self.assertLessEqual(len(norm["props"]["series_title"]), 22)
        self.assertEqual(len(norm["props"]["phone_norm_cards"]), 3)
        self.assertTrue(norm["props"]["phone_norm_cards"][0][0].startswith("#"))
        self.assertEqual(len(norm["props"]["swarm_badges"]), 6)
        self.assertTrue(all(len(b) <= 7 for b in norm["props"]["swarm_badges"]))
        self.assertEqual([d["beat"] for d in norm["dialogue"]], list(REQUIRED_POV_BEATS))
        self.assertEqual(norm["dialogue"][0]["speaker"], "pov")
        self.assertLessEqual(len(norm["dialogue"][0]["text"].split()), 28)

    def test_schedule_pov_dialogue_events_monotonic_beats(self) -> None:
        raw_clips = [
            {"beat": b, "speaker": "pov" if b in ("intro", "timer_react", "agree") else "partner", "text": f"Line for {b}.", "dur": 4.2, "wav_path": f"{b}.wav"}
            for b in REQUIRED_POV_BEATS
        ]
        events, timings = _schedule_pov_dialogue_events(raw_clips, gap_scale=1.0, endcard_dur=3.5)
        self.assertEqual(len(events), 8)
        ordered_keys = ["t_trap", "t_explain", "t_timer", "t_scan", "t_desk", "t_agree", "t_ping", "t_endcard", "total_dur"]
        vals = [timings[k] for k in ordered_keys]
        self.assertEqual(vals, sorted(vals))
        self.assertLess(timings["total_dur"], 58.2)

    def test_each_pillar_maps_to_a_distinct_short_visual_style(self) -> None:
        from src.config_loader import load_config

        cfg = load_config()
        rot = (cfg.get("content_pillars") or {}).get("rotation") or []
        self.assertEqual(len(rot), 3)
        short_styles = [p.get("visual_style_short") for p in rot]
        self.assertEqual(len(set(short_styles)), 3, f"Expected 3 distinct short visual styles across pillars, got {short_styles}")
        self.assertEqual(short_styles, ["pov_3d_toon", "cinema_broll_html", "minimal_line_story"])


if __name__ == "__main__":
    unittest.main()
