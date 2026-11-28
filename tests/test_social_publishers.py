"""Unit tests verifying all 6 direct free social media API uploaders & publisher routing."""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.publisher import publish_all_platforms
from src.scheduler_state import (
    allocate_youtube_schedule_slots,
    compute_facebook_prime_schedule_ts,
    save_schedule_state,
)
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

    @patch("src.social_publishers.requests.get")
    @patch("src.social_publishers.requests.post")
    def test_scheduled_mode_distinct_youtube_dates_and_fb_native_schedule(self, mock_post: MagicMock, mock_get: MagicMock) -> None:
        state_file = self.root / "schedule_state.json"
        now = datetime(2026, 11, 26, 14, 0, 0, tzinfo=timezone.utc)  # 09:00 AM EST / 21:00 WIB

        # Simulate 3 Mode Ngebut runs on the SAME day -> must allocate 3 DISTINCT consecutive dates!
        l1, s1, st1 = allocate_youtube_schedule_slots(state_file, now_utc=now)
        save_schedule_state(state_file, st1)
        l2, s2, st2 = allocate_youtube_schedule_slots(state_file, now_utc=now)
        save_schedule_state(state_file, st2)
        l3, s3, st3 = allocate_youtube_schedule_slots(state_file, now_utc=now)
        save_schedule_state(state_file, st3)

        self.assertEqual((l1, s1), ("2026-11-26T16:00:00Z", "2026-11-26T19:00:00Z"))
        self.assertEqual((l2, s2), ("2026-11-27T16:00:00Z", "2026-11-27T19:00:00Z"))
        self.assertEqual((l3, s3), ("2026-11-28T16:00:00Z", "2026-11-28T19:00:00Z"))

        # Facebook US Prime Time slot must be strictly >= now+20m (17:00 UTC = 12:00 PM EST!)
        fb_ts = compute_facebook_prime_schedule_ts(now_utc=now)
        self.assertEqual(fb_ts, int(datetime(2026, 11, 26, 17, 0, 0, tzinfo=timezone.utc).timestamp()))

        # Verify Facebook Reels native SCHEDULED payload
        env = {"META_ACCESS_TOKEN": "tok_meta", "FB_PAGE_ID": "fb_1"}
        with patch.dict(os.environ, env, clear=True):
            mock_get.return_value = _mock_resp(200, {"access_token": "page_tok"})
            mock_post.side_effect = [
                _mock_resp(200, {"video_id": "v_sched", "upload_url": "https://rupload.facebook.com/video-upload/v_sched"}),
                _mock_resp(200, {"success": True}),
                _mock_resp(200, {"success": True}),
            ]
            res = publish_facebook_reel_direct(self.mp4, "FB Scheduled Reel", "scheduled", scheduled_publish_ts=fb_ts)
            self.assertEqual(res["status"], "SCHEDULED")
            fin = mock_post.call_args_list[2].kwargs["json"]
            self.assertEqual(fin["video_state"], "SCHEDULED")
            self.assertEqual(fin["scheduled_publish_time"], fb_ts)

    @patch("src.publisher.send_reupload_telegram_report", return_value=True)
    @patch("src.publisher.publish_instagram_carousel_direct")
    @patch("src.publisher.publish_x_and_threads_direct")
    @patch("src.publisher.publish_instagram_reels_direct")
    def test_auto_reupload_recovers_only_failed_platforms(self, mock_ig, mock_threads, mock_carousel, mock_tg_reup) -> None:
        # IG Carousel succeeds on pass 1 (must NOT be re-uploaded!)
        mock_carousel.return_value = {"handled": True, "status": "PUBLISHED", "external_id": "car_1", "url": "https://ig/c1", "notes": "OK"}
        # IG Reels fails on pass 1, succeeds on delayed auto-reupload #1!
        mock_ig.side_effect = [
            {"handled": True, "status": "FAILED", "external_id": "c_bad", "url": "", "notes": "IG Reels binary upload gagal (400): ProcessingFailedError"},
            {"handled": True, "status": "PUBLISHED", "external_id": "ig_ok", "url": "https://ig/r1", "notes": "IG Reels OK"},
        ]
        # Threads fails on pass 1, succeeds on delayed auto-reupload #1!
        mock_threads.side_effect = [
            {"handled": True, "status": "FAILED", "external_id": "", "url": "", "notes": "Threads publish gagal (400)"},
            {"handled": True, "status": "PUBLISHED", "external_id": "threads:t_ok", "url": "", "notes": "Threads OK"},
        ]
        blueprint = {
            "meta": {"topic": "Auto Reupload Test", "channel_name": "HabitSains"},
            "youtube_long": {"title": "Long"},
            "shorts_reels_tiktok": {"title": "Short", "caption_ig_reels": "IG cap", "caption_tiktok": "TT"},
            "carousel_social": {"caption_instagram": "Car", "caption_linkedin": "LI", "thread_x": ["1/1"], "post_threads": "Hi Threads", "post_facebook": "FB"},
        }
        assets = {
            "youtube_long": {"video_path": "", "thumbnail_path": ""},
            "shorts_reels_tiktok": {"video_path": str(self.mp4)},
            "carousel_social": {"slide_paths": [str(s) for s in self.slides]},
        }
        cfg = {
            "publishing": {"default_mode": "publish", "save_payload_snapshots": True, "auto_reupload_delays_sec": [0, 0]},
            "platforms": {
                "youtube_long": {"enabled": False},
                "youtube_shorts": {"enabled": False},
                "tiktok": {"enabled": False},
                "linkedin": {"enabled": False},
                "facebook": {"enabled": False},
                "instagram_reels": {"enabled": True, "adapter": "direct"},
                "instagram_carousel": {"enabled": True, "adapter": "direct"},
                "x_threads": {"enabled": True, "adapter": "direct"},
            },
        }
        summary = publish_all_platforms(blueprint, assets, self.root, cfg, self.root, publish_mode="publish")
        self.assertEqual(summary["counts"]["failed"], 0)
        self.assertEqual(summary["counts"]["published"], 3)
        self.assertEqual(mock_carousel.call_count, 1)
        self.assertEqual(mock_ig.call_count, 2)
        self.assertEqual(mock_threads.call_count, 2)
        by_plat = {r["platform"]: r for r in summary["results"]}
        self.assertIn("auto-reupload #1 sukses", by_plat["Instagram Reels"]["notes"])
        self.assertIn("auto-reupload #1 sukses", by_plat["X & Threads"]["notes"])
        self.assertEqual(summary["auto_reupload_recovered"], ["Instagram Reels", "X & Threads"])
        self.assertEqual(mock_tg_reup.call_count, 1)

    @patch("src.social_publishers.time.sleep", return_value=None)
    @patch("src.social_publishers.requests.delete")
    @patch("src.social_publishers.requests.get")
    @patch("src.social_publishers.requests.post")
    def test_instagram_reels_falls_back_to_fb_cdn_video_url_on_processing_failed(
        self, mock_post: MagicMock, mock_get: MagicMock, mock_delete: MagicMock, _mock_sleep: MagicMock
    ) -> None:
        env = {"META_ACCESS_TOKEN": "tok_meta", "IG_BUSINESS_ACCOUNT_ID": "ig_1", "FB_PAGE_ID": "fb_1"}
        with patch.dict(os.environ, env, clear=True):
            # 2x rupload fails with ProcessingFailedError -> FB unpublished video upload -> IG video_url container -> media_publish
            mock_post.side_effect = [
                _mock_resp(200, {"id": "c_try1", "uri": "https://rupload.facebook.com/ig-api-upload/v21.0/c_try1"}),
                _mock_resp(400, {"debug_info": {"type": "ProcessingFailedError"}}),
                _mock_resp(200, {"id": "c_try2", "uri": "https://rupload.facebook.com/ig-api-upload/v21.0/c_try2"}),
                _mock_resp(400, {"debug_info": {"type": "ProcessingFailedError"}}),
                _mock_resp(200, {"id": "fb_vid_tmp"}),
                _mock_resp(200, {"id": "ig_cdn_cont"}),
                _mock_resp(200, {"id": "ig_pub_cdn"}),
            ]
            mock_get.side_effect = [
                _mock_resp(200, {"access_token": "page_tok"}),
                _mock_resp(200, {"source": "https://video.xx.fbcdn.net/v/t42/sample.mp4"}),
                _mock_resp(200, {"status_code": "FINISHED"}),
                _mock_resp(200, {"permalink": "https://www.instagram.com/reel/CDN_OK/"}),
            ]
            res = publish_instagram_reels_direct(self.mp4, "Reel caption", "scheduled")
            self.assertEqual(res["status"], "PUBLISHED")
            self.assertEqual(res["url"], "https://www.instagram.com/reel/CDN_OK/")
            self.assertIn("CDN video_url fallback", res["notes"])
            self.assertEqual(mock_delete.call_count, 1)

    @patch("src.publisher.publish_instagram_reels_direct")
    def test_auto_reupload_exhausted_failure_explicitly_reported_in_telegram_and_markdown(self, mock_ig: MagicMock) -> None:
        from src.publisher import _format_telegram_report_html
        from src.reporter import generate_publish_report

        mock_ig.return_value = {
            "handled": True, "status": "FAILED", "external_id": "c_err", "url": "",
            "notes": "IG Reels binary upload gagal (400): ProcessingFailedError",
        }
        bp = {
            "meta": {"topic": "Exhausted Retry Test", "channel_name": "HabitSains", "channel_handle": "@HabitSains"},
            "youtube_long": {"title": "Long", "description": "d"},
            "shorts_reels_tiktok": {"title": "Short", "caption_ig_reels": "IG cap"},
            "carousel_social": {"caption_instagram": "C", "thread_x": ["1"]},
        }
        assets = {
            "youtube_long": {"video_path": ""},
            "shorts_reels_tiktok": {"video_path": str(self.mp4)},
            "carousel_social": {"slide_paths": []},
        }
        cfg = {
            "publishing": {"default_mode": "scheduled", "save_payload_snapshots": True, "auto_reupload_delays_sec": [0, 0]},
            "platforms": {
                "youtube_long": {"enabled": False}, "youtube_shorts": {"enabled": False},
                "tiktok": {"enabled": False}, "linkedin": {"enabled": False},
                "facebook": {"enabled": False}, "instagram_carousel": {"enabled": False},
                "x_threads": {"enabled": False}, "instagram_reels": {"enabled": True, "adapter": "direct"},
            },
        }
        summary = publish_all_platforms(bp, assets, self.root, cfg, self.root, publish_mode="scheduled")
        self.assertEqual(mock_ig.call_count, 3)  # 1 initial + 2 auto-reupload rounds
        self.assertEqual(summary["auto_reupload_failed"], ["Instagram Reels"])
        self.assertEqual(summary["auto_reupload_log"][0]["attempts"], 2)
        self.assertIn("sudah dicoba auto-reupload 2/2x", summary["results"][0]["notes"])

        # Verify BOTH Telegram HTML and Markdown report explicitly disclose re-upload attempt count & failure!
        md_path, _, report_data = generate_publish_report("run_test", self.root, bp, assets, summary, 12.0, self.root / "hist.json")
        md_text = md_path.read_text(encoding="utf-8")
        tg_html = _format_telegram_report_html(report_data)
        self.assertIn("Status Auto-Reupload", md_text)
        self.assertIn("2/2 ronde", md_text)
        self.assertIn("Riwayat Auto-Reupload Otomatis", md_text)
        self.assertIn("Status Auto-Reupload", tg_html)
        self.assertIn("sudah diulang 2/2x, tetap gagal", tg_html)


if __name__ == "__main__":
    unittest.main()
