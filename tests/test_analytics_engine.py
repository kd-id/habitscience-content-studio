"""Unit tests for Closed-Loop Analytics, Visual Style Optimizer & Sequel Auto-Selection."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.analytics_engine import (
    choose_next_visual_styles,
    compute_growth_deltas,
    compute_pillar_leaderboard,
    compute_style_leaderboard,
)
from src.ideation import select_topic


class AnalyticsOptimizerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_style_leaderboard_and_epsilon_greedy_winner(self) -> None:
        history = [
            {"external_ids": {"YouTube Shorts (9:16)": "s1"}, "visual_style_short": "pov_3d_toon", "visual_style_long": "cozy_diorama"},
            {"external_ids": {"YouTube Shorts (9:16)": "s2"}, "visual_style_short": "pov_3d_toon", "visual_style_long": "cozy_diorama"},
            {"external_ids": {"YouTube Shorts (9:16)": "s3"}, "visual_style_short": "minimal_line_story", "visual_style_long": "cozy_diorama"},
            {"external_ids": {"YouTube Shorts (9:16)": "s4"}, "visual_style_short": "minimal_line_story", "visual_style_long": "cozy_diorama"},
        ]
        videos = [
            {"id": "s1", "platform": "YouTube Shorts", "privacy": "public", "views": 1200, "likes": 80, "comments": 10, "score": 1860.0},
            {"id": "s2", "platform": "YouTube Shorts", "privacy": "public", "views": 1600, "likes": 90, "comments": 12, "score": 2356.0},
            {"id": "s3", "platform": "YouTube Shorts", "privacy": "public", "views": 9500, "likes": 400, "comments": 45, "score": 12710.0},
            {"id": "s4", "platform": "YouTube Shorts", "privacy": "public", "views": 8800, "likes": 350, "comments": 40, "score": 11620.0},
        ]
        board = compute_style_leaderboard(videos, history)
        self.assertEqual(board["short"]["minimal_line_story"]["videos"], 2)
        self.assertGreater(board["short"]["minimal_line_story"]["avg_views"], board["short"]["pov_3d_toon"]["avg_views"])

        ins_file = self.root / "analytics_insights.json"
        ins_file.write_text(json.dumps({"style_leaderboard": board}), encoding="utf-8")

        # Non-explore run (run #3): must EXPLOIT data-backed winner 'minimal_line_story'!
        l_st, s_st, reason = choose_next_visual_styles(ins_file, history_count=3, config={"video": {"style_explore_every_n_runs": 5}})
        self.assertEqual(l_st, "cozy_diorama")
        self.assertEqual(s_st, "minimal_line_story")
        self.assertIn("exploit_best", reason)

        # Explore run (run #5): must EXPLORE a different challenger visual style!
        l_st2, s_st2, reason2 = choose_next_visual_styles(ins_file, history_count=5, config={"video": {"style_explore_every_n_runs": 5}})
        self.assertNotEqual(s_st2, "minimal_line_story")
        self.assertIn("explore_challenger_short", reason2)

    def test_ideation_auto_picks_part2_sequel_on_every_3rd_run(self) -> None:
        hist_file = self.root / "history.json"
        hist_file.write_text(json.dumps([{"slug": "ep-1"}, {"slug": "ep-2"}, {"slug": "ep-3"}]), encoding="utf-8")
        ins_file = self.root / "analytics_insights.json"
        ins_file.write_text(json.dumps({
            "total_views_all_platforms": 4500,
            "recommended_sequels": [
                {
                    "topic": "Part 2: The 7 AM Dopamine Trap — What Happens at 3 PM",
                    "angle": "Sequel to our #1 most watched Short",
                    "hook": "76% of you chose Option A — here is what happens to your brain at 3 PM!",
                    "keywords": ["dopamine", "part 2", "focus"],
                }
            ],
        }), encoding="utf-8")

        idea = select_topic(
            config={"channel": {"language": "en", "niche": "Focus Science"}},
            history_file=hist_file,
        )
        self.assertEqual(idea.source, "analytics_sequel")
        self.assertIn("Part 2", idea.topic)

    def test_growth_deltas_rising_videos_and_pillar_leaderboard(self) -> None:
        prev = {
            "updated_at_wib": "2026-11-26 19:13:00 WIB",
            "total_views_all_platforms": 300,
            "account_stats": {"yt_subscribers": 10, "ig_followers": 100, "fb_followers": 50},
            "video_views_snapshot": {"v1": 200, "v2": 100},
        }
        current_videos = [
            {"id": "v1", "title": "Phone Face Down", "platform": "Instagram Reels", "privacy": "public", "views": 650, "likes": 30, "comments": 8, "score": 974.0},
            {"id": "v2", "title": "Coffee 2 PM Crash", "platform": "YouTube Shorts", "privacy": "public", "views": 180, "likes": 10, "comments": 2, "score": 276.0},
        ]
        cur_acct = {"yt_subscribers": 15, "ig_followers": 112, "fb_followers": 53}
        g = compute_growth_deltas(prev, current_videos, cur_acct)
        self.assertEqual(g["delta_total_views"], 530)
        self.assertEqual(g["delta_yt_subs"], 5)
        self.assertEqual(g["delta_ig_followers"], 12)
        self.assertEqual(g["rising_videos"][0]["id"], "v1")
        self.assertEqual(g["rising_videos"][0]["delta_views"], 450)

        hist = [
            {"pillar_label": "Everyday Focus & Habits", "external_ids": {"Instagram Reels": "v1"}},
            {"pillar_label": "Fun Everyday Science", "external_ids": {"YouTube Shorts": "v2"}},
        ]
        pboard = compute_pillar_leaderboard(current_videos, hist)
        self.assertEqual(pboard["Everyday Focus & Habits"]["avg_views"], 650.0)
        self.assertEqual(pboard["Fun Everyday Science"]["avg_views"], 180.0)


if __name__ == "__main__":
    unittest.main()
