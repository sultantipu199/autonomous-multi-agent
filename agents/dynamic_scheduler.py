"""Dynamic Scheduler with Algorithmic Timing and Organic Jitter.

Adapts publishing window to peak engagement hours (08:30 AM - 11:30 AM BD Time / UTC+6)
adding organic jitter (randomized micro-shifts) to mimic genuine human activity rather
than robotic fixed-time posting.
"""

import os
import random
from datetime import datetime, time, timedelta
import zoneinfo
from typing import Dict, Any


class DynamicScheduler:
    """Calculates adaptive publishing schedules within peak BD engagement windows."""

    def __init__(
        self,
        timezone_str: str = "Asia/Dhaka",
        window_start_str: str = "08:30",
        window_end_str: str = "11:30",
    ):
        try:
            self.tz = zoneinfo.ZoneInfo(timezone_str)
        except Exception:
            # Fallback if zoneinfo tzdata is not available on Windows
            self.tz = zoneinfo.ZoneInfo("UTC")

        self.start_hour, self.start_minute = map(int, window_start_str.split(":"))
        self.end_hour, self.end_minute = map(int, window_end_str.split(":"))

    def get_current_time(self) -> datetime:
        """Returns current time in targeted timezone."""
        return datetime.now(self.tz)

    def calculate_optimal_slot(self, base_date: datetime = None) -> Dict[str, Any]:
        """Calculates a randomized peak publication slot with organic jitter.

        Returns:
            Dict containing planned time, jitter_seconds, and human-readable explanation.
        """
        now = base_date or self.get_current_time()

        # Define window boundaries for today
        window_start = datetime.combine(
            now.date(),
            time(self.start_hour, self.start_minute),
            tzinfo=self.tz,
        )
        window_end = datetime.combine(
            now.date(),
            time(self.end_hour, self.end_minute),
            tzinfo=self.tz,
        )

        total_window_seconds = int((window_end - window_start).total_seconds())

        # If current time is already past window_end, plan for tomorrow's window
        if now > window_end:
            tomorrow = now.date() + timedelta(days=1)
            window_start = datetime.combine(
                tomorrow,
                time(self.start_hour, self.start_minute),
                tzinfo=self.tz,
            )
            window_end = datetime.combine(
                tomorrow,
                time(self.end_hour, self.end_minute),
                tzinfo=self.tz,
            )

        # Apply peak-weighted distribution (peak engagement around 09:30 - 10:30 AM)
        # We use a triangular distribution peaking around 40-60% into the window
        peak_offset = random.triangular(0.2, 0.8, 0.5) * total_window_seconds
        
        # Add micro-jitter (+/- 3 to 14 minutes in seconds)
        micro_jitter = random.randint(-180, 240)
        target_seconds_offset = max(0, min(total_window_seconds, int(peak_offset + micro_jitter)))

        scheduled_time = window_start + timedelta(seconds=target_seconds_offset)
        delay_from_now = max(0.0, (scheduled_time - now).total_seconds())

        return {
            "scheduled_time": scheduled_time.isoformat(),
            "scheduled_time_display": scheduled_time.strftime("%Y-%m-%d %I:%M:%S %p %Z"),
            "window_start": window_start.strftime("%I:%M %p"),
            "window_end": window_end.strftime("%I:%M %p"),
            "micro_jitter_seconds": micro_jitter,
            "seconds_until_execution": delay_from_now,
            "is_within_window_now": window_start <= now <= window_end,
        }


# Quick convenience function
def get_dynamic_schedule() -> Dict[str, Any]:
    scheduler = DynamicScheduler(
        timezone_str=os.getenv("TIMEZONE", "Asia/Dhaka"),
        window_start_str=os.getenv("PUBLISH_WINDOW_START", "08:30"),
        window_end_str=os.getenv("PUBLISH_WINDOW_END", "11:30"),
    )
    return scheduler.calculate_optimal_slot()
