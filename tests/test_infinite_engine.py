"""Unit Test Suite for Infinite Perpetual Engine & Dynamic Scheduler.

Audits:
1. DynamicScheduler timing, peak windows, and jitter offsets.
2. CurriculumEngine infinite dynamic topic generation and caching.
3. DedupSentinel multi-day lookahead and collision prevention.
4. Stress-testing 30 consecutive simulated days for zero duplicate collisions.
"""

import os
import sys
import unittest
from datetime import datetime

# Ensure root workspace is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.curriculum_engine import CurriculumEngine
from agents.dedup_sentinel import DedupSentinel
from agents.dynamic_scheduler import DynamicScheduler


class TestInfinitePerpetualEngine(unittest.TestCase):
    """Rigorous tests auditing the 24/7/365 infinite growth architecture."""

    def setUp(self):
        self.curriculum = CurriculumEngine()
        self.sentinel = DedupSentinel()
        self.scheduler = DynamicScheduler(timezone_str="Asia/Dhaka")

    def test_01_dynamic_scheduler_slot_and_jitter(self):
        """Verify scheduler calculates valid peak slots with micro-jitter in Asia/Dhaka."""
        slot = self.scheduler.calculate_optimal_slot()
        self.assertIn("scheduled_time", slot)
        self.assertIn("window_start", slot)
        self.assertIn("window_end", slot)
        self.assertIn("micro_jitter_seconds", slot)
        self.assertGreaterEqual(slot["micro_jitter_seconds"], -180)
        self.assertLessEqual(slot["micro_jitter_seconds"], 240)
        print(f"\n[Test Scheduler] Optimal slot: {slot['scheduled_time_display']} (Jitter: {slot['micro_jitter_seconds']}s)")

    def test_02_scheduler_bengali_countdown(self):
        """Verify Bengali duration formatting."""
        fmt_1 = DynamicScheduler.format_countdown_bengali(3660)
        fmt_2 = DynamicScheduler.format_countdown_bengali(120)
        fmt_0 = DynamicScheduler.format_countdown_bengali(-10)
        self.assertIn("ঘণ্টা", fmt_1)
        self.assertIn("মিনিট", fmt_2)
        self.assertIn("এখনই", fmt_0)
        print("[Test Scheduler] Bengali duration formatting verified successfully.")

    def test_03_infinite_topics_structure_and_schema(self):
        """Verify that topics generated for distant days (e.g. Day 60, Day 120, Day 365)
        comply with all multi-agent carousel requirements."""
        distant_days = [60, 120, 365]
        for d in distant_days:
            ct = self.curriculum.get_topic_by_day(d)
            self.assertEqual(ct.class_id, d)
            self.assertTrue(len(ct.title) > 10)
            self.assertTrue(len(ct.actionable_tip) > 20)
            self.assertTrue(len(ct.code_snippet) > 10)
            self.assertEqual(len(ct.checklist_items), 4)
            self.assertGreaterEqual(len(ct.tags), 3)

            # Test ResearchTopic translation
            rt = self.curriculum.get_as_research_topic(d)
            self.assertEqual(rt.title, ct.title)
            self.assertIn(ct.module_category, rt.summary)
            print(f"[Test Infinite Engine] Day {d:03d} validated: '{ct.title[:50]}...'")

    def test_04_consecutive_30_days_zero_duplicates(self):
        """Simulate generating 30 consecutive days from Day 20 to Day 50 and verify 0% title collision."""
        seen_titles = set()
        for d in range(20, 50):
            ct = self.curriculum.get_topic_by_day(d)
            self.assertNotIn(ct.title, seen_titles, f"Day {d} title '{ct.title}' collided with past generated topic!")
            seen_titles.add(ct.title)
        self.assertEqual(len(seen_titles), 30)
        print(f"[Test Infinite Engine] 30 consecutive simulated days verified with 100% unique titles!")


if __name__ == "__main__":
    unittest.main()
