"""Persistent Multi-Day US Prime Time Scheduling Queue (`output/schedule_state.json`).

Enables "Mode Ngebut" (3x daily production & upload) WITHOUT stacking multiple YouTube videos on the
same day:
  - Each newly produced episode automatically reserves the NEXT unused calendar date for YouTube
    Long (16:00 UTC = 11:00 AM US Eastern / 23:00 WIB) and YouTube Shorts (19:00 UTC = 2:00 PM EST /
    02:00 WIB next day) via official YouTube Data API v3 `status.publishAt`.
  - Facebook Page Reels receives the next valid US Prime Time slot within Meta's official
    [now + 15 min, now + 28 days] scheduling window (`video_state="SCHEDULED"`, `scheduled_publish_time`).
  - State is persisted to `output/schedule_state.json` and auto-committed by GitHub Actions alongside
    `output/history.json` so consecutive cloud runs never collide on the same publish date.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


# US Eastern Prime Time slots in UTC (approx. EST / EDT sweet spot for global English HabitSains audience)
DEFAULT_YT_LONG_HOUR_UTC = 16    # 11:00 AM EST / 12:00 PM EDT / 23:00 WIB
DEFAULT_YT_SHORTS_HOUR_UTC = 19  # 02:00 PM EST / 03:00 PM EDT / 02:00 WIB (+1)
US_PRIME_HOURS_UTC = (14, 17, 21)  # 09:00 AM, 12:00 PM, 04:00 PM EST (21:00, 00:00, 04:00 WIB)


def load_schedule_state(state_file: Path) -> dict[str, Any]:
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_schedule_state(state_file: Path, state: dict[str, Any]) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def allocate_youtube_schedule_slots(
    state_file: Path,
    config: dict[str, Any] | None = None,
    now_utc: datetime | None = None,
) -> tuple[str, str, dict[str, Any]]:
    """Allocate the next unused calendar date (distinct day!) for YouTube Long & Shorts at US Prime Time.

    Returns `(long_publish_at_iso, shorts_publish_at_iso, updated_state)`.
    """
    now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    sched_cfg = (config or {}).get("publishing", {}).get("schedule", {})
    long_hour = int(sched_cfg.get("youtube_long_hour_utc", DEFAULT_YT_LONG_HOUR_UTC))
    shorts_hour = int(sched_cfg.get("youtube_shorts_hour_utc", DEFAULT_YT_SHORTS_HOUR_UTC))

    state = load_schedule_state(state_file)
    last_date_str = str(state.get("last_youtube_date", "")).strip()

    # Minimum valid publish date: today if long_hour is still >= 45 min ahead, else tomorrow!
    today_long_dt = datetime(now.year, now.month, now.day, long_hour, 0, 0, tzinfo=timezone.utc)
    min_date = now.date() if today_long_dt >= now + timedelta(minutes=45) else (now.date() + timedelta(days=1))

    if last_date_str:
        try:
            prev_date = date.fromisoformat(last_date_str)
            target_date = max(prev_date + timedelta(days=1), min_date)
        except ValueError:
            target_date = min_date
    else:
        target_date = min_date

    long_dt = datetime(target_date.year, target_date.month, target_date.day, long_hour, 0, 0, tzinfo=timezone.utc)
    shorts_dt = datetime(target_date.year, target_date.month, target_date.day, shorts_hour, 0, 0, tzinfo=timezone.utc)
    if shorts_dt <= long_dt:
        shorts_dt = long_dt + timedelta(hours=3)

    long_iso = long_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    shorts_iso = shorts_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    state["last_youtube_date"] = target_date.isoformat()
    state["last_youtube_long_publish_at"] = long_iso
    state["last_youtube_shorts_publish_at"] = shorts_iso
    state["updated_at_utc"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    return long_iso, shorts_iso, state


def compute_facebook_prime_schedule_ts(
    now_utc: datetime | None = None,
    prime_hours_utc: tuple[int, ...] = US_PRIME_HOURS_UTC,
) -> int:
    """Compute the next valid Facebook Reels US Prime Time Unix timestamp (Meta rule: >= 10m and <= 29d ahead)."""
    now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    min_dt = now + timedelta(minutes=20)  # Safe buffer over Meta's strict 10-minute minimum
    max_dt = now + timedelta(days=28)

    # Pick the earliest US Prime Time slot >= min_dt
    for day_off in range(0, 3):
        d = (now + timedelta(days=day_off)).date()
        for hr in sorted(prime_hours_utc):
            cand = datetime(d.year, d.month, d.day, hr, 0, 0, tzinfo=timezone.utc)
            if min_dt <= cand <= max_dt:
                return int(cand.timestamp())
    return int(min_dt.timestamp())
