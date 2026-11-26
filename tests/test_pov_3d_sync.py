"""Unit tests for Story-Synced Studio v9 3D POV script, props, and timing choreography."""

from __future__ import annotations

import unittest

from src.habitsains_3d_pov_engine import _schedule_pov_dialogue_events
from src.scriptwriter import (
    REQUIRED_POV_BEATS,
    build_topic_matched_pov_3d_episode,
    normalize_pov_3d_episode,
)


class TestPov3DSync(unittest.TestCase):
    def test_dopamine_attention_coupling_episode_matches_topic(self) -> None:
        ep = build_topic_matched_pov_3d_episode(
            topic="Dopamine Supports Coupling of Attention-Related Networks",
            angle="Neuroscience breakdown of dopamine and attention networks",
            hook="Why quick scrolling breaks attention network coupling.",
            config={"branding": {"watermark_text": "@HabitSains"}},
        )
        props = ep["props"]
        dlg = ep["dialogue"]

        self.assertEqual([d["beat"] for d in dlg], list(REQUIRED_POV_BEATS))
        self.assertEqual([d["speaker"] for d in dlg], ["pov", "partner", "partner", "pov", "partner", "partner", "pov", "partner"])
        self.assertEqual(len(props["phone_norm_cards"]), 3)
        self.assertEqual(len(props["phone_urgent_cards"]), 3)
        self.assertEqual(len(props["swarm_badges"]), 6)

        # Verify topic coupling terms appear in BOTH 3D props AND spoken beats!
        self.assertIn("ATTENTION", props["scan_title"].upper())
        self.assertIn("COUPLING", props["scan_stat"].upper())
        self.assertIn("DOPAMINE", props["series_title"].upper())
        self.assertIn("COUPLING", props["series_title"].upper())
        self.assertNotIn("SUPPORTS", props["series_title"].upper())
        self.assertTrue(any("coupling" in d["text"].lower() for d in dlg))
        self.assertTrue(any("scan" in d["text"].lower() for d in dlg if d["beat"] == "scan"))
        self.assertTrue(any("desk" in d["text"].lower() for d in dlg if d["beat"] == "desk"))
        self.assertTrue(any("alert" in d["text"].lower() or "hand" in d["text"].lower() for d in dlg if d["beat"] == "ping"))

    def test_archetype_coverage_and_normalization_clamping(self) -> None:
        topics = [
            "How Late-Night Sleep Debt Ruins Prefrontal Focus",
            "The 23-Minute Rule: What Multitasking Does to Your Brain",
            "Procrastination Is Not Laziness: The Emotional Regulation Loop",
            "The 90-Minute Ultradian Cycle: Work Less and Produce More",
            "Why Morning Sunlight Resets Your Cortisol Rhythm",
            "Neuroplasticity Tricks for Rapid Skill Mastery",
        ]
        for t in topics:
            ep = build_topic_matched_pov_3d_episode(topic=t, config={"branding": {"watermark_text": "@HabitSains"}})
            self.assertEqual(len(ep["dialogue"]), 8)
            self.assertTrue(all(len(d["text"].split()) <= 30 for d in ep["dialogue"]), f"Line too long for {t}")

        # Verify malformed / overly verbose Gemini JSON is safely sanitized without crashing
        dirty = {
            "props": {
                "series_title": "THIS IS AN EXTREMELY LONG SERIES TITLE THAT WOULD OVERFLOW THE BANNER",
                "phone_norm_cards": [["invalid-color", "VERY LONG CARD TITLE HERE", "Extremely long subtitle that should be clamped cleanly"]],
                "swarm_badges": ["SUPERLONGWORD", "OK"],
            },
            "dialogue": [
                {"beat": "intro", "speaker": "partner", "text": " ".join(["word"] * 45)},
                {"beat": "scan", "speaker": "partner", "text": "Look at this scan showing a forty percent drop in clarity."},
            ],
        }
        norm = normalize_pov_3d_episode(dirty, topic="Test Focus Science")
        self.assertLessEqual(len(norm["props"]["series_title"]), 22)
        self.assertEqual(len(norm["props"]["phone_norm_cards"]), 3)
        self.assertTrue(norm["props"]["phone_norm_cards"][0][0].startswith("#"))
        self.assertEqual(len(norm["props"]["swarm_badges"]), 6)
        self.assertTrue(all(len(b) <= 7 for b in norm["props"]["swarm_badges"]))
        self.assertEqual([d["beat"] for d in norm["dialogue"]], list(REQUIRED_POV_BEATS))
        # Speaker role is strictly enforced by beat even if model swapped it
        self.assertEqual(norm["dialogue"][0]["speaker"], "pov")
        self.assertLessEqual(len(norm["dialogue"][0]["text"].split()), 28)
        self.assertIn("forty percent", norm["dialogue"][4]["text"])

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


if __name__ == "__main__":
    unittest.main()
