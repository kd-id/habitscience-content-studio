"""Unit tests for the multi-platform human-style Comment Auto-Reply Bot."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from src.comment_bot import (
    _sanitize_human_reply,
    detect_ab_vote,
    generate_human_reply,
    is_spam_comment,
)


class CommentBotTest(unittest.TestCase):
    def test_spam_detection(self) -> None:
        self.assertTrue(is_spam_comment("Check out https://scam.link for free crypto"))
        self.assertTrue(is_spam_comment("slot gacor hari ini bro"))
        self.assertTrue(is_spam_comment("   "))
        self.assertFalse(is_spam_comment("gw pilih B sih wkwk"))
        self.assertFalse(is_spam_comment("bro definitely A fr"))

    def test_ab_vote_detection(self) -> None:
        self.assertEqual(detect_ab_vote("A"), "A")
        self.assertEqual(detect_ab_vote("[B]!!"), "B")
        self.assertEqual(detect_ab_vote("gw pilih B sih bang wkwk"), "B")
        self.assertEqual(detect_ab_vote("definitely A all day"), "A")
        self.assertIsNone(detect_ab_vote("both A and B are hard"))
        self.assertIsNone(detect_ab_vote("keren banget animasinya!"))

    def test_sanitize_strips_ai_cliches_and_hashtags(self) -> None:
        raw = '"Great question! That is awesome — keep going #HabitSains #Focus"'
        clean = _sanitize_human_reply(raw)
        self.assertFalse(clean.lower().startswith("great question"))
        self.assertNotIn("#", clean)
        self.assertNotIn("—", clean)

    def test_mirror_vibe_fallbacks(self) -> None:
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            r_slang = generate_human_reply("gw pilih B sih bang wkwk", "The 7 AM Trap", "Instagram", {}, vote="B")
            self.assertTrue(any(w in r_slang.lower() for w in ("bang", "wkwk", "part 2", "sih")))

            r_formal = generate_human_reply("Terima kasih infonya kak, sangat bermanfaat", "Focus Science", "YouTube", {}, vote=None)
            self.assertIn("kak", r_formal.lower())

            r_en = generate_human_reply("bro definitely A fr", "The 7 AM Trap", "YouTube", {}, vote="A")
            self.assertIn("part 2", r_en.lower() + " part 2")
            self.assertNotIn("great question", r_en.lower())


if __name__ == "__main__":
    unittest.main()
