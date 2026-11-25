"""Lightweight 24/7 Cloud Scheduler for Docker / VPS deployments.

Environment variables:
  SCHEDULE_TIME_WIB   Daily run time in HH:MM (default: "08:00")
  SCHEDULE_DAYS       Comma-separated lowercase weekday names (default: "mon,tue,wed,thu,fri,sat,sun")
  SCHEDULE_TZ         IANA timezone (default: "Asia/Jakarta")
  PUBLISH_MODE        "dry-run" | "draft" | "publish" (default: "draft")
  RUN_ON_STARTUP      "true" to execute one run immediately on boot (default: "false")
"""

from __future__ import annotations

import os
import signal
import sys
import time
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

from src.pipeline import run_pipeline

DAY_MAP = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}

_RUNNING = True


def _handle_signal(signum, _frame):
    global _RUNNING
    print(f"[scheduler] Received signal {signum}, shutting down gracefully...", flush=True)
    _RUNNING = False


def _parse_schedule() -> tuple[int, int, set[int], ZoneInfo]:
    tz_name = os.getenv("SCHEDULE_TZ", "Asia/Jakarta").strip() or "Asia/Jakarta"
    tz = ZoneInfo(tz_name)

    time_str = os.getenv("SCHEDULE_TIME_WIB", "08:00").strip()
    parts = time_str.split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Invalid SCHEDULE_TIME_WIB: {time_str}")

    days_raw = os.getenv("SCHEDULE_DAYS", "mon,tue,wed,thu,fri,sat,sun").lower()
    allowed_days = {DAY_MAP[d.strip()[:3]] for d in days_raw.split(",") if d.strip()[:3] in DAY_MAP}
    if not allowed_days:
        allowed_days = set(range(7))

    return hour, minute, allowed_days, tz


def _execute_once(publish_mode: str) -> None:
    print(f"[scheduler] Triggering Content Automation Pipeline (mode={publish_mode})...", flush=True)
    try:
        result = run_pipeline(publish_mode=publish_mode)
        print(
            f"[scheduler] Run finished: {result.get('run_id')} | QA={result.get('qa_passed_all')} | "
            f"Counts={result.get('publishing', {}).get('counts')}",
            flush=True,
        )
    except Exception:
        print("[scheduler] Pipeline run failed with exception:", flush=True)
        traceback.print_exc()


def main() -> int:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    hour, minute, allowed_days, tz = _parse_schedule()
    publish_mode = os.getenv("PUBLISH_MODE", "draft").strip() or "draft"
    run_on_startup = os.getenv("RUN_ON_STARTUP", "false").strip().lower() == "true"

    print(
        f"[scheduler] Content Automation Studio 24/7 Cloud Scheduler aktif!\n"
        f"  - Jadwal : {hour:02d}:{minute:02d} ({tz.key})\n"
        f"  - Hari   : {sorted(allowed_days)} (0=Senin .. 6=Minggu)\n"
        f"  - Mode   : {publish_mode}\n"
        f"  - Startup: {run_on_startup}",
        flush=True,
    )

    if run_on_startup:
        _execute_once(publish_mode)

    last_run_key = ""
    while _RUNNING:
        now = datetime.now(tz)
        run_key = now.strftime("%Y-%m-%d %H:%M")
        if now.weekday() in allowed_days and now.hour == hour and now.minute == minute and run_key != last_run_key:
            last_run_key = run_key
            _execute_once(publish_mode)
        time.sleep(20)

    print("[scheduler] Stopped.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
