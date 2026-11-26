"""Unit tests verifying all 6 direct free social media API uploaders & publisher routing."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.publisher import publish_all_platforms
from src.social_publishers import (
    _oauth1_header,
    publish_facebook_reel_direct,
    publish_instagram_carousel_direct,
    publish_instagram_reels_direct,
    publish_linkedin_direct,
    publish_tiktok_direct,
    publish_x_and_threads_direct,
)


def _mock_resp(status: int = 200, json_data: dict | None = None, headers: dict | None = None, text: str = "") -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.ok = 200 <= status < 300
    r.json.return_value = json_data or {}
    r.headers = headers or {}
    r.text = text or str(json_data or "")
    return r


class DirectSocialPublishersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.mp4 = self.root / "video_9x16.mp4"
        self.mp4.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"A" * 4096)
        self.slides = []
        for i in range(1, 4):
            p = self.root / f"slide_{i:02d}.png"
            p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"B" * 512)
            self.slides.append(p)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    @patch("src.social_publishers.requests.get")
    @patch("src.social_publishers.requests.post")
    def test_instagram_reels_resumable_publish_and_draft(self, mock_post: MagicMock, mock_get: MagicMock) -> None:
        env = {"META_ACCESS_TOKEN": "tok_meta", "IG_BUSINESS_ACCOUNT_ID": "17841400001"}
        with patch.dict(os.environ, env, clear=True):
            # Publish mode: init -> rupload -> poll FINISHED -> publish -> permalink
            mock_post.side_effect = [
                _mock_resp(200, {"id": "cont_1", "uri": "https://rupload.facebook.com/ig-api-upload/v21.0/cont_1"}),
                _mock_resp(200, {"success": True}),
                _mock_resp(200, {"id": "media_99"}),
            ]
            mock_get.side_effect = [
                _mock_resp(200, {"status_code": "FINISHED"}),
                _mock_resp(200, {"permalink": "https://www.instagram.com/reel/ABC/"}),
            ]
            res = publish_instagram_reels_direct(self.mp4, "Hook caption #HabitSains", "publish")
            self.assertTrue(res["handled"])
            self.assertEqual(res["status"], "PUBLISHED")
            self.assertEqual(res["external_id"], "media_99")
            self.assertEqual(res["url"], "https://www.instagram.com/reel/ABC/")

            # Verify rupload headers used OAuth + offset + file_size
            rupload_call = mock_post.call_args_list[1]
            self.assertEqual(rupload_call.args[0], "https://rupload.facebook.com/ig-api-upload/v21.0/cont_1")
            self.assertEqual(rupload_call.kwargs["headers"]["Authorization"], "OAuth tok_meta")
            self.assertEqual(rupload_call.kwargs["headers"]["offset"], "0")
            self.assertEqual(rupload_call.kwargs["headers"]["file_size"], str(self.mp4.stat().st_size))

            # Draft mode: skips media_publish cleanly
            mock_post.reset_mock()
            mock_get.reset_mock()
            mock_post.side_effect = [
                _mock_resp(200, {"id": "cont_2", "uri": "https://rupload.facebook.com/ig-api-upload/v21.0/cont_2"}),
                _mock_resp(200, {"success": True}),
            ]
            mock_get.side_effect = [_mock_resp(200, {"status_code": "FINISHED"})]
            d_res = publish_instagram_reels_direct(self.mp4, "Draft caption", "draft")
            self.assertEqual(d_res["status"], "DRAFTED")
            self.assertEqual(mock_post.call_count, 2)

    @patch("src.social_publishers.requests.get")
    @patch("src.social_publishers.requests.post")
    def test_instagram_carousel_via_fb_cdn_bridge(self, mock_post: MagicMock, mock_get: MagicMock) -> None:
        env = {"META_ACCESS_TOKEN": "tok_meta", "IG_BUSINESS_ACCOUNT_ID": "ig_1", "FB_PAGE_ID": "fb_1"}
        with patch.dict(os.environ, env, clear=True):
            # get page token + 3 photo image fetches + poll parent + permalink
            mock_get.side_effect = [
                _mock_resp(200, {"access_token": "page_tok"}),
                _mock_resp(200, {"images": [{"source": "https://scontent.fbcdn.net/s1.png"}]}),
                _mock_resp(200, {"images": [{"source": "https://scontent.fbcdn.net/s2.png"}]}),
                _mock_resp(200, {"images": [{"source": "https://scontent.fbcdn.net/s3.png"}]}),
                _mock_resp(200, {"status_code": "FINISHED"}),
                _mock_resp(200, {"permalink": "https://www.instagram.com/p/CAR1/"}),
            ]
            # 3x (FB unpublished photo + IG child container) + parent CAROUSEL + media_publish
            mock_post.side_effect = [
                _mock_resp(200, {"id": "fbp1"}), _mock_resp(200, {"id": "c1"}),
                _mock_resp(200, {"id": "fbp2"}), _mock_resp(200, {"id": "c2"}),
                _mock_resp(200, {"id": "fbp3"}), _mock_resp(200, {"id": "c3"}),
                _mock_resp(200, {"id": "parent_car"}),
                _mock_resp(200, {"id": "pub_car"}),
            ]
            res = publish_instagram_carousel_direct(self.slides, "Carousel caption", "publish")
            self.assertEqual(res["status"], "PUBLISHED")
            self.assertEqual(res["url"], "https://www.instagram.com/p/CAR1/")

    @patch("src.social_publishers.requests.get")
    @patch("src.social_publishers.requests.post")
    def test_facebook_reels_native_draft(self, mock_post: MagicMock, mock_get: MagicMock) -> None:
        env = {"META_ACCESS_TOKEN": "tok_meta", "FB_PAGE_ID": "fb_1"}
        with patch.dict(os.environ, env, clear=True):
            mock_get.return_value = _mock_resp(200, {"access_token": "page_tok"})
            mock_post.side_effect = [
                _mock_resp(200, {"video_id": "v_123", "upload_url": "https://rupload.facebook.com/video-upload/v_123"}),
                _mock_resp(200, {"success": True}),
                _mock_resp(200, {"success": True}),
            ]
            res = publish_facebook_reel_direct(self.mp4, "FB Reel draft", "draft")
            self.assertEqual(res["status"], "DRAFTED")
            self.assertEqual(res["external_id"], "v_123")
            finish_body = mock_post.call_args_list[2].kwargs["json"]
            self.assertEqual(finish_body["video_state"], "DRAFT")

    @patch("src.social_publishers.requests.put")
    @patch("src.social_publishers.requests.post")
    def test_tiktok_inbox_upload_with_auto_refresh(self, mock_post: MagicMock, mock_put: MagicMock) -> None:
        env = {
            "TIKTOK_REFRESH_TOKEN": "rt_365d",
            "TIKTOK_CLIENT_KEY": "ck_1",
            "TIKTOK_CLIENT_SECRET": "cs_1",
        }
        with patch.dict(os.environ, env, clear=True):
            mock_post.side_effect = [
                _mock_resp(200, {"access_token": "fresh_tt_tok"}),
                _mock_resp(200, {
                    "data": {"publish_id": "v_inbox~1", "upload_url": "https://open-upload.tiktokapis.com/video/?id=1"},
                    "error": {"code": "ok", "message": ""},
                }),
            ]
            mock_put.return_value = _mock_resp(201, {})
            res = publish_tiktok_direct(self.mp4, "TikTok caption #HabitSains", "draft")
            self.assertTrue(res["handled"])
            self.assertEqual(res["status"], "DRAFTED")
            self.assertEqual(res["external_id"], "v_inbox~1")
            expected_range = f"bytes 0-{self.mp4.stat().st_size - 1}/{self.mp4.stat().st_size}"
            self.assertEqual(mock_put.call_args.kwargs["headers"]["Content-Range"], expected_range)

    @patch("src.social_publishers.requests.put")
    @patch("src.social_publishers.requests.post")
    def test_linkedin_multi_image_publish(self, mock_post: MagicMock, mock_put: MagicMock) -> None:
        env = {"LINKEDIN_ACCESS_TOKEN": "li_tok", "LINKEDIN_AUTHOR_URN": "urn:li:person:abc123"}
        with patch.dict(os.environ, env, clear=True):
            mock_post.side_effect = [
                _mock_resp(200, {"value": {"uploadUrl": "https://li.dms/1", "image": "urn:li:image:1"}}),
                _mock_resp(200, {"value": {"uploadUrl": "https://li.dms/2", "image": "urn:li:image:2"}}),
                _mock_resp(200, {"value": {"uploadUrl": "https://li.dms/3", "image": "urn:li:image:3"}}),
                _mock_resp(201, {}, headers={"x-restli-id": "urn:li:share:999"}),
            ]
            mock_put.return_value = _mock_resp(201, {})
            res = publish_linkedin_direct(self.slides, "LinkedIn science post", "publish")
            self.assertEqual(res["status"], "PUBLISHED")
            self.assertEqual(res["external_id"], "urn:li:share:999")
            post_body = mock_post.call_args_list[3].kwargs["json"]
            self.assertIn("multiImage", post_body["content"])
            self.assertEqual(len(post_body["content"]["multiImage"]["images"]), 3)

    @patch("src.social_publishers.requests.post")
    def test_threads_and_x_direct_publish(self, mock_post: MagicMock) -> None:
        hdr = _oauth1_header("POST", "https://api.x.com/2/tweets", "k", "s", "at", "as")
        self.assertTrue(hdr.startswith("OAuth "))
        self.assertIn("oauth_signature=", hdr)

        env = {
            "THREADS_ACCESS_TOKEN": "th_tok",
            "THREADS_USER_ID": "th_uid",
            "X_API_KEY": "xk",
            "X_API_SECRET": "xs",
            "X_ACCESS_TOKEN": "xat",
            "X_ACCESS_SECRET": "xas",
        }
        with patch.dict(os.environ, env, clear=True):
            mock_post.side_effect = [
                _mock_resp(200, {"id": "th_c1"}),
                _mock_resp(200, {"id": "th_pub1"}),
                _mock_resp(201, {"data": {"id": "tw_1"}}),
                _mock_resp(201, {"data": {"id": "tw_2"}}),
            ]
            res = publish_x_and_threads_direct(["Tweet 1", "Tweet 2"], "Threads post", "publish")
            self.assertEqual(res["status"], "PUBLISHED")
            self.assertIn("threads:th_pub1", res["external_id"])
            self.assertIn("x:tw_1", res["external_id"])
            # Verify 2nd tweet chained as reply to 1st tweet
            second_x_body = mock_post.call_args_list[3].kwargs["json"]
            self.assertEqual(second_x_body["reply"]["in_reply_to_tweet_id"], "tw_1")

    def test_publisher_routing_dry_run(self) -> None:
        bp = {
            "meta": {"topic": "Focus Science", "channel_name": "HabitSains"},
            "youtube_long": {"title": "Focus Science", "description": "", "tags": []},
            "shorts_reels_tiktok": {"title": "Focus Short", "caption_ig_reels": "IG", "caption_tiktok": "TT", "caption_yt_shorts": "YT", "hashtags": []},
            "carousel_social": {"caption_instagram": "C", "caption_linkedin": "L", "thread_x": ["T1"], "post_threads": "TH", "post_facebook": "FB", "hashtags": []},
        }
        assets = {
            "youtube_long": {"video_path": str(self.mp4), "thumbnail_path": str(self.slides[0])},
            "shorts_reels_tiktok": {"video_path": str(self.mp4)},
            "carousel_social": {"slide_paths": [str(p) for p in self.slides]},
        }
        cfg = {
            "platforms": {
                "youtube_long": {"enabled": True},
                "youtube_shorts": {"enabled": True},
                "instagram_reels": {"enabled": True, "adapter": "direct"},
                "instagram_carousel": {"enabled": True, "adapter": "direct"},
                "tiktok": {"enabled": True, "adapter": "direct"},
                "linkedin": {"enabled": True, "adapter": "direct"},
                "x_threads": {"enabled": True, "adapter": "direct"},
                "facebook": {"enabled": True, "adapter": "direct"},
            },
            "publishing": {"save_payload_snapshots": True},
        }
        summary = publish_all_platforms(bp, assets, self.root, cfg, self.root, publish_mode="dry-run")
        self.assertEqual(summary["counts"]["total"], 8)
        self.assertEqual(summary["counts"]["dry_run_ready"], 8)


if __name__ == "__main__":
    unittest.main()
